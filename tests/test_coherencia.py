from src.reasoning.coherence import classify, opposite, to_past
from src.memory.store import MemoryStore


def F(s, p, o, neg=False, when=""):
    return {"s": s, "p": p, "o": o, "neg": neg, "when": when}


def test_cambio_de_estado():
    k, old = classify([F("ANA", "VIVIR_EN", "MADRID")], ("ana", "vivir_en", "sevilla"), False)
    assert k == "supersede" and old["o"] == "MADRID"
    assert classify([F("ANA", "VIVIR_EN", "MADRID")], ("ana", "trabajar_en", "sevilla"), False)[0] == ""
    assert classify([F("ANA", "VIVIR_EN", "MADRID", when="2020")], ("ana", "vivir_en", "sevilla"), False)[0] == ""


def test_contradicciones():
    assert classify([F("LUIS", "AMAR_A", "ANA")], ("luis", "amar_a", "ana"), True)[0] == "negation"
    assert classify([F("CASA", "SER", "GRANDE")], ("casa", "ser", "pequena"), False)[0] == "antonym"
    assert opposite("alta", "bajo") and not opposite("alto", "rojo")
    assert classify([F("PEDRO", "VIVIR_EN", "X")], ("pedro", "vivir_en", "x"), True, ya_no=True)[0] == "supersede_neg"


def test_pasado(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("ana", "vivir_en", "madrid"))
    to_past(m, m.facts[0], "2026-11-06")
    assert not m.facts and m.past[0]["until"] == "2026-11-06"
