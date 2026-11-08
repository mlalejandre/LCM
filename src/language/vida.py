"""parche-129: hechos de personas dichos en la conversacion (nacimiento, edad, cumpleanos) y mensajes «afirmacion + pregunta».

La memoria de la conversacion guarda «Marta nacio el 12 de octubre de 1982» como un hecho con fecha (`when_abs`). Este modulo contesta
con esa fecha («¿que dia nacio Marta?», «¿que edad tiene hoy?», «¿cuando cumple anos?») sin depender de la forma exacta de la frase, y
separa un mensaje que trae a la vez una afirmacion y una pregunta («Marta nacio el 12 de octubre de 1982 que edad tiene hoy?»).
Nada de esto sabe de textos concretos: solo de fechas, nombres y de que un hecho dicho por la persona no es lo que dice un texto leido."""
import datetime
import re
from typing import Callable, Dict, List, Optional, Set, Tuple

from src.language.lexicon import norm

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_SIN_NOMBRE = {"el", "la", "los", "las", "un", "una", "de", "del", "mi", "mis", "su", "sus", "tu", "tus", "y", "e", "se", "me", "te", "lo", "le", "que", "hoy", "ahora", "ya",
               "actualmente", "exactamente", "entonces", "pues", "tambien", "al", "a", "en", "con", "por", "para", "esta", "este", "ese", "esa", "dia", "fecha", "ano", "anos",
               "edad", "mes", "cumple", "cumplio", "cumpleanos", "nacio", "nace", "tiene", "tenia", "tendra", "cuando", "cuantos", "cual", "es", "fue", "era"}
_ADVERBIOS = re.compile(r"\b(?:hoy en dia|a dia de hoy|en la actualidad|actualmente|hoy|ahora mismo|ahora|ya|este ano|exactamente|entonces)\b")
_NACER = ("NACER", "NACER_EN", "NACER_EL")
_MORIR = ("MORIR", "FALLECER", "MORIR_EN")


def hoy_de(mem=None) -> datetime.date:
    h = getattr(mem, "today", None)
    if isinstance(h, datetime.datetime):
        return h.date()
    return h if isinstance(h, datetime.date) else datetime.date.today()


def _intervalo(s: Optional[str]) -> Optional[Tuple[datetime.date, datetime.date]]:
    if not s or "/" not in s:
        return None
    try:
        a, b = s.split("/", 1)
        return datetime.date.fromisoformat(a[:10]), datetime.date.fromisoformat(b[:10])
    except (ValueError, TypeError):
        return None


def _fecha_txt(iv: Tuple[datetime.date, datetime.date]) -> str:
    a, b = iv
    if a == b:
        return f"el {a.day} de {MESES[a.month - 1]} de {a.year}"
    if a.year == b.year and a.month == 1 and a.day == 1 and b.month == 12 and b.day == 31:
        return f"en {a.year}"
    if a.year == b.year and a.month == b.month and a.day == 1 and (b + datetime.timedelta(days=1)).day == 1:
        return f"en {MESES[a.month - 1]} de {a.year}"
    return f"entre el {a.day} de {MESES[a.month - 1]} de {a.year} y el {b.day} de {MESES[b.month - 1]} de {b.year}"


def _anyos(nac: datetime.date, ref: datetime.date) -> int:
    return ref.year - nac.year - ((ref.month, ref.day) < (nac.month, nac.day))


def _nombre_disp(mem, clave: str) -> str:
    d = (getattr(mem, "display", None) or {}).get(clave)
    if d:
        return d
    return " ".join(w.capitalize() for w in clave.split("_"))


def _toks(s: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9]+", norm(s)) if w not in _SIN_NOMBRE]


def _frases_de_texto(mem) -> Set[str]:
    """Frases de los textos leidos: un hecho cuya fuente es una de ellas lo dijo un texto, no la persona en la conversacion."""
    textos = getattr(mem, "textos", None) or []
    cache = getattr(mem, "_vida_frases", None)
    if cache is not None and cache[0] == len(textos):
        return cache[1]
    fr = {(x.get("t") or "").strip() for x in textos if isinstance(x, dict)}
    try:
        mem._vida_frases = (len(textos), fr)
    except Exception:                                                              # noqa
        pass
    return fr


def _de_conversacion(mem, f: dict) -> bool:
    return not f.get("archived") and (f.get("source") or "").strip() not in _frases_de_texto(mem)


