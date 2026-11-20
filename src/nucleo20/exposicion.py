"""LCM 2.18 · Aprender de un texto expositivo (y de la charla que explica cosas).

Un texto que explica («el panal, una estructura de celdas de cera», «las personas que cuidan las colmenas se llaman apicultores»,
«es la seta más venenosa», «algunos… y otros…», «cuando A, B», «A, por eso B») no se entiende frase a frase como una narración.
Este módulo hace tres cosas, todas por la FORMA de la frase (ninguna regla nombra un tema):
  1. resuelve de qué se habla (el sujeto explícito más reciente) para que una frase sin sujeto nunca herede un tema dudoso;
  2. desdobla cada frase en afirmaciones sencillas que el núcleo ya entiende;
  3. guarda lo que no es un hecho simple en su forma propia: definiciones, tipos, superlativos, «el único que…», afirmaciones parciales
     («algunos…»), reglas («cuando/si…») y causas, y contesta con ello diciendo que viene de lo leído.
"""
from __future__ import annotations

import re

from . import conceptos as K
from . import morfo as M
from .morfo import sa

_DET = r"(?:el|la|los|las|un|una|unos|unas|cada|este|esta|estos|estas|ese|esa|esos|esas)"
_VAC = set("""el la los las un una unos unas de del al a en y o e u que se su sus lo le les es son era eran fue esta estan ser estar hay ha han muy mas menos tan como con por para sin sobre
no ni ya solo tambien cuando si donde quien cual cuales que como cuanto cuantos cuantas todo toda todos todas otro otra otros otras cada mi tu me te nos pasa pasan ocurre sucede hace hacen
llama llaman dice texto segun""".split())
_ADV0 = {"siempre", "nunca", "solo", "también", "tambien", "ya", "casi", "apenas", "aún", "aun", "todavía", "todavia", "no", "se", "que", "le", "les", "lo", "la", "los", "las", "me", "nos"}


def expo(nuc):
    d = nuc.usuario.setdefault("expo", {})
    for k in ("defs", "superl", "parc", "reglas", "unico", "restr"):
        d.setdefault(k, [])
    d.setdefault("tipos", {})
    return d


def _fin3(w):
    """¿Es una forma verbal conjugada de 3.ª persona? Devuelve 's', 'p' o None."""
    w = w.lower().strip(",.;:")
    try:
        an = M.analizar(w) or []
    except Exception:                                    # noqa
        an = []
    for a in an:
        if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut") and a[2] in ("3s", "3p"):
            return "s" if a[2] == "3s" else "p"
    return None


def _sing(w):
    return M.singular(w) if len(w) > 3 else w


def claves(t):
    out = set()
    for w in re.findall(r"[a-záéíóúñü0-9]+", (t or "").lower()):
        w0 = sa(w)
        if w0 in _VAC or len(w0) < 2:
            continue
        me = re.match(r"^(.+(?:ar|er|ir))(?:se)?(?:lo|la|los|las|le|les|me|te|nos)$", w0)
        if me and len(me.group(1)) >= 4:                 # «cazarlos» -> cazar
            w0 = w = me.group(1)
        try:
            an = M.analizar(w)
        except Exception:                                # noqa
            an = None
        out.add(an[0][0] if an and len(w0) > 3 and not K._kb_clase(sa(_sing(w0))) else sa(_sing(w0)))
    return out


def sujeto(f):
    """(SN sujeto, resto) si la frase empieza por un sujeto explícito («La abeja obrera | muere»), o (None, f)."""
    ws = f.split()
    if len(ws) < 2:
        return None, f
    w0 = sa(ws[0].lower())
    if re.fullmatch(_DET, w0):
        if sa(_sing(ws[1].lower().strip(","))) in ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo", "dia", "mañana", "manana", "tarde", "noche", "año", "ano", "mes", "semana", "verano",
                                            "invierno", "otoño", "otono", "primavera", "fin", "otro", "otra", "vez", "primer", "primero", "resto"):
            return None, f
        i = 2
        while i < len(ws):
            w = ws[i].lower().strip(",")
            if ws[i - 1].endswith(","):
                break
            tras_prep = ws[i - 1].lower() in ("de", "a", "en", "con", "por", "para", "sobre", "entre", "sin", "hasta", "desde", "y")
            if (w in _ADV0 and not (tras_prep and w in ("la", "los", "las", "lo"))) or (_fin3(w) and not tras_prep) or w in ("es", "son", "era", "eran", "está", "están", "hay"):
                break
            i += 1
        if i < len(ws):
            return " ".join(ws[:i]), " ".join(ws[i:])
        return None, f
    if ws[0][:1].isupper() and not _fin3(ws[0]) and w0 not in ("en", "para", "cuando", "si", "al", "a", "de", "por", "con", "se", "su", "sus", "hay", "despues", "antes", "gracias", "debajo", "algunos",
                                                                 "algunas", "muchos", "muchas", "nunca", "siempre", "tambien", "ademas", "es", "son", "esta", "estan", "no", "como", "segun", "desde", "hasta", "durante", "entre", "sobre", "tras", "casi", "solo"):
        i = 1
        while i < len(ws) and ws[i][:1].isupper():
            i += 1
        if i < len(ws) and (_fin3(ws[i]) or ws[i].lower() in ("es", "son", "se", "no")):
            return " ".join(ws[:i]), " ".join(ws[i:])
    return None, f


def _num(sn):
    w = sa(sn.split()[0].lower())
    return "p" if w in ("los", "las", "unos", "unas", "estos", "estas", "esos", "esas", "algunos", "algunas") else "s"


def _min(x):
    return x[:1].lower() + x[1:] if x and not (len(x) > 1 and x[1:2].isupper()) else x


def _may(x):
    return x[:1].upper() + x[1:] if x else x


def _propio(sn):
    """«El Teide», «Marta»: nombre propio (no se pasa a minúscula ni es una clase)."""
    ws = sn.split()
    return any(w[:1].isupper() for w in ws[1:]) or (len(ws) == 1 and ws[0][:1].isupper())


class Hilo:
    """De qué se viene hablando: último sujeto explícito en singular y en plural."""

    def __init__(self):
        self.s = None
        self.p = None
        self.ult = None
        self.previa = ""

    def pon(self, sn):
        if not sn:
            return
        if _num(sn) == "p":
            self.p = sn
        else:
            self.s = sn
        self.ult = sn

    def para(self, n):
        return (self.p if n == "p" else self.s) or None


def resuelve(f, hilo):
    """Devuelve (frase con sujeto explícito, sujeto) o (None, None) si no hay sujeto y no se sabe de quién se habla."""
    sn, _ = sujeto(f)
    if sn:
        return f, sn
    ws = f.split()
    if not ws:
        return None, None
    w0 = ws[0].lower()
    m = re.match(r"^(Su|Sus)\s+([a-záéíóúñü]+)\b(.*)$", f)
    if m and hilo.ult:
        pl = m.group(1) == "Sus"
        g = M.genero_sust(sa(_sing(m.group(2)))) == "f"
        art = ("Las" if g else "Los") if pl else ("La" if g else "El")
        nuevo = f"{art} {m.group(2)} de {_min(hilo.ult) if not _propio(hilo.ult) else hilo.ult}{m.group(3)}"
        return re.sub(r" de [Ee]l ", " del ", nuevo), None
    mp = re.match(r"^((?:En|Durante|Por|Con|Sin|Desde|Bajo|Sobre|Dentro de|Fuera de)\s+(?:(?:el|la|los|las|su|sus|ese|esa)\s+)?[a-záéíóúñü]+(?:\s+[a-záéíóúñü]+)?),?\s+((?!se\b|hay\b|no hay\b)(?:no\s+)?[a-záéíóúñü]+)\b(.*)$", f)
    if mp and not re.match(r"^Por (?:eso|ello)\b", f):
        vb = mp.group(2).split()[-1]
        n_pp = _fin3(vb) or ("p" if vb in ("son", "están") else "s" if vb in ("es", "está") else None)
        t_pp = hilo.para(n_pp) if n_pp else None
        if n_pp and t_pp and not re.match(r"^\s*(?:el|la|los|las|un|una|unos|unas)\s+[a-záéíóúñü]+\s*$", mp.group(3)):
            return f"{t_pp} {mp.group(2)}{mp.group(3)} {_min(mp.group(1))}", t_pp
    n = _fin3(w0) or ("s" if w0 in ("es", "está", "tiene") else "p" if w0 in ("son", "están", "tienen") else None)
    if n and w0 not in ("hay",):
        t = hilo.para(n)
        if t:
            return f"{t} {_min(f)}", t
        return None, None
    return f, None


# ------------------------------------------------------------------ desdoblar una frase expositiva
def _limpia(f):
    f = re.sub(r"\b(?:también|tambien|además|ademas)\s+", "", f)
    f = re.sub(r"\b(es|son|era|eran)\s+solo\s+", r"\1 ", f)
    f = re.sub(r"\b(es|son)\s+otr([oa])\s+", lambda m: f"{m.group(1)} un{'a' if m.group(2) == 'a' else ''} ", f)
    f = re.sub(r"\b(es|son|era|eran)\s+de\s+color\s+", r"\1 ", f)
    f = re.sub(r"\bya\s+no\b", "no", f)
    f = re.sub(r",?\s+sobre todo\b", "", f)
    return re.sub(r"\s+", " ", f).strip()


def _cab(sn):
    """Núcleo de un SN: («el», «panal») para «el panal»; el artículo puede faltar."""
    ws = sn.strip().split()
    if not ws:
        return "", ""
    if re.fullmatch(_DET, sa(ws[0].lower())) and len(ws) > 1:
        return ws[0].lower(), " ".join(ws[1:])
    return "", " ".join(ws)


def _un(n):
    return ("una " if M.genero_sust(sa(_sing(n.split()[0]))) == "f" else "un ") + n


def _el(n, pl=False):
    g = M.genero_sust(sa(_sing(n.split()[0]))) == "f"
    return (("las " if g else "los ") if pl else ("la " if g else "el ")) + n


