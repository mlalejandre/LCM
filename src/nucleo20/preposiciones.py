"""LCM 2.10 · VALOR CONCEPTUAL DE LAS PREPOSICIONES.

Una preposición no tiene un único significado: propone varios PAPELES y los decide la clase del término
(lo que el núcleo sabe de fábrica: persona, lugar, vehículo, material, tiempo, evento, actitud…) y el verbo.
    con + persona -> compañía       con + objeto -> instrumento      con + actitud -> modo
    de  + lugar (ser/venir) -> origen   de + material -> materia   de + persona (ser) -> posesión
    en  + lugar -> lugar            en + vehículo -> medio           en + mes/año -> tiempo
    por + lugar (pasar) -> recorrido    por + fenómeno/enfermedad -> causa   por la noche -> tiempo
    para + infinitivo/evento -> finalidad   para + persona -> destinatario   para el lunes -> plazo
Las preguntas buscan un PAPEL, no una palabra: «¿dónde?» encuentra «en», «encima de» o «al lado de».
Cuando no hay papel claro se devuelve la preposición tal cual («de», «a»…) y la pregunta solo encuentra esa misma palabra.

Relaciones espaciales con su inversa (conceptos, no hechos del mundo):
    A encima de B  <->  B debajo de A        A delante de B <-> B detrás de A
    A al lado de B <->  B al lado de A        A cerca de B   <-> B cerca de A
    A dentro de B  ->   en B hay A            cerca / lejos son contrarios
"""
from __future__ import annotations

import re

from . import conceptos as KB
from . import morfo as M
from .morfo import sa

# ------------------------------------------------------------------ papeles
DESCRIPCION = {
    "lugar": "dónde", "destino": "adónde", "origen": "de dónde", "recorrido": "por dónde", "direccion": "hacia dónde",
    "tiempo": "cuándo", "t_inicio": "desde cuándo", "t_fin": "hasta cuándo", "t_antes": "antes de qué", "t_despues": "después de qué",
    "duracion": "cuánto tiempo", "plazo": "para cuándo", "compania": "con quién", "instrumento": "con qué", "medio": "cómo (medio)",
    "modo": "cómo (manera)", "carencia": "sin qué", "causa": "por qué", "finalidad": "para qué", "destinatario": "para quién",
    "materia": "de qué está hecho", "tema": "de qué / sobre qué", "posesion": "de quién", "oponente": "contra quién",
    "fuente": "según quién", "estado": "cómo está", "precio": "por cuánto", "agente": "por quién",
}

POSICION = {"encima_de": "sobre", "sobre": "sobre", "debajo_de": "bajo", "bajo": "bajo", "so": "bajo", "delante_de": "delante", "ante": "delante",
            "detras_de": "detras", "tras": "detras", "al_lado_de": "junto", "junto_a": "junto", "cabe": "junto", "dentro_de": "dentro",
            "fuera_de": "fuera", "cerca_de": "cerca", "lejos_de": "lejos", "enfrente_de": "enfrente", "alrededor_de": "alrededor", "entre": "entre"}
INVERSA = {"sobre": "bajo", "bajo": "sobre", "delante": "detras", "detras": "delante", "junto": "junto", "cerca": "cerca", "lejos": "lejos", "enfrente": "enfrente"}
CONTRARIA = {"sobre": {"bajo"}, "bajo": {"sobre"}, "delante": {"detras"}, "detras": {"delante"}, "cerca": {"lejos"}, "lejos": {"cerca"},
             "dentro": {"fuera"}, "fuera": {"dentro"}}
DECIR_REL = {"sobre": "encima de", "bajo": "debajo de", "delante": "delante de", "detras": "detrás de", "junto": "al lado de", "dentro": "dentro de",
             "fuera": "fuera de", "cerca": "cerca de", "lejos": "lejos de", "enfrente": "enfrente de", "alrededor": "alrededor de", "entre": "entre"}
# locución de la pregunta -> relación («¿qué hay encima de la mesa?»)
REL_DE_PREP = dict(POSICION)

_MOV = {"ir", "venir", "viajar", "volver", "llegar", "salir", "mudar", "marchar", "regresar", "caminar", "andar", "correr", "conducir", "pasear",
        "entrar", "subir", "bajar", "mandar", "enviar", "llevar", "traer", "acercar", "pasar", "volar", "navegar", "huir", "escapar", "partir", "trasladar", "emigrar"}
_UBIC = {"estar", "vivir", "trabajar", "estudiar", "quedar", "dormir", "comer", "cenar", "desayunar", "haber", "poner", "dejar", "guardar", "colocar",
         "meter", "aparcar", "esconder", "sentar", "tener", "encontrar", "jugar", "nacer", "residir", "alojar", "veranear"}
