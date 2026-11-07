"""parche-77: nombre+verbo leido como NOUN, estado con participio, comparativo con segundo sujeto, dos raices, coherencia con la "a" personal."""
from src.language.extract import triples_full
from src.language.school_parser import SchoolParser
from src.reasoning.coherence import classify

S = SchoolParser


def _tr(rows):
    return [(t["s"], t["p"], t["o"], t["neg"]) for t in triples_full(rows, entities_only=True)]


def test_nombre_adjetivo_y_verbo_como_sustantivo():
    C = [("Clara", "ADJ", 2, "amod", "claro"), ("compra", "NOUN", 0, "root", "compra"), ("pan", "NOUN", 2, "obj", "pan"), (".", "PUNCT", 2, "punct", ".")]
    got = S._fix_name_adj(C)
    assert got[0][1:4] == ("PROPN", 2, "nsubj") and got[1][1] == "VERB"
    D = [("Clara", "ADJ", 2, "amod", "claro"), ("casa", "NOUN", 0, "root", "casa"), (".", "PUNCT", 2, "punct", ".")]
    assert S._fix_name_adj(D) == D                                          # sin objeto no se toca


def test_estar_mas_participio_es_un_estado():
    A = [("Ana", "PROPN", 3, "nsubj", "ana"), ("está", "AUX", 3, "cop", "estar"), ("cansada", "VERB", 0, "root", "cansar"), (".", "PUNCT", 3, "punct", ".")]
    assert _tr(S._fix_participle_state(A)) == [("ana", "estar", "cansada", False)]
    P = [("La", "DET", 2, "det", "el"), ("puerta", "NOUN", 4, "nsubj", "puerta"), ("es", "AUX", 4, "cop", "ser"), ("abierta", "VERB", 0, "root", "abrir"), (".", "PUNCT", 4, "punct", ".")]
    assert S._fix_participle_state(P)[3][1] == "VERB"                       # con "ser" seria una pasiva


def test_comparativo_con_segundo_sujeto():
    R = [("Sara", "PROPN", 4, "nsubj", "sara"), ("es", "AUX", 4, "cop", "ser"), ("más", "ADV", 4, "advmod", "mas"), ("baja", "ADJ", 0, "root", "bajo"),
         ("que", "SCONJ", 6, "mark", "que"), ("Rosa", "PROPN", 4, "nsubj", "rosa"), (".", "PUNCT", 4, "punct", ".")]
    assert _tr(S._fix_comparative(R)) == [("sara", "mas_bajo_que", "rosa", False)]
    N = [("Sara", "PROPN", 3, "nsubj", "sara"), ("y", "CCONJ", 4, "cc", "y"), ("Rosa", "PROPN", 3, "conj", "rosa"), ("viven", "VERB", 0, "root", "vivir")]
    assert S._fix_comparative(N) == N


def test_dos_raices_nombre_y_verbo():
    C = [("Carlos", "PROPN", 0, "root", "carlos"), ("nada", "PRON", 0, "root", "nada"), ("en", "ADP", 5, "case", "en"), ("la", "DET", 5, "det", "el"),
         ("piscina", "NOUN", 2, "obl", "piscina"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(S._fix_subject_verb_appos(C)) == [("carlos", "nadar_en", "piscina", False)]


def test_coherencia_ignora_la_a_personal():
    facts = [{"s": "LUIS", "p": "AMAR_A", "o": "ANA", "neg": False}]
    assert classify(facts, ("luis", "amar", "ana"), True)[0] == "negation"
    assert classify([{"s": "RAUL", "p": "LLEGAR_A", "o": "SEVILLA", "neg": False}], ("raul", "llegar", "sevilla"), True)[0] == ""
