"""LCM 2.32 · PAPELES EN LA FRASE: quién hace y a quién se le hace.

Contar qué palabras van juntas (tema.py) no distingue «el conejo come hierba» de «comemos conejo». Aquí se mira el PAPEL de cada nombre
respecto a cada verbo: sujeto (S) u objeto (O). Se aprende del mismo texto inyectado y de lo que dice el usuario:

    S[comer]  = {mono, gorrión, caballo…}      O[comer]  = {pan, fruta, sopa…}
    S[ladrar] = {perro}                        O[asar]   = {pollo, carne}

y de ahí salen dos pistas para elegir el sentido de una palabra dudosa, las dos por CLASE (los miembros que la base de conceptos pone en ella):
  · la propensión de la clase al papel: los animales suelen ser sujeto; los alimentos, objeto;
  · el verbo concreto: quiénes más hacen de sujeto (u objeto) de ESE verbo.

No es un analizador sintáctico: son reglas cortas de posición (determinante + nombre antes o después del verbo), suficientes para frases simples.
"""
from __future__ import annotations

import os
import re

from .morfo import sa
from . import morfo as M

_DET = {"el", "la", "los", "las", "un", "una", "unos", "unas", "mi", "mis", "tu", "tus", "su", "sus", "este", "esta", "estos", "estas", "ese", "esa",
        "esos", "esas", "aquel", "aquella", "nuestro", "nuestra", "otro", "otra", "cada", "dos", "tres", "muchos", "muchas", "varios", "varias"}
_PREP = {"a", "de", "en", "con", "por", "para", "sin", "sobre", "entre", "hasta", "desde", "hacia", "junto", "tras", "bajo", "contra", "segun"}
_PUENTE = {"que", "se", "no", "ya", "tambien", "nunca", "siempre", "le", "lo", "les", "nos", "me", "te", "ha", "han", "habia", "habian", "muy", "casi", "solo"}
_AUX = {"he": "1s", "has": "2s", "ha": "3s", "hemos": "1p", "han": "3p", "habia": "3s", "habian": "3p"}
_NOV = {"ser", "estar", "haber", "tener", "hay"}        # no dicen quién hace qué
MAX_USUARIO = 1500
_F = {}


def apagado():
    return bool(os.environ.get("LCM_SIN_PAPELES") or os.environ.get("LCM_SIN_TEMA"))