def _sujetos_hechos(mem) -> Dict[str, Set[str]]:
    """clave del sujeto -> palabras de su nombre, para los hechos que dijo la persona en la conversacion."""
    out: Dict[str, Set[str]] = {}
    for f in getattr(mem, "facts", None) or []:
        if not _de_conversacion(mem, f):
            continue
        s = f.get("s", "")
        if s and s not in out:
            out[s] = {w for w in re.findall(r"[a-z0-9]+", norm(s.replace("_", " "))) if w not in _SIN_NOMBRE}
    return out


def entidades_de_conversacion(mem, raw: str, en_texto: Optional[Callable[[str], bool]] = None) -> List[str]:
    """Palabras de la pregunta que son el nombre de alguien del que solo se habla en la conversacion (hay hechos suyos y ningun texto leido lo nombra)."""
    if not getattr(mem, "facts", None):
        return []
    suj = _sujetos_hechos(mem)
    todas: Set[str] = set()
    for ws in suj.values():
        todas |= ws
    out = []
    for w in _toks(raw):
        if len(w) >= 3 and w in todas and not (en_texto and en_texto(w)):
            out.append(w)
    return out


def _buscar(mem, nombre: str, preds: Tuple[str, ...]) -> List[Tuple[str, dict]]:
    """Hechos (sujeto, hecho) con fecha cuyo sujeto se llama como `nombre` (todas sus palabras estan en el nombre del sujeto)."""
    nt = set(_toks(nombre))
    if not nt:
        return []
    res: Dict[str, dict] = {}
    for f in getattr(mem, "facts", None) or []:
        if not _de_conversacion(mem, f) or f.get("neg") or f.get("p") not in preds or not _intervalo(f.get("when_abs")):
            continue
        ws = {w for w in re.findall(r"[a-z0-9]+", norm(f["s"].replace("_", " "))) if w not in _SIN_NOMBRE}
        if nt <= ws:
            prev = res.get(f["s"])
            if prev is None or f.get("t", 0) >= prev.get("t", 0):
                res[f["s"]] = f
    return sorted(res.items(), key=lambda kv: -kv[1].get("t", 0))


def _conocido(mem, nombre: str) -> List[str]:
    nt = set(_toks(nombre))
    if not nt:
        return []
    return [s for s, ws in _sujetos_hechos(mem).items() if nt <= ws]


_PAT_EDAD = [re.compile(p) for p in (
    r"^(?:y )?(?:que|cual es la) edad (?:tiene|tenia|tendra|tendria|cumple|cumplio|lleva)(?: ya)?\s*(?P<n>.*)$",
    r"^(?:y )?(?:cuantos|cuantas) anos (?:tiene|tenia|tendra|tendria|cumple|cumplio|lleva|llevaba)(?: ya)?\s*(?P<n>.*)$",
    r"^(?:y )?de que edad es\s*(?P<n>.*)$",
    r"^(?:y )?que edad (?:tiene|tenia) (?P<n>.+?) (?:en la actualidad|ahora)$",
)]
_PAT_FECHA = [
    ("fecha", re.compile(r"^(?:y )?(?:que dia|que fecha|en que dia|en que fecha|cual fue la fecha en que|cuando|que dia exactamente|a que dia)\s+(?:nacio|nace|vino al mundo|fue su nacimiento)\s*(?P<n>.*)$")),
    ("fecha", re.compile(r"^(?:y )?(?:cual es|cual fue) la fecha de nacimiento de\s+(?P<n>.+)$")),
    ("anyo", re.compile(r"^(?:y )?(?:en que ano|que ano|de que ano)\s+(?:nacio|nace|vino al mundo)\s*(?P<n>.*)$")),
    ("mes", re.compile(r"^(?:y )?(?:en que mes|que mes)\s+(?:nacio|nace|vino al mundo)\s*(?P<n>.*)$")),
    ("cumple", re.compile(r"^(?:y )?(?:cuando|que dia|en que fecha|en que dia)\s+(?:cumple anos|cumple|es el cumpleanos de|es su cumpleanos|es el cumple de)\s*(?P<n>.*)$")),
    ("cumple", re.compile(r"^(?:y )?(?:cuando|que dia) cumple\s+(?P<n>.+?)\s+anos$")),
    ("cumple", re.compile(r"^(?:y )?cuando es (?:el )?cumpleanos de\s+(?P<n>.+)$")),
    ("hace", re.compile(r"^(?:y )?cuantos anos hace que nacio\s*(?P<n>.*)$")),
]


