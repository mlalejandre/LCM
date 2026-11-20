"""LCM 2.17 · Iniciativa: el LCM deja de ser solo reactivo.

Tres piezas, todas apoyadas en la base de conceptos (secciones [huecos] y [tono]) y en los marcos de la memoria:
  - curiosidad por huecos: lo que se cuenta deja casillas vacías (adónde, cómo se llama, qué pasó) o usa una palabra que no conoce -> UNA pregunta;
  - tono: una buena o mala noticia se recibe como tal antes de apuntarla;
  - contención: nunca más de una pregunta, ninguna si la persona acaba de preguntar o de contestar, ninguna en un duelo, ninguna si pide que no se le pregunte.
La respuesta a la pregunta se integra en el hecho original (se relee la frase completa con el dato nuevo): no hay casillas rellenadas a mano."""
import re
from . import conceptos as K, morfo as M
from .nucleo import sa, cambia_persona, causa_tu

_PREP = r"(?:a|al|en|hacia|para|con|de|del|desde|por)"
_NO_DICE = re.compile(r"^\W*(?:prefiero no (?:decir|contar|hablar)\w*.*|no (?:lo )?s[eé]|ni idea|no (?:te )?lo (?:quiero|voy a) (?:decir|contar)|no quiero (?:decirlo|contarlo|hablar de (?:eso|ello|el tema))|"
                      r"da igual|d[eé]jalo|no importa|es igual|paso|mejor no|eso no|no me acuerdo|todav[ií]a no lo s[eé]|a[uú]n no lo s[eé]|no tiene nombre)\W*$", re.I)


_DIAS = r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bados?|domingos?)"
_MES = r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"


def base_dim(w):
    """«perrita», «gatito», «casita»: el diminutivo es el mismo concepto. Devuelve la base si la base de conceptos la conoce."""
    w0 = sa(w)
    kb = K.kb()
    for suf in ("citos", "citas", "cito", "cita", "itos", "itas", "ito", "ita", "illos", "illas", "illo", "illa", "icos", "icas", "ico", "ica", "ines", "in", "ina"):
        if w0.endswith(suf) and len(w0) - len(suf) >= 3:
            raiz = w0[:-len(suf)]
            if raiz.endswith("qu"):
                raiz = raiz[:-2] + "c"
            elif raiz.endswith("gu"):
                raiz = raiz[:-1]
            for c in (raiz + "o", raiz + "a", raiz, raiz + "e", raiz + "on"):
                if c in kb["isa"] or c in kb["hijos"]:
                    return c
    return None


def _cap(x):
    return x[:1].upper() + x[1:] if x else x


def _une(xs):
    xs = [x for x in xs if x]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def estado(nuc):
    d = nuc.usuario.setdefault("inic", {})
    d.setdefault("off", False); d.setdefault("hechas", []); d.setdefault("pend", None); d.setdefault("ult_q", -9)
    return d


def _nombre(nuc):
    n = (nuc.usuario.get("nombre") or nuc.E.get("U", {}).get("nombre") or "").strip()
    return ", " + n if n else ""


# ------------------------------------------------------------------ conocimiento: claves de un marco
def _clases(nuc, f):
    """Clases (con ancestros) de lo que nombra el marco: objeto y complementos. Devuelve lista de (clase, origen)."""
    out = []

    def mete(c, de):
        c = sa(c or "").strip()
        if not c:
            return
        if not K.ancestros(c) and not K.ancestros(c.split()[0]) and base_dim(c.split()[0]):
            c = base_dim(c.split()[0])
        for x in [c, c.split()[0]] + list(K.ancestros(c)) + list(K.ancestros(c.split()[0])):
            if (x, de) not in out:
                out.append((x, de))
    if f.get("obj_cls"):
        mete(f["obj_cls"], "obj")
        try:
            from .nucleo import FAMILIA
            if f["obj_cls"] in FAMILIA or M.masc(f["obj_cls"]) in FAMILIA:
                out.append(("familiar", "obj"))
        except Exception:                                # noqa
            pass
    for i, c in enumerate(f.get("comps") or []):
        e = c[1] or ""
        if str(e).startswith(("K:", "I:")):
            mete(str(e)[2:].split("@")[0], "c%d" % i)
        elif c[2]:
            w = sa(re.sub(r"^(?:el|la|los|las|un|una|mi|mis|tu|tus|su|sus)\s+", "", c[2].lower()))
            mete(M.singular(w.split()[0]) if w else "", "c%d" % i)
    return out


def _busca(tabla, nuc, f):
    """Clave de la tabla que casa con el marco: «verbo clase» antes que «verbo», y después atributo y clase sola."""
    v = f.get("v") or ""
    cls = _clases(nuc, f)
    for c, de in cls:
        if v + " " + c in tabla:
            return v + " " + c, de
    if v in tabla:
        return v, ""
    for a in f.get("attr") or []:
        if M.masc(sa(a)) in tabla:
            return M.masc(sa(a)), "attr"
        if v == "ser":                                   # «he sido despedido»: el participio lleva al verbo
            lem = [x[0] for x in (M.analizar(M.masc(sa(a))) or []) if x[1] == "part"]
            if lem and lem[0] in tabla:
                return lem[0], "part"
    for c, de in cls:
        if c in tabla:
            return c, de
    return None, ""


# ------------------------------------------------------------------ tono
_REACCION = {"logro": ["¡Enhorabuena{n}!", "¡Qué buena noticia{n}! Enhorabuena."], "bueno": ["¡Qué bien{n}!", "¡Me alegro{n}!"], "felicidades": ["¡Felicidades{n}!"],
             "malo": ["Vaya, lo siento{n}.", "Lo siento{n}."], "duelo": ["Lo siento mucho{n}."], "reto": ["¡Mucha suerte{n}!", "¡Ánimo{n}, mucha suerte!"]}


def tono(nuc, f):
    tabla = K.kb().get("tono") or {}
    clave, de = _busca(tabla, nuc, f)
    if not clave:
        return None
    t = tabla[clave]
    verbal = clave.split()[0] == f.get("v")
    if de == "part":
        return None if (f.get("neg") or (t == "reto" and f.get("t") in ("pret", "imp"))) else t
    if f.get("neg"):                                     # «no he aprobado» es una mala noticia; «no tengo hijos» no es ninguna noticia
        return "malo" if (t == "logro" and verbal and f.get("t") == "pret" and f.get("v") not in ("tener", "casar")) else None
    if verbal and f.get("t", "pres") == "pres" and not f.get("cuando") and not f.get("exp") and t != "reto":
        return None                                      # «gano 2000 euros al mes» es una costumbre, no una noticia
    if t == "reto" and f.get("t") in ("pret", "imp"):
        return None                                      # el examen de ayer ya pasó
    if t in ("logro", "reto") and f.get("freq"):
        return None
    return t


def _reaccion(nuc, t, f):
    s = nuc.can(f["s"]) if f.get("s") else None
    op = _REACCION[t]
    txt = op[nuc.turno % len(op)].format(n=_nombre(nuc) if nuc.turno % 3 == 0 else "")
    if t == "reto" and s != "U":
        txt = "Espero que vaya bien."
    if t == "malo" and s not in ("U", None) and f.get("v") == "estar":
        txt = "Vaya, lo siento. Espero que se mejore."
    return txt


# ------------------------------------------------------------------ huecos
def _lleno(nuc, f, hueco, de):
    comps = f.get("comps") or []
    if hueco == "destino":
        tiempo = r"^(?:el |la |los |las )?(?:" + _MES[3:-1] + r"|verano|invierno|primavera|otono|navidad(?:es)?|semana santa|vacaciones|\d{4}|\d+ (?:dias|semanas|meses)|unos dias|puente)\b"
        return any(c[0] in ("a", "hacia", "para", "en") and ("c%d" % i) != de and not (c[0] in ("en", "para") and re.match(tiempo, sa(c[2] or "")))
                   for i, c in enumerate(comps)) or bool(f.get("lugar_adv"))
    if hueco == "con":
        return any(c[0] == "con" for c in comps)
    if hueco == "causa":
        return bool(f.get("causa")) or bool(re.search(r"\b(?:porque|por que|ya que|por culpa)\b", sa(f.get("src", ""))))
    if hueco == "nombre":
        o = f.get("obj")
        if o and nuc.E.get(nuc.can(o), {}).get("nombre"):
            return True
        if o and str(nuc.can(o)).startswith("N:"):
            return True
        cl = f.get("obj_cls")
        return any(d.get("nombre") and d.get("clase") == cl and d.get("dueno") in ("U", None) and e not in ("U", "L") for e, d in nuc.E.items())
    if hueco == "resultado":
        return f.get("t") not in ("pret", "imp") or bool(f.get("modo")) or any(g.get("v") in ("salir", "ir") and g.get("vig", True) and sa((g.get("suj_txt") or "") + " " + str(g.get("s") or "")).find(sa(f.get("obj_cls") or "#")) >= 0 for g in nuc.F)
    if hueco == "cual":
        return len((f.get("obj_disp") or "").split()) > 2 or bool(comps)
    if hueco == "quien":
        if f.get("v") == "conocer":
            return not any(sa(c[2] or "") == "alguien" for c in comps)
        return False
    return False


