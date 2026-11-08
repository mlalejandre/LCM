"""parche-96: MARCOS DE PREGUNTA sin analizador. Responden leyendo directamente los hechos de la memoria cuando el camino normal (analizador + busqueda) ha fallado.
Cubren familias enteras (no frases): si/no de clase/propiedad/posesion/composicion/giro, "que/quien/cual + verbo + X" (sujeto buscado), "que es/como es/que tipo de.. es X",
"de que color", "cuantas Y tiene X", "que lugar ocupa X". Solo contestan cuando hay un hecho que lo sostiene; nunca inventan un "no"."""
import re
from functools import lru_cache

from src.language.lexicon import norm
from src.reasoning.lessons import canon

DET = {"el", "la", "los", "las", "un", "una", "unos", "unas", "al", "del", "lo", "algun", "alguna", "algunos", "algunas"}
STOP = DET | {"color", "tamano", "naturales", "natural", "demas", "de", "en", "a", "que", "y", "por", "con", "se", "hay", "es", "son", "esta", "estan", "para", "como", "cual", "cuales", "quien", "quienes"}
SYN = {"posee": "tiene", "poseen": "tienen", "natural": "", "naturales": "", "satelite": "luna", "satelites": "luna", "mayor": "grande", "menor": "pequeno", "gigantesco": "grande", "enorme": "grande", "diminuto": "pequeno", "astro": "estrella"}
HECHO = re.compile(r"\b(?:hech\w+|compuest\w+|formad\w+|constituid\w+) (?:de|por)\b")
VERBS = {"es": "ser", "son": "ser", "esta": "estar", "estan": "estar", "tiene": "tener", "tienen": "tener", "gira": "giro", "giran": "giro", "orbita": "giro", "orbitan": "giro",
         "rodea": "giro", "rodean": "giro", "hay": "estar", "posee": "tener", "poseen": "tener", "ocupa": "estar", "contiene": "cont", "contienen": "cont"}


def st(w):
    w = SYN.get(w, w)
    return re.sub(r"(os|as|es|o|a|e|s)$", "", w) if len(w) > 3 else w


@lru_cache(maxsize=1 << 18)
def _clave(name):
    """parche-130: la clave normalizada de un nombre se calcula UNA vez (antes se recalculaba por cada hecho y pregunta: coste cuadratico con la memoria)."""
    return " ".join(st(w) for w in norm(name.replace("_", " ")).split())


@lru_cache(maxsize=1 << 18)
def _palabras(obj, pred):
    ws = {st(w) for w in norm(obj.replace("_", " ")).split()}
    if pred.upper().startswith("SER_EL_"):
        ws |= {st(w) for w in pred.lower().split("_")[2:]}
    return frozenset(ws)


def _fam(p, kind):
    p = p.upper()
    if kind == "ser":
        return p in ("ES", "SER") or p.startswith("SER_EL_")
    if kind == "estar":
        return p in ("ESTAR", "ESTAR_EN", "HECHO_DE", "FORMADO_DE", "COMPUESTO_DE", "ES", "SER") or p.startswith("ESTAR")
    if kind == "tener":
        return p.startswith("TENER")
    if kind == "giro":
        return p.endswith("_ALREDEDOR_DE")
    if kind == "cont":
        return p.startswith("TENER") or p in ("HECHO_DE", "FORMADO_DE", "COMPUESTO_DE", "CONJUNTO_DE")
    return False


