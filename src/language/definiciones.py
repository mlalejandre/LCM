"""parche-105: GRAFO DE DEFINICIONES. Sobre el diccionario de conceptos (conceptos.py) se carga data/definiciones.json.gz: las glosas de WordNet enlazadas a conceptos (la definicion de "bicicleta"
menciona "rueda", "pedal"...), mas cualidades, contrarios, derivados (profesor -> ensenar), usos y acciones. Con eso el LCM contesta como un diccionario enlazado:
 "para que sirve X", "que hace X", "que relacion hay entre X e Y", "cual no encaja: a, b, c", "que se parece mas a X: Y o Z", "A es a B como C es a ?", "nombra tres X", "de que es parte X",
 "como se llama un grupo de X", "es X un A o un B", "define X", "dime algo de X".
Siempre el ultimo recurso: la memoria manda (se llama desde conceptos.responder / antes)."""
import gzip
import heapq
import json
import os
import re

_FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "definiciones.json.gz")
_X = None

# Funciones de objetos cotidianos (conocimiento propio, ver data/CONCEPTOS_LICENCIAS.txt): palabra -> para que sirve
FUNCION = {
    "martillo": "golpear, clavar", "lapiz": "escribir, dibujar", "boligrafo": "escribir", "cuchillo": "cortar", "tijeras": "cortar", "tijera": "cortar", "tenedor": "pinchar y comer alimentos",
    "cuchara": "comer alimentos líquidos o blandos", "plato": "servir y comer alimentos", "vaso": "beber", "taza": "beber bebidas calientes", "botella": "guardar líquidos", "llave": "abrir y cerrar cerraduras",
    "reloj": "medir el tiempo", "paraguas": "protegerse de la lluvia", "gafas": "corregir la vista", "peine": "peinar el pelo", "cepillo": "limpiar o peinar", "jabon": "lavar", "toalla": "secar",
    "espejo": "verse reflejado", "lampara": "dar luz", "bombilla": "dar luz", "sofa": "sentarse", "silla": "sentarse", "cama": "dormir", "mesa": "apoyar cosas y comer", "armario": "guardar ropa",
    "nevera": "conservar fríos los alimentos", "horno": "cocinar, hornear", "cocina": "cocinar", "lavadora": "lavar la ropa", "television": "ver programas", "radio": "escuchar", "telefono": "hablar a distancia",
    "ordenador": "calcular y procesar información", "camara": "hacer fotografías", "libro": "leer", "cuaderno": "escribir apuntes", "mochila": "llevar cosas", "maleta": "llevar equipaje", "bolsa": "llevar cosas",
    "coche": "viajar, transportar personas", "bicicleta": "desplazarse pedaleando", "avion": "volar, viajar", "barco": "navegar", "tren": "viajar por vías", "puerta": "entrar y salir", "ventana": "dejar pasar la luz y el aire",
    "escalera": "subir y bajar", "puente": "cruzar un río o un obstáculo", "moneda": "pagar", "billete": "pagar", "carta": "comunicarse por escrito", "sello": "franquear el correo", "periodico": "informarse de las noticias",
    "guitarra": "tocar música", "piano": "tocar música", "pelota": "jugar", "zapato": "proteger los pies", "bota": "proteger los pies", "calcetin": "abrigar los pies", "abrigo": "protegerse del frío", "guante": "proteger las manos",
    "sombrero": "cubrir la cabeza", "cinturon": "sujetar el pantalón", "camisa": "vestir", "pantalon": "vestir", "mapa": "orientarse", "brujula": "orientarse", "telescopio": "observar los astros", "microscopio": "ver cosas muy pequeñas",
    "termometro": "medir la temperatura", "balanza": "pesar", "regla": "medir y trazar líneas", "goma": "borrar", "sacapuntas": "afilar lápices", "pegamento": "pegar", "aguja": "coser", "hacha": "cortar madera",
    "sierra": "serrar, cortar madera", "pala": "cavar", "rastrillo": "recoger hojas", "escoba": "barrer", "fregona": "fregar el suelo", "cubo": "llevar agua", "olla": "cocer alimentos", "sarten": "freír alimentos",
    "hospital": "curar a los enfermos", "escuela": "enseñar y aprender", "biblioteca": "leer y prestar libros", "museo": "exponer obras y objetos", "iglesia": "rezar", "banco": "guardar dinero", "tienda": "comprar y vender",
    "restaurante": "comer fuera de casa", "hotel": "alojarse", "aeropuerto": "coger aviones", "estacion": "coger trenes", "estadio": "ver deportes", "cine": "ver películas", "teatro": "ver obras", "farmacia": "comprar medicinas",
}
PROFESION = {  # a que se dedica (conocimiento propio de fabrica)
    "bombero": "apagar incendios y rescatar personas", "medico": "atender y curar a los enfermos", "doctor": "atender y curar a los enfermos", "enfermero": "cuidar a los enfermos", "profesor": "enseñar a los alumnos",
    "maestro": "enseñar a los niños", "panadero": "hacer y vender pan", "carnicero": "cortar y vender carne", "pescadero": "vender pescado", "cocinero": "preparar comidas", "camarero": "servir comidas y bebidas",
    "policia": "mantener el orden y proteger a las personas", "juez": "juzgar y dictar sentencias", "abogado": "defender a las personas ante la ley", "arquitecto": "diseñar edificios", "ingeniero": "diseñar y construir máquinas o estructuras",
    "albanil": "construir con ladrillos y cemento", "carpintero": "trabajar la madera", "electricista": "instalar y reparar la electricidad", "fontanero": "instalar y reparar tuberías", "mecanico": "reparar vehículos",
    "piloto": "pilotar aviones", "conductor": "conducir vehículos", "marinero": "trabajar en un barco", "granjero": "cuidar animales y cultivos", "agricultor": "cultivar la tierra", "pastor": "cuidar el ganado",
    "pescador": "pescar", "cartero": "repartir cartas", "periodista": "informar de las noticias", "escritor": "escribir libros", "poeta": "escribir poemas", "pintor": "pintar cuadros", "cantante": "cantar",
    "musico": "tocar música", "actor": "interpretar papeles en teatro o cine", "bailarin": "bailar", "futbolista": "jugar al fútbol", "deportista": "practicar deporte", "cientifico": "investigar y descubrir cosas",
    "astronomo": "estudiar los astros", "astronauta": "viajar al espacio", "dentista": "cuidar los dientes", "veterinario": "curar animales", "farmaceutico": "preparar y vender medicinas", "peluquero": "cortar y arreglar el pelo",
    "sastre": "hacer y arreglar ropa", "zapatero": "hacer y arreglar zapatos", "jardinero": "cuidar jardines", "soldado": "servir en el ejército", "bibliotecario": "cuidar y prestar libros", "contable": "llevar las cuentas",
    "vendedor": "vender productos", "cajero": "cobrar en una tienda o un banco", "taxista": "llevar pasajeros en taxi", "traductor": "pasar textos de una lengua a otra", "programador": "escribir programas de ordenador",
}
VIVE = {}
GENERAL = {"instrumental", "equipamiento", "aparato", "artículo", "construcción", "organismo", "ser vivo", "entidad", "objeto", "cosa", "entidad física", "abstracción", "todo", "objeto físico", "objeto natural", "unidad", "conjunto", "causal agent", "artefacto", "físico", "sustancia", "materia"}
REL_ES = {"hyp": "es un tipo de", "hypo": "incluye como tipo a", "parte": "tiene como parte a", "parte_inv": "es parte de", "miembro": "tiene como miembro a", "miembro_inv": "es miembro de", "sustancia": "está hecho de",
          "sustancia_inv": "es material de", "gl": "se define mencionando a", "gl_inv": "aparece en la definición de", "deriv": "está emparentada con", "uso": "sirve para", "ant": "es lo contrario de",
          "tema": "pertenece al ámbito de", "pert": "se refiere a", "sim": "se parece en significado a", "attr": "es una cualidad de"}


