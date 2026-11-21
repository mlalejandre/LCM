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
    """Las palabras de contenido de una frase, en su forma de diccionario (las mismas que usan los vectores de tema)."""
    from . import tema as T
    return T.lemas(texto)


def apunta(nuc, texto, entidades=(), deducida=False):
    """Guarda lo que se acaba de decir. La caché es corta a propósito.
    2.31: con deducida=True la persona no la nombró el usuario: la eligió el modelo entre tocayos. Cuenta la mitad, para que una elección
    suya no pese lo mismo que lo que el usuario dice después con todas las letras."""
    c = _cache(nuc)
    t = nuc.turno
    _NUC[0] = nuc
    for l in dict.fromkeys(lemas(texto)):
        c.append((t, "w", l))
    for e in dict.fromkeys(entidades):
        if e and e not in ("U", "L"):
            c.append((t, "e", e, 0.5) if deducida and not os.environ.get("LCM_SIN_CLASE") else (t, "e", e))
    c[:] = [x for x in c if t - x[0] <= VENTANA][-MAXIMO:]


def peso_entidad(nuc, e):
    t = nuc.turno
    return max(((x[3] if len(x) > 3 else 1.0) * OLVIDO ** max(0, t - x[0]) for x in _cache(nuc) if x[1] == "e" and x[2] == e and t - x[0] <= VENTANA), default=0.0)   # cuenta la última vez que se habló de él


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


_NUC = [None]                                           # el conversador de ahora, para la capa de tema del usuario


def parecido(a, b):
    """Cuánto tienen que ver dos palabras: 1 si son la misma; si no, lo que digan los vectores de sinonimia (léxico) o los de TEMA
    (aprendidos leyendo y conversando, 2.30): «tubería» y «fontanero» no significan lo mismo, pero van juntas."""
    if a == b or (len(a) > 4 and len(b) > 4 and a[:5] == b[:5]):
        return 1.0
    s = 0.0
    try:
        from . import vectores as V
        s = V.sim(a, b)
        s = s if s >= 0.45 else 0.0
    except Exception:                                    # noqa
        s = 0.0
    try:
        from . import tema as T
        t = T.tema(_NUC[0], a, b)
        for a2, b2 in ((a, b[:-1] + "o"), (a[:-1] + "o", b)):   # «veterinaria» va con lo que va «veterinario»
            if (b2 != b and len(b) > 5 and b.endswith("a")) or (a2 != a and len(a) > 5 and a.endswith("a")):
                t = max(t, T.tema(_NUC[0], a2, b2))
        if t >= 0.25:
            s = max(s, 0.9 * t)
    except Exception:                                    # noqa
        pass
    return s


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
