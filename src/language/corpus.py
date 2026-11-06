"""Generador de oraciones en espanol con su significado conocido (parche-16).

Cada oracion combina: un marco de frase (activa, inversa, pasiva, "es un"), una
polaridad (afirmativa/negada), adornos, incisos, adverbios, entidades de varios
tipos (nombres, nombres inventados, sustantivos con articulo y adjetivos, plurales).
Hay marcos, vocabulario y entidades RESERVADOS solo para medir generalizacion.
"""
import random
from .lexicon import PREPS, BASE_PHRASES

NAMES_TRAIN = ("ana luis carlos elena marta juan pedro sara pablo lucia diego rosa andres irene hugo nuria mateo alba sergio laura raul clara oscar julia ivan marina "
               "adrian beatriz cristina daniel david eva fernando gabriel guillermo javier jesus joaquin jose lorena manuel maria mario monica "
               "nicolas olga patricia paula rafael rebeca ricardo roberto rocio salvador santiago sonia susana teresa victor vicente yolanda "
               "alberto alicia amparo angel antonio aurora blanca camila carla celia dolores emilio enrique esther eugenio fatima francisco "
               "gonzalo ignacio ines jaime lidia lola lourdes manolo margarita martin natalia noa pilar quique reyes ruben sandra sofia tania "
               "uxia valeria vera violeta xavier yago zoe").split()
NAMES_TEST = "bruno carmen felix gloria hector isabel jorge leonor miguel noelia ramon silvia tomas veronica abel agustin celina elias fabian gema hilario jimena kevin leticia mauro nerea olivia ursula".split()
NOUNS_TRAIN = [("el", w) for w in "agua hielo fuego metal perro libro rio gato arbol coche camino puente cielo mar sol bosque campo pan vino lago monte barco reloj martillo jardin pueblo muro papel".split()] + \
              [("la", w) for w in "piedra lluvia luna casa nube flor mesa silla puerta ventana montana playa isla carta calle torre cuerda moneda botella lampara escuela".split()]
NOUNS_TEST = [("el", w) for w in "viento tren cristal hongo teatro volcan".split()] + [("la", w) for w in "arena ciudad cueva fabrica espada ola".split()]
CATS_TRAIN = "animal planta mineral objeto persona cosa metal fenomeno".split()
CATS_TEST = "vehiculo herramienta alimento edificio".split()
ADJ_TRAIN = ("grande fuerte comun util facil dificil veloz rojo azul verde blanco negro viejo nuevo joven alto bajo largo corto "
             "pesado ligero duro blando frio caliente dulce amargo limpio sucio rico pobre feliz triste bueno malo hermoso feo "
             "antiguo moderno publico privado").split()
ADJ_TEST = "interesante brillante capaz extrano valiente profundo sencillo misterioso oscuro".split()
HEADS_TRAIN = "padre madre hijo hermano jefe amigo vecino dueno autor creador maestro alumno lider socio rival mayor menor anterior posterior superior inferior parecido cercano lejano igual distinto mejor peor primo sobrino".split()
HEADS_TEST = "abuelo nieto tio suegro heredero sucesor aliado enemigo responsable delegado guardian tutor mentor discipulo".split()
VERBS_TRAIN = {"admira": "admirado", "visita": "visitado", "conoce": "conocido", "ayuda": "ayudado", "sigue": "seguido",
               "guia": "guiado", "protege": "protegido", "vigila": "vigilado", "construye": "construido",
               "ensena": "ensenado", "vende": "vendido", "compra": "comprado", "escribe": "escrito"}
VERBS_TEST = {"ama": "amado", "odia": "odiado", "respeta": "respetado", "teme": "temido", "busca": "buscado",
              "encuentra": "encontrado", "detecta": "detectado", "mueve": "movido", "sostiene": "sostenido",
              "contiene": "contenido"}
