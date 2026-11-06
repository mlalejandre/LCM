"""El oido del LCM: del espanol a proposiciones (sujeto, predicado, objeto).

Es un modelo PEQUENO ENTRENADO (no un LLM, no reglas):
  - cada palabra se representa por su forma y sus trozos de letras, asi que
    palabras y nombres nunca vistos tambien tienen representacion;
  - un Transformer lee la frase entera;
  - una cabeza marca que palabra es el sujeto y cual el objeto (aprende el ORDEN:
    "Ana es madre de Luis" y "Luis tiene como madre a Ana" significan lo mismo);
  - el predicado se elige comparando la frase con la frase-etiqueta de cada
    predicado del catalogo ("padre de"). Como la comparacion es por palabras
    emparejadas, un predicado NUEVO se entiende sin reentrenar.
"""
from __future__ import annotations

import re
import zlib
from difflib import SequenceMatcher
from typing import Dict, List, Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F

from .lexicon import ES_ALIASES, NO_EAR, PREPS, norm, phrase_for, tokenize

# En MPS (Mac) el camino rapido de PyTorch para Transformers en inferencia no existe: se desactiva.
try:
    torch.backends.mha.set_fastpath_enabled(False)
except Exception:
    pass

STOPWORDS = set("el la los las un una unos unas que de a por con en y o no nunca jamas se sabe dicen es son fue ser siendo "
                "como segun ya muy mi su sus lo al del era eran fue fueron sera seran seria estaba estaban esta estan sido ha han habia".split()) | set(",.;:!?")

BUCKETS = 24000
GRAMS = 14
MAXLEN = 40


def _h(s: str) -> int:
    return zlib.crc32(s.encode()) % (BUCKETS - 1) + 1


_cache: Dict[str, List[int]] = {}


def word_features(w: str) -> List[int]:
    if w in _cache:
        return _cache[w]
    ids = [_h("w:" + w)]
    padded = f"<{w}>"
    for n in (3, 4, 5):
        for i in range(max(0, len(padded) - n + 1)):
            ids.append(_h(f"g{n}:" + padded[i:i + n]))
    ids = ids[:GRAMS] + [0] * (GRAMS - len(ids[:GRAMS]))
    _cache[w] = ids
    return ids


def key(w: str) -> str:
    """Raiz aproximada: 'causa'~'causado'~'causan', 'padre'~'padres'. Palabras cortas, enteras."""
    return w if len(w) <= 4 else w[:4]


def same_word(w: str, t: str) -> bool:
    """Misma palabra o variante cercana (padre~padres, causa~causado); 'contradice' ya no casa con 'contracayes'."""
    if w == t:
        return True
    return key(w) == key(t) and len(w) > 4 and SequenceMatcher(None, w, t).ratio() >= 0.8


def find_phrase(words, toks) -> int:
    n = len(words)
    for i in range(len(toks) - n + 1):
        if all(same_word(w, t) for w, t in zip(words, toks[i:i + n])):
            return i
    return -1


def word_id(w: str) -> int:
    return _h("w:" + key(w))


