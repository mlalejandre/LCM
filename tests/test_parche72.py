"""parche-72: un nombre propio leido como ADJ al principio de la frase pasa a ser sujeto."""
from src.language.extract import triples_full
from src.language.school_parser import SchoolParser

fix = SchoolParser._fix_name_adj


def _tr(rows):
    return [(t["s"], t["p"], t["o"], t["neg"]) for t in triples_full(rows, entities_only=True)]


def test_nombre_como_adjetivo_inicial():
    T = [("Clara", "ADJ", 2, "amod", "claro"), ("canta", "VERB", 0, "root", "cantar"), ("en", "ADP", 5, "case", "en"),
         ("el", "DET", 5, "det", "el"), ("coro", "NOUN", 2, "obl", "coro"), (".", "PUNCT", 2, "punct", ".")]
    assert fix(T)[0][1:4] == ("PROPN", 2, "nsubj")
    assert _tr(fix(T)) == [("clara", "cantar_en", "coro", False)]
    N = [("Clara", "ADJ", 3, "amod", "claro"), ("no", "ADV", 3, "advmod", "no"), ("compra", "VERB", 0, "root", "comprar"),
         ("leche", "NOUN", 3, "obj", "leche"), (".", "PUNCT", 3, "punct", ".")]
    assert _tr(fix(N)) == [("clara", "comprar", "leche", True)]


def test_no_toca_adjetivos_de_verdad():
    otro = [("Clara", "ADJ", 3, "amod", "claro"), ("Ana", "PROPN", 3, "nsubj", "ana"), ("canta", "VERB", 0, "root", "cantar"), (".", "PUNCT", 3, "punct", ".")]
    assert fix(otro)[0][1] == "ADJ"                                   # el verbo ya tiene sujeto
    minus = [("claro", "ADJ", 2, "amod", "claro"), ("canta", "VERB", 0, "root", "cantar"), (".", "PUNCT", 2, "punct", ".")]
    assert fix(minus)[0][1] == "ADJ"                                  # sin mayuscula inicial
    con_det = [("Clara", "ADJ", 2, "amod", "claro"), ("canta", "VERB", 0, "root", "cantar"), (".", "PUNCT", 2, "punct", ".")]
    assert fix(con_det[:1] + [("el", "DET", 1, "det", "el")] + con_det[1:])[0][1] == "ADJ"