def _C():
    from src.language import conceptos as C
    return C


def _load():
    global _X
    if _X is not None:
        return _X
    _X = {"ok": False}
    try:
        with gzip.open(_FD, "rt", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        return _X
    X = {k: {int(a): b for a, b in v.items()} for k, v in raw.items() if isinstance(v, dict)}
    inv = {}
    for nombre in ("gl", "deriv", "tema", "sim", "attr"):
        r = {}
        for c, ts in X[nombre].items():
            for t in ts:
                r.setdefault(t, []).append(c)
        inv[nombre] = r
    X["inv"] = inv
    X["ok"] = True
    _X = X
    return _X


def disponible():
    return _load()["ok"] and _C().disponible()


def _inv(clave):
    """concepto -> conceptos que lo tienen como parte/miembro/sustancia (el todo)."""
    d = _C()._load()
    cache = _load().setdefault("_inv_" + clave, None)
    if cache is None:
        cache = {}
        for c, ts in d[clave].items():
            for t in ts:
                cache.setdefault(t, []).append(c)
        _load()["_inv_" + clave] = cache
    return cache


def lab(c, ingles=False):
    C = _C()
    return C.etiqueta(c) or (C.etiqueta(c, "en") if ingles else None)


def _alto(c):
    C = _C()
    d = C._load()
    e = C.etiqueta(c) or ""
    return e.lower() in GENERAL or e.lower() in C.ALTO or d["lexnames"].get(d["lex"][c], "") == "noun.Tops"


# ---- fichas ---------------------------------------------------------------------------------------------------------------
def verbos_relacionados(c, n=3):
    """Verbos emparentados por derivacion (profesor -> ensenar, martillo -> clavar): lo que la cosa o la persona HACE."""
    d, X, C = _C()._load(), _load(), _C()
    out = []
    for t in X["deriv"].get(c, []):
        if d["pos"][t] == "v":
            e = C.etiqueta(t)
            if e and " " not in e and e not in out:
                out.append(e)
    return out[:n]


def funcion(c, palabra=None):
    """Para que sirve: tabla de fabrica por palabra, o el 'used for/to' de la glosa (solo si el verbo es fiable)."""
    C = _C()
    X = _load()
    if palabra is not None:
        f = FUNCION.get(C.nrm(palabra))
        if f:
            return f
    for nom in C.nombres(c):
        f = FUNCION.get(C.nrm(nom))
        if f:
            return f
    u = X["uso"].get(c)
    if u and u[0] is not None:
        v = lab(u[0])
        o = lab(u[1]) if u[1] is not None else None
        if v and " " not in v:
            return v + (" " + o if o and " " not in o else "")
    return None


def accion(c, palabra=None):
    """Lo que hace quien es un X (persona): 'enseñar', 'cocer pan'."""
    C = _C()
    X = _load()
    for nom in ([palabra] if palabra else []) + C.nombres(c):
        f = PROFESION.get(C.nrm(nom))
        if f:
            return f
    h = X["hace"].get(c)
    if h and h[0] is not None:
        v = lab(h[0])
        o = lab(h[1]) if h[1] is not None else None
        if v and " " not in v:
            return v + (" " + o if o and " " not in o else "")
    vs = verbos_relacionados(c, 2)
    return " o ".join(vs) if vs else None


def relacionados(c, n=6):
    """Conceptos que su definicion menciona (con nombre en espanol), sin repetir su cadena de tipos."""
    C = _C()
    X = _load()
    d = C._load()
    arriba = set(C.ascendentes(c))
    out = []
    for t in X["gl"].get(c, []):
        e = C.etiqueta(t)
        if e and t not in arriba and e not in out and e.lower() not in GENERAL and d["pos"][t] in ("n", "a") and not e[:1].isupper() and " " not in e:
            out.append(e)
    return out[:n]


def contrarios(c):
    C = _C()
    d = C._load()
    out = []
    for t in d["ant"].get(c, []):
        e = C.etiqueta(t)
        if e and e not in out:
            out.append(e)
    return out


def ampliar(c, palabra=None):
    """Frases extra para la ficha de un concepto."""
    C = _C()
    X = _load()
    if not X["ok"]:
        return []
    out = []
    f = funcion(c, palabra)
    if f:
        out.append(f"Sirve para {f}.")
    d = C._load()
    if d["pos"][c] == "n" and C.dominio(c) == "persona":
        a = accion(c)
        if a:
            out.append(f"Su actividad: {a}.")
    elif d["pos"][c] == "n":
        vs = verbos_relacionados(c, 3)
        if vs and not f:
            out.append(f"Acción asociada: {C._lista(vs)}.")
    co = contrarios(c)
    if co:
        out.append(f"Lo contrario: {C._lista(co[:3])}.")
    rl = relacionados(c, 6)
    if rl:
        out.append(f"En su definición aparecen, entre otras: {C._lista(rl[:5])}.")
    return out


# ---- grafo ----------------------------------------------------------------------------------------------------------------
def _vecinos(c, meta=None):
    """(vecino, relacion, coste) desde c. Las relaciones *_inv/hypo/gl_inv son las del reves."""
    C = _C()
    d = C._load()
    X = _load()
    for t in d["hyp"].get(c, []):
        yield t, "hyp", 1.0
    hs = d["hypo"].get(c, [])
    if len(hs) <= 60:
        for t in hs:
            yield t, "hypo", 1.0
    elif meta is not None and meta in hs:
        yield meta, "hypo", 1.0
    for k in ("parte", "miembro", "sustancia"):
        for t in d[k].get(c, []):
            yield t, k, 1.0
        w = _inv(k).get(c, [])
        if len(w) <= 40:
            for t in w:
                yield t, k + "_inv", 1.0
        elif meta is not None and meta in w:
            yield meta, k + "_inv", 1.0
    for t in X["gl"].get(c, []):
        yield t, "gl", 1.5
    ig = X["inv"]["gl"].get(c, [])
    if len(ig) <= 80:
        for t in ig:
            yield t, "gl_inv", 1.5
    elif meta is not None and meta in ig:
        yield meta, "gl_inv", 1.5
    for t in X["deriv"].get(c, []):
        yield t, "deriv", 1.0
    for t in d["ant"].get(c, []):
        yield t, "ant", 1.0
    for t in X["tema"].get(c, []):
        yield t, "tema", 1.0
    for t in X["sim"].get(c, []) + X["attr"].get(c, []):
        yield t, "sim", 1.0
    for t in X["pert"].get(c, []):
        yield t, "pert", 1.0
    u = X["uso"].get(c)
    if u and u[0] is not None:
        yield u[0], "uso", 1.0


def camino(a, b, maxc=4.0, solo_es=True):
    """Camino mas corto entre dos conceptos: lista de (desde, relacion, hasta) o None. Pasa solo por conceptos con nombre en espanol y no por categorias demasiado generales."""
    C = _C()
    if a == b:
        return []
    cola = [(0.0, 0, a, None)]
    ant = {a: None}
    mejor = {a: 0.0}
    n = 0
    while cola:
        coste, _, x, _p = heapq.heappop(cola)
        if x == b:
            break
        if coste > mejor.get(x, 1e9) or coste >= maxc:
            continue
        n += 1
        if n > 4000:
            break
        for t, rel, w in _vecinos(x, b):
            if t != b and (_alto(t) or (solo_es and not C.etiqueta(t))):
                continue
            nc = coste + w
            if nc < mejor.get(t, 1e9) and nc <= maxc:
                mejor[t] = nc
                ant[t] = (x, rel)
                heapq.heappush(cola, (nc, id(t) % 997 + n, t, None))
    if b not in ant:
        return None
    out, x = [], b
    while ant[x] is not None:
        p, rel = ant[x]
        out.append((p, rel, x))
        x = p
    return out[::-1]


def _frase_arista(p, rel, q):
    return f"«{lab(p, True)}» {REL_ES[rel]} «{lab(q, True)}»"


def comun_es(a, b):
    """Antepasado comun mas cercano con nombre en espanol (y no demasiado general); None si no hay."""
    C = _C()
    aa, bb = C.ascendentes(a), C.ascendentes(b)
    cand = sorted((aa[x] + bb[x], x) for x in set(aa) & set(bb))
    for _k, x in cand:
        e = C.etiqueta(x)
        if e and e.lower() not in C.TAXON and e.lower() not in GENERAL and not _alto(x):
            return x
    return None


_PERMITIDAS = {("hyp", "hypo"), ("gl", "gl_inv"), ("gl_inv", "gl"), ("parte", "parte"), ("parte_inv", "parte_inv"), ("parte_inv", "parte"), ("parte", "hypo"), ("hyp", "parte"), ("hyp", "parte_inv"), ("hypo", "parte"),
               ("hyp", "hyp"), ("hypo", "hypo"), ("parte_inv", "hypo"), ("miembro_inv", "hypo"), ("hyp", "miembro_inv"), ("hyp", "miembro"), ("hyp", "uso"), ("uso", "hypo")}


def explicar_camino(ca, cb, na, nb):
    """Texto que explica como se relacionan dos conceptos, o None (mejor callar que inventar una cadena rara)."""
    C = _C()
    if ca == cb:
        return f"«{na}» y «{nb}» son el mismo concepto."
    asc_a, asc_b = C.ascendentes(ca), C.ascendentes(cb)
    if cb in asc_a:
        return f"«{na}» es un tipo de «{nb}»."
    if ca in asc_b:
        return f"«{nb}» es un tipo de «{na}»."
    cam = camino(ca, cb, 3.5, True)
    rels = tuple(r for _p, r, _q in cam) if cam else ()
    if cam and len(cam) == 1:
        a, rel, b = cam[0]
        txt = {"gl": f"en la definición de «{na}» aparece «{nb}».", "gl_inv": f"en la definición de «{nb}» aparece «{na}».", "parte": f"«{nb}» es parte de «{na}».", "parte_inv": f"«{na}» es parte de «{nb}».",
               "miembro": f"«{nb}» es miembro de «{na}».", "miembro_inv": f"«{na}» es miembro de «{nb}».", "sustancia": f"«{na}» está hecho de «{nb}».", "sustancia_inv": f"«{na}» es material de «{nb}».",
               "uso": f"«{na}» sirve para «{nb}».", "ant": f"«{na}» y «{nb}» son contrarios.", "deriv": f"«{na}» y «{nb}» comparten raíz (son palabras emparentadas).", "tema": f"«{na}» pertenece al ámbito de «{nb}»."}.get(rel)
        if txt:
            return txt
    if cam and rels in (("gl", "pert"), ("gl", "deriv"), ("gl", "sim")):
        return f"en la definición de «{na}» aparece «{lab(cam[0][2], True)}», que se refiere a «{nb}»."
    if cam and rels == ("gl", "gl_inv"):
        return f"las definiciones de «{na}» y «{nb}» mencionan las dos «{lab(cam[0][2], True)}»."
    if cam and len(cam) <= 3 and all(r in ("parte", "parte_inv", "uso", "sustancia", "sustancia_inv") for r in rels):
        return "; ".join(_frase_arista(p, r, q) for p, r, q in cam) + "."
    cam2 = camino(ca, cb, 2.5, False)
    if cam2 and tuple(r for _p, r, _q in cam2) in (("parte_inv", "hypo"),):
        m_ = cam2[0][2]
        return f"«{na}» es parte de «{lab(m_, True)}»{'' if C.etiqueta(m_) else ' (nombre en inglés)'}, y «{nb}» es un tipo de eso."
    cm = comun_es(ca, cb)
    if cm is not None and asc_a[cm] + asc_b[cm] <= 8:
        return f"«{na}» y «{nb}» son tipos de «{lab(cm)}»."
    if cam and len(cam) <= 3 and all(r in ("hyp", "hypo", "parte", "parte_inv", "uso", "sustancia", "sustancia_inv") for r in rels):
        return "; ".join(_frase_arista(p, r, q) for p, r, q in cam) + "."
    return None


def similitud_ranking(c, otros):
    C = _C()
    return sorted(((C.coseno(c, o), o) for o in otros), reverse=True)


def ejemplos(c, n=5):
    """Ejemplos de la categoria c: descendientes con nombre sencillo en espanol, los mas usados primero."""
    C = _C()
    d = C._load()
    vistos, cola, hojas = {c}, list(d["hypo"].get(c, [])), []
    while cola and len(vistos) < 3000:
        x = cola.pop(0)
        if x in vistos:
            continue
        vistos.add(x)
        cola.extend(d["hypo"].get(x, []))
        e = C.etiqueta(x)
        if e and " " not in e and not e[:1].isupper() and e.lower() not in C.TAXON and d["freq"][x] > 0 and not C.es_genero(x):
            hojas.append((d["freq"][x], e))
    hojas.sort(key=lambda t: (-t[0], t[1]))
    out = []
    for _f, e in hojas:
        if e not in out:
            out.append(e)
        if len(out) >= n:
            break
    return out


_NUM = {"un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10}


def describir_otro(palabra):
    """Ficha de un adjetivo, verbo o adverbio (lo que no es un sustantivo): sinonimos cercanos, contrarios, cualidad, raiz, lo que implica."""
    C = _C()
    X = _load()
    d = C._load()
    cs = [c for c in C.conceptos(palabra, solo_nombres=False) if d["pos"][c] in ("a", "v", "r") and C.etiqueta(c)]
    if not cs:
        return None
    c = cs[0]
    pos = d["pos"][c]
    nom = C._vo(palabra)
    cat = {"a": "un adjetivo (una cualidad)", "v": "un verbo", "r": "un adverbio"}[pos]
    out = f"«{nom}» es {cat}."
    otros = [w for w in C.nombres(c) if C.nrm(w) != C.nrm(palabra) and " " not in w][:4]
    if otros:
        out += f" Significa algo parecido a: {C._lista(otros)}."
    if pos == "v":
        for rel, txt in (("entrana", "Implica"), ("causa", "Hace que ocurra")):
            xs = [C.etiqueta(t) for t in X[rel].get(c, []) if C.etiqueta(t)]
            if xs:
                out += f" {txt}: {C._lista(xs[:3])}."
    co = contrarios(c)
    if co:
        out += f" Lo contrario: {C._lista(co[:3])}."
    at = [C.etiqueta(t) for t in X["attr"].get(c, []) if C.etiqueta(t)]
    if at:
        out += f" Es una cualidad relacionada con «{at[0]}»."
    pe = [C.etiqueta(t) for t in X["pert"].get(c, []) if C.etiqueta(t)]
    if pe:
        out += f" Se refiere a «{pe[0]}»."
    dv = [C.etiqueta(t) for t in X["deriv"].get(c, []) if C.etiqueta(t) and d["pos"][t] != pos]
    dv = [x for x in dict.fromkeys(dv) if C.nrm(x) != C.nrm(palabra)]
    if dv:
        out += f" Palabras de su familia: {C._lista(dv[:4])}."
    return out if len(out) > len(f"«{nom}» es {cat}.") + 1 else None


def _prof(c):
    """Altura de un concepto en el arbol de tipos (pasos hasta la raiz por el primer padre)."""
    d = _C()._load()
    n, x, vistos = 0, c, set()
    while d["hyp"].get(x) and x not in vistos:
        vistos.add(x)
        x = d["hyp"][x][0]
        n += 1
    return n


def _sust(txt, mem):
    """Resuelve un sustantivo (o frase corta) a (palabra tal como la escribio la persona, [conceptos]); None si no se conoce."""
    C = _C()
    r = C._resolver(txt, mem)
    if not r:
        return None
    nom = r[2] if r[0] == "ent" and r[2] else r[1]
    return nom, r[3]


def _lista(xs):
    return _C()._lista(xs)


def responder(t, raw, mem=None):
    """t: pregunta normalizada (sin tildes ni signos). Devuelve texto o None."""
    if not disponible():
        return None
    C = _C()
    ART = r"(?:un |una |unos |unas |el |la |los |las )?"
    # ---- para que sirve / que hace
    m = re.match(r"(?:y )?(?:para que|a que)\s+(?:sirve|sirven|se usa|se usan|se utiliza|se utilizan|se emplea|vale)\s+" + ART + r"(.+)$", t) or re.match(r"(?:y )?(?:que )?(?:uso|utilidad|funcion) (?:tiene|tienen) " + ART + r"(.+)$", t) \
        or re.match(r"(?:y )?(?:que )?se hace con " + ART + r"(.+)$", t) or re.match(r"(?:y )?(?:para que) (?:puedo usar|se puede usar|puedo utilizar|uso) " + ART + r"(.+)$", t)
    if m:
        pal0 = re.sub(r"^(?:un |una |el |la |los |las )", "", m.group(1).strip())
        if C.nrm(pal0) in FUNCION and not (mem is not None and getattr(mem, "facts", None) and any(C._st(f["s"]) == C._st(pal0) for f in mem.facts)):
            return f"Según mi diccionario de conceptos, «{C._vo(pal0)}» sirve para {FUNCION[C.nrm(pal0)]}."
        r = _sust(m.group(1), mem)
        if r:
            for c in r[1][:3]:
                f = funcion(c, m.group(1))
                if f:
                    return f"Según mi diccionario de conceptos, «{r[0]}» sirve para {f}."
            for c in r[1][:3]:
                vs = verbos_relacionados(c, 3)
                if vs:
                    return f"Según mi diccionario de conceptos, «{r[0]}» está relacionado con la acción de {_lista(vs)}."
        return None
    m = re.match(r"(?:y )?(?:que|cual es la) (?:hace|hacen|actividad de|ocupacion de|trabajo de|labor de) " + ART + r"(.+)$", t) or re.match(r"(?:y )?(?:a que se dedica|a que se dedican) " + ART + r"(.+)$", t) \
        or re.match(r"(?:y )?(?:que )?(?:hace|hacen) " + ART + r"(.+)$", t)
    if m:
        pal0 = re.sub(r"^(?:un |una |el |la |los |las )", "", m.group(1).strip())
        if C.nrm(pal0) in PROFESION:
            return f"Según mi diccionario de conceptos, un «{C._vo(pal0)}» se dedica a {PROFESION[C.nrm(pal0)]}."
        r = _sust(m.group(1), mem)
        if r:
            for c in r[1][:3]:
                a = accion(c, m.group(1))
                if a:
                    return f"Según mi diccionario de conceptos, la actividad de «{r[0]}» tiene que ver con {a}."
        return None
    # ---- relacion entre dos conceptos
    m = re.match(r"(?:y )?(?:que|cual) (?:relacion|conexion|vinculo|parentesco) (?:hay|existe|tienen|tiene|guardan) entre " + ART + r"(.+?) (?:y|e) " + ART + r"(.+)$", t) \
        or re.match(r"(?:y )?(?:que|cuanto) (?:tienen|tiene) que ver " + ART + r"(.+?) (?:y|con|e) " + ART + r"(.+)$", t) \
        or re.match(r"(?:y )?como se relacionan " + ART + r"(.+?) (?:y|con|e) " + ART + r"(.+)$", t) or re.match(r"(?:y )?como se relaciona " + ART + r"(.+?) con " + ART + r"(.+)$", t) \
        or re.match(r"(?:y )?(?:que )?(?:relacion|conexion) (?:hay|existe) de " + ART + r"(.+?) (?:con|a) " + ART + r"(.+)$", t) or re.match(r"(?:y )?(?:en que|de que manera) se (?:relacionan|conectan|vinculan) " + ART + r"(.+?) (?:y|con|e) " + ART + r"(.+)$", t)
    if m:
        ra, rb = _sust(m.group(1), mem), _sust(m.group(2), mem)
        if ra and rb:
            best = None
            for ca in ra[1][:3]:
                for cb in rb[1][:3]:
                    if ca == cb:
                        return f"Según mi diccionario de conceptos, «{ra[0]}» y «{rb[0]}» son nombres del mismo concepto."
                    cam = camino(ca, cb, 4.0)
                    if cam is not None and (best is None or len(cam) < len(best[2])):
                        best = (ca, cb, cam)
            if best:
                ca, cb, _cam = best
                tx = explicar_camino(ca, cb, ra[0], rb[0])
                if tx:
                    return "Según mi diccionario de conceptos: " + tx
            return f"Según mi diccionario de conceptos no encuentro una relación directa entre «{ra[0]}» y «{rb[0]}» (están en zonas lejanas del diccionario)."
        return None
    # ---- el intruso
    m = re.match(r"(?:y )?(?:cual|que) (?:no encaja|sobra|no pertenece|es el intruso|no pega|no va|no es como los demas|es diferente|es distinto)(?: de| entre| en| con)?\s*[:,]?\s*(?:los siguientes\s*)?(.+)$", t) \
        or re.match(r"(?:y )?(?:cual|que) (?:de estos|de estas|de los siguientes|de las siguientes)\s*(?:\w+\s+)?(?:no encaja|sobra|no pertenece|es diferente|es distinto)\s*[:,]?\s*(.+)$", t) \
        or re.match(r"(?:y )?(?:el |la )?intruso (?:entre|de|en)\s*[:,]?\s*(.+)$", t)
    if m:
        items = [w for w in re.split(r"\s*(?:,| y | o | e )\s*", m.group(1)) if w.strip()]
        items = [re.sub(r"^(?:el |la |los |las |un |una )", "", w.strip()) for w in items]
        if len(items) < 3 or len(items) > 7:
            return None
        res = [_sust(w, mem) for w in items]
        if any(r is None for r in res):
            return None
        cs = [r[1][0] for r in res]
        if len(set(cs)) < len(cs):
            return None
        media = []
        for i, ci in enumerate(cs):
            media.append((sum(C.coseno(ci, cj) for j, cj in enumerate(cs) if j != i) / (len(cs) - 1), i))
        media.sort()
        i = media[0][1]
        resto = [res[j][0] for j in range(len(cs)) if j != i]
        resto_c = [cs[j] for j in range(len(cs)) if j != i]
        cm = comun_es(resto_c[0], resto_c[1]) if len(resto_c) >= 2 else None
        for x in resto_c[2:]:
            if cm:
                cm = comun_es(cm, x) or cm
        et = lab(cm) if cm else None
        txt = f"Según mi diccionario de conceptos, «{res[i][0]}» es la que no encaja"
        if et and et.lower() not in GENERAL:
            txt += f": {_lista(['«' + x + '»' for x in resto])} son tipos de «{et}»"
            ci = C.cadena(cs[i], 1)
            if ci:
                txt += f", y «{res[i][0]}» es un tipo de «{ci[0]}»"
        return txt + "."
    # ---- a es a b como c es a ?
    m = re.match(r"(?:y )?" + ART + r"(\w+(?: \w+)?) es a " + ART + r"(\w+(?: \w+)?) como " + ART + r"(\w+(?: \w+)?) es a\s*\??\s*(?:que)?$", t)
    if m:
        def _s2(g):
            r_ = _sust(g, mem)
            if r_:
                return r_
            cs_ = C.conceptos(g, solo_nombres=False)
            return (C._vo(g), cs_) if cs_ else None
        try:                                                           # contrarios entre palabras (adjetivos, verbos): el lexico los guarda por palabra
            from src.language import lexico as _lx
            wa, wb, wc = (re.sub(r"^(?:un |una |el |la )", "", g) for g in (m.group(1), m.group(2), m.group(3)))
            if _lx.disponible():
                an_a = [C.nrm(x) for x in _lx.antonimos(wa)]
                if C.nrm(wb) in an_a or C.nrm(wa) in [C.nrm(x) for x in _lx.antonimos(wb)]:
                    an_c = [x for x in _lx.antonimos(wc) if " " not in x]
                    if an_c:
                        return f"Según mi diccionario de conceptos: «{C._vo(wa)}» es a «{C._vo(wb)}» (su contrario) como «{C._vo(wc)}» es a «{an_c[0]}»."
        except ImportError:
            pass
        ra, rb, rc = _s2(m.group(1)), _s2(m.group(2)), _s2(m.group(3))
        if ra and rb and rc:
            ca, cb, cc = ra[1][0], rb[1][0], rc[1][0]
            d = C._load()
            asc = C.ascendentes(ca)
            if cb in asc and asc[cb] > 0:
                prof = _prof(cb)                                   # la misma altura en el arbol: perro -> animal como rosa -> planta
                cand = [x for x, n_ in sorted(C.ascendentes(cc).items(), key=lambda kv: kv[1]) if C.etiqueta(x) and _prof(x) == prof]
                if cand:
                    return f"Según mi diccionario de conceptos: «{ra[0]}» es a «{rb[0]}» (su tipo) como «{rc[0]}» es a «{C.etiqueta(cand[0])}»."
            if ca in C.ascendentes(cb) and C.ascendentes(cb)[ca] > 0:
                ts = [x for x in C.tipos(cc, 3)]
                if ts:
                    return f"Según mi diccionario de conceptos: «{ra[0]}» es a «{rb[0]}» (un ejemplo suyo) como «{rc[0]}» es a «{ts[0]}»."
            for xa in ra[1][:4]:
                for xb in rb[1][:4]:
                    if xb in d["ant"].get(xa, []) or xa in d["ant"].get(xb, []):
                        for xc in rc[1][:4]:
                            if d["ant"].get(xc) and C.etiqueta(d["ant"][xc][0]):
                                return f"Según mi diccionario de conceptos: «{ra[0]}» es a «{rb[0]}» (su contrario) como «{rc[0]}» es a «{C.etiqueta(d['ant'][xc][0])}»."
            for k in ("parte", "miembro", "sustancia"):
                if cb in d[k].get(ca, []):
                    inv = _inv(k).get(cc, [])
                    pt = d[k].get(cc, [])
                    if pt and C.etiqueta(pt[0]):
                        return f"Según mi diccionario de conceptos: «{rb[0]}» es parte de «{ra[0]}» como «{C.etiqueta(pt[0])}» lo es de «{rc[0]}»."
        return None
    # ---- que se parece mas
    m = re.match(r"(?:y )?(?:de que|con que|con que cosa) (?:esta hecho|esta hecha|se hace|se fabrica|se elabora|se prepara|se compone|esta compuesto|esta compuesta) " + ART + r"(\w+)$", t)
    if m:
        r = _sust(m.group(1), mem)
        if r:
            for c in r[1][:3]:
                ps = C.partes(c, "sustancia", 6)
                if ps:
                    return f"Según mi diccionario de conceptos, «{r[0]}» está hecho de: {_lista(ps)}."
            c = r[1][0]
            rl = relacionados(c, 5)
            if rl:
                return f"Según mi diccionario de conceptos no tengo anotada su composición, pero en la definición de «{r[0]}» aparecen: {_lista(rl)}."
        return None
    m = re.match(r"(?:y )?(?:que|cual) (?:se parece|es mas parecido|es mas parecida|esta mas cerca|es mas cercano|es mas similar)\s+(?:mas\s+)?(?:a|de)\s+" + ART + r"(.+?)\s*[:,]\s*" + ART + r"(.+?) (?:o|y) " + ART + r"(.+)$", t) \
        or re.match(r"(?:y )?(?:que|cual) (?:se parece|es mas parecido|es mas parecida|es mas similar)\s+(?:mas\s+)?(?:a|de)\s+" + ART + r"(\w+),? (?:" + ART + r")?(\w+) (?:o|y) " + ART + r"(\w+)$", t) \
        or re.match(r"(?:y )?(?:a|de) (?:que|cual) se parece mas " + ART + r"(.+?)\s*[:,]\s*" + ART + r"(.+?) (?:o|a) " + ART + r"(.+)$", t) \
        or re.match(r"(?:y )?" + ART + r"(\w+) se parece mas a " + ART + r"(\w+) o a " + ART + r"(\w+)$", t)
    if m:
        gs = [g for g in m.groups() if g]
        if len(gs) >= 3:
            gs = gs[-3:]
            r0, r1, r2 = (_sust(g, mem) for g in gs)
            if r0 and r1 and r2:
                s1 = max(C.coseno(x, y) for x in r0[1][:3] for y in r1[1][:3])
                s2 = max(C.coseno(x, y) for x in r0[1][:3] for y in r2[1][:3])
                if abs(s1 - s2) < 0.02:
                    return f"Según mi diccionario de conceptos, «{r0[0]}» se parece casi igual a «{r1[0]}» que a «{r2[0]}» ({s1:.2f} y {s2:.2f} sobre 1)."
                ganador, perdedor, a, b = (r1, r2, s1, s2) if s1 > s2 else (r2, r1, s2, s1)
                return f"Según mi diccionario de conceptos, «{r0[0]}» se parece más a «{ganador[0]}» que a «{perdedor[0]}» (parecido {a:.2f} frente a {b:.2f} sobre 1)."
    # ---- ejemplos con cantidad: nombra tres animales / dame cinco frutas / dime algunos animales
    m = re.match(r"(?:y )?(?:dime|dame|nombra|cita|menciona|enumera|di|ponme|pon|escribe|lista)(?:me)? (?:(\w+) )?(?:ejemplos de |tipos de |cosas que sean )?(\w+(?: \w+)?)$", t)
    if m:
        k = _NUM.get(m.group(1) or "", 5)
        pl = m.group(2)
        if m.group(1) and m.group(1) not in _NUM and m.group(1) not in ("algunos", "algunas", "unos", "unas", "varios", "varias", "algunos"):
            if len(pl.split()) == 1:
                pl = m.group(1) + " " + pl                     # "dame ejemplos de instrumentos musicales" sin cantidad
                k = 5
            else:
                pl = None
        if pl and pl not in ("algo", "todo", "nada", "mas", "otro"):
            cand = []
            sing = []
            for w in pl.split():
                sing.append(next(iter(C._sing(w)), w) if w.endswith("s") else w)
            for w in [" ".join(sing)] + list(C._sing(pl)) + [pl]:
                for c in C.conceptos(w)[:3]:
                    if c not in cand:
                        cand.append(c)
            for c in cand:
                if not C._load()["hypo"].get(c):
                    continue
                ex = ejemplos(c, k)
                if len(ex) >= min(k, 2):
                    return f"Según mi diccionario de conceptos, algunos ejemplos de «{pl}» son: {_lista(ex)}."
        return None
    # ---- de que es parte / grupo
    m = re.match(r"(?:y )?(?:de que|de quien) es (?:parte|miembro|componente|pieza) " + ART + r"(.+)$", t) or re.match(r"(?:y )?(?:a que|en que) pertenece " + ART + r"(.+)$", t) \
        or re.match(r"(?:y )?(?:donde|en que) (?:se encuentra|se halla|va|esta) (?:la |el )?(?:parte|pieza)? ?" + ART + r"(\w+)$", t)
    if m:
        r = _sust(m.group(1), mem)
        if r:
            for c in r[1][:3]:
                tod = []
                for k in ("parte", "miembro", "sustancia"):
                    for x in _inv(k).get(c, []):
                        e = C.etiqueta(x)
                        if e and e not in tod:
                            tod.append(e)
                if not tod:
                    for k in ("parte", "miembro", "sustancia"):
                        for x in _inv(k).get(c, []):
                            e = C.etiqueta(x, "en")
                            if e and e not in tod:
                                tod.append(e)
                    if tod:
                        return f"Según mi diccionario de conceptos, «{r[0]}» es parte de: {_lista(tod[:3])} (nombres en inglés)."
                if tod:
                    return f"Según mi diccionario de conceptos, «{r[0]}» es parte de: {_lista(tod[:5])}."
        return None
    m = re.match(r"(?:y )?como se (?:llama|denomina) (?:un |el |al )?(?:grupo|conjunto|rebaño|manada|banda|coleccion) (?:de |del )" + ART + r"(\w+)$", t)
    if m:
        r = _sust(m.group(1), mem)
        if r:
            for c in r[1][:3]:
                gs = []
                for x in _inv("miembro").get(c, []):
                    e = C.etiqueta(x)
                    if e and e not in gs and not any(w.lower().startswith(("genus", "type genus", "family", "order ", "superfamily", "subfamily", "suborder", "class ", "phylum", "subclass", "tribe", "subgenus")) for w in C.nombres(x, "en")) and C.nrm(e.split()[0]) not in ("genero", "familia", "orden") and e.lower() not in C.TAXON:
                        gs.append(e)
                if gs:
                    return f"Según mi diccionario de conceptos, un grupo de «{r[0]}» se llama {_lista(['«' + g + '»' for g in gs[:3]], ) if len(gs) == 1 else 'por ejemplo ' + _lista(['«' + g + '»' for g in gs[:3]])}."
        return None
    # ---- ¿es X un A o un B?
    m = re.match(r"(?:y )?(?:es|son) " + ART + r"(\w+(?: \w+)?) " + ART + r"(\w+(?: \w+)?) o " + ART + r"(\w+(?: \w+)?)$", t) or re.match(r"(?:y )?" + ART + r"(\w+(?: \w+)?) (?:es|son) " + ART + r"(\w+(?: \w+)?) o " + ART + r"(\w+(?: \w+)?)$", t)
    if m:
        rx, ra, rb = (_sust(g, mem) for g in m.groups())
        if rx and ra and not rb:
            if any(C.es_un(x, y) is not None for x in rx[1][:3] for y in ra[1][:3]):
                return f"Según mi diccionario de conceptos, «{rx[0]}» es un tipo de «{ra[0]}»."
        if rx and rb and not ra:
            if any(C.es_un(x, y) is not None for x in rx[1][:3] for y in rb[1][:3]):
                return f"Según mi diccionario de conceptos, «{rx[0]}» es un tipo de «{rb[0]}»."
        if rx and ra and rb:
            va = any(C.es_un(x, y) is not None for x in rx[1][:6] for y in ra[1][:6])
            vb = any(C.es_un(x, y) is not None for x in rx[1][:6] for y in rb[1][:6])
            if va and not vb:
                return f"Según mi diccionario de conceptos, «{rx[0]}» es {'un tipo de' } «{ra[0]}», no de «{rb[0]}»."
            if vb and not va:
                return f"Según mi diccionario de conceptos, «{rx[0]}» es un tipo de «{rb[0]}», no de «{ra[0]}»."
            if va and vb:
                return f"Según mi diccionario de conceptos, «{rx[0]}» es un tipo de las dos cosas: «{ra[0]}» y «{rb[0]}»."
            return f"Según mi diccionario de conceptos, «{rx[0]}» no es ni un tipo de «{ra[0]}» ni de «{rb[0]}»."
        return None
    # ---- define / dime algo de / que tipo de cosa es
    m = re.match(r"(?:y )?(?:define|defineme|definir|como definirias|como definiria|como defines|como definiras|definicion de|dame la definicion de|dime la definicion de|cual es la definicion de|que entiendes por|que quieres decir con|explicame que es|explicame que significa|explicame) " + ART + r"(\w+)$", t)
    if m and m.group(1) not in ("que", "como"):
        r = C.describir(m.group(1), mem)
        return ("Según mi diccionario de conceptos: " + r) if r else None
    m = re.match(r"(?:y )?(?:que sabes|que conoces|que me puedes decir|que puedes decirme|que me dices|que me cuentas|que cuentas) (?:de|del|sobre|acerca de|acerca del) " + ART + r"(\w+)$", t)
    if m:
        if mem is not None and any(C._st(f["s"]) == C._st(m.group(1)) for f in getattr(mem, "facts", [])):
            return None
        r = C.describir(m.group(1), mem)
        return ("Según mi diccionario de conceptos: " + r) if r else None
    m = re.match(r"(?:y )?(?:que tipo de cosa|que clase de cosa|que clase de (?:objeto|animal|ser)|que categoria|a que categoria|a que grupo|de que tipo|de que clase|a que familia) (?:es|pertenece|son|pertenecen) " + ART + r"(\w+)$", t)
    if m:
        r = _sust(m.group(1), mem)
        if r:
            c = r[1][0]
            ch = C.cadena(c, 4)
            if ch:
                dom = C.dominio(c)
                return f"Según mi diccionario de conceptos, «{r[0]}» es un tipo de {_lista(['«' + x + '»' for x in ch[:3]])}" + (f" (dominio: {dom})." if dom else ".")
        return None
    return None
