"""LCM 2.28 · ACEPCIONES: una palabra, varios nodos.

Es el mismo problema que los tocayos, pero con las palabras: «banco» es un mueble y es una entidad; «cabo» es una cuerda y es un militar.
El núcleo tenía UN nodo por palabra, y por eso decía «No, un banco es un mueble» a «¿un banco es una entidad?», o deducía que «mi primo
es una cuerda» porque «mi primo es cabo». Aquí cada palabra tiene sus sentidos (los que trae el léxico de fábrica y los que enseña el
usuario) y se elige por lo que se sabe:

  · una pregunta sobre la palabra en general vale si la cumple ALGUNO de sus sentidos, y se dice que es «en uno de sus sentidos»;
  · de algo concreto se elige el sentido que casa con lo que ya se sabe de él: una persona que «es cabo» es el militar, no la cuerda.
"""
from __future__ import annotations

import os
import re

from .morfo import sa
from . import morfo as M

_ART = r"(?:un|una|el|la|los|las|unos|unas)"


def _lex():
    from . import vectores as V
    return V._grafo()


def _pos():
    c = getattr(_pos, "_c", None)
    if c is None:
        import json
        from . import vectores as V
        try:
            L = json.load(open(V.RUTA_LEXICO, encoding="utf-8"))
            c = {int(k): v for k, v in L["pos"].items()}
        except Exception:                                # noqa
            c = {}
        _pos._c = c
    return c


def sentidos(w):
    """Los sentidos de un nombre según el léxico (identificadores de concepto)."""
    w2s, _ = _lex()
    pos = _pos()
    w = w.lower()
    cands = {sa(w), sa(M.singular(w)), w, M.singular(w)}
    out = set()
    for c in cands:
        out |= {s for s in w2s.get(c, ()) if not pos or pos.get(s) == "n"}
    return out


def _anc(s, tope=14):
    _, hyp = _lex()
    out, f = set(), {s}
    for _ in range(tope):
        f = {p for x in f for p in hyp.get(x, ())} - out
        if not f:
            break
        out |= f
    return out


def cumple(w, z):
    """Los sentidos de `w` que son un `z` (por sí mismos o por sus clases)."""
    sz = sentidos(z)
    return [s for s in sentidos(w) if sz and ((_anc(s) | {s}) & sz)]


def es_persona(s):
    return bool((_anc(s) | {s}) & sentidos("persona"))


def _aprendidos(nuc, w):
    """Lo que el usuario ha dicho que es un `w` («un cabo es una cuerda», «un cabo también es un militar»)."""
    try:
        from . import conceptos as K
        return [sa(p) for p in K._padres_aprendidos(nuc, sa(M.singular(w)))]
    except Exception:                                    # noqa
        return []


def _ok(txt):
    return {"respuesta": txt, "estado": "ok", "consultar": False, "tipo": "resp"}


def _un(w):
    try:
        return ("una " if M.genero_sust(sa(w)) == "f" else "un ") + w
    except Exception:                                    # noqa
        return "un " + w


def responde(nuc, q, r_nucleo):
    """Enmienda al núcleo cuando contestó mirando UN solo sentido de una palabra que tiene varios."""
    if os.environ.get("LCM_SIN_ACEPCIONES") or "?" not in q or not isinstance(r_nucleo, dict):
        return None
    txt = r_nucleo.get("respuesta") or ""
    t = q.strip()
    try:
        # 1) la palabra en general: «¿un banco es una entidad?»  ->  el núcleo dijo «No, un banco es un mueble»
        m = re.match(r"^¿?\s*(?:y\s+)?" + _ART + r"\s+([a-záéíóúñü]+)\s+(?:es|son)\s+" + _ART + r"\s+([a-záéíóúñü]+)\s*\?$", t, re.I)
        if m and re.match(r"^No\b", txt):
            w, z = m.group(1).lower(), m.group(2).lower()
            if cumple(w, z) and len(sentidos(w)) > 1:
                otro = re.sub(r"^No[,.:]?\s*", "", txt).rstrip(".")
                return _ok(f"Sí, en uno de sus sentidos: «{w}» tiene varios, y en uno {_un(w)} es {_un(z)}." + (f" En otro, {otro}." if otro and len(otro) < 120 else ""))
            if sa(M.singular(z)) in _aprendidos(nuc, w):
                return _ok(f"Sí, en uno de sus sentidos: me dijiste que {_un(w)} también es {_un(z)}.")
            return None
        # 2) alguien concreto: «¿mi primo es una cuerda?» tras «mi primo es cabo» y «un cabo es una cuerda» / «…también es un militar»
        m = re.match(r"^¿?\s*(?:y\s+)?((?:mi|mis|tu)\s+[a-záéíóúñü]+|[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+)\s+(?:es|son)\s+" + _ART + r"\s+([a-záéíóúñü]+)\s*\?$", t)
        if m and re.match(r"^S[ií]\b", txt) and "deduzco" in txt:
            from . import grafo as G
            e = G._ent(nuc, m.group(1))
            z = sa(M.singular(m.group(2).lower()))
            if not e or not (e == "U" or nuc._persona_por_rol(e)):
                return None
            for f in nuc.F:                              # lo que se dijo que ES esa persona
                if not f.get("vig", True) or f.get("neg") or f.get("v") != "ser" or nuc.can(f.get("s") or "") != e:
                    continue
                for w in re.findall(r"\b(?:es|son|soy|era)\s+(?:un\s+|una\s+)?([a-záéíóúñü]+)", (f.get("src") or "").lower()):   # lo que va tras «es»: «mi primo es CABO»
                    ap = _aprendidos(nuc, w)
                    ss = sentidos(w)
                    if z not in ap and not cumple(w, z) and not re.search(r"\b" + re.escape(w) + r"\b", txt.lower()):
                        continue                         # la deducción del núcleo tiene que pasar por esa palabra
                    de_persona = [p for p in ap if any(es_persona(s) for s in sentidos(p))] + [s for s in ss if es_persona(s)]
                    z_persona = any(es_persona(s) for s in sentidos(z))
                    if de_persona and not z_persona:
                        cual = next((p for p in ap if any(es_persona(s) for s in sentidos(p))), None)
                        return _ok(f"No. «{w}» tiene varios sentidos y {nuc.disp(e)} es una persona" + (f": es {w} en el sentido de {cual}." if cual else "."))
    except Exception:                                    # noqa
        return None
    return None
