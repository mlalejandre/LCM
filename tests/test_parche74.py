"""parche-74: comparativos con "que" etiquetado como mark o como case."""
from src.language.extract import triples_full
from src.reasoning.lessons import compare


def _tr(rows):
    return [(t["s"], t["p"], t["o"], t["neg"]) for t in triples_full(rows, entities_only=True)]


def _frase(sujeto, objeto, rel_que):
    return [(sujeto, "PROPN", 4, "nsubj", sujeto.lower()), ("es", "AUX", 4, "cop", "ser"), ("más", "ADV", 4, "advmod", "mas"),
            ("alto", "ADJ", 0, "root", "alto"), ("que", "SCONJ", 6, rel_que, "que"), (objeto, "PROPN", 4, "nmod", objeto.lower()),
            (".", "PUNCT", 4, "punct", ".")]


def test_comparativo_con_que_case_y_mark():
    for rel in ("case", "mark"):
        assert _tr(_frase("Luis", "Pedro", rel)) == [("luis", "mas_alto_que", "pedro", False)]


def test_comparativo_encadena_con_compare():
    f = [t[:3] for t in _tr(_frase("Luis", "Pedro", "case")) + _tr(_frase("Pedro", "Juan", "case"))]
    got = compare([(a.upper(), b.upper(), c.upper()) for a, b, c in f])
    assert ("LUIS", "MAS_ALTO_QUE", "JUAN") in got and ("JUAN", "MAS_ALTO_QUE", "LUIS") not in got