class Marcos:
    def __init__(self, qa):
        self.qa = qa
        self.facts = [f for f in qa.m.facts if not f.get("neg")]
        self.key = _clave
        self.por_sujeto = {}                                            # parche-130: indice sujeto -> hechos (en el orden de la memoria)
        for f in self.facts:
            self.por_sujeto.setdefault(_clave(f["s"]), []).append(f)
        self.names = {}
        for f in self.facts:
            for x in (f["s"], f["o"]):
                self.names.setdefault(self.key(x), x)
        self.subj_keys = {self.key(f["s"]) for f in self.facts}
        self.classes = {self.key(f["o"]) for f in self.facts if f["p"].upper() == "ES"}
        self.colors = {self.key(f["s"]) for f in self.facts if f["p"].upper() == "ES" and canon(f["o"]) == "COLOR"}
        self.colors |= {st(c) for c in ("rojo", "azul", "verde", "amarillo", "blanco", "negro", "naranja", "marron", "gris", "rosa", "morado", "violeta", "dorado", "plateado", "celeste")}

    # ---- utilidades ----
    def fw(self, f):
        return _palabras(f["o"], f["p"])

    def ents(self, tk):
        """Entidades conocidas en tk: lista de (i, j, clave), las mas largas primero y sin solaparse."""
        out, used = [], set()
        for ln in (3, 2, 1):
            for i in range(len(tk) - ln + 1):
                if used & set(range(i, i + ln)) or tk[i] in STOP:
                    continue
                k = " ".join(st(w) for w in tk[i:i + ln])
                if k in self.names:
                    out.append((i, i + ln, k))
                    used |= set(range(i, i + ln))
        return sorted(out)

    def of(self, key, kind=None):
        return [f for f in self.por_sujeto.get(key, ()) if kind is None or _fam(f["p"], kind)]

    def cover(self, f, q):
        return bool(q) and set(q) <= self.fw(f)

    def says(self, fs):
        out = []
        for f in fs:
            x = self.qa.say((f["s"], f["p"], f["o"])) + "."
            if x not in out:
                out.append(x)
        return " ".join(out[:6])

    def describe(self, key, only_ser=False):
        fs = self.of(key)
        if only_ser:
            fs = [f for f in fs if f["p"].upper() in ("SER", "ES")] or fs
        order = {"ES": 0, "SER_EL": 1, "SER": 2}
        fs = sorted(fs, key=lambda f: order.get(f["p"].upper()[:6] if f["p"].upper().startswith("SER_EL") else f["p"].upper(), 3))
        parts, conj, hecho = [], [], []
        for f in fs:
            p = f["p"].upper()
            if p == "CONJUNTO_DE":
                conj.append(self.qa._disp(f["o"]).lower())
            elif p == "HECHO_DE":
                hecho.append(self.qa._disp(f["o"]).lower())
            else:
                parts.append(f)
        txt = self.says(parts) if parts else ""
        d = self.qa._disp(self.names.get(key, key))
        if conj:
            conj = [re.sub(r"^(el|la|los|las)\s+", "", c) for c in conj]
            txt += f" {d[:1].upper() + d[1:]} es el conjunto de {conj[0] if len(conj) == 1 else ', '.join(conj[:-1]) + ' y ' + conj[-1]}."
        if hecho:
            pl = d.lower().startswith(("los ", "las ")) or d.upper().endswith("S")
            txt += f" {d[:1].upper() + d[1:]} {'están hechos' if pl else 'está hecho'} de {' y '.join(hecho)}."
        return txt.strip() or None

    # ---- familias ----
    def tokens(self, question):
        t = re.sub(r"\s+", " ", re.sub(r"[¡!¿?.,;:]", " ", norm(question))).strip()
        t = HECHO.sub("", t).replace("  ", " ")
        t = re.sub(r"^como se llama\b", "cual es", t)
        t = re.sub(r"^en que lugar (esta|estan)\b", r"donde \1", t)
        t = re.sub(r"\balrededor de quien\b", "alrededor de que", t)
        t = re.sub(r"\bque hay alrededor de\b", "que gira alrededor de", t)
        tk = t.split()
        return tk if len(tk) >= 2 else []

    def responder(self, question):
        """Familias muy especificas: se contestan ANTES que el camino normal (que a veces responde otra cosa)."""
        tk = self.tokens(question)
        for fn in (self.atributo, self.lugar, self.materiales):
            try:
                r = fn(tk) if tk else None
            except Exception:                                   # noqa
                r = None
            if r:
                return r
        return None

    def responder_fallo(self, tk):
        for fn in (self.yn_comp, self.yn_hay, self.existen, self.yn, self.wh_subject, self.cuantos_clase, self.orden, self.ordinal, self.nombre_de, self.donde, self.atributo, self.cuantos, self.lugar, self.describir, self.materiales):
            try:
                r = fn(tk)
            except Exception:                                   # noqa
                r = None
            if r:
                return r
        return None

    def yn(self, tk):
        if tk[0] in ("que", "quien", "quienes", "cual", "cuales", "cuantos", "cuantas", "como", "donde", "cuando", "por", "en", "de", "alrededor"):
            return None
        vi = next((i for i, w in enumerate(tk) if w in VERBS and w != "hay"), None)
        if vi is None:
            return None
        kind = VERBS[tk[vi]]
        rest = tk[:vi] + tk[vi + 1:]
        es = self.ents(rest)
        if kind == "giro" and len(es) >= 2:
            (i1, j1, k1), (i2, j2, k2) = es[0], es[1]
            fs = [f for f in self.of(k1, "giro") if self.key(f["o"]) == k2]
            return "Sí. " + self.says(fs[:1]) if fs else None
        if kind == "giro":
            return None
        for (i, j, k) in es:
            if k not in self.subj_keys:
                continue
            q = [st(w) for idx, w in enumerate(rest) if not (i <= idx < j) and w not in STOP and w not in ("alrededor",)]
            fs = [f for f in self.of(k, kind) if self.cover(f, q)]
            if fs:
                return "Sí. " + self.says(fs[:1])
        return None

    def wh_subject(self, tk):
        if tk[0] not in ("que", "quien", "quienes", "cual", "cuales"):
            return None
        vi = next((i for i, w in enumerate(tk) if w in VERBS and w != "hay" or (w == "hay" and i > 0)), None)
        if vi is None:
            return None
        kind = VERBS[tk[vi]]
        mid = [w for w in tk[1:vi] if w not in DET]
        after = tk[vi + 1:]
        if tk[vi] == "hay" and after[:1] == ["en"]:
            kind = "estar"
        cls = None
        if mid and st(mid[-1]) in self.classes:
            cls = st(mid[-1])
        elif not mid and kind == "ser" and tk[0] in ("cual", "cuales"):
            nxt = [w for w in after if w not in DET]
            if nxt and st(nxt[0]) in self.classes:
                cls, after = st(nxt[0]), nxt[1:]
        elif mid and tk[0] != "que" and kind == "ser":
            return None
        a = list(after)
        while a and a[0] in ("alrededor", "de", "en", "del"):
            a = a[1:]
        if kind == "estar" or tk[vi] == "hay":
            head = []
            for w in a:
                if w in ("de", "del"):
                    break
                head.append(w)
            a = head
        if a[:1] == ["que"] and a[1:2] and a[1] in VERBS:                # "el planeta que tiene anillos"
            kind, a = VERBS[a[1]], a[2:]
        opts = None
        es_ = [e_ for e_ in self.ents(a) if e_[2] in self.subj_keys]
        if "o" in a and len(es_) >= 2:                               # "¿Cual tiene anillos, Saturno o Marte?"
            opts = {k_ for (_, _, k_) in es_}
            a = [w for i_, w in enumerate(a) if w != "o" and not any(i0 <= i_ < j0 for (i0, j0, _) in es_)]
        if kind == "ser" and not cls and tk[0] in ("cual", "cuales"):
            a = a[:a.index("de")] if "de" in a else (a[:a.index("del")] if "del" in a else a)
        q = [st(w) for w in a if w not in STOP and w != "alrededor"]
        if not q:
            return None
        kinds = ("ser", "tener", "estar") if kind == "ser" else (kind,)      # "el planeta de los anillos", "el planeta rojo", "el centro del sistema"
        porsuj = {}
        for f in self.facts:
            if any(_fam(f["p"], k) for k in kinds):
                porsuj.setdefault(self.key(f["s"]), []).append(f)
        res = []
        for sk, fs in porsuj.items():
            if kind == "giro":
                hit = [f for f in fs if self.cover(f, q)]
            else:
                uni = set().union(*[self.fw(f) for f in fs])
                hit = [f for f in fs if self.fw(f) & set(q)] if set(q) <= uni else []
            res += [f for f in hit if f not in res]
        if cls:                                                     # la clase afina, pero no excluye lo que no se sabe de que clase es ("Saturno tiene anillos")
            withc = [f for f in res if any(self.key(g["o"]) == cls for g in self.of(self.key(f["s"]), "ser") if g["p"].upper() == "ES")]
            res = withc or res
        if opts:
            res = [f for f in res if self.key(f["s"]) in opts]
        if res:
            return self.says(res)
        # sujeto conocido, se pregunta por lo que tiene/es: "¿Que tiene Saturno?"
        es = self.ents(a)
        if es and not cls:
            fs = [f for f in self.of(es[0][2], kind)]
            if fs:
                return self.says(fs)
        return None

    def donde(self, tk):
        if tk[0] != "donde" or not any(w in tk for w in ("esta", "estan", "queda", "quedan", "encuentra", "encuentran")):
            return None
        for (_, _, k) in self.ents(tk[1:]):
            fs = [f for f in self.of(k) if f["p"].upper().startswith("ESTAR_EN")]
            if fs:
                return self.says(fs)
        return None

    SIZES = {"pequeno", "grande", "enano", "gigante", "mediano", "inmenso", "minusculo"}

    def atributo(self, tk):
        """"de que color es X" / "que color tiene X" / "de que tamano son X" / "cual es el color|tamano de X"."""
        j = " ".join(tk)
        m = re.match(r"(?:de que |que |cual es el )(color|colores|tamano)(?: es| son| tiene| tienen| de)? (.+)$", j)
        if not m:
            return None
        conj = self.colors if m.group(1).startswith("color") else {st(c) for c in self.SIZES}
        for (_, _, k) in self.ents(m.group(2).split()):
            fs = [f for f in self.of(k, "ser") if self.key(f["o"]) in conj]
            if fs:
                return self.says(fs)
        return None

    def cuantos(self, tk):
        if tk[0] not in ("cuantos", "cuantas") or not any(w in tk for w in ("tiene", "tienen", "hay")):
            return None
        es = self.ents(tk[1:])
        for (i, j, k) in es:
            if k not in self.subj_keys:
                continue
            q = [st(w) for idx, w in enumerate(tk[1:]) if not (i <= idx < j) and w not in STOP and w not in ("tiene", "tienen", "hay")]
            for f in self.of(k, "tener"):
                if self.cover(f, q):
                    o_d = self.qa._disp(f["o"])
                    if f["o"].upper().split("_")[0] in ("DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE", "DIEZ", "UNA", "UN") or o_d.lower().startswith(("dos", "tres", "cuatro")):
                        return self.says([f])
                    if not f["o"].upper().endswith("S"):
                        art = re.sub(r"^(el|la)\s+", lambda m: "un " if m.group(1).lower() == "el" else "una ", o_d, flags=re.I)
                        d = self.qa._disp(f["s"])
                        return f"{d[:1].upper() + d[1:]} tiene {art[:1].lower() + art[1:]}."
                    return self.says([f])
        return None

    def lugar(self, tk):
        j = " ".join(tk)
        if not re.search(r"\b(lugar|posicion|puesto|orden|numero)\b.*\b(ocupa|tiene)\b|\ben que (?:lugar|posicion|puesto) esta\b|\bque (?:lugar|posicion|puesto) (?:ocupa|tiene)\b", j):
            return None
        for (_, _, k) in self.ents(tk):
            fs = [f for f in self.of(k) if f["p"].upper().startswith("SER_EL_") and not f["p"].upper().startswith("SER_EL_MAS")]
            if fs:
                return self.says(fs)
        return None

    def describir(self, tk):
        j = " ".join(tk)
        m = re.match(r"(?:que|como) (?:es|son) (.+)$|que (?:tipo|clase|especie) de \w+ (?:es|son) (.+)$|que (?:sabes|conoces|puedes decir|me puedes decir) (?:de|del|sobre|acerca de) (.+)$|como (?:es|son) (.+)$", j)
        if not m:
            return None
        rest = [w for w in next(g for g in m.groups() if g).split()]
        for (_, _, k) in self.ents(rest):
            if k in self.subj_keys:
                r = self.describe(k, only_ser=j.startswith("como"))
                if r:
                    return r
        return None

    def materiales(self, tk):
        if tk[0] not in ("que", "cual", "cuales", "de", "como"):
            return None
        if not any(w in tk for w in ("forman", "componen", "constituyen", "contienen", "contiene", "compone", "material", "materiales")):
            return None
        for (_, _, k) in self.ents(tk):
            fs = [f for f in self.of(k) if f["p"].upper() in ("HECHO_DE", "FORMADO_DE", "COMPUESTO_DE")]
            if fs:
                return self.describe(k)
        return None


