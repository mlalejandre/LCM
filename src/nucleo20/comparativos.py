"""LCM 2.13 · COMPARACIONES SUPUESTAS.

«si un conejo es más grande que una liebre, ¿la liebre será más pequeña o más grande que el conejo?»
Cada adjetivo comparativo es un sentido sobre una escala (grande + / pequeño − sobre «tamaño»). Las relaciones supuestas
forman un orden (transitivo) sobre cada escala, y la pregunta se contesta por ese orden: no hace falta saber nada del mundo,
solo qué significa «más grande» y que su contrario es «más pequeño».
"""
from __future__ import annotations

import re

from .morfo import sa

# adjetivo (masculino singular) -> (escala, sentido)
ESCALAS = {
    "grande": ("tamaño", 1), "pequeño": ("tamaño", -1), "chico": ("tamaño", -1),
    "alto": ("altura", 1), "bajo": ("altura", -1),
    "rápido": ("velocidad", 1), "veloz": ("velocidad", 1), "lento": ("velocidad", -1),
    "pesado": ("peso", 1), "ligero": ("peso", -1), "liviano": ("peso", -1),
    "viejo": ("edad", 1), "mayor": ("edad", 1), "anciano": ("edad", 1), "joven": ("edad", -1), "menor": ("edad", -1), "nuevo": ("edad", -1),
    "caro": ("precio", 1), "barato": ("precio", -1),
    "largo": ("longitud", 1), "corto": ("longitud", -1),
    "ancho": ("anchura", 1), "estrecho": ("anchura", -1),
    "fuerte": ("fuerza", 1), "débil": ("fuerza", -1), "debil": ("fuerza", -1),
    "gordo": ("grosor", 1), "grueso": ("grosor", 1), "delgado": ("grosor", -1), "flaco": ("grosor", -1), "fino": ("grosor", -1),
    "caliente": ("temperatura", 1), "cálido": ("temperatura", 1), "frío": ("temperatura", -1), "frio": ("temperatura", -1),
    "rico": ("riqueza", 1), "pobre": ("riqueza", -1),
    "listo": ("listeza", 1), "inteligente": ("listeza", 1), "tonto": ("listeza", -1),
    "mejor": ("calidad", 1), "peor": ("calidad", -1), "bueno": ("calidad", 1), "malo": ("calidad", -1),
    "profundo": ("profundidad", 1), "hondo": ("profundidad", 1), "superficial": ("profundidad", -1),
    "lejano": ("distancia", 1), "cercano": ("distancia", -1), "oscuro": ("oscuridad", 1), "claro": ("oscuridad", -1),
    "duro": ("dureza", 1), "blando": ("dureza", -1), "fácil": ("dificultad", -1), "facil": ("dificultad", -1), "difícil": ("dificultad", 1), "dificil": ("dificultad", 1),
}
SINTETICOS = {"mayor": "mayor", "menor": "menor", "mejor": "mejor", "peor": "peor", "mayores": "mayor", "menores": "menor", "mejores": "mejor", "peores": "peor"}
# «tiene más años que», «pesa más que», «corre más que»
VERBALES = {("tener", "años"): ("edad", 1), ("pesar", None): ("peso", 1), ("correr", None): ("velocidad", 1), ("medir", None): ("altura", 1),
            ("costar", None): ("precio", 1), ("valer", None): ("precio", 1), ("saber", None): ("listeza", 1), ("durar", None): ("duración", 1)}
_V_FORMAS = {"tiene": "tener", "tienen": "tener", "tendrá": "tener", "tendra": "tener", "tenía": "tener", "tenia": "tener", "pesa": "pesar",
             "pesan": "pesar", "pesará": "pesar", "corre": "correr", "corren": "correr", "mide": "medir", "miden": "medir", "cuesta": "costar",
             "cuestan": "costar", "vale": "valer", "valen": "valer", "sabe": "saber", "saben": "saber", "dura": "durar", "duran": "durar"}
_DET = r"(?:el|la|los|las|un|una|unos|unas|mi|mis|tu|tus|su|sus|este|esta|ese|esa|nuestro|nuestra)"
_COP = r"(?:es|son|sea|sean|era|eran|fue|será|sera|serán|seran|sería|seria|está|esta|están|estan|estará|estara)"


def _masc(adj):
    a = adj.lower()
    if a in SINTETICOS:
        return SINTETICOS[a]
    for cand in (a, a[:-1] if a.endswith("s") else a, re.sub(r"as$", "o", a), re.sub(r"a$", "o", a), re.sub(r"es$", "", a), re.sub(r"os$", "o", a)):
        if cand in ESCALAS:
            return cand
        if sa(cand) in {sa(k): k for k in ESCALAS}:
            return {sa(k): k for k in ESCALAS}[sa(cand)]
    return None


