from src.language.extract import surface, triples_full


def test_svo_and_negation():
    T = [("Luis", "PROPN", 3, "nsubj", "luis"), ("no", "ADV", 3, "advmod", "no"), ("come", "VERB", 0, "root", "comer"),
         ("carne", "NOUN", 3, "obj", "carne"), (".", "PUNCT", 3, "punct", ".")]
    (tr,) = triples_full(T, entities_only=True)
    assert (tr["s"], tr["p"], tr["o"], tr["neg"]) == ("luis", "comer", "carne", True)
    assert surface(T, tr)["template"] == "{s} come {o}"


def test_copular_with_preposition():
    T = [("Sara", "PROPN", 4, "nsubj", "sara"), ("es", "AUX", 4, "cop", "ser"), ("la", "DET", 4, "det", "el"),
         ("profesora", "NOUN", 0, "root", "profesora"), ("de", "ADP", 6, "case", "de"), ("Pablo", "PROPN", 4, "nmod", "pablo"),
         (".", "PUNCT", 4, "punct", ".")]
    (tr,) = triples_full(T, entities_only=True)
    assert tr["p"] == "profesora_de" and surface(T, tr)["o_disp"] == "Pablo"


def test_adjective_as_object():
    T = [("Hugo", "PROPN", 2, "nsubj", "hugo"), ("estudia", "VERB", 0, "root", "estudiar"),
         ("matemáticas", "ADJ", 2, "obj", "matematico"), (".", "PUNCT", 2, "punct", ".")]
    (tr,) = triples_full(T, entities_only=True)
    assert (tr["s"], tr["p"], tr["o"]) == ("hugo", "estudiar", "matematicas")


def _tr(T, **kw):
    return sorted((t["s"], t["p"], t["o"], t["neg"]) for t in triples_full(T, entities_only=True, **kw))


def test_coordinated_subjects():
    # Pedro y Marta viven en Madrid .
    T = [("Pedro", "PROPN", 4, "nsubj", "pedro"), ("y", "CCONJ", 3, "cc", "y"), ("Marta", "PROPN", 1, "conj", "marta"),
         ("viven", "VERB", 0, "root", "vivir"), ("en", "ADP", 6, "case", "en"), ("Madrid", "PROPN", 4, "obl", "madrid"),
         (".", "PUNCT", 4, "punct", ".")]
    assert _tr(T) == [("marta", "vivir_en", "madrid", False), ("pedro", "vivir_en", "madrid", False)]
    assert _tr(T, coordination=False) == [("pedro", "vivir_en", "madrid", False)]
    assert surface(T, triples_full(T, entities_only=True)[0]) == {}


def test_coordinated_objects_and_verbs():
    # Luis compro pan y leche y vende coches .
    T = [("Luis", "PROPN", 2, "nsubj", "luis"), ("compró", "VERB", 0, "root", "comprar"), ("pan", "NOUN", 2, "obj", "pan"),
         ("y", "CCONJ", 4, "cc", "y"), ("leche", "NOUN", 3, "conj", "leche"), ("y", "CCONJ", 7, "cc", "y"),
         ("vende", "VERB", 2, "conj", "vender"), ("coches", "NOUN", 7, "obj", "coche"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(T) == [("luis", "comprar", "leche", False), ("luis", "comprar", "pan", False), ("luis", "vender", "coches", False)]


def test_coordinated_oblique_shares_preposition():
    # Alba vive con su abuela y su tio .
    T = [("Alba", "PROPN", 2, "nsubj", "alba"), ("vive", "VERB", 0, "root", "vivir"), ("con", "ADP", 5, "case", "con"),
         ("su", "DET", 5, "det", "su"), ("abuela", "NOUN", 2, "obl", "abuela"), ("y", "CCONJ", 8, "cc", "y"),
         ("su", "DET", 8, "det", "su"), ("tío", "NOUN", 5, "conj", "tio"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(T) == [("alba", "vivir_con", "abuela", False), ("alba", "vivir_con", "tio", False)]


def test_capitalised_adjective_as_name():
    T = [("Clara", "ADJ", 2, "nsubj", "claro"), ("canta", "VERB", 0, "root", "cantar"), ("en", "ADP", 5, "case", "en"),
         ("el", "DET", 5, "det", "el"), ("coro", "NOUN", 2, "obl", "coro"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(T) == [("clara", "cantar_en", "coro", False)]
    T[0] = ("claro", "ADJ", 2, "nsubj", "claro")
    assert _tr(T) == []
