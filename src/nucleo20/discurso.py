"""LCM 2.23 · Leer las frases que no se sostienen solas.

En un texto, muchas frases dependen de la anterior: no traen sujeto («Se toca de pie»), son la segunda mitad de otra («…y maman
durante un año»), usan un pronombre («Con ellas trepan a los árboles») o empiezan por un adverbio de lugar («Debajo hay dos
piedras»). El núcleo entiende bien frases completas; aquí se le prepara cada frase para que lo sea:

    «Se toca de pie.»                              ->  «El contrabajo se toca de pie.»
    «…se llaman ballenatos y maman durante un año» ->  «…se llaman ballenatos.» + «Los ballenatos maman durante un año.»
    «Con ellas trepan a los árboles.»              ->  «Los osos trepan a los árboles con las garras.»
    «Debajo hay dos piedras redondas.»             ->  «Debajo de la tolva hay dos piedras redondas.»

Es un paso de TEXTO: no consulta el núcleo ni la base de conceptos, solo lleva la cuenta de qué se viene hablando (el último sujeto
en singular y en plural, y los nombres de la frase anterior). No depende del tema.

Interruptores para medir cada pieza por separado (variable LCM_DISCURSO, lista separada por comas; por defecto, todas):
    sujeto   poner el sujeto que falta          y        partir la segunda mitad con «y»
    pron     resolver pronombres                lugar    «Debajo hay…» -> «Debajo de X hay…»
    rel      «…, que se calienta…» -> otra frase sobre lo que va delante de la coma
    nada     desactiva el módulo
"""
from __future__ import annotations

import os
import re

from . import morfo as M
from .morfo import sa

_DET = ("el", "la", "los", "las", "un", "una", "unos", "unas", "cada", "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas")
_ADV_INI = ("también", "tambien", "además", "ademas", "después", "despues", "luego", "primero", "antes", "antiguamente", "hoy", "siempre", "a veces", "a menudo", "normalmente",
            "casi siempre", "por último", "por ultimo", "al final", "entonces")
_QUITA = ("también", "tambien", "además", "ademas")           # no aportan nada al hecho
_LUGAR = ("debajo", "encima", "dentro", "detrás", "detras", "delante", "alrededor", "al lado", "cerca", "fuera", "arriba", "abajo")
_NO_VERBO = {"para", "como", "sobre", "entre", "bajo", "una", "uno", "nada", "casa", "cara", "sal", "vino", "tarde", "cerca", "segundo", "primero", "parte", "forma", "medio", "solo",
             "junto", "listo", "mano", "calor", "color", "sabor", "tela", "lana", "pie"}


def _activo(pieza):
    conf = os.environ.get("LCM_DISCURSO", "sujeto,y,pron,lugar,rel")
    return "nada" not in conf and pieza in conf.split(",")


def _fin3(w):
    """'s' o 'p' si la palabra es un verbo conjugado en 3.ª persona; None si no."""
    w = w.lower().strip(",.;:")
    if sa(w) in _NO_VERBO or len(w) < 2:
        return None
    if w in ("es", "está", "esta", "tiene", "era", "fue", "hay", "tenía", "tenia"):
        return "s"
    if w in ("son", "están", "estan", "tienen", "eran", "fueron", "tenían", "tenian"):
        return "p"
    try:
        an = M.analizar(w) or []
    except Exception:                                    # noqa
        an = []
    for a in an:
        if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut") and a[2] in ("3s", "3p"):
            return "s" if a[2] == "3s" else "p"
    return None


def _num(sn):
    ws = sn.split()
    w = sa(ws[0].lower())
    if w in ("los", "las", "unos", "unas", "estos", "estas", "esos", "esas", "algunos", "algunas", "muchos", "muchas"):
        return "p"
    if w not in _DET and len(ws) == 1 and ws[0].endswith("s") and not ws[0][:1].isupper():
        return "p"
    return "s"


def _min(x):
    return x[:1].lower() + x[1:] if x and not (len(x) > 1 and x[1:2].isupper()) and x.split()[0].lower() in _DET else x