BASE_PART = {"CAUSA": "causado", "PRODUCE": "producido", "PROVOCA": "provocado", "ORIGINA": "originado",
             "POSEE": "poseido", "EXHIBE": "exhibido", "ADQUIERE": "adquirido", "HEREDA": "heredado",
             "IMPLICA": "implicado", "CONTRADICE": "contradicho"}
ES_ALIASES = [("es un", "E"), ("es una", "E"), ("son", "E"), ("era un", "E"), ("era una", "E"), ("eran", "E")]

# ---- marcos de entrenamiento -------------------------------------------------
A_ACTIVE = ["{S} {neg} es {p} {O}", "{S} {neg} resulta ser {p} {O}", "{S} {neg} es siempre {p} {O}",
            "se sabe que {S} {neg} es {p} {O}", "{S} , como todos saben , {neg} es {p} {O}",
            "dicen que {S} {neg} es {p} {O}", "{S} {neg} es tambien {p} {O}", "{S} , que vive cerca , {neg} es {p} {O}",
            "ahora {S} {neg} es {p} {O}", "{S} {neg} es el {p} {O}", "{S} {neg} es claramente {p} {O}",
            "creo que {S} {neg} es {p} {O} desde hace tiempo",
            "{S} {neg} era {p} {O}", "{S} {neg} fue {p} {O}", "{S} {neg} era el {p} {O}", "{S} {neg} era siempre {p} {O}",
            "{S} {neg} habia sido {p} {O}", "{S} , que ya no vivia alli , {neg} era {p} {O}"]
A_INV = ["el {head} de {O} {neg} es {S}", "{O} {neg} tiene como {head} a {S}", "dicen que el {head} de {O} {neg} es {S}",
         "{O} , segun parece , {neg} tiene como {head} a {S}", "el {head} de {O} {neg} era {S}",
         "{O} {neg} tenia como {head} a {S}"]
V_ACTIVE = ["{S} {neg} {p} {O}", "{S} siempre {neg} {p} {O}", "se sabe que {S} {neg} {p} {O}",
            "{S} , como todos saben , {neg} {p} {O}", "dicen que {S} {neg} {p} {O}",
            "{S} , que vive cerca , {neg} {p} {O}", "ahora {S} {neg} {p} {O}", "{S} {neg} {p} a {O}",
            "{S} tambien {neg} {p} {O}"]
V_PASSIVE = ["{O} {neg} es {part} por {S}", "{O} {neg} fue {part} por {S}", "dicen que {O} {neg} es {part} por {S}"]
E_ACTIVE = ["{S} {neg} {p} {O}", "se sabe que {S} {neg} {p} {O}", "{S} , como todos saben , {neg} {p} {O}",
            "dicen que {S} {neg} {p} {O}", "{S} , segun parece , {neg} {p} {O}", "ahora {S} {neg} {p} {O}"]
# ---- marcos RESERVADOS (solo evaluacion) -------------------------------------
HELD_A = ["{S} {neg} termina siendo {p} {O}", "{S} {neg} acaba por ser {p} {O}", "para mi , {S} {neg} es {p} {O}"]
HELD_A_INV = ["{O} cuenta con {S} como {head}", "{S} es el {head} que tiene {O}"]
HELD_V = ["{S} , de hecho , {neg} {p} {O}", "{S} {neg} llega a {p} {O}", "es cierto que {S} {neg} {p} {O}"]
HELD_PASSIVE = ["{O} {neg} resulta {part} por {S}", "{O} {neg} queda {part} por {S}"]
HELD_E = ["segun el libro , {S} {neg} {p} {O}", "{S} , {neg} {p} {O}", "es evidente que {S} {neg} {p} {O}"]
PREFIX = ["", "", "", "", "oye ,", "por cierto ,", "creo que", "ayer supe que", "mi amigo dice que", "fijate ,",
          "pues bien ,", "te cuento que", "ya sabes que", "resulta que", "mira ,", "dime una cosa :", "segun mi madre ,", "me han contado que",
          "no me lo creo pero", "entonces ,", "a ver ,", "pues mira ,", "te aseguro que", "estoy seguro de que", "ayer lei que", "es curioso ,",
          "hoy me han dicho que", "total ,", "bueno ,", "ya ves ,"]
