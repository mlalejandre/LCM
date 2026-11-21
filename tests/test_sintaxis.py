"""La capa de sintaxis. Si el analizador no está entrenado (no existe src/sintaxis/analizador.pt), el LCM funciona como siempre y estas pruebas se saltan."""
import os
import pytest

from src.sintaxis import integra
from src.sintaxis.datos import trocea, frases_de
from src.sintaxis.relaciones import limpia

ENTRENADO = os.path.exists(os.path.join(os.path.dirname(integra.__file__), "analizador.pt"))


def test_trocea_contracciones():
    assert trocea("Voy al parque del pueblo.") == ["Voy", "a", "el", "parque", "de", "el", "pueblo", "."]


def test_limpia_notas_de_pdf():
    t = limpia("El sistema solar1 es grande.\n2\nLa estrella concentra la masa,10 y brilla.")
    assert "solar1" not in t and "solar es grande" in t and ",10" not in t


def test_es_texto():
    assert integra.es_texto("Las abejas viven en colonias. La reina pone los huevos. Las obreras recogen el néctar de las flores.")
    assert not integra.es_texto("Mi tío vive en Navarra.")
    assert not integra.es_texto("¿Dónde vive mi tío?")


def test_sin_entrenar_no_molesta(monkeypatch):
    monkeypatch.setenv("LCM_SIN_SINTAXIS", "1")
    assert integra.activo() is False
    assert integra.responde(None, "¿qué es eso?", {"respuesta": "No lo sé."}) is None


@pytest.mark.skipif(not ENTRENADO, reason="analizador sin entrenar")
def test_relaciones_y_pregunta():
    from src.sintaxis.relaciones import Memoria
    M = Memoria().lee("Johannes Gutenberg inventó la imprenta en la ciudad de Maguncia hacia 1450. Los monjes copiaban los libros a mano.", limpiar=False)
    r = M.pregunta("¿Quién inventó la imprenta?")
    assert r and "gutenberg" in r["respuesta"].lower()
    assert M.pregunta("¿Quién inventó el telégrafo?") is None


@pytest.mark.skipif(not ENTRENADO, reason="analizador sin entrenar")
def test_pronombres_y_concordancia():
    from src.sintaxis.relaciones import Memoria
    M = Memoria().lee("Los bomberos llegaron al incendio en diez minutos. Ellos apagaron el fuego con agua. Una vecina los llamó desde su balcón.", limpiar=False)
    r = M.pregunta("¿Quiénes apagaron el fuego?")
    assert r and "bomberos" in r["respuesta"].lower()
    r = M.pregunta("¿Quién llamó a los bomberos?")
    assert r and "vecina" in r["respuesta"].lower()


def test_sinonimos_no_confunde_contrarios():
    from src.sintaxis.relaciones import sim_concepto
    assert sim_concepto("comprar", "vender") == 0.0
    assert sim_concepto("abrir", "cerrar") == 0.0