def responder(qa, question, primero=False):
    mc = Marcos(qa)
    tk = mc.tokens(question)
    if not tk:
        return None
    return mc.responder(question) if primero else mc.responder_fallo(tk)


# ---- familias de parche-96 (ronda 2) ------------------------------------------------------------------------------------
ORDS = ["primero", "segundo", "tercero", "cuarto", "quinto", "sexto", "septimo", "octavo", "noveno", "decimo"]
NUMS = {"uno": 0, "un": 0, "una": 0, "1": 0, "dos": 1, "2": 1, "tres": 2, "3": 2, "cuatro": 3, "4": 3, "cinco": 4, "5": 4, "seis": 5, "6": 5, "siete": 6, "7": 6, "ocho": 7, "8": 7, "nueve": 8, "9": 8, "diez": 9, "10": 9}
ORDW = {"primer": 0, "primero": 0, "primera": 0, "segundo": 1, "segunda": 1, "tercer": 2, "tercero": 2, "tercera": 2, "cuarto": 3, "cuarta": 3, "quinto": 4, "quinta": 4,
        "sexto": 5, "sexta": 5, "septimo": 6, "septima": 6, "octavo": 7, "octava": 7, "noveno": 8, "novena": 8, "decimo": 9, "decima": 9}


def _yn_comp(self, tk):
    """"¿Es Jupiter mas grande que la Tierra?": se deduce del superlativo ("Jupiter es el planeta mas grande") si ambos son de la misma clase."""
    j = " ".join(tk)
    m = re.match(r"(?:es|son) (.+?) (mas|menos) (\w+) que (.+)$", j)
    if not m:
        return None
    ea, eb = self.ents(m.group(1).split()), self.ents(m.group(4).split())
    if not ea or not eb:
        return None
    ka, kb, mm, adj = ea[0][2], eb[0][2], m.group(2), st(m.group(3))

    def sup(k):
        return [f for f in self.of(k) if f["p"].upper().startswith("SER_EL_" + mm.upper() + "_") and st(f["p"].lower().split("_", 3)[-1]) == adj]

    def cls(k):
        return {self.key(f["o"]) for f in self.of(k) if f["p"].upper() == "ES"}
    sa, sb = sup(ka), sup(kb)
    if sa and ka != kb and (cls(kb) & {self.key(sa[0]["o"].split("_")[0])}):
        return "Sí. " + self.says(sa[:1])
    if sb and ka != kb and (cls(ka) & {self.key(sb[0]["o"].split("_")[0])}):
        return "No. " + self.says(sb[:1])
    return None