def _plural(f):
    c = f.get("cuant")
    if isinstance(c, (int, float)) and c > 1:
        return True
    return bool(f.get("pl_obj")) and c is None and sa(f.get("obj_disp") or "").endswith("s")


def hueco(nuc, f):
    """(hueco, pregunta, clave) del primer hueco abierto y no preguntado del marco, o None."""
    if not f.get("s") or nuc.can(f["s"]) != "U" or f.get("neg") or f.get("efecto") or not f.get("vig", True):
        return None
    if f.get("freq") or any(sa(x) in ("mucho", "poco", "siempre", "nunca", "a menudo", "normalmente", "bastante") for x in f.get("modo") or []):
        return None                                      # una costumbre («viajo mucho») no es un plan con casillas por rellenar
    tabla = K.kb().get("huecos") or {}
    v = f.get("v") or ""
    claves = [(v + " " + c, de) for c, de in _clases(nuc, f) if v + " " + c in tabla] + ([(v, "")] if v in tabla else [])
    hechas = estado(nuc)["hechas"]
    for clave, de in claves:
        for h, preg in tabla[clave]:
            marca = "%s|%s|%s" % (h, clave, f.get("obj_cls") or "")
            if marca in hechas or _lleno(nuc, f, h, de):
                continue
            if h == "nombre" and _plural(f):
                preg = "¿Cómo se llaman?"
            return h, preg, marca
    return None


def _conocida(nuc, w):
    from . import coloquial as Q, relaciones as R
    w0 = sa(w)
    if len(w0) < 4 or not w0.isalpha() or base_dim(w0):
        return True
    from . import lengua as G
    for x in {w0, sa(M.singular(w)), M.masc(sa(M.singular(w)))}:
        if Q._conocida(x) or G._comun_conocida(x) or x in K.kb()["forma"] or x in K.kb()["alias"]:
            return True
        if any(x in (d or {}) for d in R.ENSENADO.values() if isinstance(d, dict)):
            return True
        if x in (nuc.usuario.get("significa") or {}) or x in (nuc.usuario.get("partes") or {}) or x in (nuc.usuario.get("ant") or {}):
            return True
        if any(f.get("s") == "K:" + x and (f.get("isa") or f.get("attr")) for f in nuc.F):
            return True
    return False


def persona_nueva(nuc, f, n_af):
    """Alguien a quien se nombra por primera vez y de quien no se sabe nada: «he quedado con Marta» -> ¿quién es Marta?"""
    for c in f.get("comps") or []:
        e = c[1]
        if not e or not str(e).startswith("N:") or not (c[0] == "con" or (c[0] == "a" and f.get("v") in ("conocer", "ver", "llamar", "visitar", "invitar", "escribir"))):
            continue
        e = nuc.can(e)
        d = nuc.E.get(e, {})
        if d.get("lugar") or d.get("cosa") or d.get("clase") or d.get("pl") or not d.get("nombre"):
            continue
        if any(r_.get("x") == e or r_.get("y") == e for r_ in nuc.R):
            continue
        visto = False
        for g in nuc.F[:n_af]:
            if nuc.can(g.get("s") or "") == e or nuc.can(g.get("obj") or "") == e or any(nuc.can(x[1] or "") == e for x in g.get("comps") or []):
                visto = True
                break
        if not visto:
            return e, d["nombre"]
    return None


def enlace(nuc, f, n_af):
    """Lo que se acaba de contar toca un sitio del que ya se habló: se recuerda («me voy a Lisboa» -> allí vive tu prima)."""
    st = estado(nuc)
    for c in f.get("comps") or []:
        e = c[1]
        if not e or c[0] not in ("a", "en", "hacia") or not str(e).startswith("N:"):
            continue
        e = nuc.can(e)
        if not nuc.E.get(e, {}).get("lugar") or ("enlace|" + e) in st["hechas"]:
            continue
        for g in reversed(nuc.F[:n_af]):
            if not g.get("vig", True) or g.get("neg") or g.get("efecto") or g.get("src") == f.get("src") or g.get("turno", 0) >= f.get("turno", 0) - 1:
                continue
            if nuc.can(g.get("s") or "") == "U" and g.get("v") == f.get("v"):
                continue
            if any(nuc.can(x[1] or "") == e and x[0] in ("en", "a", "de") for x in g.get("comps") or []):
                st["hechas"].append("enlace|" + e)
                return "Por cierto, me contaste que %s." % nuc.frase(g)
    return None


def palabra_nueva(nuc, f):
    """Nombre común que el LCM no ha visto nunca en lo que se acaba de contar: (palabra, «un/una palabra»)."""
    src = f.get("src") or ""
    cands = []
    if f.get("obj_cls") and str(f.get("obj") or "").startswith(("I:", "K:")):
        cands.append((f["obj_cls"].split()[0], f.get("obj_disp") or ""))
    for c in f.get("comps") or []:
        if c[2] and not str(c[1] or "").startswith("N:"):
            m = re.search(r"\b(el|la|un|una|los|las|mi|mis)\s+([a-záéíóúñü]+)\s*$", c[2])
            if m:
                cands.append((m.group(2), m.group(1) + " " + m.group(2)))
            m = re.search(r"\bde\s+([a-záéíóúñü]+)\s*$", c[2])
            if m:
                cands.append((m.group(1), "el " + m.group(1)))
            if re.fullmatch(r"[a-záéíóúñü]{4,}", c[2]) and c[0] in ("de", "a"):
                cands.append((c[2], "el " + c[2]))
    for w, disp in cands:
        if re.search(r"(?<!^)(?<![.!?] )\b" + re.escape(w[:1].upper() + w[1:]) + r"\b", src):
            continue                                     # con mayúscula en mitad de la frase: es un nombre propio
        if _conocida(nuc, w):
            continue
        m = re.search(r"\b(el|la|un|una|los|las|mi|mis)\s+(" + re.escape(w) + r"\w*)", disp or src, re.I) or re.search(r"\b(el|la|un|una|los|las|mi|mis)\s+(" + re.escape(w[:4]) + r"\w*)", src, re.I)
        if disp.startswith("el ") and not re.search(r"\b(?:el|la|un|una)\s+" + re.escape(w), src, re.I):
            return sa(w), "«" + w + "»"                  # «clases de frupe»: no se sabe ni el género
        det = (m.group(1).lower() if m else "un")
        art = {"el": "un", "la": "una", "los": "unos", "las": "unas", "mi": "un", "mis": "unos"}.get(det, det)
        forma = m.group(2).lower() if m else w
        if art == "un" and det == "mi" and forma.endswith("a"):
            art = "una"
        return sa(w), art + " " + forma
    return None


# ------------------------------------------------------------------ después de una afirmación
_POS = {"mejor", "bien", "genial", "fenomenal", "estupendamente", "contento", "feliz", "tranquilo", "animado", "recuperado", "curado"}


