"""parche-117: preguntas sobre lo aprendido de textos, traza de lectura y adjetivos con lema verbal."""
import os
import tempfile

from src.language.dialogue import Conversation
from src.language.lector_ud import LectorUD, escribir_traza
from src.language.qa import QA
from src.memory.store import MemoryStore
from src.reasoning.lessons import deduce_all


def _conv():
    m = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
    m.add_fact(("AKIRA_TORIYAMA", "CREAR", "GOKU"), when="1984")
    m.add_fact(("GOKU", "EXHIBIR", "COLA_DE_MONO"))
    m.add_fact(("LEON", "COMER", "CARNE"))
    m.add_fact(("ANA", "ESCRIBIR", "POEMA"))
    return Conversation(m, None, lambda mm, p: QA(mm, (lambda *a: []), lambda f: deduce_all(f, mm.active_lessons())))


def test_preguntas_sobre_lo_leido():
    c = _conv()
    for q in ("quien creo a Goku?", "quien es el creador de Gokū?", "Quien fue el creador de goku?"):
        assert "Toriyama" in c.say(q), q
    assert "Cola" in c.say("que exhibe Goku?")
    assert "Carne" in c.say("que come el leon?")
    assert "Poema" in c.say("quien escribe poemas?")
    assert "Toriyama" not in c.say("quien escribio el poema?")


def test_sin_dato_sigue_diciendo_que_no_sabe():
    c = _conv()
    assert "Toriyama" not in c.say("quien dibujo a Goku?")


class _P:
    def tree(self, s):
        return [("Goku", "PROPN", 3, "nsubj", "Goku"), ("fue", "AUX", 3, "cop", "ser"), ("vencido", "ADJ", 0, "root", "vencer"), (".", "PUNCT", 3, "punct", ".")]


def test_adjetivo_con_lema_verbal_y_traza():
    m = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
    rep = LectorUD(m, _P()).leer("Goku fue vencido por alguien conocido.")
    claves = {(h["s"], h["p"], h["o"]) for h in rep["hechos"]}
    assert ("GOKU", "SER", "VENCIDO") in claves and not any(o == "VENCER" for _, _, o in claves)
    ruta = os.path.join(tempfile.mkdtemp(), "r", "l.txt")
    escribir_traza(rep, ruta)
    assert "GOKU SER VENCIDO" in open(ruta, encoding="utf-8").read()
