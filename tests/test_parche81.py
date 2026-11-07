"""parche-81: clases en singular, rewrite de "a quien" con complemento y "donde" con sujeto coordinado."""
from src.language.extract import triples_full
from src.language.qa import rewrite


def test_clase_plural_se_guarda_en_singular():
    R = [("Todos", "DET", 3, "det", "todo"), ("los", "DET", 3, "det", "el"), ("gatos", "NOUN", 5, "nsubj", "gato"), ("son", "AUX", 5, "cop", "ser"),
         ("animales", "NOUN", 0, "root", "animal"), (".", "PUNCT", 5, "punct", ".")]
    assert [(t["s"], t["p"], t["o"]) for t in triples_full(R, entities_only=True)] == [("gato", "es", "animal")]
    S = [("Félix", "PROPN", 4, "nsubj", "felix"), ("es", "AUX", 4, "cop", "ser"), ("un", "DET", 4, "det", "uno"), ("gato", "NOUN", 0, "root", "gato"), (".", "PUNCT", 4, "punct", ".")]
    assert [(t["s"], t["p"], t["o"]) for t in triples_full(S, entities_only=True)] == [("felix", "es", "gato")]


def test_rewrite_a_quien_con_complemento():
    assert rewrite("¿A quién regaló Rubén un libro?")[0][0] == "Rubén regaló un libro a Xqx."
    assert rewrite("¿A quién llamó Pedro?")[0][0] == "Pedro llamó a Xqx."


def test_rewrite_donde_con_sujeto_coordinado():
    assert rewrite("¿Dónde tienen una casa Andrea y Bruno?")[0][0] == "Andrea y Bruno tienen una casa en Xqx."
    assert rewrite("¿Dónde estudia Luis música?")[0][0] == "Luis estudia música en Xqx."