def despues(nuc, texto, r, n_af):
    """Tras apuntar lo que la persona cuenta: recibe la noticia con su tono y, si procede, hace UNA pregunta."""
    if not isinstance(r, dict) or r.get("estado") != "ok" or not texto or "?" in texto or getattr(nuc, "_leyendo", False):
        return r
    st = estado(nuc)
    resp = r.get("respuesta") or ""
    if st["off"] and "¿" in resp and r.get("tipo") != "resp":
        limpio = re.sub(r"\s*¿[^?]*\?", "", resp).strip()
        if limpio:
            r = dict(r); r["respuesta"] = resp = limpio
    nuevos = [f for f in nuc.F[n_af:] if not f.get("efecto") and not f.get("deducido") and not f.get("fab")]
    if not nuevos or r.get("tipo") != "ack":
        return r
    if not re.match(r"^\W*(?:entendido|vale|de acuerdo|anotado|apuntado|lo apunto)\b", sa(resp)):
        return r                                         # ya es una respuesta con voz propia (corrección, saludo, conflicto…)
    for f in nuevos:                                     # «ya estoy mejor» deja atrás el «estoy preocupado» de antes
        if f.get("v") == "estar" and nuc.can(f["s"]) == "U" and not f.get("neg") and any(M.masc(sa(a)) in _POS for a in f.get("attr") or []):
            from .social import NEGATIVAS
            for g in nuc.F[:n_af]:
                if g.get("v") == "estar" and g.get("vig", True) and g.get("s") and nuc.can(g["s"]) == "U" and any(M.masc(sa(a)) in NEGATIVAS for a in g.get("attr") or []):
                    g["vig"] = False
                    try:
                        nuc._espejo(g, quitar=True)
                    except Exception:                    # noqa
                        pass
            return dict(r, respuesta="¡Me alegro%s! %s" % (_nombre(nuc) if nuc.turno % 3 == 0 else "", resp))
    for f in nuevos:                                     # «me he quedado embarazada», «estoy cansada»: quien habla es una mujer
        if nuc.can(f["s"] or "") == "U" and not nuc.E["U"].get("gen"):
            for a_ in f.get("attr") or []:
                m_, fe_ = M.masc(sa(a_)), M.masc(sa(a_))[:-1] + "a"
                if m_.endswith("o") and re.search(r"\b" + fe_ + r"\b", sa(texto.lower())):
                    nuc.E["U"]["gen"] = "f"
                    resp = re.sub(r"\b" + re.escape(nuc._acento(m_)) + r"\b", nuc._acento(m_)[:-1] + "a", resp)
                    r = dict(r, respuesta=resp)
    personal = [f for f in nuevos if f.get("s") and (nuc.can(f["s"]) == "U" or not str(nuc.can(f["s"])).startswith("K:"))]
    t = None
    for f in personal:
        t = tono(nuc, f)
        if t:
            ft = f
            break
    pre = _reaccion(nuc, t, ft) if t else ""
    if t == "duelo":
        return dict(r, respuesta=pre)
    preg = None
    if not st["off"] and st["ult_q"] != nuc.turno - 1 and "¿" not in resp and t not in ("malo", "logro", "felicidades") and len(texto.split()) <= 14 \
            and not re.match(r"^\W*(?:apunta|anota|recuerda|acu[eé]rdate|no olvides|ten en cuenta)\b", texto, re.I):
        for f in nuevos:
            if not f.get("s") or nuc.can(f["s"]) != "U":
                continue
            pn = palabra_nueva(nuc, f)
            if pn and ("que_es|" + pn[0]) not in st["hechas"]:
                preg = "¿Qué es %s? Es la primera vez que oigo esa palabra." % pn[1].replace("«", "").replace("»", "")
                st["hechas"].append("que_es|" + pn[0])
                st["pend"] = {"h": "que_es", "w": pn[0], "disp": pn[1], "turno": nuc.turno, "src": f.get("src", ""), "ft": f.get("turno")}
                break
            h = hueco(nuc, f)
            if h:
                preg = h[1]
                st["hechas"].append(h[2])
                st["pend"] = {"h": h[0], "turno": nuc.turno, "src": f.get("src", ""), "ft": f.get("turno"), "cls": f.get("obj_cls") or "", "disp": f.get("obj_disp") or "",
                              "pl": _plural(f), "gen": f.get("obj_gen") or ""}
                break
            pe = persona_nueva(nuc, f, n_af)
            if pe and ("quien_es|" + pe[0]) not in st["hechas"]:
                preg = "¿Quién es %s?" % pe[1]
                st["hechas"].append("quien_es|" + pe[0])
                st["pend"] = {"h": "quien_es", "turno": nuc.turno, "nombre": pe[1], "src": f.get("src", ""), "ft": f.get("turno")}
                break
    if not preg and not pre:
        for f in nuevos:
            if f.get("s") and nuc.can(f["s"]) == "U":
                en = enlace(nuc, f, n_af)
                if en:
                    return dict(r, respuesta=resp + " " + en)
    for f in nuevos:                                     # «me he quedado embarazada» -> lo estoy
        if f.get("v") == "quedar" and f.get("refl") and f.get("attr") and not f.get("neg") and f.get("s"):
            g = nuc._nuevo(v="estar", s=f["s"], attr=list(f["attr"]), t="pres", src=f.get("src", ""), efecto=True)
            nuc.F.append(g)
            try:
                nuc._espejo(g)
            except Exception:                            # noqa
                pass
    if preg:
        st["ult_q"] = nuc.turno
        del st["hechas"][:-200]
    if not pre and not preg:
        return r
    return dict(r, respuesta=" ".join(x for x in (pre, resp, preg) if x))


def nombra_grupo(nuc, texto, r):
    """«¿Con quién comparto piso?» -> «con dos amigas» se completa con sus nombres si se dijeron («…, Sara y Noelia»)."""
    if not isinstance(r, dict) or r.get("estado") != "ok" or not re.match(r"^\W*(?:y\s+)?(?:con|a|de|para)\s+qui[eé]n", texto or "", re.I):
        return r
    resp = r.get("respuesta") or ""
    for f in reversed(nuc.F):
        if not f.get("vig", True):
            continue
        for c in f.get("comps") or []:
            if not c[1] or not str(c[1]).startswith(("K:", "I:", "G:")) or not c[2] or (sa(c[2]) not in sa(resp) and sa(cambia_persona(c[2])) not in sa(resp)):
                continue
            cl = str(c[1])[2:].split("@")[0]
            miembros = [d["nombre"] for e, d in nuc.E.items() if d.get("clase") == cl and d.get("dueno") == "U" and d.get("nombre")
                        and any(x.get("x") == e and x.get("t") == f.get("turno") for x in nuc.R)]
            if len(miembros) >= 2 and not all(sa(m) in sa(resp) for m in miembros):
                lista = ", ".join(miembros[:-1]) + " y " + miembros[-1]
                return dict(r, respuesta=resp.rstrip(". ") + ": " + lista + ".")
    return r


# ------------------------------------------------------------------ antes: la respuesta a mi pregunta y las peticiones sobre la charla
def _invalida(nuc, pend):
    viejos = [f for f in nuc.F if f.get("turno") == pend.get("ft") and f.get("src") == pend.get("src") and f.get("vig", True)]
    for f in viejos:
        f["vig"] = False
        try:
            nuc._espejo(f, quitar=True)
        except Exception:                                # noqa
            pass
    return viejos


def _revive(nuc, viejos):
    for f in viejos:
        f["vig"] = True
        try:
            nuc._espejo(f)
        except Exception:                                # noqa
            pass


def _misma(nuc, viejos, nuevos):
    """La frase releída con el dato nuevo sigue siendo el mismo hecho: mismo verbo y mismo sujeto."""
    if not viejos:
        return True
    v0, s0 = viejos[0].get("v"), nuc.can(viejos[0].get("s") or "")
    return any(f.get("v") == v0 and nuc.can(f.get("s") or "") == s0 for f in nuevos)


def _es_fragmento(t):
    ws = t.strip(" .!").split()
    if not ws or len(ws) > 9:
        return False
    if re.match(r"^(?:" + _PREP + r"|un|una|unos|unas|el|la|los|las|mi|mis)\b", t.strip(), re.I) and len(ws) <= 9 and not re.search(r"\b(?:es|son|está|están|tiene|tienen)\b", t):
        return True
    if len(ws) <= 4:
        fin = [w for w in ws if any(a[1] in ("pres", "pret", "imp", "fut") for a in (M.analizar(sa(w)) or []) if isinstance(a, tuple) and len(a) > 2) and not w[:1].isupper()]
        return not fin
    return False


def _mi(pend):
    cl = pend.get("cls") or ""
    disp = (pend.get("disp") or "").strip()
    nom = re.sub(r"^(?:un|una|unos|unas|dos|tres|cuatro|cinco|seis|varios|varias|el|la|los|las|\d+)\s+", "", disp, flags=re.I) or cl
    return ("Mis " if pend.get("pl") else "Mi ") + nom


