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
        r0 = _aclara(nuc, q, r_nucleo)                   # 2.29: el sentido más probable por el contexto
        if r0 is not None:
            return r0
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


# ---------------------------------------------------------------- 2.29: el sentido más probable por el contexto
_VAGOS = {"entidad", "objeto", "cosa", "artefacto", "todo", "unidad", "ser", "organismo", "abstraccion", "grupo", "medida", "cantidad", "parte", "lugar", "estado", "accion",
          "acto", "actividad", "suceso", "relacion", "atributo", "propiedad", "comunicacion", "instrumentalidad", "objeto fisico", "materia", "sustancia", "persona", "individuo", "elemento"}


def _syn():
    c = getattr(_syn, "_c", None)
    if c is None:
        import json
        from . import vectores as V
        try:
            L = json.load(open(V.RUTA_LEXICO, encoding="utf-8"))
            c = {int(k): v for k, v in L["syn"].items()}
        except Exception:                                # noqa
            c = {}
        _syn._c = c
    return c


def firmas(nuc, w):
    """Los sentidos de una palabra, cada uno con su etiqueta y su bolsa de palabras: [(etiqueta, bolsa, es_de_persona, previo)].
    Salen de la base de conceptos de fábrica (primero: es el sentido por defecto), del léxico (sinónimos y clases de cada sentido) y de lo
    que haya enseñado el usuario o se haya aprendido de sus respuestas."""
    from . import conceptos as K
    w0 = sa(M.singular(w.lower()))
    syn = _syn()
    _, hyp = _lex()
    out = {}
    try:
        padres = list(dict.fromkeys(K.kb()["isa"].get(w0, [])))
    except Exception:                                    # noqa
        padres = []
    for n_, p in enumerate(padres):
        try:
            anc = [sa(a) for a in K.ancestros(p)]
        except Exception:                                # noqa
            anc = []
        if any(set([sa(p)] + anc) - _VAGOS <= set(b_) for _, (b_, _, _) in out.items()):
            continue                                     # misma rama que un sentido ya puesto («recipiente» y «vajilla»)
        out[sa(p)] = [set([sa(p)] + anc) - _VAGOS, "persona" in anc, 0.5 if n_ == 0 else 0.15]
    for s in sorted(sentidos(w)):
        ps_ = [p for p in hyp.get(s, ())]
        nivel2 = [q for p in ps_ for q in hyp.get(p, ())]
        bolsa = {sa(x) for x in syn.get(s, []) if " " not in x} | {sa(x) for p in ps_ + nivel2 for x in syn.get(p, [])[:3] if " " not in x}
        bolsa -= {w0} | _VAGOS
        et = next((sa(x) for p in ps_ for x in syn.get(p, []) if " " not in x and sa(x) != w0), None) or next((sa(x) for x in syn.get(s, []) if sa(x) != w0 and " " not in x), None)
        if not et or et in _VAGOS or not bolsa or et[:4] == w0[:4]:
            continue
        ya = next((e for e, (b_, _, _) in out.items() if b_ & bolsa), None)   # el mismo sentido que uno de fábrica: se suman
        d = out.setdefault(ya or et, [set(), False, 0.1])
        d[0] |= bolsa
        d[1] = d[1] or es_persona(s)
    for a in (nuc.usuario.get("acepciones") or {}).get(w0, []):
        ya = next((e for e, (b_, _, _) in out.items() if sa(a["et"]) in b_ or e == sa(a["et"]) or sa(a["et"]) in e.split()), None)
        d = out.setdefault(ya or sa(a["et"]), [set(), False, 0.15])
        d[0] |= set(a["bolsa"])
        d[1] = d[1] or any(es_persona(s) for s in sentidos(a["et"]))
    return [(et, b, per, pr) for et, (b, per, pr) in out.items()]


def _de_un_todo(w0, c):
    """¿Es `w0` una parte de `c` según la base de conceptos? («ratón» lo es de «ordenador»). Devuelve las clases de `c`."""
    from . import conceptos as K
    try:
        kb = K.kb()
        if w0 in [sa(x) for x in kb["partes"].get(c, [])] or c in [sa(x) for x in kb["parte_de"].get(w0, [])]:
            return {c} | {sa(a) for a in K.ancestros(c)}
    except Exception:                                    # noqa
        pass
    return set()


