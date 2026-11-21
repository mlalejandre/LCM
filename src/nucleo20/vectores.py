"""LCM 2.20 · Vectores de significado de las palabras, aprendidos del léxico del proyecto.

No son embeddings de texto preentrenados: se APRENDEN aquí, de fábrica, del grafo de sinonimia del léxico (data/lexico_es.json). Dos
palabras quedan cerca si comparten sentidos, directamente o por una cadena corta de sinónimos («elaborar» ~ «fabricar», «comida» ~
«alimento»), sin que nadie haya escrito esa pareja a mano. Es un espacio de SINONIMIA a propósito: si se meten los ancestros como
contexto, «perro» y «gato» salen tan cerca como dos sinónimos (medido en lab/iter220/calibra.py), y cambiar uno por otro es un error.
La relación «es una manera de» (almacenar -> guardar) no es simétrica y un parecido no la puede representar sin acercar también a
los hermanos; para ella está `parentesco`, que mira el grafo.

Se entrenan en unos segundos y se guardan en src/nucleo20/vectores_lexico.pt. Si falta el léxico, no hay vectores y todo sigue
funcionando con coincidencia exacta.
    python -m src.nucleo20.vectores            entrena y guarda
    python -m src.nucleo20.vectores comer      vecinos de una palabra
"""
from __future__ import annotations

import json
import os

from .morfo import sa

_AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA_LEXICO = os.path.join(_AQUI, "..", "..", "data", "lexico_es.json")
RUTA_DEF = os.path.join(_AQUI, "..", "..", "data", "definiciones.json.gz")
RUTA_CON = os.path.join(_AQUI, "..", "..", "data", "conceptos.json.gz")
RUTA_VEC = os.path.join(_AQUI, "vectores_lexico.pt")
DIM = 96
P_SIM = 0.5          # peso de «adjetivo de sentido parecido» frente a «mismo sentido» (1.0)
_V = {}


def _lexico():
    """(sinónimos por concepto, padres de cada concepto, parecidos entre adjetivos, categoría). Solo palabras sueltas."""
    L = json.load(open(RUTA_LEXICO, encoding="utf-8"))
    syn = {int(k): [sa(w.lower()) for w in v if " " not in w and "_" not in w and sa(w.lower()).isalpha()] for k, v in L["syn"].items()}
    hyp = {int(k): [int(x) for x in v] for k, v in L.get("hyp", {}).items()}
    sim_ = {}
    if os.path.exists(RUTA_DEF):
        import gzip
        D = json.load(gzip.open(RUTA_DEF, "rt", encoding="utf-8"))
        sim_ = {int(k): [int(x) for x in v if x is not None] for k, v in D.get("sim", {}).items()}
    return L, syn, hyp, sim_


def entrenar(dim=DIM, semilla=7, guardar=True, log=None, p_sim=P_SIM):
    """Aprende los vectores del grafo de sinonimia del léxico. Devuelve (palabras, matriz) o None si no hay léxico.
    Se factoriza la matriz palabra-palabra («comparten un sentido») normalizada: X·Xt la aproxima, así que el producto de dos vectores
    mide si dos palabras comparten sentidos, directamente o a través de una cadena corta de sinónimos."""
    import warnings
    import torch
    if not os.path.exists(RUTA_LEXICO):
        return None
    warnings.simplefilter("ignore")
    L, syn, _, sim_ = _lexico()
    palabras = sorted({w for ws in syn.values() for w in ws})
    idx = {w: k for k, w in enumerate(palabras)}
    W = {}

    def suma(a, b, v):
        if a != b:
            k = (idx[a], idx[b]) if idx[a] < idx[b] else (idx[b], idx[a])
            if W.get(k, 0) < v:
                W[k] = v
    for s, ws in syn.items():
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                suma(ws[i], ws[j], 1.0)
        if p_sim:
            for o in sim_.get(s, ()):                    # adjetivos de sentido parecido («grande» ~ «enorme»)
                for a in ws:
                    for b in syn.get(o, ()):
                        suma(a, b, p_sim)
    n = len(palabras)
    if log:
        log(f"léxico: {n} palabras, {len(W)} parejas que comparten sentido")
    ii = torch.tensor([[a for a, _ in W] + [b for _, b in W], [b for _, b in W] + [a for a, _ in W]], dtype=torch.long)
    vv = torch.tensor(list(W.values()) * 2, dtype=torch.float32)
    A = torch.sparse_coo_tensor(ii, vv, (n, n)).coalesce()
    d = torch.sparse.sum(A, dim=1).to_dense() + 1.0
    i2 = A.indices()
    v2 = A.values() / (d[i2[0]].sqrt() * d[i2[1]].sqrt())
    dg = torch.arange(n)
    An = torch.sparse_coo_tensor(torch.cat([i2, torch.stack([dg, dg])], 1), torch.cat([v2, 1.0 / d]), (n, n)).coalesce()
    torch.manual_seed(semilla)
    U, S, Vt = torch.svd_lowrank(An, q=dim, niter=6)
    signo = (U * Vt).sum(0).sign()
    X = torch.nn.functional.normalize(U * (S.clamp_min(0) * (signo > 0)).sqrt(), dim=1)
    if guardar:
        torch.save({"palabras": palabras, "X": X.half(), "dim": dim, "fuente": L.get("fuente", ""), "puentes": puentes(log=log), "puentes1": puentes(minimo=1, solo=1)}, RUTA_VEC)
    return palabras, X