def _contesta(nuc, texto, pend):
    t = texto.strip()
    h = pend["h"]
    limpio = t.strip(" .!")
    if _NO_DICE.match(t):
        nuc.turno += 1
        return nuc._ok("De acuerdo, no pasa nada.", tipo="ack")
    if re.match(r"^\W*(?:venga|bueno|vale|ok|okey|gracias|hola|adi[oó]s|hasta|chao|s[ií]|no|claro|ya|jaja\w*|ah|oh|uf|pues|nada|luego|despu[eé]s te (?:lo )?(?:digo|cuento)|otro d[ií]a)\b", t, re.I):
        return None                                      # no es la respuesta: es otra cosa (un saludo, un acuse, una despedida)
    frase = None
    if h == "que_es":
        w = pend["w"]
        if re.search(r"\b" + re.escape(w[:4]), sa(t)):
            return None                                  # ya es una frase completa sobre la palabra
        un = pend["disp"][:1].upper() + pend["disp"][1:]
        if un.startswith("«"):
            un = "El " + pend["disp"].strip("«»")
        m = re.match(r"^(?:pues\s+)?(?:es|son)?\s*((?:un|una|unos|unas|como|el|la|una especie de|un tipo de)\b.+)$", limpio, re.I)
        m2 = re.match(r"^(?:pues\s+)?(?:sirven?|se usan?|vale|valen)\s+para\s+(.+)$", limpio, re.I) or re.match(r"^para\s+(.+)$", limpio, re.I)
        if m2:
            frase = f"{un} sirve para {m2.group(1)}."
        elif m:
            resto = re.sub(r"^(?:una especie de|un tipo de|como)\s+", "", m.group(1), flags=re.I)
            if not re.match(r"^(?:un|una|unos|unas|el|la)\b", resto, re.I):
                resto = "un " + resto
            resto = re.sub(r"\s+(?:para|con (?:el|la) que se puede)\s+(?=[a-záéíóúñ]+(?:ar|er|ir)\b)", " que sirve para ", resto, count=1) if "sirve" not in resto else resto
            frase = f"{un} es {resto}."
    elif h == "nombre":
        if re.match(r"^(?:[\wáéíóúñ ]+?\s)?(?:[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+\s*,\s*)+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+\s+[ye]\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+$", limpio):
            cab, cola = limpio, ""                       # «Miso, Pelusa y Tom»: la coma separa nombres
        else:
            cab, _, cola = limpio.partition(",")
        cab = re.sub(r"^(?:pues\s+)?(?:se llaman?|es|son|le llamamos|la llamamos|lo llamamos|le puse|le hemos puesto|su nombre es|sus nombres son)\s+", "", cab.strip(), flags=re.I)
        ws = cab.split()
        ws = [w.strip(",") for w in ws]
        if ws and len(ws) <= 7 and all(w[:1].isupper() or w.lower() in ("y", "e", "de", "del", "la") for w in ws) or (len(ws) == 1 and ws[0].isalpha() and not _conocida(nuc, ws[0]) and not M.analizar(ws[0])):
            ws = cab.split()
            cab = " ".join(w if w.lower() in ("y", "e", "de", "del", "la") else w[:1].upper() + w[1:] for w in ws)
            if len(ws) == 2 and "," not in cab and all(w[:1].isupper() for w in ws) and pend.get("pl"):
                cab = ws[0] + " y " + ws[1]
            pl = pend.get("pl") and (" y " in cab or " e " in cab)
            frase = f"{_mi(dict(pend, pl=pl))} se llama{'n' if pl else ''} {cab}."
            if cola.strip():
                frase += " " + cola.strip()[:1].upper() + cola.strip()[1:] + "."
    elif h == "quien" and "alguien" in sa(pend.get("src", "")):
        m = re.match(r"^(?:pues\s+)?(?:se llama|es|a)\s+([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)\s*(?:,\s*(.*))?$", limpio) or re.match(r"^([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)\s*(?:,\s*(.*))?$", limpio)
        if m:
            frase = re.sub(r"\balguien\b", m.group(1), pend["src"].rstrip(". "), flags=re.I) + "."
            if m.group(2):
                frase += " " + m.group(2)[:1].upper() + m.group(2)[1:] + "."
    elif h == "cual" and re.match(r"^(?:pues\s+)?(?:se titula|se llama|es|el de|la de)?\s*[«\"']?([A-ZÁÉÍÓÚÑ][^«»\"]{1,60}?)[»\"']?$", limpio) and not re.match(r"^(?:Un|Una|El|La|Es|Se)\s+[a-záéíóúñ]+\s+de\b", limpio):
        tit = re.match(r"^(?:pues\s+)?(?:se titula|se llama|es|el de|la de)?\s*[«\"']?([A-ZÁÉÍÓÚÑ][^«»\"]{1,60}?)[»\"']?$", limpio).group(1)
        frase = f"{_mi(pend)} se titula {tit}."
    elif h == "cual" and re.match(r"^(?:es\s+)?(?:una?|la|el)\s+de\s+(.+)$", limpio, re.I):
        de_ = re.match(r"^(?:es\s+)?(?:una?|la|el)\s+de\s+(.+)$", limpio, re.I).group(1)
        frase = f"{_mi(pend)} es de {de_}."
    elif h == "cual" and _es_fragmento(t) and not re.match(r"^" + _PREP + r"\b", limpio, re.I):
        frase = f"{_mi(pend)} es {limpio[:1].lower() + limpio[1:] if not limpio[:1].isupper() or limpio.split()[0].lower() in ('un', 'una', 'el', 'la') else limpio}."
    elif h == "causa":
        if re.match(r"^por\s+(?!que\b|qué\b)", limpio, re.I) and len(limpio.split()) <= 8:
            frase = "Es que fue " + limpio[:1].lower() + limpio[1:] + "."
        elif not re.match(r"^(?:es que|es porque|porque|pues porque|y es que)\b", limpio, re.I) and len(limpio.split()) <= 14:
            # sin «porque»: solo es la causa si lo que cuenta es algo malo o difícil («me duele la espalda»); si no, es otro tema
            viejos_c = [f for f in nuc.F if f.get("turno") == pend.get("ft") and f.get("src") == pend.get("src") and f.get("vig", True)]
            n0c = len(nuc.F)
            rc = nuc.procesar(t)
            if isinstance(rc, dict) and rc.get("estado") == "ok" and viejos_c and any(tono(nuc, f) in ("malo", "reto", "duelo") and nuc.can(f.get("s") or "") == "U" for f in nuc.F[n0c:]):
                for f in viejos_c:
                    if not f.get("causa"):
                        f["causa"] = limpio[:1].lower() + limpio[1:]
            return rc
        else:
            return None
        n0c = len(nuc.F)
        rc = nuc.procesar(frase)
        if isinstance(rc, dict) and rc.get("estado") == "ok":
            for f in nuc.F[n0c:]:
                tt = tono(nuc, f)
                if tt and tt != "reto":
                    return dict(rc, respuesta=_reaccion(nuc, tt, f) + " " + rc["respuesta"])
        return rc
    elif h in ("destino", "con") and _es_fragmento(t):
        frag = re.sub(r"\s*,\s*", " ", limpio)
        if h == "destino" and not re.match(r"^(?:a|al|en|hacia|para)\b", frag, re.I):
            frag = "a " + frag
        if h == "con" and not re.match(r"^con\b", frag, re.I):
            frag = "con " + frag
        frase = pend["src"].rstrip(". ") + " " + frag[:1].lower() + frag[1:] + "."
    elif h == "quien" and re.match(r"^(?:es\s+)?(?:la|el)\s+de\s+(.+)$", limpio, re.I):
        de = re.match(r"^(?:es\s+)?(?:la|el)\s+de\s+(.+)$", limpio, re.I).group(1)
        art = "La" if (pend.get("gen") == "f" or (pend.get("disp") or "").lower().startswith(("una", "la"))) else "El"
        frase = f"{art} {pend.get('cls') or 'fiesta'} es de {de}."
    elif h == "quien_es":
        m = re.match(r"^(?:pues\s+)?(?:es\s+)?(?:un|una|mi|el|la)\s+(.+)$", limpio, re.I)
        if m and len(limpio.split()) <= 7 and pend["nombre"].lower() not in limpio.lower():
            frase = f"{pend['nombre']} es mi {m.group(1)}."
    elif h == "resultado":
        m = re.match(r"^(?:pues\s+)?(?:me fue |me ha ido |fue |ha ido |sali[oó] )?((?:muy |bastante |super |regular|un poco )?(?:bien|mal|regular|genial|fatal|fenomenal|estupendamente|normal|flojo|de maravilla|de pena))$", limpio, re.I)
        if m:
            frase = f"{_mi(pend)} salió {m.group(1).lower()}."
    elif h == "perfil" and _es_fragmento(t):
        p = pend.get("p")
        if p == "nombre":
            frase = "Me llamo " + limpio[:1].upper() + limpio[1:] + "."
        elif p == "edad" and re.match(r"^(?:tengo\s+)?[\wáéíóú ]+?(?:\s+años)?$", limpio, re.I):
            frase = "Tengo " + re.sub(r"^tengo\s+|\s+años$", "", limpio, flags=re.I) + " años."
        elif p == "vivir":
            frase = "Vivo " + (limpio if re.match(r"^(?:en|cerca|al lado|por)\b", limpio, re.I) else "en " + limpio) + "."
        elif p == "trabajo":
            frase = ("Trabajo " + limpio if re.match(r"^(?:en|de|como|para)\b", limpio, re.I) else "Soy " + limpio[:1].lower() + limpio[1:]) + "."
        elif p == "gusto":
            frase = "Me gusta " + limpio[:1].lower() + limpio[1:] + "."
    if not frase:
        return None
    viejos = _invalida(nuc, pend) if h in ("destino", "con", "quien") and "alguien" in sa(pend.get("src", "")) or h in ("destino", "con") else []
    foto_turno, n0 = nuc.turno, len(nuc.F)
    r = nuc.procesar(frase)
    if viejos and isinstance(r, dict) and r.get("estado") == "ok" and h in ("destino", "con") and not _misma(nuc, viejos, nuc.F[n0:]):
        for f in nuc.F[n0:]:
            f["vig"] = False
            try:
                nuc._espejo(f, quitar=True)
            except Exception:                            # noqa
                pass
        _revive(nuc, viejos)
        return None
    if not isinstance(r, dict) or r.get("estado") != "ok" or len(nuc.F) == n0 and h not in ("que_es",):
        _revive(nuc, viejos)
        return None if (not isinstance(r, dict) or r.get("estado") != "ok") else r
    return r