def reparto(nuc, w, frase="", ctx=None):
    """[(etiqueta, probabilidad, puntos)] de mayor a menor, con la frase de ahora y la caché de contexto."""
    from . import contexto as X
    fs = firmas(nuc, w)
    if len(fs) < 2:
        return []
    w0 = sa(M.singular(w.lower()))
    if ctx is None:
        ctx = X.palabras(nuc, frase)
    ctx = {c: p for c, p in ctx.items() if c != w0}
    puntos = []
    for et, b, _, _ in fs:
        pt = X.casa(ctx, b | {et})
        for c, p in ctx.items():                         # y lo que es parte de qué: un ratón «del ordenador» es el aparato
            if (_de_un_todo(w0, c) - _VAGOS) & (b | {et}):
                pt += 2.0 * p
        puntos.append(pt)
    ps = X.reparte(puntos, [f[3] for f in fs])
    return sorted(zip([f[0] for f in fs], ps, puntos), key=lambda x: -x[1])


def apunta(nuc, texto):
    """Con cada frase DICHA: (1) si enseña un sentido («un X también es un Y …») se guarda; (2) de cada palabra con varios sentidos que
    aparezca se guarda el contexto en que se dijo, para elegir sentido cuando luego se pregunte por ella."""
    from . import contexto as X
    if X.apagado() or os.environ.get("LCM_SIN_ACEPCIONES") or not texto or "?" in texto:
        return
    t = texto.strip()
    m = re.match(r"^(?:un|una|el|la)\s+([a-záéíóúñü]+)\s+(tambi[eé]n\s+)?es\s+(?:un|una)\s+([a-záéíóúñü]+)\b(.*)$", t, re.I)
    if m:
        w0, et = sa(M.singular(m.group(1).lower())), sa(M.singular(m.group(3).lower()))
        A = nuc.usuario.setdefault("acepciones", {}).setdefault(w0, [])
        if not any(a["et"] == et for a in A):
            A.append({"et": et, "bolsa": sorted({et} | set(X.lemas(m.group(4))))})
        return
    S = getattr(nuc, "_sent229", None)
    if S is None:
        S = nuc._sent229 = {}
    ctx = X.palabras(nuc, t)
    for w in dict.fromkeys(re.findall(r"[a-záéíóúñü]{4,}", t.lower())):
        w0 = sa(M.singular(w))
        if w0 in S and S[w0].get("fijo"):
            continue
        if len(firmas(nuc, w)) >= 2:
            S[w0] = {"ctx": {c: p for c, p in ctx.items() if c != w0}, "turno": nuc.turno}
    if len(S) > 12:
        for k_ in sorted(S, key=lambda k_: S[k_]["turno"])[:-12]:
            del S[k_]


def _aprende(nuc, w0, et, ctx):
    """El usuario ha dicho de qué sentido hablaba: las palabras que había alrededor quedan asociadas a ese sentido."""
    A = nuc.usuario.setdefault("acepciones", {}).setdefault(w0, [])
    a = next((x for x in A if x["et"] == et), None)
    if a is None:
        a = {"et": et, "bolsa": [et]}
        A.append(a)
    a["bolsa"] = sorted(set(a["bolsa"]) | {c for c, p in (ctx or {}).items() if p >= 0.4 and len(c) > 3})[:40]


