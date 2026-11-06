import os
from pathlib import Path

# Diccionario con todos los archivos del proyecto LCM
FILES = {}

# -----------------------------------------------------------------------------
# REQUIREMENTS & README
# -----------------------------------------------------------------------------
FILES["requirements.txt"] = """torch>=2.1.0
numpy>=1.24.0
tqdm>=4.66.0
"""

FILES["README.md"] = """# Large Conceptual Model (LCM)

Arquitectura de razonamiento en espacio latente continuo (independiente del idioma).

## Estructura
- configs/: Configuraciones del modelo y entrenamiento.
- src/ontology/: Espacio geométrico y registro de conceptos universales.
- src/model/: Transformer continuo (sin vocabulario) y decodificador verbal desacoplado.
- src/reasoning/: Motor de deducción secuencial en silencio.
- scripts/: Preparación de datos, entrenamiento del razonador e inferencia interactiva.
- exportar.py: Script para empaquetar árbol y código para otro LLM.

## Uso
1. python -m scripts.prepare_concepts
2. python -m scripts.train_reasoner
3. python -m scripts.think
4. python exportar.py
"""

# -----------------------------------------------------------------------------
# CONFIGURACIONES
# -----------------------------------------------------------------------------
FILES["configs/__init__.py"] = ""

FILES["configs/config.py"] = """from dataclasses import dataclass
import torch

@dataclass
class LCMConfig:
    d_concept: int = 128         # Dimension vectorial del espacio conceptual
    n_layers: int = 4            # Bloques Transformer continuos
    n_heads: int = 4             # Cabezas de atencion
    max_concept_seq: int = 16    # Longitud maxima de la cadena de pensamientos
    dropout: float = 0.05
    device: str = (
        "mps" if torch.backends.mps.is_available()
        else ("cuda" if torch.cuda.is_available() else "cpu")
    )

@dataclass
class TrainConfig:
    batch_size: int = 16
    learning_rate: float = 1e-3
    epochs: int = 15
    checkpoint_dir: str = "checkpoints"
    device: str = (
        "mps" if torch.backends.mps.is_available()
        else ("cuda" if torch.cuda.is_available() else "cpu")
    )
"""

# -----------------------------------------------------------------------------
# ONTOLOGÍA CONCEPTUAL
# -----------------------------------------------------------------------------
FILES["src/__init__.py"] = ""
FILES["src/ontology/__init__.py"] = "from .concept_space import ConceptSpace\n"

FILES["src/ontology/concept_space.py"] = """import torch
import torch.nn.functional as F

class ConceptSpace:
    # Espacio conceptual universal independiente del lenguaje.
    def __init__(self, d_concept: int = 128):
        self.d_concept = d_concept
        self.concept_to_id = {}
        self.id_to_concept = {}
        self.translations = {}
        self.embeddings = None

    def register_concept(self, name: str, es_text: str, en_text: str):
        if name not in self.concept_to_id:
            cid = len(self.concept_to_id)
            self.concept_to_id[name] = cid
            self.id_to_concept[cid] = name
            self.translations[name] = {"es": es_text, "en": en_text}

    def build_space(self, seed: int = 42):
        # Genera vectores aleatorios distribuidos en la hiperesfera unitaria
        torch.manual_seed(seed)
        n = len(self.concept_to_id)
        raw = torch.randn(n, self.d_concept)
        self.embeddings = F.normalize(raw, p=2, dim=-1)

    def get_vector(self, name: str) -> torch.Tensor:
        cid = self.concept_to_id[name]
        return self.embeddings[cid].clone()

    def find_nearest_concept(self, vector: torch.Tensor) -> tuple:
        # Busca el concepto mas cercano por similitud coseno
        v_norm = F.normalize(vector.view(1, -1), p=2, dim=-1)
        sims = torch.mm(v_norm, self.embeddings.t()).squeeze(0)
        best_id = torch.argmax(sims).item()
        return self.id_to_concept[best_id], sims[best_id].item()

    def verbalize(self, name: str, lang: str = "es") -> str:
        # Traduce el concepto a lenguaje natural bajo demanda
        return self.translations.get(name, {}).get(lang, f"[{name}]")
"""

# -----------------------------------------------------------------------------
# MODELO: CAPAS, RAZONADOR LATENTE Y DECODIFICADOR
# -----------------------------------------------------------------------------
FILES["src/model/__init__.py"] = "from .reasoner import LatentReasoner\nfrom .decoder import ConceptDecoder\n"