SUFFIX = ["", "", ".", ".", "!", ", segun parece .", ", ya lo ves .", ", como siempre .", ", dicen ."]
FILL_TRAIN = "siempre tambien ya claramente realmente casi todavia ademas quiza aqui entonces antes hoy luego".split()
ADJ_SUFFIX = ["oso", "ico", "al", "ente", "able", "ivo"]
NEG_WORDS = ["no", "no", "no", "nunca", "jamas"]
SYL = "ba be bi bo bu ca ce co cu da de di do fa fe fo ga gi go la le li lo lu ma me mi mo na ne ni no pa pe pi po ra re ri ro sa se si so ta te ti to va ve vi vo za zo".split()


CLAUSES_TRAIN, CLAUSES_TEST = [], []
BOOK_NAMES = set()          # nombres propios del libro: salen en miles de clausulas negativas (parche-25)


_COP = {"es", "era", "son", "eran", "fue", "fueron"}
_ART = {"el", "la", "los", "las", "un", "una", "unos", "unas"}


def looks_relational(clause: str) -> bool:
    """"Mesia era el amigo de Quintanar": una afirmacion de relacion REAL. No puede ser un negativo (parche-24)."""
    t = [w for w in clause.split() if w not in ",.;:!?\u00bf\u00a1"]
    if "?" in clause or len(t) < 4 or len(t) > 9:
        return False
    for i in range(1, min(len(t) - 2, 5)):
        if t[i] in _COP and "de" in t[i + 1:]:
            return t[i + 1] in _ART or (i + 2 < len(t) and t[i + 2] == "de")
    return False


def load_book_vocab(path="data/libro_vocab.json"):
    """Si existe el vocabulario REAL de un libro (scripts.read_book), se mezcla con el sintetico.
    Un 20 % de las palabras (por hash) queda reservado para la prueba."""
    from .book_vocab import load_vocab, split_vocab
    v = load_vocab(path)
    if not v:
        return False
    tr, te = split_vocab(v)
    NAMES_TRAIN.extend(w for w in tr["names"] if w not in NAMES_TRAIN and w not in NAMES_TEST)
    NAMES_TEST.extend(w for w in te["names"] if w not in NAMES_TEST and w not in NAMES_TRAIN)
    NOUNS_TRAIN.extend(tuple(x) for x in tr["nouns"])
    NOUNS_TEST.extend(tuple(x) for x in te["nouns"])
    ADJ_TRAIN.extend(w for w in tr["adjs"] if w not in ADJ_TRAIN)
    ADJ_TEST.extend(w for w in te["adjs"] if w not in ADJ_TEST and w not in ADJ_TRAIN)
    FILL_TRAIN.extend(tr["advs"])
    BOOK_NAMES.update(tr["names"]); BOOK_NAMES.update(te["names"])
    CLAUSES_TRAIN.extend(c for c in tr["clauses"] if not looks_relational(c))
    CLAUSES_TEST.extend(c for c in te["clauses"] if not looks_relational(c))
    return True


def pseudo_name(rng):
    return "".join(rng.choice(SYL) for _ in range(rng.choice([2, 3, 3, 4])))


def pseudo_adj(rng):
    return pseudo_name(rng) + rng.choice(ADJ_SUFFIX)


def pseudo_filler(rng):
    return pseudo_name(rng) + rng.choice(["mente", "ando", "ado", "mente"])


def pseudo_periphrasis(rng):
    """Giros tipo 'termina siendo / acaba por ser' con un verbo inventado (vocabulario abierto)."""
    verb = pseudo_name(rng) + rng.choice(["a", "e", "ea", "ece"])
    return [verb] + rng.choice([["siendo"], ["por", "ser"], ["a", "ser"], ["de", "ser"]])