def _restrictivo(sn):
    """«Los volcanes extinguidos», «un volcán dormido»: un SUBGRUPO de una clase conocida; lo que se diga no vale para toda la clase."""
    det, resto = _cab(sn)
    ws = resto.split()
    if len(ws) != 2 or _propio(sn) or det in ("este", "esta", "estos", "estas", "ese", "esa", "esos", "esas"):
        return False
    n, adj = sa(_sing(ws[0].lower())), sa(ws[1].lower())
    if not K._kb_clase(n):
        return False
    if K._kb_clase(sa(_sing(adj))) and not re.search(r"(?:ad|id)[oa]s?$", adj):
        return False
    return bool(re.search(r"(?:[oa]s?|es|ales?|ntes?|bles?)$", adj))


def _individuo(sn):
    """«La hija de Olga», «el loro», «el del primero»: alguien concreto a quien se pone nombre (no un término que se define)."""
    det, resto = _cab(sn)
    ws = resto.split()
    if not ws or not det or sa(ws[0].lower()) in ("de", "del", "que"):
        return True
    h = sa(_sing(ws[0].lower()))
    try:
        from .nucleo import FAMILIA
    except Exception:                                    # noqa
        FAMILIA = set()
    anc = set(K.ancestros(K._kb_clase(h) or h))
    return h in FAMILIA or M.masc(h) in FAMILIA or bool(anc & {"persona", "animal", "familiar", "profesional"}) or h in ("persona", "animal")


