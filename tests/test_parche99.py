"""parche-99: diccionario de conceptos (universales, multilingue, con jerarquia)."""
import pytest

from src.language import conceptos

pytestmark = pytest.mark.skipif(not conceptos.disponible(), reason="falta data/conceptos.json.gz")


class Mem:
    def __init__(self, facts, display=None):
        self.facts, self.display = facts, display or {}


def test_mismo_concepto_en_varias_lenguas():
    c = conceptos.conceptos("perro")[0]
    assert c in conceptos.conceptos("can") and c in conceptos.conceptos("dog") and c in conceptos.conceptos("chien")
    assert "dog" in conceptos.nombres(c, "en") and "chien" in conceptos.nombres(c, "fr")
    assert conceptos.conceptos("gato")[0] in conceptos.conceptos("cat")


def test_jerarquia_y_caracteristicas():
    c = conceptos.conceptos("perro")[0]
    assert conceptos.es_un(c, conceptos.conceptos("animal")[0]) is not None
    assert conceptos.es_un(conceptos.conceptos("gato")[0], c) is None
    ft = conceptos.caracteristicas(c)
    assert "animal" in ft["tipo_de"] and ft["dominio"] == "animal"


def test_vectores_parecido():
    p, g, co = (conceptos.conceptos(w)[0] for w in ("perro", "lobo", "coche"))
    assert conceptos.coseno(p, g) > 0.4 > conceptos.coseno(p, co)


def test_responder():
    assert "mismo concepto" in conceptos.responder("¿Es can lo mismo que perro?")
    assert "dog" in conceptos.responder("¿Cómo se dice perro en inglés?")
    assert conceptos.responder("¿Es un perro un animal?").startswith("Sí")
    assert " no" in conceptos.responder("¿Es un gato un perro?")
    assert "cánido" in conceptos.responder("¿Qué es un perro?")


def test_memoria_y_diccionario():
    m = Mem([{"s": "REX", "p": "ES", "o": "PERRO"}], {"REX": "Rex", "PERRO": "el perro"})
    assert conceptos.responder("¿Es Rex un animal?", m).startswith("Sí, Rex es un perro")
    assert conceptos.responder("¿Es Rex un can?", m).startswith("Sí")
    assert conceptos.responder("¿Es Rex un coche?", m).startswith("No")


def test_nombres_propios_no_se_inventan():
    assert conceptos.responder("¿Qué es Marte?") is None
    assert "perro" not in (conceptos.responder("¿Qué es serrucho?") or "")      # serrucho NO es sinonimo de perro: es una sierra


def test_clase_vs_entidad_con_semilla():
    m = Mem([{"s": "PERRO", "p": "ES", "o": "MAMIFERO", "source": "semilla"}, {"s": "PEZ", "p": "ES", "o": "ANIMAL", "source": "semilla"},
             {"s": "DELFIN", "p": "ES", "o": "MAMIFERO", "source": "semilla"}, {"s": "REX", "p": "ES", "o": "PERRO"}],
            {"PERRO": "el perro", "PEZ": "el pez", "DELFIN": "el delfín", "REX": "Rex"})
    assert "no" in conceptos.responder("¿Es un delfín un pez?", m).lower()            # 'pez' es una clase, no una entidad de clase animal
    assert "mismo concepto" in conceptos.responder("¿Es can lo mismo que perro?", m)
    assert conceptos.responder("¿Qué características tiene un perro?", m).startswith("Según mi diccionario")
    assert conceptos.complemento("¿Qué es un perro?", m).startswith("Según mi diccionario")
    assert conceptos.complemento("¿Qué es Rex?", m) is None