def pick_adj(rng, adjs):
    return rng.choice(adjs) if rng.random() < 0.5 else pseudo_adj(rng)


def plural(w):
    return w + ("es" if w[-1] not in "aeiou" else "s")


def singular(w):
    if w.endswith("es") and len(w) > 3 and w[-3] not in "aeiou":
        return w[:-2]
    return w[:-1] if w.endswith("s") else w


def base_pool():
    items = []
    for name, (text, kind) in BASE_PHRASES.items():
        words = text.split()
        items.append((name, text, kind, " ".join(words[:-1]) if kind == "A" else text,
                      words[-1] if kind == "A" else "", BASE_PART.get(name)))
    return items


def es_pool():
    return [("ES", text, "E", text, "", None) for text, _ in ES_ALIASES]


class PredicatePool:
    def __init__(self, heads, verbs, preps=None):
        preps = preps or sorted(PREPS)
        self.items = []
        for h in heads:
            for p in preps:
                self.items.append((f"{h}_{p}".upper(), f"{h} {p}", "A", h, p, None))
        for v, part in verbs.items():
            self.items.append((v.upper(), v, "V", v, "", part))


def entity(rng, mode, role, pl=False):
    """Devuelve (articulo, palabra_en_texto, adjetivos, nombre_canonico)."""
    names = NAMES_TRAIN if mode == "train" else NAMES_TEST
    nouns = NOUNS_TRAIN if mode == "train" else NOUNS_TEST
    adjs = ADJ_TRAIN if mode == "train" else ADJ_TEST
    r = rng.random()
    if not pl and r < 0.40:
        return None, rng.choice(names), [], None
    if not pl and r < 0.62:
        n = pseudo_name(rng)
        return None, n, [], None
    art, noun = rng.choice(nouns)
    if rng.random() < 0.3:
        noun = pseudo_name(rng)
    mods = [pick_adj(rng, adjs)] if rng.random() < 0.35 else []
    if pl:
        return ("los" if art == "el" else "las"), plural(noun), [(plural(m)) for m in mods], noun
    return (art if rng.random() < 0.7 else ("un" if art == "el" else "una")), noun, mods, noun


def category(rng, mode, pl):
    cats = CATS_TRAIN if mode == "train" else CATS_TEST
    adjs = ADJ_TRAIN if mode == "train" else ADJ_TEST
    c = rng.choice(cats) if rng.random() < 0.7 else pseudo_name(rng)
    mods = [pick_adj(rng, adjs)] if rng.random() < 0.35 else []
    return (None, plural(c), [plural(m) for m in mods], c) if pl else (None, c, mods, c)


def build(rng, item, frames, mode, neg_prob=0.2):
    name, text, kind, head, prep, part = item
    fa, fi, fv, fp, fe = frames
    plural_e = text in ("son", "eran")
    if kind == "A":
        template = rng.choice(fi if (prep == "de" and fi and rng.random() < 0.4) else fa)
    elif kind == "E":
        template = rng.choice(fe)
    elif part and fp and rng.random() < 0.3:
        template = rng.choice(fp)
    else:
        template = rng.choice(fv)
    if kind == "E":
        e1 = entity(rng, mode, "S", pl=plural_e)
        e2 = category(rng, mode, plural_e)
    else:
        e1, e2 = entity(rng, mode, "S"), entity(rng, mode, "O")
        while e2[1] == e1[1]:
            e2 = entity(rng, mode, "O")
    neg = rng.random() < neg_prob
    tokens, tags = [], []

    def add(tok, tag=0):
        tokens.append(tok)
        tags.append(tag)

    def fill(p=0.45):
        if rng.random() < p:
            if rng.random() < 0.3:
                for w in pseudo_periphrasis(rng):
                    add(w)
                return
            for _ in range(rng.choice([1, 1, 2])):
                add(rng.choice(FILL_TRAIN) if rng.random() < 0.6 else pseudo_filler(rng))

    clauses = CLAUSES_TRAIN if mode == "train" else CLAUSES_TEST
    pre = rng.choice(PREFIX)
    post = rng.choice(SUFFIX)
    if clauses and rng.random() < 0.25:                       # prosa real alrededor de la afirmacion
        if rng.random() < 0.5:
            pre = rng.choice(clauses) + " ,"
        else:
            post = ", " + rng.choice(clauses)
    for piece in (pre + " " + template).split():
        if piece in ("{S}", "{O}"):
            art, word, mods, canon = e1 if piece == "{S}" else e2
            if art:
                add(art)
            add(word, 1 if piece == "{S}" else 2)
            for m in mods:
                add(m)
            if piece == "{S}" and mode == "train":
                fill(0.15)
        elif piece == "{p}":
            if mode == "train":
                fill()
            for w in text.split():
                add(w)
        elif piece == "{head}":
            if mode == "train":
                fill(0.2)
            for w in head.split():
                add(w)
        elif piece == "{part}":
            if mode == "train":
                fill(0.3)
            add(part)
        elif piece == "{neg}":
            if neg:
                add(rng.choice(NEG_WORDS))
        else:
            add(piece)
    for w in post.split():
        add(w)
    s_name = (e1[3] or e1[1]).upper()
    o_name = (e2[3] or e2[1]).upper()
    return {"tokens": tokens, "tags": tags, "pred": name, "text": text, "neg": neg, "triple": (s_name, name, o_name)}