_TEMA_V = {"hablar", "saber", "tratar", "charlar", "discutir", "conversar", "quejar", "acordar", "olvidar", "enterar", "pensar", "escribir", "leer",
           "opinar", "preguntar", "contar", "informar", "aprender", "estudiar", "investigar", "reflexionar", "soñar", "bromear", "dudar"}
_CAUSA_V = {"morir", "temblar", "llorar", "sufrir", "cansar", "enfermar", "reir", "doler", "saltar", "gritar", "estallar", "agotar", "harto", "cansado", "muerto"}
_DAR_V = {"dar", "regalar", "llamar", "escribir", "decir", "enviar", "mandar", "contar", "preguntar", "prestar", "devolver", "pedir", "comprar", "vender",
          "explicar", "enseñar", "dedicar", "entregar", "llevar", "traer", "cocinar", "hacer", "preparar"}
_DET = {"el", "la", "los", "las", "lo", "un", "una", "unos", "unas", "mi", "mis", "tu", "tus", "su", "sus", "nuestro", "nuestra", "nuestros", "nuestras",
        "vuestro", "vuestra", "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas", "aquel", "aquella", "al", "del", "mucho", "mucha", "muchos",
        "muchas", "poco", "poca", "pocos", "pocas", "todo", "toda", "todos", "todas", "otro", "otra", "cada", "algun", "alguna", "varios", "varias", "tanto", "tanta"}
_HORA = re.compile(r"^(?:las?|la una)\s+(?:\d+|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)\b|^(?:\d+|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)(?:\s+y\s+media)?$|^(?:mediodia|medianoche)$")
_HACE = re.compile(r"^hace\s+")
_DUR = re.compile(r"^(?:\d+|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|quince|veinte|treinta|muchos|muchas|varios|varias|pocos|pocas|unos|unas|media)\s+(?:minutos?|horas?|dias?|semanas?|meses|mes|anos?|ratos?|hora)\b")
_PRECIO = re.compile(r"\b(?:euros?|dolares?|libras?|pesetas?|centimos?)\b")


def _cats_de_palabra(w):
    w = sa(w)
    for c in (w, sa(M.singular(w)) if w.endswith("s") else w):
        a = KB.ancestros(c)
        if a or c in KB.kb()["hijos"]:
            return [c] + list(a)
    return []


def categoria(texto, ent=None, nuc=None):
    """Clase gruesa del término de una preposición: persona, animal, lugar, vehiculo, medio_com, material, evento, tiempo, hora, duracion,
    actitud, emocion, enfermedad, fenomeno, actividad, organizacion, alimento, objeto, tema, infinitivo, propio, precio o ''."""
    t = sa((texto or "").strip().lower())
    if nuc is not None and ent and isinstance(ent, str):
        e = nuc.can(ent)
        if e in ("U", "L") or nuc.es_persona(e):
            return "persona"
        cl = nuc.E.get(e, {}).get("clase") or (e[2:] if e.startswith("K:") else "")
        if cl:
            c = _cat_de_clase(cl)
            if c:
                return c
        if e.startswith("N:") and not t:
            return "propio"
    if not t:
        return ""
    if _PRECIO.search(t):
        return "precio"
    if _HACE.match(t):
        return "tiempo"
    if _DUR.match(t):
        return "duracion"
    if _HORA.match(t):
        return "hora"
    ws = [w for w in re.findall(r"[a-zñ]+|\d+", t) if w not in _DET]
    if not ws:
        return ""
    orig_ws = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+|\d+", texto or "") if sa(w.lower()) not in _DET]
    if orig_ws and orig_ws[0][:1].isupper():
        return "propio"                                  # «a Granada», «por Jaén»: nombre propio antes que la fruta
    if any(x[1] == "inf" for x in M.analizar(ws[0])) and not _cats_de_palabra(ws[0]):
        return "infinitivo"
    for k in (2, 1):                                     # «llave inglesa», «manga pastelera», «fin de semana»
        if len(ws) >= k:
            c = _cat_de_clase(" ".join(ws[:k]))
            if c:
                return c
    if len(ws) >= 3 and ws[1] == "de":
        c = _cat_de_clase(" ".join(ws[:3]))
        if c:
            return c
    try:
        from .nucleo import FAMILIA, PERSONA_CLS
        w0 = sa(M.singular(ws[0])) if ws[0].endswith("s") else ws[0]
        if w0 in FAMILIA or M.masc(w0) in FAMILIA or w0 in PERSONA_CLS or M.masc(w0) in PERSONA_CLS:
            return "persona"
    except Exception:                                    # noqa
        pass
    orig = (texto or "").strip()
    if orig[:1].isupper() or re.search(r"(?:^|\s)[A-ZÁÉÍÓÚÑ]", orig):
        return "propio"
    return ""