_PERFIL = [("nombre", "¿Cómo te llamas?"), ("trabajo", "¿A qué te dedicas?"), ("vivir", "¿Dónde vives?"), ("edad", "¿Cuántos años tienes?"), ("gusto", "¿Qué te gusta hacer en tu tiempo libre?")]


def _falta_perfil(nuc):
    out = []
    F = [f for f in nuc.F if f.get("s") and nuc.can(f["s"]) == "U" and f.get("vig", True) and not f.get("neg")]
    sabe = {"nombre": bool((nuc.usuario.get("nombre") or nuc.E.get("U", {}).get("nombre") or "").strip()),
            "trabajo": any(f["v"] in ("trabajar", "dedicar", "estudiar") or (f["v"] == "ser" and f.get("isa")) for f in F),
            "vivir": any(f["v"] in ("vivir", "residir") for f in F),
            "edad": any(f["v"] == "tener" and f.get("obj_cls") == "año" for f in F) or bool(nuc.E.get("U", {}).get("edad")),
            "gusto": any(f["v"] in ("gustar", "encantar", "adorar") for f in F)}
    return [(p, q) for p, q in _PERFIL if not sabe[p]]


def _pregunta_algo(nuc, pre=""):
    st = estado(nuc)
    for f in reversed(nuc.F[-40:]):                      # primero, lo que me has contado a medias
        h = hueco(nuc, f)
        if h:
            st["hechas"].append(h[2]); st["ult_q"] = nuc.turno
            st["pend"] = {"h": h[0], "turno": nuc.turno, "src": f.get("src", ""), "ft": f.get("turno"), "cls": f.get("obj_cls") or "", "disp": f.get("obj_disp") or "",
                          "pl": _plural(f)}
            base = nuc.frase(f)
            return nuc._ok(f"{pre}Me contaste que {base}. {h[1]}", tipo="ack")
    for p, q in _falta_perfil(nuc):
        if "perfil|" + p in st["hechas"]:
            continue
        st["hechas"].append("perfil|" + p); st["ult_q"] = nuc.turno
        st["pend"] = {"h": "perfil", "p": p, "turno": nuc.turno}
        return nuc._ok(pre + q, tipo="ack")
    return nuc._ok(pre + "Ahora mismo no se me ocurre nada más que preguntarte. Cuéntame lo que te apetezca.", tipo="ack")


def _preocupa(nuc):
    """«¿Qué me preocupa?» sin que se haya dicho: lo malo o lo difícil que se ha contado hace poco es una conjetura razonable, y se dice como tal."""
    cands = []
    for f in nuc.F[-30:]:
        if not f.get("vig", True) or f.get("efecto") or not f.get("s") or str(nuc.can(f["s"])).startswith("K:"):
            continue
        if f.get("v") == "estar" and nuc.can(f["s"]) == "U":
            continue
        if tono(nuc, f) in ("malo", "reto", "duelo"):
            fr = nuc.frase(f)
            if fr not in cands:
                cands.append(fr)
    if not cands:
        return None
    return "Puede que sea porque " + " y porque ".join(cands[-3:]) + ". Lo supongo por lo que me has contado: no me lo has dicho tú."


def _corrige(nuc, t):
    """«Perdona, los viernes, no los jueves», «no, en Soria»: se corrige el dato en la frase original y se vuelve a leer entera."""
    ua = getattr(nuc, "_ult_afirm", None)
    if not ua or nuc.turno - ua[1] > 2 or "?" in t:
        return None
    m = re.match(r"^\W*(?:no|perdona|perd[oó]n|disculpa|me he equivocado|me equivoqu[eé]|me he confundido|rectifico|mejor dicho|quer[ií]a decir|digo)\s*[,:;]?\s*(?:perdona|perd[oó]n)?\s*[,:]?\s*(.+?)\s*[.!]*$", t, re.I)
    if not m:
        return None
    cuerpo = m.group(1)
    nuevo, _, viejo = cuerpo.partition(", no ")
    if not viejo:
        mm = re.match(r"^(.+?)\s+(?:y\s+)?no\s+(.+)$", cuerpo)
        if mm and len(mm.group(2).split()) <= 3:
            nuevo, viejo = mm.group(1), mm.group(2)
    nuevo, viejo = nuevo.strip(" ,"), viejo.strip(" ,.")
    if not nuevo or len(nuevo.split()) > 5 or not _es_fragmento(nuevo):
        return None
    viejos = [f for f in nuc.F[ua[2]:ua[3]] if f.get("vig", True)]
    if not viejos:
        return None
    src = viejos[0].get("src") or ua[0]
    quita = lambda x: re.sub(r"^(?:el|la|los|las|en|a|al|con|de)\s+", "", x, flags=re.I)
    frase = None
    if viejo and re.search(r"\b" + re.escape(quita(viejo)) + r"\b", src, re.I):
        frase = re.sub(r"\b" + re.escape(quita(viejo)) + r"\b", quita(nuevo), src, count=1, flags=re.I)
    else:
        for clase in (_DIAS, _MES, r"\d+(?:[.,]\d+)?"):
            mn, ms = re.search(r"\b" + clase + r"\b", nuevo, re.I), re.search(r"\b" + clase + r"\b", src, re.I)
            if mn and ms:
                frase = src[:ms.start()] + mn.group(0) + src[ms.end():]
                break
        if frase is None:
            mp = re.match(r"^(" + _PREP + r")\s+(.+)$", nuevo, re.I)
            if mp:
                hits = list(re.finditer(r"\b" + mp.group(1) + r"\s+(?:(?:el|la|los|las|mi|un|una)\s+)?[\wáéíóúñ]+", src, re.I))
                if hits:
                    frase = src[:hits[-1].start()] + nuevo + src[hits[-1].end():]
    if not frase or sa(frase) == sa(src):
        return None
    for f in viejos:
        f["vig"] = False
        try:
            nuc._espejo(f, quitar=True)
        except Exception:                                # noqa
            pass
    r = nuc.procesar(frase.rstrip(". ") + ".")
    if not isinstance(r, dict) or r.get("estado") != "ok":
        _revive(nuc, viejos)
        return None
    resp = re.sub(r"\s*¿[^?]*\?(?: Es la primera vez que oigo esa palabra\.)?", "", r.get("respuesta") or "")
    resp = re.sub(r"^.*?Entendido: ", "Corregido: ", resp, count=1) if "Entendido: " in resp else resp
    estado(nuc)["pend"] = None
    return dict(r, respuesta=resp)


def _claves_txt(t):
    vac = {"hoy", "ayer", "que", "por", "el", "la", "los", "las", "un", "una", "de", "en", "me", "te", "se", "he", "has", "ha", "muy", "y", "es", "mi", "tu", "lo", "al", "del", "con", "a", "no", "ya", "tan"}
    out = set()
    for w in re.findall(r"[a-záéíóúñü]+", (t or "").lower()):
        w0 = re.sub(r"isim([oa]s?)$", r"\1", sa(w))
        if w0 in vac or len(w0) < 3:
            continue
        w = w0 if w0 != sa(w) else w
        an = M.analizar(w)
        out.add(an[0][0] if an else sa(M.singular(w0)))
    return out


def causa_suelta(nuc, texto, previo):
    """«Hoy he tenido un día horrible.» «Es que se me ha estropeado el coche.»: aunque lo primero no dejara un hecho, la explicación queda unida a ello."""
    m = re.match(r"^\s*(?:es que|es porque|porque|pues porque|y es que)\s+(.+?)\s*[.!]*$", texto.strip(), re.I)
    if not m or not previo:
        return None
    causa = m.group(1)
    n0 = len(nuc.F)
    try:
        nuc._procesar_charla(causa[:1].upper() + causa[1:] + ".")
    except Exception:                                    # noqa
        pass
    lista = nuc.usuario.setdefault("porques", [])
    lista.append({"de": sorted(_claves_txt(previo)), "dicho": previo.strip().rstrip(".!"), "causa": causa})
    del lista[:-30]
    pre = ""
    for f in nuc.F[n0:]:
        tt = tono(nuc, f)
        if tt:
            pre = _reaccion(nuc, tt, f) + " "
            break
    return nuc._ok(f"{pre}Entendido: es porque {causa_tu(causa)}.", tipo="ack")


