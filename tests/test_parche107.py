"""parche-107: cartuchos de conocimiento general (mundo_*) y su convivencia con el diccionario."""
import json
import os
import tempfile

import pytest

from src.language import conceptos as C
from src.memory import cartuchos
from src.memory.store import MemoryStore


class _M:
    def __init__(self, facts, display=None):
        self.facts, self.display = facts, display or {}


def _f(s, p, o, **k):
    return {"s": s, "p": p, "o": o, "neg": False, **k}


def test_los_hechos_de_cartucho_no_silencian_el_diccionario():
    m = _M([_f("MARTILLO", "ES", "HERRAMIENTA", cart="mundo_objetos", source="mundo")], {"MARTILLO": "martillo", "HERRAMIENTA": "herramienta"})
    assert not C._conoce(m, "para que sirve un martillo")
    assert C.antes("¿Para qué sirve un martillo?", m) is not None
    assert C.complemento("¿Qué es un martillo?", m) is not None


def test_lo_que_ensena_la_persona_sigue_mandando():
    m = _M([_f("MARTILLO", "ES", "HERRAMIENTA", source="usuario")], {"MARTILLO": "martillo", "HERRAMIENTA": "herramienta"})
    assert C._conoce(m, "para que sirve un martillo")


def test_cartuchos_mundo_montan_y_se_retiran():
    d = tempfile.mkdtemp()
    h = [{"s": "PERRO", "p": "ES", "o": "ANIMAL", "n": 1, "t": 0, "source": "mundo", "imp": 1.0, "tick": 0, "archived": False, "neg": False, "when": "", "when_disp": "", "when_abs": None, "q": ""}]
    cartuchos.guardar_cartucho("mundo_x", {"hechos": h, "display": {"PERRO": "perro"}}, base=d)
    cartuchos.insertar("mundo_x", d)
    mem = MemoryStore(os.path.join(d, "m.json"))
    assert cartuchos.montar(mem, d) == [("mundo_x", 1)]
    assert mem.display["PERRO"] == "perro"
    cartuchos.retirar("mundo_x", d)
    cartuchos.montar(mem, d)
    assert not mem.facts


def test_cartuchos_generados_si_estan_instalados():
    base = "cartuchos"
    nombres = [n for n, *_ in cartuchos.listar(base) if n.startswith("mundo_")]
    if not nombres:
        pytest.skip("cartuchos mundo_* no instalados")
    total = 0
    for n in nombres:
        c = cartuchos.cargar(n, base)
        assert c["hechos"] and all(h["p"] in ("ES", "PARTE_DE") and h["s"] != h["o"] for h in c["hechos"])
        total += len(c["hechos"])
    assert total > 1000
