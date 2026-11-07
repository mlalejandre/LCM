"""parche-102: preguntas sin signos que empiezan por verbo; calificador sin respaldo."""
from src.language import consultas


def test_verbo_primero_sin_signos():
    assert consultas.canonical("es la tierra el tercer planeta") == "¿Es la tierra el tercer planeta?"
    assert consultas.canonical("tiene la tierra alguna luna") == "¿Tiene la tierra alguna luna?"
    assert consultas.canonical("Es un planeta.") == "Es un planeta."          # un hecho
    assert consultas.canonical("Tiene un perro") == "Tiene un perro"          # capitalizado: hecho
    assert consultas.canonical("hay un gato en la casa") == "hay un gato en la casa"