def desdobla(f, hilo, ex, reg=True):
    """Lista de frases sencillas para el núcleo. Lo que no es un hecho simple se guarda en `ex` (si reg)."""
    f = f.strip().rstrip(".!").strip()
    out = []

    def anota(clave, dato):
        if reg and dato not in ex[clave]:
            ex[clave].append(dato)
            del ex[clave][:-120]

    m = re.match(r"^Por (?:eso|ello|esa razón|ese motivo),?\s+(.+)$", f)
    if m and hilo.previa:
        b0 = m.group(1).strip()
        anota("reglas", {"tipo": "causa", "cons": _may(b0), "cond": _min(hilo.previa.rstrip("."))})
        return []
    # --- «A, por eso B» / «B, porque A»
    m = re.match(r"^(.+?),?\s+(?:y\s+)?por eso\s+(.+)$", f)
    if m:
        a, b = m.group(1).strip(), m.group(2).strip()
        sa_, _ = sujeto(a)
        if not sujeto(_may(b))[0] and sa_ and _fin3(b.split()[0]):
            b = f"{sa_} {b}"
        anota("reglas", {"tipo": "causa", "cons": _may(b), "cond": a})
        return desdobla(a, hilo, ex, reg) + desdobla(_may(b), hilo, ex, reg)
    m = re.match(r"^(.+?),\s+(?:porque|ya que|pues)\s+(.+)$", f)
    if m:
        anota("reglas", {"tipo": "causa", "cons": m.group(1).strip(), "cond": m.group(2).strip()})
        f = m.group(1).strip()
    # --- contraste: «A, mientras que B», «A, aunque B», «A, pero B»
    m = re.match(r"^(.+?),\s+(?:mientras que|aunque|pero|sin embargo)\s+(.+)$", f) or re.match(r"^(.+?);\s+(.+)$", f)
    if m:
        a, b = m.group(1).strip(), _may(m.group(2).strip())
        sa_, _ = sujeto(a)
        if not sujeto(b)[0] and sa_ and (_fin3(b.split()[0]) or b.split()[0].lower() in ("es", "son", "no")) and not re.match(r"^(?:si|cuando)\b", b, re.I):
            b = f"{sa_} {_min(b)}"
        return desdobla(a, hilo, ex, reg) + desdobla(b, hilo, ex, reg)
    m = re.match(r"^(?:La mayoría|La mayor parte|Casi todos|Casi todas|Muchos|Muchas)\s+(?:de\s+)?(?:los|las)\s+([a-záéíóúñü]+)\s+(.+?)(?:,?\s+(?:pero|aunque|y)\s+(?:algun[oa]s|otr[oa]s|unos pocos)\s+(.+))?$", f)
    if m:
        anota("parc", {"cls": sa(_sing(m.group(1).lower())), "disp": m.group(1), "a": m.group(2).strip(), "b": (m.group(3) or "").strip(), "mayoria": True})
        return []
    # --- reglas: «Cuando/Si A, B», «B si/cuando A»
    m = re.match(r"^(Cuando|Si|Siempre que|Después de|Despues de|Antes de|Al)\s+(.+?),\s+(.+)$", f)
    if m and not re.search(r"\bse (?:llama|llaman|dice que)\b", f):
        anota("reglas", {"tipo": "cond", "con": m.group(1).lower(), "cond": m.group(2).strip(), "cons": m.group(3).strip(), "tema": hilo.ult or ""})
        return []
    m = re.match(r"^Cuando\s+(.+?)\s+se dice que\s+(.+)$", f)
    if m:
        anota("reglas", {"tipo": "cond", "con": "cuando", "cond": m.group(1).strip(), "cons": m.group(2).strip(), "tema": hilo.ult or ""})
        return []
    m = re.match(r"^(.+?)\s+(?:solo\s+)?(si|cuando)\s+(.+)$", f)
    if m and sujeto(m.group(1))[0] and len(m.group(1).split()) >= 3 and _fin3(m.group(3).split()[0] if m.group(3).split()[0] not in ("se", "no", "le") else "es"):
        anota("reglas", {"tipo": "cond", "con": m.group(2), "cond": m.group(3).strip(), "cons": re.sub(r"\s+solo$", "", m.group(1).strip()), "tema": hilo.ult or ""})
        return []
    m = re.match(r"^si\s+(.+?)\s+(se\s+\w+.*)$", _min(f))
    if m and hilo.ult:
        anota("reglas", {"tipo": "cond", "con": "si", "cond": f"{_min(hilo.ult)} {m.group(1).strip()}", "cons": m.group(2).strip(), "tema": hilo.ult})
        return []
    m = re.search(r"\bse\s+(?:les?\s+|los\s+|las\s+|la\s+|lo\s+)?llaman?\s+(?:[a-záéíóúñü]+\s+)?[A-ZÁÉÍÓÚÑ]", f)
    if m or (re.search(r"\bse\s+llaman?\b", f) and not re.match(r"^(?:(?:Los|Las|El|La)\s+(?:[a-záéíóúñü]+\s+)?que|Cuando|Si|A\s+(?:los|las))\b", f) and _individuo(re.split(r"\s+se\s+llaman?\b", f)[0])):
        return [f + "."]                                 # «El loro se llama Kiko»: poner nombre a alguien es cosa del núcleo, no una definición
    # --- nombrar: «Los N que VP se llaman X», «Las que VP se llaman X», «A los N se les llama X», «SN se llama X», «Este N se llama X», «Cuando A se llama X»
    m = re.match(r"^(Los|Las|El|La)\s+([a-záéíóúñü]+)\s+que\s+(.+?)\s+se\s+llama(?:n|ba|ban)?\s+(.+)$", f) or re.match(r"^(Los|Las|El|La)()\s*que\s+(.+?)\s+se\s+llama(?:n|ba|ban)?\s+(.+)$", f)
    if m and len(m.group(4).split()) <= 3:
        plq = m.group(1) in ("Los", "Las")
        cls = m.group(2) or (ex.get("_ult_cls") or ("personas" if plq else "persona"))
        x = m.group(4).strip()
        ex["_ult_cls"] = cls
        anota("defs", {"t": sa(_sing(x.lower())), "disp": x, "d": f"{m.group(1).lower()} {cls} que {m.group(3)}", "pl": plq})
        hilo.pon(_may(_el(x, pl=plq)))
        return [f"{_may(_un(_sing(x)))} es {_un(_sing(cls))}.", f"{_may(_el(x, pl=plq))} {m.group(3)}."]
    m = re.match(r"^A\s+(.+?)\s+se\s+(?:les?|los|las|la|lo)\s+llaman?\s+(.+)$", f)
    if m:
        anota("defs", {"t": sa(_sing(m.group(2).lower())), "disp": m.group(2), "d": m.group(1), "pl": True})
        return []
    m = re.match(r"^Cuando\s+(.+?)\s+se\s+llaman?\s+(.+)$", f)
    if m:
        anota("defs", {"t": sa(_sing(m.group(2).lower())), "disp": m.group(2), "d": "cuando " + m.group(1), "cuando": True})
        return []
    m = re.match(r"^(Este|Esta|Esto|Eso|Estos|Estas)(?:\s+[a-záéíóúñü]+)?\s+se\s+llaman?\s+(.+)$", f)
    if m:
        if hilo.previa:
            anota("defs", {"t": sa(_sing(m.group(2).lower())), "disp": m.group(2), "d": "que " + _min(hilo.previa.rstrip(".")), "previa": True})
        return []
    m = re.match(r"^(.+?)\s+se\s+llaman?\s+(.+)$", f)
    if m and re.match(r"^" + _DET + r"\b", sa(m.group(1).lower())) and not _fin3(m.group(1).split()[-1]) and len(m.group(2).split()) <= 3:
        anota("defs", {"t": sa(_sing(m.group(2).lower())), "disp": m.group(2), "d": _min(m.group(1))})
        return []
    # --- «…, llamad@ X» / «N llamad@s X»
    m = re.match(r"^(.*?)(" + _DET + r"\s+)?((?:[a-záéíóúñü]+\s+){0,2}[a-záéíóúñü]+(?:\s+[a-záéíóúñü]+){0,3}?),?\s+llamad[oa]s?\s+([a-záéíóúñü ]+)$", f)
    if m and len(m.group(4).split()) <= 2:
        d = re.sub(r"^(?:hay|existen?|tienen?|viven en|en)\s+", "", m.group(3).strip())
        anota("defs", {"t": sa(_sing(m.group(4).strip().lower())), "disp": m.group(4).strip(), "d": d})
        f = re.sub(r",?\s+llamad[oa]s?\s+[a-záéíóúñü ]+$", "", f)
    # --- aposición que define: «…el panal, una estructura de celdas de cera», «…el cráter, que es la boca del volcán»
    m = re.match(r"^(.*?)\b((?:el|la|los|las)\s+)?([a-záéíóúñü]+),\s+(?:que\s+(?:es|son)\s+)?((?:un|una|unos|unas|el|la|los|las)\s+.+)$", f)
    if m and ", " not in m.group(4) and not re.search(r"\s+[ye]\s+(?:un|una|el|la|los|las)?\s*[a-záéíóúñü]+$", m.group(4)) \
            and (m.group(2) or not re.search(r"\b(?:un|una|unos|unas)\s+(?:[a-záéíóúñü]+\s+)?$", m.group(1) + " ")) \
            and (re.search(r",\s+que\s+(?:es|son)\s+", f) or re.match(r"^(?:un|una|unos|unas)\b", m.group(4))) and (re.search(r",\s+que\s+(?:es|son)\s+", f) or not re.match(r"^(?:los|las)\b", m.group(4))):
        x, d = m.group(3), m.group(4).strip()
        pl = (m.group(2) or "").strip().lower() in ("los", "las") or (not m.group(2) and x.endswith("s"))
        anota("defs", {"t": sa(_sing(x.lower())), "disp": x, "d": d, "pl": pl})
        principal = (m.group(1) + (m.group(2) or "") + x).strip()
        d0 = re.split(r"\s+que\s+", d)[0]
        d0 = re.sub(r"^(?:unos|unas)\s+", "", d0) if pl else d0
        extra_d = [] if re.match(r"^(?:los|las)\b", d0) else [f"{_may(_el(x, pl=pl))} {'son' if pl else 'es'} {d0}."]
        return desdobla(principal, hilo, ex, reg) + extra_d
    # --- tipos: «hay tres tipos de N: a, b y c»
    m = re.match(r"^(.*?)\b(?:[a-záéíóúñü]+\s+)?(?:tipos|clases|especies|variedades)\s+de\s+([a-záéíóúñü]+)\s*:\s*(.+)$", f)
    if m:
        items = [re.sub(r"^(?:el|la|los|las|un|una)\s+", "", x.strip()) for x in re.split(r",\s*|\s+y\s+|\s+e\s+", m.group(3)) if x.strip()]
        if reg and items:
            ex["tipos"].setdefault(sa(_sing(m.group(2).lower())), [])
            for it in items:
                if it not in ex["tipos"][sa(_sing(m.group(2).lower()))]:
                    ex["tipos"][sa(_sing(m.group(2).lower()))].append(it)
        return []
    # --- elaboración tras dos puntos y «no … ni …»
    m = re.match(r"^(.+?):\s+([a-záéíóúñü]+)\b(.*)$", f)
    if m and _fin3(m.group(2)) and not re.search(r"\b(?:partes|tipos|clases)\b", m.group(1)):
        sa_, _ = sujeto(m.group(1))
        b = f"{m.group(2)}{m.group(3)}"
        return desdobla(m.group(1), hilo, ex, reg) + desdobla(f"{sa_} {b}" if sa_ else _may(b), hilo, ex, reg)
    m = re.match(r"^(.+?\bno\s+[a-záéíóúñü]+)\s+(.+?)\s+ni\s+(.+)$", f)
    if m and len(m.group(2).split()) <= 3 and len(m.group(3).split()) <= 3:
        return [f"{m.group(1)} {m.group(2)}.", f"{m.group(1)} {m.group(3)}."]
    f = _limpia(f)
    sn, resto = sujeto(f)
    if sn:
        m = re.match(r"^(.+?),?\s+y\s+(lo|la|los|las)\s+([a-záéíóúñü]+)\s+((?:el|la|los|las|un|una|unos|unas)\s+[a-záéíóúñü ]+|[A-ZÁÉÍÓÚÑ][\wáéíóúñü ]+)$", f)
        if m and _fin3(m.group(3)) and len(m.group(4).split()) <= 4:
            # «…y la construyeron los romanos»: el sujeto va detrás y «la» es aquello de lo que se habla
            return desdobla(m.group(1), hilo, ex, reg) + [f"{_may(m.group(4).strip())} {m.group(3)} {_min(sn) if not (_propio(sn) or sn[:1].isupper() and len(sn.split()) == 1) else sn}."]
        m = re.match(r"^(.+?)\s+y\s+((?:a veces|también|además|luego|después|entonces|así|nunca|siempre|no)\s+)?((?:se\s+|no\s+)?[a-záéíóúñü]+)\b(.*)$", f)
        if m and len(m.group(1).split()) > len(sn.split()) and _fin3(m.group(3).split()[-1]) and not K._kb_clase(sa(_sing(m.group(3).split()[-1]))) \
                and _fin3(sujeto(m.group(1) + " x")[1].split()[0] if sujeto(m.group(1) + " x")[1].split()[0] not in ("se", "no") else "es") \
                and not re.search(r"\b(?:entre|tanto|ni)\b", m.group(1)):
            seg = f"{sn} {(m.group(2) or '')}{m.group(3)}{m.group(4)}"
            return desdobla(m.group(1), hilo, ex, reg) + desdobla(re.sub(r"\s+", " ", seg), hilo, ex, reg)
    # --- parciales: «Algunos N son A y otros son B»
    m = re.match(r"^Algun[oa]s\s+([a-záéíóúñü]+)\s+(.+?)\s+y\s+otr[oa]s\s+(.+)$", f)
    if m:
        anota("parc", {"cls": sa(_sing(m.group(1).lower())), "disp": m.group(1), "a": m.group(2).strip(), "b": (m.group(3) or "").strip()})
        return []
    if not sn:
        return [f + "."]
    # --- un subgrupo («los volcanes extinguidos…»): no vale para toda la clase; se guarda aparte
    if _restrictivo(sn):
        anota("restr", {"sn": sn, "resto": resto, "cls": sa(_sing(_cab(sn)[1].split()[0].lower()))})
        return []
    # --- relativa en el sujeto: «El moho que aparece en el pan viejo es un hongo»
    m = re.match(r"^(.+?)\s+que\s+(.+?)\s+(es|son)\s+(.+)$", f)
    if m and sujeto(m.group(1) + " es")[0] and _fin3(m.group(2).split()[0]):
        return desdobla(f"{m.group(1)} {m.group(3)} {m.group(4)}", hilo, ex, reg) + [f"{m.group(1)} {m.group(2)}."]
    # --- «X es el/la único/a (N) que VP»
    m = re.match(r"^(es|son|fue|era|fueron)\s+(?:el|la|los|las)\s+(?:únic[oa]s?|primer[oa]?s?|últim[oa]s?)(?:\s+([a-záéíóúñü]+))?\s+que\s+(.+)$", resto)
    if m:
        orden = re.search(r"\b(únic[oa]s?|primer[oa]?s?|últim[oa]s?)\b", resto).group(1)
        anota("unico", {"ent": sn, "cls": sa(_sing((m.group(2) or "").lower())), "vp": m.group(3), "ord": orden})
        extra = [f"{sn} es {_un(_sing(m.group(2)))}."] if m.group(2) else []
        return extra + [f"{sn} {m.group(3)}."]
    # --- superlativos: «X es el N más ADJ (de Y)», «X es uno de los N más ADJ»
    m = re.match(r"^(es|son|era)\s+(?:el|la|los|las)\s+([a-záéíóúñü]+)\s+(más|menos)\s+([a-záéíóúñü]+)(?:\s+(de(?:l)?\s+.+|que\s+exist[ea]n?|que\s+hay|conocid[oa]s?))?$", resto)
    if m:
        amb = m.group(5) or ""
        anota("superl", {"ent": sn, "cls": sa(_sing(m.group(2).lower())), "adj": sa(M.masc(_sing(m.group(4).lower()))), "signo": m.group(3), "amb": amb if amb.startswith("de") else "",
                         "disp": f"{m.group(2)} {m.group(3)} {m.group(4)}{' ' + amb if amb else ''}"})
        base = [f"{sn} es {_un(_sing(m.group(2)))}."]
        return base + ([f"{sn} es muy {m.group(4)}."] if m.group(3) == "más" else [])
    m = re.match(r"^(es|son)\s+un[oa]\s+de\s+(?:los|las)\s+([a-záéíóúñü]+)\s+más\s+([a-záéíóúñü]+)(?:\s+.+)?$", resto)
    if m:
        adj = _sing(m.group(3))
        if M.genero_sust(sa(_sing(_cab(sn)[1].split()[0]))) == "f" and adj.endswith("o"):
            adj = adj[:-1] + "a"
        return [f"{sn} es {_un(_sing(m.group(2)))}.", f"{sn} es muy {adj}."]
    # --- «X es un N que VP»: la clase y lo que hace, por separado
    m = re.match(r"^(es|son)\s+((?:un|una|unos|unas)\s+[a-záéíóúñü]+(?:\s+(?:de\s+|del\s+)?[\wáéíóúñü]+){0,2}?)\s+que\s+(?:solo\s+|siempre\s+|casi\s+siempre\s+)?(.+)$", resto)
    if m and _fin3(m.group(3).split()[0] if m.group(3).split()[0] not in ("se", "no") else "es"):
        anota("defs", {"t": sa(_sing(_cab(sn)[1].lower())), "disp": _cab(sn)[1], "d": f"{m.group(2)} que {m.group(3)}"})
        clase = re.sub(r"^(?:unos|unas)\s+", "", m.group(2))
        return [f"{sn} {m.group(1)} {clase}.", f"{sn} {m.group(3)}."]
    m = re.match(r"^(es|son)\s+(?:el|la|los|las)\s+(?:alimento|comida)s?\s+(?:principal(?:es)?\s+)?de\s+(.+)$", resto)
    if m:
        quien = _may(m.group(2).strip())
        return [f + ".", f"{quien} come{'n' if _num(quien) == 'p' else ''} {_min(sn) if not _propio(sn) else sn}."]
    m = re.match(r"^(son)\s+([a-záéíóúñü]+(?:\s+[a-záéíóúñü]+)?)\s+que\s+(.+)$", resto)
    if m and _num(sn) == "p" and not _propio(sn) and sa(m.group(2).split()[0]) not in ("los", "las", "unos", "unas", "tan", "mas", "muy", "lo"):
        anota("defs", {"t": sa(_sing(_cab(sn)[1].split()[0].lower())), "disp": _cab(sn)[1], "d": f"{m.group(2)} que {m.group(3)}", "pl": True})
        return [f"{sn} son {m.group(2)}."]
    m = re.match(r"^(es|son)\s+((?:un|una|el|la)\s+[a-záéíóúñü]+\s+.+)$", resto)
    if m and not _propio(sn) and len(m.group(2).split()) >= 4 and _cab(sn)[0] in ("un", "una", "el", "la", "los", "las") and len(_cab(sn)[1].split()) == 1:
        anota("defs", {"t": sa(_sing(_cab(sn)[1].lower())), "disp": _cab(sn)[1], "d": m.group(2), "pl": _num(sn) == "p"})
    return [f + "."]


