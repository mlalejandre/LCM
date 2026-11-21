"""Lectura del corpus analizado a mano (Universal Dependencies, español) y preparación de las frases."""
from __future__ import annotations

import re


def lee_conllu(ruta):
    """[[(forma, upos, cabeza, relación)]] una lista por frase. Se saltan los rangos (1-2 «del») y los nodos vacíos (1.1)."""
    frases, act = [], []
    with open(ruta, encoding="utf-8") as fh:
        for l in fh:
            l = l.rstrip("\n")
            if not l:
                if act:
                    frases.append(act)
                act = []
                continue
            if l[0] == "#":
                continue
            c = l.split("\t")
            if "-" in c[0] or "." in c[0]:
                continue
            act.append((c[1], c[3], int(c[6]), c[7].split(":")[0]))
    if act:
        frases.append(act)
    return frases


_CONTR = {"del": ("de", "el"), "al": ("a", "el")}


def trocea(texto):
    """Texto -> palabras como las del corpus: signos aparte, «del» = «de el», «al» = «a el»."""
    out = []
    for w in re.findall(r"\d+(?:[.,]\d+)*|[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+|[^\sA-Za-zÁÉÍÓÚÜÑáéíóúüñ\d]", texto):
        c = _CONTR.get(w.lower())
        if c:
            out.append(c[0].capitalize() if w[0].isupper() else c[0])
            out.append(c[1])
        else:
            out.append(w)
    return out


def frases_de(texto):
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+", texto.strip()) if f.strip()]


TRAMOS = [(1, 5), (6, 10), (11, 20), (21, 40), (41, 999)]


def tramo(n):
    for a, b in TRAMOS:
        if a <= n <= b:
            return f"{a}-{b}" if b < 999 else f"{a}+"
