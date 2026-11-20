"""Núcleo 2.0 · análisis superficial: tokens (Escuela UD) -> sintagmas nominales y cláusulas.

La Escuela aporta categoría y lema de cada palabra; aquí solo se agrupan en sintagmas y se
asignan papeles (sujeto, objeto, atributo, complementos, tiempo). Si algo no encaja, se
devuelve None y el turno se delega en las capas anteriores: nunca se guarda a medias.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from . import morfo as M
from .morfo import sa

ARTS = {"el": ("d", "m", 0), "la": ("d", "f", 0), "los": ("d", "m", 1), "las": ("d", "f", 1), "un": ("i", "m", 0), "una": ("i", "f", 0), "unos": ("i", "m", 1), "unas": ("i", "f", 1),
        "este": ("d", "m", 0), "esta": ("d", "f", 0), "estos": ("d", "m", 1), "estas": ("d", "f", 1), "ese": ("d", "m", 0), "esa": ("d", "f", 0), "esos": ("d", "m", 1), "esas": ("d", "f", 1),
        "aquel": ("d", "m", 0), "aquella": ("d", "f", 0)}
POSS = {"mi": "U", "mis": "U", "tu": "L", "tus": "L", "su": "3", "sus": "3", "nuestro": "U", "nuestra": "U", "nuestros": "U", "nuestras": "U"}
QUANT = {"mucho", "mucha", "muchos", "muchas", "poco", "poca", "pocos", "pocas", "varios", "varias", "algunos", "algunas", "todos", "todas", "bastante", "bastantes", "demasiado", "demasiada",
         "demasiados", "demasiadas", "ningun", "ninguna", "algun", "alguna", "otro", "otra", "otros", "otras", "cada", "ambos", "ambas", "todo", "toda"}
_COLORES_N = {"rojo", "azul", "verde", "amarillo", "blanco", "negro", "naranja", "gris", "rosa", "morado", "marron", "violeta", "dorado", "plateado", "turquesa", "beige", "lila", "granate", "celeste"}
PREPS = {"a", "de", "en", "con", "por", "para", "sin", "sobre", "entre", "hacia", "desde", "hasta", "contra", "bajo", "tras", "durante", "segun", "junto_a", "cerca_de", "lejos_de",
         "al_lado_de", "dentro_de", "fuera_de", "encima_de", "debajo_de", "delante_de", "detras_de", "enfrente_de", "alrededor_de", "antes_de", "despues_de"}
LOCUC = [("al", "lado", "de"), ("a", "el", "lado", "de"), ("cerca", "de"), ("lejos", "de"), ("dentro", "de"), ("fuera", "de"), ("encima", "de"), ("debajo", "de"), ("delante", "de"),
         ("detras", "de"), ("enfrente", "de"), ("alrededor", "de"), ("junto", "a"), ("antes", "de"), ("despues", "de")]
PRON_S = {"yo": "U", "tu": "L", "usted": "L", "el": "3m", "ella": "3f", "ellos": "3mp", "ellas": "3fp", "nosotros": "U", "nosotras": "U", "esto": "3n", "eso": "3n", "aquello": "3n"}
CLIT = {"me", "te", "se", "lo", "la", "le", "nos", "los", "las", "les", "os"}
NEG = {"no", "nunca", "jamas", "tampoco"}
GRADO = {"muy", "mucho", "poco", "bastante", "demasiado", "mas", "menos", "tan", "algo", "super", "realmente", "bien", "nada", "un_poco", "tanto"}
T_ADV = {"hoy", "ayer", "mañana", "anoche", "anteayer", "ahora", "antes", "despues", "luego", "siempre", "nunca", "todavia", "ya", "pronto", "tarde", "temprano", "actualmente", "antiguamente",
         "ultimamente", "recientemente", "normalmente", "habitualmente", "diariamente", "mensualmente", "semanalmente", "anualmente"}
MODO = {"bien", "mal", "despacio", "rapido", "deprisa", "regular", "fatal", "genial", "asi", "juntos", "juntas", "solo", "sola", "tambien", "aqui", "alli", "alla", "aca", "ahi", "cerca", "lejos",
        "arriba", "abajo", "dentro", "fuera", "mucho", "poco", "bastante", "demasiado", "tanto"}
LUGAR_ADV = {"aqui", "alli", "alla", "aca", "ahi", "cerca", "lejos", "arriba", "abajo", "dentro", "fuera"}
DIAS = {"lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo", "sabados", "domingos"}
MESES = {"enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "setiembre", "octubre", "noviembre", "diciembre"}
T_SUST = {"dia", "semana", "mes", "año", "mañana", "tarde", "noche", "fin", "verano", "invierno", "otoño", "primavera", "madrugada", "mediodia", "momento", "vez", "rato", "hora", "minuto", "siglo",
          "finde", "navidad", "navidades", "vacaciones", "cumpleaños"} | DIAS | MESES
WH = {"quien", "quienes", "que", "cual", "cuales", "donde", "adonde", "cuando", "cuanto", "cuanta", "cuantos", "cuantas", "como"}
# verbos de suceso con dativo de afectado: «a mi hija le salen los dientes», «se me ha roto el móvil», «se le murió el gato»
DAT_EV = {"salir", "romper", "caer", "olvidar", "perder", "estropear", "morir", "acabar", "terminar", "escapar", "quemar", "pinchar", "averiar", "ocurrir", "pasar", "manchar", "rajar", "parar", "colgar", "bloquear", "inflamar", "hinchar", "caducar"}
_DAT_CL = ("me", "te", "le", "les", "nos")
DAT_INTR = {"salir", "caer", "morir", "acabar", "terminar", "escapar", "ocurrir", "pasar", "caducar", "inflamar", "hinchar"}   # sin «se» tampoco tienen agente


def dativo_ev(C) -> bool:
    """¿Es un suceso que le pasa a alguien (dativo), no una acción de un agente?"""
    if C is None or C.v not in DAT_EV:
        return False
    cl = list(getattr(C, "clit", []) or [])
    dat_cl = [c for c in cl if c in _DAT_CL]
    if not dat_cl:
        return False
    if "se" in cl:
        return True                                     # «se me ha roto», «se le murió»
    if C.v not in DAT_INTR or (C.suj is not None and C.obj is not None):
        return False                                    # «le rompieron la nariz»: sin «se», romper tiene agente
    return any(c in ("le", "les") for c in dat_cl)      # «a mi hija le salen los dientes», «le está saliendo el primer diente»


GUSTAR = {"apasionar", "entusiasmar", "divertir", "relajar", "gustar", "encantar", "interesar", "molestar", "apetecer", "doler", "importar", "fascinar", "aburrir", "preocupar", "asustar", "agradar", "disgustar", "chiflar", "flipar", "sobrar", "faltar"}
COPULAS = {"ser", "estar", "parecer"}
MODALES = {"querer", "poder", "deber", "soler", "necesitar", "saber", "preferir", "desear", "intentar", "pensar", "esperar", "odiar", "adorar", "decidir", "conseguir", "lograr", "empezar", "comenzar", "aprender", "gustar"}
SUBORD = {"que", "si", "cuando", "aunque", "mientras", "donde", "como", "pues", "porque", "sino", "pero"}
RELLENO = {"pues", "bueno", "oye", "mira", "entonces", "ah", "oh", "eh", "vale", "ok", "bien", "ya", "claro", "y", "pero", "tambien", "ademas", "por_cierto", "sabes", "eso", "si"}


@dataclass
class Tok:
    f: str
    n: str
    pos: str
    lem: str
    dep: str
    cap: bool
    i: int = 0
    lo: str = ""
    ini: bool = False
    nom: bool = False               # nombre propio por contexto («me llamo javier»)
    min_ok: bool = False            # el mensaje va todo en minúsculas: se admiten nombres sin mayúscula


@dataclass
class SN:
    cab: str = ""                 # lema de la cabeza (sin acentos) o nombre propio en minúsculas
    propio: bool = False
    nombre: str = ""              # forma mostrable del nombre propio
    det: str = ""                 # 'd' definido, 'i' indefinido, '' sin artículo
    pos: str = ""                 # poseedor: 'U', 'L', '3'
    num: Optional[float] = None
    cuant: str = ""
    adjs: List[str] = field(default_factory=list)
    de: Optional["SN"] = None
    pl: bool = False
    gen: str = ""
    pron: str = ""                # 'U','L','3m','3f','3mp','3fp','3n'
    texto: str = ""
    coord: List["SN"] = field(default_factory=list)
    apos: str = ""                # nombre propio en aposición («mi hermana Laura»)
    i0: int = 0
    i1: int = 0
    nsubj: bool = False
    art_nombre: bool = False


@dataclass
class Clausula:
    v: str = ""
    tiempo: str = "pres"
    pers: str = "3s"
    neg: bool = False
    refl: bool = False
    clit: List[str] = field(default_factory=list)
    suj: Optional[SN] = None
    dat: Optional[SN] = None          # «a Ana (le)»
    obj: Optional[SN] = None
    obj2: Optional[SN] = None
    attr: List[str] = field(default_factory=list)
    grado: str = ""
    comps: list = field(default_factory=list)      # [(prep, SN)]
    cuando: str = ""
    freq: str = ""
    modo: List[str] = field(default_factory=list)
    xinf: str = ""                    # infinitivo complemento con su resto («comprar un coche»)
    comp: Optional[tuple] = None      # ('mas'|'menos'|'tan', adj, SN)
    wh: Optional[dict] = None         # {'tipo': 'quien'|'que'|..., 'prep': '', 'sust': ''}
    marc: List[str] = field(default_factory=list)  # marcadores: 'ahora', 'ya_no', 'corr', 'tambien'
    modal: str = ""
    prog: bool = False
    lugar_adv: str = ""
    amb1: bool = False              # la forma vale para 1.ª y 3.ª persona («vivía», «tenía»)


def tokens(parser, texto: str) -> List[Tok]:
    filas = []
    try:
        filas = parser.tree(texto) or []
    except Exception:                                                         # noqa
        filas = []
    out = []
    for r in filas:
        f, pos, _h, dep, lem = r[0], r[1], r[2], r[3], r[4]
        if pos == "PUNCT" or not re.search(r"\w", f):
            continue
        out.append(Tok(f, sa(f), pos, sa(lem or f), dep, f[:1].isupper(), len(out), (lem or f).lower()))
    # locuciones prepositivas -> una sola preposición
    res, i = [], 0
    while i < len(out):
        hecho = False
        for loc in LOCUC:
            if tuple(t.n for t in out[i:i + len(loc)]) == loc:
                clave = "_".join(loc).replace("a_el_lado", "al_lado")
                res.append(Tok(" ".join(t.f for t in out[i:i + len(loc)]).replace("a el", "al"), clave, "ADP", clave, "case", False))
                i += len(loc); hecho = True
                break
        if not hecho:
            if out[i].n == "un" and i + 1 < len(out) and out[i + 1].n == "poco" and (i + 2 >= len(out) or out[i + 2].n != "de"):
                res.append(Tok("un poco", "un_poco", "ADV", "un_poco", "advmod", False)); i += 2
            elif out[i].n == "por" and i + 1 < len(out) and out[i + 1].n == "cierto":
                res.append(Tok("por cierto", "por_cierto", "ADV", "por_cierto", "advmod", False)); i += 2
            else:
                res.append(out[i]); i += 1
    for k, t in enumerate(res):
        t.i = k
    if res:
        res[0].ini = True
    todo_min = not any(c.isupper() for c in texto)
    for k, t in enumerate(res):
        t.min_ok = todo_min
        if k >= 2 and t.cap and t.n in MESES and res[k - 2].n in POSS and not res[k - 1].cap and res[k - 1].pos in ("NOUN", "PROPN", "ADJ"):
            t.nom = True                                 # 2.17: «mi hermano Julio», «mi prima Abril»: tras un parentesco, el mes es un nombre de persona
        if t.n == "nada" and k >= 1 and k + 1 < len(res) and ((res[k - 1].cap and res[k - 1].n not in ARTS and res[k - 1].n not in NEG and not M.analizar(res[k - 1].f.lower())) or res[k - 1].n in ("el", "ella")) \
                and res[k + 1].n in ("mas", "menos", "muy", "bien", "mal", "rapido", "despacio", "en", "todos", "cada", "los", "con", "por", "mucho", "poco", "tan", "mejor", "peor", "como"):
            if res[k - 1].cap and res[k - 1].pos in ("VERB", "AUX"):
                res[k - 1].pos = "PROPN"; res[k - 1].lem = res[k - 1].n
            t.pos = "VERB"; t.lem = "nadar"; t.n = "nada_v"     # 2.17: «Irene nada más rápido que Paula»: es el verbo nadar
        if k >= 2 and res[k - 1].n in ("llamo", "llama", "llaman", "llamas") and res[k - 2].n in ("me", "se", "te") and t.f.isalpha() and t.n not in ARTS and t.n not in WH:
            t.nom = True
            if k + 2 < len(res) and res[k + 1].n in ("y", "e") and res[k + 2].f.isalpha():
                res[k + 2].nom = True
    # «Sara coleccionó sellos»: la Escuela tomó el nombre por verbo; si no es forma verbal conocida y le sigue un verbo finito, es un nombre
    if len(res) > 1 and res[0].cap and res[0].pos in ("VERB", "AUX"):
        ex, lax = M.formas()
        c0 = ex.get(res[0].f.lower()) or lax.get(sa(res[0].f)) or []
        if not c0 or (all(x[0] not in M._VERBOS_BASE and x[0] not in M._IRR for x in c0) and M.genero_nombre(res[0].f) in ("f", "m") and res[1].f.lower() in ex):
            c1 = ex.get(res[1].f.lower()) or (lax.get(sa(res[1].f)) if res[1].pos in ("VERB", "AUX", "NOUN") else None)
            if not res[1].cap and c1 and any(x[1] in ("pres", "pret", "imp", "fut", "cond") for x in c1) and res[1].n not in ARTS and res[1].n not in PREPS:
                res[0].pos = "PROPN"; res[0].lem = res[0].n; res[1].pos = "VERB"; res[1].lem = c1[0][0]
    # «¿Está rota la bici…?»: tras una cópula, una forma en -o/-a etiquetada como verbo es el atributo
    _COP = {"esta", "estan", "estaba", "estaban", "es", "son", "era", "eran", "parece", "parecen", "estas", "eres", "estoy", "soy", "sigue", "siguen", "quedo", "queda"}
    for k in range(1, len(res)):
        t = res[k]
        if t.pos in ("VERB",) and sa(res[k - 1].f) in _COP and sa(t.f).endswith(("o", "a", "os", "as")) and not t.cap \
                and (k + 1 == len(res) or res[k + 1].n in ARTS or res[k + 1].n in POSS or res[k + 1].pos in ("DET", "PROPN", "PUNCT")):
            t.pos = "ADJ"; t.lem = M.masc(sa(M.singular(t.f) if sa(t.f).endswith("s") else t.f))
    for t in res:                                   # «sé» con tilde es siempre el verbo saber (la Escuela a veces lo toma por «se»)
        if t.f.lower() == "sé" and t.pos != "VERB":
            t.pos = "VERB"; t.lem = "saber"
    try:                                            # 2.11: «Como pasta los martes»: en una afirmación, «como» + nombre es el verbo comer
        if "?" in (texto or "") or "¿" in (texto or ""):
            for k, t in enumerate(res):                 # «¿Qué como los martes?»: sin tilde y tras «qué», es el verbo comer
                if t.f == "como" and k > 0 and res[k - 1].n in ("que", "donde", "cuando", "con", "cuanto") and res[k - 1].f.lower() != res[k - 1].n:
                    t.pos = "VERB"; t.lem = "comer"
        if "?" not in (texto or "") and "¿" not in (texto or ""):
            for k, t in enumerate(res):
                if t.n == "como" and (k == 0 or res[k - 1].n in ("yo", "no", "siempre", "nunca", "tambien", "solo", "casi", "a_veces")) and k + 1 < len(res) \
                        and (res[k + 1].n in ARTS or res[k + 1].n in POSS or res[k + 1].pos in ("NOUN",) or _cat_kb(res[k + 1].n)):
                    t.pos = "VERB"; t.lem = "comer"
    except Exception:                               # noqa
        pass
    try:                                            # 2.11: «haré pasta», «como pasta»: un nombre conocido de fábrica tras un verbo conjugado es el objeto
        from . import conceptos as _K
        for k in range(1, len(res)):
            t, a_ = res[k], res[k - 1]
            if t.pos == "VERB" and not t.cap and _K.ancestros(t.n) and not t.f.lower().endswith(("é", "ó", "á", "í")) \
                    and not t.n.endswith(("ado", "ido", "ada", "ida", "ados", "idos", "adas", "idas")) \
                    and sa(a_.lem or "") not in ("ser", "estar", "haber", "parecer", "quedar", "seguir", "sentir") \
                    and a_.pos in ("VERB", "AUX") and not (a_.cap and not a_.ini) and any(x[1] in ("pres", "pret", "imp", "fut", "cond") for x in M.analizar(a_.f)) \
                    and (k + 1 == len(res) or res[k + 1].pos in ("ADP", "PUNCT", "CCONJ", "DET", "ADV")):
                t.pos = "NOUN"; t.lem = sa(M.singular(t.n)) if t.n.endswith("s") else t.n
    except Exception:                               # noqa
        pass
    try:                                            # 2.15: «¿Qué fruta comí?», «¿Qué prenda me he comprado?»: tras el interrogativo, un concepto de la base es el nombre
        from . import conceptos as _K
        for k in range(1, len(res)):
            t, a_ = res[k], res[k - 1]
            if a_.n in ("que", "cuanto", "cuanta", "cuantos", "cuantas", "cual", "cuales") and k <= 2 and _K._kb_clase(t.n) and not t.cap:
                if t.pos != "NOUN" or sa(t.lem or "") != sa(M.singular(t.n)):
                    t.pos = "NOUN"; t.lem = sa(M.singular(t.n)) if t.n.endswith("s") else t.n; t.lo = t.lem
                if k + 1 < len(res):
                    u = res[k + 1]
                    fin = [x for x in M.analizar(u.f) if x[1] in ("pres", "pret", "imp", "fut", "cond")]
                    if u.pos not in ("VERB", "AUX", "PRON") and fin and not _K._kb_clase(u.n):
                        u.pos = "VERB"; u.lem = fin[0][0]; u.lo = fin[0][0]
    except Exception:                               # noqa
        pass
    return res


NOMBRES = set()          # nombres propios ya conocidos por el núcleo (los fija el núcleo antes de analizar)


def _cat_kb(w):
    try:
        from . import conceptos as _K
        return bool(_K.ancestros(w) or _K.ancestros(M.singular(w)))
    except Exception:                               # noqa
        return False


def _comun_conocida(w: str) -> bool:
    try:
        from src.language import lexico
        return lexico.conoce(w)
    except Exception:                                                         # noqa
        return True


def _es_verbo_finito(t: Tok, T, k, laxo=False) -> bool:
    if t.n == "hace" and k + 2 < len(T) and (M.numero(T[k + 1].n) is not None or T[k + 1].n in ("mucho", "poco", "tiempo", "unos", "unas", "varios", "varias")) and any(x.pos in ("VERB", "AUX") for x in T[k + 2:]):
        return False
    if t.f.lower() in ("está", "están", "estás", "esté", "estáis", "sé"):
        return True
    if t.n in ("esta", "este", "estas", "estos") and t.f.lower() == t.n and k + 1 < len(T) and T[k + 1].n in ("mañana", "tarde", "noche", "semana", "vez", "mes", "año", "verano", "invierno", "primavera", "otoño", "temporada", "madrugada", "finde", "fin"):
        return False                                    # «esta mañana»: demostrativo, no el verbo estar
    if t.n in ("esta", "estas") and t.pos in ("VERB", "AUX") and k + 1 < len(T) and T[k + 1].pos not in ("NOUN",) and (k > 0 or T[k + 1].pos in ("PROPN", "DET", "ADJ", "ADV", "ADP")):
        return True
    if t.n in ("esta", "estan") and t.f.lower() == t.n and k + 1 < len(T) and ((k > 0 and T[k - 1].n in ("como", "donde", "no", "ya", "tambien")) or (k == 0 and (_propio(T[k + 1], k + 1) or (T[k + 1].n in ("el", "la", "mi", "tu", "su") and len(T) >= 3)))
                                                                           or (k > 0 and (_propio(T[k - 1], k - 1) or T[k - 1].pos in ("NOUN", "PROPN")) and (T[k + 1].pos in ("ADJ", "ADP", "ADV", "VERB") or T[k + 1].n in ("en", "muy", "bien", "mal")))):
        return True
    if t.n == "como" and t.pos == "VERB" and t.lem == "comer":
        return True                                     # 2.11: «Yo como pasta»: ya se decidió al leer la frase
    if t.n in ARTS or t.n in POSS or t.n in PREPS or t.n in CLIT or t.n in WH or t.n in NEG or t.n in ("y", "o", "e", "ni", "que", "como", "para", "sobre", "entre", "bajo", "nada", "era_", "una", "uno", "si", "ante", "cerca", "vale"):
        return False
    c = M.analizar(t.f, t.lem)
    fin = [x for x in c if x[1] in ("pres", "pret", "imp", "fut", "cond")]
    if not fin and t.pos in ("VERB", "AUX") and t.lem.endswith(("ar", "er", "ir")) and t.lem != t.n and not (t.cap and not t.ini):
        fin = [_adivina(t)]
    if not fin:
        return False
    prev = T[k - 1].n if k else ""
    if k and T[k - 1].f.lower() in ("él", "tú", "ella", "yo"):
        prev = "_pron"
    if prev in ARTS or prev in POSS or (prev in PREPS and prev not in ("a",)) or prev in QUANT or M.numero(prev) is not None:
        return False                                   # «el trabajo», «mi casa», «tres cuentas»
    if k > 0 and _comun_conocida(t.n) and T[k - 1].pos in ("VERB", "AUX") and not (T[k - 1].cap and not T[k - 1].ini) and any(x[1] in ("pres", "pret", "imp", "fut", "cond") for x in M.analizar(T[k - 1].f)) and T[k - 1].n not in ("se",):
        try:
            from . import conceptos as _K
            if _K.ancestros(t.n) and not t.f.lower().endswith(("é", "ó", "á")):
                return False                           # «haré pasta», «como pasta»: tras un verbo, un nombre conocido es el objeto
        except Exception:                              # noqa
            pass
    if t.pos in ("VERB", "AUX"):
        return True
    # forma verbal inequívoca (con su tilde, y que no es además un sustantivo o adjetivo conocido): manda la morfología
    if not t.cap or t.ini:
        ex, _lax = M.formas()
        if t.f.lower() in ex and any(x[1] in ("pres", "pret", "imp", "fut", "cond") for x in ex[t.f.lower()]) and not _comun_conocida(t.n) and t.n not in T_ADV and t.n not in MODO and M.numero(t.n) is None \
                and not (t.ini and t.pos == "PROPN"):
            return True
    # la Escuela dijo NOUN/ADJ/PROPN: solo se acepta como verbo al inicio de la cláusula o tras sujeto/negación/clítico
    if t.cap and k > 0:
        return False
    if t.pos in ("NOUN", "ADJ", "PROPN", "ADV", "INTJ", "X"):
        if k == 0 and t.cap and (t.pos == "PROPN" or t.n in NOMBRES) and any(x.pos in ("VERB", "AUX") for x in T[1:]):
            return False
        if k == 0 or prev in NEG or prev in CLIT:
            return fin[0][0] in M._VERBOS_BASE or fin[0][0] in M._IRR or (laxo and k + 1 < len(T))
        if laxo and not t.cap:
            return True
        return False
    return False


def tiempo_expr(T, i):
    """Expresión temporal desde i -> (texto, j, es_frecuencia) o None."""
    n = [t.n for t in T[i:i + 6]]
    if not n:
        return None
    def txt(k):
        return re.sub(r"\bde el\b", "del", re.sub(r"\ba el\b", "al", " ".join(t.f.lower() if not (t.cap and t.pos == "PROPN") else t.f for t in T[i:i + k])))
    a = n + [""] * 6
    if a[0] == "el" and a[1] == "dia" and (M.numero(a[2]) is not None or re.fullmatch(r"\d{1,2}", a[2])):
        k = 3                                           # «el día doce», «el día 12 de mayo»
        if a[3] == "de" and a[4] in MESES:
            k = 5
        return txt(k), i + k, False
    if a[0] == "los" and a[1] in DIAS and (a[1].endswith("s") or a[1] in ("lunes", "martes", "miercoles", "jueves", "viernes")):
        k = 2                                           # «los martes (y los jueves)»: frecuencia
        while k + 2 < len(a) and a[k] == "y" and a[k + 1] == "los" and a[k + 2] in DIAS:
            k += 3
        return txt(k), i + k, True
    if (M.numero(a[0]) is not None or a[0] in ("una", "un", "muchas", "pocas", "varias")) and a[1] in ("veces", "vez") and a[2] in ("al", "a", "por", "cada") and a[3]:
        k = 4 if a[2] in ("al", "por", "cada") else 5                 # «tres veces por semana», «una vez al mes», «dos veces a la semana»
        return txt(k), i + k, True
    if a[0] in ("todos", "todas") and a[1] in ("los", "las") and a[2] in T_SUST | {"dias", "semanas", "meses", "años", "noches", "tardes", "mañanas", "veranos", "inviernos", "fines"}:
        k = 3
        if a[2] == "fines" and a[3] == "de" and a[4] == "semana":
            k = 5
        return txt(k), i + k, True
    if a[0] in ("todo", "toda") and a[1] in ("el", "la") and a[2] in ("dia", "noche", "mañana", "tarde", "semana", "mes", "año", "verano", "invierno", "rato", "finde"):
        return txt(3), i + 3, False                 # «toda la noche», «todo el día»
    if a[0] == "cada" and (a[1] in T_SUST or sa(M.singular(a[1])) in T_SUST):
        k = 2
        if a[1] == "fin" and a[2] == "de" and a[3] == "semana":
            k = 4
        return txt(k), i + k, True
    if a[0] in ("los", "las") and (a[1] in DIAS or a[1] in ("fines", "domingos", "sabados", "veranos", "inviernos")):
        k = 2
        if a[1] == "fines" and a[2] == "de" and a[3] == "semana":
            k = 4
        if a[2] == "por" and a[3] == "la" and a[4] in ("mañana", "tarde", "noche"):
            k = 5
        return txt(k), i + k, True
    if a[0] in ("el", "la", "este", "esta", "ese", "esa", "aquel") and a[1] in T_SUST and a[2] in ("pasado", "pasada", "proximo", "proxima", "anterior", "siguiente", "que"):
        k = 3
        if a[2] == "que" and a[3] == "viene":
            k = 4
        return txt(k), i + k, False
    if a[0] in ("el", "la") and a[1] in ("proximo", "proxima", "pasado", "pasada") and a[2] in T_SUST:
        return txt(3), i + 3, False
    if a[0] in ("el", "este", "esta", "esa", "ese") and (a[1] in DIAS or a[1] in ("mañana", "tarde", "noche", "semana", "mes", "año", "verano", "invierno", "otoño", "primavera", "finde")) :
        k = 2
        if a[1] == "fin" :
            k = 2
        if a[2] == "por" and a[3] == "la" and a[4] in ("mañana", "tarde", "noche"):
            k = 5
        return txt(k), i + k, False
    if a[0] in ("el", "este") and a[1] == "fin" and a[2] == "de" and a[3] == "semana":
        k = 4 + (1 if a[4] in ("pasado", "proximo") else 0)
        return txt(k), i + k, False
    if a[0] == "el" and re.fullmatch(r"\d{1,2}", a[1]) and a[2] == "de" and a[3] in MESES:
        k = 4
        if a[4] == "de" and re.fullmatch(r"\d{4}", a[5]):
            k = 6
        return txt(k), i + k, False
    if a[0] == "en" and (re.fullmatch(r"(1[0-9]|20)\d\d", a[1]) or a[1] in MESES or a[1] in ("verano", "invierno", "otoño", "primavera", "navidad", "navidades", "vacaciones")):
        k = 2
        if a[1] in MESES and a[2] == "de" and re.fullmatch(r"\d{4}", a[3]):
            k = 4
        return txt(k), i + k, False
    if a[0] == "en" and a[1] in ("el", "la") and a[2] in ("año", "siglo") and a[3]:
        return txt(4), i + 4, False
    if a[0] == "hace" and (M.numero(a[1]) is not None or a[1] in ("mucho", "poco", "tiempo", "unos", "unas", "varios", "varias")) and a[2]:
        k = 3 if (a[2] in ("dias", "dia", "semanas", "semana", "meses", "mes", "años", "año", "horas", "hora", "minutos", "rato", "tiempo")) else 2
        if a[1] in ("unos", "unas", "varios", "varias") and a[3]:
            k = 4 if M.numero(a[2]) is not None else 3
        return txt(k), i + k, False
    if a[0] == "por" and a[1] in ("la", "las") and a[2] in ("mañana", "tarde", "noche", "mañanas", "tardes", "noches"):
        return txt(3), i + 3, a[1] == "las"
    if a[0] in ("a", "hasta", "desde") and a[1] in ("las", "la") and (M.numero(a[2]) is not None or re.fullmatch(r"\d{1,2}[:.]\d\d", a[2])):
        k = 3
        if a[3] in ("y", "menos") and a[4]:
            k = 5
        if a[k] == "de" and a[k + 1] == "la" if k + 1 < 6 else False:
            k = min(6, k + 3)
        return txt(k), i + k, False
    if a[0] == "a" and a[1] in ("veces", "menudo", "diario"):
        return txt(2), i + 2, True
    if a[0] == "de" and a[1] == "vez" and a[2] == "en" and a[3] == "cuando":
        return txt(4), i + 4, True
    if a[0] == "desde" and a[1] in ("el", "la") and a[2] in ("colegio", "instituto", "universidad", "infancia", "carrera", "guarderia", "principio", "verano", "invierno", "primer", "primero", "bachillerato", "parvulario"):
        return txt(3), i + 3, False                 # «nos conocemos desde el colegio»
    if a[0] == "desde" and (a[1] == "hace" or re.fullmatch(r"\d{4}", a[1]) or a[1] in ("ayer", "siempre", "pequeño", "pequeña", "niño", "niña")):
        k = 2
        if a[1] == "hace":
            k = 4 if a[3] else 3
        return txt(k), i + k, False
    if a[0] == "esta" and a[1] in ("mañana", "tarde", "noche", "semana"):
        return txt(2), i + 2, False
    if a[0] == "pasado" and a[1] == "mañana":
        return txt(2), i + 2, False
    if a[0] in T_ADV and a[0] not in ("nunca",):
        k = 1
        if a[0] in ("ayer", "hoy", "mañana") and a[1] == "por" and a[2] == "la" and a[3] in ("mañana", "tarde", "noche"):
            k = 4
        return txt(k), i + k, a[0] in ("siempre", "normalmente", "habitualmente", "diariamente", "mensualmente", "semanalmente", "anualmente")
    if a[0] in DIAS and (i == 0 or True) and T[i].pos != "PROPN":
        return None
    return None


def _propio(t: Tok, k: int) -> bool:
    if not t.cap and (t.n in NOMBRES or getattr(t, "nom", False)) and t.n not in ARTS and t.n not in PREPS and t.n not in WH:
        return True
    if not t.cap and t.pos in ("PROPN", "NOUN", "X", "ADJ") and len(t.n) > 2 and t.n not in ARTS and t.n not in POSS and t.n not in PREPS and t.n not in WH and t.n not in CLIT and t.n not in NEG \
            and t.n not in PRON_S and t.n not in QUANT and t.n not in T_ADV and t.n not in RELLENO and t.n not in MODO and t.n not in GRADO and t.n not in T_SUST and M.numero(t.n) is None \
            and not _comun_conocida(t.n) and not M.analizar(t.f) and not _comun_conocida(M.singular(t.n)) and t.f.isalpha() and getattr(t, "min_ok", False):
        return True
    if not t.cap or t.n in ARTS or t.n in POSS or t.n in PREPS or t.n in WH or t.n in CLIT or t.n in NEG or t.n in PRON_S or t.n in QUANT or t.n in T_ADV or t.n in RELLENO:
        return False
    if t.n in DIAS or (t.n in MESES and not t.nom):
        return False
    if not t.ini:
        return True
    if t.pos == "PROPN" or t.n in NOMBRES:
        return True
    if t.pos in ("NOUN", "ADJ", "X", "INTJ", "ADV") and not _comun_conocida(t.n) and not M.analizar(t.f):
        return True                  # palabra desconocida con mayúscula al inicio: nombre propio
    return False


def sn(T, i, simple=False, nominal=False) -> Optional[tuple]:
    """Sintagma nominal desde i -> (SN, j) o None. nominal=True: posición de objeto, se admite cabeza mal etiquetada."""
    L = len(T)
    if i >= L:
        return None
    j = i
    s = SN(i0=i)
    t = T[j]
    if t.f.lower() in ("té",) :
        s.cab = "te"; s.texto = "té"; s.i1 = j + 1
        return s, j + 1
    if t.n in ("el", "la", "los", "las") and j + 1 < L and T[j + 1].n in ("mio", "mia", "mios", "mias", "tuyo", "tuya", "tuyos", "tuyas", "suyo", "suya"):
        s.cab = "*"; s.det = "d"; s.gen = ARTS[t.n][1]; s.pl = bool(ARTS[t.n][2]); s.pos = {"m": "U", "t": "L", "s": "3"}[T[j + 1].n[0]]
        s.texto = t.f.lower() + " " + T[j + 1].f.lower(); s.i1 = j + 2
        return s, j + 2
    if t.n in ("el", "la", "los", "las") and j + 2 < L and T[j + 1].n == "de" and not simple:
        r = sn(T, j + 2, simple=True)
        if r and (r[0].propio or r[0].pos or r[0].det):
            s.cab = "*"; s.det = "d"; s.gen = ARTS[t.n][1]; s.pl = bool(ARTS[t.n][2]); s.de = r[0]
            s.texto = " ".join(x.f if x.cap and x.pos == "PROPN" else x.f.lower() for x in T[i:r[1]]); s.i1 = r[1]
            return s, r[1]
    # pronombres tónicos tras preposición: «para mí», «con ti» (de «contigo»)
    if t.f.lower() in ("mí", "ti") and (j + 1 >= L or T[j + 1].pos not in ("NOUN", "ADJ", "PROPN")) and j > 0 and T[j - 1].n in PREPS:
        s.pron = "U" if t.f.lower() == "mí" else "L"; s.texto = t.f.lower(); s.i1 = j + 1
        return s, j + 1
    # pronombres
    if t.n in PRON_S and not (t.n in ("el", "tu") and j + 1 < L and (T[j + 1].pos in ("NOUN", "ADJ", "PROPN", "NUM") or T[j + 1].n in QUANT or T[j + 1].f.lower() == "té") and t.f.lower() not in ("él", "tú")):
        s.pron = PRON_S[t.n]; s.texto = t.f.lower(); s.i1 = j + 1; s.nsubj = t.dep.startswith("nsubj")
        return s, j + 1
    if t.n in ("alguien", "nadie", "algo", "todo") and (j + 1 >= L or T[j + 1].pos not in ("NOUN",)):
        s.cab = t.n; s.texto = t.n; s.i1 = j + 1
        return s, j + 1
    visto = False
    while j < L:
        t = T[j]
        if t.n in ("otro", "otra") and not s.det and not s.pos and j + 1 < L and T[j + 1].pos in ("NOUN", "ADJ"):
            s.det = "i"; s.gen = "f" if t.n == "otra" else "m"; s.cuant = "otro"; j += 1; visto = True; continue
        if t.n in ("todos", "todas", "todo", "toda") and j + 1 < L and T[j + 1].n in ARTS:
            s.cuant = "todo"; j += 1; continue
        if t.n in ARTS and not s.det and not s.pos:
            s.det, g, pl = ARTS[t.n]; s.gen = g; s.pl = bool(pl); j += 1; visto = True; continue
        if t.n in POSS and not s.pos and not s.det:
            s.pos = POSS[t.n]; s.pl = t.n.endswith("s"); j += 1; visto = True; continue
        if M.numero(t.n) is not None and t.n not in ("un", "una", "medio", "media") and s.num is None and j + 1 <= L:
            s.num = M.numero(t.n); s.pl = s.num != 1; j += 1; visto = True; continue
        if t.n in ("mas", "menos") and not s.cuant and not visto and j + 1 < L and T[j + 1].pos == "NOUN" and T[j + 1].n.endswith("s"):
            s.cuant = t.n; s.pl = True; j += 1; visto = True; continue
        if t.n in QUANT and not s.cuant and j + 1 < L and T[j + 1].pos in ("NOUN", "ADJ", "PROPN"):
            s.cuant = t.n; s.pl = s.pl or t.n.endswith("s"); j += 1; visto = True; continue
        break
    if j >= L:
        if s.num is not None and not s.det:           # «tiene tres»
            s.cab = ""; s.texto = " ".join(x.f.lower() for x in T[i:j]); s.i1 = j
            return s, j
        return None
    t = T[j]
    # adjetivos antepuestos («un buen amigo», «mi mejor amiga»)
    pre = []
    while j + 1 < L and T[j].pos == "ADJ" and not T[j + 1].cap and (T[j + 1].pos in ("NOUN", "PROPN") or (T[j + 1].pos == "ADJ" and j + 2 < L and T[j + 2].pos == "NOUN")) and not _propio(T[j], j):
        pre.append(M.masc(T[j].lem if T[j].lem else T[j].n)); j += 1
    t = T[j]
    if t.f.lower() == "té":
        s.cab = "te"; s.gen = s.gen or "m"; j += 1
        s.i1 = j
        s.texto = " ".join(x.f.lower() for x in T[i:j])
        return s, j
    if s.det == "d" and not s.pl and t.cap and not t.ini and t.pos in ("PROPN", "NOUN", "X") and s.num is None and not pre and i == j - 1:
        s.det = ""; s.art_nombre = True
    if _propio(t, j) and not s.det and not s.pos and s.num is None:
        k = j
        while k < L and _propio(T[k], k) and (k == j or T[k].pos in ("PROPN", "NOUN", "ADJ", "X")):
            k += 1
        s.propio = True; s.nombre = " ".join(x.f if x.cap else x.f.capitalize() for x in T[j:k]); s.cab = sa(s.nombre); j = k
    elif t.pos in ("NOUN", "PROPN") or (nominal and not visto and t.pos in ("ADJ", "PRON", "ADV", "DET", "NUM", "SCONJ", "CCONJ") and t.n not in PREPS and t.n not in WH and t.n not in CLIT and t.n not in NEG
                                         and t.n not in T_ADV and t.n not in MODO and t.n not in GRADO and t.n not in PRON_S and t.n not in ARTS and t.n not in POSS and t.n not in QUANT and t.n not in ("y", "o", "e", "ni", "que", "si")
                                         and M.numero(t.n) is None and not any(x[1] in ("pres", "pret", "imp", "fut", "cond", "inf", "ger") for x in M.analizar(t.f))) or (t.pos in ("VERB", "X", "INTJ") and not visto and t.n not in PREPS and t.n not in WH and t.n not in CLIT and t.n not in NEG and t.n not in T_ADV and t.n not in MODO
                                         and not any(x[1] in ("pres", "pret", "imp", "fut", "cond", "inf", "ger", "part") for x in M.analizar(t.f))) or (visto and t.pos in ("ADJ", "VERB", "X", "ADV", "INTJ", "NUM") and t.n not in PREPS and t.n not in WH and not (t.pos == "VERB" and _es_verbo_finito(t, T, j) and not (s.det or s.pos))):
        lem = t.lem if t.pos == "NOUN" and t.lem else t.n
        if "ñ" in t.n and "ñ" not in lem:
            lem = sa(M.singular(t.n))
        if t.pos != "NOUN" or lem == t.n:
            lem = sa(M.singular(t.n)) if (s.pl or s.num not in (None, 1) or t.n.endswith("s")) else t.n
        if t.n.endswith("s") and lem == t.n and sa(M.singular(t.n)) != t.n:
            lem = sa(M.singular(t.n))
        if lem != t.n and (t.n.endswith("s")) and not s.pl and (s.det == "" and not s.pos):
            s.pl = True
        if t.n.endswith("s") and sa(M.singular(t.n)) != t.n:
            s.pl = True
        if t.n.endswith("s") and sa(M.singular(t.n)) == t.n:
            lem = t.n                                   # invariables: «paraguas», «lunes», «virus»
        if t.n.endswith("s") and sa(M.singular(t.f.lower())) == t.n:
            lem = t.n; s.pl = s.pl and s.det not in ("", )   # agudas con tilde: «portugués», «inglés», «autobús»
        s.cab = lem; j += 1
        # «una serie muy buena»: adjetivo con grado detrás del nombre
        if j + 1 < L and T[j].n in ("muy", "bastante", "super", "tan", "algo", "poco", "demasiado") and T[j + 1].pos == "ADJ" and not T[j + 1].cap:
            s.adjs.append(M.masc(T[j + 1].n)); s.texto = (s.texto + " " + T[j].f.lower() + " " + T[j + 1].f.lower()).strip(); j += 2
        # «el vecino de arriba», «la casa de al lado»: modificador de lugar
        if j + 1 < L and T[j].n == "de" and T[j + 1].n in ("arriba", "abajo", "enfrente", "atras", "delante", "fuera", "dentro"):
            s.adjs.append("de " + T[j + 1].n); s.texto = (s.texto + " de " + T[j + 1].f.lower()).strip(); j += 2
        elif j + 2 < L and T[j].n == "de" and T[j + 1].n == "al" and T[j + 2].n == "lado":
            s.adjs.append("de al lado"); s.texto = (s.texto + " de al lado").strip(); j += 3
        # compuestos «fin de semana», «vaso de agua»: de + sustantivo sin artículo
        if not simple and j + 1 < L and T[j].n == "de" and T[j + 1].pos == "NOUN" and not _propio(T[j + 1], j + 1) and T[j + 1].n not in ARTS and s.cab not in REL_SIN_COMP \
                and T[j + 1].n not in _COLORES_N:                 # «pintar la cocina de blanco»: el color no forma un nombre compuesto
            s.cab = s.cab + " de " + T[j + 1].n; j += 2
        # aposición con nombre propio: «mi hermana Laura», «el perro Toby»
        if j < L and _propio(T[j], j) and (s.pos or s.det == "d"):
            k = j
            while k < L and _propio(T[k], k):
                k += 1
            s.apos = " ".join(x.f for x in T[j:k]); j = k
        # «el año 2015», «el piso 3», «la talla 42»: número en aposición
        elif j < L and T[j].pos == "NUM" and re.match(r"^\d+$", T[j].f) and s.cab in ("año", "modelo", "piso", "planta", "talla", "numero", "portal", "puerta", "linea", "autobus", "habitacion", "aula"):
            s.apos = T[j].f; j += 1
    else:
        return None
    s.adjs = pre
    if not s.gen:
        s.gen = ""
    # adjetivos pospuestos (no tras nombre propio)
    if not s.propio and not s.apos:
        while j < L and T[j].pos == "ADJ" and T[j].n not in ("mas", "menos") and not _propio(T[j], j):
            s.adjs.append(M.masc(T[j].n)); j += 1
            if j + 1 < L and T[j].n == "y" and T[j + 1].pos == "ADJ":
                s.adjs.append(M.masc(T[j + 1].n)); j += 2
    # complemento «de SN» (poseedor)
    if not simple and j + 1 < L and T[j].n == "de" and not s.propio:
        r = sn(T, j + 1, simple=False)
        if r and (r[0].propio or r[0].pron or r[0].det or r[0].pos):
            s.de = r[0]; j = r[1]
            otros = [r[0]]
            while j + 2 < L and T[j].n in ("y", "e") and T[j + 1].n == "de":
                r2 = sn(T, j + 2, simple=True)
                if not r2 or not (r2[0].propio or r2[0].det or r2[0].pos):
                    break
                otros.append(r2[0]); j = r2[1]
            if len(otros) > 1:
                s.de = SN(coord=otros, pl=True, texto=" y ".join(x.texto for x in otros))
            elif s.de.propio and j + 1 < L and T[j].n == "de" and T[j + 1].n in ARTS and s.cab not in REL_SIN_COMP:
                r3 = sn(T, j + 1, simple=False)        # «la cena de Navidad de la empresa»: «cena de Navidad» es el nombre
                if r3 and (r3[0].det or r3[0].pos):
                    s.cab = s.cab + " de " + s.de.texto; s.de = r3[0]; j = r3[1]
    s.i1 = j
    s.texto = " ".join(x.f if (x.cap and _propio(x, x.i)) else x.f.lower() for x in T[i:j]).replace("a el ", "al ").replace("de el ", "del ")
    s.nsubj = any(x.dep.startswith("nsubj") for x in T[i:j])
    return s, j


REL_SIN_COMP = {"padre", "madre", "hijo", "hija", "hermano", "hermana", "amigo", "amiga", "abuelo", "abuela", "tio", "tia", "primo", "prima", "jefe", "jefa", "vecino", "vecina", "novio", "novia",
                "marido", "mujer", "esposo", "esposa", "profesor", "profesora", "color", "nombre", "capital", "dueño", "dueña"}


def sn_coord(T, i, nominal=False):
    """SN con coordinación: «Ana y Luis», «un perro, un gato y dos peces»."""
    r = sn(T, i, nominal=nominal)
    if not r:
        return None
    s, j = r
    partes = [s]
    while j < len(T):
        if T[j].n in ("y", "e", "o", "ni") and j + 1 < len(T):
            r2 = sn(T, j + 1, nominal=nominal)
            if not r2 or (j + 1 < len(T) and _es_verbo_finito(T[j + 1], T, j + 1) and not T[j + 1].cap):
                break
            partes.append(r2[0]); j = r2[1]
        else:
            break
    if len(partes) > 1:
        s = SN(coord=partes, pl=True, texto=" ".join(x.f if x.cap and x.pos == "PROPN" else x.f.lower() for x in T[i:j]), i0=i, i1=j, nsubj=any(p.nsubj for p in partes))
    return s, j


def _adivina(t):
    """(lema, tiempo, persona) por terminación, para verbos que solo conoce la Escuela."""
    f = t.f.lower()
    if f.endswith(("ó", "ió")):
        return (t.lem, "pret", "3s")
    if f.endswith(("aron", "ieron")):
        return (t.lem, "pret", "3p")
    if f.endswith(("aba", "ía")):
        return (t.lem, "imp", "3s")
    if f.endswith(("aban", "ían")):
        return (t.lem, "imp", "3p")
    if f.endswith(("é", "í")):
        return (t.lem, "pret", "1s")
    if f.endswith(("an", "en")):
        return (t.lem, "pres", "3p")
    if f.endswith("o"):
        return (t.lem, "pres", "1s")
    if f.endswith(("as", "es")):
        return (t.lem, "pres", "2s")
    return (t.lem, "pres", "3s")


def _grupo_verbal(T, k):
    """Desde el verbo finito en k: (lema, tiempo, persona, j, modal, prog, xinf_inicio) resolviendo perífrasis."""
    t = T[k]
    c = M.analizar(t.f, t.lem)
    fin = [x for x in c if x[1] in ("pres", "pret", "imp", "fut", "cond")]
    if not fin and t.pos in ("VERB", "AUX") and t.lem.endswith(("ar", "er", "ir")):
        fin = [_adivina(t)]
    if not fin:
        return None
    lema, tiempo, pers = fin[0]
    if t.pos in ("VERB", "AUX") and t.lem and t.lem != lema:
        alt = [x for x in fin if x[0] == t.lem]
        if alt:
            lema, tiempo, pers = alt[0]
    if lema == "ser" and tiempo == "pret" and k + 1 < len(T) and (T[k + 1].n in ("a", "hacia", "de", "con", "en") and not (T[k + 1].n in ("de", "en", "con") and "se" not in [x.n for x in T[max(0, k - 2):k]] and T[k + 1].n != "a")
                                                                   or T[k + 1].n in ("alli", "alla", "ahi", "aqui")):
        alt = [x for x in fin if x[0] == "ir"]
        if alt:
            lema, tiempo, pers = alt[0][0], alt[0][1], pers
    amb = pers == "1s" and any(x[0] == lema and x[1] == tiempo and x[2] == "3s" for x in fin)
    if amb:
        pers = "3s"
    _grupo_verbal.amb = amb
    j = k + 1
    L = len(T)
    modal, prog = "", False
    def an(x):
        return M.analizar(x.f, x.lem)
    if lema == "haber" and j < L and any(x[1] == "part" for x in an(T[j])):
        lema = [x for x in an(T[j]) if x[1] == "part"][0][0]; tiempo = "pret"; j += 1
    elif lema == "estar" and j < L and any(x[1] == "ger" for x in an(T[j])):
        lema = [x for x in an(T[j]) if x[1] == "ger"][0][0]; prog = True; j += 1
    elif lema == "ir" and tiempo in ("pres", "imp") and j + 1 < L and T[j].n == "a" and any(x[1] == "inf" for x in an(T[j + 1])):
        lema = [x for x in an(T[j + 1]) if x[1] == "inf"][0][0]; tiempo = "fut"; j += 2
    elif lema == "acabar" and j + 1 < L and T[j].n == "de" and any(x[1] == "inf" for x in an(T[j + 1])):
        lema = [x for x in an(T[j + 1]) if x[1] == "inf"][0][0]; tiempo = "pret"; j += 2
    return lema, tiempo, pers, j, modal, prog


def clausula(T, pregunta=False) -> Optional[Clausula]:
    """Analiza una cláusula simple. None si hay algo que no se entiende por completo."""
    L = len(T)
    if not L:
        return None
    C = Clausula()
    i = 0
    # marcadores iniciales
    while i < L and T[i].n in RELLENO and L - i > 1 and not (T[i].n in ("ya", "eso", "si", "bien", "vale") and False):
        if T[i].n == "tambien":
            C.marc.append("tambien")
        if T[i].n in ("eso", "si", "bien", "ya", "vale", "claro") and i + 1 < L and (_es_verbo_finito(T[i + 1], T, i + 1) or T[i + 1].n in NEG) and T[i].n in ("eso", "ya"):
            break
        i += 1
    T = T[i:]
    for k, t in enumerate(T):
        t.i = k
    L = len(T)
    if not L:
        return None
    # verbo finito: el primero que no esté dentro de un SN
    kv = None
    for k, t in enumerate(T):
        if _es_verbo_finito(t, T, k, laxo=(pregunta and k == 0)):
            kv = k
            break
    if kv is None:
        # la Escuela no marcó ningún verbo: se acepta una forma verbal inequívoca tras el sujeto («los perros ladran»)
        for k, t in enumerate(T):
            if k and _es_verbo_finito(t, T, k, laxo=True):
                kv = k
                break
    if kv is None:
        return None
    gv = _grupo_verbal(T, kv)
    if not gv:
        return None
    C.v, C.tiempo, C.pers, jv, C.modal, C.prog = gv
    C.amb1 = bool(getattr(_grupo_verbal, "amb", False))
    if C.pers == "1s" and T[kv].f.lower() == sa(T[kv].f.lower()):
        _ex, _lax = M.formas()
        alt = [x for x in _lax.get(T[kv].n, ()) if x[0] == C.v and x[2] == "3s" and x[1] == "pret"]
        hay_suj = (kv > 0 and any(_propio(x, x.i) or x.pos in ("NOUN", "PROPN") for x in T[:kv]) and not any(x.n == "yo" for x in T[:kv])) or (pregunta and kv + 1 < len(T) and _propio(T[kv + 1], kv + 1))
        if alt and hay_suj and "me" not in [x.n for x in T[:kv]]:
            C.tiempo, C.pers = "pret", "3s"
    # «Ayer jugamos…»: «-amos/-imos» vale para presente y pasado; un adverbio de pasado decide
    if C.pers == "1p" and C.tiempo == "pres" and T[kv].n.endswith(("amos", "imos")) and any(x.n in ("ayer", "anoche", "anteayer", "pasado", "pasada") for x in T):
        if any(x[0] == C.v and x[1] == "pret" and x[2] == "1p" for x in M.analizar(T[kv].f)):
            C.tiempo = "pret"
    # --- zona preverbal
    pre = T[:kv]
    if len(pre) >= 1 and pre[0].ini and pre[0].cap and pre[0].pos in ("NOUN", "ADJ", "X") and pre[0].n not in ARTS and pre[0].n not in POSS and pre[0].n not in QUANT and pre[0].n not in T_ADV \
            and pre[0].n not in NEG and pre[0].n not in CLIT and pre[0].n not in RELLENO and pre[0].n not in PRON_S and M.numero(pre[0].n) is None and pre[0].n not in DIAS and pre[0].n not in MESES \
            and (len(pre) == 1 or pre[1].n in NEG or pre[1].n in CLIT or pre[1].n in ("y", "e", "ya", "tambien")) and not pregunta and not pre[0].n.endswith("s"):
        pre[0].pos = "PROPN"
    i = 0
    while i < len(pre):
        t = pre[i]
        if t.n in NEG:
            C.neg = True
            if t.n in ("nunca", "jamas"):
                C.freq = "nunca"
            if i > 0 and pre[i - 1].n == "ya":
                C.marc.append("ya_no")
            i += 1; continue
        if t.n == "ya":
            C.marc.append("ya"); i += 1; continue
        if t.n in CLIT and i >= len(pre) - 3 and all(x.n in CLIT for x in pre[i:]):
            C.clit.append(t.n); i += 1; continue
        te = tiempo_expr(pre, i)
        if te and not (pre[i].n in ("el", "la", "los", "las", "este", "esta") and False):
            if te[2]:
                C.freq = te[0]
            else:
                C.cuando = te[0]
                if te[0] in ("ahora", "actualmente"):
                    C.marc.append("ahora")
            i = te[1]; continue
        if t.n == "a" and C.dat is None:
            r = sn_coord(pre, i + 1)
            if r:
                C.dat = r[0]; i = r[1]; continue
            return None
        if t.n == "tambien":
            C.marc.append("tambien"); i += 1; continue
        if t.n in PREPS and t.n != "a" and C.suj is None:
            r = sn_coord(pre, i + 1)
            if r:
                C.comps.append((t.n, r[0])); i = r[1]; continue
            return None
        if t.n in ("solo", "solamente", "casi", "aun", "todavia", "siempre"):
            if t.n == "siempre":
                C.freq = "siempre"
            i += 1; continue
        if C.suj is None:
            r = sn_coord(pre, i)
            if r:
                C.suj = r[0]; i = r[1]; continue
        return None
    if "se" in C.clit:
        C.refl = True
    if C.pers in ("1s", "1p") and "me" in C.clit or C.pers in ("1p",) and "nos" in C.clit:
        C.refl = C.v not in GUSTAR
    if C.pers == "2s" and "te" in C.clit:
        C.refl = C.v not in GUSTAR
    # --- zona posverbal
    R = T[jv:]
    for k, t in enumerate(R):
        t.i = k
    i = 0
    cop = C.v in COPULAS
    while i < len(R):
        t = R[i]
        if t.n in ("tambien", "solo", "solamente", "casi", "aun", "incluso", "pues", "entonces", "ademas"):
            if t.n == "tambien":
                C.marc.append("tambien")
            i += 1; continue
        if t.n in NEG and t.n != "no":
            C.neg = True; C.freq = "nunca"; i += 1; continue
        if t.n == "ya" :
            i += 1; continue
        te = tiempo_expr(R, i)
        if te:
            if te[2]:
                C.freq = te[0]
            else:
                C.cuando = (C.cuando + " " + te[0]).strip()
                if te[0] in ("ahora", "actualmente"):
                    C.marc.append("ahora")
            i = te[1]; continue
        # superlativos: «el más alto», «la mayor»
        if t.n in ("el", "la", "los", "las") and i + 1 < len(R) and (R[i + 1].n in ("mas", "menos") and i + 2 < len(R) or R[i + 1].n in ("mayor", "menor", "mejor", "peor", "pequeño", "pequeña", "grande") and (i + 2 == len(R) or R[i + 2].n == "de")) and cop and pregunta:
            i += 1; continue
        # comparativos
        if t.n in ("mas", "menos", "tan") and i + 2 < len(R) and R[i + 1].pos in ("ADJ", "ADV", "NOUN", "VERB") and R[i + 2].n in ("que", "como"):
            r = sn_coord(R, i + 3)
            if not r:
                return None
            C.comp = (t.n, M.masc(R[i + 1].n), r[0]); i = r[1]; continue
        if t.n in ("mayor", "menor", "mejor", "peor") and i + 1 < len(R) and R[i + 1].n == "que":
            r = sn_coord(R, i + 2)
            if not r:
                return None
            C.comp = ("mas", t.n, r[0]); i = r[1]; continue
        if pregunta and t.n in ("mas", "menos") and not cop and not (i + 1 < len(R) and R[i + 1].pos == "NOUN" and R[i + 1].n.endswith("s")):
            C.modo.append(t.n); i += 1; continue
        if pregunta and cop and t.n in ("pequeño", "pequeña", "grande") and i > 0 and R[i - 1].n in ("el", "la") and (i + 1 == len(R) or R[i + 1].n == "de"):
            C.attr.append("menor" if t.n != "grande" else "mayor"); i += 1; continue
        if t.n in ("mayor", "menor", "mejor", "peor") and cop and (i + 1 == len(R) or R[i + 1].n in ("de", "y", "o")):
            C.attr.append(t.n); i += 1; continue
        if t.n in ("mas", "menos") and i + 1 < len(R) and R[i + 1].pos in ("ADJ",) and pregunta:
            C.comp = (t.n, M.masc(R[i + 1].n), None); i += 2; continue
        # grado + adjetivo / adjetivo(s) -> atributo
        if t.n in GRADO and i + 1 < len(R) and (R[i + 1].pos in ("ADJ",) or (cop and R[i + 1].pos in ("VERB", "ADV", "NOUN") and R[i + 1].n not in PREPS and R[i + 1].n not in ARTS)) and t.n not in ("mas", "menos", "tan"):
            C.grado = t.f.lower(); i += 1; t = R[i]
            C.attr.append(M.masc(t.n)); i += 1
            while i + 1 < len(R) and R[i].n in ("y", "e", ",") and R[i + 1].pos in ("ADJ", "VERB"):
                C.attr.append(M.masc(R[i + 1].n)); i += 2
            continue
        if (t.pos == "ADJ" or (cop and t.pos in ("VERB", "NOUN") and (any(x[1] == "part" for x in M.analizar(t.f)) or any(x[1] == "part" for x in M.analizar(M.masc(t.n)))) and not (i + 1 < len(R) and R[i + 1].pos in ("NOUN", "PROPN", "DET")))) and not _propio(t, 1) and t.n not in QUANT and not (i + 1 < len(R) and R[i + 1].pos == "NOUN" and not cop):
            if cop or C.v in ("sentir", "quedar", "poner", "volver", "encontrar", "andar", "seguir", "llegar", "venir", "ir", "vivir", "dormir"):
                # «es buen amigo» -> SN, no atributo
                if not (i + 1 < len(R) and R[i + 1].pos == "NOUN" and not R[i + 1].cap and R[i + 1].n not in T_SUST):
                    C.attr.append(M.masc(t.n)); i += 1
                    while i + 1 < len(R) and R[i].n in ("y", "e") and R[i + 1].pos in ("ADJ", "VERB"):
                        C.attr.append(M.masc(R[i + 1].n)); i += 2
                    continue
        if cop and i == len(R) - 1 and t.pos in ("VERB", "X", "INTJ", "PRON", "NUM") and not t.cap and t.n not in PREPS and t.n not in ARTS and t.n not in POSS and t.n not in CLIT and t.n not in WH \
                and t.n not in QUANT and t.n not in PRON_S and t.n not in LUGAR_ADV and t.n not in T_ADV and M.numero(t.n) is None and not any(x[1] in ("inf", "ger") for x in M.analizar(t.f)) and len(t.n) > 2:
            C.attr.append(M.masc(t.n)); i += 1; continue
        if t.n in LUGAR_ADV:
            C.lugar_adv = t.n; i += 1; continue
        if t.n in MODO or (t.pos == "ADV" and t.n.endswith("mente")) or (t.n in GRADO and t.n not in ("mas", "menos", "tan", "nada")):
            C.modo.append(t.f.lower()); i += 1; continue
        # infinitivo complemento
        if any(x[1] == "inf" for x in M.analizar(t.f)) and t.pos in ("VERB", "AUX", "NOUN") and (C.v in MODALES or C.v in GUSTAR or (i > 0 and R[i - 1].n in ("a", "de", "que"))):
            resto_x = list(R[i:])
            if pregunta and C.suj is None and C.obj is None and len(resto_x) >= 2:
                for k0 in range(1, len(resto_x)):
                    if _propio(resto_x[k0], 1) and resto_x[k0 - 1].n not in PREPS and resto_x[k0 - 1].n not in ARTS:
                        k1 = k0
                        while k1 < len(resto_x) and _propio(resto_x[k1], 1):
                            k1 += 1
                        C.suj = SN(cab=sa(" ".join(x.f for x in resto_x[k0:k1])), propio=True, nombre=" ".join(x.f if x.cap else x.f.capitalize() for x in resto_x[k0:k1]), texto=" ".join(x.f for x in resto_x[k0:k1]))
                        resto_x = resto_x[:k0] + resto_x[k1:]
                        break
            C.xinf = " ".join(x.f if (x.cap and x.pos == "PROPN") else x.f.lower() for x in resto_x).replace("a el ", "al ").replace("de el ", "del ")
            i = len(R); continue
        if t.n == "que" and C.v == "tener" and i + 1 < len(R) and any(x[1] == "inf" for x in M.analizar(R[i + 1].f)):
            C.modal = "tener que"
            C.xinf = " ".join(x.f.lower() if not (x.cap and x.pos == "PROPN") else x.f for x in R[i + 1:]).replace("a el ", "al ").replace("de el ", "del ")
            i = len(R); continue
        if t.n == "en" and i + 1 < len(R) and R[i + 1].n == "total":
            i += 2; continue
        if t.n == "de" and i + 2 < len(R) and R[i + 1].n in ("los", "las") and R[i + 2].n in ("dos", "tres", "cuatro", "todos", "todas") and i + 3 == len(R):
            i += 3; continue
        if t.n == "como" and i + 1 < len(R) and R[i + 1].pos in ("NOUN", "ADJ", "PROPN", "DET") and C.v in ("trabajar", "actuar", "servir", "empezar", "seguir", "ejercer"):
            r = sn_coord(R, i + 1, nominal=True)
            if r:
                C.comps.append(("como", r[0])); i = r[1]; continue
        if t.n == "bajo" and (i == len(R) - 1 or sn_coord(R, i + 1) is None) and cop:
            C.attr.append("bajo"); i += 1; continue
        if t.n in PREPS:
            if i + 1 < len(R) and any(x[1] == "inf" for x in M.analizar(R[i + 1].f)) and R[i + 1].pos in ("VERB", "AUX"):
                fin_x = len(R)
                for k_t in range(i + 2, len(R)):         # «a pasear todas las mañanas»: el tiempo es de la frase, no del infinitivo
                    te_ = tiempo_expr(R, k_t)
                    if te_ and te_[1] == len(R):
                        fin_x = k_t
                        if te_[2]:
                            C.freq = C.freq or te_[0]
                        else:
                            C.cuando = C.cuando or te_[0]
                        break
                C.comps.append((t.n, SN(cab="", texto=" ".join(x.f.lower() if not (x.cap and x.pos == "PROPN") else x.f for x in R[i + 1:fin_x]))))
                C.xinf = C.xinf or ""
                i = len(R); continue
            if i + 1 < len(R) and R[i + 1].n in LUGAR_ADV:
                C.lugar_adv = R[i + 1].n; i += 2; continue
            r = sn_coord(R, i + 1)
            if not r:
                return None
            C.comps.append((t.n, r[0])); i = r[1]; continue
        r = sn_coord(R, i, nominal=not cop)
        if r:
            s_, j = r
            if C.obj is None:
                C.obj = s_
            elif C.obj2 is None:
                C.obj2 = s_
            else:
                return None
            i = j; continue
        return None
    return C


def resuelve_elipsis(C, cabeza_wh=""):
    """«Mi coche es más viejo que el de Pilar»: «el de Pilar» = «el coche de Pilar». False si no hay antecedente."""
    plano = []
    for x in [C.suj, C.obj]:
        if x is not None:
            plano += x.coord or [x]
    ant = next((x.cab for x in plano if x.cab and x.cab != "*" and not x.propio), "") or cabeza_wh
    todos = plano + [s_ for _, s_ in C.comps] + ([C.comp[2]] if C.comp and C.comp[2] is not None else []) + ([C.obj2] if C.obj2 is not None else [])
    for x in todos:
        for y in (x.coord or [x]):
            if y.cab == "*":
                if not ant:
                    return False
                y.cab = ant
    return True