def _yn_hay(self, tk):
    """"¿Hay lunas en Marte?" / "¿Hay anillos en Saturno?"."""
    if tk[0] != "hay" or "en" not in tk:
        return None
    i = tk.index("en")
    es = self.ents(tk[i + 1:])
    q = [st(w) for w in tk[1:i] if w not in STOP]
    for (_, _, k) in es:
        fs = [f for f in self.of(k) if _fam(f["p"], "cont") and self.cover(f, q)]
        if fs:
            return "Sí. " + self.says(fs[:1])
    return None


def _cuantos_clase(self, tk):
    """"¿Cuantos planetas helados conoces?" / "¿Cuantos planetas tienen anillos?" -> recuento con nombres."""
    if tk[0] not in ("cuantos", "cuantas"):
        return None
    words = [w for w in tk[1:] if w not in STOP and w not in ("conoces", "sabes", "existen", "tienen", "tiene", "son", "hay", "conocemos", "tienes")]
    if not words:
        return None
    q = [st(w) for w in words]
    cl = [x for x in q if x in self.classes]
    rest = [x for x in q if x not in cl]
    if not rest:
        return None
    res = {}
    for f in self.facts:
        res.setdefault(self.key(f["s"]), []).append(f)
    names = []
    for sk, fs in res.items():
        uni = set().union(*[self.fw(f) for f in fs])
        if set(rest) <= uni and (not cl or set(cl) & uni or all(x in cl for x in cl) and not any(self.key(g["o"]) in self.classes for g in fs if g["p"].upper() == "ES")):
            names.append(self.names.get(sk, sk))
    withc = [n_ for n_ in names if set(cl) & {self.key(g["o"]) for g in self.of(self.key(n_)) if g["p"].upper() == "ES"}] if cl else []
    names = withc or names
    if not names:
        return None
    disp = [self.qa._disp(n_) for n_ in names]
    disp = [d_[:1].upper() + d_[1:] for d_ in disp]
    joined = disp[0] if len(disp) == 1 else ", ".join(disp[:-1]) + " y " + disp[-1]
    return f"Conozco {len(names)}: {joined}."