def puentes(minimo=2, log=None, solo=None):
    """2.22 · Sinónimos que el léxico español no enlaza, sacados de los otros idiomas de la base de conceptos (data/conceptos.json.gz).
    Si dos sentidos distintos comparten palabra en varios idiomas («transformar» y «convertir»: it. trasformare, pt. modificar), es un
    indicio de que dicen lo mismo. Devuelve {palabra: {otra: n.º de idiomas}} con n >= minimo. Es un indicio ruidoso (a ojo, la mitad
    de las parejas son buenas): por eso nunca basta solo; quien lo usa exige además que la pregunta rehecha tenga respuesta."""
    if not os.path.exists(RUTA_CON):
        return {}
    import gzip
    c = json.load(gzip.open(RUTA_CON, "rt", encoding="utf-8"))
    lem, ids = c.get("lem", {}), c.get("ids", [])
    if "es" not in lem:
        return {}
    par = {}
    for l in lem:
        if l == "es":
            continue
        inv = {}
        for s, ws in lem[l].items():
            for w in ws:
                inv.setdefault(w.lower(), []).append(int(s))
        vistos = set()
        for ss in inv.values():
            if len(ss) < 2 or len(ss) > 6:
                continue
            for i in range(len(ss)):
                for j in range(i + 1, len(ss)):
                    a, b = (ss[i], ss[j]) if ss[i] < ss[j] else (ss[j], ss[i])
                    if ids[a][-1] != ids[b][-1] or (a, b) in vistos:
                        continue
                    vistos.add((a, b))
                    par[(a, b)] = par.get((a, b), 0) + 1
    es = {int(s): [sa(w.lower()) for w in ws if " " not in w and sa(w.lower()).isalpha()] for s, ws in lem["es"].items()}
    w2s = {}
    for s, ws in es.items():
        for w in ws:
            w2s.setdefault(w, set()).add(s)
    out = {}
    for (a, b), n in par.items():
        if n < minimo or (solo is not None and n != solo):
            continue
        for x in es.get(a, ()):
            for y in es.get(b, ()):
                if x != y and not (w2s[x] & w2s[y]):
                    if out.setdefault(x, {}).get(y, 0) < n:
                        out[x][y] = n
                        out.setdefault(y, {})[x] = n
    if log:
        log(f"puentes entre idiomas: {sum(len(v) for v in out.values()) // 2} parejas nuevas")
    return out


def puente(a, b):
    """N.º de idiomas en que dos palabras sin sentido común en español comparten palabra (0 si ninguno o si no hay datos)."""
    _carga()
    a, b = sa(a.lower()), sa(b.lower())
    return (_V.get("puentes") or {}).get(a, {}).get(b, 0) or (_V.get("puentes1") or {}).get(a, {}).get(b, 0)


def _carga():
    if "X" in _V or _V.get("sin"):
        return
    try:
        import torch
        if os.path.exists(RUTA_VEC):
            d = torch.load(RUTA_VEC, map_location="cpu")
            palabras, X = d["palabras"], d["X"].float()
            if "puentes" not in d:                       # fichero de la 2.20/2.21: se completa sin reentrenar los vectores
                d["puentes"] = puentes()
                try:
                    torch.save(d, RUTA_VEC)
                except Exception:                        # noqa
                    pass
            if "puentes1" not in d:                      # 2.24: parejas que coinciden en UN solo idioma (indicio débil: nunca vale solo)
                d["puentes1"] = puentes(minimo=1, solo=1)
                try:
                    torch.save(d, RUTA_VEC)
                except Exception:                        # noqa
                    pass
            _V["puentes"] = d["puentes"]
            _V["puentes1"] = d["puentes1"]
        else:
            r = entrenar()
            if r is None:
                _V["sin"] = True
                return
            palabras, X = r
            try:                                         # recién entrenados: los puentes están en el fichero que se acaba de guardar
                d = torch.load(RUTA_VEC, map_location="cpu")
                _V["puentes"], _V["puentes1"] = d.get("puentes") or {}, d.get("puentes1") or {}
            except Exception:                            # noqa
                pass
        _V["X"] = X
        _V["idx"] = {w: k for k, w in enumerate(palabras)}
        _V["palabras"] = palabras
    except Exception:                                    # noqa
        _V["sin"] = True


def disponible():
    _carga()
    return "X" in _V


def vector(w):
    _carga()
    if "X" not in _V:
        return None
    k = _V["idx"].get(sa(w.lower()))
    return None if k is None else _V["X"][k]


