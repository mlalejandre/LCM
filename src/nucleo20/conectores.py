"""LCM 2.11 · CONECTORES LÓGICOS (copulativas, disyuntivas, comparativas, condicionales).

Disyunción («o», «u», «o… o», «bien… bien», «ya sea… o»): cada alternativa se entiende como una frase normal, pero queda
como POSIBLE dentro de un grupo; nunca se afirma sola. Al responder se dice el grupo entero con «o». Si una alternativa
se niega, se descarta; si queda una sola, se deduce (silogismo disyuntivo) y se dice por qué.
"""
from __future__ import annotations

import re

from . import morfo as M
from .morfo import sa

_NO_DISY = re.compile(r"\b(?:o sea|o algo así|o algo asi|o no|más o menos|mas o menos|tarde o temprano|uno u otro|una u otra|o bien)\b", re.I)   # «dos o tres primos» sí es una disyunción (entre cantidades)
_DUDA = re.compile(r"\s*,\s*(?:no me acuerdo|no lo s[ée]|no s[ée] cu[áa]l|no estoy segur[oa]|creo|me parece|no recuerdo|seg[úu]n creo|ya veremos|todav[íi]a no lo s[ée]|a[úu]n no lo s[ée]|depende)\s*([.!]?)$", re.I)
_ENCAB = ("en", "a", "al", "de", "del", "con", "para", "por", "desde", "hasta", "el", "la", "los", "las", "un", "una", "unos", "unas", "mi", "mis", "tu", "tus",
          "su", "sus", "este", "esta", "ese", "esa", "sobre", "hacia", "entre")


def _fin_finito(ws, verbo_finito):
    for k, w in enumerate(ws):
        if verbo_finito(w.lower()) and k > 0:
            j = k - 1 if ws[k - 1].lower() in ("me", "te", "se", "nos", "le", "les", "lo", "la", "los", "las", "no") else k
            return j
    return None


def expande_o(t, verbo_finito):
    """Frase con una disyunción -> lista de frases alternativas, o None si no hay disyunción tratable."""
    if not t or "?" in t or "¿" in t:
        return None
    t0 = t.strip()
    duda = _DUDA.search(t0)
    if duda:
        t0 = t0[:duda.start()] + (duda.group(1) or "")
    t0 = t0.rstrip(".! ")
    if _NO_DISY.search(t0):
        return None
    # «o mi padre o mi madre me llevará…», «o voy en tren o voy en autobús», «bien… bien…», «ya sea… o…»
    m = re.match(r"^(?:[Oo]|[Bb]ien|[Yy]a sea)\s+(.+?)\s+(?:o|u|bien)\s+(.+)$", t0)
    if m:
        x, r = m.group(1), m.group(2)
        wx = x.split()
        if any(verbo_finito(w.lower()) for w in wx):
            return [x, r]                                  # dos frases completas
        wr = r.split()
        j = _fin_finito(wr, verbo_finito)
        if j is None or j == 0:
            return None
        y, pred = " ".join(wr[:j]), " ".join(wr[j:])
        return [f"{x} {pred}", f"{y} {pred}"]
    partes = re.split(r"\s+(?:o|u)\s+", t0)
    if len(partes) != 2:
        return None
    izq, der = partes
    if "," in der:
        return None
    wd = der.split()
    if not wd:
        return None
    cl = ("me", "te", "se", "nos", "le", "les", "lo", "la", "los", "las", "no")
    from . import conceptos as KB
    es_nombre = bool(KB.ancestros(sa(wd[0].lower())) or KB.ancestros(sa(M.singular(wd[0].lower()))))
    clausal = len(wd) >= 2 and ((verbo_finito(wd[0].lower()) and wd[0].lower() not in _ENCAB and not es_nombre) or (wd[0].lower() in cl and verbo_finito(wd[1].lower())))
    if clausal and any(verbo_finito(w.lower()) for w in izq.split()):
        return [izq, der]                                  # «voy al cine o me quedo en casa»
    w0 = wd[0].lower()
    # la alternativa de la derecha acaba donde empieza otro complemento: «pizza o pasta para cenar»
    preps = ("en", "a", "al", "con", "para", "por", "desde", "hasta", "sobre", "hacia", "entre", "sin", "durante")
    fin = len(wd)
    for k in range(1, len(wd)):
        if wd[k].lower() in preps:
            fin = k
            break
    if w0 not in _ENCAB:
        fin = 1 if not (len(wd) > 2 and wd[1].lower() in ("de", "del")) else min(fin, 3)
    elif w0 in ("el", "la", "los", "las", "un", "una", "unos", "unas", "mi", "mis", "tu", "tus", "su", "sus", "este", "esta", "ese", "esa"):
        fin = min(fin, 2 if not (len(wd) > 3 and wd[2].lower() in ("de", "del")) else 4)
    alt_d, cola = " ".join(wd[:fin]), " ".join(wd[fin:])
    trozos = [c.strip() for c in izq.split(",")]
    alts, pref = [], None
    for n_, c in enumerate(reversed(trozos)):
        wc = c.split()
        primero = n_ == len(trozos) - 1
        if w0 in _ENCAB:
            eq = lambda w: w.lower() == w0 or (w0 in ("al", "a") and w.lower() in ("al", "a")) or (w0 in ("del", "de") and w.lower() in ("del", "de"))
            if not primero:
                if not wc or not eq(wc[0]):
                    return None
                alts.insert(0, c)
                continue
            idx = max((k for k, w in enumerate(wc) if eq(w)), default=None)
            if idx is None or idx == 0:
                return None
            pref, alt0 = " ".join(wc[:idx]), " ".join(wc[idx:])
        else:
            if not primero:
                if len(wc) != 1:
                    return None
                alts.insert(0, c)
                continue
            if len(wc) < 2:
                return None
            pref, alt0 = " ".join(wc[:-1]), wc[-1]
        alts.insert(0, alt0)
    alts.append(alt_d)
    if not pref or not any(verbo_finito(w.lower()) for w in pref.split()):
        return None
    return [f"{pref} {a}" + (f" {cola}" if cola else "") for a in alts]


