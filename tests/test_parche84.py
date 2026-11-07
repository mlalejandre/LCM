"""parche-84: "¿Como lo sabes?" cae a lo ultimo que dije cuando la pregunta se lee pero no da hechos; contrario simetrico."""
from src.language.dialogue import Dialogue
from src.language.qa import QA
from src.memory.store import MemoryStore


def test_explicar_cae_a_lo_ultimo_dicho(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("pedro", "vivir_en", "madrid"), source="Pedro vive en Madrid.")
    table = {"Xqx vive en Madrid.": [{"s": "xqx", "p": "vivir_en", "o": "sevilla", "neg": False}],
             "Pedro vive en Madrid.": [{"s": "pedro", "p": "vivir_en", "o": "madrid", "neg": False}]}
    qa = QA(m, lambda s: table.get(s))
    d = Dialogue(m)
    d.last_question, d.last = "¿Dónde vive Pedro?", "Pedro vive en Madrid."
    qa.read = lambda q: ("objeto", {"s": "pedro", "p": "vivir_en", "o": "sevilla"})
    assert "dijiste" in d.explain(qa).lower()


def test_contrario_simetrico(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("alto", "contrario_de", "bajo"))
    qa = QA(m, lambda s: None)
    assert qa.answer("¿Cuál es lo contrario de bajo?") == "Lo contrario de bajo es alto."
    assert qa.answer("¿Cuál es lo contrario de alto?") == "Lo contrario de alto es bajo."