def _cat_de_clase(cl):
    a = _cats_de_palabra(cl)
    if not a:
        return ""
    orden = [("persona", "persona"), ("profesional", "persona"), ("animal", "animal"), ("vehiculo", "vehiculo"), ("medio de comunicacion", "medio_com"),
             ("lugar", "lugar"), ("elemento", "lugar_obj"), ("mueble", "lugar_obj"), ("material", "material"), ("dia de la semana", "tiempo"),
             ("tiempo", "tiempo"), ("estacion", "tiempo"), ("evento", "evento"), ("actitud", "actitud"), ("emocion", "emocion"),
             ("enfermedad", "enfermedad"), ("fenomeno", "fenomeno"), ("actividad", "actividad"), ("organizacion", "organizacion"),
             ("alimento", "alimento"), ("bebida", "alimento"), ("deporte", "tema"), ("asignatura", "tema"), ("arte", "tema"), ("idioma", "tema"),
             ("documento", "objeto"), ("objeto", "objeto"), ("planta", "objeto")]
    for k, v in orden:
        if k in a:
            return v
    return ""


def papel(prep, cat, verbo="", texto="", hay_obj=False, otra_prep=None):
    """Papel de un complemento «prep + término». cat = categoria(término). Devuelve el papel o la propia preposición si no hay uno claro."""
    p, v = prep, verbo or ""
    if p in POSICION and p not in ("sobre", "entre", "tras", "ante", "bajo") or (p == "entre" and cat not in ("tiempo", "hora")):
        return "posicion:" + POSICION[p]
    if p in ("antes_de",):
        return "t_antes"
    if p in ("despues_de",):
        return "t_despues"
    if p == "a":
        if cat in ("hora", "tiempo"):
            return "tiempo"
        if cat in ("persona", "animal", "organizacion"):
            return "destinatario" if v not in _MOV or v in ("llevar", "mandar", "enviar", "traer") else "destino"
        if cat in ("lugar", "lugar_obj", "propio", "evento"):
            return "destino" if v in _MOV or v in ("asistir", "acudir", "invitar", "apuntar") else ("lugar" if v in _UBIC else "destino")
        if cat == "tema":
            return "tema"
        return "a"
    if p == "ante":
        return "posicion:delante" if cat in ("lugar", "lugar_obj", "objeto") else "ante"
    if p in ("bajo", "so"):
        return "posicion:bajo" if cat in ("lugar", "lugar_obj", "objeto", "propio", "") else ("estado" if cat == "fenomeno" else "bajo")
    if p == "con":
        if cat in ("persona", "animal", "organizacion", "propio"):
            return "compania"
        if cat in ("actitud", "emocion"):
            return "modo"
        if cat in ("enfermedad",):
            return "estado"
        if cat in ("objeto", "vehiculo", "medio_com", "material", "lugar_obj"):
            return "instrumento"
        if cat in ("alimento",):
            return "instrumento" if hay_obj else "con"
        return "con"
    if p == "contra":
        if cat in ("persona", "organizacion", "propio", "animal"):
            return "oponente"
        if cat in ("lugar_obj", "lugar", "objeto"):
            return "posicion:contra"
        if cat in ("enfermedad",):
            return "finalidad"
        return "contra"
    if p == "de":
        if otra_prep == "a" and cat in ("hora", "tiempo", "") and re.match(r"^(?:\d+|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b", sa(texto or "")):
            return "t_inicio"
        if cat == "material":
            return "materia"
        if cat in ("lugar", "propio") and (v in ("ser", "venir", "volver", "llegar", "salir", "regresar", "proceder", "escapar", "huir", "bajar") or v in _MOV):
            return "origen"
        if cat in ("persona", "organizacion") and v in ("ser", "pertenecer"):
            return "posesion"
        if v in _TEMA_V:
            return "tema"
        if cat in ("enfermedad", "emocion", "infinitivo") or v in _CAUSA_V:
            return "causa"
        if cat in ("tiempo",) and re.match(r"^(?:dia|noche|madrugada|tarde|mañana|manana)$", sa(texto or "")):
            return "tiempo"
        return "de"
    if p == "desde":
        return "t_inicio" if cat in ("tiempo", "hora", "evento", "enfermedad", "fenomeno") or _HACE.match(sa(texto or "")) else "origen"
    if p == "durante":
        return "duracion" if cat in ("duracion", "tiempo") else "tiempo"
    if p == "en":
        if cat in ("vehiculo", "medio_com"):
            return "medio"
        if cat in ("tiempo",) or re.match(r"^(?:\d{4}|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|primavera|verano|otono|invierno)$", sa(texto or "")):
            return "tiempo"
        if cat in ("duracion",):
            return "duracion"
        if cat in ("actitud", "emocion"):
            return "modo"
        if cat in ("lugar", "lugar_obj", "propio", "evento", "objeto", "organizacion", ""):
            return "lugar"
        return "en"
    if p == "hacia":
        return "tiempo" if cat in ("hora", "tiempo") else "direccion"
    if p == "hasta":
        return "t_fin" if cat in ("hora", "tiempo", "evento") else ("destino" if cat in ("lugar", "lugar_obj", "propio") else "hasta")
    if p in ("mediante", "via"):
        return "instrumento"
    if p == "para":
        if cat == "infinitivo":
            return "finalidad"
        if cat in ("persona", "animal", "organizacion"):
            return "destinatario"
        if cat in ("tiempo", "hora"):
            return "plazo"
        if cat in ("lugar", "propio") and v in _MOV:
            return "destino"
        if cat in ("lugar", "propio") and v in ("trabajar", "cocinar", "escribir", "diseñar", "jugar", "vender", "fichar", "competir", "producir", "fabricar"):
            return "destinatario"                         # «trabaja para un hotel», «juega para el Betis»
        return "finalidad"
    if p == "por":
        if cat == "precio":
            return "precio"
        if cat in ("tiempo",) or re.match(r"^(?:la |las )?(?:mananas?|tardes?|noches?|madrugadas?)$", sa(texto or "")):
            return "tiempo"
        if cat in ("lugar", "lugar_obj", "propio") and (v in _MOV or v in ("pasar", "cruzar", "atravesar", "pasear")):
            return "recorrido"
        if cat == "medio_com":
            return "medio"
        if cat in ("persona",) and v in ("ser",):
            return "agente"
        return "causa"
    if p == "segun":
        return "fuente"
    if p == "sin":
        return "carencia"
    if p == "sobre":
        if cat == "hora":
            return "tiempo"
        if v in _TEMA_V or cat in ("tema", "persona", "propio", "evento", "actividad", "fenomeno", "animal", "enfermedad"):
            return "tema"
        if v in _UBIC or cat in ("lugar_obj", "objeto", "lugar"):
            return "posicion:sobre"
        return "tema"
    if p == "tras":
        return "t_despues" if cat in ("evento", "tiempo", "hora", "actividad", "infinitivo") else "posicion:detras"
    if p == "versus":
        return "oponente"
    return p


