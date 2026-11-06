from src.language.extract import triples_full
from src.language.irregulares import IRREG
from src.language.school_parser import SchoolParser


def tree(rows):
    return [tuple(r) for r in rows]


def test_irregulares():
    assert IRREG["duerme"] == "dormir" and IRREG["puede"] == "poder" and IRREG["vino"] == "venir"
    assert "se" not in IRREG and "como" not in IRREG


def test_nombre_mas_verbo_en_minusculas():
    rows = [("Ana", "PROPN", 0, "root", "ana"), ("duerme", "PROPN", 1, "flat", "duerme"), (".", "PUNCT", 1, "punct", ".")]
    fixed = SchoolParser._fix_name_verb(rows)
    assert fixed[1][1] == "VERB" and fixed[1][3] == "root" and fixed[0][3] == "nsubj"


def test_intransitivo_y_adjetivo():
    t = tree([("Luis", "PROPN", 2, "nsubj", "luis"), ("llegó", "VERB", 0, "root", "llegar"), (".", "PUNCT", 2, "punct", ".")])
    assert [(x["s"], x["p"], x["o"]) for x in triples_full(t)] == [("luis", "llegar", "_")]
    t = tree([("La", "DET", 2, "det", "el"), ("casa", "NOUN", 4, "nsubj", "casa"), ("es", "AUX", 4, "cop", "ser"),
              ("grande", "ADJ", 0, "root", "grande"), (".", "PUNCT", 4, "punct", ".")])
    assert [(x["s"], x["p"], x["o"]) for x in triples_full(t)] == [("casa", "ser", "grande")]