def _may(x):
    return x[:1].upper() + x[1:] if x else x


class Estado:
    """De qué se viene hablando."""

    def __init__(self):
        self.s = None            # último tema en singular
        self.p = None            # último tema en plural
        self.ult = None          # último tema, sea cual sea
        self.nombres = []        # nombres de la frase anterior (para los pronombres): [(texto, género, número)]
        self.es_lugar = False    # ¿lo último presentado es un sitio? («…es el edificio donde…»)

    def pon(self, sn):
        if not sn:
            return
        if _num(sn) == "p":
            self.p = sn
        else:
            self.s = sn
        self.ult = sn

    def para(self, n):
        t = self.p if n == "p" else self.s
        # solo temas generales («el contrabajo», «los osos»): de las personas con nombre se ocupa el núcleo, que sabe quién es quién
        return t if t and t.split()[0].lower() in _DET else None


def _sujeto(f):
    """(sujeto explícito al principio, resto) o (None, f). Mismo criterio que la lectura expositiva."""
    from . import exposicion as X
    try:
        sn, resto = X.sujeto(f)
    except Exception:                                    # noqa
        return None, f
    if sn and len(sn.split()) == 1 and sa(sn.lower()) in [sa(x) for x in _ADV_INI] + ["alli", "ahi", "aqui", "asi"]:
        return None, f                                   # «Entonces toman…»: un adverbio con mayúscula no es un sujeto
    return sn, resto


def _nombres(frase, sujeto=None):
    """Nombres con determinante (o en plural sin él) de una frase, para resolver un pronombre de la siguiente."""
    out = []
    t = frase
    if sujeto and t.startswith(sujeto):
        t = t[len(sujeto):]
    ws = re.findall(r"[A-Za-záéíóúñüÁÉÍÓÚÑ]+", t)
    for i, w in enumerate(ws):
        wl = sa(w.lower())
        if wl in ("el", "la", "los", "las", "un", "una", "unos", "unas", "sus", "su") and i + 1 < len(ws):
            n = ws[i + 1]
            if _fin3(n) and sa(n.lower()) not in ("garras", "alas", "cuerdas", "patas"):
                pass
            g = "f" if wl in ("la", "las", "una", "unas") else "m" if wl in ("el", "los", "un", "unos") else M.genero_sust(sa(M.singular(n.lower())))
            num = "p" if wl in ("los", "las", "unos", "unas", "sus") or (wl == "su" and False) else "s"
            art = {("m", "s"): "el", ("f", "s"): "la", ("m", "p"): "los", ("f", "p"): "las"}[(g, num)]
            out.append((f"{art} {n.lower()}", g, num))
        elif i > 0 and len(w) > 3 and w.endswith("s") and w[:1].islower() and not _fin3(w) and sa(ws[i - 1].lower()) in ("tienen", "tiene", "usan", "usa", "con", "llevan", "lleva", "de", "comen", "hacen"):
            sg = sa(M.singular(w.lower()))
            g = M.genero_sust(sg)
            out.append((f"{'las' if g == 'f' else 'los'} {w.lower()}", g, "p"))
    return out


