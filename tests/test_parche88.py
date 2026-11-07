"""parche-88: aritmetica, dia de la semana, dias hasta, fuera de alcance."""
from datetime import date

from src.language import intents, skills


def test_operaciones_nuevas():
    for text, op in (("¿Cuánto es 12 por 7?", "ARITMETICA"), ("¿Qué día de la semana fue el 1 de enero de 2000?", "DIA_SEMANA"),
                     ("¿Cuántos días faltan para Navidad?", "DIAS_HASTA"), ("Ana abre la puerta.", "OTRO")):
        assert intents.route(text)[0] == op, text


def test_habilidades():
    hoy = date(2026, 11, 7)
    assert "84" in skills.aritmetica("¿Cuánto es 12 por 7?")
    assert "sábado" in skills.dia_semana("¿Qué día de la semana fue el 1 de enero de 2000?", hoy)
    assert "Faltan 48 días" in skills.dias_hasta("¿Cuántos días faltan para Navidad?", hoy)
