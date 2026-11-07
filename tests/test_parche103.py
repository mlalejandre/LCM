"""parche-103: think usa la capa de preguntas; ordenes; dias relativos; contar; aritmetica con palabras."""
from src.language import consultas


def test_ordenes_no_son_hechos_y_caracteristicas():
    assert consultas.es_orden("Cuenta los planetas que existen en el sistema solar.")
    assert not consultas.es_orden("Llama es un animal.") and not consultas.es_orden("Pedro cuenta cuentos.")
    assert consultas.canonical("Dime caracteríricas de la Tierra") == "¿Qué sabes de la Tierra?"
    assert consultas.canonical("puedes contar hasta 10?") == "¿Cuenta hasta 10?"


def test_cuantos_en_sistema_solar_y_unidades():
    assert consultas.canonical("cuántos planetas tiene el sistema solar?") == "¿Cuántos planetas hay?"
    assert consultas.canonical("en el sistema solar cuantos planetas hay?") == "¿Cuántos planetas hay?"
    assert consultas.canonical("cuántas lunas tiene Marte?") != "¿Cuántas lunas hay?"
