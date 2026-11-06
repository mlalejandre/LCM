from src.reasoning.efectos import effects
from src.reasoning.lessons import apply_lessons


def test_dar_y_vender():
    ops = effects([("ANA", "dar", "libro", "un libro"), ("ANA", "dar_a", "LUIS", "Luis")])
    assert ("lose", ("ANA", "tener", "libro")) in ops and ("add", ("LUIS", "tener", "libro")) in ops
    ops = effects([("LUIS", "comprar", "bicicleta", "una bicicleta")])
    assert ops == [("add", ("LUIS", "tener", "bicicleta"))]


def test_estados_con_genero():
    assert effects([("ANA", "abrir", "puerta", "la puerta")]) == [("add", ("puerta", "estar", "abierta"))]
    assert effects([("ANA", "romper", "vaso", "el vaso")]) == [("add", ("vaso", "estar", "roto"))]
    assert effects([("ANA", "ir_a", "MADRID", "Madrid")]) == [("add", ("ANA", "estar_en", "MADRID"))]


def test_parentesco_de_fabrica():
    got = apply_lessons([("PEDRO", "PADRE_DE", "ANA"), ("ANA", "MADRE_DE", "LUIS")], [])
    assert ("PEDRO", "ABUELO_DE", "LUIS") in got and ("LUIS", "NIETO_DE", "PEDRO") in got and ("LUIS", "HIJO_DE", "ANA") in got
    got = apply_lessons([("MARTA", "HERMANA_DE", "ROSA"), ("ROSA", "MADRE_DE", "PACO")], [])
    assert ("MARTA", "TIA_DE", "PACO") in got
    got = apply_lessons([("RUEDA", "PARTE_DE", "COCHE"), ("COCHE", "PARTE_DE", "FLOTA")], [])
    assert ("RUEDA", "PARTE_DE", "FLOTA") in got