# ------------------------------------------------------------------ preguntas -> papeles
def papeles_de_pregunta(tipo, prep, verbo="", sust=""):
    """Qué papeles responden a una pregunta. tipo = donde/cuando/como/porque/paraque/quien/que/cual/cuanto."""
    if tipo == "donde":
        return {"": {"lugar", "posicion"} | ({"destino"} if verbo in _MOV else set()), "a": {"destino", "direccion"}, "de": {"origen"},
                "desde": {"origen"}, "por": {"recorrido"}, "hasta": {"destino"}, "hacia": {"direccion", "destino"}, "en": {"lugar", "posicion"},
                "para": {"destino"}}.get(prep, set())
    if tipo == "cuando":
        return {"": {"tiempo", "t_antes", "t_despues", "t_inicio", "t_fin"}, "desde": {"t_inicio"}, "hasta": {"t_fin"}, "para": {"plazo"},
                "a": {"tiempo", "t_inicio", "t_fin"}}.get(prep, set())
    if tipo == "como":
        return {"modo", "medio", "instrumento", "carencia", "estado"}
    if tipo == "porque":
        return {"causa"}
    if tipo == "paraque":
        return {"finalidad"}
    if tipo in ("quien", "quienes"):
        return {"con": {"compania"}, "contra": {"oponente"}, "para": {"destinatario"}, "de": {"posesion"}, "a": {"destinatario"},
                "por": {"agente", "causa"}, "segun": {"fuente"}, "sobre": {"tema"}}.get(prep, set())
    if tipo in ("que", "cual"):
        if sust in ("tiempo",) and not prep:
            return set()
        return {"con": {"instrumento", "modo", "compania"}, "de": {"materia", "tema"}, "sobre": {"tema"}, "contra": {"oponente"}, "en": {"medio", "lugar"},
                "sin": {"carencia"}, "para": {"finalidad"}, "a": {"destino", "tema"}, "por": {"causa", "recorrido"}, "hasta": {"t_fin"}, "desde": {"t_inicio", "origen"}}.get(prep, set())
    if tipo == "cuanto":
        return {"duracion"} if sust in ("tiempo", "rato") else ({"precio"} if sust in ("dinero",) or prep == "por" else set())
    return set()


def casa_papel(p, buscados):
    return p in buscados or (p.startswith("posicion:") and "posicion" in buscados)
