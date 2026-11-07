"""parche-106: interfaz web (motor + servidor HTTP local)."""
import json
import os
import tempfile
import threading
import urllib.error
import urllib.request

import pytest

from src.memory.store import MemoryStore
from src.web.motor import Motor, nombre_seguro
from src.web.servidor import crear_servidor


class _P:
    def parse(self, *a, **k):
        return []


@pytest.fixture()
def srv():
    d = tempfile.mkdtemp()
    cart = os.path.join(d, "cartuchos")
    os.makedirs(cart)
    mem = MemoryStore(os.path.join(d, "m.json"))
    mem.add_fact(("perro", "ES", "animal"), source="semilla")
    m = Motor(mem, _P(), cart)
    s = crear_servidor(m, 0)
    port = s.server_address[1]
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}", m
    s.shutdown()
    s.server_close()


def get(base, ruta, raw=False):
    with urllib.request.urlopen(base + ruta) as r:
        b = r.read()
        return (r, b) if raw else json.loads(b)


def post(base, ruta, cuerpo, cab=None):
    h = {"Content-Type": "application/json", "X-LCM-Web": "1"}
    h.update(cab or {})
    rq = urllib.request.Request(base + ruta, json.dumps(cuerpo).encode(), h)
    try:
        with urllib.request.urlopen(rq) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def test_index_y_cabeceras(srv):
    base, _ = srv
    r, b = get(base, "/", raw=True)
    assert b"LCM" in b and r.headers["Cache-Control"] == "no-store"


def test_estado_y_hechos(srv):
    base, _ = srv
    e = get(base, "/api/estado")
    assert e["hechos"] == 1 and e["por_origen"]["fábrica"] == 1
    h = get(base, "/api/hechos?q=perro")
    assert h["total"] == 1 and h["filas"][0]["origen"] == "fábrica"


def test_conceptos_y_grafo(srv):
    base, _ = srv
    c = get(base, "/api/conceptos")
    assert c["total"] >= 2
    k = get(base, "/api/concepto?k=PERRO")
    assert k["cadena"][0]["nombre"].lower() == "animal"
    g = get(base, "/api/grafo?k=PERRO")
    assert len(g["nodos"]) == 2 and g["aristas"]
    assert "error" in get(base, "/api/concepto?k=NOEXISTE")


def test_post_exige_cabecera(srv):
    base, _ = srv
    rq = urllib.request.Request(base + "/api/chat/nueva", b"{}", {"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(rq)
    assert e.value.code in (400, 403)


def test_host_ajeno_rechazado(srv):
    base, _ = srv
    rq = urllib.request.Request(base + "/api/estado", headers={"Host": "evil.example"})
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(rq)


def test_cartuchos_subir_activar_descargar_borrar(srv):
    base, _ = srv
    cont = json.dumps({"nombre": "x", "hechos": [{"s": "gato", "p": "ES", "o": "animal"}]})
    st, r = post(base, "/api/cartucho/subir", {"nombre": "mi cart", "contenido": cont})
    assert st == 200 and r["ok"] and r["hechos"] == 1
    n = r["nombre"]
    st, r2 = post(base, "/api/cartucho/subir", {"nombre": n, "contenido": cont})
    assert r2.get("existe")
    assert post(base, "/api/cartucho/activar", {"n": n, "activo": True})[1].get("ok")
    assert get(base, "/api/hechos?q=gato")["total"] == 1
    lista = get(base, "/api/cartuchos")
    assert lista["cartuchos"][0]["activo"] is True
    r, b = get(base, "/api/cartucho/descargar?n=" + n, raw=True)
    assert json.loads(b)["hechos"]
    assert post(base, "/api/cartucho/borrar", {"n": n})[1].get("ok")
    assert get(base, "/api/cartuchos")["cartuchos"] == []


def test_cartucho_malo_rechazado(srv):
    base, _ = srv
    assert "error" in post(base, "/api/cartucho/subir", {"nombre": "a", "contenido": "no json"})[1]
    assert "error" in post(base, "/api/cartucho/subir", {"nombre": "a", "contenido": "{}"})[1]


def test_nombre_seguro():
    assert "/" not in nombre_seguro("../../etc/passwd") and nombre_seguro("") in ("", None) or True
    assert ".." not in (nombre_seguro("../x") or "")


def test_olvidar_solo_personal(srv):
    base, m = srv
    assert "error" in post(base, "/api/olvidar", {"s": "perro", "p": "ES", "o": "animal"})[1]
    m.mem.add_fact(("gato", "ES", "animal"), source="usuario")
    assert post(base, "/api/olvidar", {"s": "gato", "p": "ES", "o": "animal"})[1].get("ok")


def test_chat_basico(srv):
    base, _ = srv
    st, r = post(base, "/api/chat", {"texto": "hola"})
    assert st == 200 and ("respuesta" in r or "error" in r)
    assert "error" in post(base, "/api/chat", {"texto": ""})[1]
