from datetime import date

from src.language.fechas import resolve, fmt, extract_abs, before, after

HOY = date(2026, 11, 6)      # viernes


def test_relativos():
    assert fmt(resolve("ayer", HOY)) == "5 de noviembre de 2026"
    assert fmt(resolve("anteayer", HOY)) == "4 de noviembre de 2026"
    assert fmt(resolve("lunes", HOY)) == "2 de noviembre de 2026"
    assert fmt(resolve("ano_pasado", HOY)) == "2025"
    assert fmt(resolve("diciembre", HOY)) == "diciembre de 2025"


def test_fecha_escrita_y_orden():
    clean, iv, disp = extract_abs("Ana llegó el 3 de diciembre de 2024.", HOY)
    assert clean == "Ana llegó." and fmt(iv) == "3 de diciembre de 2024"
    assert before(resolve("lunes", HOY), resolve("ayer", HOY))
    assert after(resolve("ayer", HOY), resolve("lunes", HOY))
    assert resolve("pronto", HOY) is None