def _parte_y(f):
    """Parte «A y V2…» en dos cuando V2 es un verbo conjugado que comparte el sujeto de A. Devuelve [f] si no hay nada que partir."""
    for m in re.finditer(r"(,\s+y\s+|\s+y\s+|,\s+pero\s+|\s+pero\s+|;\s+)", f):
        izq, der = f[:m.start()].strip(), f[m.end():].strip()
        ws = der.split()
        if len(ws) < 2 or len(izq.split()) < 2:
            continue
        k = 0
        if " ".join(ws[:2]).lower() in ("a veces", "a menudo", "casi siempre"):
            k = 2
        elif ws[0].lower() in ("también", "tambien", "después", "despues", "luego", "siempre", "nunca", "ya", "entonces"):
            k = 1
        cl = ""
        if k < len(ws) and ws[k].lower() in ("se", "no", "lo", "la", "los", "las", "le", "les"):
            cl = ws[k].lower(); k += 1
            if k < len(ws) and ws[k].lower() in ("se", "lo", "la", "los", "las", "le", "les") and cl == "no":
                cl += " " + ws[k].lower(); k += 1
        if k >= len(ws) or not _fin3(ws[k]) or ws[k].endswith(",") or k + 1 >= len(ws) or ws[k][:1].isupper():
            continue                                     # «…larga y fina, típica de Francia»: une adjetivos, no frases; «…y Lucía es…»: un nombre propio
        if cl in ("lo", "la", "los", "las"):
            sig = sa(ws[k + 1].lower().strip(","))
            if not (sig in ("en", "con", "a", "al", "de", "del", "por", "para", "sobre", "hasta", "desde", "dos", "tres", "cuatro", "cinco", "seis", "varios", "varias", "muchos", "muchas",
                            "el", "la", "los", "las", "un", "una", "unos", "unas", "muy", "bien", "mal", "despues", "luego", "siempre", "cada") or sig.endswith(("ar", "er", "ir"))):
                continue                                 # «…y la cola corta»: artículo y nombre, no pronombre y verbo
        wi = izq.split()
        if not cl and k == 0 and re.search(r"\b(?:es|son|era|eran|está|están)\b", izq) and sa(ws[0].lower())[-1:] in "aoe" and sa(wi[-1].lower().strip(","))[-1:] == sa(ws[0].lower())[-1:] \
                and not _fin3(wi[-1]):
            continue                                     # «…es duro y transparente que…»: dos adjetivos
        # la izquierda tiene que tener ya su verbo; si no, «y» une nombres, no frases
        if not any(_fin3(w) for w in izq.split()[1:] + izq.split()[:1]):
            continue
        if _fin3(wi[-1]) and len(wi) >= 2 and wi[-2].lower() not in ("se", "muy", "más", "mas", "tan", "es", "son") and k + 1 < len(ws) \
                and not any(_fin3(w) or w.lower() in ("es", "son", "era", "eran") for w in wi[:-1]):
            izq = izq + " " + " ".join(ws[k + 1:])       # «cargan y descargan las mercancías»: el complemento es de los dos verbos
        return [izq, der]
    return [f]


def _resuelve_clitico(der, izq):
    """«lo cortan en rodajas» con «…limpian el pescado»: el pronombre es el objeto de la primera mitad."""
    m = re.match(r"^((?:a veces|también|tambien|después|despues|luego|siempre)\s+)?(lo|la|los|las)\s+([a-záéíóúñü]+)\b(.*)$", der, re.I)
    if not m or not _fin3(m.group(3)):
        return der
    g, n = {"lo": ("m", "s"), "la": ("f", "s"), "los": ("m", "p"), "las": ("f", "p")}[m.group(2).lower()]
    cands = [x for x in _nombres(izq, _sujeto(izq)[0]) if x[1] == g and x[2] == n]
    if not cands:
        return der
    if re.match(r"^\s*(?:dos|tres|cuatro|cinco|seis|varios|varias|muchos|muchas|los|las|el|la|un|una|unos|unas)\s+[a-záéíóúñü]+\s*$", m.group(4)):
        return der                                       # «la sujetan dos bomberos»: lo que sigue al verbo es el sujeto; se resuelve aparte
    return f"{m.group(1) or ''}{m.group(3)} {cands[-1][0]}{m.group(4)}".strip()


def _adv_inicial(f):
    """(adverbio inicial o '', resto)."""
    fl = f.lower()
    for a in sorted(_ADV_INI, key=len, reverse=True):
        if fl.startswith(a + " ") or fl.startswith(a + ", "):
            return f[:len(a)], f[len(a):].lstrip(" ,")
    return "", f


_INI_COMP = ("en", "durante", "con", "sin", "desde", "hoy", "antiguamente", "antes", "después", "despues", "luego", "primero", "allí", "alli")