def _ent(x):
    """«una liebre» / «el conejo» / «la tuya» -> clave estable («liebre», «conejo», «tuya»)."""
    x = re.sub(rf"^{_DET}\s+", "", x.strip().lower())
    x = re.sub(r"^(?:de|del)\s+", "", x)
    return sa(x).strip(" ,.?¿")


def _sujeto_bonito(x):
    x = x.strip(" ,.?¿")
    return x


_REL = re.compile(rf"(?P<a>(?:{_DET}\s+)?[\wáéíóúñü]+)\s+(?P<cop>{_COP})\s+(?:(?P<mas>m[aá]s|menos)\s+(?P<adj>[\wáéíóúñü]+)|(?P<sint>mayor(?:es)?|menor(?:es)?|mejor(?:es)?|peor(?:es)?))\s+que\s+(?P<b>(?:{_DET}\s+)?[\wáéíóúñü]+)", re.I)
_REL_V = re.compile(rf"(?P<a>(?:{_DET}\s+)?[\wáéíóúñü]+)\s+(?P<v>[\wáéíóú]+)\s+(?P<mas>m[aá]s|menos)\s+(?P<obj>años\s+|kilos\s+)?que\s+(?P<b>(?:{_DET}\s+)?[\wáéíóúñü]+)", re.I)


def relaciones(texto):
    """Relaciones comparativas de un texto: [(a, b, escala, sentido)] con el sentido «a está por encima de b»."""
    out = []
    for m in _REL.finditer(texto):
        adj = m.group("sint") or m.group("adj")
        k = _masc(adj)
        if not k:
            continue
        esc, sgn = ESCALAS[k]
        if m.group("mas") and m.group("mas").lower() == "menos":
            sgn = -sgn
        a, b = _ent(m.group("a")), _ent(m.group("b"))
        out.append((a, b, esc, sgn, m.group("a").strip(), m.group("b").strip()))
    for m in _REL_V.finditer(texto):
        v = _V_FORMAS.get(m.group("v").lower())
        if not v:
            continue
        obj = (m.group("obj") or "").strip().lower() or None
        clave = (v, obj) if (v, obj) in VERBALES else (v, None)
        if clave not in VERBALES:
            continue
        esc, sgn = VERBALES[clave]
        if m.group("mas").lower() == "menos":
            sgn = -sgn
        out.append((_ent(m.group("a")), _ent(m.group("b")), esc, sgn, m.group("a").strip(), m.group("b").strip()))
    return out


def _orden(rels):
    """escala -> conjunto de pares (x, y) con x > y, cerrado por transitividad."""
    por = {}
    for a, b, esc, sgn, *_ in rels:
        s = por.setdefault(esc, set())
        s.add((a, b) if sgn > 0 else (b, a))
    for esc, s in por.items():
        cambia = True
        while cambia:
            cambia = False
            for (x, y) in list(s):
                for (y2, z) in list(s):
                    if y == y2 and (x, z) not in s and x != z:
                        s.add((x, z)); cambia = True
    return por


def _nombres(rels):
    n = {}
    for a, b, _, _, ta, tb in rels:
        n.setdefault(a, ta); n.setdefault(b, tb)
    return n


def _sin_art(t):
    return re.sub(rf"^{_DET}\s+", "", t.strip(), flags=re.I)


def _con_art(clave, nombres):
    t = nombres.get(clave, clave)
    m = re.match(rf"^(un|una|unos|unas)\s+(.+)$", t, re.I)
    if m:
        art = {"un": "el", "una": "la", "unos": "los", "unas": "las"}[m.group(1).lower()]
        return f"{art} {m.group(2)}"
    return t


def _forma(adj_masc, como):
    """Concordancia del adjetivo con la palabra que lo lleva («la liebre» -> «pequeña»)."""
    if adj_masc in ("mayor", "menor", "mejor", "peor") or not adj_masc.endswith("o"):
        return adj_masc
    if re.search(r"(?:^|\s)(?:la|una|mi|tu|su|esta|esa|nuestra)\s", " " + como.lower() + " ") or como.lower().strip() in ("tuya", "mía", "suya", "la tuya", "la mía", "la suya"):
        return adj_masc[:-1] + "a"
    return adj_masc


