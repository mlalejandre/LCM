"""parche-104: habilidades sin analizador: unidades, calendario, geometria, operaciones con palabras."""
import os
import tempfile

import pytest

from src.memory.store import MemoryStore


class _P:
    def parse(self, *a, **k):
        return []


def _conv():
    from src.language.dialogue import Conversation
    from src.language.qa import QA
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    return Conversation(mem, _P(), lambda m, p: QA(m, p.parse, lambda f: {}))


@pytest.mark.parametrize("q,exp", [("cuántos metros tiene un kilómetro?", "1000 metros"), ("cuántos segundos tiene una hora?", "3600 segundos"), ("cuántos días tiene un año", "365"),
                                   ("cuántos días tiene febrero", "28"), ("cuántos lados tiene un triángulo", "tres lados"), ("cuánto es la mitad de 50", "25"),
                                   ("cuánto son 3 al cuadrado", "9"), ("cuenta hasta 5", "1, 2, 3, 4, 5"), ("cuanto son dos mas dos", "4")])
def test_habilidades(q, exp):
    assert exp in _conv()._skills_pre(q)


def test_dias_relativos():
    c = _conv()
    assert "fue" in c._skills_pre("hace 4 días que día fué?") and "será" in c._skills_pre("qué día será dentro de 10 días")
