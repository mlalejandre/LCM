"""LCM 2.5 · habla coloquial: muletillas, erratas frecuentes, preguntas sin signos, y la memoria literal de lo que
no se ha entendido (notas), para poder citarlo en vez de inventar o quedarse en blanco."""
from __future__ import annotations

import re

from . import morfo as M
from .morfo import sa

_MULET_LIBRE = (r"pues nada|pues eso|pues mira|pues|es que|el caso es que|la verdad es que|lo cierto es que|por cierto|total que|resulta que|que sepas que|y nada|y bueno|"
                r"cambiando de tema|hablando de otra cosa|por otro lado|a todo esto|ya que estamos|oye una cosa")
_MULET_COMA = (r"bueno|vale|oye|mira|a ver|la verdad|total|en fin|entonces|hombre|venga|ah|eh|uf|jo|ay|anda|ademas|encima|te cuento|fijate|sabes que|otra cosa|una pregunta|una cosa|nada|ya|"
               r"ya me acuerdo|ahora me acuerdo|ahora caigo|ya caigo|me acabo de acordar|ahora que lo pienso|pensandolo bien|pensándolo bien|al final|por cierto")
_INI = re.compile(rf"^\s*(?:(?:{_MULET_LIBRE})\s*[,:;.!…]*\s+|(?:{_MULET_COMA})\s*[,:;.!…]+\s*)(?=\S)", re.I)
_FIN = re.compile(r"\s*,\s*(?:por cierto|la verdad|eh|sabes|vamos|en fin|creo yo|digo yo|ya sabes|ya ves|no te creas|¿?no\??|¿?verdad\??|¿?vale\??|¿?sabes\??)\s*([.!?]*)$", re.I)
_ERRATAS = {"yamo": "llamo", "yama": "llama", "yaman": "llaman", "bibo": "vivo", "bibe": "vive", "aki": "aquí", "k": "que", "q": "que", "tb": "también", "xq": "porque", "pq": "porque",
            "tngo": "tengo", "kiero": "quiero", "ke": "que", "aver": "a ver", "haver": "a ver", "ola": "hola", "mui": "muy", "boy": "voy", "ba": "va", "tanbien": "también", "tambien": "también",
            "d": "de", "xa": "para", "pa": "para", "tmb": "también", "dnd": "donde", "cmo": "como", "grax": "gracias", "porfa": "por favor", "finde": "fin de semana",
            "wenas": "buenas", "kien": "quien", "kienes": "quienes", "komo": "como", "kuando": "cuando", "dnde": "donde", "xo": "pero", "tb": "también", "salu2": "saludos",
            "mñn": "mañana", "mñna": "mañana", "xfa": "por favor", "bn": "bien", "muxo": "mucho", "muxa": "mucha", "toy": "estoy", "ns": "no sé", "nse": "no sé",
            "tqm": "te quiero mucho", "pf": "por favor", "xk": "porque", "porq": "porque", "aunq": "aunque", "wapo": "guapo", "wapa": "guapa", "weno": "bueno",
            "wena": "buena", "sip": "sí", "nop": "no", "kiza": "quizá", "medico": "médico",
            "tambn": "también", "dsp": "después", "ad+": "además", "hno": "hermano", "hna": "hermana", 
            "porfi": "por favor"}
_SEGURAS = set("""hola ola ya yo ayer hoy hay mayo muy pero bien bueno vale si no ni que de la el los las un una y o a en con por para mi tu su me te se le lo nos os les del al mas menos casi
como cuando donde quien cual cuanto este esta ese esa eso esto aquel ella el ellos ellas nosotros vosotros usted tambien tampoco siempre nunca jamas ahora luego despues antes
entonces aqui alli ahi asi tan tanto poco mucho todo nada algo alguien nadie cada otro otra mismo sobre bajo entre hasta desde hacia sin segun tras vaya baya valla haya
halla calló cayó rayo rallo bello vello basta vasta tubo tuvo cabo cavo sabia savia hierba hierva bota vota casa caza cocer coser abría habría hola echo hecho asta hasta""".split())
_FON = [("k", "qu"), ("k", "c"), ("y", "ll"), ("b", "v"), ("v", "b"), ("z", "c"), ("x", "ch"), ("w", "gu"), ("w", "bu"), ("ll", "y"), ("j", "g"), ("s", "z"), ("c", "z"), ("i", "y")]


def _conocida(w):
    from . import conceptos as _K
    if M.analizar(w) or _K._kb_clase(sa(w)) or sa(w) in _SEGURAS or sa(w) in ("quien", "quienes", "porque", "aunque", "mientras", "todavia", "tambien"):
        return True
    try:
        from .nucleo import PERSONA_CLS, REL_CANON
        x = sa(M.singular(w))
        return x in PERSONA_CLS or x in REL_CANON or (x.endswith("a") and x[:-1] + "o" in PERSONA_CLS)
    except Exception:                                   # noqa
        return False


def _fonetica(w):
    """2.16: una palabra que no existe y suena como otra que sí («komo», «yamo», «bibo», «aser») se lee como la que existe."""
    wl = w.lower()
    if len(wl) < 3 or not wl.isalpha() or w[:1].isupper() and not w.isupper() or sa(wl) in _SEGURAS or _conocida(wl):
        return w
    cands = []
    for a, b in _FON:
        i = wl.find(a)
        while i >= 0:
            cands.append(wl[:i] + b + wl[i + len(a):])
            i = wl.find(a, i + 1)
    if wl[0] in "aeiou":
        cands.append("h" + wl)
        cands += ["h" + wl[:i] + b_ + wl[i + len(a_):] for a_, b_ in (("s", "c"), ("z", "c"), ("b", "v"), ("v", "b")) for i in [wl.find(a_)] if i >= 0]
    if re.search(r"(.)\1", wl):
        cands.append(re.sub(r"(.)\1+", r"\1", wl))
    for c in cands:
        if c != wl and _conocida(c):
            return c
    return w
_WH = ("que", "quien", "quienes", "como", "donde", "adonde", "cuando", "cuanto", "cuanta", "cuantos", "cuantas", "cual", "cuales", "por que", "de que", "a que", "en que", "con quien", "de quien", "a quien", "para que")
_TILDE = {"que": "qué", "quien": "quién", "quienes": "quiénes", "como": "cómo", "donde": "dónde", "adonde": "adónde", "cuando": "cuándo", "cuanto": "cuánto", "cuanta": "cuánta",
          "cuantos": "cuántos", "cuantas": "cuántas", "cual": "cuál", "cuales": "cuáles"}


def _sin_acento_inicial(w):
    return sa(w)


_NO_PASIVA = {"decir", "contar", "preguntar", "pedir", "dar", "ofrecer", "regalar", "mandar", "enviar", "traer", "poner", "quitar", "robar", "comprar", "vender", "prestar", "dejar", "explicar",
              "enseñar", "gustar", "encantar", "hacer", "escribir", "responder", "contestar", "devolver", "subir", "bajar", "cambiar", "arreglar", "cortar", "sacar", "recomendar", "prometer"}


class _Grupos:
    """Vista de un match sin su grupo 2 (el pronombre), para no renumerar el resto."""
    def __init__(self, m):
        self._g = [m.group(0), m.group(1)] + [m.group(i) for i in range(3, (m.lastindex or 0) + 1)]

    def group(self, i):
        return self._g[i] if i < len(self._g) else None


def _pasiva_impersonal(t):
    mneg = re.match(r"^(¿?)(\s*)no\s+((?:me|le|la|lo)\s+(?:han|habían|van a)\s+.+)$", t, re.I)
    if mneg:                                             # «no me han ascendido» -> «no he sido ascendido»
        sin = _pasiva_impersonal_(mneg.group(1) + mneg.group(3)[:1].upper() + mneg.group(3)[1:])
        if sin != mneg.group(1) + mneg.group(3)[:1].upper() + mneg.group(3)[1:]:
            cuerpo = sin.lstrip("¿")
            return mneg.group(1) + "No " + cuerpo[:1].lower() + cuerpo[1:]
        return t
    return _pasiva_impersonal_(t)


def _pasiva_impersonal_(t):
    """2.17: «me han despedido», «me operan mañana», «¿me han ascendido?»: 3.ª plural sin sujeto y la persona como paciente -> pasiva («he sido despedido»)."""
    preg = t.startswith("¿")
    cuerpo = t.strip("¿?").rstrip(".! ")
    m = re.match(r"^((?:ayer|hoy|mañana|esta mañana|esta tarde|esta semana|el [a-záéíóú]+|al final|ya|por fin|es que|y|cu[aá]ndo|d[oó]nde|por qu[eé]|de qu[eé])\s+)?(me|le|la|lo)\s+(?:(han|habían|van a|iban a)\s+)?([a-záéíóúñ]+)\b\s*(.*)$", cuerpo, re.I)
    if not m:
        return t
    yo = m.group(2).lower() == "me"
    m = re.match(r"^(.*)$", "").__class__ and _Grupos(m)
    pre, aux, w, resto = (m.group(1) or ""), (m.group(2) or "").lower(), m.group(3).lower(), m.group(4).strip()
    mo_ = re.match(r"^(el|la|los|las|mi|mis)\s+([a-záéíóúñ]+)((?:\s+(?:de|del|en)\s+[\wáéíóúñ ]+)?)$", resto, re.I)
    if mo_ and yo and (m.group(2) or "").lower() in ("han", "habían") and not preg:
        an_ = M.analizar(m.group(3).lower())
        if an_ and an_[0][0] in ("robar", "quitar", "romper", "rayar", "estropear", "pinchar", "abollar") and any(a_[1] == "part" for a_ in an_):
            pl_ = mo_.group(1).lower() in ("los", "las", "mis")
            fem_ = mo_.group(1).lower() in ("la", "las") or (mo_.group(1).lower() in ("mi", "mis") and M.genero_sust(sa(M.singular(mo_.group(2)))) == "f")
            part_ = M.conjugar(an_[0][0], "part", "")
            part_ = (part_[:-1] + ("a" if fem_ else "o")) + ("s" if pl_ else "")
            return f"{'Mis' if pl_ else 'Mi'} {mo_.group(2)}{mo_.group(3)} {'fueron' if pl_ else 'fue'} {part_}."   # «me han robado el móvil» -> «mi móvil fue robado»
    if resto and not re.match(r"^(?:en|de|del|al|a los|a las|por|con|para|desde|hasta|mañana|hoy|ayer|ya|esta|este|el (?:lunes|martes|miércoles|jueves|viernes|sábado|domingo|mes|año|día)|la semana|pasado|muy|otra vez|dos veces|sin)\b", resto, re.I):
        return t                                        # «me han robado el móvil»: hay un objeto, no es la persona la que lo recibe
    an = M.analizar(w)
    if not an:
        return t
    lema = an[0][0]
    if lema in _NO_PASIVA:
        return t
    if aux in ("han", "habían"):
        if not any(a[1] == "part" for a in an):
            return t
        ser = ("he sido" if aux == "han" else "había sido") if yo else ("ha sido" if aux == "han" else "había sido")
    elif aux in ("van a", "iban a"):
        if not any(a[1] == "inf" for a in an):
            return t
        ser = ("seré" if aux == "van a" else "iba a ser") if yo else ("será" if aux == "van a" else "iba a ser")
    else:
        a3 = [a for a in an if len(a) > 2 and a[2] == "3p" and a[1] in ("pres", "pret", "fut")]
        if not a3 or len({a[0] for a in an}) > 1:
            return t
        ser = {"pres": "seré", "pret": "fui", "fut": "seré"}[a3[0][1]] if yo else {"pres": "será", "pret": "fue", "fut": "será"}[a3[0][1]]
        if not yo:
            return t                                    # «le llaman Paco», «lo venden»: sin auxiliar, en tercera persona es demasiado ambiguo
    part = M.conjugar(lema, "part", "") or ""
    if not part:
        return t
    out = (pre + ser + " " + part + (" " + resto if resto else "")).strip()
    out = out[:1].upper() + out[1:]
    return ("¿" + out + "?") if preg else out + "."


