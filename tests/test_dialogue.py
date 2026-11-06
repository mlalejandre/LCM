from src.language.dialogue import Dialogue, n, _article
from src.memory.store import MemoryStore


def mk(tmp_path):
    return Dialogue(MemoryStore(str(tmp_path / "m.json")))


def test_social(tmp_path):
    d = mk(tmp_path)
    assert d.act("Hola", None)[0].startswith("¡Hola")
    assert d.act("¡Gracias!", None)[0] == "De nada."
    assert d.act("Perdona", None)[0] == "No pasa nada."
    assert n("¿Qué día es hoy?") == "que dia es hoy"


def test_name_and_possessive(tmp_path):
    d = mk(tmp_path)
    reply, cont = d.act("Mi madre es Ana.", None)
    assert "cómo te llamas" in reply.lower() and cont is None
    reply, cont = d.act("Me llamo Marcos", None)
    assert cont == "La madre de Marcos es Ana."


def test_references(tmp_path):
    d = mk(tmp_path)
    d.user = "Marcos"
    assert d.act("Ese perro muerde a Pedro.", None)[1] == "El perro muerde a Pedro."
    assert d.act("Javier tampoco compró pan.", None)[1] == "Javier no compró pan."
    assert d.act("Ana también compró pan.", None)[1] == "Ana compró pan."
    assert _article("madre") == "la" and _article("hermano") == "el"


def test_ask_unknown_and_define(tmp_path):
    d = mk(tmp_path)
    assert "explicas" in d.act("¿Qué es un tenedor?", None)[0]
    assert d.act("Es un cubierto", None)[1] == "Un tenedor es un cubierto."