def sim(a, b):
    """Parecido de significado entre dos palabras (lemas), de 0 a 1. 0 si alguna no está en el léxico."""
    a, b = sa(a.lower()), sa(b.lower())
    if a == b:
        return 1.0
    va, vb = vector(a), vector(b)
    if va is None or vb is None:
        return 0.0
    return max(0.0, float((va * vb).sum()))


def vecinos(w, n=10):
    v = vector(w)
    if v is None:
        return []
    s = _V["X"] @ v
    top = s.topk(n + 1)
    return [(_V["palabras"][int(k)], round(float(x), 2)) for x, k in zip(top.values, top.indices) if _V["palabras"][int(k)] != sa(w.lower())][:n]


if __name__ == "__main__":
    import sys
    import time
    if len(sys.argv) > 1:
        for w in sys.argv[1:]:
            print(w, vecinos(w))
    else:
        t0 = time.time()
        r = entrenar(log=print)
        print("sin léxico" if r is None else f"vectores: {len(r[0])} palabras x {r[1].shape[1]} -> {RUTA_VEC}  ({time.time() - t0:.1f} s)")


def antonimos(a, b):
    """¿El léxico da estas dos palabras por contrarias? (los contrarios se parecen mucho como vectores y no son intercambiables)"""
    if "ant" not in _V:
        pares = set()
        try:
            L = json.load(open(RUTA_LEXICO, encoding="utf-8"))
            for k, v in L.get("ant", {}).items():
                for x in v:
                    for wa in L["syn"].get(str(k), []):
                        for wb in L["syn"].get(str(x), []):
                            pares.add((sa(wa.lower()), sa(wb.lower())))
        except Exception:                                # noqa
            pass
        _V["ant"] = pares
    a, b = sa(a.lower()), sa(b.lower())
    return (a, b) in _V["ant"] or (b, a) in _V["ant"]


def _grafo():
    if "w2s" not in _V:
        try:
            L, syn, hyp, sim_ = _lexico()
            w2s = {}
            for s, ws in syn.items():
                for w in ws:
                    w2s.setdefault(w, set()).add(s)
            _V["w2s"], _V["hyp"], _V["simr"] = w2s, hyp, sim_
        except Exception:                                # noqa
            _V["w2s"], _V["hyp"], _V["simr"] = {}, {}, {}
    return _V["w2s"], _V["hyp"]


def parentesco(a, b):
    """Enlace directo entre dos palabras en el grafo del léxico: (tipo, peso) o (None, 0.0).
    tipo "igual": comparten sentidos; "modo": una es una manera de la otra («almacenar» -> «guardar»), a un solo paso.
    peso: qué parte de los sentidos de la palabra con menos sentidos entra en el enlace. Dos palabras de muchos sentidos que solo
    coinciden en uno raro («beber» y «usar») pesan poco; «fallecer» y «morir» pesan 1."""
    w2s, hyp = _grafo()
    a, b = sa(a.lower()), sa(b.lower())
    sa_, sb_ = w2s.get(a, set()), w2s.get(b, set())
    if not sa_ or not sb_:
        return None, 0.0
    m = min(len(sa_), len(sb_))
    com = sa_ & sb_
    hijos_a = {s for s in sa_ if any(p in sb_ for p in hyp.get(s, ()))}
    hijos_b = {s for s in sb_ if any(p in sa_ for p in hyp.get(s, ()))}
    n_modo = max(len(hijos_a) / len(sa_), len(hijos_b) / len(sb_))
    if com and len(com) / m >= n_modo:
        return "igual", len(com) / m
    if n_modo:
        return "modo", n_modo
    if com:
        return "igual", len(com) / m
    par = {s for s in sa_ if any(o in sb_ for o in _V["simr"].get(s, ()))}
    if par:
        return "igual", len(par) / len(sa_)              # adjetivos que el léxico da por parecidos («grande» ~ «enorme»)
    return None, 0.0


def dos_pasos(a, b):
    """¿Hay una tercera palabra que el léxico da por sinónima de las dos? («vigilar» ~ «guardar» ~ «cuidar»). Es un indicio, no una prueba."""
    w2s, _ = _grafo()
    if "s2w" not in _V:
        s2w = {}
        for w, ss in w2s.items():
            for s in ss:
                s2w.setdefault(s, set()).add(w)
        _V["s2w"] = s2w
    a, b = sa(a.lower()), sa(b.lower())
    va = {w for s in w2s.get(a, ()) for w in _V["s2w"].get(s, ())}
    vb = {w for s in w2s.get(b, ()) for w in _V["s2w"].get(s, ())}
    return bool((va & vb) - {a, b})


def tipo_de(a, b):
    """¿Es `a` un tipo de `b` según el léxico (algún sentido de `a` tiene por padre un sentido de `b`) y no al revés ni lo mismo?"""
    w2s, hyp = _grafo()
    sa_, sb_ = w2s.get(sa(a.lower()), set()), w2s.get(sa(b.lower()), set())
    if not sa_ or not sb_ or sa_ & sb_:
        return False
    return any(p in sb_ for s in sa_ for p in hyp.get(s, ()))