def _normaliza_217(t):
    """2.17: formas de la charla diaria que el núcleo ya entiende dichas de otro modo."""
    if "?" not in t:
        # «apunta que…», «que sepas que…», «te cuento que…»: lo que importa es lo que viene después
        t0_ = t
        t = re.sub(r"^(?:apunta|ap[uú]ntate|anota|recuerda|acu[eé]rdate de|que sepas|te cuento|te comento|para que lo sepas,?|por cierto,?|sabes qu[eé]\W+|te digo|toma nota de|ten en cuenta)\s+que\s+(?=\w)",
                   "", t, flags=re.I)
        if t != t0_ and not any(c.isupper() for c in t0_[:1]):
            pass
        elif t != t0_:
            t = t[:1].upper() + t[1:]
        # «comparto piso con…»: nombre sin artículo tras el verbo
        t = re.sub(r"^(compart(?:o|imos|[ií]a|[ií]amos)|busco|buscamos|alquilo|alquilamos)\s+(piso|casa|habitaci[oó]n|coche|despacho|oficina|cuarto)\b",
                   lambda m_: m_.group(1) + (" una " if m_.group(2).lower().startswith(("casa", "habit", "ofic")) else " un ") + m_.group(2), t, flags=re.I)
        # «me ha tocado la lotería / un premio» = lo he ganado
        t = re.sub(r"^((?:ayer|hoy|esta semana)\s+)?me\s+(?:ha tocado|toc[oó])\s+((?:la|el|un|una)\s+(?:loter[ií]a|premio|sorteo|quiniela|gordo|rifa|viaje)\b.*)$",
                   lambda m_: ((m_.group(1) or "") + "he ganado " + m_.group(2)).capitalize() if not m_.group(1) else m_.group(1).capitalize() + "he ganado " + m_.group(2), t, flags=re.I)
    t = re.sub(r"\b[Ss]emana [Ss]anta\b", "semana santa", t)
    t = re.sub(r"\b(estoy|me siento|me encuentro|me noto)\s+((?:ya|ahora|algo|un poco)\s+)?m[aá]s\s+(tranquil[oa]|animad[oa]|content[oa]|relajad[oa]|calmad[oa]|descansad[oa]|segur[oa])\b", r"\1 \3", t, flags=re.I)
    if "?" not in t or t.startswith("¿"):
        # «me han puesto una multa», «me han hecho un contrato»: 3.ª plural sin sujeto con algo que se recibe -> «he recibido…»
        mi_ = re.match(r"^(¿?)((?:ayer|hoy|esta mañana|esta semana|al final|ya|por fin)\s+)?(no\s+)?me\s+(han|habían)\s+(puesto|hecho|entregado|otorgado|concedido|diagnosticado|recetado|traído|traido|asignado|adjudicado)\s+((?:un|una|unos|unas|el|la|los|las|dos|tres|otro|otra)\s+.+?)([?.!]*)$", t, re.I)
        if mi_:
            aux_ = "he" if mi_.group(4).lower() == "han" else "había"
            cuerpo_ = f"{mi_.group(2) or ''}{mi_.group(3) or ''}{aux_} recibido {mi_.group(6)}"
            t = mi_.group(1) + cuerpo_[:1].upper() + cuerpo_[1:] + ("?" if mi_.group(1) else ".")
        # «me han subido el sueldo», «me han cambiado el turno»: lo que cambia es la cosa
        mc_ = re.match(r"^(¿?)((?:ayer|hoy|esta semana|al final|ya|por fin)\s+)?(no\s+)?me\s+han\s+(subido|bajado|cambiado|aumentado|reducido)\s+(?:el|la|los|las|mi|mis)\s+([a-záéíóúñ]+)([^?.!]*)([?.!]*)$", t, re.I)
        if mc_:
            pl_ = mc_.group(5).lower().endswith("s")
            cuerpo_ = f"{mc_.group(2) or ''}{'mis' if pl_ else 'mi'} {mc_.group(5)}{mc_.group(6)} {mc_.group(3) or ''}{'han' if pl_ else 'ha'} {mc_.group(4)}"
            t = mc_.group(1) + cuerpo_[:1].upper() + cuerpo_[1:] + ("?" if mc_.group(1) else ".")
    t = re.sub(r"\b(sac(?:ado|[oó]|aron|u[eé]|aste)|he sacado|ha sacado)\s+un\s+(?:diez|10|nueve|9)\b", r"\1 un sobresaliente", t, flags=re.I)
    return _pasiva_impersonal(t)


def _es_yo_verbo(w):
    """«mido», «pido», «decido»: acaban como un participio pero son un verbo en primera persona («yo mido…» no es «estoy mido»)."""
    try:
        from . import morfo as _M
        an = _M.analizar(w.lower()) or []
        return any(len(a) > 2 and a[1] == "pres" and a[2] == "1s" for a in an) and not any(len(a) > 1 and a[1] == "part" for a in an)
    except Exception:                                    # noqa
        return False


def _clitico_perfecto(t):
    """2.26 · «Ya lo he recogido» = «Ya lo recogí»: con el pronombre delante del auxiliar el núcleo colocaba mal el objeto
    («he mi coche recogido»). El pretérito simple dice lo mismo y lo entiende bien."""
    from . import morfo as _M
    if "?" in t or "¿" in t:
        return t

    def _f(m_):
        try:
            lem = next((a[0] for a in (_M.analizar(m_.group(3).lower()) or []) if len(a) > 1 and a[1] == "part"), None)
            forma = _M.conjugar(lem, "pret", {"he": "1s", "has": "2s", "ha": "3s", "hemos": "1p", "han": "3p"}[m_.group(2).lower()]) if lem else None
        except Exception:                                # noqa
            forma = None
        return f"{m_.group(1)} {forma}" if forma else m_.group(0)
    if not re.match(r"^\W*ya\s+(?:lo|la|los|las)\s+(?:he|has|ha|hemos|han)\b", t, re.I):
        return t                                         # solo el caso que fallaba («Ya lo he recogido»); «hoy la he llamado…» el núcleo ya lo entiende
    return re.sub(r"\b(lo|la|los|las)\s+(he|has|ha|hemos|han)\s+([a-záéíóúñ]+(?:ado|ido|to|so|cho))\b", _f, t, count=1, flags=re.I)


def _medidas(t):
    """2.25 · «un metro ochenta», «metro y medio», «dos kilos y medio»: la medida dicha de palabra, en cifras con su unidad."""
    from . import numerales as _N

    def _dec(m_):
        ent = {"un": 1, "uno": 1, "dos": 2, "tres": 3}.get(m_.group(1).lower(), 1) if m_.group(1) else 1
        cola = m_.group(2).strip()
        if cola.lower() in ("y medio", "medio"):
            return f"{ent},50 metros"
        try:
            c = _N.a_cifras(re.sub(r"^y\s+", "", cola, flags=re.I)).strip()
        except Exception:                                # noqa
            return m_.group(0)
        if re.fullmatch(r"\d{1,2}", c):
            return f"{ent},{int(c):02d} metros"
        return m_.group(0)
    t = re.sub(r"\b(?:(un|uno|dos|tres)\s+)?metros?\s+(y medio|(?:y\s+)?(?:\d{1,2}|[a-záéíóúñ]+(?:\s+y\s+[a-záéíóúñ]+)?))(?=[\s.,;!?]|$)(?!\s+(?:cent[ií]metros|metros|de\b))",
               _dec, t, flags=re.I)
    t = re.sub(r"\b(un|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s+(kilos?|litros?|horas?)\s+y\s+(?:medio|media)\b",
               lambda m_: f"{ {'un': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5, 'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10}[m_.group(1).lower()] },5 "
                          + (m_.group(2) if m_.group(2).endswith("s") else m_.group(2) + "s"), t, flags=re.I)
    return t


_MARCO232 = (r"^(?:(?:hoy|ayer|anoche|esta mañana|esta tarde|esta semana|antes|ahora)\s*,?\s+)?(?:he aprendido|aprend[ií]|he sabido|me he enterado de|me enter[eé] de|he descubierto|"
             r"descubr[ií]|me han dicho|me han contado|me dijeron|me contaron|he o[ií]do|he le[ií]do|resulta)\s+que\s+")


def _noticia232(t):
    """2.32 · Maneras corrientes de contar algo que el núcleo no entendía:
    «Hoy he aprendido que mi tío es carpintero. Que vive en Navarra y que le gusta cazar» -> «Mi tío es carpintero. Vive en Navarra y le gusta cazar.»
    «Tengo un amigo que se llama Manuel Pérez que le gustan mucho los gatos»        -> «Mi amigo se llama Manuel y le gustan mucho los gatos.»"""
    import os
    if os.environ.get("LCM_SIN_PAPELES") or "?" in t or "¿" in t or "\n" in t or len(t) > 300:
        return t
    t0 = t
    t = re.sub(r"\b(gustan?|encantan?|interesan?)\s+muchos\s+(?=(?:los|las|el|la)\b)", r"\1 mucho ", t, flags=re.I)
    marco = bool(re.match(_MARCO232, t, re.I))
    if marco:
        t = re.sub(_MARCO232, "", t, flags=re.I)
        t = t[:1].upper() + t[1:]
    if marco or re.search(r"[.!]\s+Que\s+[a-záéíóúñ]", t):
        t = re.sub(r"([.!])\s+Que\s+([a-záéíóúñ])", lambda m: m.group(1) + " " + m.group(2).upper(), t)   # «. Que vive en…» sigue contando lo mismo
        t = re.sub(r"(\s+y|,)\s+que\s+(?=[a-záéíóúñ])", r"\1 ", t)
    m = re.match(r"^(?:tengo|conozco a)\s+(un|una)\s+([a-záéíóúñ]+)\s+(?:que\s+se\s+llama|llamad[oa])\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)((?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})"
                 r"(?:\s*(?:,|\by\b)?\s*(?:y\s+)?(?:que|al que|a la que|a quien)\s+(.+?))?[.!]?$", t, re.I)
    if m and m.group(3)[:1].isupper():
        rol, nombre, resto = m.group(2).lower(), m.group(3), (m.group(5) or "").strip()
        t = f"Mi {rol} se llama {nombre}" + (f" y {resto}" if resto else "") + "."
    return t if t else t0


