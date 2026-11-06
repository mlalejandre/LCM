"""Escuela de espanol (parche-30/34): aprender SINTAXIS con frases reales anotadas (Universal Dependencies).

Cada palabra lleva: categoria (UPOS), de que palabra depende (head), con que funcion (deprel) y su forma base (lema).
v2 (parche-34): rasgo de MAYUSCULA por palabra (Pedro / pedro) y cabeza de LEMA (escribio -> escribir) por "guion de edicion":
(cuantas letras quitar del final, que letras anadir).
"""
from __future__ import annotations

import glob
import json
import os
from collections import Counter
from typing import List, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .ear import MAXLEN, Ear, encode_batch
from .lexicon import norm

Word = Tuple[str, str, int, str, str]            # (forma, upos, head, deprel, lemma)
UPOS = ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB", "X"]
REL = ["acl", "advcl", "advmod", "amod", "appos", "aux", "case", "cc", "ccomp", "compound", "conj", "cop", "csubj", "dep", "det", "discourse",
       "dislocated", "expl", "fixed", "flat", "goeswith", "iobj", "mark", "nmod", "nsubj", "nummod", "obj", "obl", "orphan", "parataxis",
       "punct", "reparandum", "root", "vocative", "xcomp"]
META = "checkpoints/school_meta.json"


def token_of(form: str) -> str:
    t = norm(form).replace(" ", "_")
    return t if t.strip() else form


def cap_of(form: str, i: int) -> int:
    """0 minuscula, 1 mayuscula inicial en mitad de frase (nombre propio probable), 2 mayuscula por inicio de frase o siglas."""
    if not form[:1].isalpha():
        return 0
    if form.isupper() and len(form) > 1:
        return 2
    if form[:1].isupper():
        return 2 if i == 0 else 1
    return 0


def _clean(s: str) -> str:
    return norm(s).replace(" ", "_")


def edit_script(form: str, lemma: str) -> Tuple[int, str]:
    a, b = _clean(form), _clean(lemma)
    p = 0
    while p < min(len(a), len(b)) and a[p] == b[p]:
        p += 1
    return len(a) - p, b[p:]


def apply_script(form: str, script: Sequence) -> str:
    a = _clean(form)
    cut, add = int(script[0]), str(script[1])
    return (a[:len(a) - cut] if cut <= len(a) else a) + add


def build_scripts(sents: Sequence[Sequence[Word]], top: int = 600) -> List[list]:
    c = Counter(edit_script(w[0], w[4]) for s in sents for w in s if w[1] != "PUNCT")
    return [[k, v] for (k, v), _ in c.most_common(top)]


def read_conllu(path: str, max_len: int = MAXLEN) -> Tuple[List[List[Word]], int]:
    """Devuelve (frases de <= max_len palabras, numero de frases omitidas por largas). Usa palabras sintacticas (del = de + el)."""
    sents, cur, skipped = [], [], 0

    def close():
        nonlocal cur, skipped
        if cur:
            if len(cur) <= max_len:
                sents.append(cur)
            else:
                skipped += 1
        cur = []

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                close()
                continue
            if line.startswith("#"):
                continue
            c = line.split("\t")
            if len(c) < 8 or "-" in c[0] or "." in c[0]:
                continue                                  # rangos (del = de+el) y nodos vacios
            rel = c[7].split(":")[0]
            cur.append((c[1], c[3] if c[3] in UPOS else "X", int(c[6]), rel if rel in REL else "dep", c[2]))
    close()
    return sents, skipped


def find_files(split: str, root: str = "data/ud") -> List[str]:
    return sorted(glob.glob(os.path.join(root, "*", f"*-ud-{split}.conllu")))


class School(nn.Module):
    """Encoder del oido + cabezas de categoria, dependencia (a quien se une), funcion y lema."""

    def __init__(self, ear: Ear | None = None, n_scripts: int = 0):
        super().__init__()
        self.ear = ear or Ear()
        d = self.ear.d
        self.upos = nn.Linear(d, len(UPOS))
        self.root = nn.Parameter(torch.randn(d) * 0.1)
        self.aq = nn.Linear(d, d)
        self.ak = nn.Linear(d, d)
        self.rel = nn.Sequential(nn.Linear(2 * d, d), nn.GELU(), nn.Linear(d, len(REL)))
        self.cap_emb = nn.Embedding(3, d)
        nn.init.zeros_(self.cap_emb.weight)               # arranca sin efecto: un checkpoint antiguo se comporta igual
        self.lemma = nn.Linear(d, n_scripts) if n_scripts else None

    def forward(self, feat, mask, cap=None):
        extra = self.cap_emb(cap) if cap is not None else None
        h, _ = self.ear(feat, mask, extra=extra)
        B, T, d = h.shape
        keys = torch.cat([self.root.expand(B, 1, d), h], 1)                       # posicion 0 = raiz
        arc = torch.einsum("bid,bjd->bij", self.aq(h), self.ak(keys)) / d ** 0.5
        kmask = torch.cat([torch.ones(B, 1, dtype=torch.bool, device=mask.device), mask], 1)
        arc = arc.masked_fill(~kmask[:, None, :], -1e4)
        eye = torch.eye(T, dtype=torch.bool, device=mask.device)
        arc[:, :, 1:] = arc[:, :, 1:].masked_fill(eye[None], -1e4)                  # una palabra no depende de si misma
        return h, self.upos(h), arc

    def rel_logits(self, h, heads):
        B, T, d = h.shape
        keys = torch.cat([self.root.expand(B, 1, d), h], 1)
        head_h = keys.gather(1, heads[..., None].expand(-1, -1, d))
        return self.rel(torch.cat([h, head_h], -1))


