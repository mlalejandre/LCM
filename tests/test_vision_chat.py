# LCM_VISION_01_GENERATED
"""Integración chat: archivo + pregunta, muestra PNG y persistencia sin bytes."""
import base64
import io
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from PIL import Image
from src.memory.store import MemoryStore
from src.web.motor import Motor
from src.web.servidor import crear_servidor


class Parser:
    def parse(self, *a, **k):
        return []


def png(rgb):
    b = io.BytesIO()
    Image.new("RGB", (32, 32), rgb).save(b, "PNG")
    return b.getvalue()


@pytest.fixture
def entorno(tmp_path):
    mem = MemoryStore(str(tmp_path / "memoria.json"))
    motor = Motor(mem, Parser(), str(tmp_path / "cartuchos"))
    server = crear_servidor(motor, 0)
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    yield "http://127.0.0.1:" + str(server.server_address[1]), motor
    server.shutdown()
    server.server_close()
    hilo.join(timeout=5)


def post(base, url, body):
    datos = json.dumps(body).encode()
    request = urllib.request.Request(base + url, datos, {"Content-Type": "application/json", "X-LCM-Web": "1"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_adjunto_y_pregunta_mismo_turno(entorno):
    base, motor = entorno
    st, r = post(base, "/api/chat", {"texto": "¿De qué color es esta imagen?", "nombre": "foto.png",
                                      "imagen_base64": base64.b64encode(png((22, 163, 74))).decode()})
    assert st == 200 and "verde" in r["respuesta"].lower()
    assert r["aprendido"]
    assert motor.mem.facts[-1]["o"] == "VERDE"
    assert "verde" in post(base, "/api/chat", {"texto": "¿De qué color es?"})[1]["respuesta"].lower()
    # No se guardan los bytes de la imagen original en memoria.
    memoria = Path(motor.mem.path).read_text()
    assert "imagen_base64" not in memoria


def test_adjunto_solo_y_repeticion(entorno):
    base, motor = entorno
    datos = {"texto": "", "nombre": "verde.png", "imagen_base64":base64.b64encode(png((22,163,74))).decode()}
    assert "verde" in post(base, "/api/chat", datos)[1]["respuesta"].lower()
    assert "verde" in post(base, "/api/chat", datos)[1]["respuesta"].lower()
    assert len([x for x in motor.mem.facts if x["p"] == "TENER_COLOR"]) == 1


def test_ultimo_adjunto_prevalece_sobre_orden_memoria(entorno):
    base, _ = entorno
    for rgb in ((22,163,74),(220,38,38),(22,163,74)):
        post(base, "/api/chat", {"texto":"", "imagen_base64":base64.b64encode(png(rgb)).decode()})
    assert "verde" in post(base, "/api/chat", {"texto": "¿Qué color tiene esta foto?"})[1]["respuesta"].lower()


def test_muestra_de_color_integrada_y_png(entorno):
    base, _ = entorno
    st, r = post(base, "/api/chat", {"texto": "Muéstrame un ejemplo del color verde"})
    assert st == 200 and r["imagen"]["color"] == "VERDE"
    with urllib.request.urlopen(base + r["imagen"]["url"]) as response:
        assert response.headers.get_content_type() == "image/png"
        imagen = Image.open(io.BytesIO(response.read()))
    assert imagen.getpixel((80,90)) == (22,163,74)
    assert post(base, "/api/chat", {"texto": "¿Qué es el verde?"})[1].get("imagen") is None


def test_error_y_abstencion(entorno):
    base, _ = entorno
    assert post(base, "/api/chat", {"texto": "", "imagen_base64": "ZZ@@"})[0] == 400
    # LCM 2.3: el gris ya es un color del catálogo; la abstención se prueba con un tono que sigue fuera (turquesa)
    st, r = post(base, "/api/chat", {"texto": "¿De qué color es?", "imagen_base64": base64.b64encode(png((0,200,200))).decode()})
    assert st == 200 and r["fallo"] is True and "verde" not in r["respuesta"].lower()
    assert post(base, "/api/chat", {"texto": "¿De qué color es?"})[1]["fallo"] is True
    rq = urllib.request.Request(base+"/api/vision/muestra?color=INVENTADO")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(rq)
    assert e.value.code == 400


def test_html_tiene_compositor_visual():
    html = (Path(__file__).resolve().parents[1] / "src/web/static/index.html").read_text()
    assert 'id="vision-adjuntar"' in html
    assert 'id="vision-file"' in html
    assert 'visionZona.addEventListener("drop"' in html
    assert 'm.imagen &&' in html
    assert 'id="env"' in html
    assert '<a href="/vision"' not in html