def inversa(texto):
    """«¿Qué pieza se mueve en diagonal?» -> «¿Quién se mueve en diagonal?» (la clase se comprueba con la respuesta)."""
    m = re.match(r"^\W*(?:y\s+)?(?:qu[eé]|cu[aá]l)\s+([a-záéíóúñü]+)\s+(.+?)\?*$", texto.strip(), re.I)
    if not m or m.group(1).lower() in ("es", "son", "hay", "pasa", "hace", "hacen", "tipo", "tipos", "clase", "se", "le", "les", "me", "te", "tiene", "tienen", "puede", "pueden", "significa"):
        return None
    w = m.group(2).split()[0].lower()
    if not (_fin3(w) or w in ("es", "son", "está", "están", "se", "no", "tiene", "tienen", "puede", "pueden")):
        return None
    return f"¿Quién {m.group(2)}?"


# ------------------------------------------------------------------ leer una frase (texto o charla)
def procesa(nuc, f, hilo, reg=True):
    """Lee UNA frase expositiva. Devuelve (n.º de hechos nuevos del núcleo, n.º de datos guardados aparte, frase resuelta)."""
    ex = expo(nuc)
    antes_ex = sum(len(v) for v in ex.values() if isinstance(v, (list, dict)))
    from . import compuestos as C
    try:
        C.aprende_propios(nuc, f)
        f = C.codifica(nuc, f)
    except Exception:                                    # noqa
        pass
    f1, sn = resuelve(f.strip().rstrip("."), hilo)
    if f1 is None:
        return 0, 0, None
    enlace = None
    sn1, resto1 = sujeto(f1)
    if sn1 and len(sn1.split()) == 3:                    # 2.19: «el zorro volador», «un café solo»: el nombre de una clase, una sola pieza
        try:
            ya = set(C.tabla(nuc))
            cl = C.aprende_clase(nuc, sn1)
            if cl:
                f1 = C.codifica(nuc, f1)
                if sa(cl[0].lower()) not in ya and not re.match(r"^(?:es|son|era|fue)\s+(?:un|una|el|la|los|las)\s+(?!más\b|menos\b)", resto1):
                    enlace = cl
        except Exception:                                # noqa
            pass
    partes = desdobla(f1, hilo, ex, reg)
    n0 = len(nuc.F)
    if enlace:
        try:
            nuc._procesar_charla(f"{_may(_un(enlace[0]))} es {_un(enlace[1])}.")
            for fr in nuc.F[n0:]:
                fr["enlace"] = True
        except Exception:                                # noqa
            pass
        nuc.pend = None
        n0 = len(nuc.F)
    oks = 0
    for p in partes:
        p1, _ = resuelve(p.rstrip("."), hilo)
        if p1 is None:
            continue
        sn_p, _ = sujeto(p1)
        if sn_p and _restrictivo(sn_p):
            ex["restr"].append({"sn": sn_p, "resto": sujeto(p1)[1], "cls": sa(_sing(_cab(sn_p)[1].split()[0].lower()))})
            continue
        try:
            rp = nuc._procesar_charla(p1 + ".")
        except Exception:                                # noqa
            rp = None
        if isinstance(rp, dict) and rp.get("estado") == "ok" and rp.get("tipo") == "ack" and not sa((rp.get("respuesta") or "").lower()).startswith("no lo he entendido"):
            oks += 1                                     # lo ha entendido aunque no deje un hecho (p. ej. una relación «sirve para»)
        nuc.pend = None
    sn0, _ = sujeto(f1)
    if sn0 and not re.match(r"^(?:Las|Los) (?:personas )?que\b", f1) and not re.match(r"^(?:Su|Sus)\b", f.strip()) and not re.match(r"^Cada\b", sn0):
        hilo.pon(sn0)                                    # el tema no deriva hacia «sus alas» ni hacia «cada tirna»
    hilo.previa = f1
    despues_ex = sum(len(v) for v in ex.values() if isinstance(v, (list, dict)))
    return max(len(nuc.F) - n0, oks), despues_ex - antes_ex, f1


# ------------------------------------------------------------------ contestar con lo guardado aparte
def _solapa(q, d, minimo=0.6):
    if not q or not d:
        return 0.0
    c = len(q & d)
    return c / len(d) if (c >= max(1, round(minimo * len(d))) and c >= max(1, round(minimo * len(q)))) else 0.0


def _ok(nuc, txt, src=None):
    nuc.turno += 1
    nuc.ult_just = {"dicho": [src] if src else [], "pasos": ["lo aprendí de lo que leí o me explicaste"]}
    return {"respuesta": txt, "estado": "ok", "consultar": False, "tipo": "resp"}


def _def_de(ex, w):
    w = sa(_sing(w.lower().strip()))
    w = re.sub(r"^(?:el|la|los|las|un|una)\s+", "", w)
    for d in reversed(ex["defs"]):
        if d["t"] == w or sa(d["disp"].lower()) == w:
            return d
    return None


def _superl_de(ex, cls, adj, signo="más", amb=""):
    for s in reversed(ex["superl"]):
        if s["cls"] == sa(_sing(cls)) and s["adj"] == sa(M.masc(_sing(adj))) and s["signo"] == signo:
            if amb and s["amb"] and not (claves(amb) & claves(s["amb"])):
                continue
            return s
    return None


def sustituye(nuc, texto):
    """Descripciones definidas -> la cosa: «el volcán más alto de España» -> «el Teide»; «la que pone los huevos» -> «la reina»."""
    ex = expo(nuc)
    if not (ex["superl"] or ex["unico"]) or "?" not in texto:
        return texto
    if re.match(r"^\W*(?:cu[aá]l(?:es)?|qui[eé]n(?:es)?|qu[eé]\s+[a-záéíóúñü]+)\s+(?:es|son|fue|era)\b", texto, re.I):
        return texto
    m = re.search(r"\b(el|la|los|las)\s+([a-záéíóúñü]+)\s+(más|menos)\s+([a-záéíóúñü]+)((?:\s+de(?:l)?\s+(?:[A-ZÁÉÍÓÚÑ][\wáéíóúñü]+|mundo|todos|todas))?)", texto)
    if m:
        s = _superl_de(ex, m.group(2).lower(), m.group(4).lower(), m.group(3), m.group(5))
        if s:
            return texto[:m.start()] + _min(s["ent"]) + texto[m.end():]
    m = re.search(r"\b(?:el|la|los|las)\s+(?:(?:únic[oa]s?|primer[oa]?s?|últim[oa]s?)\s+)?(?:[a-záéíóúñü]+\s+)?que\s+([^?]+)", texto)
    if m and not re.match(r"^\W*(?:qui[eé]n|cu[aá]l|qu[eé]\s+[a-záéíóúñü]+)\s+(?:es|fue|era|son)\b", texto, re.I):
        q = claves(m.group(1))
        for u in reversed(ex["unico"]):
            cu = claves(u["vp"])
            if _solapa(q, cu) or (cu and cu <= q):
                ent = u["ent"] if _propio(u["ent"]) or u["ent"][:1].isupper() and len(u["ent"].split()) == 1 else _min(u["ent"])
                return texto[:m.start()] + ent + "?"
    return texto