def make_negatives(n, seed, mode="train"):
    """Frases que NO afirman una relacion: prosa suelta, fragmentos, preguntas, sin relacion, sin sujeto."""
    rng = random.Random(seed)
    clauses = CLAUSES_TRAIN if mode == "train" else CLAUSES_TEST
    names = NAMES_TRAIN if mode == "train" else NAMES_TEST
    out = []
    for _ in range(n):
        r = rng.random()
        e1, e2 = entity(rng, mode, "S"), entity(rng, mode, "O")

        def ent(e):
            return ([e[0]] if e[0] else []) + [e[1]] + list(e[2])
        head = rng.choice(HEADS_TRAIN if mode == "train" else HEADS_TEST)
        if r < 0.50 and clauses:
            toks = rng.choice(clauses).split()
            if BOOK_NAMES and rng.random() < 0.85:      # que un nombre del libro no sea una pista de "basura"
                swap = {}
                toks = [swap.setdefault(w, rng.choice(names) if rng.random() < 0.6 else pseudo_name(rng))
                        if w in BOOK_NAMES else w for w in toks]
        elif r < 0.60:
            toks = ["el", head, rng.choice(["de", "a", "con"])] + ent(e2)                   # fragmento nominal
        elif r < 0.70:
            toks = ent(e1) + [rng.choice(["y", "habla con", "mira a", "pasea con", "vive cerca de"])] + ent(e2)
        elif r < 0.80:
            toks = ["quien", "es", "el", head, "de"] + ent(e2) + ["?"]                      # pregunta
        elif r < 0.88:
            toks = ["es", "el", head, "de"] + ent(e2)                                     # sin sujeto
        elif r < 0.95:
            toks = ["es"] + ent(e1) + ["el", head, "de"] + ent(e2) + ["?"]
        else:
            toks = [pseudo_name(rng) for _ in range(rng.choice([3, 4, 5]))]
        toks = [t for w in toks for t in w.split()]
        out.append({"tokens": toks, "tags": [0] * len(toks), "pred": None, "text": None, "neg": False,
                    "triple": None, "reject": True})
    return out


def make(n, pool_items, seed, mode="train", held_frames=False, neg_prob=0.2):
    rng = random.Random(seed)
    frames = ((HELD_A, HELD_A_INV, HELD_V, HELD_PASSIVE, HELD_E) if held_frames
              else (A_ACTIVE, A_INV, V_ACTIVE, V_PASSIVE, E_ACTIVE))
    return [build(rng, rng.choice(pool_items), frames, mode, neg_prob) for _ in range(n)]


load_book_vocab()