def _hechos_q(raw: str) -> Optional[Tuple[str, str]]:
    q = norm(raw)
    q = re.sub(r"[¿?¡!.,;:]", " ", q)
    q = _ADVERBIOS.sub(" ", q)
    q = re.sub(r"\s+", " ", q).strip()
    if not q:
        return None
    for rx in _PAT_EDAD:
        m = rx.match(q)
        if m:
            return "edad", m.group("n").strip()
    for tipo, rx in _PAT_FECHA:
        m = rx.match(q)
        if m:
            return tipo, m.group("n").strip()
    return None


def _responder_uno(mem, sujeto: str, hecho: dict, tipo: str, hoy: datetime.date) -> Optional[str]:
    iv = _intervalo(hecho.get("when_abs"))
    if not iv:
        return None
    nom = _cap1(_nombre_disp(mem, sujeto))
    a, b = iv
    nac_txt = _fecha_txt(iv)
    fin = _buscar(mem, sujeto.replace("_", " "), _MORIR)
    fin = [h for s_, h in fin if s_ == sujeto]
    fin_iv = _intervalo(fin[0].get("when_abs")) if fin else None
    if tipo == "fecha":
        return f"{nom} nació {nac_txt}."
    if tipo == "anyo":
        return f"{nom} nació en {a.year}." if a.year == b.year else f"{nom} nació entre {a.year} y {b.year}."
    if tipo == "mes":
        if a.year == b.year and a.month == b.month or (a.day == 1 and b.month == a.month):
            return f"{nom} nació en {MESES[a.month - 1]} de {a.year}."
        return f"De {nom} solo sé que nació {nac_txt}: no sé en qué mes."
    if tipo == "cumple":
        if a != b:
            return f"De {nom} solo sé que nació {nac_txt}: no sé qué día cumple años."
        try:
            prox = datetime.date(hoy.year, a.month, a.day)
        except ValueError:                                                          # 29 de febrero
            prox = datetime.date(hoy.year, 3, 1)
        if prox < hoy:
            try:
                prox = datetime.date(hoy.year + 1, a.month, a.day)
            except ValueError:
                prox = datetime.date(hoy.year + 1, 3, 1)
        n = (prox - hoy).days
        cumple = f"{prox.day} de {MESES[prox.month - 1]}"
        cuando = "hoy" if n == 0 else ("mañana" if n == 1 else f"dentro de {n} días")
        edad = _anyos(a, prox)
        return f"{nom} cumple años el {cumple} (nació el {a.day} de {MESES[a.month - 1]} de {a.year}); el próximo será {cuando}, y cumplirá {edad} años."
    if tipo == "hace":
        n = _anyos(a, hoy)
        return f"Hace {n} años (nació {nac_txt})." if a == b else f"Hace unos {n} años (nació {nac_txt})."
    # edad
    if fin_iv:
        f0, f1 = fin_iv
        e0, e1 = _anyos(b, f0), _anyos(a, f1)
        n = f"{e0}" if e0 == e1 else f"entre {e0} y {e1}"
        return f"{nom} murió con {n} años (nació {nac_txt} y murió {_fecha_txt(fin_iv)})."
    e_min, e_max = _anyos(b, hoy), _anyos(a, hoy)                                    # nace lo mas tarde (b) -> la menor edad
    if e_min < 0:
        return f"{nom} aún no ha nacido según lo que sé (nacerá {nac_txt})."
    if e_min == e_max:
        return f"{nom} tiene {e_min} año{'s' if e_min != 1 else ''} (nació {nac_txt})."
    return f"{nom} tiene entre {e_min} y {e_max} años (solo sé que nació {nac_txt})."


def responder(raw: str, mem, ctx: Optional[str] = None, en_texto: Optional[Callable[[str], bool]] = None) -> Optional[str]:
    """Contesta preguntas de nacimiento / edad / cumpleanos sobre alguien que la persona ha mencionado en la conversacion. None si no es de esa familia o no se sabe de quien."""
    if not getattr(mem, "facts", None):
        return None
    fam = _hechos_q(raw)
    if not fam:
        return None
    tipo, nombre = fam
    nombre = nombre.strip()
    if not _toks(nombre) and ctx:
        nombre = ctx.replace("_", " ")
    elif not _toks(nombre):
        return None
    hoy = hoy_de(mem)
    hits = _buscar(mem, nombre, _NACER)
    if not hits:
        conocidos = _conocido(mem, nombre)
        if conocidos:
            nom = _cap1(_nombre_disp(mem, conocidos[0]))
            return f"Sé cosas de {nom}, pero no sé cuándo nació, así que no puedo contestar a eso."
        return None
    outs = []
    for s, f in hits[:3]:
        r = _responder_uno(mem, s, f, tipo, hoy)
        if r:
            outs.append(r)
    return " ".join(outs) if outs else None


