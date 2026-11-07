"""parche-93: superlativos, ordinales, adjetivos en plural y preguntas sobre textos."""
import os
import tempfile

from src.language.extract import triples_full
from src.language.qa import QA
from src.memory.store import MemoryStore


def _tree(forms, rows):
    return [(f, r[0], r[1], r[2], r[3]) for f, r in zip(forms, rows)]


def test_superlativo_y_ordinal_como_hechos_propios():
    t = _tree("Mercurio es el planeta más cercano a el Sol .".split(),
              [("PROPN", 4, "nsubj", "mercurio"), ("AUX", 4, "cop", "ser"), ("DET", 4, "det", "el"), ("NOUN", 0, "root", "planeta"), ("ADV", 6, "advmod", "mas"),
               ("ADJ", 4, "amod", "cercano"), ("ADP", 9, "case", "a"), ("DET", 9, "det", "el"), ("PROPN", 6, "nmod", "sol"), ("PUNCT", 4, "punct", ".")])
    got = {(x["s"], x["p"], x["o"]) for x in triples_full(t)}
    assert ("mercurio", "es", "planeta") in got and ("mercurio", "ser_el_mas_cercano", "planeta_al_sol") in got and ("mercurio", "ser", "cercano") not in got
    t2 = _tree("Venus es el segundo planeta .".split(),
               [("PROPN", 5, "nsubj", "venus"), ("AUX", 5, "cop", "ser"), ("DET", 5, "det", "el"), ("ADJ", 5, "amod", "segundo"), ("NOUN", 0, "root", "planeta"), ("PUNCT", 5, "punct", ".")])
    assert ("venus", "ser_el_segundo", "planeta") in {(x["s"], x["p"], x["o"]) for x in triples_full(t2)}


def test_adjetivo_plural_a_singular():
    t = _tree("Urano y Neptuno son planetas helados .".split(),
              [("PROPN", 5, "nsubj", "urano"), ("CCONJ", 3, "cc", "y"), ("PROPN", 1, "conj", "neptuno"), ("AUX", 5, "cop", "ser"), ("NOUN", 0, "root", "planeta"),
               ("ADJ", 5, "amod", "helado"), ("PUNCT", 5, "punct", ".")])
    got = {(x["s"], x["p"], x["o"]) for x in triples_full(t)}
    assert ("urano", "ser", "helado") in got and ("neptuno", "ser", "helado") in got


def _qa(facts):
    mem = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
    for f in facts:
        mem.add_fact(f)
    return QA(mem, lambda s: [], lambda fs: [])


def test_preguntas_de_texto():
    qa = _qa([("MERCURIO", "es", "planeta"), ("MERCURIO", "ser_el_mas_cercano", "planeta_al_sol"), ("TIERRA", "ser_el_tercero", "planeta"),
              ("URANO", "es", "planeta"), ("URANO", "ser", "helado"), ("NEPTUNO", "es", "planeta"), ("NEPTUNO", "ser", "helado"),
              ("COMETAS", "hecho_de", "hielo"), ("COMETAS", "hecho_de", "polvo")])
    assert "Mercurio" in qa.special("¿Cuál es el planeta más cercano al Sol?")
    assert "Tierra" in qa.special("¿Cuál es el tercer planeta?")
    assert "Tierra" in qa.special("¿Qué planeta es el tercero?")
    assert qa.special("¿Qué planetas son helados?").startswith("Urano y Neptuno son planetas helados")
    r = qa.special("¿De qué están hechos los cometas?")
    assert "hielo" in r and "polvo" in r
    assert qa.special("¿Cuál es el planeta más grande?") == "No lo sé."
    assert qa.special("¿Qué hora es?") is None


def test_concordancia_al_reutilizar_plantillas():
    assert QA._agree("{s} giran alrededor de {o}", "Urano") == "{s} gira alrededor de {o}"
    assert QA._agree("{s} es {o}", "Los asteroides") == "{s} son {o}"
    assert QA._agree("{s} vive en {o}", "Pedro") == "{s} vive en {o}"
    assert QA._agree("{s} viven en {o}", "Pedro y Marta") == "{s} viven en {o}"
