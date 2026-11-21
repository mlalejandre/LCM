"""LCM 2.29 · CONTEXTO: una caché corta de lo último que se ha hablado, y probabilidades a partir de ella.

Cuando un nombre lleva a varios nodos (dos Pedros, los sentidos de «copa»), lo más probable es el que casa con lo que se venía diciendo.
Aquí se guarda eso, y poco: las entidades y las palabras de contenido de los últimos turnos, con un peso que decae en cada turno. Con ello
se da una PROBABILIDAD a cada candidato; si la del mejor es alta se elige sin molestar, y si no, se pregunta.
"""
from __future__ import annotations

import os
import re

from .morfo import sa
from . import morfo as M

VENTANA = 6          # turnos que se recuerdan
MAXIMO = 40          # apuntes como mucho
OLVIDO = 0.5         # lo que pesa un apunte por cada turno que pasa
SEGURO = 0.70        # a partir de aquí se elige sin preguntar (en una pregunta)
SEGURO_DICHO = 0.80  # …y algo más si lo que se dice va a quedar guardado
PREVIO = 0.10        # lo que vale un candidato del que el contexto no dice nada


def _cache(nuc):
    c = getattr(nuc, "_cache229", None)
    if c is None:
        c = nuc._cache229 = []
    return c


def lemas(texto):
    """Las palabras de contenido de una frase, en su forma de diccionario."""
    from . import lectura as L
    out = []
    for w in re.findall(r"[a-záéíóúñü]+", (texto or "").lower()):
        if sa(w) in L._VACIAS or len(w) < 3:
            continue
        try:
            an = M.analizar(w) or []
        except Exception:                                # noqa
            an = []
        l = next((a[0] for a in an if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut", "inf", "part", "ger")), None)
        out.append(sa(l) if l else sa(M.singular(w)))
    return out


def apunta(nuc, texto, entidades=()):
    """Guarda lo que se acaba de decir. La caché es corta a propósito."""
    c = _cache(nuc)
    t = nuc.turno
    for l in dict.fromkeys(lemas(texto)):
        c.append((t, "w", l))
    for e in dict.fromkeys(entidades):
        if e and e not in ("U", "L"):
            c.append((t, "e", e))
    c[:] = [x for x in c if t - x[0] <= VENTANA][-MAXIMO:]


def peso_entidad(nuc, e):
    t = nuc.turno
    return max((OLVIDO ** max(0, t - x[0]) for x in _cache(nuc) if x[1] == "e" and x[2] == e and t - x[0] <= VENTANA), default=0.0)   # cuenta la última vez que se habló de él


def palabras(nuc, frase=""):
    """{palabra: peso}: las de la frase de ahora valen 1; las de antes, menos cuanto más atrás."""
    t = nuc.turno
    out = {}
    for x in _cache(nuc):
        if x[1] == "w" and t - x[0] <= VENTANA:
            out[x[2]] = max(out.get(x[2], 0.0), 0.7 * OLVIDO ** max(0, t - x[0]))
    for l in lemas(frase):
        out[l] = 1.0
    return out


def parecido(a, b):
    """Cuánto se parecen dos palabras: 1 si son la misma, y si no lo que digan los vectores del léxico (0 si poco)."""
    if a == b or (len(a) > 4 and len(b) > 4 and a[:5] == b[:5]):
        return 1.0
    try:
        from . import vectores as V
        s = V.sim(a, b)
        return s if s >= 0.45 else 0.0
    except Exception:                                    # noqa
        return 0.0


def casa(ctx, bolsa):
    """Cuánto apoya un contexto {palabra: peso} a una bolsa de palabras."""
    if not bolsa:
        return 0.0
    return sum(w * max((parecido(c, b) for b in bolsa), default=0.0) for c, w in ctx.items())


def reparte(puntos, previos=None):
    """De puntos a probabilidades."""
    previos = previos or [PREVIO] * len(puntos)
    tot = sum(p + q for p, q in zip(puntos, previos)) or 1.0
    return [(p + q) / tot for p, q in zip(puntos, previos)]


def apagado():
    return bool(os.environ.get("LCM_SIN_CONTEXTO"))