def responder(nuc, texto):
    """Preguntas que se contestan con definiciones, tipos, superlativos, parciales, reglas y causas aprendidas."""
    ex = expo(nuc)
    if "?" not in texto or not any(ex[k] for k in ("defs", "superl", "parc", "reglas", "unico", "tipos", "restr")):
        return None
    n = sa(texto.lower()).strip(" ¿?¡!.")
    n = re.sub(r"^(?:y|pero|entonces|oye|dime)\s*,?\s+", "", n)
    # ¿qué es X?
    m = re.match(r"^que (?:es|son|significa|quiere decir) (?:(?:el|la|los|las|un|una|unos|unas) )?([a-zñ ]+)$", n)
    if m:
        d = _def_de(ex, m.group(1))
        if d and not d.get("cuando") and not d.get("previa") and len(d["d"].split()) < 2:
            d = None
        if d:
            nombre = d["disp"] if d.get("pl") or d.get("cuando") else _el(d["disp"]) if not re.match(_DET, d["disp"]) else d["disp"]
            if d.get("cuando"):
                return _ok(nuc, f"Se llama {d['disp']} {d['d']}. Lo he aprendido de lo que leí o me explicaste.")
            if d.get("previa"):
                return _ok(nuc, f"Según lo que he aprendido, se llama {d['disp']} a esto: {d['d'][4:]}.")
            pl = d.get("pl")
            mia = f"{_el(_sing(d['disp'])) if not pl else _el(d['disp'], pl=True)} {'son' if pl else 'es'} {d['d']}"
            if not getattr(nuc, "_reform", False):
                nuc._reform = True
                try:
                    rn = nuc._procesar_charla(texto)
                except Exception:                        # noqa
                    rn = None
                finally:
                    nuc._reform = False
                if isinstance(rn, dict) and rn.get("estado") == "ok" and rn.get("respuesta"):
                    if claves(d["d"]) <= claves(rn["respuesta"]):
                        return rn
                    return dict(rn, respuesta=rn["respuesta"].rstrip() + f" Además, según lo que he aprendido, {mia}.")
            return _ok(nuc, f"Según lo que he aprendido, {mia}.")
    # ¿cómo se llama(n) D? / ¿cómo se (le) llama a D?
    m = re.match(r"^como se (?:les? |las? |los? )?llaman? (?:a )?(.+)$", n)
    if m:
        q = claves(m.group(1))
        mejor = None
        for d in ex["defs"]:
            s = _solapa(q, claves(d["d"]), 0.5)
            if s and (mejor is None or s > mejor[0]):
                mejor = (s, d)
        if mejor:
            return _ok(nuc, f"{_may(mejor[1]['disp'])}. Lo he aprendido de lo que leí o me explicaste.")
    # tipos
    m = re.match(r"^(?:que|cuales son los|cuantos) (?:tipos|clases|especies) de ([a-zñ]+)(?: hay| existen)?(?: en .+)?$", n)
    if m and ex["tipos"].get(sa(_sing(m.group(1)))):
        its = ex["tipos"][sa(_sing(m.group(1)))]
        return _ok(nuc, f"Según lo que he aprendido, hay {len(its)}: {', '.join(its[:-1])} y {its[-1]}.")
    m = re.match(r"^(?:(?:el|la|los|las|un|una) )?([a-zñ]+) (?:es|son) (?:un|una|unos|unas) ([a-zñ]+)$", n)
    if m:
        x, c = sa(_sing(m.group(1))), sa(_sing(m.group(2)))
        for cls, its in ex["tipos"].items():
            if any(sa(_sing(i.lower())) == x for i in its):
                if cls == c:
                    return _ok(nuc, f"Sí: según lo que he aprendido, {_el(x)} es un tipo de {cls}.")
                anc = K.ancestros(K._kb_clase(cls) or cls)
                if c in anc:
                    return _ok(nuc, f"Sí. Lo deduzco porque {_el(x)} es un tipo de {cls} y {_un(cls)} es {_un(c)}.")
    # superlativos
    m = re.match(r"^(?:cual|que) es (?:el|la) ([a-zñ]+) (mas|menos) ([a-zñ]+)(?: (de(?:l)? .+|que existe|que hay))?$", n) or re.match(r"^que ([a-zñ]+) es (?:el|la) (mas|menos) ([a-zñ]+)(?: (de(?:l)? .+|que existe|que hay))?$", n)
    if m:
        s = _superl_de(ex, m.group(1), m.group(3), "más" if m.group(2) == "mas" else "menos", m.group(4) or "")
        if s:
            return _ok(nuc, f"{s['ent']}: según lo que he aprendido, es {_el(s['disp'])}.")
    # el único
    for u in ex["unico"]:
        vq = claves(u["vp"])
        if vq and vq <= claves(n):
            m = re.match(r"^(?:(?:el|la|los|las|un|una) )?([a-zñ ]+?) (?:puede[n]? |sabe[n]? )?", n)
            ent = sa(_cab(u["ent"])[1].lower())
            fem_u = M.genero_sust(sa(ent.split()[0])) == "f" if ent else False
            if re.match(r"^(?:quien|que [a-zñ]+|cual)\b", n):
                if u.get("ord") and not sa(u["ord"]).startswith("unic"):
                    return _ok(nuc, f"{u['ent']}: según lo que he aprendido, fue {'la' if sa(u['ord']).endswith('a') else 'el'} {u['ord']}{' ' + u['cls'] if u['cls'] else ''} que {u['vp']}.")
                return _ok(nuc, f"{u['ent']}: según lo que he aprendido, es {'la única' if fem_u else 'el único'} que {u['vp']}.")
            if u.get("ord") and not sa(u["ord"]).startswith("unic"):
                continue
            if m and ent not in n and not re.match(r"^(?:por que|como|cuando|donde)\b", n):
                return _ok(nuc, f"No: según lo que he aprendido, {_min(u['ent']) if not _propio(u['ent']) else u['ent']} es {'la única' if M.genero_sust(sa(ent.split()[0])) == 'f' else 'el único'} que {u['vp']}.")
    # parciales
    m = re.match(r"^(todos |todas )?(?:los |las )?([a-zñ]+) (.+)$", n)
    if m:
        for p in ex["parc"]:
            if p["cls"] == sa(_sing(m.group(2))) and (claves(m.group(3)) & (claves(p["a"]) | claves(p["b"]))):
                fem = M.genero_sust(p["cls"]) == "f"
                if p.get("mayoria"):
                    resto = f"la mayoría de l{'a' if fem else 'o'}s {p['disp']} {p['a']}" + (f", pero algun{'a' if fem else 'o'}s {p['b']}" if p["b"] else "")
                    return _ok(nuc, ("No todos: " if m.group(1) else "En general sí: ") + resto + ", según lo que he aprendido.")
                resto = f"algun{'a' if fem else 'o'}s {p['disp']} {p['a']}" + (f" y otr{'a' if fem else 'o'}s {p['b']}" if p["b"] else "")
                return _ok(nuc, ("No todos: " if m.group(1) else "Depende: ") + resto + ", según lo que he aprendido.")
    m = re.match(r"^(.*?)\b(?:la mayoria|la mayor parte|casi todos|casi todas) de (?:los|las) ([a-zñ]+)(.*)$", n)
    if m:
        for p in ex["parc"]:
            if p.get("mayoria") and p["cls"] == sa(_sing(m.group(2))):
                fem = M.genero_sust(p["cls"]) == "f"
                return _ok(nuc, f"La mayoría de l{'a' if fem else 'o'}s {p['disp']} {p['a']}" + (f", pero algun{'a' if fem else 'o'}s {p['b']}" if p["b"] else "") + ". Lo he aprendido de lo que leí o me explicaste.")
    # reglas: ¿qué pasa cuando/si…?, ¿qué hace X cuando…?, ¿cuándo…?, ¿por qué…?
    m = re.match(r"^por que (.+)$", n)
    if m:
        q = claves(m.group(1))
        mejor = None
        for r in ex["reglas"]:
            if r["tipo"] != "causa":
                continue
            cc = claves(r["cons"])
            s = _solapa(q, cc)
            if not s and q and len(q & cc) >= 2 and len(q & cc) >= round(0.6 * len(q)):
                s = 0.5                                  # la consecuencia dice más cosas, pero cubre lo que se pregunta
            if not s and q and len(q & cc) >= 2 and len(q & cc) >= len(q) - 1 and len(q) >= 3:
                s = 0.4
            if s and (mejor is None or s > mejor[0]):
                mejor = (s, r)
        if mejor:
            return _ok(nuc, f"Porque {_min(mejor[1]['cond']) if not _propio(mejor[1]['cond'].split()[0]) else mejor[1]['cond']}. Lo he aprendido de lo que leí o me explicaste.")
    m = re.match(r"^(?:que (?:pasa|ocurre|sucede|hace[n]?|le pasa|les pasa)|en que se conviert[e]n?|como se llama)\b(.*?)\b(cuando|si|despues de|antes de|al) (.+)$", n)
    if m:
        q = claves(m.group(3))
        qx = claves(m.group(1))
        mejor = None
        for r in ex["reglas"]:
            if r["tipo"] != "cond":
                continue
            cc = claves(r["cond"])
            s = _solapa(q, cc) or _solapa(q | qx, cc | claves(r.get("tema", ""))) or _solapa(q, cc | claves(r.get("tema", "")))
            if s and (mejor is None or s > mejor[0]):
                mejor = (s, r)
        if mejor:
            r = mejor[1]
            return _ok(nuc, f"Según lo que he aprendido: {r['con']} {r['cond']}, {r['cons']}.")
    m = re.match(r"^cuando (.+)$", n)
    if m:
        q = claves(m.group(1))
        mejor = None
        for r in ex["reglas"]:
            if r["tipo"] != "cond":
                continue
            s = _solapa(q, claves(r["cons"])) or _solapa(q, claves(r["cons"]) | claves(r.get("tema", "")))
            if s and (mejor is None or s > mejor[0]):
                mejor = (s, r)
        if mejor:
            r = mejor[1]
            return _ok(nuc, f"{_may(r['con'])} {r['cond']}. Lo he aprendido de lo que leí o me explicaste.")
    # subgrupos: «¿los volcanes extinguidos entran en erupción?»
    for r in reversed(ex["restr"]):
        qs = claves(r["sn"])
        if qs and qs <= claves(n):
            resto_q = claves(n) - qs
            cr = claves(r["resto"])
            if resto_q and _solapa(resto_q, cr, 0.5):
                si_no = not re.match(r"^(?:que|quien|como|cuando|donde|cual|cuant|por que|para que|en que|de que)\b", n)
                neg = re.search(r"\b(?:no|nunca|jamas)\b", sa(r["resto"].lower()))
                frase = f"{_min(r['sn'])} {r['resto']}"
                return _ok(nuc, (("No: " if neg else "Sí: ") if si_no else "") + (frase if si_no else _may(frase)) + ". Lo he aprendido de lo que leí o me explicaste.")
    return None


