"""LCM 2.2 · base de conceptos de fábrica: capas de abstracción, excepciones, partes, contrarios y efectos (sin Escuela)."""
from src.nucleo20 import conceptos as K


def test_base_carga():
    k = K.kb()
    assert len(k["isa"]) > 500 and len(k["props"]) > 150 and len(k["ant"]) > 100 and k["efectos"]["romper"] == "roto"


def test_capas_de_abstraccion():
    assert K.ancestros("gorrion") == ["pajaro", "ave", "animal", "ser vivo"]
    assert "mueble" in K.ancestros("silla") and "objeto" in K.ancestros("silla")
    assert "animal" not in K.ancestros("rosa") and "planta" in K.ancestros("rosa")


def test_la_excepcion_cercana_manda():
    assert K._estado("gorrion", "volar", "")[1] is False          # hereda de ave: vuela
    assert K._estado("pinguino", "volar", "")[1] is True          # excepción: no vuela
    assert K._estado("perro", "volar", "")[1] is True             # mamífero: no vuela
    assert K._estado("murcielago", "volar", "")[1] is False       # excepción de la excepción
    assert K._estado("silla", "volar", "") is None                # de lo que no hay dato, no se afirma nada


def test_cantidades_y_partes():
    assert K._estado("bicicleta", "tener", "dos ruedas")[1] is False
    assert K._estado("coche", "tener", "dos ruedas") is None      # tiene cuatro: «dos» no casa
    assert "rueda" in K.kb()["partes"]["coche"] and K.kb()["parte_disp"][("coche", "rueda")] == "ruedas"


def test_formas():
    assert K.un("ave") == "un ave" and K.los("pez") == "los peces" and K.suj("hierba") == "la hierba"
    assert K._frase_prop("gato", False, "maullar", "") == "los gatos maúllan"
    assert K._frase_prop("hierba", False, "ser", "verde") == "la hierba es verde"
