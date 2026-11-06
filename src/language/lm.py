"""Preentrenamiento del oido con TEXTO CORRIENTE (parche-26): adivinar palabras ocultas.

Como el "siguiente token" de un LLM, pero bidireccional: se oculta ~15 % de las palabras de cada frase del libro y
el oido debe adivinarlas a partir del resto. Para hacerlo tiene que aprender que palabras se parecen, que clase
de palabra va en cada hueco (nombre, verbo, adjetivo...) y como se ordena el espanol. No necesita etiquetas.
"""
from __future__ import annotations

import json
import os
import random
import zlib
from collections import Counter
from typing import List, Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F

from .book import sentences
from .ear import MAXLEN, encode_batch
from .lexicon import tokenize

PUNCT = set(",.;:!?")


def load_sentences(path="data/libro.txt", min_tokens=5, max_tokens=MAXLEN - 2) -> List[List[str]]:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    out = []
    for s in sentences(text, max_words=30):
        t = tokenize(s)
        if min_tokens <= len(t) <= max_tokens:
            out.append(t)
    return out


def is_heldout(tokens: Sequence[str]) -> bool:
    return zlib.crc32(" ".join(tokens).encode()) % 10 == 0          # 10 % de las frases, fijo y reproducible


def build_vocab(train: Sequence[Sequence[str]], size=8000, min_count=2) -> List[str]:
    c = Counter(w for t in train for w in t if w not in PUNCT)
    return [w for w, n in c.most_common(size) if n >= min_count]


class LMHead(nn.Module):
    """Adivina la palabra oculta entre las V mas frecuentes del libro (las demas no puntuan)."""

    def __init__(self, d: int, vocab: Sequence[str]):
        super().__init__()
        self.vocab = list(vocab)
        self.index = {w: i for i, w in enumerate(self.vocab)}
        self.proj = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.Linear(d, len(self.vocab)))

    def forward(self, h):
        return self.proj(h)

    def save(self, path):
        torch.save({"vocab": self.vocab, "state": self.state_dict()}, path)

    @staticmethod
    def load(path, d, device="cpu"):
        blob = torch.load(path, map_location="cpu")
        head = LMHead(d, blob["vocab"])
        head.load_state_dict(blob["state"])
        return head.to(device)


def mask_batch(batch: Sequence[Sequence[str]], head: LMHead, rng: random.Random, p=0.15, device="cpu"):
    feat, ids, mask = encode_batch(batch, device)
    B, T = mask.shape
    hide = torch.zeros(B, T, dtype=torch.bool)
    target = torch.full((B, T), -100, dtype=torch.long)
    for i, toks in enumerate(batch):
        cand = [j for j, w in enumerate(toks[:T]) if w not in PUNCT]
        k = max(1, int(round(p * len(cand))))
        for j in rng.sample(cand, min(k, len(cand))):
            hide[i, j] = True
            target[i, j] = head.index.get(toks[j], -100)
    return feat, mask, hide.to(device), target.to(device)


def lm_loss(ear, head: LMHead, batch, rng, device="cpu", p=0.15):
    feat, mask, hide, target = mask_batch(batch, head, rng, p, device)
    h, _ = ear(feat, mask, hide=hide)
    logits = head(h)
    if (target != -100).sum() == 0:
        return logits.sum() * 0.0, 0, 0
    sel = target != -100
    loss = F.cross_entropy(logits[sel], target[sel])
    acc = (logits[sel].argmax(-1) == target[sel]).float().mean().item()
    return loss, acc, int(sel.sum())


@torch.no_grad()
def evaluate(ear, head, data, device="cpu", seed=123, batch=128, rounds=3):
    """Acierto (top-1 y top-5) adivinando palabras ocultas de frases NO vistas, y la linea base 'siempre la mas frecuente'."""
    ear.eval()
    rng = random.Random(seed)
    top1 = top5 = n = 0
    for _ in range(rounds):
        for b in range(0, len(data), batch):
            feat, mask, hide, target = mask_batch(data[b:b + batch], head, rng, 0.15, device)
            h, _ = ear(feat, mask, hide=hide)
            sel = target != -100
            if sel.sum() == 0:
                continue
            lg = head(h)[sel]
            tg = target[sel]
            top1 += (lg.argmax(-1) == tg).sum().item()
            top5 += (lg.topk(5, dim=-1).indices == tg[:, None]).any(-1).sum().item()
            n += len(tg)
    return top1 / max(n, 1), top5 / max(n, 1), n
