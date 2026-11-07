"""parche-86: nombre propio de una cosa ("se llama") y "¿Como lo sabes?" con verbo + preposicion."""
from src.language.qa import QA
from src.language.school_parser import SchoolParser
from src.memory.store import MemoryStore


def test_se_llama(tmp_path):
    p = SchoolParser.__new__(SchoolParser)
    p.today = None
    got = SchoolParser.parse(p, "El perro de Irene se llama Toby.")
    assert [(t["s"], t["p"], t["o"]) for t in got] == [("perro_de_irene", "llamarse", "toby")]
    m = MemoryStore(str(tmp_path / "m.json"))
    for t in got:
        tr = (t["s"], t["p"], t["o"])
        m.add_fact(tr, source="x")
        m.note_surface(tr, t["template"], t["s_disp"], t["o_disp"])
    qa = QA(m, lambda s: None)
    assert qa.answer("¿Cómo se llama el perro de Irene?") == "El perro de Irene se llama Toby."