def _aclara(nuc, q, r_nucleo):
    """«¿mi copa es un premio?», «¿el ratón es un animal?»: según el sentido más probable por el contexto; si no está claro y la respuesta
    depende de ello, SE PREGUNTA, y de la respuesta se aprende."""
    from . import contexto as X
    if X.apagado():
        return None
    S = getattr(nuc, "_sent229", None)
    if S is None:
        S = nuc._sent229 = {}
    pend = getattr(nuc, "_sent_pend229", None)
    nuc._sent_pend229 = None
    t = q.strip()
    m = re.match(r"^¿?\s*(?:y\s+)?(?:mi|mis|el|la|los|las|ese|esa|aquel|aquella)\s+([a-záéíóúñü]+)\s+(?:es|son)\s+(?:un|una|unos|unas)\s+([a-záéíóúñü ]+?)\s*\?$", t, re.I)
    if not m:
        return None
    w0, z = sa(M.singular(m.group(1).lower())), sa(M.singular(m.group(2).lower().split()[-1]))
    zc = sa(m.group(2).lower().strip())
    d = S.get(w0)
    if not d:
        return None
    try:
        from . import grafo as G
        if G._canon(w0):
            return None                                  # «mi primo», «mi jefa»: es una persona por su papel; aquí no hay sentido que elegir
    except Exception:                                    # noqa
        pass
    fl = firmas(nuc, w0)
    fs = {f[0]: f for f in fl}
    if d.get("fijo"):
        orden = [(d["fijo"], 1.0, 9.0)]
    else:
        orden = reparto(nuc, w0, ctx=d.get("ctx") or {})
    if not orden:
        return None

    def es(et):
        f = fs.get(et)
        return bool(f) and (z == et or zc == et or z in et.split() or z in f[1] or zc in f[1] or X.parecido(z, et) >= 0.6 or any(X.parecido(z, b) >= 0.75 for b in f[1]))
    e1, p1, pt1 = orden[0]
    defecto = next((f[0] for f in fl if f[3] >= 0.5), None)
    if defecto and es(defecto) and not (p1 >= X.SEGURO and e1 != defecto and pt1 > 0):
        if e1 == defecto and p1 >= X.SEGURO and pt1 > 0 and re.match(r"^No\b", (r_nucleo or {}).get("respuesta") or ""):
            return _ok(f"Sí: por lo que me has contado, hablamos de «{w0}» en el sentido de {e1}.")
        return None                                      # lo que se pregunta encaja con el sentido de siempre y nada dice otra cosa: ni se duda ni se pregunta
    nuc._ult_prob229 = (w0, [(e, round(p, 2)) for e, p, _ in orden[:3]])
    otros = [e for e, _, _ in orden[1:] if es(e)]
    if p1 >= X.SEGURO and (pt1 > 0 or d.get("fijo")):
        if es(e1):
            return _ok(f"Sí: por lo que me has contado, hablamos de «{w0}» en el sentido de {e1}.")
        if otros or re.match(r"^S[ií]\b", (r_nucleo or {}).get("respuesta") or ""):
            return _ok(f"No: por lo que me has contado, hablamos de «{w0}» en el sentido de {e1}, no de {_un(m.group(2).lower().strip())}.")
        return None
    if not defecto and pt1 <= 0 and not (nuc.usuario.get("acepciones") or {}).get(w0):
        return None                                      # ni sentido de fábrica, ni enseñado, ni pista: no hay base para dudar
    if otros and not es(e1):                             # la respuesta depende del sentido y el contexto no lo deja claro: se pregunta
        ops = [e1, otros[0]]
        nuc._sent_pend229 = {"turno": nuc.turno, "w": w0, "ops": ops, "texto": t, "ctx": d.get("ctx") or {}}
        return {"respuesta": f"«{w0}» tiene varios sentidos y no tengo claro de cuál hablamos: ¿{ops[0]} o {ops[1]}?", "estado": "ok", "consultar": False, "tipo": "pregunta"}
    return None


def pendiente(nuc, texto):
    """La respuesta del usuario a «¿taza o premio?»: se fija el sentido, se aprende su contexto y se retoma la pregunta."""
    pend = getattr(nuc, "_sent_pend229", None)
    if not pend or nuc.turno - pend["turno"] > 1 or len(texto.split()) > 4:
        return None
    n = sa(texto.lower())
    for et in pend["ops"]:
        if re.search(r"\b" + re.escape(et[:5]), n):
            nuc._sent_pend229 = None
            S = getattr(nuc, "_sent229", None) or {}
            S[pend["w"]] = {"fijo": et, "ctx": pend["ctx"], "turno": nuc.turno}
            nuc._sent229 = S
            _aprende(nuc, pend["w"], et, pend["ctx"])
            return pend["texto"]
    return None