FILES["src/model/layers.py"] = """import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        var = x.pow(2).mean(-1, keepdim=True)
        return x * torch.rsqrt(var + self.eps) * self.weight

class ContinuousAttention(nn.Module):
    # Atencion causal sobre vectores continuos de pensamiento
    def __init__(self, d_concept: int, n_heads: int, max_len: int, dropout: float = 0.0):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = d_concept // n_heads

        self.q = nn.Linear(d_concept, d_concept, bias=False)
        self.k = nn.Linear(d_concept, d_concept, bias=False)
        self.v = nn.Linear(d_concept, d_concept, bias=False)
        self.out = nn.Linear(d_concept, d_concept, bias=False)
        self.drop = nn.Dropout(dropout)

        self.register_buffer("mask", torch.tril(torch.ones(max_len, max_len)).view(1, 1, max_len, max_len))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.shape
        q = self.q(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)

        scores = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        scores = scores.masked_fill(self.mask[:, :, :T, :T] == 0, float("-inf"))
        probs = self.drop(F.softmax(scores, dim=-1))

        out = (probs @ v).transpose(1, 2).contiguous().view(B, T, C)
        return self.out(out)

class ConceptBlock(nn.Module):
    def __init__(self, d_concept: int, n_heads: int, max_len: int, dropout: float):
        super().__init__()
        self.norm1 = RMSNorm(d_concept)
        self.attn = ContinuousAttention(d_concept, n_heads, max_len, dropout)
        self.norm2 = RMSNorm(d_concept)
        self.mlp = nn.Sequential(
            nn.Linear(d_concept, d_concept * 4, bias=False),
            nn.SiLU(),
            nn.Linear(d_concept * 4, d_concept, bias=False),
            nn.Dropout(dropout)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x
"""

FILES["src/model/reasoner.py"] = """import torch
import torch.nn as nn
import torch.nn.functional as F
from configs.config import LCMConfig
from .layers import ConceptBlock, RMSNorm

class LatentReasoner(nn.Module):
    # El Cerebro: Recibe secuencias de vectores conceptuales y predice el siguiente vector
    def __init__(self, config: LCMConfig):
        super().__init__()
        self.config = config
        self.pos_emb = nn.Embedding(config.max_concept_seq, config.d_concept)
        self.layers = nn.ModuleList([
            ConceptBlock(config.d_concept, config.n_heads, config.max_concept_seq, config.dropout)
            for _ in range(config.n_layers)
        ])
        self.norm = RMSNorm(config.d_concept)
        self.concept_head = nn.Linear(config.d_concept, config.d_concept, bias=False)

    def forward(self, x: torch.Tensor, target: torch.Tensor = None):
        B, T, D = x.shape
        pos = torch.arange(0, T, device=x.device)
        h = x + self.pos_emb(pos)

        for layer in self.layers:
            h = layer(h)

        h = self.norm(h)
        pred_vector = self.concept_head(h[:, -1, :])
        pred_vector = F.normalize(pred_vector, p=2, dim=-1)

        loss = None
        if target is not None:
            target_norm = F.normalize(target, p=2, dim=-1)
            # Perdida Coseno: 0 cuando apuntan exactamente en la misma direccion
            loss = (1.0 - F.cosine_similarity(pred_vector, target_norm, dim=-1)).mean()

        return pred_vector, loss
"""

FILES["src/model/decoder.py"] = """import torch
from src.ontology.concept_space import ConceptSpace

class ConceptDecoder:
    # La Boca: Inactiva durante el pensamiento. Solo traduce a lenguaje si se le pide
    def __init__(self, space: ConceptSpace):
        self.space = space

    def translate_thought(self, vector: torch.Tensor, lang: str = "es") -> dict:
        name, certainty = self.space.find_nearest_concept(vector.cpu())
        human_text = self.space.verbalize(name, lang=lang)
        return {
            "concept": name,
            "certainty": round(certainty * 100, 2),
            "text": human_text,
            "lang": lang
        }
"""

# -----------------------------------------------------------------------------
# ENTRENADOR LATENTE
# -----------------------------------------------------------------------------
FILES["src/training/__init__.py"] = "from .trainer import ConceptTrainer\n"