class Ear(nn.Module):
    def __init__(self, d: int = 128, layers: int = 2, heads: int = 4):
        super().__init__()
        self.d = d
        self.emb = nn.Embedding(BUCKETS, d, padding_idx=0)
        self.pos = nn.Embedding(MAXLEN, d)
        layer = nn.TransformerEncoderLayer(d, heads, 2 * d, dropout=0.1, batch_first=True)
        self.enc = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.tag = nn.Linear(d, 3)
        self.pred_vec = nn.Parameter(torch.randn(d) * 0.1)
        self.pol = nn.Linear(d, 1)
        self.scope = nn.Linear(d, 1)
        self.q = nn.Linear(d, d)
        self.k = nn.Linear(d, d)
        self.scale = nn.Parameter(torch.tensor(4.0))
        self.exact = nn.Parameter(torch.tensor(4.0))
        nn.init.normal_(self.emb.weight, std=0.1)
        with torch.no_grad():
            self.emb.weight[0].zero_()

    def embed(self, feat):                     # (..., G) -> (..., d)
        e = self.emb(feat).sum(-2)
        return e / (feat != 0).sum(-1, keepdim=True).clamp(min=1).sqrt()

    def forward(self, feat, mask, pmark=None, hide=None, extra=None):
        """pmark (B,T) bool: palabras de la relacion; se sustituyen por un marcador generico
        para que el orden de la frase no dependa de QUE relacion sea."""
        T = feat.shape[1]
        e = self.embed(feat)
        if hide is not None:                   # palabras ocultas (preentrenamiento): su vector se anula, queda solo la posicion
            e = e.masked_fill(hide[..., None], 0.0)
        if extra is not None:                  # rasgos adicionales por palabra (parche-34: mayusculas)
            e = e + extra
        if pmark is not None:
            e = torch.where(pmark[..., None], self.pred_vec.expand_as(e), e)
        x = e + self.pos(torch.arange(T, device=feat.device))[None]
        h = self.enc(x, src_key_padding_mask=~mask)
        return h, self.tag(h)

    def polarity(self, h, mask):
        m = mask[..., None].float()
        return self.pol((h * m).sum(1) / m.sum(1).clamp(min=1)).squeeze(-1)    # logit de "negada"

    def in_scope(self, h, mask):
        m = mask[..., None].float()
        return self.scope((h * m).sum(1) / m.sum(1).clamp(min=1)).squeeze(-1)  # logit: "afirma una relacion"

    def mark(self, tok_ids, phrase_ids):
        """tok_ids (B,T), phrase_ids (B,W) con -1 de relleno -> (B,T) bool"""
        return (tok_ids[:, :, None] == phrase_ids[:, None, :]).any(-1)

    def score(self, h, mask, tok_ids, cand_feat, cand_mask, cand_ids):
        qh = F.normalize(self.q(h), dim=-1)                        # (B,T,d)
        kc = F.normalize(self.k(self.embed(cand_feat)), dim=-1)    # (C,W,d)
        sim = torch.einsum("btd,cwd->bcwt", qh, kc)
        exact = (tok_ids[:, None, None, :] == cand_ids[None, :, :, None]).float()
        s = self.scale * sim + self.exact * exact
        s = s.masked_fill(~mask[:, None, None, :], -1e4).max(-1).values          # (B,C,W)
        cm = cand_mask[None].float()
        return (s * cm).sum(-1) / cm.sum(-1)


def encode_batch(sentences: Sequence[Sequence[str]], device="cpu"):
    T = min(MAXLEN, max(len(s) for s in sentences))
    feat = torch.zeros(len(sentences), T, GRAMS, dtype=torch.long)
    ids = torch.zeros(len(sentences), T, dtype=torch.long)
    mask = torch.zeros(len(sentences), T, dtype=torch.bool)
    for i, toks in enumerate(sentences):
        for j, w in enumerate(toks[:T]):
            feat[i, j] = torch.tensor(word_features(w))
            ids[i, j] = word_id(w)
            mask[i, j] = True
    return feat.to(device), ids.to(device), mask.to(device)


def encode_candidates(phrases: Sequence[str], device="cpu"):
    toks = [tokenize(p) for p in phrases]
    W = max(len(t) for t in toks)
    feat = torch.zeros(len(toks), W, GRAMS, dtype=torch.long)
    ids = torch.full((len(toks), W), -1, dtype=torch.long)
    mask = torch.zeros(len(toks), W, dtype=torch.bool)
    for i, t in enumerate(toks):
        for j, w in enumerate(t):
            feat[i, j] = torch.tensor(word_features(w))
            ids[i, j] = word_id(w)
            mask[i, j] = True
    return feat.to(device), mask.to(device), ids.to(device)