def _ord_of(self, key):
    for f in self.of(key):
        p = f["p"].lower()
        if p.startswith("ser_el_") and p[7:] in ORDS:
            return ORDS.index(p[7:]), f["o"]
    for f in self.of(key):
        if f["p"].upper().startswith("SER_EL_MAS_CERCANO"):
            return 0, f["o"]
    return None


def _by_ord(self, idx, noun_key=None):
    for f in self.facts:
        p = f["p"].lower()
        if p == "ser_el_" + ORDS[idx] or (idx == 0 and f["p"].upper().startswith("SER_EL_MAS_CERCANO")):
            if noun_key is None or self.key(f["o"].split("_")[0]) == noun_key:
                return f
    return None


def _orden(self, tk):
    """"¿Que planeta va despues de Venus?" / "antes de" / "viene despues" / "sigue a" / "el siguiente a"."""
    j = " ".join(tk)
    m = re.match(r"(?:que|cual) (\w+) (?:va|viene|esta|sigue|es el siguiente|es el anterior|va justo|viene justo|esta justo|precede) ?(despues|antes|detras|delante)? ?(?:de|a) (.+)$", j)
    if not m:
        return None
    mm_ = re.search(r"\b(siguiente|anterior|sigue|precede)\b", j)
    d = m.group(2) or (("despues" if mm_ and mm_.group(1) in ("siguiente", "sigue") else "antes") if mm_ else None)
    if d is None:
        return None
    d = 1 if d in ("despues", "detras") else -1
    for (_, _, k) in self.ents(m.group(3).split()):
        o = _ord_of(self, k)
        if o and 0 <= o[0] + d < len(ORDS):
            f = _by_ord(self, o[0] + d, self.key(o[1].split("_")[0]))
            if f:
                return self.says([f])
    return None


