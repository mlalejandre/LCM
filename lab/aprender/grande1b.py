"""APRENDER · EXAMEN GRANDE 1, CORREGIDO. Mismos textos y preguntas que grande1; cambia solo la CLAVE de las preguntas cuya respuesta no se
seguía del texto (observación de Marcos: «trabajan de noche» no dice que no trabajen de día).
  - Deducciones en las que el texto no excluye lo preguntado: vale abstenerse o dar el dato que sí se sabe.
  - «Contradicciones» que en realidad son compatibles con lo leído (otra estación, otro sitio, otro ingrediente): no se puntúan
    (criterio ANY); se miran aparte, porque lo ideal es avisar de que es distinto sin llamarlo contradicción.
  - Un criterio mal escrito («medicos» en vez de «medico*»).
El original se conserva tal cual en grande1.py. Sigue siendo una vara fija: no se usa para desarrollar."""
import copy

from lab.aprender import grande1 as _G

CAMBIOS = {
    # deducciones: el texto no excluye lo preguntado
    "¿los castores trabajan de día?": "noche|ABST",                      # «trabajan sobre todo de noche»
    "¿las maletas viajan con los pasajeros?": "bodega|ABST",             # se dijo dónde van las maletas, no dónde van los pasajeros
    "¿el público aplaude antes del concierto?": "terminar|ABST",         # «al terminar el concierto el público aplaude»
    "¿la sosa es buena para la piel?": "^no|quema|ABST",                 # hace falta saber que quemar es malo: conocimiento del mundo
    # afirmaciones distintas de lo leído pero compatibles: no se puntúan
    "las ballenas viajan hacia aguas cálidas en verano": "ANY",
    "las maletas viajan en la cabina del avión": "ANY",
    "los artistas ensayan cada noche": "ANY",
    "el jabón de Marsella se hace con aceite de girasol": "ANY",
    "los bebés nacen en el quirófano": "ANY",
    "en Japón el arroz se come con cuchara": "ANY",
    # criterio mal escrito
    "¿qué son los cirujanos?": "medico*",
}
COMPATIBLES = [q for q, c in CAMBIOS.items() if c == "ANY"]


def _aplica(sondas):
    return [(t, q, CAMBIOS.get(q, c)) for t, q, c in sondas]


TEMAS = []
for _t in _G.TEMAS:
    _n = copy.deepcopy(_t)
    _n["frases"] = [(f, _aplica(ss)) for f, ss in _n["frases"]]
    _n["extra"] = _aplica(_n["extra"])
    TEMAS.append(_n)