def une_o(textos):
    """«Lola vive en Teruel» + «Lola vive en Huesca» -> «Lola vive en Teruel o en Huesca» (factoriza lo común)."""
    textos = [t.rstrip(". ") for t in dict.fromkeys(textos)]
    if len(textos) == 1:
        return textos[0]
    ws = [t.split() for t in textos]
    pre = 0
    while all(len(w) > pre for w in ws) and len({w[pre].lower() for w in ws}) == 1:
        pre += 1
    suf = 0
    while all(len(w) > pre + suf for w in ws) and len({w[-1 - suf].lower() for w in ws}) == 1:
        suf += 1
    # que la parte variable empiece por la preposición: «en Teruel o en Huesca»
    while pre > 0 and ws[0][pre - 1].lower() in _ENCAB and all(len(w) - pre - suf >= 1 for w in ws):
        pre -= 1                                           # «el jueves o el viernes», «en Teruel o en Huesca», «mi padre o mi madre»
    medios = [" ".join(w[pre:len(w) - suf if suf else None]) for w in ws]
    if any(not m_ for m_ in medios):
        return " o ".join(textos)
    cab = " ".join(ws[0][:pre])
    cola = " ".join(ws[0][len(ws[0]) - suf:]) if suf else ""
    lista = ", ".join(medios[:-1]) + (" u " if sa(medios[-1]).startswith(("o", "ho")) else " o ") + medios[-1]
    return " ".join(x for x in (cab, lista, cola) if x)


# ====================================================================== condicionales
_SUBJ_IRR = {"tuviera": "tener", "tuviese": "tener", "fuera": "ser", "fuese": "ser", "estuviera": "estar", "estuviese": "estar", "hiciera": "hacer",
             "hiciese": "hacer", "pudiera": "poder", "supiera": "saber", "quisiera": "querer", "dijera": "decir", "viniera": "venir", "pusiera": "poner",
             "tuvieras": "tener", "fueras": "ser", "estuvieras": "estar", "hubiera": "haber", "hubiese": "haber", "hubieras": "haber"}
_COND_IRR = {"tendr": "tener", "ser": "ser", "estar": "estar", "har": "hacer", "podr": "poder", "dir": "decir", "saldr": "salir", "vendr": "venir",
             "pondr": "poner", "sabr": "saber", "querr": "querer", "habr": "haber", "ir": "ir", "vivir": "vivir"}
_NO_VERBO = {"como", "para", "entre", "sobre", "bajo", "vino", "casa", "cocina", "paso", "trabajo", "estudio", "sal", "cuento", "regalo", "beso", "abrazo", "llamo"}


def _pers_de(antes):
    """1s si no hay sujeto delante del verbo; 3s si lo hay («si mi hermano tuviera…»)."""
    ws = [w for w in antes.split() if w.lower() not in ("si", "no", "me", "te", "se", "le", "lo", "la", "y", "pues", "yo")]
    return "3s" if ws else "1s"


