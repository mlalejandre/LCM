"""parche-78: el termino de la comparacion se reconoce aunque la escuela lo etiquete csubj/nmod/ADJ (nombre leido como adjetivo)."""
from src.language.extract import triples_full
from src.language.school_parser import SchoolParser

S = SchoolParser


def _tr(rows):
    return [(t["s"], t["p"], t["o"], t["neg"]) for t in triples_full(rows, entities_only=True)]


def test_comparativo_con_termino_csubj_o_adjetivo():
    for dep, pos in (("csubj", "PROPN"), ("nmod", "ADJ"), ("csubj", "ADJ")):
        R = [("Rosa", "PROPN", 4, "nsubj", "rosa"), ("es", "AUX", 4, "cop", "ser"), ("más", "ADV", 4, "advmod", "mas"), ("baja", "ADJ", 0, "root", "bajo"),
             ("que", "SCONJ", 6, "mark", "que"), ("Clara", pos, 4, dep, "clara"), (".", "PUNCT", 4, "punct", ".")]
        assert _tr(S._fix_comparative(R)) == [("rosa", "mas_bajo_que", "clara", False)], (dep, pos)


def test_comparativo_no_toca_otras_frases():
    N = [("Rosa", "PROPN", 2, "nsubj", "rosa"), ("sabe", "VERB", 0, "root", "saber"), ("que", "SCONJ", 5, "mark", "que"), ("Clara", "PROPN", 2, "ccomp", "clara"),
         ("vino", "VERB", 2, "ccomp", "venir"), (".", "PUNCT", 2, "punct", ".")]
    assert S._fix_comparative(N) == [tuple(x) for x in N]
