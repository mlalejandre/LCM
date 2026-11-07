"""parche-98: lexico (sinonimos, antonimos, tipo de) y sinonimos conocidos por la memoria."""
import pytest

from src.language import consultas, lexico

pytestmark = pytest.mark.skipif(not lexico.disponible(), reason="falta data/lexico_es.json")


def test_sinonimos_antonimos():
    assert "auto" in lexico.sinonimos("coche")
    assert "pequeño" in lexico.antonimos("grande")
    assert "vender" in lexico.antonimos("comprar")


def test_tipo_de():
    assert lexico.es_un_tipo_de("gato", "animal")
    assert not lexico.es_un_tipo_de("gato", "piedra")


def test_responder_palabras():
    assert "veloz" in lexico.responder("¿Cuál es el sinónimo de rápido?")
    assert "vender" in lexico.responder("¿Cuál es lo contrario de comprar?")
    assert lexico.responder("¿Qué es Marte?") is None          # nombres propios: no se inventa un sentido
    assert lexico.responder("¿Es Marte un planeta?") is None


def test_sinonimizar_usa_la_memoria():
    class M:
        facts = [{"s": "PLUTON", "p": "SER", "o": "ENANO"}]
        display = {}
    assert "enano" in consultas.sinonimizar("¿Es Plutón diminuto?", M())
    assert consultas.sinonimizar("¿Es Plutón enano?", M()) == "¿Es Plutón enano?"
    assert consultas.SUBS and consultas.SUBS[-1][0].lower() == "diminuto"


def test_no_corrige_palabras_del_lexico():
    class M:
        facts = []
        display = {}
    assert consultas.corregir("¿Qué es un caballo?", M()) == "¿Qué es un caballo?"


def test_canonical_lexico():
    assert consultas.canonical("Dime otra palabra para comprar") == "¿Dime otra palabra para comprar?"
    assert consultas.canonical("¿Qué sinónimos tiene coche?") == "¿Cuál es el sinónimos de coche?"
    assert consultas.canonical("¿Qué planeta está más próximo al Sol?") == "¿Cuál es el planeta más cercano al Sol?"