def _verbo(w, previo=None):
    """(lema, personas) si `w` es una forma verbal que cuenta; None si no."""
    from . import tema as T
    ws = sa(w)
    if ws in _DET or ws in _PREP or ws in _PUENTE or len(w) < 3:
        return None
    try:
        an = M.analizar(w) or []
    except Exception:                                    # noqa
        return None
    if previo in _AUX:                                   # «ha comido»: el participio hace de verbo, con la persona del auxiliar
        l = next((a[0] for a in an if len(a) > 2 and a[1] == "part"), None)
        if l:
            return sa(l), {_AUX[previo]}
    if T._es_nombre(w):
        return None
    fin = [a for a in an if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut") and a[2] in ("1s", "1p", "3s", "3p")]   # «rotas» no es «tú rotas»
    if not fin:
        ger = next((a[0] for a in an if len(a) > 2 and a[1] == "ger"), None)
        return (sa(ger), {"ger"}) if ger else None
    return sa(fin[0][0]), {a[2] for a in fin}


def analiza(frase):
    """[(verbo, 'S'|'O', nombre)] de una frase simple."""
    from . import tema as T
    ws = re.findall(r"[a-záéíóúñü]+|[,;:]", (frase or "").lower())
    n = len(ws)
    S = [sa(w) for w in ws]
    verbos = {}
    for i, w in enumerate(ws):
        v = _verbo(w, S[i - 1] if i else None)
        if v and v[0] not in _NOV and S[i] not in _AUX:
            verbos[i] = v
    # sintagmas: determinante (+ una palabra) + nombre. Se apunta la cabeza y si lleva preposición delante
    cabezas = {}                                         # posición del nombre -> (lema, con_preposición, posición del determinante)
    for i in range(n):
        if S[i] in _DET or S[i] in ("al", "del"):
            j = i + 1
            if j < n and j not in verbos and S[j] not in _DET and S[j] not in _PREP and re.match(r"[a-zñ]", S[j]):
                prep = S[i] in ("al", "del") or (i > 0 and S[i - 1] in _PREP)
                cabezas[j] = (T.lema(ws[j]), prep, i)
    for i in range(n):                                   # nombre sin determinante justo detrás de un verbo: «come plátanos»
        if i - 1 in verbos and i not in cabezas and i not in verbos and S[i] not in _DET and S[i] not in _PREP and S[i] not in _PUENTE \
                and len(S[i]) >= 3 and re.match(r"[a-zñ]", S[i]) and T._es_nombre(ws[i]):
            cabezas[i] = (T.lema(ws[i]), False, i)
    out = []
    ult_suj = None
    for i in sorted(verbos):
        v, pers = verbos[i]
        suj = None
        tercera = bool(pers & {"3s", "3p", "ger"})
        if tercera:
            j = i - 1
            saltos = 0
            while j >= 0 and (S[j] in _PUENTE or (j not in cabezas and j not in verbos and saltos < 1 and S[j] not in _PREP and S[j] not in _DET and S[j] not in (",", ";", ":", "y", "e", "o"))):
                if S[j] not in _PUENTE:
                    saltos += 1                          # un adjetivo entre el nombre y el verbo
                j -= 1
            if j in cabezas and not cabezas[j][1]:
                if not (i > 0 and S[i - 1] == "se"):     # «la pasta se hierve»: no es ella la que hierve; no se apunta ni de sujeto ni de objeto
                    suj = cabezas[j][0]
            elif j >= 0 and S[j] in ("y", "e", ",") and ult_suj:
                suj = ult_suj                            # «salía de su madriguera Y comía hierba»: el mismo sujeto
            elif "ger" in pers and ult_obj_de(out):
                suj = ult_obj_de(out)                    # «vimos un cometa cruzando el cielo»
        k = i + 1
        if k < n and S[k] == "a":
            k += 1
        obj = None
        if k < n and (S[k] in _DET or S[k] in ("al",)) and k + 1 in cabezas and (not cabezas[k + 1][1] or S[k] == "al" or S[k - 1] == "a"):
            obj = cabezas[k + 1][0]
        elif k in cabezas and cabezas[k][2] == k:
            obj = cabezas[k][0]
        if suj and suj != obj:
            out.append((v, "S", suj))
            ult_suj = suj
        elif not tercera:
            ult_suj = None
        if obj:
            out.append((v, "O", obj))
    return out


def ult_obj_de(out):
    for v, r, nm in reversed(out):
        if r == "O":
            return nm
    return None


def _suma(R, tr, peso=1.0):
    for v, r, nm in tr:
        d = R.setdefault(r, {}).setdefault(v, {})
        d[nm] = d.get(nm, 0.0) + peso


def _fabrica():
    if "R" not in _F:
        from . import tema as T
        R = {"S": {}, "O": {}}
        try:
            with open(T.RUTA_CORPUS, encoding="utf-8") as fh:
                for linea in fh:
                    linea = linea.strip()
                    if not linea or linea.startswith("#"):
                        continue
                    for frase in re.split(r"(?<=[.!?])\s+", linea):
                        _suma(R, analiza(frase))
        except OSError:
            pass
        _F["R"] = R
    return _F["R"]


def aprende(nuc, texto):
    """Los papeles de lo que dice el usuario también cuentan (el triple, como en tema.py)."""
    if apagado() or not texto or "?" in texto:
        return
    U = nuc.usuario.setdefault("papeles", {"S": {}, "O": {}})
    for frase in re.split(r"(?<=[.!?])\s+|\n", texto)[:40]:
        _suma(U, analiza(frase))
    tot = sum(len(d) for r in ("S", "O") for d in U[r].values())
    if tot > MAX_USUARIO:
        for r in ("S", "O"):
            for v in list(U[r])[:len(U[r]) // 4]:
                del U[r][v]
    nuc._papeles_c = None


def _todo(nuc):
    c = getattr(nuc, "_papeles_c", None) if nuc is not None else _F.get("solo")
    if c is not None:
        return c
    F = _fabrica()
    U = (nuc.usuario.get("papeles") if nuc is not None else None) or {}
    R = {r: {v: dict(d) for v, d in F[r].items()} for r in ("S", "O")}
    for r in ("S", "O"):
        for v, d in (U.get(r) or {}).items():
            for nm, x in d.items():
                R[r].setdefault(v, {})[nm] = R[r].get(v, {}).get(nm, 0.0) + 3.0 * x
    if nuc is not None:
        nuc._papeles_c = R
    else:
        _F["solo"] = R
    return R


def _de_clase(nuc, bolsa, sin=()):
    from . import tema as T
    ms = set()
    for x in bolsa:
        ms |= T.miembros(x, nuc) | {sa(x)}
    return ms - {sa(x) for x in sin}


def propension(nuc, bolsa, sin=()):
    """(veces de sujeto, veces de objeto) de los miembros de una clase en todo lo leído."""
    R = _todo(nuc)
    ms = _de_clase(nuc, bolsa, sin)
    s = sum(x for d in R["S"].values() for nm, x in d.items() if nm in ms)
    o = sum(x for d in R["O"].values() for nm, x in d.items() if nm in ms)
    return s, o


def apoyo(nuc, papeles_w, bolsas, sin=()):
    """Puntos para cada sentido (una bolsa de clases por sentido) según los papeles que hace la palabra en la frase: [(puntos, detalle)]."""
    if apagado() or not papeles_w or len(bolsas) < 2:
        return [(0.0, "")] * len(bolsas)
    R = _todo(nuc)
    clases = [_de_clase(nuc, b, sin) for b in bolsas]
    prop = [propension(nuc, b, sin) for b in bolsas]
    pts = [0.0] * len(bolsas)
    det = [[] for _ in bolsas]
    for v, r in papeles_w:
        # 1) el verbo concreto: quiénes más hacen ese papel con ESE verbo
        n = [sum(x for nm, x in R[r].get(v, {}).items() if nm in ms) for ms in clases]
        if sum(n) >= 1.0:
            for i_ in range(len(bolsas)):
                q = n[i_] / sum(n)
                if q > 1.0 / len(bolsas):
                    pts[i_] += 2.0 * (q - 1.0 / len(bolsas)) * min(1.0, sum(n) / 2.0)
                    det[i_].append(f"{r}:{v}={n[i_]:.0f}/{sum(n):.0f}")
        # 2) la propensión de la clase a ese papel (solo con datos suficientes de las dos)
        if all(s + o >= 4 for s, o in prop):
            p = [((s if r == "S" else o) + 1.0) / (s + o + 2.0) for s, o in prop]
            m_ = sum(p) / len(p)
            for i_ in range(len(bolsas)):
                if p[i_] > m_:
                    pts[i_] += 3.0 * (p[i_] - m_)
                    det[i_].append(f"prop{r}={p[i_]:.2f}")
    return [(round(x, 3), " ".join(d)) for x, d in zip(pts, det)]
