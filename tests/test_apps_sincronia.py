"""LCM 2.13 · sincronía entre el LCM y sus aplicaciones deterministas (src/apps)."""
import re
import unicodedata
from fractions import Fraction

import pytest

from src.apps import registro as R
from src.apps import manifiesto as MF
from src.apps.registro import App, ErrorApp
from src.nucleo20 import calculo as CA
from src.nucleo20 import conceptos as K
from src.nucleo20.numerales import a_cifras
from src.nucleo20.morfo import sa


def _sa(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def test_manifiesto_al_dia():
    """Si cambia una aplicación (léxico, versión, ejemplos), hay que regenerar el manifiesto: python -m src.apps.manifiesto"""
    assert MF.leido()["huella"] == R.manifiesto()["huella"]


@pytest.mark.parametrize("nombre", sorted(R.REGISTRO))
def test_cada_app_esta_completa(nombre):
    a = R.REGISTRO[nombre]
    assert a.lexico, f"{nombre}: sin léxico, el LCM no podría pedírsela"
    assert a.ejemplos, f"{nombre}: sin ejemplos que comprobar"
    assert a.version and a.nombre_humano
    assert K._kb_clase(_sa(a.concepto)), f"{nombre}: su concepto «{a.concepto}» no está en la base de fábrica"


def test_el_lexico_del_lcm_sale_del_registro():
    L = CA.lexico()
    assert L["huella"] == R.manifiesto()["huella"]
    ops = {(w, n) for w, n in L["ops"]}
    for a in R.de_familia("aritmetica"):
        for o in a.lexico.get("operador", []):
            assert (tuple(CA._toks(o)), a.nombre) in ops
        for v in a.lexico.get("verbo", []):
            assert L["verbos"].get(sa(v.lower())) == a.nombre


@pytest.fixture(scope="module")
def motor():
    from lab.banco import motor as m
    mo = m()
    yield mo


@pytest.mark.parametrize("nombre,frase,esperado", [(a.nombre, f, e) for a in R.REGISTRO.values() for f, e in a.ejemplos])
def test_ejemplos_por_el_lcm(motor, nombre, frase, esperado):
    out = motor.chat(frase)
    assert _sa(esperado) in _sa(out["respuesta"]), (frase, out["respuesta"])


def test_el_lcm_no_calcula_de_memoria(motor, monkeypatch):
    """Si la aplicación de suma diera otro resultado, el LCM diría ese: la cuenta no está en el modelo."""
    a = R.REGISTRO["suma"]
    monkeypatch.setattr(a, "funcion", lambda *xs: Fraction(999))
    assert "999" in motor.chat("¿cuánto es 2 más 5?")["respuesta"]


def test_app_nueva_se_entiende_sin_tocar_el_lcm():
    """Escalar al unísono: registrar una aplicación con su léxico basta para que el LCM la entienda."""
    app = App("modulo", "aritmetica", lambda a, b: Fraction(int(a) % int(b)), (2, 2), "mod", 2, nombre_humano="el resto",
              lexico={"operador": ["módulo", "modulo", "mod"]}, ejemplos=[("¿cuánto es 17 módulo 5?", "2")])
    R.registra(app)
    try:
        nodo = CA.calculo_directo("¿cuánto es 17 módulo 5?")
        assert nodo is not None and CA.ejecuta(nodo, []) == 2
    finally:
        del R.REGISTRO["modulo"]
    assert CA.calculo_directo("¿cuánto es 17 módulo 5?") is None


def test_errores_de_dominio():
    with pytest.raises(ErrorApp):
        R.ejecuta("division", 1, 0)
    with pytest.raises(ErrorApp):
        R.ejecuta("raiz", -4)


def test_determinista():
    assert [R.ejecuta("division", 10, 4)[0] for _ in range(3)] == [Fraction(5, 2)] * 3
    assert R.ejecuta("dibujo", [("círculo", "ROJO", 2)])[0]["svg"] == R.ejecuta("dibujo", [("círculo", "ROJO", 2)])[0]["svg"]


@pytest.mark.parametrize("texto,cifras", [("doscientos treinta más ciento veinte", "230 más 120"), ("mil menos uno", "1000 menos 1"),
                                          ("dos mil quinientos", "2500"), ("treinta y cinco", "35"), ("un perro", "un perro"),
                                          ("tres coma cinco", "3,5"), ("sesenta y veinte", "60 y 20"),
                                          ("(cuatrocientos dos más uno)", "(402 más 1)"), ("quince%", "15 %")])
def test_numerales(texto, cifras):
    assert a_cifras(texto) == cifras


@pytest.mark.parametrize("frase", ["tengo 3 hermanos y 2 hermanas", "nací en 1990", "mi hermano tiene 12 años y yo 9", "vivo en el número 5",
                                   "haz la cama", "voy a casa de mi abuela entre semana"])
def test_no_todo_es_una_cuenta(frase):
    assert CA.calculo_directo(frase) is None and CA.problema(frase) is None
