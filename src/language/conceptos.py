"""parche-99: DICCIONARIO DE CONCEPTOS. Un concepto es un sentido universal (identificado por un numero, no por una palabra): "perro", "can", "dog", "chien" y "cane" son nombres del MISMO concepto.
Cada concepto trae su lugar en la jerarquia (es un tipo de...), sus partes/miembros/sustancias, su dominio y un vector de rasgos con el que se mide el parecido entre conceptos.
Datos: data/conceptos.json.gz (WordNet 3.0 + Open Multilingual WordNet; licencias en data/CONCEPTOS_LICENCIAS.txt). Sin el fichero todo devuelve vacio. Es el ultimo recurso: la memoria manda."""
import gzip
import json
import math
import os
import re
import unicodedata

_F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "conceptos.json.gz")
_D = None
_O = {}                                                           # palabra normalizada -> como la escribio la persona (con tildes)
LANG = {"es": "español", "en": "inglés", "fr": "francés", "it": "italiano", "pt": "portugués", "ca": "catalán", "gl": "gallego", "eu": "euskera"}
LANG_IN = {"espanol": "es", "castellano": "es", "ingles": "en", "frances": "fr", "italiano": "it", "portugues": "pt", "catalan": "ca", "gallego": "gl", "euskera": "eu", "vasco": "eu"}
DOMINIO = {"noun.animal": "animal", "noun.artifact": "objeto fabricado", "noun.person": "persona", "noun.plant": "planta", "noun.food": "alimento o bebida", "noun.location": "lugar",
           "noun.substance": "sustancia", "noun.body": "parte del cuerpo", "noun.time": "tiempo", "noun.cognition": "idea o conocimiento", "noun.communication": "comunicación",
           "noun.act": "acción", "noun.event": "suceso", "noun.feeling": "sentimiento", "noun.group": "grupo", "noun.object": "objeto natural", "noun.attribute": "cualidad",
           "noun.quantity": "cantidad", "noun.phenomenon": "fenómeno", "noun.shape": "forma", "noun.state": "estado", "noun.possession": "posesión", "noun.relation": "relación",
           "noun.motive": "motivo", "noun.process": "proceso", "noun.Tops": "categoría general"}
TAXON = {"mammalia", "chordata", "euterios", "eutheria", "animalia", "metazoa", "plantae", "magnoliophyta", "tracheophyta", "carnivora", "primates", "aves", "reptilia", "insecta", "arthropoda", "actinopterygii", "dicotiledonea", "magnoliopsida", "liliopsida"}
ALTO = {"object", "physical entity", "entity", "whole", "abstraction", "thing", "natural object", "unit", "conjunto", "entidad", "entidad física", "abstracción", "objeto", "objeto físico", "cosa", "causal agent", "whole", "todo", "unidad", "objeto natural", "artefacto"}
# huecos conocidos del MCR espanol (la palabra existe pero solo como adjetivo o no esta): se enlazan al concepto por su nombre ingles
SUPLEMENTO = {"mamifero": "mammal", "mamiferos": "mammal", "ballena": "whale@cetacean", "delfin": "dolphin@toothed whale", "bicicleta": "bicycle", "cometa": "comet", "azul": "blue", "cuerpo celeste": "celestial body",
              "astro": "celestial body", "ave": "bird", "reptil": "reptile", "anfibio": "amphibian", "insecto": "insect", "pez": "fish", "tierra": "earth", "satelite": "satellite", "asteroide": "asteroid",
              "vehiculo": "vehicle", "herramienta": "tool", "fruta": "fruit", "verdura": "vegetable", "mueble": "furniture", "ropa": "clothing", "metal": "metal", "roca": "rock", "gas": "gas"}
SUPLEMENTO.update({"circulo": "circle@ellipse in which", "esfera": "sphere@a solid figure bounded", "linea": "line@a length (straight or curved) without"})
FORZAR_ES = {"cutlery"}                                                           # etiqueta curada que gana aunque la palabra no figure entre los lemas de OMW
SUPLEMENTO.update({"felino": "feline@", "canido": "canine@carnivorous", "carnivoro": "carnivore@", "herbivoro": "herbivore@", "roedor": "rodent@", "primate": "primate@", "ungulado": "ungulate@", "cetaceo": "cetacean@",
                   "marsupial": "marsupial@", "artropodo": "arthropod@", "molusco": "mollusk@", "crustaceo": "crustacean@", "martes": "Tuesday@third day", "lunes": "Monday@", "miercoles": "Wednesday@", "jueves": "Thursday@",
                   "viernes": "Friday@", "sabado": "Saturday@", "domingo": "Sunday@", "vegetal": "plant@a living organism", "animal": "animal@a living organism", "martillo": "hammer@hand tool", "lapiz": "pencil@writing implement", "tijeras": "scissors@edge tool", "tijera": "scissors@edge tool", "tenedor": "fork@cutlery", "rana": "frog@tailless",
                   "corazon": "heart@hollow muscular organ", "reina": "queen@female sovereign", "fuego": "fire@process of combustion", "papel": "paper@material made of cellulose", "cuaderno": "notebook@book with blank pages",
                   "mochila": "backpack@bag carried", "gafas": "eyeglasses@optical instrument", "falda": "skirt@garment", "guante": "glove@handwear: covers", "cinturon": "belt@band to tie", "peine": "comb@flat device",
                   "cepillo": "brush@implement", "horno": "oven@kitchen appliance", "sello": "stamp@small adhesive token", "equipo": "team@cooperative unit", "cama": "bed@piece of furniture", "llave": "key@metal device",
                   "gallo": "cock@adult male chicken", "perro": "dog@member of the genus Canis", "gato": "cat@feline mammal", "caballo": "horse@solid-hoofed", "vaca": "cow@female of domestic cattle", "oveja": "sheep@woolly",
                   "cerdo": "pig@domestic swine", "pato": "duck@small wild or domestic", "conejo": "rabbit@any of various burrowing", "raton": "mouse@any of numerous small rodents", "mono": "monkey@any of various long-tailed",
                   "elefante": "elephant@five-toed pachyderm", "lobo": "wolf@any of various predatory", "oso": "bear@massive plantigrade", "zorro": "fox@alert carnivorous mammal", "tortuga": "turtle@any of various aquatic",
                   "lluvia": "rain@water falling in drops", "nube": "cloud@visible mass of water", "viento": "wind@air moving", "cielo": "sky@atmosphere and outer space", "estrella": "star@(astronomy) a celestial body",
                   "montana": "mountain@land mass that projects", "rio": "river@large natural stream", "mar": "sea@division of an ocean", "arbol": "tree@tall perennial woody plant", "flor": "flower@reproductive organ",
                   "hoja": "leaf@organ of photosynthesis", "fruta": "fruit@edible reproductive body", "manzana": "apple@fruit with red or yellow", "naranja": "orange@round yellow to orange fruit", "platano": "banana@elongated crescent-shaped",
                   "pan": "bread@food made from dough", "leche": "milk@a white nutritious liquid", "agua": "water@binary compound", "sal": "salt@white crystalline", "azucar": "sugar@a white crystalline carbohydrate",
                   "casa": "house@a dwelling", "coche": "car@a motor vehicle", "ciudad": "city@a large and densely populated", "pais": "country@a politically organized", "escuela": "school@an educational institution",
                   "libro": "book@a written work", "mesa": "table@a piece of furniture having a smooth flat top", "silla": "chair@a seat for one person", "ventana": "window@a framework of wood", "puerta": "door@a swinging or sliding barrier"})
