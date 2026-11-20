# LCM_VISION_01_GENERATED
"""Pruebas unitarias de Vision 0.1, sin modelo de lenguaje ni descarga externa."""
import io

import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image

from src.vision.color_features import analizar_imagen
from src.vision.concept_alignment import (asegurar_conceptos_en_espacio,
    registrar_observacion, responder_pregunta_visual)


def png(color):
    b = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(b, format="PNG")
    return b.getvalue()


@pytest.mark.parametrize("rgb,esperado", [
    ((230, 35, 35), "ROJO"), ((22, 163, 74), "VERDE"),
    ((37, 99, 235), "AZUL"), ((250, 204, 21), "AMARILLO"),
    ((255, 255, 255), "BLANCO"), ((0, 0, 0), "NEGRO")])
def test_basicos(rgb, esperado):
    r = analizar_imagen(png(rgb))
    assert r["concepto"] == esperado
    assert r["fraccion"] == 1.0


@pytest.mark.parametrize("rgb,esperado", [
    ((249, 115, 22), "NARANJA"), ((244, 114, 182), "ROSA"), ((126, 34, 206), "MORADO"), ((120, 63, 4), "MARRON"), ((128, 128, 128), "GRIS")])
def test_colores_lcm23(rgb, esperado):
    assert analizar_imagen(png(rgb))["concepto"] == esperado


def test_fuera_de_catalogo_y_mezcla_abstienen():
    assert analizar_imagen(png((0, 200, 200)))["concepto"] is None          # turquesa: fuera del catálogo
    assert analizar_imagen(png((200, 200, 200)))["concepto"] is None        # gris muy claro: zona muerta entre gris y blanco
    im = Image.new("RGB", (32, 32), (255, 0, 0))
    for x in range(16, 32):
        for y in range(32):
            im.putpixel((x, y), (0, 150, 45))
    b = io.BytesIO(); im.save(b, "PNG")
    assert analizar_imagen(b.getvalue())["concepto"] is None


def test_formatos_invalidos():
    with pytest.raises(ValueError):
        analizar_imagen(b"esto no es una imagen")
    with pytest.raises(ValueError):
        analizar_imagen(b"x" * 8_000_001)


def test_memoria_y_consulta(tmp_path):
    from src.memory.store import MemoryStore
    mem = MemoryStore(str(tmp_path / "mem.json"))
    datos = png((22, 163, 74))
    id_, nuevo = registrar_observacion(mem, datos, "VERDE")
    assert nuevo and id_.startswith("IMAGEN_")
    assert not registrar_observacion(mem, datos, "VERDE")[1]
    assert responder_pregunta_visual(mem, "¿De qué color es la imagen?") is not None
    assert "verde" in responder_pregunta_visual(mem, "¿De qué color es la imagen?")
    assert responder_pregunta_visual(mem, "¿Qué es el verde?") is None
    assert sum(f["p"] == "TENER_COLOR" for f in mem.facts) == 1


def test_espacio_semantico_conserva_vector():
    torch = pytest.importorskip("torch")
    from src.ontology.concept_space import ConceptSpace
    sp = ConceptSpace()
    sp.register_concept("VERDE", features={"rasgo_existente": 1})
    sp.build_space()
    previo = sp.get_vector("VERDE")
    vectores = asegurar_conceptos_en_espacio(sp)
    assert torch.allclose(previo, sp.get_vector("VERDE"))
    assert vectores["AZUL"].shape == (128,)


def test_muestra_png_es_imagen_real():
    from src.vision.sample import muestra_png, datos_muestra, RGB
    im = Image.open(io.BytesIO(muestra_png("VERDE")))
    assert im.size == (400, 224)
    assert im.getpixel((100, 100)) == RGB["VERDE"]
    assert datos_muestra("VERDE")["url"] == "/api/vision/muestra?color=VERDE"
    with pytest.raises(ValueError): muestra_png("CELESTE")


def test_intenciones_de_chat_visual():
    from src.vision.concept_alignment import color_solicitado, es_pregunta_color_visual
    assert color_solicitado("¿Me puedes mostrar un ejemplo del color verde?") == "VERDE"
    assert color_solicitado("Muéstrame el rojo") == "ROJO"
    assert color_solicitado("¿Qué es el verde?") is None
    assert es_pregunta_color_visual("¿De qué color es la foto?")
    assert es_pregunta_color_visual("¿De qué color es?")
    assert not es_pregunta_color_visual("¿De qué color es la hierba?")
