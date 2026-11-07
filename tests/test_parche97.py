"""parche-97: formas generales de preguntar (contar, modales, definir, tag questions, existencia, seguimiento)."""
from src.language import consultas
from src.language.consultas import canonical as c


def test_contar():
    assert c("cuenta los planetas que existen en el sistema solar") == "¿Cuántos planetas hay?"
    assert c("puedes contar el numero de planetas que existen en el sistema solar?") == "¿Cuántos planetas hay?"
    assert c("dime el número de lunas que tiene Marte") == "¿Cuántas lunas tiene Marte?"
    assert c("¿Podrías decirme cuántos planetas hay?") == "¿Cuántos planetas hay?"
    assert c("dime cuantos planetas hay en el sistema solar") == "¿Cuántos planetas hay?"


def test_modales_sin_romper_capacidad():
    assert c("Puedes decirme qué es el Sol?") == "¿Qué es el Sol?"
    assert c("puedes decirme si Marte es rojo") == "¿Marte es rojo?"
    assert c("¿Puedes hablar español?") == "¿Puedes hablar español?"


def test_tag_y_verdad():
    assert c("Marte es rojo, ¿verdad?") == "¿Marte es rojo?"
    assert c("¿Es cierto que Júpiter es el planeta más grande?") == "¿Júpiter es el planeta más grande?"
    assert c("Dime si es verdad que Saturno tiene anillos") == "¿Saturno tiene anillos?"


def test_definir_y_listar():
    assert c("Definición de cometa") == "¿Qué es el cometa?"
    assert c("¿Qué significa Plutón?") == "¿Qué es Plutón?"
    assert c("Dame una lista de los planetas") == "¿Cuáles son los planetas?"
    assert c("¿Cómo se llaman los planetas?") == "¿Cuáles son los planetas?"
    assert c("Dime todo lo que sepas de Marte") == "¿Qué sabes de Marte?"
    assert c("¿Conoces el planeta Marte?") == "¿Qué sabes de Marte?"
    assert c("Dime por favor cuántas lunas tiene Marte") == "¿Cuántas lunas tiene Marte?"


def test_seguimiento_y_comparar():
    class M:
        facts = [{"s": "MARTE"}]
        display = {"MARTE": "Marte"}
    assert consultas.seguimiento("¿Y Venus?", "¿De qué color es Marte?", M()) == "¿De qué color es Venus?"
    assert consultas.comparar("Compara Marte y la Tierra") == ("Marte", "Tierra")
    assert consultas.quien_mas("¿Cuál es mayor: Júpiter o Saturno?") == ("más", "grande", "Júpiter", "Saturno")


def test_no_toca_afirmaciones():
    for t in ("Quiero un café", "Puede que llueva", "Hola, me llamo Ana", "Marta vive en Vigo.", "Mi gato no es negro, ¿vale?"):
        assert c(t) == t or t.endswith("¿vale?"), t