FILES["src/training/trainer.py"] = """import os
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from configs.config import TrainConfig
from src.model.reasoner import LatentReasoner

class ConceptTrainer:
    def __init__(self, model: LatentReasoner, config: TrainConfig, loader: DataLoader):
        self.model = model.to(config.device)
        self.config = config
        self.loader = loader
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=1e-4)
        os.makedirs(config.checkpoint_dir, exist_ok=True)

    def train(self):
        self.model.train()
        print(f"[*] Entrenando Razonador Conceptual en [{self.config.device.upper()}]...")

        for epoch in range(self.config.epochs):
            total_loss = 0.0
            pbar = tqdm(self.loader, desc=f"Epoca {epoch+1}/{self.config.epochs}")
            for seq_vectors, target_vector in pbar:
                seq_vectors = seq_vectors.to(self.config.device)
                target_vector = target_vector.to(self.config.device)

                _, loss = self.model(seq_vectors, target=target_vector)

                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                total_loss += loss.item()
                pbar.set_postfix(loss_coseno=f"{loss.item():.4f}")

            avg_loss = total_loss / len(self.loader)
            print(f"[!] Epoca {epoch+1} completada. Loss Coseno: {avg_loss:.4f}")
            self.save_checkpoint(epoch, avg_loss)

    def save_checkpoint(self, epoch: int, loss: float):
        path = os.path.join(self.config.checkpoint_dir, "lcm_reasoner.pt")
        torch.save({
            "epoch": epoch + 1,
            "model_state_dict": self.model.state_dict(),
            "loss": loss
        }, path)
"""

# -----------------------------------------------------------------------------
# MOTOR DE INFERENCIA
# -----------------------------------------------------------------------------
FILES["src/reasoning/__init__.py"] = "from .engine import ReasoningEngine\n"

FILES["src/reasoning/engine.py"] = """import torch
from src.ontology.concept_space import ConceptSpace
from src.model.reasoner import LatentReasoner

class ReasoningEngine:
    # Encadena deducciones de pensamientos puros en el espacio latente
    def __init__(self, model: LatentReasoner, space: ConceptSpace, device: str):
        self.model = model.to(device)
        self.space = space
        self.device = device
        self.model.eval()

    def think(self, premise_names: list, steps: int = 1) -> list:
        vectors = [self.space.get_vector(name) for name in premise_names]
        generated = []

        with torch.no_grad():
            for _ in range(steps):
                inp = torch.stack(vectors).unsqueeze(0).to(self.device)
                next_vec, _ = self.model(inp)
                next_vec_cpu = next_vec.squeeze(0).cpu()
                vectors.append(next_vec_cpu)
                generated.append(next_vec_cpu)

        return generated
"""

# -----------------------------------------------------------------------------
# SCRIPTS DE ENTRADA
# -----------------------------------------------------------------------------
FILES["scripts/prepare_concepts.py"] = """import os
import pickle
import torch
from torch.utils.data import TensorDataset
from src.ontology.concept_space import ConceptSpace

def main():
    print("[*] Creando base ontologica de conceptos...")
    space = ConceptSpace(d_concept=128)

    concepts = [
        # Dinamica fisica
        ("MANZANA", "una manzana", "an apple"),
        ("SOLTAR", "es soltada en el aire", "is released into the air"),
        ("GRAVEDAD", "bajo el efecto de la gravedad", "under gravity"),
        ("CAER", "cae al suelo", "falls down to the ground"),

        # Cardinalidad
        ("CONJUNTO_FINITO", "un conjunto de elementos numerables", "a finite set"),
        ("CONTAR", "puede ser contado uno por uno", "can be counted one by one"),
        ("CARDINALIDAD", "posee un numero finito verificable", "has a finite cardinality"),

        # Incontabilidad / Infinito
        ("CONJUNTO_INFINITO", "una sucesion infinita", "an infinite succession"),
        ("NO_CONTAR", "no se puede terminar de contar jamas", "cannot ever be counted"),
        ("INNUMERABLE", "pertenece a la categoria de lo infinito e incontable", "belongs to the uncountable"),

        # Termodinamica
        ("HIELO", "un cubo de hielo solido", "a solid ice cube"),
        ("CALOR", "se expone a alta temperatura", "is exposed to heat"),
        ("DERRETIR", "se convierte en agua liquida", "melts into water"),

        # Logica relacional
        ("PREMISA_A_MAYOR_B", "sabemos que A es mayor que B", "A is greater than B"),
        ("PREMISA_B_MAYOR_C", "y sabemos que B es mayor que C", "B is greater than C"),
        ("CONCLUSION_A_MAYOR_C", "se deduce logicamente que A es mayor que C", "it follows that A is greater than C")
    ]

    for name, es, en in concepts:
        space.register_concept(name, es, en)

    space.build_space()
    print(f"[+] Registrados {len(concepts)} conceptos universales.")

    # Cadenas de razonamiento causa-efecto
    chains = [
        (["MANZANA", "SOLTAR", "GRAVEDAD"], "CAER"),
        (["CONJUNTO_FINITO", "CONTAR"], "CARDINALIDAD"),
        (["CONJUNTO_INFINITO", "CONTAR"], "NO_CONTAR"),
        (["CONJUNTO_INFINITO", "NO_CONTAR"], "INNUMERABLE"),
        (["HIELO", "CALOR"], "DERRETIR"),
        (["PREMISA_A_MAYOR_B", "PREMISA_B_MAYOR_C"], "CONCLUSION_A_MAYOR_C"),
    ] * 200

    MAX_LEN = 4
    seq_tensors = []
    target_tensors = []

    for premises, target in chains:
        vecs = [space.get_vector(c) for c in premises]
        while len(vecs) < MAX_LEN:
            vecs.insert(0, torch.zeros(128))
        seq_tensors.append(torch.stack(vecs))
        target_tensors.append(space.get_vector(target))

    dataset = TensorDataset(torch.stack(seq_tensors), torch.stack(target_tensors))

    os.makedirs("data", exist_ok=True)
    with open("data/concept_space.pkl", "wb") as f:
        pickle.dump(space, f)
    with open("data/concept_dataset.pkl", "wb") as f:
        pickle.dump(dataset, f)

    print("[+] Datos listos en data/concept_space.pkl y data/concept_dataset.pkl")

if __name__ == "__main__":
    main()
"""

