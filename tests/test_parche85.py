"""parche-85: "No, X ..." es una correccion y las preguntas especiales se pueden justificar."""
import re

from src.language.dialogue import Conversation


class _QA:
    def answer(self, q):
        return "ok"

    def read(self, q):
        return None, None


def test_no_coma_es_correccion(tmp_path):
    from src.memory.store import MemoryStore
    m = MemoryStore(str(tmp_path / "m.json"))
    seen = []

    class P:
        today = None

        def parse(self, s, topic=None, verbs=None):
            seen.append(s)
            return None

    c = Conversation(m, P(), lambda mem, p: _QA())
    c.say("No, Marta vive en Vigo.")
    assert "Marta vive en Vigo." in seen and not any(s.startswith("No,") for s in seen)
    seen.clear()
    c.say("No, no vive en Vigo.")                              # con otra negacion no se toca
    assert any(s.lower().startswith("no") for s in seen)