_ART = {"un", "una", "unos", "unas", "el", "la", "los", "las", "al", "del", "lo", "tipo", "clase", "de", "cierto", "algun", "alguna", "otro", "otra"}


def nrm(w):
    w = unicodedata.normalize("NFD", str(w).lower().replace("_", " "))
    return re.sub(r"\s+", " ", "".join(c for c in w if unicodedata.category(c) != "Mn")).strip()


def _st(w):
    w = nrm(w)
    return re.sub(r"(os|as|es|o|a|e|s)$", "", w) if len(w) > 3 else w


def _vo(w):
    return _O.get(nrm(w), w)


def _marcar(raw):
    global _O
    _O = {nrm(w): w for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑüÜ]+", str(raw))}


def _sing(w):
    for suf, rep in (("ces", "z"), ("es", ""), ("s", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            yield w[:-len(suf)] + rep


def _load():
    global _D
    if _D is not None:
        return _D
    _D = {"ok": False}
    try:
        with gzip.open(_F, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return _D
    n = len(d["ids"])
    lem = {lg: {int(k): v for k, v in x.items()} for lg, x in d["lem"].items()}
    idx = {}                                                      # palabra normalizada -> [(lengua, concepto)]
    for lg, x in lem.items():
        for c, ws in x.items():
            for w in ws:
                idx.setdefault(nrm(w), []).append((lg, c))
    rev = {}
    for c, ts in d["hyp"].items():
        for t in ts:
            rev.setdefault(t, []).append(int(c))
    _D = {"ok": True, "n": n, "pos": [i[-1] for i in d["ids"]], "lex": d["lex"], "lexnames": {int(k): v for k, v in d["lexnames"].items()}, "gloss": d["gloss"], "freq": d["freq"],
          "lem": lem, "idx": idx, "hyp": {int(k): v for k, v in d["hyp"].items()}, "hypo": rev, "parte": {int(k): v for k, v in d["parte"].items()},
          "miembro": {int(k): v for k, v in d["miembro"].items()}, "sustancia": {int(k): v for k, v in d["sustancia"].items()}, "ant": {int(k): v for k, v in d["ant"].items()}, "vec": {}, "fen": {int(k): v for k, v in d.get("fen", {}).items()}}
    return _D


def disponible():
    return _load()["ok"]


def total():
    return _load().get("n", 0) if disponible() else 0


# ---- palabras <-> conceptos --------------------------------------------------------------------------------------------
def conceptos(palabra, lengua=None, solo_nombres=True):
    """Conceptos (ordenados por uso) a los que se refiere la palabra, en cualquier lengua. Si la palabra existe en espanol, solo se miran los sentidos del espanol."""
    d = _load()
    if not d["ok"]:
        return []
    w = nrm(palabra)
    w0 = w
    hits = d["idx"].get(w)
    if not hits or w.endswith("s"):                                  # "gatos": si el singular existe y se usa mas, manda el singular (el plural exacto puede ser otro concepto: gatos = latigo)
        for s_ in _sing(w):
            h2 = d["idx"].get(s_)
            if h2 and (not hits or max(d["freq"][c] for _l, c in h2 if _l == "es" or not any(x[0] == "es" for x in h2)) > max(d["freq"][c] for _l, c in hits)):
                hits, w = h2, s_
                break
    pre = []
    if (w0 in SUPLEMENTO or w in SUPLEMENTO) and lengua is None:                       # huecos del MCR: el concepto va primero
        lem_, _, pista = SUPLEMENTO[w0 if w0 in SUPLEMENTO else w].partition("@")
        lem_ = lem_.lower()
        pre = [c for lg_, c in d["idx"].get(lem_, []) if lg_ == "en" and (not solo_nombres or d["pos"][c] == "n") and pista in d["gloss"][c]]
        pre.sort(key=lambda c: (-d["fen"].get(c, {}).get(lem_, 0), -d["freq"][c]))
        pre = pre[:1]
    if not hits and not pre:
        return []
    hits = hits or []
    if lengua:
        hits = [h for h in hits if h[0] == lengua]
    elif any(h[0] == "es" for h in hits):
        hits = [h for h in hits if h[0] == "es"]
    cs = []
    for _lg, c in hits:
        if c not in cs and (not solo_nombres or d["pos"][c] == "n"):
            cs.append(c)
    en_ = lengua == "en" or not any(h[0] == "es" for h in d["idx"].get(nrm(palabra), []) or [])
    cs = sorted(cs, key=lambda c: (-_peso(c, w, en_), -d["freq"][c]))
    return pre + [c for c in cs if c not in pre]


_REGISTRO = re.compile(r"^(?:\((?:slang|informal|vulgar|offensive|derogatory|mythology)|insulting|a coarse|a person who is|someone who is|a (?:stupid|foolish|despicable)|terms? (?:of|for)|disparaging|\(roman|\(greek|\(often followed|\(usually|alternative names? for|type genus|genus of|family of|an? (?:genus|family|order|class) )", re.I)


def _peso(c, w, en_):
    """Peso de un sentido para ordenar: el uso del lema SOLO si la palabra es inglesa (una palabra espanola puede coincidir por azar con un lema ingles: mesa, pan, sol); los sentidos
    vulgares, figurados o mitologicos pierden peso. Los nombres propios (mayuscula) tambien."""
    d = _D
    p = d["fen"].get(c, {}).get(w, 0) if en_ else 0
    if _REGISTRO.match(d["gloss"][c]) or all(x[:1].isupper() for x in d["lem"]["en"].get(c, ["x"])):
        p -= 100000
    return p


def lengua_de(palabra):
    d = _load()
    w = nrm(palabra)
    hits = list(d["idx"].get(w) or [])
    if not any(lg == "es" for lg, _ in hits):                         # "gatos": el plural cuenta como la palabra espanola "gato"
        for s_ in _sing(w):
            hits += [h for h in d["idx"].get(s_, []) if h[0] == "es"]
    return sorted({lg for lg, _ in hits})


# nombres espanoles corrientes de categorias que el MCR da solo en latin cientifico o no da (parche-105)
ETIQUETA_ES = {"mammal": "mamífero", "carnivore": "carnívoro", "bird": "ave", "reptile": "reptil", "amphibian": "anfibio", "insect": "insecto", "fish": "pez", "vertebrate": "vertebrado", "plant": "planta",
                "fruit": "fruta", "vegetable": "verdura", "tool": "herramienta", "vehicle": "vehículo", "furniture": "mueble", "wheeled vehicle": "vehículo con ruedas", "primate": "primate", "rodent": "roedor",
                "feline": "felino", "canine": "cánido", "herbivore": "herbívoro", "ungulate": "ungulado", "cetacean": "cetáceo", "marsupial": "marsupial", "arthropod": "artrópodo", "mollusk": "molusco",
                "crustacean": "crustáceo", "musical instrument": "instrumento musical", "container": "recipiente", "building": "edificio", "food": "alimento", "beverage": "bebida", "liquid": "líquido",
                "celestial body": "cuerpo celeste", "body part": "parte del cuerpo", "weapon": "arma", "device": "dispositivo", "machine": "máquina", "utensil": "utensilio", "placental": "mamífero placentario",
                "chordate": "cordado", "organism": "ser vivo", "animal": "animal", "poultry": "ave de corral", "domestic animal": "animal doméstico", "pachyderm": "paquidermo", "equine": "équido", "bovine": "bóvido",
                "clothing": "ropa", "garment": "prenda", "footwear": "calzado", "jewelry": "joyería", "toy": "juguete", "appliance": "electrodoméstico", "electronic equipment": "equipo electrónico", "cutlery": "cubiertos"}


def etiqueta(c, lengua="es"):
    """Nombre del concepto en una lengua (la palabra sencilla mas corta primero); None si no tiene."""
    d = _load()
    ws = d["lem"].get(lengua, {}).get(c)
    if lengua == "es":
        for e in d["lem"]["en"].get(c, []):
            if e in ETIQUETA_ES and (not ws or e in FORZAR_ES or ETIQUETA_ES[e] in ws or any(w.lower() in TAXON for w in ws)):
                return ETIQUETA_ES[e]
    if not ws:
        return None
    gen = {x.lower() for x in d["lem"]["en"].get(c, []) if x[:1].isupper()}                  # nombre cientifico (fagus, albizia): solo si no hay otro
    ws2 = [w for w in ws if w.lower() not in gen] or ws
    ok = [w for w in ws2 if " " not in w and not w[:1].isupper()] or [w for w in ws2 if not w[:1].isupper()] or ws2
    return ok[0]


def nombres(c, lengua="es"):
    ws = list(_load()["lem"].get(lengua, {}).get(c, []))
    return [w for w in ws if " " not in w] + [w for w in ws if " " in w]


def _label(c):
    return etiqueta(c) or etiqueta(c, "en")


# ---- jerarquia y caracteristicas ----------------------------------------------------------------------------------------
def ascendentes(c, max_niv=12):
    """{concepto: distancia} de c hacia arriba (incluye c con 0)."""
    d = _load()
    out, cur = {c: 0}, [c]
    for niv in range(1, max_niv + 1):
        nxt = []
        for x in cur:
            for t in d["hyp"].get(x, []):
                if t not in out:
                    out[t] = niv
                    nxt.append(t)
        cur = nxt
        if not cur:
            break
    return out


OMITIR = {"mamífero placentario", "cordado", "euterios", "ser vivo"}                       # categorias reales pero poco informativas para una persona


def cadena(c, n=5):
    """Camino principal hacia arriba con nombres en espanol (sin los niveles demasiado abstractos)."""
    d = _load()
    es, en, x, vistos = [], [], c, set()
    while x is not None and x not in vistos:
        vistos.add(x)
        if x != c:
            for lab, dst in ((etiqueta(x), es), (etiqueta(x, "en"), en)):
                if lab and lab.lower() not in ALTO and lab.lower() not in TAXON and lab not in dst and lab not in OMITIR:
                    dst.append(lab)
        ts = d["hyp"].get(x, [])
        x = ts[0] if ts else None
    return (es if len(es) >= 2 else es + [e for e in en if e not in es])[:n]


def es_genero(x):
    """True si el concepto es un genero o taxon cientifico (fagus, albizia): su nombre en espanol es el latin."""
    e = (etiqueta(x) or "").lower()
    return any(w[:1].isupper() and w.lower() == e for w in _load()["lem"]["en"].get(x, []))


def tipos(c, n=8):
    """Subtipos directos con nombre en espanol, los mas usados primero."""
    d = _load()
    hs = [h for h in d["hypo"].get(c, []) if etiqueta(h) and not es_genero(h)]
    hs.sort(key=lambda h: -d["freq"][h])
    out = []
    for h in hs:
        e = etiqueta(h)
        if e not in out and nrm(e) != nrm(etiqueta(c) or ""):
            out.append(e)
    return out[:n]


def partes(c, clave="parte", n=6):
    d = _load()
    out = []
    for t in d[clave].get(c, []):
        e = etiqueta(t)
        if e and e not in out:
            out.append(e)
    return out[:n]


def dominio(c):
    d = _load()
    return DOMINIO.get(d["lexnames"].get(d["lex"][c], ""), "")


def caracteristicas(c):
    """Ficha del concepto: lo que el LCM 'sabe' de el desde fabrica."""
    d = _load()
    return {"nombres": nombres(c), "en": nombres(c, "en")[:3], "tipo_de": cadena(c), "dominio": dominio(c), "partes": partes(c, "parte"), "miembros": partes(c, "miembro"), "sustancias": partes(c, "sustancia"),
            "subtipos": tipos(c), "glosa": d["gloss"][c]}


# ---- vectores y parecido -------------------------------------------------------------------------------------------------
def vector(c):
    """Vector disperso de rasgos del concepto: el mismo concepto y sus antepasados (peso decreciente), su dominio y sus partes."""
    d = _load()
    v = d["vec"].get(c)
    if v is None:
        v = {}
        for a, niv in ascendentes(c).items():
            v[("c", a)] = 0.75 ** niv
        v[("d", d["lex"][c])] = 0.6
        for k in ("parte", "miembro", "sustancia"):
            for t in d[k].get(c, []):
                v[(k, t)] = 0.4
        try:
            from src.language import definiciones as _df                  # parche-105: lo que menciona su definicion y lo que hace aportan rasgos
            X = _df._load()
            if X["ok"]:
                for t in X["gl"].get(c, []):
                    v[("g", t)] = 0.25
                for t in X["deriv"].get(c, []):
                    v[("g", t)] = max(v.get(("g", t), 0), 0.3)
                u = X["uso"].get(c)
                if u and u[0] is not None:
                    v[("g", u[0])] = 0.35
        except ImportError:
            pass
        d["vec"][c] = v
    return v


def coseno(a, b):
    va, vb = vector(a), vector(b)
    num = sum(x * vb[k] for k, x in va.items() if k in vb)
    den = math.sqrt(sum(x * x for x in va.values())) * math.sqrt(sum(x * x for x in vb.values()))
    return num / den if den else 0.0


def comun(a, b):
    """Antepasado comun mas cercano (concepto, dist_a, dist_b) o None; entre los casi igual de cercanos prefiere el que tiene nombre en espanol."""
    aa, bb = ascendentes(a), ascendentes(b)
    cand = sorted((aa[x] + bb[x], x) for x in set(aa) & set(bb))
    if not cand:
        return None
    mejor = cand[0][0]
    for k, x in cand:
        if k > mejor + 1:
            break
        lab = etiqueta(x)
        if lab and lab.lower() not in TAXON and lab.lower() not in ALTO:
            return (x, aa[x], bb[x])
    x = cand[0][1]
    return (x, aa[x], bb[x])


def es_un(a, b):
    """Distancia si el concepto a es (o es tipo de) b; None si no."""
    return ascendentes(a).get(b)


# ---- memoria: entidades con clase ----------------------------------------------------------------------------------------
def _clases_memoria(mem, nombre):
    k = nrm(nombre)
    return [str(f["o"]) for f in getattr(mem, "facts", []) if not f.get("neg") and str(f["p"]).upper() == "ES" and nrm(f["s"]) == k]


def _vis(mem, k, clase=False):
    """Nombre tal como lo escribio la persona (sin articulo)."""
    v = (getattr(mem, "display", {}) or {}).get(str(k)) or str(k).replace("_", " ")
    v = re.sub(r"^(?:el|la|los|las|un|una)\s+", "", v, flags=re.I)
    if v.isupper():
        v = v.capitalize()
    return v.lower() if clase else (v if v[:1].isupper() else v.capitalize())


def _es_clase(mem, k):
    """True si el sujeto de memoria k es una CLASE (alguien es un k, o se escribe en minuscula / con articulo): 'perro', 'pez'. Rex o Marte son entidades."""
    kk = nrm(k)
    for f in getattr(mem, "facts", []):
        if str(f["p"]).upper() == "ES" and nrm(f["o"]) == kk:
            return True
    v = (getattr(mem, "display", {}) or {}).get(str(k)) or ""
    v = re.sub(r"^(?:el|la|los|las|un|una|unos|unas)\s+", "", v)
    return bool(v) and v[:1].islower()


def _resolver(txt, mem):
    """('ent', nombre, clase, [conceptos]) | ('con', palabra, None, [conceptos]) | None"""
    t = " ".join(w for w in nrm(txt).split() if w not in _ART) or nrm(txt)
    for f in getattr(mem, "facts", []):
        if nrm(f["s"]) == t and str(f["p"]).upper() == "ES" and not f.get("neg") and not (_es_clase(mem, f["s"]) and conceptos(t)):
            for cl in _clases_memoria(mem, f["s"]):
                cs = conceptos(cl)
                if cs:
                    return ("ent", _vis(mem, f["s"]), _vis(mem, cl, True), cs)
    cs = conceptos(t)
    orig = " ".join(_vo(w) for w in re.sub(r"[¡!¿?.,;:]", " ", str(txt)).split() if nrm(w) not in _ART) or t
    return ("con", orig, None, cs) if cs else None


def _ruta(c, objetivo):
    x, out = c, []
    d = _load()
    while x is not None:
        lab = etiqueta(x)
        if lab and lab.lower() not in TAXON and lab not in out and (lab not in OMITIR or x == objetivo or x == c):
            out.append(lab)
        if x == objetivo:
            return out
        nxt = None
        for t in d["hyp"].get(x, []):
            if objetivo in ascendentes(t):
                nxt = t
                break
        x = nxt
    return out


# ---- preguntas -----------------------------------------------------------------------------------------------------------
def _lista(xs):
    xs = [x for x in xs if x]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1] if xs else ""


def describir(palabra, mem=None):
    """Ficha en prosa del concepto al que se refiere la palabra (sentido mas usado)."""
    cs = conceptos(palabra)
    if not cs:
        try:
            from src.language import definiciones as _df                  # parche-105: adjetivos y verbos (abstracto, correr)
            return _df.describir_otro(palabra)
        except ImportError:
            return None
    c = cs[0]
    ft = caracteristicas(c)
    palabra = _vo(palabra)
    ft["tipo_de"] = [x for x in ft["tipo_de"] if nrm(x) != nrm(palabra)]
    nom = palabra if (any(nrm(n_) == nrm(palabra) for n_ in ft["nombres"]) or nrm(palabra) in SUPLEMENTO or not ft["nombres"]) else (ft["nombres"][0] if ft["nombres"] else (ft["en"][0] if ft["en"] else palabra))
    lg = lengua_de(palabra)
    pre = ""
    if lg and "es" not in lg and nrm(palabra) not in SUPLEMENTO:
        pre = f"«{palabra}» es una palabra en {LANG.get(lg[0], lg[0])} que nombra el concepto «{nom}». " if nom != palabra else ""
    out = pre + f"«{nom}»"
    if ft["tipo_de"]:
        out += " es un tipo de " + _lista([f"«{x}»" for x in ft["tipo_de"][:3]])
        if len(ft["tipo_de"]) > 3:
            out += f" (y, más en general, {_lista([f'«{x}»' for x in ft['tipo_de'][3:5]])})"
    elif ft["dominio"]:
        out += f" es un concepto de tipo {ft['dominio']}"
    out += "."
    if ft["dominio"] and ft["tipo_de"]:
        out += f" Dominio: {ft['dominio']}."
    otros = [n_ for n_ in ft["nombres"] if nrm(n_) != nrm(nom) and nrm(n_) != nrm(palabra) and " " not in n_][:4]
    if otros:
        out += f" Otras palabras para el mismo concepto: {_lista(otros)}."
    if ft["en"]:
        out += f" En inglés: {_lista(ft['en'][:3])}."
    for k, txt in (("partes", "Partes"), ("miembros", "Miembros"), ("sustancias", "Hecho de")):
        if ft[k]:
            out += f" {txt}: {_lista(ft[k][:5])}."
    try:
        from src.language import definiciones as _df                  # parche-105: para que sirve, actividad, contrarios, lo que menciona su definicion
        for x in _df.ampliar(c, palabra):
            out += " " + x
    except ImportError:
        pass
    if ft["subtipos"]:
        out += f" Algunos tipos: {_lista(ft['subtipos'][:6])}."
    if len(cs) > 1:
        alt = [x for x in (cadena(c2, 1) for c2 in cs[1:3]) if x]
        if alt:
            out += f" (La palabra también puede referirse a otros conceptos, como un tipo de {_lista(['«' + a[0] + '»' for a in alt])}.)"
    return out


def _split_terms(tk, mem):
    """Parte una lista de palabras en X e Y: devuelve (X, Y) donde ambos se resuelven."""
    for i in range(1, len(tk)):
        a, b = " ".join(tk[:i]), " ".join(tk[i:])
        if i <= 3 and len(tk) - i <= 3:
            ra, rb = _resolver(a, mem), _resolver(b, mem)
            if ra and rb:
                return ra, rb
    return None


def _sino(ra, rb, igual=True):
    for ca in ra[3]:                                             # primero: nombres del MISMO concepto (can = perro) en cualquiera de sus sentidos
        if ca in rb[3]:
            if ra[0] == "ent":
                return True, f"{ra[1]} es un {ra[2]}, y «{rb[1]}» es otro nombre del mismo concepto."
            if not igual:
                return True, f"«{ra[1]}» es un «{rb[1]}» (en mi diccionario nombran el mismo concepto)."
            return True, f"«{ra[1]}» y «{rb[1]}» son nombres del mismo concepto («{etiqueta(ca) or etiqueta(ca, 'en')}»)."
    for ca in ra[3][:4]:
        for cb in rb[3][:4]:
            dist = es_un(ca, cb)
            if dist is not None:
                if dist == 0:
                    return True, f"«{rb[1]}» y «{ra[2] or ra[1]}» nombran el mismo concepto." if ra[0] == "ent" else f"«{ra[1]}» y «{rb[1]}» son nombres del mismo concepto («{etiqueta(ca) or etiqueta(ca, 'en')}»)."
                rr_ = _ruta(ca, cb)
                rr_[0] = (ra[2] if ra[0] == "ent" else ra[1]).lower()
                if nrm(rr_[-1]) != nrm(rb[1]):
                    rr_.append(rb[1])
                ruta = " → ".join(rr_)
                if ra[0] == "ent":
                    return True, f"{ra[1]} es un {ra[2]} (según lo que me has contado) y, en mi diccionario de conceptos, un «{ra[2]}» es un tipo de «{rb[1]}» ({ruta})."
                return True, f"un «{ra[1]}» es un tipo de «{rb[1]}» ({ruta})."
    for ca in ra[3][:4]:
        for cb in rb[3][:4]:
            if es_un(cb, ca) is not None:
                return False, f"no exactamente: «{rb[1]}» es un tipo de «{ra[1]}», no al revés."
    return None, ""


def _propio(raw):
    """True si hay un nombre propio (palabra con mayuscula que no abre la frase): no se inventan sentidos de nombres propios."""
    ws = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑüÜ]+", raw)
    return any(w[:1].isupper() for w in ws[1:])


def responder(raw, mem=None):
    """Contesta con el diccionario de conceptos. None si no aplica o no sabe (la memoria manda siempre)."""
    if not disponible():
        return None
    _marcar(raw)
    if _propio(raw) and not re.match(r"[¿\s]*(?:es|son)\b", nrm(raw)) and not re.search(r"\b(?:se parecen|en comun)\b", nrm(raw)):
        return None
    t = re.sub(r"\s+", " ", re.sub(r"[¡!¿?.,;:\"«»]", " ", nrm(raw))).strip()
    try:
        from src.language import definiciones as _df                  # parche-105: grafo de definiciones (para que sirve, relacion entre, intruso, analogias, ejemplos...)
        r_ = _df.responder(re.sub(r"\s+", " ", re.sub(r"[¡!¿?.;\"«»]", " ", nrm(raw))).strip().replace(" :", ":"), raw, mem) or _df.responder(t, raw, mem)
        if r_:
            return r_
    except ImportError:
        pass
    # traduccion
    m = re.match(r"(?:como )?se dice (.+?) en (\w+)$", t) or re.match(r"(?:cual es|dime|dame) (?:la palabra para |el nombre de |la traduccion de )?(.+?) en (\w+)$", t) \
        or re.match(r"(?:como )?(?:se llama|se traduce) (.+?) en (\w+)$", t) or re.match(r"traduce (.+?) al (\w+)$", t)
    if m and m.group(2) in LANG_IN:
        pal, lg = " ".join(_vo(w) for w in m.group(1).split() if w not in _ART), LANG_IN[m.group(2)]
        cs = conceptos(pal)
        if not cs:
            return None
        for c in cs[:3]:
            ws = nombres(c, lg)
            ws = [w for w in ws if nrm(w) != nrm(pal)]
            if ws:
                return f"En {LANG[lg]}, «{pal}» se dice {_lista(['«' + w + '»' for w in ws[:4]])}."
        return None
    m = re.match(r"(?:que )?(?:significa|quiere decir|es) (?:la palabra |el termino )?(?:un |una |el |la )?(\w+)$", t) or re.match(r"que es (?:un |una |el |la )?(\w+)$", t)
    if m:
        pal = m.group(1)
        if mem is not None and any(nrm(f["s"]) == pal and not (_es_clase(mem, f["s"]) and conceptos(pal)) for f in getattr(mem, "facts", [])):
            return None
        r = describir(pal, mem)
        if r:
            return "Según mi diccionario de conceptos: " + r
        return None
    m = re.match(r"(?:que|cuales) (?:caracteristicas|rasgos|propiedades|cosas) (?:tiene|tienen|definen|hay en|identifican a) (?:un |una |el |la |los |las )?(\w+)$", t) \
        or re.match(r"como es (?:un |una |el |la )?(\w+)$", t) or re.match(r"(?:describeme|descr[ií]beme|describe) (?:un |una |el |la )?(\w+)$", t)
    if m and not (mem is not None and any(nrm(f["s"]) == m.group(1) and not (_es_clase(mem, f["s"]) and conceptos(m.group(1))) for f in getattr(mem, "facts", []))):
        r = describir(m.group(1), mem)
        return ("Según mi diccionario de conceptos: " + r) if r else None
    m = re.match(r"(?:que )?(?:partes|piezas|componentes) (?:tiene|tienen|forman) (?:un |una |el |la |los |las )?(\w+)$", t)
    if m:
        for c in conceptos(m.group(1))[:3]:
            ps = partes(c, "parte", 8)
            if ps:
                return f"Según mi diccionario de conceptos, «{_vo(m.group(1))}» tiene como partes: {_lista(ps)}."
        return None
    m = re.match(r"(?:de )?que (?:esta hecho|esta hecha|se compone|esta compuesto|esta compuesta|material es) (?:un |una |el |la )?(\w+)$", t)
    if m:
        for c in conceptos(m.group(1))[:3]:
            ps = partes(c, "sustancia", 6)
            if ps:
                return f"Según mi diccionario de conceptos, «{_vo(m.group(1))}» está hecho de: {_lista(ps)}."
        return None
    m = re.match(r"(?:que )?(?:tipos|clases|variedades|especies) de (\w+) (?:hay|existen|conoces|conoce|sabes)$", t) or re.match(r"(?:dime|dame|cita|nombra) (?:algunos |unos )?(?:tipos|ejemplos) de (\w+)$", t)
    if m:
        for c in conceptos(m.group(1))[:3]:
            ts = tipos(c, 10)
            if ts:
                return f"Según mi diccionario de conceptos, algunos tipos de «{_vo(m.group(1))}» son: {_lista(ts)}."
        return None
    # parecido
    m = re.match(r"en que se parecen (.+?) y (.+)$", t) or re.match(r"que (?:tienen|tiene) en comun (.+?) y (.+)$", t) or re.match(r"que (?:tienen|tiene) (.+?) y (.+) en comun$", t) \
        or re.match(r"(?:que )?(?:es )?(?:lo )?(?:mismo|parecido|distinto|diferente) (?:es )?(.+?) (?:y|que|de) (.+)$", t)
    if m:
        ra, rb = _resolver(m.group(1), mem), _resolver(m.group(2), mem)
        if ra and rb:
            ca, cb = max(((x, y) for x in ra[3][:3] for y in rb[3][:3]), key=lambda xy: coseno(*xy))
            cm = comun(ca, cb)
            if cm:
                lab = etiqueta(cm[0]) or ((etiqueta(cm[0], "en") or "") + " (nombre en inglés)")
                sim = coseno(ca, cb)
                if sim < 0.1:
                    return f"Según mi diccionario de conceptos, «{ra[2] or ra[1]}» y «{rb[2] or rb[1]}» tienen muy poco en común (parecido entre conceptos: {sim:.2f} sobre 1)."
                if lab and lab.lower() not in ALTO or (lab and sim > 0.5):
                    return f"Según mi diccionario de conceptos, «{ra[2] or ra[1]}» y «{rb[2] or rb[1]}» son tipos de «{lab}» (parecido entre conceptos: {sim:.2f} sobre 1)."
                return f"Según mi diccionario de conceptos, solo comparten una categoría muy general («{lab}»; parecido {sim:.2f} sobre 1)."
        return None
    # es un / son el mismo concepto
    m = re.match(r"(?:es|son) (.+)$", t) or re.match(r"(.+?) (?:es|son) (?:un |una )?(?:tipo de |clase de |lo mismo que |sinonimo de |otro nombre de |otra forma de decir )(.+)$", t)
    if m:
        tk = [w for w in (m.group(1) + (" " + m.group(2) if m.lastindex == 2 else "")).split() if w not in {"un", "una", "unos", "unas", "el", "la", "los", "las", "tipo", "clase", "mismo", "que", "sinonimo", "nombre", "otro", "otra", "forma", "decir"}]
        if m.lastindex == 2:
            rr = (_resolver(m.group(1), mem), _resolver(m.group(2), mem))
            sp = rr if rr[0] and rr[1] else None
        else:
            sp = _split_terms(tk, mem)
        if sp:
            ra_, rb_ = sp
            if ra_[0] == "ent" and rb_[0] == "ent":
                return None
            ok, why = _sino(*sp, igual=bool(re.search(r"lo mismo|sinonimo|otro nombre|otra forma", t)))
            if ok is True:
                return "Sí, " + why
            if ok is False:
                return "No, " + why
            ra, rb = sp
            if ra[0] == "ent" and rb[0] == "con" and not any(es_un(y, x) is not None for x in ra[3][:4] for y in rb[3][:4]):
                return f"No, según lo que me has contado {ra[1]} es un {ra[2]}, y en mi diccionario de conceptos un «{ra[2]}» no es un tipo de «{rb[1]}»."
            if all(x[0] == "con" for x in sp):
                ca, cb = ra[3][0], rb[3][0]
                if not any(es_un(x, y) is not None or es_un(y, x) is not None for x in ra[3][:4] for y in rb[3][:4]):
                    return f"Según mi diccionario de conceptos, no: «{ra[1]}» y «{rb[1]}» son conceptos distintos y ninguno es un tipo del otro."
    return None


_SIM = re.compile(r"(?:y )?(?:dime |dame |dinos |nombra |cita )?(?:algunas |unas |las |otras )?(?:palabras |cosas |conceptos |terminos )?(?:similares|parecid\w+|relacionad\w+|afines|cercan\w+) (?:a|con|de) (?:un |una |el |la |los |las )?(\w+)$")
_SIM2 = re.compile(r"(?:y )?(?:que|con que) (?:cosas |conceptos |palabras )?(?:se parece|se parecen|se relaciona|se relacionan|esta relacionad\w+) (?:a|con) (?:un |una |el |la |los |las )?(\w+)$")


def similares(pal, mem=None, n=6):
    """parche-109: 'dime palabras similares a coche': sinonimos, conceptos parecidos (hermanos por tipo, ordenados por parecido) y los nexos que la reflexion descubrio en memoria. None si no hay concepto."""
    cs = conceptos(pal)
    if not cs:
        return None
    d = _load()
    c, k = cs[0], nrm(pal)
    trozos = []
    sin = [w for w in nombres(c) if nrm(w) != k and not w[:1].isupper()][:5]
    if sin:
        trozos.append("Sinónimos: " + _lista(sin) + ".")
    mem_ = []
    for f in getattr(mem, "nexos", []):
        if str(f["p"]).upper() in ("SE_PARECE_A", "RELACIONADO_CON", "CONTRARIO_DE") and not f.get("neg"):
            for a, b in ((f["s"], f["o"]), (f["o"], f["s"])):
                if nrm(a) == k:
                    v = _vis(mem, b, clase=True)
                    if v not in mem_:
                        mem_.append(v)
    ps = d["hyp"].get(c, [])
    pool = []
    for p_ in ps[:1]:
        pool += [h for h in d["hypo"].get(p_, []) if h != c and etiqueta(h) and not es_genero(h)]
        for p2 in d["hyp"].get(p_, [])[:1]:
            pool += [h for h in d["hypo"].get(p2, []) if h != c and h not in pool and etiqueta(h) and not es_genero(h)]
    rank = sorted(((coseno(c, h), h) for h in pool), key=lambda x: (-x[0], -d["freq"][x[1]]))
    par = []
    arr_ = set(ascendentes(c))
    for s_, h in rank:
        e = etiqueta(h)
        if e and h not in arr_ and e not in par and nrm(e) != k and s_ > 0.2 and " " not in e and not e[:1].isupper() and "es" in lengua_de(e):
            par.append(e)
        if len(par) >= n:
            break
    arriba = etiqueta(ps[0]) if ps else None
    if mem_:
        trozos.append("Según lo que he descubierto al reflexionar: " + _lista(mem_[:n]) + ".")
    if par:
        trozos.append("Parecidos en el diccionario: " + _lista(par) + (f" (todos son tipos de «{arriba}»)." if arriba else "."))
    return (f"Sobre «{_vo(pal)}»: " + " ".join(trozos)) if trozos else None


def antes(raw, mem=None):
    """Preguntas de concepto que la memoria no puede contestar mejor: 'que es un X' cuando la memoria solo conoce ejemplares de X, y 'en que se parecen A y B'."""
    if not disponible():
        return None
    _marcar(raw)
    t = re.sub(r"\s+", " ", re.sub(r"[¡!¿?.,;:\"«»]", " ", nrm(raw))).strip()
    if re.match(r"(?:como )?se (?:dice|llama|traduce) .+ en \w+$", t) or re.match(r"traduce .+ al \w+$", t):
        return responder(raw, mem)
    m = re.match(r"que (?:es|son) (?:un |una |el |la |los |las )(\w+)$", t)
    if m and not _propio(raw):
        pal = m.group(1)
        facts = getattr(mem, "facts", [])
        base_ = _st(pal)
        if any(_st(f["s"]) == base_ for f in facts):
            return None                                                             # la memoria define esta clase: manda ella
        r = describir(pal, mem)
        if not r:
            return None
        ej = []
        for f in facts:
            if str(f["p"]).upper() == "ES" and not f.get("neg") and _st(f["o"]) == base_:
                v = _vis(mem, f["s"])
                if v not in ej:
                    ej.append(v)
        return "Según mi diccionario de conceptos: " + r + (f" Según lo que me has contado, conozco: {_lista(ej[:6])}." if ej else "")
    ms = _SIM.match(t) or _SIM2.match(t)
    if ms and not _propio(raw):
        r = similares(ms.group(1), mem)
        if r:
            return r
    if re.match(r"en que se parecen .+ y .+$", t) or re.match(r"que (?:tienen|tiene) en comun .+ y .+$", t):
        return responder(raw, mem)
    if re.search(r"\b(?:no encaja|no pertenece|sobra|intruso|se parece mas|es mas parecid[oa]|relacion (?:hay )?entre|tienen? que ver|como se relacion\w+|es a .+ como .+ es a)\b", t) \
            or re.match(r"(?:y )?(?:dime|dame|nombra|cita|menciona|enumera|define|defineme|definicion de|dime la definicion de|cual es la definicion de|que entiendes por|como se llama un (?:grupo|conjunto)|para que (?:sirve|sirven|se usa|se usan|se utiliza)|que hace un|que hacen los|a que se dedica|de que (?:es|son) (?:parte|miembro)|a que pertenece)\b", t) \
            or re.match(r"(?:y )?(?:es|son) \w+ \w+ \w+ o \w+", t):
        if _conoce(mem, t):
            return None                                                              # la persona ha hablado de eso: manda la memoria
        return responder(raw, mem)
    return None


_VACIAS = {"que", "para", "sirve", "sirven", "hace", "hacen", "un", "una", "el", "la", "los", "las", "de", "del", "es", "son", "y", "o", "entre", "relacion", "dime", "dame", "nombra", "define", "cual", "como", "se", "usa", "tipo", "tipos",
           "parte", "grupo", "conjunto", "llama", "a", "se", "dedica", "cita", "menciona", "enumera", "tres", "cinco", "dos", "cuatro", "algunos", "ejemplos", "tiene", "ver", "con", "encaja", "sobra", "parece", "mas", "pertenece", "miembro"}


def _conoce(mem, t):
    """True si la memoria tiene hechos sobre alguna palabra de la pregunta que NO es una clase de fabrica (Rex, mi hermana...): entonces responde la memoria."""
    ws = [w for w in t.split() if w not in _VACIAS and len(w) > 2]
    for f in getattr(mem, "facts", []):
        sj = nrm(f["s"])
        if any(sj == w or _st(sj) == _st(w) for w in ws) and (not _es_clase(mem, f["s"]) or (f.get("source") != "semilla" and not f.get("cart"))):
            return True
    return False


def antes_orden(raw, mem=None):
    """parche-105: ordenes y frases con signos raros que son preguntas de concepto ("Dime cinco frutas", "gato es a felino como perro es a ?"). None si no aplica."""
    if not disponible():
        return None
    t = re.sub(r"\s+", " ", re.sub(r"[¡!¿?.;\"«»]", " ", nrm(raw))).strip()
    if re.match(r"(?:y )?(?:dime|dame|nombra|cita|menciona|enumera|define|defineme|ponme|lista)\b", t) or re.search(r"\bes a .+ como .+ es a\b", t) \
            or re.search(r"\b(?:no encaja|no pertenece|sobra|intruso|se parece mas)\b", t):
        return antes(raw, mem)
    return None


def complemento(raw, mem=None):
    """'¿Que es un perro?': la memoria contesta lo que sabe (Un perro es un mamifero) y el diccionario anade la ficha del concepto. None si no aplica."""
    if not disponible():
        return None
    _marcar(raw)
    t = re.sub(r"\s+", " ", re.sub(r"[¡!¿?.,;:\"«»]", " ", nrm(raw))).strip()
    m = re.match(r"(?:que|cual es la definicion de|como es) (?:es |son )?(?:un |una |el |la |los |las )(\w+)$", t)
    if not m or _propio(raw):
        return None
    pal = m.group(1)
    if "es" not in lengua_de(pal) and nrm(pal) not in SUPLEMENTO:
        return None                                                              # solo palabras del espanol
    for f in getattr(mem, "facts", []):
        if _st(f["s"]) == _st(pal) and (not _es_clase(mem, f["s"]) or (f.get("source") != "semilla" and not f.get("cart"))):
            return None                                                          # lo que la persona ha ensenado (o una entidad) manda; el complemento es para el conocimiento de fabrica
    r = describir(pal, mem)
    return ("Según mi diccionario de conceptos: " + r) if r else None
