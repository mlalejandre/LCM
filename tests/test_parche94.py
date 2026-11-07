"""parche-94: listas y recuentos de una clase, 'dime algo de X', definicion por enumeracion, asteroides."""
import os
import tempfile

from src.language.consultas import canonical
from src.language.qa import QA
from src.language.school_parser import SchoolParser
from src.memory.store import MemoryStore
from src.reasoning.lessons import canon


def _qa(facts, display=None):
    mem = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
    for f in facts:
        mem.add_fact(f)
    mem.display.update(display or {})
    return QA(mem, lambda s: [], lambda fs: [])


def test_dime_algo_de():
    for q in ("¿Qué me puedes decir de Mercurio?", "Háblame de Mercurio", "Cuéntame algo sobre Mercurio", "¿Qué información tienes sobre Mercurio?"):
        assert canonical(q) == "¿Qué sabes de Mercurio?", q
    assert canonical("Dime los planetas que sabes") == "¿Cuáles son los planetas que conoces?"
    assert canonical("Dime que Ana compra pan") == "Dime que Ana compra pan"


def test_lista_y_recuento():
    qa = _qa([("MERCURIO", "es", "planeta"), ("VENUS", "es", "planeta"), ("TIERRA", "es", "planeta"), ("PLUTON", "es", "gigante")], {"TIERRA": "la Tierra", "PLANETA": "un planeta"})
    assert qa.special("¿Cuántos planetas hay en el sistema solar?") == "Conozco 3 planetas: Mercurio, Venus y la Tierra."
    assert qa.special("¿Cuáles son los planetas que conoces?").startswith("Los planetas que conozco son: Mercurio, Venus y la Tierra")
    assert qa.special("¿Qué planetas conoces?") is not None
    assert not (qa.special("¿Cuántos unicornios hay?") or "").startswith("Conozco")


def test_definicion_por_enumeracion():
    p = SchoolParser.__new__(SchoolParser)
    p.parse = lambda s, topic=None, verbs=None: [{"s": "planetas", "p": "orbitar_alrededor_de", "o": "sol", "neg": False}] if s.startswith("Los planetas") else []
    got = SchoolParser.parse(p, "El Sistema Solar es el conjunto de planetas, asteroides, cometas y lunas que orbitan alrededor del Sol.")
    objs = [(t["s"], t["p"], t["o"]) for t in got]
    assert ("sistema_solar", "conjunto_de", "planetas") in objs and ("sistema_solar", "conjunto_de", "lunas") in objs and ("planetas", "orbitar_alrededor_de", "sol") in objs
    qa = _qa([(t["s"], t["p"], t["o"]) for t in got if t["p"] == "conjunto_de"], {"SISTEMA_SOLAR": "el Sistema Solar"})
    assert qa.special("¿De qué se compone el Sistema Solar?") == "El Sistema Solar está formado por planetas, asteroides, cometas y lunas."


def test_asteroides_singular():
    assert canon("ASTEROIDES") == canon("ASTEROIDE") == "ASTEROIDE"
    assert canon("CIUDADES") == "CIUDAD" and canon("PLANETAS") == "PLANETA"