def porque_suelto(nuc, texto):
    n = sa(texto).strip(" ¿?¡!.")
    m = re.match(r"^(?:y )?por que (.+)$", n)
    if not m:
        return None
    q = _claves_txt(m.group(1))
    mejor = None
    for d in reversed(nuc.usuario.get("porques") or []):
        de = set(d["de"])
        if de and q and len(q & de) >= max(1, round(0.6 * len(de))) and len(q & de) >= max(1, round(0.6 * len(q))):
            mejor = d
            break
    if not mejor:
        return None
    nuc.ult_just = {"dicho": [mejor["dicho"], "Es que " + mejor["causa"]]}
    return {"respuesta": "Porque %s." % causa_tu(mejor["causa"]), "estado": "ok", "consultar": False, "tipo": "resp"}


def accion_evento(nuc, texto):
    """«Tengo una cena con Ana el viernes» y «¿con quién ceno el viernes?» hablan de lo mismo: la acción y su evento ([acciones] en la base)."""
    tabla = K.kb().get("acciones") or {}
    if not tabla or "?" not in texto:
        return None
    inv = {}
    for nom, verbos in tabla.items():
        for v in verbos:
            inv.setdefault(v, nom)
    ws = re.findall(r"[\wáéíóúñü]+", texto)
    for i, w in enumerate(ws):
        an = [a for a in (M.analizar(w.lower()) or []) if a[1] in ("pres", "pret", "fut") and len(a) > 2 and a[2] in ("1s", "1p")]
        if an and an[0][0] in inv:
            nom = inv[an[0][0]]
            if not any(f.get("v") == "tener" and f.get("vig", True) and sa((f.get("obj_cls") or "").split()[0] if f.get("obj_cls") else "") == nom for f in nuc.F):
                continue
            art = "una" if K.genero(nom) == "f" else "un"
            ten = M.conjugar("tener", an[0][1], an[0][2]) or "tengo"
            return re.sub(r"\b" + re.escape(w) + r"\b", f"{ten} {art} {K.forma(nom)}", texto, count=1)
    m = re.search(r"\b(tengo|tenemos|tuve|tuvimos|tendr[eé]|tendremos)\s+(?:el|la|un|una|mi)\s+([a-záéíóúñ]+)\b", texto, re.I)
    if m and sa(m.group(2)) in tabla:
        an = M.analizar(m.group(1).lower())
        v = tabla[sa(m.group(2))][0]
        if an and any(f.get("v") == v and f.get("vig", True) and f.get("s") and nuc.can(f["s"]) == "U" for f in nuc.F):
            return texto[:m.start()] + (M.conjugar(v, an[0][1], an[0][2]) or v) + texto[m.end():]
    return None


def correferencia(nuc, texto):
    """«Las niñas», «el peque», «los críos»: si la persona tiene hijos y no hay otros niños en la charla, habla de ellos."""
    mf = re.match(r"^a\s+((?:mi|mis)\s+[a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)?|[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)\s+(?:le|les)\s+((?:he|hemos|voy a|vamos a|acabo de)\s+)?([a-záéíóúñ]+)\b(.*)$", (texto or "").strip())
    if mf and "?" not in texto:                          # «a Alba le he comprado una bicicleta» = «he comprado una bicicleta a Alba»
        an = M.analizar(mf.group(3).lower()) or []
        yo = bool(mf.group(2)) or any(len(a) > 2 and a[2] in ("1s", "1p") for a in an)
        if yo and an and an[0][0] in ("comprar", "regalar", "dar", "mandar", "enviar", "prestar", "llevar", "traer", "escribir", "contar", "pedir", "devolver", "dejar", "hacer", "preparar", "cocinar", "leer", "enseñar"):
            cuerpo = ((mf.group(2) or "") + mf.group(3) + mf.group(4)).strip().rstrip(".")
            return cuerpo[:1].upper() + cuerpo[1:] + " a " + mf.group(1) + "."
    md = re.match(r"^((?:ayer|hoy|mañana|ya|tambi[eé]n|al final|por fin)\s+)?(le|les)\s+((?:he|hemos|voy a|vamos a|acabo de)\s+)?([a-záéíóúñ]+)\b(.*)$", (texto or "").strip(), re.I)
    if md and "?" not in texto and not re.search(r"\ba\s+(?:mi|mis|tu|su|el|la|los|las|[A-ZÁÉÍÓÚÑ])", md.group(5)) and not re.search(r"\bal\s+\w+", md.group(5)):
        an = M.analizar(md.group(4).lower()) or []       # «le he comprado un tren» (a Leo, de quien se hablaba): el «le» es él
        yo = bool(md.group(3)) or any(len(a) > 2 and a[2] in ("1s", "1p") for a in an)
        if yo and an and an[0][0] in ("comprar", "regalar", "dar", "mandar", "enviar", "prestar", "llevar", "traer", "escribir", "contar", "pedir", "devolver", "dejar", "hacer", "preparar", "cocinar", "leer", "enseñar"):
            try:
                ref = nuc.ref3(persona=True)
            except Exception:                            # noqa
                ref = None
            if ref and nuc.can(ref) not in ("U", "L") and bool(nuc.E.get(nuc.can(ref), {}).get("pl")) == (md.group(2).lower() == "les"):
                quien = cambia_persona(nuc.disp(nuc.can(ref)))
                cuerpo = ((md.group(1) or "") + (md.group(3) or "") + md.group(4) + md.group(5)).strip().rstrip(".")
                return cuerpo[:1].upper() + cuerpo[1:] + " a " + quien + "."
    m = re.search(r"\b(las niñas|los niños|los críos|las crías|los crios|los peques|las peques|los chicos|las chicas|los nenes|las nenas|la niña|el niño|la peque|el peque|la nena|el nene)\b", texto or "", re.I)
    if not m:
        return texto
    hijos = [(e, d) for e, d in nuc.E.items() if d.get("clase") == "hijo" and d.get("dueno") == "U" and e not in ("U", "L")]
    tiene = [f for f in nuc.F if f.get("v") == "tener" and f.get("vig", True) and f.get("s") and nuc.can(f["s"]) == "U" and f.get("obj_cls") == "hijo" and not f.get("neg")]
    if not hijos and not tiene:
        return texto
    if any(d.get("clase") in ("niño", "alumno", "sobrino", "nieto") and e.startswith(("N:", "I:")) for e, d in nuc.E.items()):
        return texto                                     # hay otros niños de los que se ha hablado: no se adivina
    w = m.group(1).lower()
    pl = w.split()[0] in ("las", "los")
    fem = w.split()[0] in ("las", "la")
    n_h = len([1 for e, d in hijos if e.startswith("N:")]) or max([f.get("cuant") or 1 for f in tiene] or [1])
    if pl != (n_h > 1):
        return texto
    nuevo = ("mis " if pl else "mi ") + ("hij" + ("a" if fem else "o") + ("s" if pl else ""))
    if m.start() == 0:
        nuevo = nuevo[:1].upper() + nuevo[1:]
    return texto[:m.start()] + nuevo + texto[m.end():]


_FUT = r"\b(?:mañana|pasado mañana|esta (?:tarde|noche|semana)|este (?:fin de semana|finde|verano|invierno|mes|año|" + _DIAS[3:-1] + r")|el (?:proximo|" + _DIAS[3:-1] + r")|la (?:semana|proxima semana) (?:que viene|proxima)?|la proxima semana|el (?:mes|año) que viene|en (?:" + _MES[3:-1] + r"|navidad|verano|vacaciones|semana santa)|el dia \d+|dentro de)\b"


def _planes(nuc):
    out = []
    for f in nuc.F:
        if not f.get("vig", True) or f.get("neg") or f.get("efecto") or not f.get("s") or nuc.can(f["s"]) != "U" or f.get("v") in ("ser", "estar", "llamar", "gustar") or f.get("freq"):
            continue
        if f.get("t") == "fut" or (f.get("t") == "pres" and f.get("cuando") and re.search(_FUT, sa(f["cuando"]))):
            fr = nuc.frase(f)
            if fr not in out:
                out.append(fr)
    return out


def _que_paso(nuc, cosa):
    c = sa(M.singular(cosa.split()[-1]))
    out = []
    for f in nuc.F:
        if not f.get("vig", True) or f.get("efecto") or f.get("v") in ("tener", "ser", "llamar") and not f.get("attr"):
            continue
        toca = sa((f.get("obj_cls") or "").split()[0] if f.get("obj_cls") else "") == c or (str(f.get("s") or "")[2:].split("@")[0] == c) \
            or any(str(x[1] or "")[2:].split("@")[0] == c for x in f.get("comps") or [])
        if toca and (f.get("t") in ("pret", "imp") or f.get("exp") or f.get("attr")):
            fr = nuc.frase(f)
            if fr not in out:
                out.append(fr)
    return out