def _ordinal(self, tk):
    """"¿Cual es el primer planeta desde el Sol?" / "el planeta numero tres" (completa el bloque ordinal de qa.py con 'primero' = el mas cercano)."""
    j = " ".join(tk)
    idx, noun = None, None
    m = re.match(r"(?:que|cual) es (?:el|la) (\w+) (\w+)(?: desde| del| de| al| a)?(?: .+)?$", j)
    if m and m.group(1) in ORDW and st(m.group(2)) in self.classes:
        idx, noun = ORDW[m.group(1)], st(m.group(2))
    if idx is None:
        m = re.match(r"(?:que|cual) es (?:el|la) (\w+) numero (\w+)$", j)
        if m and m.group(2) in NUMS and st(m.group(1)) in self.classes:
            idx, noun = NUMS[m.group(2)], st(m.group(1))
    if idx is None:
        return None
    f = _by_ord(self, idx, noun)
    return self.says([f]) if f else None


def _nombre_de(self, tk):
    """"¿Cual es la estrella del Sistema Solar?" / "¿Cual es el satelite de la Tierra?": la clase (o el nombre de la clase) relacionada con X."""
    j = " ".join(tk)
    m = re.match(r"cual es (?:el|la) (\w+) (?:del|de la|de los|de las|de) (.+)$", j)
    if not m:
        return None
    noun, comp = st(m.group(1)), m.group(2).split()
    ce = self.ents(comp)
    if noun in self.subj_keys and ce:                                   # el satelite (=luna) de la Tierra
        fs = [f for f in self.of(noun) if any(self.key(f["o"]) == k for (_, _, k) in ce)]
        if fs:
            return self.says(fs[:1])
    cands = [sk for sk in self.subj_keys if any(self.key(f["o"]) == noun and f["p"].upper() == "ES" for f in self.of(sk))]
    if len(cands) == 1:
        return self.says([f for f in self.of(cands[0]) if f["p"].upper() == "ES"][:1])
    return None


Marcos.yn_comp, Marcos.yn_hay, Marcos.cuantos_clase, Marcos.orden, Marcos.ordinal, Marcos.nombre_de = _yn_comp, _yn_hay, _cuantos_clase, _orden, _ordinal, _nombre_de


def _existen(self, tk):
    """"¿Existen planetas helados?" / "¿Hay algun planeta rojo?" / "¿Conoces algun planeta con anillos?": si hay al menos uno, se dice cuales."""
    if tk[0] not in ("existe", "existen", "hay", "conoces", "tienes", "sabes") or len(tk) < 2:
        return None
    r = _cuantos_clase(self, ["cuantos"] + [w for w in tk[1:] if w not in ("algun", "alguno", "alguna", "algunos", "algunas", "con", "que", "tengan", "tenga", "sean", "sea")])
    return ("Sí. " + r) if r else None


Marcos.existen = _existen