FILES["scripts/train_reasoner.py"] = """import pickle
from torch.utils.data import DataLoader
from configs.config import LCMConfig, TrainConfig
from src.model.reasoner import LatentReasoner
from src.training.trainer import ConceptTrainer

def main():
    with open("data/concept_space.pkl", "rb") as f:
        space = pickle.load(f)
    with open("data/concept_dataset.pkl", "rb") as f:
        dataset = pickle.load(f)

    lcm_config = LCMConfig(d_concept=space.d_concept, max_concept_seq=4)
    train_config = TrainConfig(batch_size=16, epochs=10)

    loader = DataLoader(dataset, batch_size=train_config.batch_size, shuffle=True)
    model = LatentReasoner(lcm_config)

    trainer = ConceptTrainer(model, train_config, loader)
    trainer.train()

if __name__ == "__main__":
    main()
"""

FILES["scripts/think.py"] = """import os
import pickle
import torch
from configs.config import LCMConfig
from src.model.reasoner import LatentReasoner
from src.model.decoder import ConceptDecoder
from src.reasoning.engine import ReasoningEngine

def main():
    if not os.path.exists("checkpoints/lcm_reasoner.pt"):
        print("[!] No hay checkpoint. Ejecuta primero: python -m scripts.train_reasoner")
        return

    with open("data/concept_space.pkl", "rb") as f:
        space = pickle.load(f)

    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    config = LCMConfig(d_concept=space.d_concept, max_concept_seq=4, device=device)

    model = LatentReasoner(config)
    ckpt = torch.load("checkpoints/lcm_reasoner.pt", map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])

    engine = ReasoningEngine(model, space, device=device)
    decoder = ConceptDecoder(space)

    print("=" * 65)
    print(f" LARGE CONCEPTUAL MODEL (LCM) - RAZONAMIENTO [{device.upper()}]")
    print("=" * 65)
    print("Conceptos disponibles:")
    print("  " + ", ".join(list(space.concept_to_id.keys())))
    print("\\nEscribe 2 o 3 conceptos (ej: MANZANA SOLTAR GRAVEDAD) o 'salir':\\n")

    while True:
        try:
            line = input("Premisa conceptual > ").strip().upper()
        except (KeyboardInterrupt, EOFError):
            break

        if line in ["SALIR", "EXIT", "QUIT"]:
            break
        if not line:
            continue

        premises = line.split()
        invalid = [p for p in premises if p not in space.concept_to_id]
        if invalid:
            print(f"[!] Conceptos no reconocidos: {invalid}")
            continue

        print("\\n[*] Razonando en el espacio latente continuo...")
        thought_vectors = engine.think(premises, steps=1)
        res_vector = thought_vectors[0]

        nearest_concept, cert = space.find_nearest_concept(res_vector)

        print("[OK] Pensamiento generado en memoria.")
        print(f"     ├── Dimension: {list(res_vector.shape)}")
        print(f"     ├── Vector muestra: [{res_vector[0]:.3f}, {res_vector[1]:.3f}, {res_vector[2]:.3f}...]")
        print(f"     └── Certeza del atractor: {cert*100:.2f}%")

        # La boca permanece inactiva a menos que se solicite
        opt = input("\\n¿Deseas verbalizar el pensamiento? [s/n]: ").strip().lower()
        if opt == "s":
            lang = input("  Idioma [es / en] (defecto es): ").strip().lower()
            lang = "en" if lang == "en" else "es"
            info = decoder.translate_thought(res_vector, lang=lang)
            print(f"\\n[BOCA / DECODER ({lang.upper()})]: \\\"{info['text']}\\\"")
            print(f"Concepto deducido: {info['concept']}")
        else:
            print("[*] El pensamiento permanece en silencio vectorial.")

if __name__ == "__main__":
    main()
"""

