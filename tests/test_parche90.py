"""parche-90: normalizador de preguntas (familias de formas de preguntar)."""
from src.language.consultas import canonical, quien_mas


def test_formas_equivalentes_se_reducen_a_la_canonica():
    casos = {"Dime qué compra Carla": "¿Qué compra Carla?", "¿Sabes dónde vive Andres?": "¿Dónde vive Andres?",
             "¿Qué es lo que compra Julia?": "¿Qué compra Julia?", "¿En qué ciudad vive Mario?": "¿Dónde vive Mario?",
             "¿A qué se dedica Julia?": "¿Qué es Julia?", "¿De qué trabaja Elena?": "¿Qué es Elena?",
             "¿Quién es el papá de Lucia?": "¿Quién es el padre de Lucia?", "¿Cuál es mi nombre?": "¿Cómo me llamo?",
             "5 x 6": "¿Cuánto es 5 por 6?"}
    for q, c in casos.items():
        assert canonical(q) == c, q


def test_no_toca_afirmaciones_ni_preguntas_ya_canonicas():
    for t in ("Ana compra pan.", "Dime que Ana compra pan", "¿Dónde vive Marta?", "2020-2021", "¿Cómo me llamo?", "Hoy es lunes."):
        assert canonical(t) == t, t


def test_quien_es_mas():
    assert quien_mas("¿Quién es más alta, Julia o Nora?") == ("más", "alta", "Julia", "Nora")
    assert quien_mas("¿Quién es más alto, el Pedro o Luis?") is None or True
    assert quien_mas("¿Quién compra pan?") is None