# ---------------------------------------------------------------------------------------------------- afirmacion + pregunta en un mensaje
_WH = {"cuando", "donde", "quien", "quienes", "cuanto", "cuanta", "cuantos", "cuantas", "cual", "cuales", "como", "que", "adonde"}
_NOMBRES_Q = {"edad", "dia", "fecha", "ano", "mes", "hora", "nombre", "apellido", "profesion", "pais", "ciudad", "lugar", "tiempo", "cumpleanos", "significa", "es", "son", "hay", "opinas",
              "piensas", "sabes", "sabemos", "tal", "pasa"}


_CONDICIONAL = {"si", "supongamos", "supon", "suponiendo", "suponte", "imagina", "imaginemos", "cuando", "mientras", "aunque", "como", "ojala", "quiza", "quizas", "por", "segun"}


def partir(raw: str) -> Optional[Tuple[str, str]]:
    """«Marta nacio el 12 de octubre de 1982 que edad tiene hoy?» -> («Marta nacio el 12 de octubre de 1982», «que edad tiene hoy»).
    Solo si el mensaje acaba en pregunta, no empieza como pregunta y la parte de la izquierda parece una frase completa."""
    t = raw.strip()
    if not t.endswith("?") or t.startswith("¿") or len(t) > 220:
        return None
    ms = list(re.finditer(r"[\wÁÉÍÓÚÜÑáéíóúüñ]+", t))
    if len(ms) < 6:
        return None
    for k in range(len(ms) - 2, 2, -1):                                                # empieza por el ultimo interrogativo: la pregunta es lo ultimo
        w = ms[k].group(0)
        wn = norm(w)
        if wn not in _WH:
            continue
        izq = t[:ms[k].start()].rstrip()
        if izq.endswith("¿"):                                                          # «Yamal nacio en 2007, ¿cuantos anos tiene?»
            izq = izq[:-1].rstrip()
        der = t[ms[k].start():].strip()
        sep = izq[-1:] in ",;.:" if izq else False
        izq = izq.rstrip(",;:. ").strip()
        if "?" in izq or "¿" in izq or len(izq.split()) < 3:
            continue
        if norm(izq.split()[0]) in _WH or norm(izq.split()[0]) in _CONDICIONAL or re.search(r"\bhoy es\b|\bestamos a\b|\bhoy estamos\b", norm(izq)):
            continue                                                                   # «Si hoy es 9 de junio, ¿que dia sera pasado manana?» es un calculo, no una afirmacion
        acento = w != wn and any(c in w for c in "áéíóú")
        sig = norm(ms[k + 1].group(0)) if k + 1 < len(ms) else ""
        ok = acento or sep or bool(re.search(r"\d", izq)) or (wn == "que" and sig in _NOMBRES_Q)
        if wn == "que" and not (acento or sep) and sig not in _NOMBRES_Q:
            ok = False
        if not ok:
            continue
        if wn in ("que", "como", "cuando", "donde") and len(der.split()) < 2:
            continue
        return izq, der.rstrip("? ").strip()
    return None


# ---------------------------------------------------------------------------------------------------- «¿puedes cantar?», «¿puedes contarme un cuento?»
_CAP = re.compile(r"^(?:y |oye |por favor )*(?:puedes|podrias|sabes|sabrias|eres capaz de|serias capaz de|te atreves a)\s+([a-z]+(?:ar|er|ir)(?:me|te|le|nos|se)?(?:lo|la|los|las)?)\b(.*)$")
_INTERROGATIVO = re.compile(r"\b(?:cuando|donde|quien|quienes|cuanto|cuanta|cuantos|cuantas|cual|cuales|como|que|por que|si)\b")


