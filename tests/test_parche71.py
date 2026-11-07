"""parche-71: convencion de la "a" personal en el examen y lema de morder."""
from scripts.eval_frases import key
from src.language.irregulares import IRREG


def test_a_personal_no_distingue_la_relacion():
    assert key("conocer_a") == key("conocer")
    assert key("amar_a") == key("amar") and key("ayudar_a") == key("ayudar")
    assert key("llegar_a") != key("llegar") and key("ir_a") != key("ir") and key("dar_a") != key("dar")
    assert key("vivir_en") != key("vivir") and key("hablar_con") != key("hablar")


def test_lema_de_morder():
    assert IRREG["muerde"] == "morder" and IRREG["muerden"] == "morder"
