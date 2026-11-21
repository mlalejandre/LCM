"""LCM 2.30 · VECTORES DE TEMA, aprendidos leyendo y conversando.

Los vectores de fábrica (vectores.py) dicen qué palabras significan lo mismo; no dicen de qué se habla junto. «Torneo» y «premio» no son
sinónimos, pero van juntos. Eso se aprende aquí de la forma más simple que funciona: contando qué palabras de contenido aparecen en la
misma frase. De esas cuentas sale, para cada palabra, un vector (cuánto más de lo esperable aparece con cada una de las demás), y dos
palabras son del mismo tema si sus vectores se parecen o si aparecen juntas más de lo esperable.

Hay dos capas que se suman:
  · la de fábrica: se entrena con el texto que se le inyecta (data/corpus_tema.txt) y con lo que la base de conceptos ya dice que va
    junto (qué es parte de qué, dónde suele estar algo, para qué sirve);
  · la del usuario: cada frase que el modelo lee u oye suma sus cuentas, y se guarda con su memoria. Así sigue aprendiendo con el uso.

No guarda hechos («Brasil produce café»), guarda compañías («café» va con «taza», «tostar», «beber»).
"""
from __future__ import annotations

import json
import math
import os
import re

from .morfo import sa
from . import morfo as M

_AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA_CORPUS = os.path.join(_AQUI, "..", "..", "data", "corpus_tema.txt")
RUTA_TEMA = os.path.join(_AQUI, "tema_fabrica.json")
MAX_USUARIO = 6000            # parejas que guarda como mucho la capa del usuario
_F = {}                       # la capa de fábrica, en memoria
_M = {}                       # los miembros de cada clase, según la base de conceptos
_GEN = {"ser", "estar", "haber", "tener", "hacer", "poder", "ir", "decir", "dar", "ver", "querer", "saber", "deber", "soler", "poner", "llevar", "pasar", "quedar", "cosa", "vez",
        "dia", "ano", "mucho", "poco", "bueno", "malo", "grande", "pequeno", "nuevo", "mismo", "otro", "todo", "cada", "siempre", "nunca", "tambien", "luego", "despues", "antes",
        "ahora", "hoy", "ayer", "manana", "aqui", "alli", "gente", "persona", "tipo", "parte", "forma", "manera", "llamar", "gustar", "primero", "segundo", "alguno", "ninguno", "porque", "cuando", "donde", "como", "aunque", "mientras", "pues", "entonces"}


def _es_nombre(w):
    c = getattr(_es_nombre, "_c", None)
    if c is None:
        c = _es_nombre._c = {}
    if w not in c:
        try:                                             # nombre «de verdad»: está en la base de conceptos, o el léxico lo conoce y no es una forma verbal
            from . import acepciones as A
            from . import conceptos as K
            b_ = sa(M.singular(w))
            en_kb = b_ in K.kb().get("isa", {}) or b_ in K.kb().get("forma", {})
            verbo = any(len(a_) > 2 and a_[1] in ("pres", "pret", "imp", "fut") for a_ in (M.analizar(w) or []))
            c[w] = en_kb or (bool(A.sentidos(w)) and not verbo)
        except Exception:                                # noqa
            c[w] = False
    return c[w]