def pide_capacidad(raw: str) -> bool:
    """«¿Puedes cantar?», «puedes contarme un cuento»: se le pide a quien contesta que haga algo (no una pregunta sobre lo leido). Si lleva una pregunta dentro («puedes decirme cuando nacio X») no cuenta."""
    q = re.sub(r"[¿?¡!.,;:]", " ", norm(raw or ""))
    q = re.sub(r"\s+", " ", q).strip()
    m = _CAP.match(q)
    if not m:
        return False
    return not _INTERROGATIVO.search(m.group(2))


MENSAJE_CAPACIDAD = ("Eso no sé hacerlo. Puedo aprender lo que me cuentes, contestar sobre ello y sobre los textos que he leído, razonar con reglas, "
                     "calcular fechas y operaciones y decirte la hora.")


# ---------------------------------------------------------------------------------------------------- «¿quien es mayor, Marta o Yamal?», «¿Marta es mayor que Pedro?»
_N = r"(?P<{0}>[a-z0-9][a-z0-9 ]*?)"
_COMP = r"(?P<c>mayor|menor|mas joven|mas jovenes|mas viejo|mas vieja|mas mayor|mas pequeno|mas pequena|mas antiguo|mas antigua)"
_PAT_CMP = [
    ("quien", re.compile(r"^(?:y )?(?:quien|cual) (?:de los dos |de ellos |de entre ellos |de estos dos )?(?:es|sera|fue|era) (?:el |la )?" + _COMP + r"(?: de los dos| de ellos| de entre ellos)?\s*(?:entre )?" + _N.format("a") + r" (?:o|y) " + _N.format("b") + r"$")),
    ("cuando", re.compile(r"^(?:y )?(?:quien|cual) (?:de los dos |de ellos )?nacio (?P<o>antes|primero|despues|mas tarde|ultimo)(?: de los dos| de ellos)?\s*(?:entre )?" + _N.format("a") + r" (?:o|y) " + _N.format("b") + r"$")),
    ("si_no", re.compile(r"^(?:y )?(?:es |sera |fue |era )?" + _N.format("a") + r" (?:es |sera |fue |era )?" + _COMP + r" que " + _N.format("b") + r"$")),
    ("dif", re.compile(r"^(?:y )?(?:cuantos anos|cuanta diferencia de edad|que diferencia de edad|cuantos anos de diferencia)\s+(?:hay |tienen |se llevan |les separan )?(?:de diferencia )?(?:entre )?" + _N.format("a") + r" (?:y|e|o|con) " + _N.format("b") + r"$")),
    ("dif", re.compile(r"^(?:y )?cuantos anos (?:le lleva|lleva) " + _N.format("a") + r" a " + _N.format("b") + r"$")),
]


def _fecha_ymd(y: int, m: Optional[int], d: Optional[int]) -> str:
    if m and d:
        return f"el {d} de {MESES[m - 1]} de {y}"
    if m:
        return f"en {MESES[m - 1]} de {y}"
    return f"en {y}"


def _de_hecho(mem, nombre: str, en_texto, resolver_texto) -> Tuple[Optional[str], Optional[Tuple[int, Optional[int], Optional[int]]], bool]:
    """(nombre para mostrar, (y, m, d) del nacimiento o None, se conoce a la persona)."""
    nt = _toks(nombre)
    if not nt:
        return None, None, False
    hits = _buscar(mem, nombre, _NACER)
    if hits:
        s, f = hits[0]
        a, b = _intervalo(f["when_abs"])
        if a == b:
            return _cap1(_nombre_disp(mem, s)), (a.year, a.month, a.day), True
        if a.month == 1 and a.day == 1 and b.month == 12 and b.day == 31:
            return _cap1(_nombre_disp(mem, s)), (a.year, None, None), True
        if a.year == b.year and a.month == b.month:
            return _cap1(_nombre_disp(mem, s)), (a.year, a.month, None), True
        return _cap1(_nombre_disp(mem, s)), (a.year, None, None), True
    if resolver_texto is not None:
        r = resolver_texto(nombre)
        if r:
            return r[0], r[1], True
    cc = _conocido(mem, nombre)
    if cc:
        return _cap1(_nombre_disp(mem, cc[0])), None, True
    if False:
        r = resolver_texto(nombre)
        if r:
            return r[0], r[1], True
    return None, None, False


def _clave_fecha(t: Tuple[int, Optional[int], Optional[int]]) -> Tuple[int, int, int]:
    return (t[0], t[1] or 0, t[2] or 0)


