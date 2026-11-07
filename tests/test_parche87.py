"""parche-87: enrutador de operaciones + habilidades exactas."""
from datetime import date

from src.language import intents, skills


def test_el_enrutador_entiende_las_frases_de_la_prueba():
    for text, op in (("Sabes que hora es?", "HORA"), ("Sabes donde estamos?", "UBICACION"),
                     ("Si hoy es dia 3 de febrero que día fue ayer?", "CALC_FECHA"), ("hola", "OTRO"), ("¿Quién compró pan?", "OTRO")):
        assert intents.route(text)[0] == op, text


def test_el_enrutador_no_se_dispara_con_una_palabra_suelta():
    for text in ("¿A qué hora llegó Pedro?", "Hoy es lunes.", "Pedro vive en Madrid.", "¿Dónde vive Marta?", "¿Cuándo compró Clara flores?"):
        assert intents.route(text)[0] == "OTRO", text


def test_calculo_de_fechas():
    hoy = date(2026, 11, 7)
    assert skills.calc_fecha("Si hoy es dia 3 de febrero que día fue ayer?", hoy) == "Si hoy es 3 de febrero, ayer fue 2 de febrero."
    assert "31 de diciembre" in skills.calc_fecha("Si hoy es 1 de enero, qué día fue ayer", hoy)
    assert "29 de febrero de 2024 (jueves)" in skills.calc_fecha("Si hoy es 28 de febrero de 2024 qué día será mañana", hoy)
    assert "no existe" in skills.calc_fecha("Si hoy es 31 de abril que dia fue ayer", hoy)
    assert skills.calc_fecha("Si hoy es 20 de abril qué día será dentro de 10 días", hoy).endswith("30 de abril.")
    assert skills.calc_fecha("¿Qué hora es?", hoy) is None
