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
    res = [(et, b, per, pr) for et, (b, per, pr) in out.items()]
    if sum(1 for f in res if f[3] >= 0.15) >= 2 and not os.environ.get("LCM_SIN_CLASE"):
        try:                                             # 2.31: con dos sentidos de la base o enseñados, uno que solo trae el léxico entra al reparto
            from . import tema as T                      # únicamente si el texto leído lo respalda (la palabra va con el vocabulario de ese sentido).
            def _resp(f):                                # «copa»–trofeo sí; «salmón»–río o «rosa»–ventana no: eran ruido
                return any(T.tema(nuc, w0, x, True) >= 0.25 for x in ({f[0]} | f[1]) if " " not in x)
            res = [f for f in res if f[3] >= 0.15 or _resp(f)]
        except Exception:                                # noqa
            pass
    return res


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
    try:                                                 # 2.31: por la CLASE de cada sentido. Una palabra del contexto apoya un sentido si va con otros miembros de esa clase
        from . import tema as T
        if not os.environ.get("LCM_SIN_TEMA") and not os.environ.get("LCM_SIN_CLASE"):
            for i_, (et, b, _, _) in enumerate(fs):
                v = 0.0
                for c, p in ctx.items():
                    t = T.afin_clase(nuc, c, et, sin=(w0,))
                    if t >= 0.2:
                        v += p * t
                puntos[i_] += 1.5 * v
    except Exception:                                    # noqa
        pass
    try:                                                 # 2.30: por las COMPAÑÍAS de la palabra, agrupadas. El contexto elige un grupo y el grupo dice el sentido
        from . import tema as T
        if not os.environ.get("LCM_SIN_TEMA"):
            gs = T.grupos(nuc, w0)
            apr = {sa(a["et"]): set(a["bolsa"]) for a in (nuc.usuario.get("acepciones") or {}).get(w0, [])}
            def _etiqueta(g):
                sol = {et: len(g & b_) for et, b_ in apr.items() if g & b_}            # lo aprendido del usuario manda
                if sol:
                    return max(sol, key=sol.get)
                en = [f[0] for f in fs if f[0] in g or (f[3] >= 0.15 and f[1] & g)]    # el nombre de un sentido está entre las compañías del grupo
                if len(en) == 1:
                    return en[0]
                if en:
                    return None
                todo = [f[0] for f in fs if f[3] >= 0.15 and any((_de_un_todo(w0, n) - _VAGOS) & (f[1] | {f[0]}) for n in g)]
                if len(todo) == 1:
                    return todo[0]                                                     # la palabra es PARTE de algo del grupo, y eso es de esa clase (ratón: ordenador: aparato)
                af = sorted(((sum(T.tema(nuc, n, f[0]) for n in g), f[0]) for f in fs if f[3] >= 0.15), reverse=True)
                if af and af[0][0] >= 0.8 and (len(af) < 2 or af[0][0] >= 2.0 * af[1][0]):
                    return af[0][1]                                                    # o el grupo entero va claramente con el nombre de un sentido
                return None
            ets = [_etiqueta(g) for g in gs]
            if not os.environ.get("LCM_SIN_CLASE"):                                    # 2.31: a un grupo sin nombre se le pone el del sentido con cuya CLASE van sus palabras
                for i_, g in enumerate(gs):                                            # («dinero, prestar, interés» van con oficinas y tiendas: es el edificio)
                    if ets[i_]:
                        continue
                    af = sorted(((sum(T.afin_clase(nuc, n_, f[0], sin=(w0,)) for n_ in g), f[0]) for f in fs if f[3] >= 0.15), reverse=True)
                    if af and af[0][0] >= 0.4 and (len(af) < 2 or af[0][0] >= 2.0 * af[1][0]):
                        ets[i_] = af[0][1]
            _et_de = {id(g): e for g, e in zip(gs, ets)}
            por = {}                                                                   # votos del contexto, sumados por sentido («sin» = grupos sin sentido conocido)
            for g in gs:
                v = sum(p * (1.0 if c in g else max((t for t in (T.tema(nuc, c, n) for n in g) if t >= 0.2), default=0.0)) for c, p in ctx.items())
                if v > 0:
                    e_ = _et_de.get(id(g)) or "sin"
                    d_ = por.setdefault(e_, [0.0, set()])
                    d_[0] += v
                    d_[1] |= g
            if por:
                orden_ = sorted(por.items(), key=lambda x: -x[1][0])
                e_, (v_, g_) = orden_[0]
                seg = orden_[1][1][0] if len(orden_) > 1 else 0.0
                if v_ >= 0.8 and v_ >= 1.3 * seg:
                    dest = next((i_ for i_, f in enumerate(fs) if f[0] == e_ or e_ in f[1]), None) if e_ != "sin" else None
                    if dest is not None:
                        puntos[dest] += 2.0 * v_
                        nuc._grupo230 = (w0, None, g_)
                    else:
                        nuc._grupo230 = (w0, "sin", g_)                                 # hay un grupo claro pero no se sabe qué sentido es: habrá que preguntar
    except Exception:                                    # noqa
        pass
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
    extra = set()
    g = getattr(nuc, "_grupo230", None)
    if g and g[0] == w0:
        extra = set(g[2])                                # y todo el grupo de compañías en el que caía la frase: se aprende el sentido entero, no una frase
    a["bolsa"] = sorted(set(a["bolsa"]) | extra | {c for c, p in (ctx or {}).items() if p >= 0.4 and len(c) > 3})[:60]


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
    # 2.31: lo que decide no es el sentido más probable, sino la SUMA de los sentidos en que la respuesta es «sí» frente a la de los que es «no».
    # Así dos caras del mismo sentido («documento» y «medio de comunicación» para la carta del buzón) no se quitan votos entre sí.
    si_ = [x for x in orden if es(x[0])]
    no_ = [x for x in orden if not es(x[0])]
    p_si, p_no = sum(x[1] for x in si_), sum(x[1] for x in no_)
    if os.environ.get("LCM_SIN_CLASE"):                  # como en la 2.30: solo cuenta el primero
        p_si, p_no = (p1, 0.0) if es(e1) else (0.0, p1)
        si_, no_ = ([orden[0]] if es(e1) else []), ([] if es(e1) else [orden[0]])
    pista_si = bool(si_) and (max(x[2] for x in si_) > 0 or bool(d.get("fijo")))
    pista_no = bool(no_) and (max(x[2] for x in no_) > 0 or bool(d.get("fijo")))
    r0 = (r_nucleo or {}).get("respuesta") or ""
    if defecto and es(defecto) and not (p_no >= X.SEGURO and pista_no):
        if p_si >= X.SEGURO and pista_si and re.match(r"^No\b", r0):
            return _ok(f"Sí: por lo que me has contado, hablamos de «{w0}» en el sentido de {si_[0][0]}.")
        return None                                      # lo que se pregunta encaja con el sentido de siempre y nada dice otra cosa: ni se duda ni se pregunta
    nuc._ult_prob229 = (w0, [(e, round(p, 2)) for e, p, _ in orden[:3]])
    otros = [e for e, _, _ in orden[1:] if es(e)]
    if p_si >= X.SEGURO and pista_si:
        return _ok(f"Sí: por lo que me has contado, hablamos de «{w0}» en el sentido de {si_[0][0]}.")
    if p_no >= X.SEGURO and pista_no:
        if si_ or re.match(r"^S[ií]\b", r0):
            return _ok(f"No: por lo que me has contado, hablamos de «{w0}» en el sentido de {no_[0][0]}, no de {_un(m.group(2).lower().strip())}.")
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