def _sujeto_interno(f):
    """«En invierno las abejas no salen…», «Antiguamente el correo viajaba…»: el sujeto va tras el complemento. Es el grupo con
    artículo que queda justo delante del primer verbo conjugado."""
    ws = f.split()
    if len(ws) < 4 or ws[0].lower().strip(",") not in _INI_COMP:
        return None
    v = None
    for i in range(1, len(ws)):
        ant = ws[i - 1].lower().strip(",")
        if _fin3(ws[i]) and ant not in _DET and ant not in ("de", "del", "al", "a", "en", "con", "por", "para", "sobre", "sin", "su", "sus"):
            v = i
            break
    if v is None:
        return None
    j = v
    while j > 0 and ws[j - 1].lower() in ("se", "no", "ya", "también", "tambien"):
        j -= 1
    k = j - 1
    while k > 0 and j - k <= 3 and ws[k].lower() not in ("el", "la", "los", "las"):
        k -= 1
    if k <= 0 or ws[k].lower() not in ("el", "la", "los", "las") or j - k < 2:
        return None
    if ws[k - 1].lower().strip(",") in ("de", "en", "con", "por", "para", "sobre", "a", "sin", "desde", "durante"):
        return None                                      # ese grupo es parte del complemento («en la fábrica»)
    return _may(" ".join(ws[k:j]))


def _pon_sujeto(f, est):
    """Devuelve (frase con sujeto, tema usado) o (f, None) si no hace falta o no se sabe."""
    sn, _ = _sujeto(f)
    if sn:
        return f, None
    adv, resto = _adv_inicial(f)
    ws = resto.split()
    if not ws:
        return f, None
    w0 = ws[0].lower()
    cola = "" if (not adv or adv.lower() in _QUITA) else " " + adv.lower()
    # «Debajo hay dos piedras»: el lugar es respecto a lo último nombrado
    if _activo("lugar") and not adv:
        for l in _LUGAR:
            if resto.lower().startswith(l + " hay ") and est.ult:
                de = _min(est.ult)
                return re.sub(r"\bde el\b", "del", f"{_may(l)} de {de} hay {resto[len(l) + 5:]}"), est.ult
    # pronombre tras preposición: «Con ellas trepan…», «…contra ellos»
    if _activo("pron"):
        mp = re.match(r"^(Con|En|De|Por|Para|Sobre|Contra|Sin|Desde)\s+(ellos|ellas|él|ella|eso|esto|ello)\s+(.+)$", resto)
        if mp:
            g, n = {"ellos": ("m", "p"), "ellas": ("f", "p"), "él": ("m", "s"), "ella": ("f", "s")}.get(mp.group(2).lower(), (None, None))
            cands = [x for x in est.nombres if g is None or (x[1] == g and x[2] == n)]
            ws2 = mp.group(3).split()
            k = 1 if ws2 and ws2[0].lower() in ("se", "no") else 0
            nv = _fin3(ws2[k]) if k < len(ws2) else None
            if cands and nv and est.para(nv):
                t = est.para(nv)
                return f"{t} {mp.group(3)} {mp.group(1).lower()} {cands[-1][0]}{cola}", t
    if not _activo("sujeto"):
        return f, None
    k = 0
    pre = ""
    if w0 in ("solo", "casi", "apenas", "sólo"):
        return f, None                                   # «Solo vive en la cima…»: el «solo» cambia el sentido; lo lee la lectura de siempre
    if w0 in ("ya", "todavía", "todavia", "aún", "aun", "ahora"):
        return f, None                                   # «Ya está cerrada»: es un cambio de estado; lo lleva el núcleo
    if w0 in ("se", "no"):
        pre = ws[0].lower() + " "
        k = 1
        if k < len(ws) and ws[k].lower() in ("se", "lo", "la", "los", "las", "le", "les") and w0 == "no":
            pre += ws[k].lower() + " "; k += 1
    if k >= len(ws):
        return f, None
    n = _fin3(ws[k])
    if not n or ws[k].lower() == "hay":
        return f, None
    if ws[k].lower() in ("es", "era", "fue", "son", "eran", "fueron") and k + 1 < len(ws) and ws[k + 1].lower() in ("un", "una", "unos", "unas"):
        return f, None                                   # «Era un trabajo muy solitario»: puede hablar del tema o de lo que se acaba de contar; no se adivina
    if w0 == "se" and re.match(r"^se\s+llama(?:n|ba|ban)?\b", resto.lower()):
        return f, None                                   # «Se llama Noa»: poner nombre es cosa del núcleo
    if w0 == "se" and adv.lower() in ("antes", "antiguamente"):
        return f, None                                   # «Antes se escribía sobre pergamino»: impersonal, no habla del tema
    if w0 == "se" and re.match(r"^se\s+(?:dice|llaman?|puede|pueden|debe|deben|necesita|sabe|cree)\b", resto.lower()) and re.search(r"\bque\b|\b[a-záéíóúñü]+r\b", resto):
        return f, None                                   # impersonal de verdad: «se dice que…», «se puede comer»
    if w0 == "se" and k + 1 < len(ws) and ws[k + 1].lower() in ("el", "la", "los", "las", "un", "una", "unos", "unas") and not re.search(r"\b(?:con|en|de|a|por|para|sobre)\b", " ".join(ws[k + 1:k + 2])):
        return f, None                                   # «Se aprieta el papel…»: el sujeto va detrás del verbo
    t = est.para(n)
    if not t:
        return f, None
    resto_v = " ".join(ws[k:])
    return f"{t} {pre}{resto_v[:1].lower() + resto_v[1:]}{cola}", t