def _familia(nuc):
    from .nucleo import FAMILIA
    out, vistos = [], set()
    for x in nuc.R:
        e = x.get("x")
        if x.get("y") != "U" or e in vistos or (x.get("r") not in FAMILIA and x.get("r") not in ("esposo", "pareja", "marido", "mujer")):
            continue
        d = nuc.E.get(e, {})
        if not d.get("nombre"):
            continue
        vistos.add(e)
        rol = nuc._acento(nuc._rel_nombre(x["r"], d.get("gen") or nuc.gen(e) or "m"))
        partes = ["%s es tu %s" % (d["nombre"], rol)]
        for f in nuc.F:
            if f.get("vig", True) and not f.get("efecto") and f.get("s") and nuc.can(f["s"]) == e and f.get("v") != "llamar" and len(partes) < 4:
                fr = nuc.frase(f)
                if sa(fr) != sa(partes[0]) and fr not in partes and not (f.get("v") == "ser" and f.get("isa") and sa(rol) in sa(fr)):
                    partes.append(fr)
        out.append("; ".join(partes))
    for f in nuc.F:                                      # parientes de los que se sabe que existen pero no el nombre
        if f.get("v") == "tener" and f.get("vig", True) and f.get("s") and nuc.can(f["s"]) == "U" and (f.get("obj_cls") in FAMILIA) and not f.get("neg"):
            cl = f["obj_cls"]
            if not any(nuc.E.get(e, {}).get("clase") == cl for e in vistos):
                out.append(nuc.frase(f))
    return out


