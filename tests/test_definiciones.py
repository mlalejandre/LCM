from src.reasoning.coherence import opposite
from src.reasoning.lessons import verb_derive


def test_contrarios_ensenados():
    assert not opposite("ruidoso", "silencioso")
    assert opposite("ruidoso", "silencioso", [["ruidoso", "silencioso"]])


def test_verbo_definido_se_hereda():
    out = verb_derive([("PEDRO", "COCINAR", "PASTA")], {"cocinar": "preparar"})
    assert ("PEDRO", "PREPARAR", "PASTA") in out
    out = verb_derive([("PEDRO", "COCINAR_QUE", "X")], {"cocinar": "preparar"})
    assert ("PEDRO", "PREPARAR_QUE", "X") in out