# -----------------------------------------------------------------------------
# EXPORTADOR COMPLETO
# -----------------------------------------------------------------------------
FILES["exportar.py"] = """import os
from pathlib import Path

OUTPUT_FILE = "LCM_PROYECTO_COMPLETO.txt"
IGNORED_DIRS = {".venv", "venv", "__pycache__", ".git", "checkpoints", "data"}
IGNORED_EXTS = {".pt", ".pkl", ".pyc", ".DS_Store"}

def build_tree(dir_path: Path, prefix: str = "") -> list:
    lines = []
    items = sorted([p for p in dir_path.iterdir() if p.name not in IGNORED_DIRS])
    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{item.name}")
        if item.is_dir():
            sub_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(build_tree(item, sub_prefix))
    return lines

def export():
    root = Path.cwd()
    print(f"[*] Empaquetando proyecto desde: {root}")

    out = []
    out.append("=" * 80)
    out.append(" PROYECTO LARGE CONCEPTUAL MODEL (LCM) - ARQUITECTURA Y FUENTE")
    out.append("=" * 80)
    out.append("\\nARBOL DE DIRECTORIOS:")
    out.append(root.name)
    out.extend(build_tree(root))
    out.append("\\n" + "=" * 80 + "\\n")

    count = 0
    for root_dir, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for fname in sorted(filenames):
            fp = Path(root_dir) / fname
            if fp.suffix in IGNORED_EXTS or fname in [OUTPUT_FILE, "expandir.py"]:
                continue
            rel = fp.relative_to(root)
            out.append("\\n" + "=" * 80)
            out.append(f"ARCHIVO: {rel}")
            out.append("=" * 80 + "\\n")
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    out.append(f.read())
                count += 1
            except Exception as e:
                out.append(f"[Error de lectura: {e}]")

    out_path = root / OUTPUT_FILE
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\\n".join(out))

    print(f"[+] {count} archivos empaquetados en: {OUTPUT_FILE}")
    print(f"[+] Peso total: {out_path.stat().st_size / 1024:.2f} KB")

if __name__ == "__main__":
    export()
"""

DIRECTORIES = [
    "configs",
    "data",
    "checkpoints",
    "scripts",
    "src",
    "src/ontology",
    "src/model",
    "src/training",
    "src/reasoning"
]

def main():
    root = Path.cwd()
    print(f"[*] Desplegando LCM en: {root}\\n")

    for d in DIRECTORIES:
        (root / d).mkdir(parents=True, exist_ok=True)
        print(f"  [Carpeta] -> {d}/")

    for rel_path, content in FILES.items():
        fp = root / rel_path
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [Archivo] -> {rel_path}")

    print("\\n" + "=" * 65)
    print(" DESPLIEGUE FINALIZADO CORRECTAMENTE")
    print("=" * 65)
    print("Pasos siguientes:")
    print("  1. python -m venv .venv && source .venv/bin/activate")
    print("  2. pip install -r requirements.txt")
    print("  3. python -m scripts.prepare_concepts")
    print("  4. python -m scripts.train_reasoner")
    print("  5. python -m scripts.think")
    print("  6. python exportar.py")

if __name__ == "__main__":
    main()