def antes(nuc, texto):
    """Antes de procesar el turno: ¿contesta a mi pregunta?, ¿pide algo sobre la propia charla?"""
    st = estado(nuc)
    t = (texto or "").strip()
    n = sa(t).strip(" .!¡¿?")
    pend, st["pend"] = st.get("pend"), None
    # ---- peticiones sobre la charla
    if re.match(r"^(?:por favor,? )?(?:(?:prefiero|preferiria|mejor|te pido) que )?(?:no me (?:hagas|preguntes)(?: mas)?(?: tantas)?(?: preguntas| nada)?|deja de (?:preguntar(?:me)?|hacer(?:me)? preguntas)|no (?:quiero|me gusta) que me (?:preguntes|hagas preguntas)|"
                r"no preguntes(?: tanto| mas)?|sin preguntas)(?:,? por favor)?$", n):
        st["off"] = True
        nuc.turno += 1
        return nuc._ok("De acuerdo, no te haré preguntas. Si cambias de idea, dímelo.", tipo="ack")
    if re.match(r"^(?:ya |ahora )?(?:si )?(?:(?:me )?puedes (?:volver a )?(?:preguntar(?:me)?|hacer(?:me)? preguntas)|preguntame lo que quieras|puedes preguntar)(?: lo que quieras| cosas| otra vez| de nuevo)*$", n):
        st["off"] = False
        nuc.turno += 1
        return nuc._ok("Gracias. Si algo no lo sé o me falta, te lo preguntaré.", tipo="ack")
    if re.match(r"^(?:venga,? |anda,? |pues |ahora )?(?:preguntame|hazme)(?: tu)? (?:algo|otra cosa|otra|una pregunta|otra pregunta|algo mas|lo que quieras|mas cosas|alguna cosa)(?: sobre mi| de mi)?(?:,? por favor)?$", n) \
            or re.match(r"^(?:que (?:quieres|te gustaria) saber(?: de mi| sobre mi)?|que me preguntarias|quieres saber algo(?: de mi| sobre mi)?|tienes alguna pregunta(?: para mi)?)$", n):
        st["off"] = False
        nuc.turno += 1
        return _pregunta_algo(nuc)
    if re.match(r"^(?:no se de que hablar|no se que contarte|no se que decir(?:te)?|no se me ocurre nada(?: que contar(?:te)?)?|de que (?:podemos hablar|hablamos|quieres hablar)|hablame de algo)$", n):
        nuc.turno += 1
        if st["off"]:
            return nuc._ok("No pasa nada. Cuéntame cómo te ha ido el día, o lo que te apetezca.", tipo="ack")
        return _pregunta_algo(nuc, pre="No pasa nada. ")
    if re.match(r"^(?:y )?que (?:es lo que )?no sabes (?:de|sobre) mi$", n) or re.match(r"^que te falta (?:por )?saber (?:de|sobre) mi$", n):
        falta = {"nombre": "cómo te llamas", "trabajo": "a qué te dedicas", "vivir": "dónde vives", "edad": "cuántos años tienes", "gusto": "qué te gusta hacer"}
        fs = [falta[p] for p, _ in _falta_perfil(nuc)]
        abiertos = []
        for f in nuc.F[-40:]:
            h = hueco(nuc, f)
            if h and h[0] == "nombre":
                abiertos.append("cómo se llama%s %s" % ("n" if f.get("pl_obj") or (f.get("cuant") or 1) > 1 else "", re.sub(r"^(?:un|una|unos|unas|dos|tres|cuatro|\d+)\s+", "tu " if not (f.get("pl_obj") or (f.get("cuant") or 1) > 1) else "tus ", f.get("obj_disp") or "")))
        fs = fs + [a for a in abiertos if a not in fs]
        nuc.turno += 1
        if not fs:
            return nuc._ok("De lo básico no echo nada en falta: sé cómo te llamas, a qué te dedicas, dónde vives, tu edad y algo de lo que te gusta. De todo lo demás solo sé lo que me cuentes.")
        return nuc._ok("Todavía no sé " + (", ".join(fs[:-1]) + " ni " + fs[-1] if len(fs) > 1 else fs[0]) + ". Solo sé lo que me cuentas.")
    if "?" in t and re.match(r"^(?:y )?(?:que planes tengo|que tengo (?:pendiente|previsto|planeado|por delante)|que voy a hacer(?: proximamente| estos dias| pronto)?|cuales son mis planes|tengo (?:algun )?planes?)$", n):
        pl = _planes(nuc)
        nuc.turno += 1
        if not pl:
            return nuc._abst("No lo sé: no me has contado ningún plan.")
        nuc.ult_just = {"pasos": ["son las cosas que me has contado que vas a hacer"]}
        return nuc._ok(_cap(_une(pl)) + ".")
    m = re.match(r"^(?:y )?que (?:le |les )?(?:paso|ha pasado|ocurrio|ha ocurrido|sucedio) (?:a|al|con|con el|con la) (?:(?:mi|el|la|los|las|mis) )?([a-zñáéíóú ]+)$", n)
    if m and "?" in t:
        qp = _que_paso(nuc, m.group(1).strip())
        if qp:
            nuc.turno += 1
            return nuc._ok(_cap(_une(qp)) + ".")
    if "?" in t and re.match(r"^(?:y )?(?:que sabes|que te he contado|que recuerdas|hablame) (?:de|sobre) mi familia$", n) or re.match(r"^hablame de mi familia$", n):
        fam = _familia(nuc)
        nuc.turno += 1
        if not fam:
            return nuc._abst("No lo sé: todavía no me has hablado de tu familia.")
        return nuc._ok(". ".join(_cap(x) for x in fam) + ".")
    m = re.match(r"^(?:y )?quien ([a-zñ]+) (mejor|peor),? ([a-zñ]+) o ([a-zñ]+)$", n)
    if m and "?" in t:
        an = [a for a in (M.analizar(m.group(1)) or []) if a[1] in ("pres", "pret", "imp")]
        if an:
            v = an[0][0]
            cierre = {}
            for f in nuc.F:
                if f.get("v") == v and f.get("comp") and f.get("vig", True) and not f.get("neg") and f["comp"][1] in ("mejor", "peor", "bien", "bueno", "malo") and f["comp"][2] and f.get("s"):
                    x, y = nuc.can(f["s"]), nuc.can(f["comp"][2])
                    mejor_ = (f["comp"][1] in ("mejor", "bien", "bueno")) == (f["comp"][0] != "menos")
                    cierre[(x, y) if mejor_ else (y, x)] = [f]
            cambio = True
            while cambio:
                cambio = False
                for (a_, b_), j1 in list(cierre.items()):
                    for (b2, c_), j2 in list(cierre.items()):
                        if b_ == b2 and a_ != c_ and (a_, c_) not in cierre:
                            cierre[(a_, c_)] = j1 + j2; cambio = True
            ea, eb = "N:" + m.group(3), "N:" + m.group(4)
            for gana, pierde in ((ea, eb), (eb, ea)):
                if (nuc.can(gana), nuc.can(pierde)) in cierre:
                    js = cierre[(nuc.can(gana), nuc.can(pierde))]
                    g2, p2 = (gana, pierde) if m.group(2) == "mejor" else (pierde, gana)
                    nuc.turno += 1
                    nuc.ult_just = {"dicho": [f["src"] for f in js]}
                    base = "%s %s %s que %s." % (nuc.disp(nuc.can(g2)), M.conjugar(v, "pres", "3s"), m.group(2), nuc.disp(nuc.can(p2)))
                    return nuc._ok(base + (" Lo deduzco porque " + " y ".join(nuc.frase(f) for f in js) + "." if len(js) > 1 else ""))
    m = re.match(r"^(?:y )?(?:que tal|como) (?:me |nos )?(?:fue|ha ido|salio|ha salido) (?:en )?(?:el|la|mi) ([a-zñ ]+)$", n)
    if m and "?" in t:
        return nuc.procesar("¿Cómo salió mi %s?" % m.group(1))
    m = re.match(r"^(?:(?:el|la|mi) ([a-zñ]+) )?(?:me |nos )(?:fue|ha ido|salio|ha salido) ((?:muy |bastante |super )?(?:bien|mal|regular|genial|fatal|fenomenal))(?: (?:en )?(?:el|la|mi) ([a-zñ]+))?$", n)
    if m and "?" not in t and (m.group(1) or m.group(3)):
        return nuc.procesar("Mi %s salió %s." % (m.group(1) or m.group(3), m.group(2)))
    if re.match(r"^(?:y )?(?:de que|que) (?:estabamos hablando|hablabamos|ibamos hablando|estabamos diciendo)$", n) or re.match(r"^por donde ibamos$", n):
        return nuc.procesar("¿De qué hemos hablado?")
    if re.match(r"^(?:mejor )?(?:cambiemos|cambiamos|cambia|vamos a cambiar|podemos cambiar) de tema(?:,? por favor)?$", n) or re.match(r"^(?:hablemos|vamos a hablar|mejor hablamos|prefiero hablar) de otra cosa$", n):
        nuc.turno += 1
        return nuc._ok("De acuerdo, cambiamos de tema. Cuéntame lo que te apetezca.", tipo="ack")
    if re.match(r"^(?:y )?(?:tu|a ti)(?:,)? (?:que tal(?: estas)?|como estas|como te va|que tal te va|como andas)$", n) or re.match(r"^(?:y )?tu que tal(?: todo)?$", n):
        nuc.turno += 1
        return nuc._ok("Bien, gracias%s. Aquí estoy, atento a lo que me cuentes." % _nombre(nuc))
    m = re.match(r"^(?:bueno|pues|vale|venga|en fin)?,?\s*(?:(?:muchas )?gracias(?: por todo| por la charla| por tu ayuda)?,?\s*(?:y )?)?(?:me voy|me tengo que ir|tengo que irme|me marcho|te dejo|tengo que dejarte|me piro|hasta luego|adios|hasta mañana|nos vemos)"
                 r"(?: ya| ahora)?(?:,?\s*(?:y )?(?:muchas )?gracias(?: por todo| por la charla| por tu ayuda)?)?(?:,?\s*(?:hasta luego|adios|hasta mañana|nos vemos))?$", n.replace("ñ", "ñ"))
    if m and "gracias" in n:
        nuc.turno += 1
        return nuc._ok("De nada%s. ¡Hasta luego! Aquí estaré cuando quieras." % _nombre(nuc))
    if m and re.match(r"^(?:bueno|pues|vale|venga|en fin)\b", n):
        nuc.turno += 1
        return nuc._ok("¡Hasta luego%s! Aquí estaré cuando quieras." % _nombre(nuc))
    if "?" in t and re.match(r"^(?:y )?(?:que (?:es lo que )?me (?:preocupa|agobia|inquieta|tiene (?:asi|preocupad[oa]))|por que estoy (?:tan )?(preocupad[oa]|nervios[oa]|agobiad[oa]|triste|mal|inquiet[oa]))$", n):
        est = [f for f in nuc.F if f.get("v") in ("estar", "preocupar") and f.get("vig", True) and f.get("s") and nuc.can(f["s"]) == "U" and f.get("causa")]
        if not est:
            c = _preocupa(nuc)
            if c:
                nuc.turno += 1
                return nuc._ok(c)
    if t and "?" in t and (nuc.usuario.get("porques")):
        rps = porque_suelto(nuc, t)
        if rps is not None:
            nuc.turno += 1
            return rps
    if t and "?" not in t:
        try:
            rc = _corrige(nuc, t)
        except Exception:                                # noqa
            rc = None
        if rc is not None:
            return rc
    m = re.match(r"^(?:hoy|ayer|esta semana|este mes)?\s*(?:ha sido|he tenido|fue|tuve|llevo|he pasado|pase|esta siendo)\s+un(?:a|os)?\s+(dia|semana|mes|año|finde|fin de semana|tarde|mañana|noche|dias)\s+(?:muy |tan |bastante |super )?([a-zñ]+)$", n)
    if m and "?" not in t:
        from . import social as _soc
        adj = re.sub(r"isim([oa]s?)$", r"\1", m.group(2))
        conocido = re.search(r"\b(mal[oa]?|horrible|terrible|dur[oa]|dificil|fatal|pesim[oa]|agotador[a]?|complicad[oa]|buen[oa]?|genial|estupend[oa]|fantastic[oa]|maravillos[oa]|perfect[oa]|increible|tranquil[oa])\b", adj)
        if not conocido:
            nuc.turno += 1
            nuc._ult_suelto = (t, nuc.turno)
            nuc._ult_afirm = None
            return nuc._ok("Vaya." + ("" if st["off"] else " ¿Qué ha pasado?"), tipo="ack")
    # ---- ¿es la respuesta a lo que pregunté?
    if pend and pend.get("turno") == nuc.turno and t and "?" not in t:
        try:
            r = _contesta(nuc, t, pend)
        except Exception:                                # noqa
            r = None
        if r is not None:
            st2 = estado(nuc)
            st2["ult_q"] = nuc.turno - 1                 # acaba de contestar: ahora no toca otra pregunta
            if isinstance(r, dict) and "¿" in (r.get("respuesta") or "") and r.get("tipo") == "ack":
                r = dict(r, respuesta=re.sub(r"\s*¿[^?]*\?(?: Es la primera vez que oigo esa palabra\.)?", "", r["respuesta"]).strip() or r["respuesta"])
                st2["pend"] = None
            return r
    elif t and "?" not in t and re.match(r"^(?:y\s+)?" + _PREP + r"\s+\S", t, re.I) and len(t.split()) <= 7 and not re.match(r"^(?:y\s+)?(?:por|de|para)\s+(?:favor|nada|acuerdo|cierto|verdad|supuesto|que|qué|eso|ejemplo)\b", t, re.I):
        ua = getattr(nuc, "_ult_afirm", None)            # «He encontrado trabajo.» «En una panadería.»: sigue la frase anterior
        ws_ = t.strip(" .!").split()
        verbo_ = any(any(a_[1] in ("pres", "pret", "imp", "fut", "cond") for a_ in (M.analizar(w_.lower()) or [])) and not (i_ and ws_[i_ - 1].lower() in ("un", "una", "el", "la", "los", "las", "mi", "mis", "su", "sus", "al", "del", "de", "en", "con", "a"))
                     for i_, w_ in enumerate(ws_) if i_ and not w_[:1].isupper())
        if ua and nuc.turno - ua[1] <= 1 and not getattr(nuc, "_continuando", False) and not verbo_ and not re.search(r"\b(?:me|te|le|les|nos|se)\s+\w+", " ".join(ws_[1:]), re.I):
            viejos = [f for f in nuc.F[ua[2]:ua[3]] if f.get("vig", True)]
            if viejos and viejos[0].get("src") and nuc.can(viejos[0]["s"] or "") == "U":
                frag = re.sub(r"\s*,\s*", " ", re.sub(r"^y\s+", "", t.strip(" .!"), flags=re.I))
                frase = viejos[0]["src"].rstrip(". ") + " " + frag[:1].lower() + frag[1:] + "."
                n0m = len(nuc.F)
                for f in viejos:
                    f["vig"] = False
                    try:
                        nuc._espejo(f, quitar=True)
                    except Exception:                    # noqa
                        pass
                nuc._continuando = True
                try:
                    r = nuc.procesar(frase)
                finally:
                    nuc._continuando = False
                if isinstance(r, dict) and r.get("estado") == "ok" and r.get("tipo") == "ack" and _misma(nuc, viejos, nuc.F[n0m:]):
                    return dict(r, respuesta=re.sub(r"^(?:¡[^!]*!\s*(?:Enhorabuena\.\s*)?|Vaya, lo siento\.\s*|Lo siento\.\s*)", "", r.get("respuesta") or ""))
                for f in nuc.F[n0m:]:                    # la frase unida no dice lo mismo que la original: se deshace
                    f["vig"] = False
                    try:
                        nuc._espejo(f, quitar=True)
                    except Exception:                    # noqa
                        pass
                _revive(nuc, viejos)
    elif _NO_DICE.match(t) and re.match(r"^\W*(?:prefiero no|no quiero|mejor no|no (?:te )?lo (?:quiero|voy))", t, re.I):
        nuc.turno += 1
        return nuc._ok("De acuerdo, no pasa nada.", tipo="ack")
    return None
