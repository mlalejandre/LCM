"""Analizador sintáctico ENTRENADO (no reglas): para cada palabra aprende su categoría (determinante, preposición, verbo…), de qué palabra
depende y con qué función (sujeto, objeto, complemento…). Aprende de frases analizadas a mano; no sabe hechos del mundo, solo gramática.

Red pequeña: cada palabra entra como su vector + los de su principio y su final (así generaliza a palabras que no ha visto: «-aron» es verbo),
una capa recurrente en los dos sentidos lee la frase entera, y tres salidas: categoría, cabeza (biafín) y función."""
from __future__ import annotations

import torch
import torch.nn as nn


def _h(s, n):
    return (hash(s) % (n - 1)) + 1 if s else 0


def _hs(s, n):                                           # hash estable (el de Python cambia entre ejecuciones)
    v = 2166136261
    for ch in s.encode("utf-8"):
        v = ((v ^ ch) * 16777619) & 0xFFFFFFFF
    return (v % (n - 1)) + 1


class Vocab:
    def __init__(self, palabras, upos, rels):
        self.w = {w: i + 2 for i, w in enumerate(palabras)}   # 0 relleno, 1 desconocida
        self.upos = list(upos)
        self.rels = list(rels)
        self.u2i = {u: i for i, u in enumerate(self.upos)}
        self.r2i = {r: i for i, r in enumerate(self.rels)}

    NB = 4000

    def rasgos(self, forma):
        f = forma.lower()
        f = "0" if f[:1].isdigit() else f
        return [self.w.get(f, 1), _hs("s2" + f[-2:], self.NB), _hs("s3" + f[-3:], self.NB), _hs("s4" + f[-4:], self.NB), _hs("p3" + f[:3], self.NB),
                (2 if forma.isupper() and len(forma) > 1 else 1 if forma[:1].isupper() else 3 if not forma[:1].isalpha() else 0) + 1]


class Analizador(nn.Module):
    def __init__(self, nw, nu, nr, dw=100, h=200, da=200, dl=100, nb=Vocab.NB):
        super().__init__()
        self.ew = nn.Embedding(nw + 2, dw, padding_idx=0)
        self.eb = nn.ModuleList([nn.Embedding(nb, 30, padding_idx=0) for _ in range(4)])
        self.ec = nn.Embedding(6, 8, padding_idx=0)
        self.raiz = nn.Parameter(torch.zeros(1, 1, 2 * h))
        self.lstm = nn.LSTM(dw + 120 + 8, h, num_layers=2, bidirectional=True, batch_first=True, dropout=0.3)
        self.drop = nn.Dropout(0.33)
        self.tag = nn.Linear(2 * h, nu)
        self.dep = nn.Sequential(nn.Linear(2 * h, da), nn.ReLU())
        self.cab = nn.Sequential(nn.Linear(2 * h, da), nn.ReLU())
        self.bil = nn.Parameter(torch.zeros(da + 1, da))
        nn.init.xavier_uniform_(self.bil)
        self.ldep = nn.Sequential(nn.Linear(2 * h, dl), nn.ReLU())
        self.lcab = nn.Sequential(nn.Linear(2 * h, dl), nn.ReLU())
        self.lab = nn.Linear(2 * dl, nr)

    def codifica(self, X):
        """X: [lote, n, 6] -> estados [lote, n+1, 2h] (posición 0 = raíz)."""
        e = torch.cat([self.ew(X[..., 0])] + [self.eb[i](X[..., i + 1]) for i in range(4)] + [self.ec(X[..., 5])], -1)
        o, _ = self.lstm(self.drop(e))
        o = self.drop(o)
        return torch.cat([self.raiz.expand(o.size(0), 1, -1), o], 1)

    def forward(self, X):
        H = self.codifica(X)
        tags = self.tag(H[:, 1:])
        d = self.dep(H[:, 1:])
        c = self.cab(H)
        d1 = torch.cat([d, torch.ones_like(d[..., :1])], -1)
        arcos = torch.einsum("bid,de,bje->bij", d1, self.bil, c)        # [lote, n, n+1]: palabra i -> cabeza j
        return H, tags, arcos

    def funciones(self, H, cabezas):
        """La función de cada palabra dada su cabeza. cabezas: [lote, n] (0 = raíz)."""
        ld = self.ldep(H[:, 1:])
        lc = self.lcab(H)
        lc = torch.gather(lc, 1, cabezas.unsqueeze(-1).expand(-1, -1, lc.size(-1)))
        return self.lab(torch.cat([ld, lc], -1))
