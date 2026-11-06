from src.language.discourse import next_topic, parse_text, split_sentences
from src.language.extract import surface, triples_full


def test_split():
    assert split_sentences("Ana vive en Madrid. Trabaja en un banco.") == ["Ana vive en Madrid.", "Trabaja en un banco."]


def test_dropped_subject_takes_topic():
    # Trabaja en un banco .
    T = [("Trabaja", "VERB", 0, "root", "trabajar"), ("en", "ADP", 4, "case", "en"), ("un", "DET", 4, "det", "uno"),
         ("banco", "NOUN", 1, "obl", "banco"), (".", "PUNCT", 1, "punct", ".")]
    assert triples_full(T, entities_only=True) == []
    (t,) = triples_full(T, entities_only=True, default_subject="ana")
    assert (t["s"], t["p"], t["o"]) == ("ana", "trabajar_en", "banco") and surface(T, t) == {}


def test_pronoun_replaced_by_topic():
    # Ella toca la guitarra .
    T = [("Ella", "PROPN", 2, "nsubj", "ella"), ("toca", "VERB", 0, "root", "tocar"), ("la", "DET", 4, "det", "el"),
         ("guitarra", "NOUN", 2, "obj", "guitarra"), (".", "PUNCT", 2, "punct", ".")]
    assert triples_full(T, entities_only=True)[0]["s"] == "ella"
    assert triples_full(T, entities_only=True, default_subject="sara")[0]["s"] == "sara"


def test_subordinate_verb_without_subject_is_not_given_topic():
    T = [("Quiero", "VERB", 0, "root", "querer"), ("que", "SCONJ", 3, "mark", "que"), ("vengas", "VERB", 1, "ccomp", "venir"),
         (".", "PUNCT", 1, "punct", ".")]
    assert triples_full(T, entities_only=True, default_subject="ana") == []


class Stub:
    def parse(self, sent, topic=None):
        if sent.startswith("Ana"):
            return [{"s": "ana", "p": "vivir_en", "o": "madrid", "neg": False}]
        return [{"s": topic, "p": "trabajar_en", "o": "banco", "neg": False}]


def test_parse_text_carries_topic():
    out = parse_text(Stub(), "Ana vive en Madrid. Trabaja en un banco.")
    assert [t["s"] for t in out] == ["ana", "ana"]
    assert next_topic([{"s": "el"}], "ana") == "ana"


def test_pronoun_tagged_det_or_pron():
    for upos in ("DET", "PRON"):
        T = [("Él", upos, 2, "nsubj", "el"), ("lee", "VERB", 0, "root", "leer"), ("el", "DET", 4, "det", "el"),
             ("periódico", "NOUN", 2, "obj", "periodico"), (".", "PUNCT", 2, "punct", ".")]
        assert [t["s"] for t in triples_full(T, entities_only=True, default_subject="pedro")] == ["pedro"]
        assert triples_full(T, entities_only=True) == []


def test_target_tree_supports_irregular_verb_and_rejects_copular(monkeypatch):
    from src.language.school_learn import target_tree

    class M:  # modelo falso: predict_trees se sustituye
        pass
    import src.language.school_learn as sl
    monkeypatch.setattr(sl, "predict_trees", lambda model, forms, device, scripts: [[("PROPN", 0, "root", "x"), ("NOUN", 1, "flat", "x"), ("NOUN", 1, "flat", "x"), ("PUNCT", 1, "punct", ".")]])
    tree, why = target_tree(M(), "cpu", [], "Andrés cocina pasta.", ("ANDRES", "COCINAR", "PASTA"))
    assert tree is not None and tree[1][3] == "root" and tree[0][3] == "nsubj" and tree[2][3] == "obj"
    tree, why = target_tree(M(), "cpu", [], "Ana es madre de Luis.", ("ANA", "ES", "LUIS"))
    assert tree is None and "copulativas" in why