def _parte_relativa(f):
    """«…con arena, que se calienta en un horno» -> «…con arena» + «La arena se calienta en un horno». Solo la explicativa (con coma) y
    solo si lo que sigue a «que» es un verbo; «…, que es/son…» es una definición y de ella se ocupa la lectura expositiva."""
    m = re.match(r"^(.*?\b)((?:el|la|los|las|un|una|unos|unas)\s+)?([a-záéíóúñü]+),\s+que\s+((?:se\s+|no\s+)?[a-záéíóúñü]+\b.*)$", f)
    if not m:
        return [f]
    resto = m.group(4)
    ws = resto.split()
    k = 1 if ws[0].lower() in ("se", "no") else 0
    if k >= len(ws) or not _fin3(ws[k]) or ws[k].lower() in ("es", "son", "era", "eran", "fue") or len(ws) - k < 2:
        return [f]
    n = m.group(3)
    if _fin3(n) and not m.group(2):
        return [f]
    n_izq = next((_fin3(w) for w in m.group(1).split() if _fin3(w)), None)
    if ws[0].lower() != "se" and n_izq == _fin3(ws[k]):
        return [f]                                       # «…viven en tiendas, que montan cada noche»: «que» puede ser lo montado, no quien monta
    pl = _fin3(ws[k]) == "p"
    if m.group(2):
        det = m.group(2).strip().lower()
        art = {"un": "el", "una": "la", "unos": "los", "unas": "las"}.get(det, det)
    else:
        g = M.genero_sust(sa(M.singular(n) if pl else n))
        art = ("las" if g == "f" else "los") if pl else ("la" if g == "f" else "el")
    if (art in ("los", "las")) != pl:
        return [f]                                       # el verbo no concuerda con ese nombre: el antecedente es otro
    return [(m.group(1) + (m.group(2) or "") + n).strip(), f"{_may(art)} {n} {resto}"]