def lema(w):
    """La forma de diccionario de una palabra. Si el léxico la conoce como nombre, se queda de nombre («casa» no es «casar»,
    «sobre» no es «sobrar»); si no, el verbo del que viene («comemos» -> «comer», «cortarme» -> «cortar»)."""
    w = w.lower()
    if _es_nombre(w) and not re.search(r"(?:ado|ido)s?$", w):
        return sa(M.singular(w))
    w2 = re.sub(r"(?<=[aeií]r)(?:me|te|se|lo|la|los|las|le|les|nos)$", "", w)
    try:
        an = M.analizar(w2) or []
    except Exception:                                    # noqa
        an = []
    l = next((a[0] for a in an if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut", "inf", "part", "ger") and len(a[0]) > 2), None)
    if l:
        return sa(l)
    b = sa(M.singular(w))
    if b.endswith("a") and len(b) > 4 and _es_nombre(b[:-1] + "o"):
        return b[:-1] + "o"                              # «peluquera» va con «peluquero»
    return b


def lemas(texto):
    """Las palabras de contenido de una frase en su forma de diccionario, sin las que van con todo."""
    from . import lectura as L
    out = []
    for w in re.findall(r"[a-záéíóúñü]+", (texto or "").lower()):
        if sa(w) in L._VACIAS or len(w) < 3 or sa(w) in ("nos", "les", "una", "uno", "los", "las"):
            continue
        l = lema(w)
        if l not in _GEN and len(l) > 2:
            out.append(l)
    return list(dict.fromkeys(out))


def _suma(C, N, ls, peso=1.0):
    for a in ls:
        N[a] = N.get(a, 0.0) + peso
    for i, a in enumerate(ls):
        for b in ls[i + 1:]:
            if a != b:
                k = a + "|" + b if a < b else b + "|" + a
                C[k] = C.get(k, 0.0) + peso


def entrena(log=None):
    """La capa de fábrica: el texto inyectado y lo que la base de conceptos dice que va junto. Tarda unos segundos; se guarda."""
    C, N, S = {}, {}, 0
    try:
        with open(RUTA_CORPUS, encoding="utf-8") as fh:
            for linea in fh:
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                for frase in re.split(r"(?<=[.!?])\s+", linea):
                    ls = lemas(frase)
                    if len(ls) >= 2:
                        _suma(C, N, ls[:14]); S += 1
    except OSError:
        pass
    try:                                                 # lo que la base de conceptos ya relaciona: cada relación cuenta como una frase corta
        from . import conceptos as K
        kb = K.kb()
        pares = []
        for sec in ("partes", "parte_de"):
            for a, bs in kb.get(sec, {}).items():
                pares += [(a, b) for b in bs]
        for rel, d in (kb.get("rel") or {}).items():
            for a, bs in (d.items() if isinstance(d, dict) else []):
                for b in (bs if isinstance(bs, (list, tuple, set)) else [bs]):
                    pares.append((a, b if isinstance(b, str) else str(b)))
        for a, b in pares:
            ls = lemas(a + " " + b)
            if len(ls) >= 2:
                _suma(C, N, ls[:6], 1.0); S += 1
    except Exception:                                    # noqa
        pass
    d = {"C": C, "N": N, "S": S}
    try:
        with open(RUTA_TEMA, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False)
    except OSError:
        pass
    if log:
        log(f"tema: {S} frases, {len(N)} palabras, {len(C)} parejas")
    return d


def _fabrica():
    if not _F:
        d = None
        try:
            if os.path.exists(RUTA_TEMA) and (not os.path.exists(RUTA_CORPUS) or os.path.getmtime(RUTA_TEMA) >= os.path.getmtime(RUTA_CORPUS)):
                with open(RUTA_TEMA, encoding="utf-8") as fh:
                    d = json.load(fh)
        except Exception:                                # noqa
            d = None
        if d is None:
            d = entrena()
        _F.update(d)
        _F["_ady"] = None
    return _F


def aprende(nuc, texto):
    """La capa del usuario: lo que el modelo lee u oye suma sus cuentas (y se guarda con su memoria)."""
    if os.environ.get("LCM_SIN_TEMA") or not texto or "?" in texto:
        return
    U = nuc.usuario.setdefault("tema", {"C": {}, "N": {}, "S": 0})
    for frase in re.split(r"(?<=[.!?])\s+|\n", texto)[:40]:
        ls = lemas(frase)
        if len(ls) >= 2:
            _suma(U["C"], U["N"], ls[:12]); U["S"] += 1
    if len(U["C"]) > MAX_USUARIO:                        # se quedan las parejas más vistas
        for k in sorted(U["C"], key=lambda k: U["C"][k])[:len(U["C"]) - MAX_USUARIO]:
            del U["C"][k]
    nuc._tema_ady = None
    nuc._tema_ady_f = None


def _ady(nuc, firme=False):
    """{palabra: {vecina: peso}} con las dos capas sumadas (el peso es cuánto más de lo esperable van juntas).
    Con firme=True no cuentan las parejas que el usuario ha dicho UNA sola vez: sirven para parecerse, no para repartir sentidos."""
    F = _fabrica()
    U = (nuc.usuario.get("tema") if nuc is not None else None) or {"C": {}, "N": {}, "S": 0}
    clave = "_tema_ady_f" if firme else "_tema_ady"
    cache = getattr(nuc, clave, None) if nuc is not None else F.get(clave)
    if cache is not None:
        return cache
    C = dict(F["C"]); N = dict(F["N"]); S = F["S"] + 3.0 * U["S"]
    for k, v in U["C"].items():
        if firme and v < 2 and k not in F["C"]:
            continue
        C[k] = C.get(k, 0.0) + 3.0 * v                   # lo que dice el usuario pesa más que una frase de fábrica
    for k, v in U["N"].items():
        N[k] = N.get(k, 0.0) + 3.0 * v
    ady = {}
    S = max(S, 1.0)
    for k, c in C.items():
        a, b = k.split("|")
        pmi = math.log((c * S) / (N.get(a, 1.0) * N.get(b, 1.0)) + 1e-9)
        if pmi <= 0:
            continue
        w = pmi * (c / (c + 1.0))                        # una sola vez juntas vale la mitad
        ady.setdefault(a, {})[b] = w
        ady.setdefault(b, {})[a] = w
    if nuc is not None:
        setattr(nuc, clave, ady)
        if not firme:
            nuc._tema_ady_f = None
    else:
        F[clave] = ady
    return ady


def tema(nuc, a, b, firme=False):
    """Cuánto van juntas dos palabras, de 0 a 1: por aparecer juntas, o por tener las mismas compañías."""
    if os.environ.get("LCM_SIN_TEMA"):
        return 0.0
    a, b = sa(a), sa(b)
    if a == b:
        return 1.0
    ady = _ady(nuc, firme)
    va, vb = ady.get(a), ady.get(b)
    if not va or not vb:
        return 0.0
    directo = min(1.0, va.get(b, 0.0) / 4.0)
    com = set(va) & set(vb)
    cos = 0.0
    if com:
        num = sum(va[k] * vb[k] for k in com)
        cos = num / (math.sqrt(sum(x * x for x in va.values())) * math.sqrt(sum(x * x for x in vb.values())) + 1e-9)
    medio = 0.0                                          # o por una compañía común fuerte: «zurbo» va con «pastel» y «pastel» con «pastelero»
    FN = _fabrica()["N"]
    if com and directo < 0.5 and (a not in FN or b not in FN):   # solo para palabras NUEVAS, que el texto de fábrica no traía
        medio = 0.8 * max(min(min(1.0, va[k] / 4.0), min(1.0, vb[k] / 4.0)) for k in com)
    return max(directo, cos, medio)


def miembros(et):
    """Los conceptos que la base de fábrica pone dentro de una clase («baile»: tango, jota, salsa…), con sus descendientes."""
    c = _M.get("m")
    if c is None:
        c = {}
        try:
            from . import conceptos as K
            for hijo, padres in K.kb()["isa"].items():
                for p_ in padres:
                    c.setdefault(sa(p_), set()).add(sa(hijo))
        except Exception:                                # noqa
            pass
        _M["m"] = c
    out, f = set(), {sa(et)}
    for _ in range(3):
        f = {h for x in f for h in c.get(x, ())} - out
        if not f:
            break
        out |= f
    return out


def _familia(v, n):
    """¿Es `v` el verbo de `n`? (bailar/baile, pescar/pesca, dibujar/dibujo, firmar/firma)."""
    if len(v) < 5 or v[-2:] not in ("ar", "er", "ir") or " " in n:
        return False
    r = v[:-2]
    return len(r) >= 3 and n in (r + "a", r + "e", r + "o")


def afin_clase(nuc, c, et, sin=()):
    """Cuánto va una palabra del contexto con una CLASE (de 0 a 1,5): por ser ella misma de la clase, o por ir con el nombre de la clase
    y con varios de sus miembros. Así «bailar» apoya el sentido «baile» de una palabra aunque nunca se hayan visto juntas: basta con que
    vaya con otros bailes. Se pide acuerdo de varios miembros (media de los tres mejores) para que una coincidencia suelta no cuente."""
    if os.environ.get("LCM_SIN_TEMA") or os.environ.get("LCM_SIN_CLASE"):
        return 0.0
    c, et = sa(c), sa(et)
    ms = miembros(et) - {sa(x) for x in sin}
    if c == et or c in ms:
        return 1.5
    if _familia(c, et) or any(_familia(c, m) for m in ms):
        return 1.0                                       # «bailar» y «baile», «pescar» y «pesca»: la misma palabra hecha verbo
    ady = _ady(nuc, True)
    vc = ady.get(c)
    if not vc:
        return 0.0
    conocidos = sum(1 for m in ms if m in ady)
    ts = sorted((min(1.0, vc.get(m, 0.0) / 4.0) for m in ms if m in vc), reverse=True)[:3]
    por_miembros = sum(ts) / float(min(3, max(1, conocidos)))   # una clase con uno o dos miembros conocidos no puede reunir tres apoyos
    if conocidos >= 3 and (len(ts) < 2 or ts[1] < 0.15):
        por_miembros = 0.0                               # en una clase grande, ir con UN solo miembro es casualidad («tomar» y «bar» no hacen de «tomar» cosa de edificios)
    return max(min(1.0, vc.get(et, 0.0) / 4.0), por_miembros)


def vecinas(nuc, a, k=8, firme=False):
    ady = _ady(nuc, firme)
    return sorted(((w, round(p, 2)) for w, p in ady.get(sa(a), {}).items()), key=lambda x: -x[1])[:k]


def grupos(nuc, w, k=30, umbral=0.2):
    """Las compañías de una palabra, agrupadas: las que van entre sí forman un grupo. Para una palabra con varios sentidos, cada grupo
    suele ser un sentido («banco»: dinero-prestar-cajero / sentar-silla-descansar / parque-columpio)."""
    vs = [n for n, _ in vecinas(nuc, w, k, firme=True)]
    G = [[v] for v in vs]
    while True:
        mejor = (umbral, None)
        for i in range(len(G)):
            for j in range(i + 1, len(G)):
                m = sum(tema(nuc, a, b, True) for a in G[i] for b in G[j]) / (len(G[i]) * len(G[j]))
                if m > mejor[0]:
                    mejor = (m, (i, j))
        if not mejor[1]:
            break
        i, j = mejor[1]
        G[i] += G.pop(j)
    return [set(g) for g in sorted(G, key=len, reverse=True)]
