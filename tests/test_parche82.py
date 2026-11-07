"""parche-82: nombre propio colgado como aposicion de un adverbial temporal."""
from src.language.extract import triples_full
from src.language.school_parser import SchoolParser


def test_lunes_nico():
    R = [("Los", "DET", 2, "det", "el"), ("lunes", "NOUN", 4, "obl", "lunes"), ("Nico", "PROPN", 2, "appos", "nico"), ("va", "VERB", 0, "root", "ir"),
         ("a", "ADP", 7, "case", "a"), ("el", "DET", 7, "det", "el"), ("gimnasio", "NOUN", 4, "obl", "gimnasio"), (".", "PUNCT", 4, "punct", ".")]
    got = SchoolParser._fix_temporal_appos(R)
    assert got[2][2:4] == (4, "nsubj")
    assert [(t["s"], t["p"], t["o"]) for t in triples_full(got, entities_only=True)] == [("nico", "ir_a", "gimnasio")]


def test_no_toca_otras_aposiciones():
    A = [("El", "DET", 2, "det", "el"), ("perro", "NOUN", 4, "nsubj", "perro"), ("Toby", "PROPN", 2, "appos", "toby"), ("ladra", "VERB", 0, "root", "ladrar"), (".", "PUNCT", 4, "punct", ".")]
    assert SchoolParser._fix_temporal_appos(A) == [tuple(x) for x in A]
