import torch
import torch.nn as nn
import torch.nn.functional as F
from configs.config import LCMConfig
from .layers import ConceptBlock, RMSNorm


class LatentReasoner(nn.Module):
    """Razonador con lector de ranuras (parche-11).

    1. LECTOR: cada premisa (sujeto, predicado, objeto fusionados en un vector)
       se desliga en tres ranuras y se limpia contra el catalogo de conceptos
       (resta iterativa: predicado -> sujeto/objeto). No se entrena.
    2. EMPAREJADOR: se calcula que ranuras de una premisa son IGUALES a que
       ranuras de otra (el termino medio de una cadena, la regla enunciada...).
       No depende de que palabras o entidades concretas sean.
    3. RAZONADOR: un Transformer recibe esas pistas y decide, para cada rol de
       la conclusion, de que ranura COPIAR o que constante aprendida usar.
    """
    N_CONST = 16

    def __init__(self, config: LCMConfig):
        super().__init__()
        self.config = config
        d = config.d_concept
        self.input_scale = float(d) ** 0.5
        self.pos_emb = nn.Embedding(config.max_concept_seq, d)
        nn.init.normal_(self.pos_emb.weight, mean=0.0, std=0.02)
        self.match_proj = nn.Linear(9, d, bias=False)
        self.layers = nn.ModuleList([
            ConceptBlock(d, config.n_heads, config.max_concept_seq, config.dropout)
            for _ in range(config.n_layers)
        ])
        self.norm = RMSNorm(d)
        self.slot_head = nn.Linear(d, 9, bias=True)       # por premisa: 3 roles de salida x 3 ranuras
        self.const_head = nn.Linear(d, 3 * self.N_CONST)  # por muestra: roles x constantes
        self.codebook = nn.Parameter(torch.randn(3, self.N_CONST, d) / d ** 0.5)
        # Catalogo y matrices de rol (se rellenan con set_space; viajan en el checkpoint).
        self.register_buffer("roles", torch.eye(d).unsqueeze(0).repeat(3, 1, 1))
        self.register_buffer("concepts", torch.zeros(1, d))

    def set_space(self, space):
        """Carga matrices de rol y catalogo de conceptos de la ontologia."""
        roles = torch.stack([space.role_matrices[r] for r in ("subject", "predicate", "object")])
        emb = F.normalize(space.embeddings.detach().float(), dim=-1)
        device = self.roles.device
        self.roles = roles.to(device).float()
        self.concepts = emb.to(device)

    @torch.no_grad()
    def read_slots(self, x):
        """Devuelve indices (B,L,3) de concepto para sujeto, predicado y objeto."""
        E, R = self.concepts, self.roles
        Rs, Rp, Ro = R[0], R[1], R[2]

        def nearest(vec, role):
            return (F.normalize(vec @ R[role], dim=-1) @ E.T).argmax(-1)

        def proj(vec, idx, role):
            bound = E[idx] @ R[role].T
            return (vec * bound).sum(-1, keepdim=True) * bound

        p = nearest(x, 1)
        rem = x - proj(x, p, 1)
        s = nearest(rem, 0)
        o = nearest(rem - proj(x, s, 0), 2)
        for _ in range(2):
            s = nearest(rem - proj(x, o, 2), 0)
            o = nearest(rem - proj(x, s, 0), 2)
        return torch.stack([s, p, o], dim=-1)

    def forward(self, x, target=None, attention_mask=None):
        if x.ndim != 3:
            raise ValueError("x debe tener forma [batch, secuencia, dimension].")
        batch, length, dim = x.shape
        if dim != self.config.d_concept:
            raise ValueError(f"Dimension recibida {dim}; esperada {self.config.d_concept}.")
        if length < 1 or length > self.config.max_concept_seq:
            raise ValueError(f"La longitud debe estar entre 1 y {self.config.max_concept_seq}.")
        if attention_mask is None:
            attention_mask = torch.ones(batch, length, device=x.device, dtype=torch.bool)
        else:
            attention_mask = attention_mask.to(device=x.device, dtype=torch.bool)
            if attention_mask.shape != (batch, length):
                raise ValueError("attention_mask debe tener forma [batch, secuencia].")
            if torch.any(attention_mask.sum(dim=1) == 0):
                raise ValueError("Cada muestra debe contener al menos una premisa valida.")

        idx = self.read_slots(x)                                   # (B,L,3)
        slots = self.concepts[idx]                                 # (B,L,3,d)
        # Emparejador: eq[b,i,j,a,c] = ranura a de i == ranura c de j (i != j, j valida)
        eq = idx.unsqueeze(2).unsqueeze(4) == idx.unsqueeze(1).unsqueeze(3)   # (B,L,L,3,3)
        other = attention_mask.unsqueeze(1) & ~torch.eye(length, dtype=torch.bool, device=x.device).unsqueeze(0)
        eq = eq & other.unsqueeze(-1).unsqueeze(-1)
        match = eq.any(dim=2).float().view(batch, length, 9)

        positions = torch.arange(length, device=x.device)
        h = x * self.input_scale + self.pos_emb(positions).unsqueeze(0) + self.match_proj(match) * self.input_scale
        for layer in self.layers:
            h = layer(h, attention_mask=attention_mask)
        h = self.norm(h)

        last_valid = attention_mask.long().sum(dim=1) - 1
        pooled = h[torch.arange(batch, device=x.device), last_valid]
        slot_logits = self.slot_head(h).view(batch, length, 3, 3)            # i, rol, ranura
        slot_logits = slot_logits.masked_fill(~attention_mask.view(batch, length, 1, 1), float("-inf"))
        slot_logits = slot_logits.permute(0, 2, 1, 3).reshape(batch, 3, length * 3)
        const_logits = self.const_head(pooled).view(batch, 3, self.N_CONST)
        logits = torch.cat([slot_logits, const_logits], dim=-1)               # (B,3,L*3+K)
        weights = F.softmax(logits, dim=-1)
        cand_slots = slots.reshape(batch, length * 3, dim)
        out = 0
        for role in range(3):
            cands = torch.cat([cand_slots, self.codebook[role].unsqueeze(0).expand(batch, -1, -1)], dim=1)
            role_vec = (weights[:, role].unsqueeze(-1) * cands).sum(dim=1)    # (B,d)
            out = out + role_vec @ self.roles[role].T
        pred_vector = F.normalize(out, p=2, dim=-1)

        loss = None
        if target is not None:
            target = F.normalize(target.to(device=x.device, dtype=pred_vector.dtype), p=2, dim=-1)
            loss = (1.0 - F.cosine_similarity(pred_vector, target, dim=-1)).mean()
        return pred_vector, loss