def prepara(f, est):
    """[(frase lista para leer, tema añadido o None, texto original de esa parte)] y actualiza el estado."""
    f = f.strip()
    punto = "." if f.endswith(".") else ""
    cuerpo = f.rstrip(".").strip()
    if not cuerpo or "nada" in os.environ.get("LCM_DISCURSO", ""):
        return [(f, None, f)]
    lugar = None
    m_alli = re.match(r"^(?:Allí|Ahí|Allá),?\s+(.+)$", cuerpo)
    if m_alli and est.ult and est.es_lugar and _activo("lugar") and est.ult.split()[0].lower() in _DET:
        lugar, cuerpo = _min(est.ult), _may(m_alli.group(1))      # «Allí duermen…»: allí es el sitio que se acaba de presentar
    m_cu = re.match(r"^Cuando\s+(.+)$", cuerpo)
    if m_cu and _activo("sujeto"):
        nuevo = _cuando(m_cu.group(1), est)
        if nuevo:
            cuerpo = nuevo                               # «Cuando suena la alarma bajan por una barra» -> «Los bomberos bajan por una barra cuando suena la alarma»
    if re.match(r"^(?:Allí|Ahí|Allá|Cuando|Si|Por eso|Para)\b", cuerpo):
        partes = [cuerpo]                                # de estas formas ya se ocupa la lectura expositiva
        intacta = True
    else:
        partes = _parte_y(cuerpo) if _activo("y") else [cuerpo]
        intacta = False
        if _activo("rel"):
            partes = [q for p_ in partes for q in _parte_relativa(p_)]
    out = []
    suj0 = None
    adv0 = _adv_inicial(partes[0])[0] if partes else ""
    if adv0.lower() not in ("antiguamente", "hoy", "antes", "siempre", "a veces", "normalmente"):
        adv0 = ""
    for i, p in enumerate(partes):
        orig = p
        if intacta:
            out.append((p + punto, None, orig + punto))
            continue
        if i > 0:
            if _activo("pron"):
                p = _resuelve_clitico(p, partes[0])
            p = _may(p)
        sn, _ = _sujeto(p)
        tema = None
        if not sn:
            if i > 0 and suj0:
                adv, resto = _adv_inicial(p)
                adv = adv or adv0                        # «Antiguamente… y tardaba semanas»: el «antiguamente» vale para las dos mitades
                cola = "" if (not adv or adv.lower() in _QUITA) else " " + adv.lower()
                p, tema = f"{suj0} {_min(resto) if resto.split()[0].lower() in _DET else resto[:1].lower() + resto[1:]}{cola}", suj0
            else:
                p, tema = _pon_sujeto(p, est)
        if i > 0 and suj0:
            mo = re.match(r"^(lo|la|los|las)\s+([a-záéíóúñü]+)\s+((?:dos|tres|cuatro|cinco|seis|varios|varias|muchos|muchas|los|las|el|la|un|una|unos|unas)\s+[a-záéíóúñü]+)$", orig, re.I)
            if mo and _fin3(mo.group(2)) and _activo("pron"):
                gs = "f" if suj0.split()[0].lower() in ("la", "las", "una", "unas") else "m"
                ns = _num(suj0)
                if {"lo": ("m", "s"), "la": ("f", "s"), "los": ("m", "p"), "las": ("f", "p")}[mo.group(1).lower()] == (gs, ns):
                    p, tema = f"{_may(mo.group(3))} {mo.group(2)} {_min(suj0)}", suj0     # «Dos bomberos sujetan la manguera»
        if i == 0:
            suj0 = _sujeto(p)[0] or _sujeto_interno(p)
            if not suj0 and re.match(r"^(?:Su|Sus)\s+[a-záéíóúñü]+", p):
                wsu = p.split()
                kv = next((j for j in range(1, len(wsu)) if _fin3(wsu[j]) or wsu[j].lower() in ("es", "son")), None)
                suj0 = " ".join(wsu[:kv]) if kv and kv <= 4 else None
            # «Las crías se llaman ballenatos y maman…»: lo que sigue se dice de los ballenatos
            mn = re.match(r"^(Los|Las|El|La)\s+.+?\s+se\s+llama(n)?\s+([a-záéíóúñü]+)$", p)
            if mn and len(partes) > 1:
                pl = bool(mn.group(2))
                x = mn.group(3)
                g = M.genero_sust(sa(M.singular(x) if pl else x))
                suj0 = f"{('Las' if g == 'f' else 'Los') if pl else ('La' if g == 'f' else 'El')} {x}"
        if lugar and not re.search(r"\b(?:en|sobre|dentro de|junto a)\s+(?:el|la|los|las|un|una)\b", p) and _sujeto(p)[0] and sa(_sujeto(p)[0].lower()) != sa(lugar.lower()):
            p = re.sub(r"\ben el\b", "en el", f"{p} en {lugar}")
            tema = tema or lugar
        out.append((p + punto, tema, orig + punto))
    # estado para la frase siguiente
    primera = out[0][0].rstrip(".")
    sn, _ = _sujeto(primera)
    mn = re.match(r"^(Los|Las|El|La)\s+.+?\s+se\s+llama(n|ba|ban)?\s+([a-záéíóúñü]+)$", partes[0])
    if mn and not intacta:
        pl = mn.group(2) in ("n", "ban")
        x = mn.group(3)
        g = M.genero_sust(sa(M.singular(x) if pl else x))
        est.pon(f"{('Las' if g == 'f' else 'Los') if pl else ('La' if g == 'f' else 'El')} {x}")
    elif sn and not re.match(r"^(?:Su|Sus)\b", sn):
        est.pon(sn)
    elif not sn:
        # «En invierno las abejas no salen…»: el sujeto va tras el complemento
        si_ = _sujeto_interno(primera)
        if si_:
            est.pon(si_)
    mh = re.search(r"\bhay\s+(?:(?:un|una|unos|unas|dos|tres|cuatro|cinco|seis|varios|varias|muchos|muchas)\s+)?([a-záéíóúñü]+)(?:\s+[a-záéíóúñü]+)?(?:,?\s+llamad[oa]s?\s+([a-záéíóúñü]+))?", cuerpo)
    if mh and not intacta:
        x = mh.group(2) or mh.group(1)
        if len(x) > 3 and not _fin3(x):
            pl = x.endswith("s")
            g = M.genero_sust(sa(M.singular(x) if pl else x))
            est.pon(f"{('Las' if g == 'f' else 'Los') if pl else ('La' if g == 'f' else 'El')} {x}")
    est.nombres = _nombres(cuerpo, sn) or est.nombres
    est.es_lugar = bool(re.search(r"\bdonde\b|\b(?:es|son|era)\s+(?:el|la|un|una)\s+(?:lugar|edificio|sitio|sala|zona|local|taller|tienda|recinto|casa|parque|espacio|habitacion|nave|planta)\b", sa(f.lower()))) \
        or (est.es_lugar and not sn)
    return out


