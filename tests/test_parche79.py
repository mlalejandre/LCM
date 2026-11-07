"""parche-79: el termino de la comparacion se recupera con etiquetas raras (appos/flat) y cuando el adjetivo queda sin raiz."""
from src.language.extract import triples_full
from src.language.school_parser import SchoolParser

S = SchoolParser


def _tr(rows):
    return [(t["s"], t["p"], t["o"], t["neg"]) for t in triples_full(rows, entities_only=True)]


def test_termino_appos():
    R = [("Sofía", "PROPN", 4, "nsubj", "sofia"), ("es", "AUX", 4, "cop", "ser"), ("más", "ADV", 4, "advmod", "mas"), ("lista", "ADJ", 0, "root", "lista"),
         ("que", "SCONJ", 6, "mark", "que"), ("Eva", "PROPN", 4, "appos", "eva"), (".", "PUNCT", 4, "punct", ".")]
    assert _tr(S._fix_comparative(R)) == [("sofia", "mas_lista_que", "eva", False)]


def test_pregunta_con_flat_y_sin_raiz():
    R = [("Es", "AUX", 4, "cop", "ser"), ("Rosa", "PROPN", 4, "nsubj", "rosa"), ("más", "ADV", 4, "advmod", "mas"), ("joven", "ADJ", 2, "amod", "joven"),
         ("que", "SCONJ", 6, "mark", "que"), ("Elena", "PROPN", 2, "flat", "elena"), (".", "PUNCT", 4, "punct", ".")]
    assert _tr(S._fix_comparative(R)) == [("rosa", "mas_joven_que", "elena", False)]


def test_sin_comparativo_no_se_toca():
    N = [("Luis", "PROPN", 2, "nsubj", "luis"), ("come", "VERB", 0, "root", "comer"), ("que", "SCONJ", 4, "mark", "que"), ("Ana", "PROPN", 2, "flat", "ana")]
    assert S._fix_comparative(N) == [tuple(x) for x in N]