def _inf_subj(w):
    w0 = sa(w.lower())
    if w0 in _SUBJ_IRR:
        return _SUBJ_IRR[w0]
    m = re.match(r"^(.+?)(ara|ase|aras|ases)$", w0)
    if m:
        return m.group(1) + "ar"
    m = re.match(r"^(.+?)(iera|iese|ieras|ieses)$", w0)
    if m:
        for fin in ("er", "ir"):
            inf = m.group(1) + fin
            if any(x[0] == inf for x in M.analizar(M.conjugar(inf, "pres", "1s"))):
                return inf
    return None


def indicativo(p):
    """«(si) hubiera nacido en 1998» -> «nací en 1998»; «tuviera 10 años menos» -> «tengo 10 años menos»; «fuera rico» -> «soy rico»."""
    ws = p.split()
    for k, w in enumerate(ws):
        w0 = sa(w.lower())
        if w0 in ("hubiera", "hubiese", "hubieras") and k + 1 < len(ws):
            part = ws[k + 1]
            inf = next((x[0] for x in M.analizar(sa(part.lower())) if x[1] == "part"), None)
            if inf:
                pers = "2s" if w0.endswith("s") else _pers_de(" ".join(ws[:k]))
                return " ".join(ws[:k] + [M.conjugar(inf, "pret", pers)] + ws[k + 2:])
        inf = _inf_subj(w) if w0 not in _NO_VERBO else None
        if inf and inf != "haber":
            pers = "2s" if w0.endswith("s") and not w0.endswith(("ase", "iese")) else _pers_de(" ".join(ws[:k]))
            return " ".join(ws[:k] + [M.conjugar(inf, "pres", pers)] + ws[k + 1:])
    return p


def presente_de_condicional(q):
    """«¿qué edad tendría?» -> «¿qué edad tengo?» (el condicional de la pregunta hipotética pasa a presente)."""
    def _cambia(m):
        w = m.group(0)
        an = [x for x in M.analizar(sa(w.lower())) if x[1] == "cond"]
        if not an:
            return w
        pers = "2s" if sa(w.lower()).endswith("rias") else ("1p" if sa(w.lower()).endswith("riamos") else "1s")
        return M.conjugar(an[0][0], "pres", pers)
    return re.sub(r"\b[a-záéíóúñ]+r[íi]a(?:s|mos|n)?\b", _cambia, q)


def condicional_de_presente(r):
    """Respuesta en presente -> condicional: «Tienes 28 años» -> «Tendrías 28 años» (solo el primer verbo en 2.ª persona)."""
    m = re.search(r"\b([a-záéíóúñ]+(?:as|es|ás|és))\b", r, re.I)
    if not m:
        return r
    w = m.group(1)
    an = [x for x in M.analizar(sa(w.lower())) if x[1] == "pres" and x[2] == "2s"]
    if not an:
        return r
    nuevo = M.conjugar(an[0][0], "cond", "2s")
    if w[:1].isupper():
        nuevo = nuevo[:1].upper() + nuevo[1:]
    return r[:m.start(1)] + nuevo + r[m.end(1):]


def a_segunda(t):
    """«si estudio, apruebo» -> «si estudias, apruebas»; «me compro un barco» -> «te compras un barco»."""
    from .nucleo import cambia_persona
    out = []
    prev = ""
    for w in t.split():
        core = w.strip(",.;:!¡¿?")
        w0 = sa(core.lower())
        verbal = w0 not in _NO_VERBO or prev in ("", "si", "no", "yo", "me", "te", "se", "lo", "la", "nunca", "tambien", "ya")
        if prev and any(x[1] in ("pres", "pret", "fut", "imp", "cond") for x in M.analizar(prev)) and prev not in ("si", "no", "como", "para", "entre", "sobre", "bajo"):
            verbal = False                               # «hace frío»: tras un verbo conjugado no va otro
        an = [x for x in M.analizar(w0) if x[2] in ("1s", "1p") and x[1] in ("pres", "pret", "fut", "imp", "cond")] if verbal else []
        prev = w0 if not w.endswith(",") else ""
        if an and not (core[:1].isupper() and out):
            nuevo = M.conjugar(an[0][0], an[0][1], "2s")
            out.append(w.replace(core, nuevo))
        else:
            out.append(w)
    return cambia_persona(" ".join(out))


_GENERICA = re.compile(r"^(?:y\s+)?(?:qu[ée]|que)\s+(?:pasa|pasar[íi]a|pasar[áa]|ocurre|ocurrir[íi]a|ocurrir[áa]|sucede|suceder[íi]a|har[ée]|har[íi]a|hago|haces|hace|har[áa])\b", re.I)


def es_generica(q):
    return bool(_GENERICA.match(sa(q.strip("¿? ").lower())))
