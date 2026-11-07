"""parche-83: "Lo contrario de grande es pequeno" se normaliza igual que "Pequeno es lo contrario de grande"; "donde" con sujeto con determinante."""
from src.language.extract import triples_full
from src.language.qa import rewrite
from src.language.school_parser import SchoolParser


def test_lo_contrario_invertido():
    R = [("Lo", "PRON", 2, "det", "el"), ("contrario", "NOUN", 6, "nsubj", "contrario"), ("de", "ADP", 4, "case", "de"), ("grande", "NOUN", 2, "nmod", "grande"),
         ("es", "AUX", 6, "cop", "ser"), ("pequeño", "ADJ", 0, "root", "pequeno"), (".", "PUNCT", 6, "punct", ".")]
    got = SchoolParser._fix_lo_contrario(R)
    assert [(t["s"], t["p"], t["o"]) for t in triples_full(got, entities_only=True)] == [("pequeño".replace("ñ", "n"), "contrario_de", "grande")]


def test_pregunta_lo_contrario_con_copula_en_el_sujeto():
    Q = [("Lo", "PRON", 2, "det", "el"), ("contrario", "NOUN", 0, "root", "contrario"), ("de", "ADP", 4, "case", "de"), ("grande", "NOUN", 2, "nmod", "grande"),
         ("es", "AUX", 6, "cop", "ser"), ("Xqx", "PROPN", 2, "nsubj", "xqx"), (".", "PUNCT", 2, "punct", ".")]
    assert [(t["s"], t["p"], t["o"]) for t in triples_full(SchoolParser._fix_lo_contrario(Q), entities_only=True)] == [("xqx", "contrario_de", "grande")]


def test_donde_con_determinante():
    assert rewrite("¿Dónde juegan los niños?")[0][0] == "los niños juegan en Xqx."