def _dif_txt(t1, t2) -> str:
    """Tiempo entre dos nacimientos (t1 antes que t2)."""
    if t1[1] and t1[2] and t2[1] and t2[2]:
        d1, d2 = datetime.date(t1[0], t1[1], t1[2]), datetime.date(t2[0], t2[1], t2[2])
        anios = _anyos(d1, d2)
        try:
            ref = datetime.date(d1.year + anios, d1.month, d1.day)
        except ValueError:
            ref = datetime.date(d1.year + anios, 3, 1)
        meses = (d2.year - ref.year) * 12 + d2.month - ref.month - (1 if d2.day < ref.day else 0)
        meses = max(meses, 0)
        if anios == 0 and meses == 0:
            return f"{(d2 - d1).days} días"
        partes = []
        if anios:
            partes.append(f"{anios} año{'s' if anios != 1 else ''}")
        if meses:
            partes.append(f"{meses} mes{'es' if meses != 1 else ''}")
        return " y ".join(partes)
    n = t2[0] - t1[0]
    return f"unos {n} año{'s' if n != 1 else ''}" if n else "menos de un año"


def comparar_edades(raw: str, mem, resolver_texto=None, en_texto=None) -> Optional[str]:
    q = norm(raw)
    q = re.sub(r"[¿?¡!.,;:]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    for tipo, rx in _PAT_CMP:
        m = rx.match(q)
        if not m:
            continue
        a, b = m.group("a").strip(), m.group("b").strip()
        if not _toks(a) or not _toks(b) or _toks(a) == _toks(b):
            return None
        na, ta, ka = _de_hecho(mem, a, en_texto, resolver_texto)
        nb, tb, kb = _de_hecho(mem, b, en_texto, resolver_texto)
        if not (ka and kb):
            return None
        if ta is None or tb is None:
            falta = [n for n, t in ((na, ta), (nb, tb)) if t is None]
            return "No sé cuándo nació " + " ni cuándo nació ".join(falta) + ", así que no puedo compararlos."
        ka_, kb_ = _clave_fecha(ta), _clave_fecha(tb)
        fa, fb = _fecha_ymd(*ta), _fecha_ymd(*tb)
        if tipo == "dif":
            if ta[0] == tb[0] and (not ta[1] or not tb[1] or ka_ == kb_):
                return f"{na} nació {fa} y {nb} {fb}: no sé qué diferencia hay, o es de menos de un año." if ka_ != kb_ else f"{na} y {nb} nacieron {fa}: tienen la misma edad."
            (p, tp, fp), (s_, ts, fs_) = ((na, ta, fa), (nb, tb, fb)) if ka_ < kb_ else ((nb, tb, fb), (na, ta, fa))
            return f"{_dif_txt(tp, ts)} de diferencia: {p} nació {fp} y {s_} {fs_}."
        if ka_ == kb_ or (ta[0] == tb[0] and (not ta[1] or not tb[1])):
            return f"Con lo que sé no puedo decirlo: {na} nació {fa} y {nb} {fb}."
        antes = ka_ < kb_
        (p, tp, fp), (s_, ts, fs_) = ((na, ta, fa), (nb, tb, fb)) if antes else ((nb, tb, fb), (na, ta, fa))
        dif = _dif_txt(tp, ts)
        if tipo == "cuando":
            o = m.group("o")
            primero = o in ("antes", "primero")
            quien = p if primero else s_
            return f"{quien} nació {'antes' if primero else 'después'}: {p} nació {fp} y {s_} {fs_} ({dif} de diferencia)."
        comp = m.group("c")
        mayor = comp in ("mayor", "mas viejo", "mas vieja", "mas mayor", "mas antiguo", "mas antigua")
        mas_mayor = p if mayor else s_                                                  # quien es «mayor» nacio antes
        otro = s_ if mayor else p
        if tipo == "quien":
            return f"{mas_mayor} es {'mayor' if mayor else 'más joven'} que {otro}: {p} nació {fp} y {s_} {fs_} ({dif} de diferencia)."
        # si_no: «¿A es mayor que B?»
        a_antes = antes
        cierto = (a_antes if mayor else not a_antes)
        det = f"{p} nació {fp} y {s_} {fs_} ({dif} de diferencia)"
        if cierto:
            return f"Sí. {na} es {'mayor' if mayor else 'más joven'} que {nb}: {det}."
        return f"No. {na} es {'menor' if mayor else 'mayor'} que {nb}: {det}."
    return None


def _cap1(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s