@torch.no_grad()
def predict(ear: Ear, token_lists: Sequence[Sequence[str]], candidates: Sequence[tuple], device="cpu", chunk: int = 128):
    """candidates: lista de (nombre_predicado, frase). Devuelve un dict por oracion."""
    ear.eval()
    valid = [i for i, t in enumerate(token_lists) if len([w for w in t if w not in ",.;:!?"]) >= 3]
    if len(valid) < len(token_lists):          # frases vacias o de 1-2 palabras: se rechazan sin pasar por el modelo
        sub = predict(ear, [token_lists[i] for i in valid], candidates, device, chunk) if valid else []
        res = {i: sub[k] for k, i in enumerate(valid)}
        return [res.get(i) or {"subject": "", "predicate": "", "object": "", "phrase": "", "negated": False,
                               "confidence": 0.0, "in_scope": 0.0, "tokens": list(token_lists[i])}
                for i in range(len(token_lists))]
    out = []
    texts = [t for _, t in candidates]
    cf, cm, ci = encode_candidates(texts, device)
    for a in range(0, len(token_lists), chunk):
        part = token_lists[a:a + chunk]
        feat, ids, mask = encode_batch(part, device)
        h, _ = ear(feat, mask)
        scores = ear.score(h, mask, ids, cf, cm, ci)
        for b, toks in enumerate(part):          # bonus: la frase-etiqueta aparece seguida, en orden
            for c, (_, text) in enumerate(candidates):
                ws = tokenize(text)
                if find_phrase(ws, toks) >= 0:
                    scores[b, c] += 0.3 + 0.05 * len(ws)
                    if any(list(toks[i:i + len(ws)]) == ws for i in range(len(toks) - len(ws) + 1)):
                        scores[b, c] += 0.3          # coincidencia exacta mejor que solo por raiz
        probs = F.softmax(scores * 6.0, dim=-1)
        top = probs.argmax(-1)
        pol = torch.sigmoid(ear.polarity(h, mask))
        scope = torch.sigmoid(ear.in_scope(h, mask))
        _, tags = ear(feat, mask, ear.mark(ids, ci[top]))
        tags = F.log_softmax(tags, dim=-1)
        for b, toks in enumerate(part):
            m = mask[b] & torch.tensor([t not in STOPWORDS for t in toks] + [False] * (mask.shape[1] - len(toks)),
                                       device=mask.device)[:mask.shape[1]]
            if m.sum() < 2:
                m = mask[b]
            m = m & torch.tensor(_not_in_relative(toks) + [False] * (mask.shape[1] - len(toks)), device=mask.device)[:mask.shape[1]] \
                if m.sum() > 2 else m
            s_i = _np_head(toks, int(tags[b, :, 1].masked_fill(~m, -1e4).argmax()))
            o_lg = tags[b, :, 2].masked_fill(~m, -1e4).clone()
            o_lg[s_i] = -1e4
            o_i = _np_head(toks, int(o_lg.argmax()))
            name, text = candidates[int(top[b])]
            conf = float(probs[b, top[b]])
            words = tokenize(text)
            need = words[:-1] if len(words) >= 2 and words[-1] in PREPS else words    # 'padre de': basta 'padre'
            if not all(any(same_word(w, t) for t in toks) for w in need):
                conf = 0.0                      # la relacion elegida no aparece en la frase
            subj, obj = toks[s_i], toks[o_i]
            if name == "ES":                    # "S es un O": orden obligatorio y giro seguido
                start = find_phrase(words, toks)
                if start < 0 or not (s_i < start and o_i >= start + len(words)):
                    conf = 0.0
                if text in ("son", "eran") and not (subj.endswith("s") and obj.endswith("s")):
                    conf = 0.0
            conf *= float(scope[b])
            if "?" in toks:
                conf = 0.0                          # una pregunta no es una afirmacion
            if text in ("son", "eran"):
                subj, obj = singular(subj), singular(obj)
            out.append({"subject": subj.upper(), "predicate": name, "object": obj.upper(), "phrase": text,
                        "negated": bool(pol[b] > 0.5), "confidence": conf, "in_scope": float(scope[b]), "tokens": list(toks)})
    return out


ARTICLES = {"el", "la", "los", "las", "un", "una", "unos", "unas"}


def _np_head(toks, i):
    """'el viento capaz': si se elige el adjetivo, el nucleo es la palabra que sigue al articulo."""
    if i >= 2 and toks[i - 2] in ARTICLES and toks[i - 1] not in STOPWORDS:
        return i - 1
    return i


def _not_in_relative(toks):
    """False dentro de incisos ', que ... ,' (clausulas relativas: no contienen sujeto ni objeto)."""
    keep, inside = [], False
    for i, t in enumerate(toks):
        if inside and t == ",":
            inside = False
            keep.append(False)
            continue
        if t == "," and i + 1 < len(toks) and toks[i + 1] == "que":
            inside = True
        keep.append(not inside)
    return keep


def singular(w: str) -> str:
    if w.endswith("es") and len(w) > 3 and w[-3] not in "aeiou":
        return w[:-2]
    return w[:-1] if w.endswith("s") else w


class EarParser:
    """Usa un Ear entrenado con el catalogo vivo de predicados del LCM."""

    def __init__(self, ear: Ear, device="cpu", min_conf: float = 0.8):
        self.ear = ear.to(device).eval()
        self.device = device
        self.min_conf = min_conf

    def candidates(self, space) -> List[tuple]:
        out = [(n, phrase_for(n)[0]) for n, m in space.metadata.items()
               if m.get("kind") == "predicate" and n not in NO_EAR]
        if "ES" in space.concept_to_id:
            out += [("ES", a) for a in ES_ALIASES]
        return out

    def parse(self, sentence: str, candidates: Sequence[tuple]):
        toks = tokenize(sentence)
        if len([t for t in toks if t not in ",.;:!?"]) < 3:
            return None
        return predict(self.ear, [toks], candidates, self.device)[0]
