"""parche-95: erratas en preguntas, caracteristicas de X, articulo indefinido."""
from src.language import consultas as c


class _M:
    facts = [{"s": "MARTE", "p": "ES", "o": "PLANETA"}]
    display = {"MARTE": "Marte"}


def test_corregir_errata():
    assert "planeta" in c.corregir("¿Cual es el plaeta mas grande?", _M())
    assert "planeta" in c.corregir("¿Qué es un plneta?", _M())


def test_corregir_no_toca_nombres_ni_conocidas():
    assert c.corregir("¿Dónde vive Bertoldo?", _M()) == "¿Dónde vive Bertoldo?"
    assert c.corregir("¿Qué es un planeta?", _M()) == "¿Qué es un planeta?"


def test_caracteristicas():
    assert c.canonical("¿Cuáles son las características de Marte?") == "¿Qué sabes de Marte?"
    assert c.canonical("Describe Marte") == "¿Qué sabes de Marte?"
    assert c.canonical("Dame información de Saturno") == "¿Qué sabes de Saturno?"


def test_es_fallo():
    assert c.es_fallo("No lo sé.") and c.es_fallo("No conozco «plaeta»") and not c.es_fallo("Sí.")