def responde(texto):
    """«si P (comparaciones), ¿Q?» -> respuesta o None. También vale con las relaciones y la pregunta en la misma frase."""
    t = (texto or "").strip()
    if "?" not in t:
        return None
    m = re.match(r"^\s*¿?\s*(?:y\s+)?si\s+(.+?)\s*,\s*(¿?.+\?)\s*$", t, re.I)
    if not m:
        return None
    sup, preg = m.group(1), m.group(2).strip("¿? ")
    rels = relaciones(sup)
    if not rels:
        return None
    orden = _orden(rels)
    nombres = _nombres(rels)
    pq = preg
    # 1) ¿quién es (el|la) más ADJ / el mayor / la menor?
    mq = re.match(r"^(?:qui[eé]n|cu[aá]l)\s+(?:es|será|sera|sería|seria|son)\s+(?:el|la|los|las)?\s*(?:(m[aá]s|menos)\s+)?([\wáéíóúñ]+)(?:\s+de\s+(?:los|las)\s+\w+)?$", pq, re.I)
    if mq:
        k = _masc(mq.group(2))
        if not k:
            return None
        esc, sgn = ESCALAS[k]
        if (mq.group(1) or "").lower() == "menos":
            sgn = -sgn
        s = orden.get(esc)
        if not s:
            return None
        elems = {x for p in s for x in p}
        if sgn > 0:
            cand = [x for x in elems if all((x, y) in s for y in elems if y != x)]
        else:
            cand = [x for x in elems if all((y, x) in s for y in elems if y != x)]
        if len(cand) != 1:
            return f"Con lo que supones no se puede saber quién es {'el más ' if not k in SINTETICOS else 'el '}{k}."
        w = _sin_art(nombres.get(cand[0], cand[0]))
        return f"{w[0].upper() + w[1:]}."
    # 2) ¿X es/será más A o más B que Y?   3) ¿X es/será más A que Y?
    mq = re.match(rf"^(?P<x>.+?)\s+(?P<cop>{_COP})\s+(?P<alt>.+?)(?:\s+que\s+(?P<y>.+))?$", pq, re.I)
    if not mq:
        return None
    x = _ent(mq.group("x"))
    if mq.group("y"):
        y = _ent(mq.group("y"))
    else:                                            # «¿la tuya es más pequeña?»: el otro término es el único que queda
        otros = [e for e in nombres if e != x]
        if x not in nombres or len(otros) != 1:
            return None
        y = otros[0]
    alts = [a.strip() for a in re.split(r"\s+o\s+", mq.group("alt"))]
    opciones = []
    for a in alts:
        ma = re.match(r"^(?:(m[aá]s|menos)\s+)?([\wáéíóúñ]+)$", a, re.I)
        if not ma:
            return None
        k = _masc(ma.group(2))
        if not k or (not ma.group(1) and k not in SINTETICOS):
            return None
        esc, sgn = ESCALAS[k]
        if (ma.group(1) or "").lower() == "menos":
            sgn = -sgn
        opciones.append((a, k, esc, sgn, (ma.group(1) or "").lower()))
    def vale(esc, sgn):
        s = orden.get(esc, set())
        if (x, y) in s:
            return sgn > 0
        if (y, x) in s:
            return sgn < 0
        return None
    X = _con_art(x, nombres) if x in nombres else mq.group("x")
    Y = _con_art(y, nombres) if y in nombres else (mq.group("y") or y)
    base = _base(rels, nombres)
    if len(opciones) >= 2:
        buenas = [o for o in opciones if vale(o[2], o[3])]
        if any(vale(o[2], o[3]) is None for o in opciones) or len(buenas) != 1:
            return "Con lo que supones no se puede saber."
        o = buenas[0]
        adj = _forma(o[1], X)
        cuant = (o[4] + " ") if o[4] else ""
        return f"{cuant.capitalize() + adj if cuant else adj.capitalize()}: si {base}, {X} es {cuant}{adj} que {Y}."
    o = opciones[0]
    r = vale(o[2], o[3])
    if r is None:
        return "Con lo que supones no se puede saber."
    adj = _forma(o[1], X)
    cuant = (o[4] + " ") if o[4] else ""
    if r:
        return f"Sí: si {base}, {X} es {cuant}{adj} que {Y}."
    contrario = _contrario(o[1])
    return f"No: si {base}, {X} es {('más ' + _forma(contrario, X)) if contrario and contrario not in SINTETICOS else _forma(contrario or o[1], X)} que {Y}."


def _contrario(k):
    esc, sgn = ESCALAS[k]
    for c, (e2, s2) in ESCALAS.items():
        if e2 == esc and s2 == -sgn and c not in ("chico", "veloz", "liviano", "anciano", "nuevo", "grueso", "flaco", "fino", "debil", "frio", "facil", "dificil", "hondo", "cálido", "bueno", "malo"):
            return c
    return None


def _base(rels, nombres):
    trozos = []
    for a, b, esc, sgn, ta, tb in rels[:3]:
        k = next((c for c, v in ESCALAS.items() if v == (esc, abs(sgn) if sgn > 0 else -1) and c not in ("chico", "veloz", "liviano", "anciano", "nuevo", "grueso", "flaco", "fino")), None)
        if esc == "edad":
            k = "mayor" if sgn > 0 else "menor"
            trozos.append(f"{_con_art(a, nombres)} es {k} que {_con_art(b, nombres)}")
            continue
        if not k:
            k = "?"
        trozos.append(f"{_con_art(a, nombres)} es más {_forma(k, _con_art(a, nombres))} que {_con_art(b, nombres)}")
    return " y ".join(trozos)