def normaliza(raw: str) -> str:
    """Quita muletillas, corrige erratas frecuentes y pone signos a las preguntas que no los traen."""
    t = raw.strip()
    if not t:
        return t
    try:
        t = _noticia232(t)
    except Exception:                                    # noqa
        pass
    try:
        t = _medidas(t)
        t = _clitico_perfecto(t)
    except Exception:                                    # noqa
        pass
    letras = [c for c in t if c.isalpha()]
    if len(letras) > 6 and sum(c.isupper() for c in letras) > 0.8 * len(letras):
        t = t[:1].upper() + t[1:].lower()               # 2.16: TODO EN MAYÚSCULAS es la misma frase dicha más alto
    t = re.sub(r"[A-Za-zÁÉÍÓÚÑáéíóúñ+]+", lambda m_: _ERRATAS.get(m_.group(0).lower(), m_.group(0)) if m_.group(0).lower() in ("mñn", "mñna", "ad+") else m_.group(0), t)
    t = re.sub(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", lambda m_: (lambda w_, r_: (r_[:1].upper() + r_[1:] if w_[:1].isupper() else r_) if r_ else w_)(m_.group(0), _ERRATAS.get(m_.group(0).lower())), t)
    t = re.sub(r"\b(me|te|le|nos|les) (?:flipa|chifla|pirra|priva|vuelve loc[oa])(n?)\b", r"\1 encanta\2", t, flags=re.I)   # 2.17: «le flipa» = «le encanta»
    t = re.sub(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", lambda m_: _fonetica(m_.group(0)), t)
    t = re.sub(r"(?<=[a-záéíóúñ]) i (?=[a-záéíóúñA-ZÁÉÍÓÚÑ])", " y ", t)             # «se llama Julia i vive en Vigo»
    t = re.sub(r"\b(me|te|le|nos|les) mola(n?)\b", r"\1 gusta\2", t, flags=re.I)     # «me mola» = «me gusta»
    t = re.sub(r"\b(me|te|le|nos|les) (?:flipa|chifla|pirra|priva|vuelve loc[oa])(n?)\b", r"\1 encanta\2", t, flags=re.I)   # 2.17: «le flipa» = «le encanta»
    t = _normaliza_217(t)
    t = re.sub(r"^no\s*,\s*(perdona|perd[oó]n|disculpa)\s*,\s*", lambda m_: m_.group(1).capitalize() + ", ", t, flags=re.I)   # «no, perdona, …»: una sola corrección
    if re.match(r"^(?:no|perdona|perd[oó]n|disculpa|me he equivocado|me equivoqu[eé]|me he confundido|rectifico|mejor dicho)\s*[,:]", t, re.I):
        # «Me he equivocado: juego los viernes, no los jueves»: lo que se niega al final ya lo dice la corrección
        t = re.sub(r",\s*(?:y\s+)?no\s+(?:(?:el|la|los|las|en|a|al|con|de)\s+)?[\wáéíóúñ ]{1,25}([.!]?)$", r"\1", t)
    t = re.sub(r"^(a [A-ZÁÉÍÓÚÑ][\wáéíóúñ]+|a mi \w+|a mis \w+|a) (me|te|le|les|nos) dan? (miedo|pánico|terror) ", lambda m_: f"{m_.group(1)} {m_.group(2)} asustan " if m_.group(1) != "a" else m_.group(0), t, flags=re.I)
    t = re.sub(r"\b(me|te|le|les|nos) (da|dan) (miedo|pánico|terror|panico) ", lambda m_: f"{m_.group(1)} {'asustan' if m_.group(2) == 'dan' else 'asusta'} ", t, flags=re.I)
    t = re.sub(r"^(cualquier|cada|todo|toda)\s+([a-záéíóúñ]+)\s+(?=(?:es|tiene|puede|sabe|come|vive|necesita|respira)\b)", lambda m_: ("Una " if m_.group(2).endswith("a") else "Un ") + m_.group(2) + " ", t, flags=re.I)
    t = re.sub(r"^(¿?\s*cu[aá]nt[oa]s\s+[a-záéíóúñ]+)\s+hay\s+en\s+(?=(?:\d+|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|media)\s+(?:segundos?|minutos?|horas?|d[ií]as?|semanas?|mes(?:es)?|años?|siglos?)\b)", r"\1 son ", t, flags=re.I)
    t = re.sub(r"^(hola|buenas|buenos d[ií]as|buenas tardes|buenas noches|hey|ey)\s+(?=(?:me|soy|te|yo|mi|tengo|quer[ií]a|quiero|vivo|estoy)\b)", lambda m_: m_.group(1).capitalize() + ". ", t, flags=re.I)
    t = re.sub(r"\b((?:me llamo|te llamas|se llama|se llaman|mi nombre es)\s+)([a-záéíóúñ]{3,})\b(?!\s+[a-záéíóúñ])",
               lambda m_: m_.group(1) + (m_.group(2).capitalize() if not _conocida(m_.group(2)) and sa(m_.group(2)) not in _SEGURAS else m_.group(2)), t)
    t = re.sub(r"^(?:oye|oyes|mira|a ver|bueno|pues eso|pues nada|pues mira|pues|total|en fin|nada|vale|venga|jo|buf|uf|ay|anda)\s*,?\s+(?:es\s+)?que\s+(?=[a-záéíóúñ])", "", t, flags=re.I)
    t = re.sub(r"^(?:oye|pues eso|pues nada|pues mira|en fin|total)\s*,\s*", "", t, flags=re.I)
    t = re.sub(r"^al final\s+(?=(?:no\s+)?(?:voy|vamos|va|van|he|hemos|ha|han|me|nos|se)\b)", "", t, flags=re.I)
    m_ap = re.match(r"^((?:mi|mis|tu|tus|su|sus|el|la|los|las)\s+[a-záéíóúñ]+)\s*,\s*(?:el|la|los|las)\s+([a-záéíóúñ]+)\s*,\s+(.+)$", t, re.I)
    if m_ap and "?" not in t:                            # «mi moto, la negra, está en el garaje» = «mi moto negra está en el garaje»
        cop = "son" if m_ap.group(1).lower().split()[0] in ("mis", "tus", "sus", "los", "las") else "es"
        t = f"{m_ap.group(1)} {m_ap.group(3).rstrip('.')}. {m_ap.group(1)[:1].upper() + m_ap.group(1)[1:]} {cop} {m_ap.group(2)}."
    t = re.sub(r"\b(no (?:me|te|le|nos|les) (?:gustan?|apetecen?|interesan?|importan?|convencen?)) (?:nada|para nada|en absoluto|mucho|demasiado)\b(?! (?:de|que)\b)", r"\1", t, flags=re.I)
    m_ng = re.match(r"^(ning[úu]n|ninguna)\s+([a-záéíóúñ]+)\s+([a-záéíóúñ]+)\b(.*)$", t, re.I)
    if m_ng and "?" not in t:                            # 2.16: «ningún pez tiene pulmones» = «los peces no tienen pulmones» (universal negativa)
        an = [x for x in M.analizar(m_ng.group(3)) if x[2] == "3s" and x[1] in ("pres", "imp", "fut", "pret")]
        if an:
            art = "las" if m_ng.group(1).lower() == "ninguna" else "los"
            t = f"{art} {M.plural(m_ng.group(2))} no {M.conjugar(an[0][0], an[0][1], '3p')}{m_ng.group(4)}"
    if t:
        t = t[:1].upper() + t[1:]
    t2 = _parte_narracion(t)                             # 2.16: dos hechos en una frase de narración -> dos frases (antes de mover nada de sitio)
    if t2 != t:
        return " ".join(normaliza(x) for x in re.split(r"(?<=[.!])\s+(?=[A-ZÁÉÍÓÚÑ])", t2))
    # erratas frecuentes (palabra a palabra, respetando mayúscula inicial y signos)
    def err(m):
        w = m.group(0)
        r = _ERRATAS.get(w.lower())
        if not r:
            return w
        return r[:1].upper() + r[1:] if w[:1].isupper() else r
    t = re.sub(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", err, t)
    for _ in range(3):
        m = _INI.match(t)
        if not m or len(t[m.end():].split()) < 2:
            break
        t = t[m.end():]
    t = re.sub(r"\s*\b(?:ja(?:ja)+j?a?|je(?:je)+|xd+|lol|jiji+)\b[.!]*\s*$", "", t, flags=re.I) or t
    t = re.sub(r",?\s+como (?:yo|tú|tu|él|ella)(?:\s+(?:casi|más o menos|igual|también))?\s*([.!]?)$", r"\1", t, flags=re.I)
    # «Te quería contar que…», «Quería decirte que…»: anuncian lo que viene
    t = re.sub(r"^\s*(?:(?:te|os) )?(?:quer[ií]a|quiero|tengo que|ten[ií]a que|voy a|he de)\s+(?:contar|decir|comentar|explicar)(?:te|os)?\s+que\s+", "", t, flags=re.I) or t
    t = re.sub(r"^\s*(?:¿sabes qu[eé]\?|sabes qu[eé]\s*[,:]|¿a que no sabes qu[eé]\?|a que no sabes qu[eé]\s*[,:]|adivina\s*[,:])\s*", "", t, flags=re.I) or t
    # «Soy Elena, la del otro día»: la coletilla tras el nombre
    t = _hendidas(t) if re.match(r"^(?:[Ss]oy)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s*,\s*(?:el|la)\s+que\s+(?:tiene|vive|trabaja|estudia|tenía|vivía)\b", t) else t   # «Soy Raquel, la que tiene una panadería»: eso es un dato
    t = re.sub(r"^((?:[Ss]oy|[Mm]e llamo)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*,\s*(?:el|la)\s+(?:del?|que)\s+.+?([.!]?)$", r"\1\2", t)
    t = re.sub(r"^((?:(?:[Hh]ola|[Bb]uenas),?\s+)?(?:[Ss]oy|[Mm]e llamo)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s+(?:otra vez|de nuevo|again)([.!]?)$", r"\1\2", t)
    t = re.sub(r"\s*,?\s*\b(?:al final|por fin|finalmente|al fin y al cabo)\b\s*,?", " ", t, flags=re.I).strip()
    t = re.sub(r"\s+([?.!])", r"\1", t)
    # «exigente pero justa»: «pero» entre dos cualidades
    def _pero(m_):
        w = m_.group(2)
        c = M.analizar(w)
        if any(x[1] in ("pres", "pret", "imp", "fut", "cond") for x in c) and sa(w) not in ("justa", "justo"):
            return m_.group(0)
        return " y " + m_.group(1) + w
    t = re.sub(r",?\s+pero\s+((?:muy |bastante |algo |un poco |también )?)([a-záéíóúñ]+)(?=\s*[.!]?$)", _pero, t)
    # «(El caso es que) llevo toda la semana durmiendo fatal» -> «Estoy durmiendo fatal toda la semana»
    t = re.sub(r"^(?:el caso es que |es que |pues )?(llevo|llevamos)\s+((?:toda la|todo el|todas las|todos los|una|un|dos|tres|varios|varias|muchos|muchas|unos|unas)\s+(?:semana|semanas|mes|meses|día|días|dia|dias|noche|noches|año|años|tarde|mañana))\s+([a-záéíóúñ]+(?:ando|iendo|yendo))\b(.*)$",
               lambda m_: ("Estoy " if m_.group(1).lower() == "llevo" else "Estamos ") + m_.group(3) + m_.group(4).rstrip(" .!") + " " + (m_.group(2) if re.match(r"tod", m_.group(2), re.I) else "desde hace " + m_.group(2)), t, flags=re.I) if not re.search(r"[¿?]", t) else t
    # «Yo un poco agobiado con el trabajo»: estado de ánimo sin verbo
    t = re.sub(r"^(?:pues |bueno,? )?yo\s+((?:un poco|algo|muy|bastante|super|tan)\s+)?([a-záéíóúñ]+(?:ado|ada|ido|ida|oso|osa))\b(.*)$",
               lambda m_: m_.group(0) if _es_yo_verbo(m_.group(2)) else "Estoy " + (m_.group(1) or "") + m_.group(2) + m_.group(3), t, flags=re.I) if not re.search(r"[¿?]", t) else t
    # «Yo fatal, mi vecino…»: respuesta corta al «¿qué tal?» seguida de lo que cuenta
    t = re.sub(r"^(?:pues |yo |pues yo )?(?:fatal|bien|mal|regular|genial|muy bien|muy mal|de maravilla|hecho polvo|hecha polvo|reventad[oa]|cansad[oa]|agotad[oa])\s*[,.;:]\s+(?=\S+\s+\S+)", "", t, flags=re.I) or t
    t = re.sub(r"^(?:menos mal que|por suerte|afortunadamente|al menos|encima|lo bueno es que|lo malo es que|ya está|ya esta|nada|pues nada|en fin)\s*[,.]?\s+(?=\S+\s+\S+)", "", t, flags=re.I) or t
    t = re.sub(r"\b(?:sobre todo|más que nada|mas que nada|principalmente|básicamente|basicamente)\s+(?=\S)", "", t, flags=re.I)
    # «aquí estudiando para…» = «estoy estudiando para…»
    t = re.sub(r"^(?:aquí|aqui|ahora|pues aquí|pues aqui|ya)\s+([a-záéíóúñ]+(?:ando|iendo|yendo))\b", r"Estoy \1", t, flags=re.I)
    m = _FIN.search(t)
    if m and len(t[:m.start()].split()) >= 2:
        t = t[:m.start()] + (m.group(1) or "")
    # «y tú cómo aprendes?» / «cuantos animales tengo?» / «donde vivo»: pregunta sin signo de apertura (o sin ninguno)
    n = sa(t).strip(" .!")
    n2 = re.sub(r"^(?:y|pero|oye|y entonces)\s+(?:tu\s+|yo\s+)?", "", n)
    if "¿" not in t:
        es_wh = any(n2 == w or n2.startswith(w + " ") for w in _WH)
        if es_wh and n2.startswith("como ") and not re.match(r"^como (?:me|te|se|es|esta|estan|estas|son|fue|va|le|lo|la|he|has|ha|puedo|aprendes|funcionas|sabes|que)\b", n2):
            es_wh = False                               # «como pan todos los días»
        if es_wh and re.match(r"^que (?:[a-zñ]+ )?(?:mas|tan) [a-zñ]+$|^que (?:bien|mal|pena|rabia|horror|asco|guay|bonito|bonita|suerte|rollo|cansancio|sueño|calor|frio|hambre|sed|ilusion|alegria|bueno|buena|fuerte|raro|rara|gracia|lio|lata|pasada|maravilla|desastre|faena)\b", n2) and "?" not in t:
            es_wh = False                               # «¡Qué día más largo!»: exclamación, no pregunta
        if es_wh and n2.startswith(("que ", "cuando ")) and re.match(r"^(?:que (?:te|tengas|sepas|vaya|bien|pena|suerte|va|bueno|mal|rollo|asco|guay)|cuando .+,)", n2):
            es_wh = False
        if t.rstrip().endswith("?") or (es_wh and len(n2.split()) <= 9 and not t.rstrip().endswith(".")):
            cuerpo = t.rstrip(" ?")
            if es_wh:                                   # tilde del interrogativo
                ps = cuerpo.split()
                for i, w in enumerate(ps[:4]):
                    if sa(w).strip(",") in _TILDE and sa(w) == w.lower():
                        ps[i] = _TILDE[sa(w)] if not w[:1].isupper() else _TILDE[sa(w)].capitalize()
                        break
                cuerpo = " ".join(ps)
            t = "¿" + cuerpo[:1].upper() + cuerpo[1:] + "?"
    t = _impersonal_dativo(t)
    def _miles(m_):
        k = M.numero(sa(m_.group(1).lower())) if m_.group(1) else 1
        return str(k * 1000) if k else m_.group(0)
    t = re.sub(r"\b(?:(\w+)\s+)?mil\b(?=\s+(?:euros|dólares|dolares|libras|pesos|personas|kilómetros|kilometros|km|metros|habitantes|seguidores|alumnos|socios|libros))", _miles, t)   # «veinte mil euros» -> «20000 euros»
    if not re.search(r"[¿?]", t):
        def _encl(m_):
            base = m_.group(1)
            return base if any(x[1] == "inf" for x in M.analizar(sa(base.lower()))) else m_.group(0)
        t = re.sub(r"\b(\w+[aeií]r)(?:le|les|lo|la|los|las|me|te|nos)\b(?=\s+\w)", _encl, t)   # «para pedirle perdón» -> «para pedir perdón»
    t = _dislocado(t)
    t = re.sub(r"\bconmigo\b", "con mí", t); t = re.sub(r"\bcontigo\b", "con ti", t)
    t = _menos_dias(t)
    t = _pero_a_mi(t)
    t = _lo_deje(t)
    t = _desde_que(t)
    t = _hendidas(t)
    t = _fecha_delante(t)
    if not re.search(r"[¿?]", t):
        t = re.sub(r"^(?:[Tt]od[oa]s)\s+((?:mis|tus|sus|nuestros|nuestras)\s+)", lambda m_: m_.group(1).capitalize(), t)   # «Todos sus amigos…» = «Sus amigos…»
    def _mevoy(m_):                                      # «…, me visto y me voy a trabajar» (no «adiós, me voy a dormir»)
        antes_ = t[:m_.start()]
        return (m_.group(1) + "voy a " + m_.group(2)) if any(_verbo_finito(w.lower().strip(",.")) for w in antes_.split()) else m_.group(0)
    t = re.sub(r"(,\s+|\s(?:y|e)\s+)me voy a ([a-záéíóúñ]+(?:ar|er|ir))\b", _mevoy, t)
    t = _verbo_repartido(t)
    t = _adj_con_grado(t)
    t = _sust_con_adj(t)
    t = _tambien_tampoco(t)
    t = _ni_sujetos(t)
    t = _lista_sujetos(t)
    t = _reparte_de(t)
    t = re.sub(r"^¿\s*([A-Za-záéíóúñ]+)\s+yo\b", r"¿\1", t)    # «¿Voy yo a la piscina?» = «¿Voy a la piscina?»
    t = _gusta_mas(t)
    t = _elipsis_tener(t)
    t = _tanto_como(t)
    t = _pp_delante(t)
    t = _sp_delante(t)
    if "?" not in t and "¿" not in t and re.match(r"^[Cc]omo\s+(?:el|la|los|las|un|una|pasta|pescado|carne|fruta|verdura|arroz|pan|ensalada|sopa|mucho|poco|bien|mal|tarde|temprano|en|con|sin|fuera|solo|sola)\b", t) \
            and not re.match(r"^[Cc]omo\s+\S+\s+(?:es|son|está|esta|era|dice|dijo)\b", t):
        t = "Yo como " + t.split(None, 1)[1]          # «Como pasta los martes»: afirmación, verbo comer
    t = _durante(t)
    t = _aposicion_sn(t)
    t = _aposicion_lista(t)
    t = _coma_frases(t)
    t = _relativas(t)
    t = _sujeto_pospuesto(t)
    t = _elipsis_nombres(t)
    t = _lista_nombrada(t)
    t = _comas_nombres(t)
    t = _comas_cosas(t)
    if t[:1] == "¿" and len(t) > 1 and t[1].islower():
        return "¿" + t[1].upper() + t[2:]               # «¿por qué…?» como «¿Por qué…?»: el análisis no debe depender de la mayúscula
    return t[:1].upper() + t[1:] if t and t[0] != "¿" else t


_LIGERAS = {"ser", "estar", "tener", "haber", "hacer", "ir", "decir", "poder", "querer", "saber", "dar", "ver", "llevar", "deber", "soler", "creer", "pasar"}
_VACIAS = set("""el la los las un una unos unas de del al a en con por para sin sobre y o e ni que como cuando donde quien cual cuanto cuantos cuantas cuanta mi mis tu tus su sus me te se le les lo nos
yo tu el ella ellos ellas mio tuyo es no si ya muy mas menos este esta esto ese esa eso hoy pues bueno vale qué algo nada todo toda todos todas alguna alguno algun ningun ninguna he has ha han hemos
va voy vas van fue era soy eres esta estoy estas son hay tiene tengo tienes ahi aqui alli entonces tambien porque""".split())


def lemas(texto):
    """Palabras con contenido de una frase, normalizadas (verbos a infinitivo, nombres a singular)."""
    out = set()
    for w in re.findall(r"[a-záéíóúñü0-9]+", texto.lower()):
        s = sa(w)
        if s in _VACIAS or len(s) < 2:
            continue
        c = M.analizar(w)
        if c and (c[0][0] in M._VERBOS_BASE or c[0][0] in M._IRR or len(s) > 4):
            out.add(c[0][0])
            if c[0][1] not in ("part", "ger", "inf"):
                continue
        out.add(sa(M.singular(w)) if s.endswith("s") and len(s) > 3 else s)
    return out


def anota(nuc, texto):
    """Guarda literalmente una frase que no se ha podido interpretar."""
    t = texto.strip()
    if not t or len(t.split()) < 2 or len(t) > 300:
        return False
    ls = sorted(lemas(t))
    if not ls:
        return False
    nuc.notas = [x for x in getattr(nuc, "notas", []) if sa(x["t"]) != sa(t)][-39:] + [{"t": t, "l": ls, "turno": nuc.turno}]
    nuc.guardar()
    return True


def recuerda(nuc, pregunta):
    """Nota literal que responde a la pregunta (todas sus palabras con contenido aparecen en la nota), o None."""
    q = lemas(pregunta) - {"recordar", "acordar", "contar"}
    fuertes = {x for x in q if x not in _LIGERAS}
    if not fuertes:
        return None
    mejor = None
    for x in getattr(nuc, "notas", []):
        l = set(x["l"])
        if fuertes <= l or (len(fuertes) >= 3 and len(fuertes & l) >= len(fuertes) - 1):
            if mejor is None or x["turno"] >= mejor["turno"]:
                mejor = x
    return mejor["t"] if mejor else None


_REC = {"ofrec": "una oferta de ", "propus": "una propuesta de ", "propuest": "una propuesta de "}


_ART_DEF = {"un": "el", "una": "la", "unos": "los", "unas": "las", "el": "el", "la": "la", "los": "los", "las": "las"}


def _verbo_finito(w):
    return any(x[1] in ("pres", "pret", "imp", "fut", "cond") for x in M.analizar(sa(w)))


def _arranca_verbo(txt):
    """¿Empieza por un verbo conjugado (con su clítico o negación delante)?"""
    ps = txt.split()
    k = 0
    while k < len(ps) - 1 and sa(ps[k]) in ("se", "me", "te", "le", "les", "nos", "lo", "la", "los", "las", "no", "siempre", "ya", "nunca", "tambien"):
        k += 1
    return k < len(ps) and _verbo_finito(ps[k])


def _persona_rel(txt):
    """Persona del primer verbo conjugado de la relativa («he comprado» -> 1s)."""
    for w in txt.split()[:4]:
        an = [x for x in M.analizar(sa(w)) if x[1] in ("pres", "pret", "imp", "fut", "cond")]
        if an:
            return an[0][2]
    return ""


def _concuerda_rel(ant, rel):
    """La relativa de sujeto concuerda en número con su antecedente («un restaurante que abrieron» no: es de objeto)."""
    per = _persona_rel(rel)
    pl = sa(ant.split()[0].lower()) in ("los", "las", "unos", "unas", "mis", "tus", "sus") or ant.split()[-1].endswith("s")
    return not (per == "3p" and not pl or per == "3s" and pl)


def _de_objeto(ant, rel):
    """«(la alfombra) que he comprado» -> «He comprado la alfombra»: relativa de objeto (el verbo no es de 3.ª persona)."""
    a = ant[:1].lower() + ant[1:] if ant.split()[0].lower() in _ART_DEF or ant.split()[0].lower() in ("mi", "tu", "su", "mis", "tus", "sus") else ant
    return rel[:1].upper() + rel[1:] + " " + a


def _antecedente(sn):
    """«mi novio» -> «mi novio»; «un restaurante» -> «el restaurante»; «Iñaki» -> «Iñaki»."""
    ps = sn.split()
    if ps and sa(ps[0]) in _ART_DEF and ps[0][:1].islower():
        return _ART_DEF[sa(ps[0])] + " " + " ".join(ps[1:])
    return sn


_SN_FIN = r"((?:(?:mi|tu|su|mis|tus|sus|un|una|unos|unas|el|la|los|las|este|esta)\s+[a-záéíóúñ]+(?:\s+(?:mayor|menor|pequeño|pequeña|mayores|pequeños|pequeñas|nuevo|nueva|mejor|favorito|favorita))?(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)"


_DUR = r"(?:muchos|pocos|varios|bastantes|tantos|muchas|pocas|varias|bastantes|tantas|un par de|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|quince|veinte|treinta|cuarenta|\d+)"


_PREF = {"me": "prefiero", "te": "prefieres", "le": "prefiere", "nos": "preferimos", "les": "prefieren"}
_SN = r"(?:(?:el|la|los|las|un|una|mi|tu|su|mis|tus|sus)\s+)?[a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?"


def _al(sn):
    return re.sub(r"^el\s", "al ", sn) if re.match(r"^el\s", sn) else "a " + sn


def _gusta_mas(t):
    """2.11 · preferencia: «me gusta más el té que el café» = «prefiero el té al café»; «menos» invierte; también en preguntas."""
    preg = "?" in t or "¿" in t
    c = t.strip().strip("¿?.! ")
    # «¿qué me gusta más, el té o el café?»
    m = re.match(r"^(?:[Yy] )?[Qq]u[ée]\s+(me|te|le|nos)\s+gusta(?:n)?\s+m[áa]s\s*,?\s+(" + _SN + r")\s+o\s+(" + _SN + r")$", c)
    if m and preg:
        return f"¿Qué {_PREF[m.group(1).lower()]}, {m.group(2)} o {m.group(3)}?"
    # «(A mi hermano) le gusta más X que Y», «me gusta menos X que Y»
    m = re.match(r"^((?:[Aa]\s+.+?\s+)?)(me|te|le|nos|les)\s+gusta(?:n)?\s+(m[áa]s|menos)\s+(" + _SN + r")\s+que\s+(" + _SN + r")$", c, re.I)
    if m:
        quien = m.group(1).strip()
        quien = re.sub(r"^[Aa]\s+", "", quien) if quien else ""
        x, y = (m.group(4), m.group(5)) if m.group(3).lower() != "menos" else (m.group(5), m.group(4))
        v = _PREF[m.group(2).lower()]
        cuerpo = (quien + " " if quien else "") + f"{v} {x} {_al(y)}"
        cuerpo = cuerpo[:1].upper() + cuerpo[1:]
        return ("¿" + cuerpo + "?") if preg else cuerpo + "."
    # «el té me gusta más que el café»
    m = re.match(r"^(" + _SN + r")\s+(me|te|le|nos)\s+gusta(?:n)?\s+(m[áa]s|menos)\s+que\s+(" + _SN + r")$", c, re.I)
    if m:
        x, y = (m.group(1), m.group(4)) if m.group(3).lower() != "menos" else (m.group(4), m.group(1))
        cuerpo = f"{_PREF[m.group(2).lower()]} {x[:1].lower() + x[1:]} {_al(y)}"
        cuerpo = cuerpo[:1].upper() + cuerpo[1:]
        return ("¿" + cuerpo + "?") if preg else cuerpo + "."
    return t


def _elipsis_tener(t):
    """«Pablo tiene treinta años y yo veintiocho» -> «Pablo tiene treinta años. Yo tengo veintiocho años.» (verbo sobrentendido)."""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^(.+?\s+(?:tiene|tengo|tienes|tienen)\s+\S+\s+años)\s+y\s+(yo|t[úu]|[ée]l|ella|(?:mi|tu|su)\s+[a-záéíóúñ]+|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s+(\S+)(?:\s+años)?\s*([.!]?)$", t.strip())
    if not m or M.numero(sa(m.group(3).lower())) is None and not m.group(3).isdigit():
        return t
    quien = m.group(2)
    v = {"yo": "tengo", "tu": "tienes", "tú": "tienes"}.get(quien.lower(), "tiene")
    return f"{m.group(1)}. {quien[:1].upper() + quien[1:]} {v} {m.group(3)} años{m.group(4) or '.'}"


def _lista_sujetos(t):
    """2.12 · «Nerea, Iker y yo vamos…» -> «Nerea y Iker y yo vamos…»: la coma de una lista de sujetos es una «y»."""
    if "?" in t or "¿" in t or "," not in t:
        return t
    ws = t.split()
    kv = None
    for k, w in enumerate(ws):
        w0 = w.strip(",.;:!").lower()
        if k > 0 and _verbo_finito(w0) and not ws[k - 1].endswith(","):
            kv = k
            break
    if kv is None or kv < 3:
        return t
    pre = " ".join(ws[:kv])
    if not re.search(r"\s(?:y|e)\s", pre) or "," not in pre or re.match(r"^(?:si|cuando|aunque|porque|como|que|pero|y|en|con|para|por|de|a)\b", pre, re.I):
        return t
    trozos = [x.strip() for x in re.split(r",\s*", pre)]
    if any(len(x.split()) > 4 or not x for x in trozos):
        return t
    return re.sub(r",\s*", " y ", pre) + " " + " ".join(ws[kv:])


def _reparte_de(t):
    """2.12 · «hay niños de Rumanía, Marruecos y Ecuador» -> «hay niños de Rumanía y niños de Marruecos y niños de Ecuador»."""
    if "?" in t or "¿" in t:
        return t
    m = re.search(r"\b([a-záéíóúñ]+s|gente|público|publico|familia)\s+de\s+(" + _NOMBRE + r"(?:\s*(?:,|\by\b|\be\b)\s*(?:de\s+)?" + _NOMBRE + r")+)", t)
    if not m:
        return t
    noms = [x for x in re.split(r"\s*(?:,|\by\b|\be\b)\s*(?:de\s+)?", m.group(2)) if x]
    if len(noms) < 2:
        return t
    rep = " y ".join(f"{m.group(1)} de {x}" for x in noms)
    return t[:m.start()] + rep + t[m.end():]


_GRADO_ADJ = r"(?:muy|bastante|super|súper|realmente|algo|un poco|demasiado)"


_COLORES_ADJ = {"rojo", "azul", "verde", "amarillo", "negro", "blanco", "gris", "naranja", "morado", "rosa", "marron", "violeta", "beis", "dorado", "plateado"}


def _sust_con_adj(t):
    """2.14: «mi vecina es una profesora muy simpática» -> «… es una profesora y es muy simpática» (si no, el adjetivo se pierde).
    Solo con adjetivos que la base conoce (tienen contrario anotado) o colores, y con un sustantivo que es clase de la base."""
    m = re.match(r"^(.+?\b(es|era|fue|será|sera|son|eran))\s+(un|una|unos|unas)\s+([a-záéíóúñ]+)\s+((?:muy|bastante|algo|un poco|tan|super|súper)\s+)?([a-záéíóúñ]+)([.!]?)$", t)
    if not m:
        return t
    from . import conceptos as _K
    sust, adj = m.group(4), m.group(6)
    a0 = sa(adj.lower())
    cands = {a0, a0[:-1] + "o" if a0.endswith("a") else a0, a0[:-1] if a0.endswith("s") else a0, a0[:-2] + "o" if a0.endswith("as") else a0, a0[:-2] if a0.endswith("es") else a0}
    es_adj = any(c in _K.kb()["ant"] or c in _COLORES_ADJ for c in cands)
    s0 = sa(M.singular(sust.lower()))
    es_sust = any(_K._kb_clase(x) for x in {sa(sust.lower()), s0, s0[:-1] + "o" if s0.endswith("a") else s0, s0[:-1] if s0.endswith("ora") else s0})
    if not es_adj or not es_sust or _K._kb_clase(a0):
        return t
    return f"{m.group(1)} {m.group(3)} {sust} y {m.group(2)} {m.group(5) or ''}{adj}{m.group(7)}".replace("  ", " ")


def _adj_con_grado(t):
    """«Mi piso es pequeño, antiguo y muy tranquilo» -> una frase por adjetivo (el «muy» dentro de la lista rompe el análisis)."""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^(.+?)\s+(es|son|está|están|era|eran|parece|parecen|soy|eres|somos|estoy|estás|estamos|era|fui|fue)\s+((?:" + _GRADO_ADJ + r"\s+)?[a-záéíóúñ]+(?:\s*,\s*(?:" + _GRADO_ADJ + r"\s+)?[a-záéíóúñ]+)*\s+(?:y|e)\s+(?:" + _GRADO_ADJ + r"\s+)?[a-záéíóúñ]+)\s*([.!]?)$", t.strip())
    if not m:
        return t
    adjs = [x.strip() for x in re.split(r"\s*,\s*|\s+(?:y|e)\s+", m.group(3)) if x.strip()]
    if len(adjs) < 2 or any(a.split()[-1] in ("el", "la", "los", "las", "un", "una", "de", "mi", "tu", "su") for a in adjs):
        return t
    if not re.search(r"\b" + _GRADO_ADJ + r"\b", m.group(3)) and not re.match(r"^(?:yo|tú|tu)$", m.group(1).strip(), re.I) \
            and len(adjs) >= 3:
        return t                                         # las listas largas sin grado ya las entiende el análisis tal cual
    suj = m.group(1)
    return " ".join(f"{(suj if k == 0 else suj[:1].upper() + suj[1:])} {m.group(2)} {a}." for k, a in enumerate(adjs))


def _persona_suj(suj):
    s0 = sa(suj.lower().strip())
    if s0 in ("yo",):
        return "1s"
    if s0 in ("tu", "tú"):
        return "2s"
    if re.search(r"\by yo\b", s0) or s0 in ("nosotros", "nosotras"):
        return "1p"
    if re.search(r"\s(?:y|e)\s", s0) or s0 in ("ellos", "ellas"):
        return "3p"
    return "3s"


def _genero_suj(suj):
    w = [x for x in sa(suj.lower()).split() if x not in ("mi", "tu", "su", "el", "la", "mis", "tus", "sus", "los", "las")]
    if not w or w[0] in ("yo", "tu", "nosotros", "nosotras", "usted"):
        return None                                      # el pronombre no dice el género
    if w[0][:1] and suj.strip().split()[-1][:1].isupper():
        return M.genero_nombre(suj.strip().split()[-1])
    return "f" if w[0].endswith("a") else ("m" if w[0].endswith(("o", "or", "e")) else None)


def _ajusta_pred(pred, pers, gen):
    """Copia el predicado con el verbo en la persona del nuevo sujeto y el atributo en su género."""
    ws = pred.split()
    for k, w in enumerate(ws):
        an = [x for x in M.analizar(sa(w.lower())) if x[1] in ("pres", "pret", "imp", "fut", "cond")]
        if an:
            ws[k] = M.conjugar(an[0][0], an[0][1], pers)
            if an[0][0] in ("ser", "estar", "parecer") and gen and k + 1 < len(ws):
                a = ws[k + 1]
                if gen == "m" and a.endswith("a") and not a.endswith("ista"):
                    ws[k + 1] = a[:-1] + ("o" if not a.endswith(("ora",)) else "")
                elif gen == "f" and a.endswith("o"):
                    ws[k + 1] = a[:-1] + "a"
                elif gen == "f" and a.endswith("or"):
                    ws[k + 1] = a + "a"
            break
    return " ".join(ws)


def _tambien_tampoco(t):
    """«Mi hermana es dentista y mi cuñado también» -> «Mi hermana es dentista. Mi cuñado es dentista.»;
       «Pablo no fuma y yo tampoco» -> «Pablo no fuma. Yo no fumo.»"""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^(.+?)\s+(?:y|e)\s+((?:yo|tú|tu|él|ella|nosotros|nosotras|ellos|ellas|(?:mi|tu|su|el|la|mis|tus|sus)\s+[a-záéíóúñ]+|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+))\s+(también|tambien|tampoco)\s*([.!]?)$", t.strip())
    if not m:
        return t
    izq, nuevo, tipo = m.group(1), m.group(2), m.group(3)
    ws = izq.split()
    kv = next((k for k, w in enumerate(ws) if k > 0 and _verbo_finito(w.lower())), None)
    if kv is None:
        return t
    j = kv - 1 if ws[kv - 1].lower() in ("no", "nunca", "me", "te", "se", "le", "lo", "la") else kv
    if j > 0 and ws[j - 1].lower() == "no":
        j -= 1
    suj1, pred = " ".join(ws[:j]), " ".join(ws[j:])
    if not suj1:
        return t
    neg = bool(re.match(r"^(?:no|nunca)\b", pred, re.I))
    if (tipo.startswith("tamp") and not neg) or (not tipo.startswith("tamp") and neg):
        return t
    pred2 = _ajusta_pred(pred, _persona_suj(nuevo), _genero_suj(nuevo))
    n2 = nuevo[:1].upper() + nuevo[1:]
    return _adj_con_grado(f"{izq}.") + " " + _adj_con_grado(f"{n2} {pred2}{m.group(4) or '.'}")


def _ni_sujetos(t):
    """«Ni Clara ni Rubén ni yo tenemos perro» -> «Clara no tiene perro. Rubén no tiene perro. Yo no tengo perro.»"""
    if "?" in t or "¿" in t:
        return t
    if not re.match(r"^[Nn]i\s", t.strip()):
        return t
    trozos = [x.strip() for x in re.split(r"\bni\b", t.strip().rstrip(".!"), flags=re.I) if x.strip()]
    if len(trozos) < 2:
        return t
    ws = trozos[-1].split()
    kv = next((k for k, w in enumerate(ws) if k > 0 and (_verbo_finito(w.lower()) or any(x[1] in ("pres", "pret", "imp", "fut") and x[2] in ("1p", "3p") for x in M.analizar(sa(w.lower())))) ), None)
    if kv is None:
        return t
    j0 = kv - 1 if ws[kv - 1].lower() in ("me", "te", "se", "nos", "le", "les") else kv
    sujs = trozos[:-1] + [" ".join(ws[:j0])]
    pred = "no " + " ".join(ws[j0:])
    out = []
    for s_ in sujs:
        p2 = _ajusta_pred(pred, _persona_suj(s_), None)
        out.append(f"{s_[:1].upper() + s_[1:]} {p2}.")
    return " ".join(out)


def _verbo_repartido(t):
    """2.12 · «Pongo los platos en la mesa, los vasos en el armario y las tazas en el cajón» -> el verbo se repite en cada trozo."""
    if "?" in t or "¿" in t or "," not in t:
        return t
    cuerpo = t.strip().rstrip(".!")
    ws = cuerpo.split()
    kv = next((k for k, w in enumerate(ws[:5]) if _verbo_finito(w.lower().strip(","))), None)
    if kv is None:
        return t
    cab = " ".join(ws[:kv + 1])
    resto = " ".join(ws[kv + 1:])
    trozos = [x.strip() for x in re.split(r"\s*,\s*|\s+(?:y|e)\s+(?=(?:el|la|los|las|un|una|unos|unas|mi|mis|tu|tus|su|sus)\s)", resto) if x.strip()]
    if len(trozos) < 2:
        return t
    dets = ("el", "la", "los", "las", "un", "una", "unos", "unas", "mi", "mis", "tu", "tus", "su", "sus")
    preps = ("en", "a", "al", "de", "del", "con", "para", "por", "sobre", "encima", "debajo", "dentro", "junto")
    for x in trozos:
        xw = x.lower().split()
        if xw[0] not in dets or not any(w in preps for w in xw[2:]) or len(xw) > 7:
            return t
    cab = cab[:1].upper() + cab[1:]
    return " ".join(f"{cab} {x}." for x in trozos)


def _tanto_como(t):
    """«Tanto mi tío como mi tía son profesores» -> «Mi tío y mi tía son profesores»; «me gusta tanto el té como el café» -> «… el té y el café»."""
    m = re.search(r"\b[Tt]anto\s+(.+?)\s+como\s+(.+)$", t)
    if not m or re.search(r"\btanto\s+(?:como|que)\b", t, re.I):
        return t
    a, resto = m.group(1), m.group(2)
    if re.match(r"^(?:mucho|poco|alto|alta|grande|[a-záéíóúñ]+(?:o|a|os|as|e|es))$", a) and not re.match(r"^(?:mi|tu|su|el|la|los|las|[A-ZÁÉÍÓÚÑ])", a):
        return t                                         # «es tanto alto como…» no aparece; «tanto … como» de igualdad lo trata la comparación
    out = t[:m.start()] + a + " y " + resto
    return out[:1].upper() + out[1:]


def _sp_delante(t):
    """«Para la cena compro tomates…» -> «Compro tomates… para la cena»: el complemento antepuesto va detrás del verbo."""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^([Pp]ara|[Ee]n|[Cc]on|[Pp]or|[Dd]esde|[Hh]asta|[Ee]ntre|[Ss]in)\s+(.+)$", t.strip())
    if not m:
        return t
    ws = m.group(2).rstrip(".!").split()
    _det = ("el", "la", "los", "las", "un", "una", "unos", "unas", "mi", "mis", "tu", "tus", "su", "sus", "este", "esta", "ese", "esa", "nuestra", "nuestro", "del", "al", "de")
    _cl = ("me", "te", "se", "nos", "os", "le", "les", "lo", "los", "la", "las")
    coma = next((k for k, w in enumerate(ws) if w.endswith(",")), None)
    if coma is not None and any(_verbo_finito(x.rstrip(",")) and (j == 0 or ws[j - 1].lower() not in ("el", "la", "los", "las", "un", "una", "mi", "tu", "su")) for j, x in enumerate(ws[:coma + 1]) if j > 0):
        coma = None                                      # la coma es de una enumeración posterior al verbo
    for k in range(1, min(8, len(ws))):
        w = ws[k].rstrip(",")
        if coma is not None and k <= coma:
            continue
        prev = ws[k - 1].rstrip(",").lower()
        if not _verbo_finito(w) or prev in _det and (coma is None or k - 1 > coma) or prev in ("que", "a"):
            continue
        ini = k - 1 if prev in _cl and (coma is None or k - 1 > coma) else k
        while ini > 1 and (sa(ws[ini - 1].rstrip(",").lower()) in ("siempre", "nunca", "normalmente", "casi", "tambien", "ya", "solo", "no", "todavia", "yo", "tu",
                                                                   "nadie", "alguien", "nada", "todos", "todas", "ella", "ellos", "ellas", "nosotros", "nosotras", "usted", "ustedes")
                           or ws[ini - 1] in ("él", "tú") or (ws[ini - 1][:1].isupper() and ini - 1 > 0)):
            ini -= 1                                     # «En Madrid Ana trabaja…»: el sujeto va con el verbo
        if ini == 0:
            continue
        if sa(ws[ini].lower()) in ("nadie", "alguien", "todos", "todas", "todo", "nada"):
            return t                                     # «En mi casa nadie fuma»: ya lo entiende otra regla tal cual
        if ws[ini].lower() in ("hay", "habia", "había", "hubo", "habrá", "habra") or ws[ini].lower() in ("es", "son", "era", "eran", "fue", "está", "esta", "están"):
            pass
        pp = (m.group(1)[:1].lower() + m.group(1)[1:]) + " " + " ".join(x.rstrip(",") for x in ws[:ini])
        resto = " ".join(ws[ini:])
        return f"{resto[:1].upper() + resto[1:]} {pp}."
    return t


def _pp_delante(t):
    """«Después del turno ceno con mis compañeras» -> «Ceno con mis compañeras después del turno» (el complemento de tiempo va detrás)."""
    if "?" in t or "¿" in t:
        return t
    mf = re.match(r"^((?:[Tt]odas las|[Tt]odos los|[Cc]ada|[Ll]os|[Ll]as)\s+(?:mañanas?|tardes?|noches?|d[ií]as?|semanas?|veranos?|inviernos?|domingos?|s[áa]bados?|lunes|martes|mi[ée]rcoles|jueves|viernes|fines de semana|fin de semana|mes(?:es)?|años?))\s*,?\s+(\S+)\s+(.+)$", t.strip())
    if mf and re.match(r"^(?:[Ll]os|[Ll]as)\s", mf.group(1)) and any(x[2] == "3p" for x in M.analizar(sa(mf.group(2).lower()))):
        mf = None                                        # «Los lunes son horribles»: ahí «los lunes» es el sujeto
    if mf and _verbo_finito(mf.group(2).lower()) and not mf.group(2).lower() in ("que",):
        resto = f"{mf.group(2)} {mf.group(3)}".rstrip(".!")
        return f"{resto[:1].upper() + resto[1:]} {mf.group(1)[:1].lower() + mf.group(1)[1:]}."   # «Todas las mañanas paso por…»
    m = re.match(r"^((?:[Dd]espués|[Dd]espues|[Aa]ntes)\s+(?:de|del)|[Tt]ras|[Dd]urante)\s+(.+)$", t.strip())
    if not m:
        return t
    ws = m.group(2).rstrip(".!").split()
    _det = ("el", "la", "los", "las", "un", "una", "unos", "unas", "mi", "mis", "tu", "tus", "su", "sus", "este", "esta", "ese", "esa", "nuestra", "nuestro")
    _cl = ("me", "te", "se", "nos", "os", "le", "les", "lo", "los", "la", "las")
    coma = next((k for k, w in enumerate(ws) if w.endswith(",")), None)
    if coma is not None and any(_verbo_finito(x.rstrip(",")) and (j == 0 or ws[j - 1].lower() not in ("el", "la", "los", "las", "un", "una", "mi", "tu", "su")) for j, x in enumerate(ws[:coma + 1]) if j > 0):
        coma = None                                      # la coma es de una enumeración posterior al verbo
    for k in range(1, min(6, len(ws))):
        w = ws[k].rstrip(",")
        if coma is not None and k <= coma:
            continue                                     # «tras la reunión, me fui…»: la coma cierra el complemento
        prev = ws[k - 1].rstrip(",").lower()
        if not _verbo_finito(w) or prev in ("que", "de", "a") or (prev in _det and (coma is None or k - 1 > coma)):
            continue
        ini = k - 1 if prev in _cl and (coma is None or k - 1 > coma) else k
        while ini > 1 and sa(ws[ini - 1].rstrip(",").lower()) in ("siempre", "nunca", "normalmente", "casi", "tambien", "ya", "solo", "no", "todavia"):
            ini -= 1                                     # «antes de la cena siempre llamo…»: el adverbio va con el verbo
        if ini == 0:
            continue
        pp = (m.group(1)[:1].lower() + m.group(1)[1:]) + " " + " ".join(x.rstrip(",") for x in ws[:ini])
        resto = " ".join(ws[ini:])
        return f"{resto[:1].upper() + resto[1:]} {pp}."
    return t


def _durante(t):
    """«Mi abuela fue maestra muchos años» -> «… fue maestra durante muchos años» (duración, no un atributo coordinado)."""
    m = re.match(r"^(.*\b(?:fue|era|ha sido|había sido|estuvo|estaba|fuimos|fui|eras|fuiste)\s+[a-záéíóúñ]+(?:\s+(?:de|en)\s+[a-záéíóúñ]+)?)\s+(" + _DUR + r"\s+(?:años|meses|semanas|días|dias))\s*([.!]?)$", t.strip(), re.I)
    if not m or re.search(r"\b(?:durante|hace|desde|por)\s*$", m.group(1)):
        return t
    return f"{m.group(1)} durante {m.group(2)}{m.group(3)}"


def _aposicion_sn(t):
    """«Mi tío Andrés, el hermano de mi padre, es fontanero» -> «Mi tío Andrés es fontanero. Andrés es el hermano de mi padre.»"""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^((?:[Mm]i|[Tt]u|[Ss]u|[Ee]l|[Ll]a)\s+[a-záéíóúñ]+\s+(" + _NOMBRE + r")|(" + _NOMBRE + r"))\s*,\s*((?:el|la|un|una|mi|tu)\s+[a-záéíóúñ]+(?:\s+(?:de|del)\s+[^,]+)?)\s*,\s*(.+?)\s*([.!]?)$", t.strip())
    if not m:
        return t
    nom = m.group(2) or m.group(3)
    resto = m.group(5)
    if not any(_verbo_finito(w) for w in resto.split()[:3]) or sa(resto.split()[0].lower()) in _NO_PARTE:
        return t
    sn = m.group(1)
    return f"{sn[:1].upper() + sn[1:]} {resto}{m.group(6) or '.'} {nom} es {m.group(4)}."


def _aposicion_lista(t):
    """«Salgo a cenar con dos compañeros, Rafa y Toni» -> «Salgo a cenar con dos compañeros. Se llaman Rafa y Toni.»"""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^(.+?\b(?:con|a|para|de)\s+(?:dos|tres|cuatro|cinco|mis|tus|sus|los|las|unos|unas|nuestros|nuestras)\s+(?:[a-záéíóúñ]+\s+)?[a-záéíóúñ]+s)\s*,\s*"
                 r"(" + _NOMBRE + r"(?:\s*,\s*" + _NOMBRE + r")*\s+(?:y|e)\s+" + _NOMBRE + r")\s*([.!]?)$", t.strip())
    if not m or not _arranca_verbo(m.group(1).split(" ", 1)[0] if not m.group(1)[:1].islower() else m.group(1)) and not any(_verbo_finito(w) for w in m.group(1).split()[:3]):
        return t
    noms = re.sub(r"\s*,\s*", " y ", m.group(2))
    return f"{m.group(1)}. Se llaman {noms}{m.group(3) or '.'}"


_NO_PARTE = ("que", "y", "e", "pero", "porque", "aunque", "cuando", "si", "donde", "como", "o", "ni", "pues", "sino", "mientras", "uno", "una", "unos", "unas", "otro", "otra", "otros", "otras", "ambos", "ambas", "cada", "alguno", "alguna", "ninguno", "ninguna", "el", "la", "los", "las", "mi", "mis", "tu", "tus", "su", "sus")


def _coma_frases(t):
    """«Estoy agotado, hoy he trabajado doce horas» -> dos frases: cada lado tiene su verbo y el segundo no es subordinado."""
    if "?" in t or "¿" in t or t.count(",") != 1:
        return t
    izq, der = [x.strip() for x in t.split(",", 1)]
    if not izq or not der or sa(der.split()[0].lower()) in _NO_PARTE or len(der.split()) < 2 or sa(izq.split()[0].lower()) in _NO_PARTE + ("cuando", "aunque", "mientras", "antes", "despues", "desde", "hasta", "para", "en cuanto", "como"):
        return t
    if not any(_verbo_finito(w) for w in izq.split()[:5]) or not any(_verbo_finito(w) for w in der.split()[:4]):
        return t
    if re.match(r"^(?:hola|mira|oye|bueno|vale|pues|claro|gracias|perdona|venga|sí|si|no)$", sa(izq.lower())):
        return t
    if re.search(r"\b(?:equivoc|perdon|corrij|rectific|me confund|quise decir|queria decir|error|me he liado|me lie)", sa(izq.lower())):
        return t                                         # «Me he equivocado, vive en Córdoba»: corrección, la trata otra regla
    if _arranca_verbo(der) and not re.match(r"^(?:[Mm]e|[Tt]e|[Ss]e|[Ll]e|[Nn]os)\b", der) and len(izq.split()) <= 2 and not any(_verbo_finito(w) for w in izq.split()):
        return t                                         # «Mi hermano, vive en…»: el sujeto antes de la coma
    der = der.rstrip(".!")
    fin = "." if not t.rstrip().endswith("!") else "!"
    return f"{izq.rstrip('.!')}. {der[:1].upper() + der[1:]}{fin}"


_T_NARR = (r"(?:(?:los|las|el|cada|todos los|todas las)\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábados?|sabados?|domingos?|fines de semana|fin de semana|días|dias|"
           r"mañanas|tardes|noches|veranos?|inviernos?)|por (?:la|las) (?:mañanas?|tardes?|noches?)|después|despues|luego|más tarde|mas tarde|al final|mañana|ayer|hoy|ahora|"
           r"el (?:año|mes|verano|invierno) que viene|la semana que viene|el próximo (?:año|mes|verano)|la próxima semana)")


def _parte_narracion(t):
    """2.16: dos cosas de una narración que se dicen en una frase son dos frases.
       «Tiene una hija que se llama Noa y un gato que se llama Milo»          -> «Tiene una hija que se llama Noa. Tiene un gato que se llama Milo.»
       «Los lunes lleva a Noa a piano y los viernes cena con sus padres»      -> «Los lunes lleva a Noa a piano. Los viernes cena con sus padres.»"""
    if "?" in t or "¿" in t:
        return t
    fin = t[-1] if t[-1:] in ".!" else ""
    c = t[:-1] if fin else t
    nom = r"(?:un|una|dos|tres|otro|otra)\s+[a-záéíóúñ]+\s+que\s+se\s+llaman?\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(?:\s+y\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)?"
    m = re.match(rf"^(.*?\b[A-Za-záéíóúñÁÉÍÓÚÑ]+\s+)({nom})\s*(?:,|\sy)\s+({nom})$", c)
    if m and len(m.group(1).split()) <= 6:
        pre = m.group(1)
        return f"{pre}{m.group(2)}. {pre[:1].upper() + pre[1:]}{m.group(3)}{fin or '.'}"
    m = re.match(rf"^(.+?)\s+y\s+({_T_NARR})\s+(.+)$", c, re.I)
    if m and len(m.group(1).split()) >= 3:
        ws = m.group(3).split()
        k = 1 if ws and ws[0].lower() in ("se", "me", "le", "lo", "la", "nos", "les", "no") else 0
        if len(ws) > k and _verbo_finito(ws[k]) and any(_verbo_finito(w) for w in m.group(1).split()):
            return f"{m.group(1)}. {m.group(2)[:1].upper() + m.group(2)[1:]} {m.group(3)}{fin or '.'}"
    return t


def _relativas(t):
    """Oraciones de relativo, partidas en frases simples:
       «Mi novio, que se llama Hugo, es cocinero»       -> «Mi novio se llama Hugo. Mi novio es cocinero.»
       «Estoy casada con Iñaki, que es profesor»        -> «Estoy casada con Iñaki. Iñaki es profesor.»
       «Trabaja en un restaurante que está en el centro» -> «Trabaja en un restaurante. El restaurante está en el centro.»"""
    if "?" in t or "¿" in t:
        return t
    if re.match(r"^(?:y\s+|mira,?\s+)?(?:este|esta|esto|estos|estas|ese|esa|eso|aquí|aqui)\b", t.strip(), re.I):
        return t                                        # «Este es el color que le gusta a Rocío»: presenta lo que se ve, lo trata la vista
    fin = t.rstrip()[-1:] if t.rstrip()[-1:] in ".!" else ""
    c = t.rstrip(" .!")
    # 1) explicativa en medio: «SN, que REL, PRINCIPAL»
    m = re.match(r"^(.+?)\s*,\s*que\s+([^,]+?)\s*,\s*(.+)$", c)
    if m and _arranca_verbo(m.group(2)) and _arranca_verbo(m.group(3)) and len(m.group(1).split()) <= 4 and not _arranca_verbo(m.group(1)):
        sn = m.group(1)
        sn2 = sn[:1].upper() + sn[1:]
        return f"{sn2} {m.group(2)}. {sn2} {m.group(3)}{fin or '.'}"
    # 2) explicativa al final: «PRINCIPAL ... SN, que REL»
    m = re.match(r"^(.+?\b" + _SN_FIN + r")\s*,\s*que\s+(.+)$", c)
    if m and _arranca_verbo(m.group(3)):
        ant = _antecedente(m.group(2))
        if _persona_rel(m.group(3)) in ("1s", "2s", "1p", "2p"):
            if ant[:1].isupper():
                return t
            return f"{m.group(1)}. {_de_objeto(ant, m.group(3))}{fin or '.'}"
        if not _concuerda_rel(ant, m.group(3)):
            return t
        return f"{m.group(1)}. {ant[:1].upper() + ant[1:]} {m.group(3)}{fin or '.'}"
    # 3b) tras un número: «Tengo tres nietos que me visitan los domingos» -> «… Mis nietos me visitan los domingos»
    m = re.match(r"^((?:[Tt]engo|[Tt]enemos)\s+(?:dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|\d+|varios|varias|muchos|muchas)\s+([a-záéíóúñ]+s))\s+que\s+(.+)$", c)
    if m and _arranca_verbo(m.group(3)) and not re.match(r"se\s+llaman", m.group(3)):
        return f"{m.group(1)}. Mis {m.group(2)} {m.group(3)}{fin or '.'}"
    # 3) especificativa tras un nombre con artículo: «… un restaurante que está en el centro»
    if re.search(r"\b(?:semana|mes|año|lunes|martes|miércoles|jueves|viernes|sábado|domingo|verano|invierno|curso|fin de semana)\s+que\s+(?:viene|vienen|entra|entran)\b", c):
        return t                                        # «la semana que viene» es una expresión de tiempo
    m = re.match(r"^(.+?\b((?:un|una|unos|unas|el|la|los|las)\s+[a-záéíóúñ]+))\s+que\s+(.+)$", c)
    if m and _arranca_verbo(m.group(3)) and not _verbo_finito(m.group(2).split()[-1]) and (len(m.group(1).split()) >= 3 or _persona_rel(m.group(3)) in ("1s", "2s", "1p", "2p")) \
            and not re.match(r"se\s+llama", m.group(3)):         # «tiene una hija que se llama Carla»: eso ya se entiende tal cual
        ant = _antecedente(m.group(2))
        if _persona_rel(m.group(3)) in ("1s", "2s", "1p", "2p"):
            if ant[:1].isupper():
                return t
            return f"{m.group(1)}. {_de_objeto(ant, m.group(3))}{fin or '.'}"
        if not _concuerda_rel(ant, m.group(3)):
            return t
        m_cop = re.match(r"^(.+?)\s+(?:es|son|era|eran|fue|fueron|será|sera)\s+(?:un|una|unos|unas)\s+[a-záéíóúñ]+$", m.group(1))
        if m_cop:                                        # 2.16: «un zorb es un animal que vive en cuevas»: lo que se añade se dice del sujeto (género + diferencia)
            suj = m_cop.group(1).strip()
            suj = re.sub(r"^(un|una|unos|unas)\b", lambda x: {"un": "el", "una": "la", "unos": "los", "unas": "las"}[x.group(1).lower()], suj, flags=re.I)
            return f"{m.group(1)}. {suj[:1].upper() + suj[1:]} {m.group(3)}{fin or '.'}"
        return f"{m.group(1)}. {ant[:1].upper() + ant[1:]} {m.group(3)}{fin or '.'}"
    return t


_NOMBRE = r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"


def _elipsis_nombres(t):
    """«Iker tiene diez años, Ane ocho y Jon cinco» -> «Iker tiene diez años. Ane tiene ocho años. Jon tiene cinco años.»
       «Ane juega al fútbol y Jon al baloncesto»   -> «Ane juega al fútbol. Jon juega al baloncesto.»"""
    if "?" in t or "¿" in t:
        return t
    fin = t.rstrip()[-1:] if t.rstrip()[-1:] in ".!" else ""
    c = t.rstrip(" .!")
    trozos = [x.strip() for x in re.split(r"\s*,\s*(?:y\s+)?|\s+y\s+", c) if x.strip()]
    if len(trozos) < 2:
        return t
    m0 = re.match(r"^(" + _NOMBRE + r")\s+((?:se\s+|no\s+)?\S+)\s+(.+)$", trozos[0])
    if not m0 or not _verbo_finito(m0.group(2).split()[-1]):
        return t
    verbo, resto0 = m0.group(2), m0.group(3)
    unidad = re.match(r"^(\S+)\s+(años|meses|kilos|hijos|hijas|hermanos|hermanas|euros|horas|días)\b", resto0)
    frases = [trozos[0]]
    for x in trozos[1:]:
        m = re.match(r"^(" + _NOMBRE + r")\s+(.+)$", x)
        if not m or _arranca_verbo(m.group(2)):
            return t                                   # «…y bebe agua»: no es elipsis del verbo
        r = m.group(2)
        if unidad and (M.numero(sa(r)) is not None or re.fullmatch(r"\d+", r)):
            r = r + " " + unidad.group(2)
        frases.append(f"{m.group(1)} {verbo} {r}")
    return ". ".join(frases) + (fin or ".")


def _lista_nombrada(t):
    """«Tengo tres sobrinos: Iker, Ane y Jon» / «Tenemos dos hijos, Pablo y Nerea» -> «… Se llaman Iker, Ane y Jon.»"""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^((?:[Tt]engo|[Tt]enemos|[Tt]iene|[Tt]ienen)\s+(?:dos|tres|cuatro|cinco|seis|\d+)\s+[a-záéíóúñ]+(?:\s+(?:pequeños|pequeñas|mayores))?)\s*[:,]\s*"
                 r"(" + _NOMBRE + r"(?:\s*,\s*" + _NOMBRE + r")*\s+y\s+" + _NOMBRE + r")\s*([.!]?)$", t.strip())
    if not m:
        return t
    return f"{m.group(1)}. Se llaman {m.group(2)}{m.group(3) or '.'}"


_NO_NOMBRE = {"hola", "mira", "oye", "bueno", "vale", "gracias", "perdona", "pues", "venga", "claro", "si", "no", "buenas", "adios", "ademas", "luego", "despues", "entonces", "hoy", "ayer", "manana"}


def _comas_cosas(t):
    """«manzanas, plátanos y uvas» -> «manzanas y plátanos y uvas»: listas de cosas de fábrica (el análisis pierde las comas)."""
    from . import conceptos as _K
    t = re.sub(r"\b((?:es|son|está|están|esta|estan|era|eran|parece|parecen|soy|eres|somos)\s+)((?:muy\s+|bastante\s+)?[a-záéíóúñ]+(?:\s*,\s+(?:muy\s+|bastante\s+)?[a-záéíóúñ]+)+)(\s+y\s+(?:muy\s+|bastante\s+)?[a-záéíóúñ]+)",
               lambda m_: m_.group(1) + re.sub(r"\s*,\s+", " y ", m_.group(2)) + m_.group(3), t)   # «es alto, rubio y simpático»
    if "," in t and re.search(r"\s(?:y|e)\s", t):    # 2.12: elementos de varias palabras («una moto negra») y final con «e»
        t2 = _lista_general(t, _K)
        if t2 != t:
            return t2
    m = re.search(r"((?:\b(?:un |una |unos |unas |el |la |los |las )?[a-záéíóúñ]+\s*,\s+)+(?:un |una |unos |unas |el |la |los |las )?[a-záéíóúñ]+\s+y\s+(?:un |una |unos |unas |el |la |los |las )?[a-záéíóúñ]+)\b", t)
    if not m:
        return t
    trozo = m.group(1)
    items = [x.strip() for x in re.split(r"\s*,\s*|\s+y\s+", trozo)]
    if len(items) < 3 or not all(_K._kb_clase(x.split()[-1]) for x in items):
        return t
    return t.replace(trozo, re.sub(r"\s*,\s+", " y ", trozo))


_DETS = ("un", "una", "unos", "unas", "el", "la", "los", "las", "mi", "mis", "tu", "tus", "su", "sus", "dos", "tres", "cuatro", "cinco", "un poco de", "de", "a", "en", "al", "del")


def _lista_general(t, _K):
    fin = re.search(r"[.!]?\s*$", t).start()
    cuerpo, cola = t[:fin], t[fin:]
    if ":" in cuerpo:
        return t
    trozos = [x.strip() for x in cuerpo.split(",")]
    if len(trozos) < 2:
        return t
    ult = re.split(r"\s+(y|e)\s+", trozos[-1], maxsplit=1)
    if len(ult) != 3:
        return t
    item_b, item_c = ult[0], ult[2]
    m_c = re.match(r"^(.+?)(\s+(?:en|a|al|con|para|desde|cerca de|al lado de|junto a|delante de|detrás de|detras de)\s+.+)$", item_c)
    if m_c and len(item_c.split()) > 4:                 # «… y un mercado en mi calle»: el complemento es de toda la lista
        item_c, cola = m_c.group(1), m_c.group(2) + cola
    medios = trozos[1:-1] + [item_b]
    n_ = len(item_b.split())
    w0 = trozos[0].split()
    if len(w0) <= n_ or n_ > 4:
        return t
    item_a = " ".join(w0[-n_:])
    items = [item_a] + medios + [item_c]

    def valido(it):
        ws = [w for w in it.split() if w.lower() not in _DETS]
        if not ws or len(it.split()) > 4:
            return False
        def cl(w):
            w = sa(w.lower()); s_ = sa(M.singular(w))
            return _K._kb_clase(w) or _K._kb_clase(s_) or (s_.endswith("a") and _K._kb_clase(s_[:-1] + "o"))   # «gata» -> gato
        return any(cl(w) for w in ws) or ws[0][:1].isupper()
    if not all(valido(x) for x in items) or any(_verbo_finito(x.split()[0].lower()) for x in items[1:] if x.split()[0].lower() not in _DETS):
        return t
    pre = " ".join(w0[:-n_])
    return f"{pre} " + " y ".join(items[:-1]) + f" {ult[1]} {item_c}{cola}"


def _comas_nombres(t):
    """«Iker, Ane y Jon» -> «Iker y Ane y Jon»: el análisis pierde las comas y juntaría «Iker Ane» en un solo nombre."""
    pat = re.compile(r"\b(" + _NOMBRE + r")\s*,\s+(?=(" + _NOMBRE + r")(?:\s*,\s+" + _NOMBRE + r")*\s+y\s+" + _NOMBRE + r"\b)")
    def rep(m):
        if sa(m.group(1).lower()) in _NO_NOMBRE or sa(m.group(2).lower()) in _NO_NOMBRE:
            return m.group(0)
        return m.group(1) + " y "
    return pat.sub(rep, t)


def _dislocado(t):
    """«Las paredes las quiero de ese color» -> «Quiero las paredes de ese color» (objeto adelantado y repetido con un pronombre)."""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^((?:[Ee]l|[Ll]a|[Ll]os|[Ll]as|[Mm]i|[Mm]is|[Tt]u|[Tt]us|[Ee]ste|[Ee]sta|[Ee]stos|[Ee]stas)\s+[a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)\s*,?\s+(lo|la|los|las)\s+([a-záéíóúñ]+)\b(.*)$", t.strip())
    if not m or not _verbo_finito(m.group(3)) or any(_verbo_finito(w) for w in m.group(1).split()[1:]):
        return t                                        # «Mi hija prefiere la pasta»: el «la» es un artículo
    from . import conceptos as _K
    from .nucleo import FAMILIA as _FAM, PERSONA_CLS as _PER
    cab = sa(M.singular(m.group(1).split()[1].lower()))
    c_ = _K._kb_clase(cab)
    if cab in _FAM or M.masc(cab) in _FAM or cab in _PER or M.masc(cab) in _PER or (c_ and "persona" in _K.ancestros(c_)):
        return t                                        # «Mi hermano lo sabe»: una persona es el sujeto, no un objeto adelantado
    art = sa(m.group(1).split()[0].lower())
    pl = art in ("los", "las", "mis", "tus", "estos", "estas") or m.group(1).split()[1].endswith("s")
    f = art in ("la", "las", "esta", "estas") or (art in ("mi", "mis", "tu", "tus") and M.genero_sust(sa(M.singular(m.group(1).split()[1]))) == "f")
    cl = m.group(2)
    if (cl.endswith("s")) != pl or (cl.startswith("la")) != f:
        return t
    sn = m.group(1)[:1].lower() + m.group(1)[1:]
    return m.group(3)[:1].upper() + m.group(3)[1:] + " " + sn + m.group(4)


_TIEMPO_INI = (r"(?:el|este|el próximo|el proximo)\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)|pasado mañana|mañana|hoy|esta tarde|esta noche|"
               r"el día \d{1,2}|el \d{1,2} de [a-z]+|la semana que viene|el mes que viene|el fin de semana|este fin de semana|en (?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)")


def _fecha_delante(t):
    """«El viernes es la cena de Navidad» -> «La cena de Navidad es el viernes» (la fecha va delante del evento)."""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^(" + _TIEMPO_INI + r")\s+(es|será|sera|son|serán|seran|fue)\s+((?:el|la|los|las|mi|tu|su|nuestra|nuestro)\s+.+?)([.!]?)$", t.strip(), re.I)
    if not m:
        return t
    sn = m.group(3)
    return f"{sn[:1].upper() + sn[1:]} {m.group(2).lower()} {m.group(1)[:1].lower() + m.group(1)[1:]}{m.group(4) or '.'}"


def _hendidas(t):
    """«El pan de centeno es el que más vendemos» / «Lo que más vendemos es el pan de centeno» -> «Vendemos el pan de centeno»;
       «Soy Raquel, la que tiene una panadería» -> «Soy Raquel. Tengo una panadería.»"""
    if "?" in t or "¿" in t:
        return t
    c = t.strip().rstrip(".!")
    m = re.match(r"^(.+?)\s+(?:es|son|era|eran)\s+(?:el|la|lo|los|las)\s+que\s+(?:más|mas)\s+([a-záéíóúñ]+)\b(.*)$", c)
    if m and _verbo_finito(m.group(2)):
        x = m.group(1); x = x[:1].lower() + x[1:] if x.split()[0].lower() in ("el", "la", "los", "las", "mi", "mis") else x
        return f"{m.group(2)[:1].upper() + m.group(2)[1:]} {x}{m.group(3)}."
    m = re.match(r"^[Ll]o que (?:más|mas)\s+([a-záéíóúñ]+)\b(.*?)\s+(?:es|son)\s+(.+)$", c)
    if m and _verbo_finito(m.group(1)):
        return f"{m.group(1)[:1].upper() + m.group(1)[1:]}{m.group(2)} {m.group(3)}."
    m = re.match(r"^([Ss]oy\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*,\s*(?:la|el)\s+(?:que|de)\s+(.+)$", c)
    if m:
        ws = m.group(2).split()
        an = [x for x in M.analizar(sa(ws[0])) if x[1] in ("pres", "pret", "imp") and x[2] == "3s"]
        if an:
            v1 = M.conjugar(an[0][0], an[0][1], "1s")
            return f"{m.group(1)}. {v1[:1].upper() + v1[1:]} {' '.join(ws[1:])}."
    return t


def _desde_que(t):
    """«Vivo sola desde que murió mi marido» -> «Mi marido murió. Vivo sola desde entonces.»"""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^(.+?)\s+desde que\s+(.+?)([.!]?)$", t.strip())
    if not m or not _arranca_verbo(m.group(2)):
        return t
    sub = m.group(2)
    ms = re.match(r"^([a-záéíóúñ]+)\s+((?:mi|tu|su|el|la|mis|tus|sus|los|las)\s+.+|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)$", sub)
    if ms and _verbo_finito(ms.group(1)):
        sub = ms.group(2)[:1].upper() + ms.group(2)[1:] + " " + ms.group(1)       # «murió mi marido» -> «Mi marido murió»
    else:
        sub = sub[:1].upper() + sub[1:]
    return f"{sub}. {m.group(1)[:1].upper() + m.group(1)[1:]} desde entonces{m.group(3) or '.'}"


def _lo_deje(t):
    """«Antes fumaba mucho pero lo dejé hace dos años» -> «Antes fumaba mucho. Dejé de fumar hace dos años.»"""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^(.*?\b([a-záéíóúñ]+(?:aba|ía|ia))\b.*?)\s*,?\s+(?:pero|y)\s+(?:ya\s+)?lo\s+(dejé|deje|he dejado|dejamos|hemos dejado)\b(.*)$", t.strip())
    if not m:
        return t
    an = [x for x in M.analizar(sa(m.group(2))) if x[1] == "imp"]
    if not an:
        return t
    dej = {"dejé": "Dejé", "deje": "Dejé", "he dejado": "He dejado", "dejamos": "Dejamos", "hemos dejado": "Hemos dejado"}[m.group(3)]
    return f"{m.group(1)}. {dej} de {an[0][0]}{m.group(4)}"


def _pero_a_mi(t):
    """«A él le ha gustado mucho pero a mí no» -> «A él le ha gustado mucho. A mí no me ha gustado.»"""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^(.+?)\s*,?\s+pero\s+(?:a\s+)?(mí|mi|ti|él|el|ella|ellos|ellas|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+|mi\s+\w+|mis\s+\w+)\s+(no|sí|si|tampoco|también|tambien)\s*([.!]?)$", t.strip())
    if not m:
        return t
    g = re.search(r"\b(le|les|me|te|nos)\s+((?:ha|han|había|habían)\s+)?(gusta|gustan|gustó|gustaron|gustado|encanta|encantan|encantó|encantaron|encantado|apetece|apetecía)\b", m.group(1), re.I)
    if not g:
        return t
    quien = m.group(2)
    cl = {"mí": "me", "mi": "me", "ti": "te"}.get(quien.lower(), "les" if quien.lower() in ("ellos", "ellas") or quien.split()[0].lower() in ("mis",) else "le")
    neg = "no " if m.group(3) in ("no", "tampoco") else ""
    return f"{m.group(1)}. A {quien} {neg}{cl} {g.group(2) or ''}{g.group(3)}{m.group(4) or '.'}"


def _menos_dias(t):
    """«Abro todos los días menos los domingos» -> «Abro todos los días. No abro los domingos.»"""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^(.+?)\s+(todos los días|todos los dias|toda la semana|cada día)\s*,?\s+(?:menos|excepto|salvo|quitando)\s+(?:los |el )?([a-záéíóúñ]+)\s*([.!]?)$", t.strip())
    if not m or len(m.group(1).split()) > 4 or not _arranca_verbo(m.group(1)):
        return t
    dia = m.group(3)
    dia = ("los " + dia) if dia.endswith("s") else ("el " + dia)
    base = m.group(1)
    return f"{base} {m.group(2)}. No {base[:1].lower() + base[1:]} {dia}{m.group(4) or '.'}"


_TITULOS = {"doctor", "doctora", "profesor", "profesora", "señor", "señora", "padre", "don", "doña", "jefe", "jefa", "médico", "médica", "medico", "medica", "dentista", "fisio", "entrenador", "entrenadora", "vecino", "vecina", "cartero", "abogado", "abogada"}


def _sujeto_pospuesto(t):
    """«Me recoge mi hermano a las cinco» / «Me opera el doctor Ruiz» -> «Mi hermano me recoge a las cinco» / «El doctor Ruiz me opera»."""
    if "?" in t or "¿" in t:
        return t
    m = re.match(r"^([Mm]e|[Tt]e|[Nn]os|[Ll]e|[Ll]es)\s+([a-záéíóúñ]+)\s+((?:(?:el|la|los|las|mi|mis|tu|tus|su|sus)\s+[a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\b(.*)$", t.strip())
    if not m:
        return t
    an = [x for x in M.analizar(sa(m.group(2))) if x[1] in ("pres", "pret", "imp", "fut", "cond")]
    if not an or an[0][2] not in ("3s", "3p"):
        return t
    from .nucleo import FAMILIA as _FAM, PERSONA_CLS as _PER
    sn = m.group(3)
    cab = sa(M.singular(sn.split()[1].lower())) if len(sn.split()) > 1 else ""
    persona = (len(sn.split()) == 1 and sn[:1].isupper()) or cab in _FAM or M.masc(cab) in _FAM or cab in _PER or M.masc(cab) in _PER or cab in {sa(x) for x in _TITULOS}
    if not persona or (len(sn.split()) == 1 and _verbo_finito(sn)):
        return t
    sn2 = sn[:1].upper() + sn[1:]
    return f"{sn2} {m.group(1).lower()} {m.group(2)}{m.group(4)}"


def _impersonal_dativo(t):
    """«Me han ofrecido un puesto en Bilbao» (3.ª plural sin sujeto: impersonal) -> «He recibido una oferta de un puesto en Bilbao»."""
    preg = t.startswith("¿")
    cuerpo = t.strip("¿?").rstrip(".! ")
    m = re.match(r"^((?:[A-Za-záéíóúñ]+\s+){0,2}?)(me|nos|Me|Nos)\s+(?:(han|habían)\s+)?(ofrecido|dado|regalado|concedido|mandado|enviado|propuesto|"
                 r"ofrecieron|dieron|regalaron|concedieron|mandaron|enviaron|propusieron)\b\s*(.*)$", cuerpo)
    if not m:
        return t
    pre = m.group(1).strip()
    if pre and (not preg or not re.match(r"^(?:qu[ée]|d[óo]nde|cu[áa]ndo|por qu[ée]|y)(?:\s+(?:qu[ée]|d[óo]nde|cu[áa]ndo))?$", pre, re.I)):
        return t                                        # hay sujeto explícito («Mis padres me han regalado…»): no es impersonal
    yo = m.group(2).lower() == "me"
    perf = bool(m.group(3)) or m.group(4).endswith("do")
    aux = ("he" if yo else "hemos") if perf else None
    verbo = (aux + " recibido") if perf else ("recibí" if yo else "recibimos")
    if m.group(3) == "habían":
        verbo = ("había" if yo else "habíamos") + " recibido"
    pref = next((v for k, v in _REC.items() if m.group(4).startswith(k)), "")
    resto = m.group(5).strip()
    if preg and not resto:
        out = f"{pre + ' ' if pre else ''}{verbo}"
    else:
        out = f"{pre + ' ' if pre else ''}{verbo} {pref}{resto}".strip()
        if m.group(4).startswith("regal") and resto and len(resto.split()) <= 3:
            out += " de regalo"
    out = out[:1].upper() + out[1:]
    return ("¿" + out + "?") if preg else out + "."


_SUBJ_IRR = {"vaya": "ir", "vayamos": "ir", "haga": "hacer", "tenga": "tener", "sea": "ser", "este": "estar", "esté": "estar", "venga": "venir", "diga": "decir",
             "ponga": "poner", "salga": "salir", "pueda": "poder", "quiera": "querer", "sepa": "saber", "de": "dar", "dé": "dar", "vea": "ver", "vuelva": "volver",
             "duerma": "dormir", "pida": "pedir", "traiga": "traer", "oiga": "oír", "conduzca": "conducir", "juegue": "jugar", "empiece": "empezar", "llegue": "llegar",
             "busque": "buscar", "pague": "pagar", "coja": "coger", "elija": "elegir", "siga": "seguir", "sienta": "sentir", "mueva": "mover", "cierre": "cerrar",
             "piense": "pensar", "pruebe": "probar", "cuente": "contar", "recuerde": "recordar", "acueste": "acostar", "sirva": "servir", "repita": "repetir", "mida": "medir"}


def subjuntivo(w):
    """¿Es «w» un presente de subjuntivo de 1.ª/3.ª singular? Devuelve el infinitivo o None.
    «descanse» (sin tilde) no es «descansé»; «coma», «vaya», «tenga»…"""
    b = w.lower().strip(",.;")
    if b in _SUBJ_IRR:
        return _SUBJ_IRR[b]
    if b != sa(b):                                       # lleva tilde: «descansé» es pretérito
        return None
    if b.endswith("e") and len(b) > 3:
        for st in (b[:-1], b[:-2] + "c" if b.endswith("que") else None, b[:-2] + "g" if b.endswith("gue") else None, b[:-1].replace("c", "z") if b.endswith("ce") else None):
            if st and any(x[1] == "inf" for x in M.analizar(st + "ar")):
                return st + "ar"
    if b.endswith("a") and len(b) > 3:
        for suf in ("er", "ir"):
            if any(x[1] == "inf" for x in M.analizar(b[:-1] + suf)) and not any(x[1] in ("pres", "pret", "imp") for x in M.analizar(b)):
                return b[:-1] + suf
    return None


def subj_a_segunda(txt):
    """«(que) descanse tres días» dicho a la persona -> «(que) descanses tres días»: el subjuntivo de 1.ª pasa a 2.ª."""
    ps = txt.split()
    k = 0
    while k < len(ps) - 1 and sa(ps[k].lower()) in ("no", "me", "se", "lo", "la", "le", "les", "los", "las", "ya", "nunca"):
        k += 1
    if k < len(ps) and subjuntivo(ps[k]):
        if any(sa(ps[j].lower()) == "me" for j in range(k)):
            return txt, True                           # «que me llame»: lo hace otra persona; el «me» lo cambia a_segunda
        base = ps[k].strip(",.;")
        ps[k] = ps[k].replace(base, base + "s" if not base.endswith("s") else base)
        return " ".join(ps), True
    return txt, False


def a_segunda_sin_verbo(txt):
    """Como a_segunda, pero sin tocar el verbo (ya está en subjuntivo de 2.ª): solo posesivos y pronombres."""
    from .nucleo import cambia_persona
    return cambia_persona(txt)


def a_segunda(txt):
    """«tengo que comer menos sal» -> «tienes que comer menos sal» (lo que alguien le dijo a la persona, contado a ella)."""
    from .nucleo import cambia_persona
    out = []
    for w in txt.split():
        base = w.strip(",.;")
        c = M.analizar(base)
        prev = sa(out[-1]) if out else ""
        if prev in ("un", "una", "el", "la", "los", "las", "mi", "tu", "su", "de", "del", "al", "con", "sin", "mucho", "poco", "menos", "mas", "este", "esta"):
            out.append(w); continue                     # tras artículo o preposición es un nombre («un perfume», «el trabajo»)
        if sa(base) in ("se", "te", "me", "le", "lo", "la", "nos", "os", "les", "los", "las", "si", "no", "ya"):
            out.append(w); continue
        if c and c[0][2] == "1s" and c[0][1] in ("pres", "pret", "fut", "imp", "cond") and sa(base) not in ("como", "para", "sobre", "nada", "bajo", "vino", "cura", "entre", "era"):
            try:
                w = w.replace(base, M.conjugar(c[0][0], c[0][1], "2s"))
            except Exception:                                                  # noqa
                pass
        out.append(w)
    return cambia_persona(" ".join(out))
