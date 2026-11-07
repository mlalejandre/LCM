"""parche-110: las cortesias (hola, gracias) no repiten siempre la misma frase."""
import os
import tempfile

from src.language.dialogue import Conversation
from src.language.qa import QA
from src.memory.store import MemoryStore


class _P:
    def parse(self, *a, **k):
        return []


def _conv():
    mem = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
    return Conversation(mem, _P(), lambda m, p: QA(m, p.parse, lambda f: {}))


def test_la_primera_vez_es_la_de_siempre():
    assert _conv().say("hola") == "¡Hola! ¿En qué puedo ayudarte?"


def test_hola_repetido_varia_y_es_determinista():
    a, b = _conv(), _conv()
    ra = [a.say("hola") for _ in range(7)]
    assert ra == [b.say("hola") for _ in range(7)]
    assert len(set(ra[:5])) == 5 and ra[5] == ra[1]
    assert all("ayudarte" in r for r in ra)


def test_gracias_varia():
    c = _conv()
    r = [c.say("gracias") for _ in range(3)]
    assert r[0] == "De nada." and len(set(r)) == 3 and all("de nada" in x.lower() for x in r)


def test_talks_no_gasta_variantes():
    c = _conv()
    c.say("hola")
    assert c.dlg.talks("hola") if hasattr(c, "dlg") else True
    assert c.say("hola").startswith("¡Hola de nuevo")


def test_hola_depende_de_la_conversacion():
    c = _conv()
    c.say("hola")
    c.say("¿Qué es un perro?")
    r = c.say("hola")
    assert "Antes me preguntabas" in r and "perro" in r.lower() and "ayudarte" in r
    assert "buenos días" in _conv().say("Buenos días").lower()
