from src.reasoning.lessons import compare, inherit


def test_comparaciones_inversa_y_transitiva():
    f = [("LUIS", "MAS_ALTO_QUE", "PEDRO"), ("PEDRO", "MAS_ALTO_QUE", "JUAN")]
    got = compare(f)
    assert ("LUIS", "MAS_ALTO_QUE", "JUAN") in got
    assert ("JUAN", "MENOS_ALTO_QUE", "LUIS") in got
    assert ("JUAN", "MAS_ALTO_QUE", "LUIS") not in got


def test_extractor_causa_y_cuantificador():
    from src.language.extract import triples_full
    t = [("Ana", "PROPN", 2, "nsubj", "ana"), ("llora", "VERB", 0, "root", "llorar"), ("porque", "SCONJ", 5, "mark", "porque"),
         ("está", "AUX", 5, "cop", "estar"), ("triste", "ADJ", 2, "advcl", "triste"), (".", "PUNCT", 2, "punct", ".")]
    out = {(x["s"], x["p"]) for x in triples_full(t)}
    assert ("ana", "llorar") in out and ("ana", "llorar_porque") in out
    t = [("Algunos", "DET", 2, "det", "alguno"), ("pájaros", "NOUN", 3, "nsubj", "pajaro"), ("vuelan", "VERB", 0, "root", "volar"), (".", "PUNCT", 3, "punct", ".")]
    assert triples_full(t)[0]["q"] == "algunos"
    t = [("Ninguna", "DET", 2, "det", "ninguno"), ("rana", "NOUN", 4, "nsubj", "rana"), ("es", "AUX", 4, "cop", "ser"), ("mamífero", "NOUN", 0, "root", "mamifero"), (".", "PUNCT", 4, "punct", ".")]
    assert triples_full(t)[0]["neg"] is True