def save_school(model: School, scripts: Sequence, path="checkpoints/school.pt", meta=META):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    torch.save(model.state_dict(), path)
    json.dump(scripts, open(meta, "w"))


def load_school(path="checkpoints/school.pt", meta=META, device="cpu"):
    """Devuelve (modelo, guiones de lema). Funciona tambien con checkpoints antiguos (sin lema ni mayusculas)."""
    scripts = json.load(open(meta)) if os.path.exists(meta) else []
    state = torch.load(path, map_location="cpu")
    if "lemma.weight" not in state:
        scripts = []
    model = School(n_scripts=len(scripts))
    model.load_state_dict(state, strict=False)
    return model.to(device).eval(), scripts


def _tensors(forms_batch: Sequence[Sequence[str]], device):
    feat, _, mask = encode_batch([[token_of(w) for w in s] for s in forms_batch], device)
    B, T = mask.shape
    cap = torch.zeros(B, T, dtype=torch.long)
    for i, s in enumerate(forms_batch):
        for j, w in enumerate(s[:T]):
            cap[i, j] = cap_of(w, j)
    return feat, mask, cap.to(device)


def to_tensors(batch: Sequence[Sequence[Word]], device="cpu", scripts=None):
    feat, mask, cap = _tensors([[w[0] for w in s] for s in batch], device)
    B, T = mask.shape
    upos = torch.full((B, T), -100, dtype=torch.long)
    head = torch.full((B, T), -100, dtype=torch.long)
    rel = torch.full((B, T), -100, dtype=torch.long)
    lem = torch.full((B, T), -100, dtype=torch.long)
    index = {(int(a), str(b)): k for k, (a, b) in enumerate(scripts)} if scripts else {}
    for i, s in enumerate(batch):
        for j, w in enumerate(s[:T]):
            upos[i, j], head[i, j], rel[i, j] = UPOS.index(w[1]), w[2], REL.index(w[3])
            if index:
                lem[i, j] = index.get(edit_script(w[0], w[4]), -100)
    return feat, mask, cap, upos.to(device), head.to(device), rel.to(device), lem.to(device)


def school_loss(model: School, batch, device="cpu", scripts=None):
    feat, mask, cap, upos, head, rel, lem = to_tensors(batch, device, scripts)
    h, lu, arc = model(feat, mask, cap)
    l_u = F.cross_entropy(lu.reshape(-1, lu.shape[-1]), upos.reshape(-1), ignore_index=-100)
    l_h = F.cross_entropy(arc.reshape(-1, arc.shape[-1]), head.reshape(-1), ignore_index=-100)
    lr = model.rel_logits(h, head.clamp(min=0))
    l_r = F.cross_entropy(lr.reshape(-1, lr.shape[-1]), rel.reshape(-1), ignore_index=-100)
    loss, parts = l_u + l_h + l_r, [l_u.item(), l_h.item(), l_r.item()]
    if model.lemma is not None and (lem != -100).any():
        ll = model.lemma(h)
        l_l = F.cross_entropy(ll.reshape(-1, ll.shape[-1]), lem.reshape(-1), ignore_index=-100)
        loss = loss + l_l
        parts.append(l_l.item())
    return loss, tuple(parts)


@torch.no_grad()
def predict_trees(model: School, sents: Sequence[Sequence[str]], device="cpu", scripts=None, chunk=128):
    """sents: listas de formas. Devuelve por frase una lista de (upos, head, deprel, lema)."""
    model.eval()
    out = []
    with torch.no_grad():
        for b in range(0, len(sents), chunk):
            part = sents[b:b + chunk]
            feat, mask, cap = _tensors(part, device)
            h, lu, arc = model(feat, mask, cap)
            heads = arc.argmax(-1)
            rels = model.rel_logits(h, heads).argmax(-1)
            pos = lu.argmax(-1)
            lem = model.lemma(h).argmax(-1) if (model.lemma is not None and scripts) else None
            # una sola copia a la CPU por lote (leer tensor a tensor desde MPS/GPU era lentisimo)
            heads_l, rels_l, pos_l = heads.cpu().tolist(), rels.cpu().tolist(), pos.cpu().tolist()
            lem_l = lem.cpu().tolist() if lem is not None else None
            for i, s in enumerate(part):
                row = []
                for j, form in enumerate(s):
                    lemma = apply_script(form, scripts[lem_l[i][j]]) if lem_l is not None else token_of(form)
                    row.append((UPOS[pos_l[i][j]], heads_l[i][j], REL[rels_l[i][j]], lemma))
                out.append(row)
    return out