# ------------------------------------------------------------------ usar lo aprendido: «dime un N», «dime los tipos de N», «descríbeme X»
_NUMS = {"un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "algun": 1, "alguna": 1, "algunos": 3, "algunas": 3, "varios": 3, "varias": 3, "los": 9, "las": 9, "unos": 3, "unas": 3}
_PIDE_LISTA = re.compile(r"^(?:dime|dame|nombra|nombrame|enumera|cita|citame|sabes|conoces)\s+(?:(un|una|uno|dos|tres|cuatro|cinco|seis|algun|alguna|algunos|algunas|varios|varias|los|las|unos|unas)\s+)?"
                         r"(?:(?:tipos?|clases?|ejemplos?|nombres?)\s+de\s+)?([a-zñ]+)(?:\s+([a-zñ]+))?(?:\s+(?:de|del)\s+[a-zñ ]+|\s+que\s+(?:conozcas|sepas|hayas aprendido))?$")


def _miembros(nuc, cls, todos=False, subclases=False):
    """Lo aprendido que ES un `cls`: por tipos, por «X es un cls» o por superlativos."""
    ex = expo(nuc)
    out = []
    for it in ex["tipos"].get(cls, []):
        out.append(it)
    for s in ex["superl"]:
        if s["cls"] == cls and s["ent"] not in out:
            out.append(s["ent"])
    for d in ex["defs"]:
        cab_d = sa(_sing((re.sub(r"^(?:un|una|el|la|unos|unas)\s+", "", d["d"]).split() or [""])[0]))
        if cab_d == cls and d["disp"] not in out and sa(_sing(d["disp"].lower())) != cls:
            out.append(d["disp"])
    for f in nuc.F:
        if f.get("v") == "ser" and f.get("vig", True) and not f.get("neg") and f.get("s") and (todos or f.get("leido") or f.get("expo")) \
                and (cls in [sa(_sing(x)) for x in (f.get("isa") or []) + (f.get("attr") or [])]):
            if f["s"] in ("U", "L"):
                continue
            d = nuc.disp(f["s"])
            d = re.sub(r"^(?:el|la|los|las|un|una)\s+(?=[a-záéíóúñü])", "", d) if f["s"].startswith("K:") else d
            try:
                from . import compuestos as _C2
                tb = _C2.tabla(nuc)
                kd = sa(d.lower())
                d = tb[kd]["s"] if kd in tb else (tb[kd[:-1]]["s"] if kd[:-1] in tb else (tb[kd[:-2]]["s"] if kd[:-2] in tb else (_sing(d) if f["s"].startswith("K:") else d)))
            except Exception:                            # noqa
                pass
            if f.get("enlace") and not subclases:
                continue
            if d and d not in out and sa(_sing(d.lower())) != cls and not any(sa(d.lower()) in sa(o.lower()).split() for o in out):
                out.append(d)
    for s in ex["superl"]:
        d = s["ent"]
        if s["cls"] == cls and d not in out and re.sub(r"^(?:El|La)\s+", "", d) not in out:
            out.append(d)
    return out


def pide(nuc, texto):
    """Peticiones que se atienden con lo aprendido. None si no hay nada aprendido que sirva (seguirá el camino de siempre)."""
    if "?" in texto and not re.match(r"^\W*(?:sabes|conoces)\b", sa(texto.lower())):
        return None
    n = sa(texto.lower()).strip(" ¿?¡!.")
    n = re.sub(r",?\s*por favor$", "", n)
    m = _PIDE_LISTA.match(n)
    if m:
        cls = sa(_sing(m.group(2)))
        its = _miembros(nuc, cls, subclases=bool(re.search(r"\b(?:tipos?|clases?) de\b", n)))
        try:
            from . import compuestos as _C
            its = [_C.decodifica(nuc, i) for i in its]
            its = [i[:1].lower() + i[1:] if not any(w[:1].isupper() for w in i.split()[1:]) and i.split()[0].lower() not in ("el", "la") else i for i in its]
        except Exception:                                # noqa
            pass
        if its and m.group(3):                           # «dime una seta venenosa»: de las aprendidas, las que tienen esa cualidad
            adj = sa(M.masc(_sing(m.group(3))))
            con = []
            for f in nuc.F:
                if f.get("vig", True) and not f.get("neg") and f.get("s") and f.get("v") in ("ser", "estar") and adj in [sa(M.masc(_sing(a))) for a in (f.get("attr") or [])]:
                    d = nuc.disp(f["s"])
                    try:
                        d = _C.decodifica(nuc, d)
                    except Exception:                    # noqa
                        pass
                    d = re.sub(r"^(?:el|la|los|las|un|una)\s+", "", d, flags=re.I)
                    plano = lambda x: " ".join(sa(_sing(w)) for w in re.sub(r"^(?:el|la|los|las|un|una)\s+", "", x.lower()).split())
                    con += [i for i in its if plano(i) == plano(d)]
                    con += [i for i in its if sa(_sing(i.lower())) in (sa(_sing(d.lower())), sa(d.lower())) or sa(re.sub(r"^(?:el|la)\s+", "", i.lower())) == sa(d.lower())]
            its = [i for i in its if i in con]
        if its:
            k = _NUMS.get(m.group(1) or "los", 9)
            its = its[:k]
            lista = its[0] if len(its) == 1 else ", ".join(its[:-1]) + " y " + its[-1]
            return _ok(nuc, f"{_may(lista)}. Lo he aprendido de lo que leí o me explicaste.")
        return None
    m = re.match(r"^(?:describeme|describe|hablame de|que sabes de|que has aprendido (?:de|sobre)|cuentame (?:algo )?(?:de|sobre)|explicame que es|como es)\s+(?:(el|la|los|las|un|una)\s+)?([a-zñ ]+)$", n)
    if m:
        x = m.group(2).strip()
        xs = sa(_sing(x.split()[0])) if len(x.split()) == 1 else x
        ex = expo(nuc)
        partes = []
        d = _def_de(ex, x)
        if d and not d.get("cuando") and not d.get("previa"):
            partes.append(f"{_may(_el(_sing(d['disp'])))} es {d['d']}")
        for f in nuc.F:
            if not f.get("vig", True) or f.get("efecto") or f.get("deducido") or not f.get("s") or not (f.get("leido") or f.get("expo")):
                continue
            ds = sa(nuc.disp(f["s"]).lower())
            if ds == xs or ds.endswith(" " + xs) or re.sub(r"^(?:el|la|los|las|un|una)\s+", "", ds) in (xs, x, xs + "s", xs + "es"):
                fr = nuc.frase(f)
                if fr not in partes and not any(sa(fr) in sa(p) for p in partes):
                    partes.append(_may(fr))
        for s in ex["superl"]:
            if sa(_cab(s["ent"])[1].lower()) in (xs, x):
                partes.append(f"Es {_el(s['disp'])}")
        for cls, its in ex["tipos"].items():
            if any(sa(_sing(i.lower())) == xs for i in its):
                partes.insert(0, f"{_may(_el(xs))} es un tipo de {cls}")
        for u in ex["unico"]:
            if sa(_cab(u["ent"])[1].lower()) in (xs, x):
                partes.append(f"Es {'la única' if M.genero_sust(xs) == 'f' else 'el único'} que {u['vp']}")
        for r in ex["reglas"]:
            if r["tipo"] == "causa" and xs in claves(r["cons"]) and len(partes) < 5:
                partes.append(f"{_may(r['cons'])} porque {r['cond']}")
        if partes:
            return _ok(nuc, ". ".join(partes[:5]) + ". Lo he aprendido de lo que leí o me explicaste.")
    return None


def peticion_sin_atender(texto, nuc=None):
    """«Dime un N…» que nadie ha sabido atender: es una petición, nunca un hecho que apuntar."""
    n = sa((texto or "").lower()).strip(" ¿?¡!.")
    m = _PIDE_LISTA.match(n)
    if m and re.match(r"^(?:dime|dame|nombra|nombrame)\b", n) and not re.search(r"\b(?:ejemplos?|nombres?) de\b", n) and m.group(1) and m.group(2) not in ("otro", "otra", "mas", "algo", "eso", "esto", "todo","cosa", "cosas", "algo", "chiste", "poema", "cuento", "secreto", "adivinanza", "numero", "nombre", "sinonimo", "palabra", "frase",
                                                                                           "idea", "ideas", "ejemplo", "rima", "titulo", "dato", "color", "razon", "motivo", "favor", "minuto", "segundo", "momento", "consejo"):
        its = _miembros(nuc, sa(_sing(m.group(2))), todos=True) if nuc is not None and not m.group(3) else []
        if its:
            its = its[:_NUMS.get(m.group(1), 1)]
            return _ok(nuc, (_may(_un(its[0])) + ", por ejemplo.") if len(its) == 1 else _may(", ".join(its[:-1]) + " y " + its[-1]) + ".")
        return {"respuesta": f"No conozco ningún ejemplo de «{m.group(2)}{' ' + m.group(3) if m.group(3) else ''}» todavía: si me cuentas alguno, lo recordaré.", "estado": "abst", "consultar": False, "tipo": "resp"}
    return None


# ------------------------------------------------------------------ la charla que explica: frase a frase, igual que al leer
_PERSONAL = re.compile(r"\b(?:yo|me|mi|mis|mio|mia|tu|tus|te|ti|tuyo|nos|nuestr[oa]s?|conmigo|contigo|usted|vosotros|os)\b")


_NO_1S = {"como", "para", "sobre", "entre", "bajo", "una", "uno", "vino", "traje", "nada", "cara", "rio", "cocina", "casa", "camino", "cuenta", "compra", "trabajo", "juego", "paso", "cambio", "pago", "uso",
          "canto", "baile", "sueño", "sueno", "paseo", "desayuno", "almuerzo", "regalo", "dibujo", "estudio", "peso", "abrigo", "saludo", "recibo", "techo", "seco", "limpio", "lleno", "solo", "fino", "vuelo",
          "cuento", "cierro", "tiro", "salto", "grito", "corte", "resto", "fin", "son", "sal", "ven", "ves", "das", "seas", "eras", "mides", "cabes", "cabe", "veo"}


def _impersonal(t):
    n = sa(t.lower())
    if _PERSONAL.search(n):
        return False
    for w in re.findall(r"[a-záéíóúñü]+", t.lower())[:8]:
        try:
            an = M.analizar(w) or []
        except Exception:                                # noqa
            an = []
        if an and all(len(a) > 2 and a[2] in ("1s", "2s", "1p", "2p") for a in an) and not K._kb_clase(sa(_sing(w))) and len(w) >= 3 and sa(w) not in _NO_1S:
            return False
    return True


def charla(nuc, texto):
    """Una frase de la charla que EXPLICA algo general. Devuelve la respuesta, o None si es charla normal."""
    t = texto.strip()
    if not t or "?" in t or len(t.split()) < 3 or len(t) > 240 or not _impersonal(t) or re.match(r"^\W*(?:dime|dame|cuenta|explica|describe|pon|haz|escribe|apunta|recuerda|hola|gracias|vale|no,|si,|sí,|perd[oó]n)", t, re.I):
        return None
    T = _may(t.rstrip(".! "))
    hilo = getattr(nuc, "_hilo", None)
    if hilo is None or nuc.turno - getattr(nuc, "_hilo_turno", -9) > 3:
        hilo = nuc._hilo = Hilo()
    sn, _ = sujeto(T)
    w0 = T.split()[0]
    generica = sn is not None and re.fullmatch(_DET, sa(sn.split()[0].lower())) is not None
    marca = re.match(r"^(?:Algun[oa]s|Cuando|Si|Siempre que|A los|A las|Después de|Antes de|Al [a-záéíóúñü]+r(?:se)?,|Hay [a-záéíóúñü]+ (?:tipos|clases)|En (?:un|una|el|la|los|las) [a-záéíóúñü]+ hay)\b", T) is not None
    sin_suj = sn is None and (_fin3(w0) or w0 in ("Su", "Sus", "Es", "Son")) and getattr(nuc, "_hilo_mio", False) and nuc.turno - getattr(nuc, "_hilo_turno", -9) <= 2 and hilo.ult is not None
    define = sn is not None and re.search(r"\b(?:es|son|fue|era|fueron)\s+(?:el|la|los|las)\s+(?:únic[oa]s?|primer[oa]?s?|últim[oa]s?|[a-záéíóúñü]+\s+(?:más|menos)\s+[a-záéíóúñü]+)\b", T) is not None
    por_eso = re.match(r"^Por (?:eso|ello|esa razón|ese motivo)\b", T) is not None and bool(hilo.previa) and nuc.turno - getattr(nuc, "_hilo_turno", -9) <= 2
    if not (generica or marca or sin_suj or define or por_eso):
        if sn is not None and not _PERSONAL.search(sa(T.lower())):
            hilo.pon(sn)                                 # se anota de qué se habla, aunque la frase la lea el núcleo
            hilo.previa = T
            nuc._hilo_turno = nuc.turno
        nuc._hilo_mio = False
        return None
    import copy
    ex = expo(nuc)
    T1, _ = resuelve(T, hilo)
    if T1 is None:
        return None
    ex2 = copy.deepcopy(ex)
    ensayo = desdobla(T1, copy.copy(hilo), ex2, reg=True)
    talla = lambda d: sum(len(v) for v in d.values() if isinstance(v, (list, dict)))
    clase3 = bool(sn) and len(sn.split()) == 3 and not _propio(sn) and (sa(sn.split()[0].lower()) in ("un", "una", "los", "las", "unos", "unas")
                                                                         or re.match(r"^(?:es|son)\s+(?:un|una|el|la)\b", sujeto(T1)[1]) is not None)
    if sn and len(sn.split()) == 3 and not clase3:
        nuc._hilo_mio = False
        return None                                      # «el coche rojo es de Ana»: una cosa concreta; es asunto del núcleo
    if len(ensayo) == 1 and talla(ex2) == talla(ex) and not sin_suj and not clase3:
        hilo.previa = T1
        hilo.pon(sn)                                     # frase sencilla: la lee el núcleo como siempre; solo se anota de qué se habla
        nuc._hilo_turno, nuc._hilo_mio = nuc.turno, False
        nuc._hilo_n = len(nuc.F)
        return None
    n0 = len(nuc.F)
    nf, nx, f1 = procesa(nuc, T, hilo)
    nuc._hilo_turno, nuc._hilo_mio = nuc.turno, True
    for f in nuc.F[n0:]:
        f["expo"] = True
    leidos = nuc.usuario.setdefault("leido", [])
    if not leidos or not leidos[-1].get("charla"):
        leidos.append({"turno": nuc.turno, "frases": [], "temas": {}, "charla": True})
        del leidos[:-12]
    leidos[-1]["frases"].append(T + ".")
    del leidos[-1]["frases"][:-80]
    if sn is None and hilo.ult:
        leidos[-1]["temas"][T + "."] = hilo.ult
    nuc.pend = None
    if nf and len(nuc.F) == n0:
        return {"respuesta": "Entendido, me lo apunto.", "estado": "ok", "consultar": False, "tipo": "ack"}
    if nf:
        fr = []
        for f in nuc.F[n0:]:
            if f.get("efecto") or f.get("deducido"):
                continue
            x = nuc.frase(f)
            if x not in fr:
                fr.append(x)
        return {"respuesta": "Entendido: " + "; ".join(fr[:4]) + ".", "estado": "ok", "consultar": False, "tipo": "ack"}
    if nx:
        return {"respuesta": "Entendido, me lo apunto.", "estado": "ok", "consultar": False, "tipo": "ack"}
    return {"respuesta": f"No lo he entendido del todo, pero me lo apunto tal como lo dices: «{T}».", "estado": "ok", "consultar": False, "tipo": "ack"}


# ------------------------------------------------------------------ lo que me dicen frente a lo que leí
def foto_leido(nuc):
    return [f for f in nuc.F if (f.get("leido") or f.get("expo")) and f.get("vig", True)]


def contraste(nuc, texto, r, foto, n_af):
    """Si lo que se acaba de decir tumba o choca con algo leído, se dice. Lo leído no se borra sin avisar."""
    if not foto or not isinstance(r, dict) or r.get("estado") != "ok" or "?" in texto:
        return r
    perdidos = [f for f in foto if not f.get("vig", True)]
    if perdidos:
        for f in perdidos:
            f["vig"] = True
            try:
                nuc._espejo(f)
            except Exception:                            # noqa
                pass
        nuevos = [g for g in nuc.F[n_af:] if g.get("vig", True)]
        for g in nuevos:
            g["vig"] = False
            try:
                nuc._espejo(g, quitar=True)
            except Exception:                            # noqa
                pass
        nuc._contra = {"texto": texto, "viejos": perdidos, "turno": nuc.turno}
        return dict(r, respuesta=f"Eso no coincide con lo que aprendí: {nuc.frase(perdidos[0])}. Me quedo con lo aprendido; si estaba mal, dime «corrígelo» y lo cambio.", tipo="ack")
    for g in nuc.F[n_af:]:
        if g.get("neg") or not g.get("s") or g.get("efecto"):
            continue
        for f in foto:
            if f is g or f.get("s") != g.get("s") or f.get("v") != g.get("v") or f.get("neg"):
                continue
            tf, tg = sa(str(f.get("cuando") or "").lower()), sa(str(g.get("cuando") or "").lower())
            af, ag = [sa(M.masc(_sing(a))) for a in f.get("attr") or []], [sa(M.masc(_sing(a))) for a in g.get("attr") or []]
            misma_familia = any(a != b_ and (set(K.ancestros(a)) & set(K.ancestros(b_))) for a in af for b_ in ag) and not (set(af) & set(ag))
            if (tf and tg and tf != tg and not (claves(tf) & claves(tg))) or (f.get("v") in ("ser", "estar") and misma_familia):
                return dict(r, respuesta=(r.get("respuesta") or "").rstrip() + f" Pero ojo: yo había aprendido que {nuc.frase(f)}. Guardo las dos cosas; si una está mal, dímelo.")
            cf, cg = {c[0]: sa((c[2] or "").lower()) for c in f.get("comps") or []}, {c[0]: sa((c[2] or "").lower()) for c in g.get("comps") or []}
            choque = [p for p in cf if p in cg and cf[p] and cg[p] and cf[p] != cg[p] and not (claves(cf[p]) & claves(cg[p]))]
            if choque and not (f.get("obj") or g.get("obj")):
                return dict(r, respuesta=(r.get("respuesta") or "").rstrip() + f" Pero ojo: yo había aprendido que {nuc.frase(f)}. Guardo las dos cosas; si una está mal, dímelo.")
    return r


def corrige_contra(nuc, texto):
    c = getattr(nuc, "_contra", None)
    if not c or nuc.turno - c["turno"] > 2:
        return None
    if not re.match(r"^\W*(?:corr[ií]gelo|c[aá]mbialo|s[ií],? (?:corr[ií]gelo|c[aá]mbialo|estaba mal)|(?:el texto|eso|lo que le[ií]ste) estaba (?:mal|equivocado)|hazme caso|tengo raz[oó]n yo)\W*$", texto.strip(), re.I):
        return None
    for f in c["viejos"]:
        f["vig"] = False
        try:
            nuc._espejo(f, quitar=True)
        except Exception:                                # noqa
            pass
    nuc._contra = None
    r = nuc._procesar_charla(c["texto"])
    if isinstance(r, dict) and r.get("estado") == "ok":
        return dict(r, respuesta="De acuerdo, lo cambio. " + (r.get("respuesta") or ""))
    return r


# ------------------------------------------------------------------ lo que vale para la clase vale para quien es de esa clase
def por_clase(nuc, texto):
    """«Mi tío es apicultor» + «los apicultores cuidan las colmenas» -> «¿mi tío cuida colmenas?»: sí, por ser apicultor."""
    if "?" not in texto or re.match(r"^\W*(?:qu[eé]|qui[eé]n|c[oó]mo|cu[aá]ndo|d[oó]nde|cu[aá]l|cu[aá]nt|por qu[eé]|para qu[eé])\b", texto.strip(), re.I):
        return None
    from .nucleo import cambia_persona
    q = texto.strip().strip("¿?").strip()
    for e, d in list(nuc.E.items()):
        if e in ("L",) or e.startswith("K:"):
            continue
        nombres = [x for x in (d.get("nombre"), cambia_persona(nuc.disp(e)) if e != "U" else None) if x]
        hit = next((x for x in nombres if re.search(r"\b" + re.escape(x) + r"\b", q, re.I)), None)
        if not hit:
            continue
        clases = []
        for f in nuc.F:
            if f.get("v") == "ser" and f.get("vig", True) and not f.get("neg") and f.get("s") and nuc.can(f["s"]) == e:
                clases += [c for c in (f.get("isa") or []) + (f.get("attr") or []) if c not in clases]
        for c in clases:
            c0 = sa(_sing(c))
            if not any(g.get("s") == "K:" + c0 and g.get("v") != "ser" and g.get("vig", True) for g in nuc.F):
                c_a = c0[:-1] + "a" if c0.endswith("o") else c0
                if c_a != c0 and any(g.get("s") == "K:" + c_a and g.get("v") != "ser" and g.get("vig", True) for g in nuc.F):
                    c0 = c_a                             # «astronauta», «barista»: nombres en -a que valen para los dos géneros
                else:
                    continue
            pl = M.plural(c0) if hasattr(M, "plural") else c0 + "s"
            q2 = re.sub(r"\b" + re.escape(hit) + r"\b", _el(pl, pl=True), q, count=1, flags=re.I)
            ws = q2.split()
            for i, w in enumerate(ws):                   # el verbo, en plural
                an = [a for a in (M.analizar(w.lower()) or []) if len(a) > 2 and a[2] == "3s" and a[1] in ("pres", "pret", "imp", "fut")]
                if an and w.lower() not in ("la", "las", "los", "el", pl) and not K._kb_clase(sa(_sing(w.lower()))):
                    ws[i] = M.conjugar(an[0][0], an[0][1], "3p") or w
                    break
            r2 = None
            variantes = [list(ws)]
            for i, w in enumerate(ws):
                an2 = [a for a in (M.analizar(w.lower()) or []) if len(a) > 2 and a[2] == "3p" and a[1] in ("pres", "pret", "imp", "fut")]
                if an2 and not K._kb_clase(sa(_sing(w.lower()))):
                    for t_ in ("pres", "imp", "pret"):
                        if t_ != an2[0][1]:
                            v2 = list(ws); v2[i] = M.conjugar(an2[0][0], t_, "3p") or w
                            variantes.append(v2)
                    break
            for var in variantes:
                try:
                    r2 = nuc._procesar_charla("¿" + _may(" ".join(var)) + "?")
                except Exception:                        # noqa
                    r2 = None
                if isinstance(r2, dict) and r2.get("estado") == "ok" and re.match(r"^(?:s[ií]|no)\b", sa((r2.get("respuesta") or "").lower())):
                    break
            if not (isinstance(r2, dict) and r2.get("estado") == "ok" and re.match(r"^(?:s[ií]|no)\b", sa((r2.get("respuesta") or "").lower()))):
                try:
                    from . import lectura as _L
                    c_ = _L.cita(nuc, "¿" + _may(" ".join(variantes[0])) + "?")
                except Exception:                        # noqa
                    c_ = None
                if c_ and re.match(r"^(?:s[ií]|no)\b", sa(c_.lower())):
                    r2 = {"respuesta": c_, "estado": "ok"}
            if isinstance(r2, dict) and r2.get("estado") == "ok" and re.match(r"^(?:s[ií]|no)\b", sa((r2.get("respuesta") or "").lower())):
                resp = r2["respuesta"].rstrip(". ")
                quien = nuc.disp(e) if e != "U" else "tú"
                return {"respuesta": f"{resp}. Lo deduzco porque {quien} {'eres' if e == 'U' else 'es'} {c} y eso vale para {_el(pl, pl=True)}.", "estado": "ok", "consultar": False, "tipo": "resp"}
    return None


def _apunta(nuc, T, tema=None):
    leidos = nuc.usuario.setdefault("leido", [])
    if not leidos or not leidos[-1].get("charla"):
        leidos.append({"turno": nuc.turno, "frases": [], "temas": {}, "charla": True})
        del leidos[:-12]
    if T not in leidos[-1]["frases"]:
        leidos[-1]["frases"].append(T)
        del leidos[-1]["frases"][:-80]
    if tema:
        leidos[-1]["temas"][T] = tema


def nota(nuc, texto):
    """Una explicación general que nadie ha entendido: se guarda tal cual (para poder citarla) y se dice con honestidad."""
    t = (texto or "").strip()
    if not t or "?" in t or len(t.split()) < 5 or len(t) > 240 or not _impersonal(t):
        return None
    if re.match(r"^\W*(?:dime|dame|cuenta|cu[eé]ntame|explica|describe|pon|haz|escribe|apunta|recuerda|hola|gracias|vale|venga|bueno|no,|si,|sí,|perd[oó]n|adi[oó]s|hasta|jaja)", t, re.I):
        return None
    if not re.search(r"\b(?:el|la|los|las|un|una|unos|unas|cada)\s+[a-záéíóúñü]+", t.lower()) or re.search(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+\s+(?:y|e)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+\b", t):
        return None
    if re.search(r"(?<=[a-záéíóúñ,] )[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+", t):
        return None                                      # con nombres propios es charla sobre alguien, no una explicación general
    T = _may(t.rstrip(".! ")) + "."
    hilo = getattr(nuc, "_hilo", None)
    _apunta(nuc, T, hilo.ult if (hilo and sujeto(T)[0] is None and nuc.turno - getattr(nuc, "_hilo_turno", -9) <= 2) else None)
    nuc.turno += 1
    return {"respuesta": f"No lo he entendido del todo, pero me lo apunto tal como lo dices: «{T.rstrip('.')}».", "estado": "ok", "consultar": False, "tipo": "ack"}


def sin_respuesta(nuc, texto):
    """Pregunta sobre algo de lo leído o explicado que nadie sabe contestar: se dice, en vez de dejar que conteste el diccionario."""
    leidos = nuc.usuario.get("leido") or []
    if not leidos or "?" not in texto:
        return None
    q = claves(texto)
    if not q:
        return None
    for t in reversed(leidos[-3:]):
        voc = set()
        for g in t.get("frases", []):
            voc |= claves(g)
        if len(q & voc) >= max(1, (len(q) + 1) // 2):
            return {"respuesta": "No lo sé: eso no lo he leído ni me lo has explicado.", "estado": "abst", "consultar": False, "tipo": "resp"}
    return None


def apunta_no_entendida(nuc, texto, r):
    """Una explicación que el núcleo dice no haber entendido queda guardada tal cual, para poder citarla."""
    if not isinstance(r, dict) or "?" in (texto or "") or not sa((r.get("respuesta") or "").lower()).startswith("no lo he entendido del todo"):
        return
    t = (texto or "").strip()
    if len(t.split()) < 4 or len(t) > 240 or not _impersonal(t):
        return
    hilo = getattr(nuc, "_hilo", None)
    T = _may(t.rstrip(".! ")) + "."
    _apunta(nuc, T, hilo.ult if (hilo and sujeto(T)[0] is None and hilo.ult and nuc.turno - getattr(nuc, "_hilo_turno", -9) <= 3) else None)


def _familia(a, b):
    """¿Son dos valores distintos de lo mismo? Contrarios («día»/«noche») o de la misma familia de cualidades (dos colores)."""
    if a == b:
        return False
    ant = K.kb().get("ant") or {}
    if b in [sa(x) for x in ant.get(a, [])] or a in [sa(x) for x in ant.get(b, [])]:
        return True
    pa, pb = set(K.ancestros(a)), set(K.ancestros(b))
    return bool(pa & pb & {"color", "forma", "sabor", "estacion", "mes", "dia de la semana", "punto cardinal"})


def contraste_texto(nuc, texto, r):
    """Lo que se acaba de decir frente a las FRASES leídas (aunque no dejaran un hecho): misma cosa, mismo verbo y un valor contrario."""
    if not isinstance(r, dict) or r.get("estado") != "ok" or "?" in texto or "coincide con lo que aprendí" in (r.get("respuesta") or "") or "Pero ojo" in (r.get("respuesta") or ""):
        return r
    leidos = nuc.usuario.get("leido") or []
    if not leidos or not _impersonal(texto):
        return r
    try:
        from . import compuestos as C
        t = C.decodifica(nuc, texto)
    except Exception:                                    # noqa
        t = texto
    T = _may(t.strip().rstrip(".! "))
    sn, resto = sujeto(T)
    if not sn:
        return r
    cs, cr = claves(sn), claves(resto)
    neg_s = bool(re.search(r"\b(?:no|nunca|jamas|tampoco|ningun[oa]?)\b", sa(resto.lower())))
    lem = lambda x: {a[0] for w in re.findall(r"[a-záéíóúñü]+", x.lower()) for a in (M.analizar(w) or []) if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut")}
    vs = lem(resto.split(" y ")[0])
    for txt in reversed(leidos[-4:]):
        temas = txt.get("temas") or {}
        for L in txt.get("frases", []):
            if sa(L.rstrip(".").lower()) == sa(T.lower()):
                continue
            Lc = L.rstrip(".")
            ctx = claves(Lc) | (claves(temas[L]) if L in temas else set())
            sujL = claves(sujeto(Lc)[0] or temas.get(L, "") or "")
            if not cs or not (cs <= ctx) or not (cs & sujL or L in temas):
                continue
            if not (vs & lem(Lc)):
                continue
            neg_l = bool(re.search(r"\b(?:no|nunca|jamas|tampoco|ningun[oa]?)\b", sa(Lc.lower())))
            cl = claves(Lc) - cs
            choque = any(_familia(a, b) for a in cr for b in cl if a not in cl)
            if not choque and neg_s != neg_l and cr and len(cr & cl) >= max(1, round(0.7 * len(cr))):
                choque = True
            if choque:
                return dict(r, respuesta=(r.get("respuesta") or "").rstrip() + f" Pero ojo: en lo que leí ponía «{Lc}». Guardo las dos cosas; si una está mal, dímelo.")
    return r