def _cuando(resto, est):
    """«Cuando A, V…» o «Cuando A V…» con la principal sin sujeto: se le pone el tema. None si no procede."""
    if "," in resto:
        sub, pri = [x.strip() for x in resto.split(",", 1)]
    else:
        ws = resto.split()
        v1 = next((i for i, w in enumerate(ws) if _fin3(w) and (i == 0 or ws[i - 1].lower() not in _DET)), None)
        if v1 is None:
            return None
        v2 = next((i for i in range(v1 + 2, len(ws)) if _fin3(ws[i]) and ws[i - 1].lower() not in _DET + ("de", "a", "en", "con", "por", "para", "que", "se", "no")), None)
        if v2 is None:
            return None
        sub, pri = " ".join(ws[:v2]), " ".join(ws[v2:])
    wp = pri.split()
    if len(wp) < 2:
        return None
    k = 1 if wp[0].lower() in ("se", "no") else 0
    n = _fin3(wp[k]) if k < len(wp) else None
    if not n or wp[k].lower() in ("hay", "es", "son"):
        return None
    if k + 1 < len(wp) and wp[k + 1].lower() in ("el", "la", "los", "las", "un", "una", "unos", "unas") and len(wp) - k <= 4:
        return None                                      # «…bajan las barreras»: el sujeto va detrás del verbo
    ms = re.match(r"^((?:el|la|los|las|un|una|unos|unas)\s+[a-záéíóúñü]+)\s+(?:se\s+|no\s+)?([a-záéíóúñü]+)", sub, re.I)
    if ms and _fin3(ms.group(2)):
        if _fin3(ms.group(2)) != n:
            t = est.para(n)                              # «Cuando hay peligro golpean…»: otro número, luego es el tema
        else:
            return None                                  # «Cuando un nurbo ve un peligro, silba»: el sujeto es el de la subordinada; lo lee bien la lectura de siempre
    else:
        t = est.para(n)
    if not t:
        return None
    return f"{t} {pri[:1].lower() + pri[1:]} cuando {sub}"
