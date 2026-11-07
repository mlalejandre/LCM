"""parche-109: reflexion (nexos entre conceptos), 'palabras similares a X', sentidos de circulo/esfera/linea, saltamontes invariable, cubiertos."""
import json
import os
import tempfile
import threading
import urllib.request

import pytest

from src.language import conceptos as C
from src.language import reflexion as R
from src.memory import cartuchos
from src.memory.store import MemoryStore


class _P:
    def parse(self, *a, **k):
        return []


def _mem(pares):
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    for s, p, o in pares:
        mem.add_fact((s, p, o), source="mundo")
        mem.display.setdefault(s.upper(), s)
        mem.display.setdefault(o.upper(), o)
    return mem, d


BASE = [("perro", "ES", "cánido"), ("lobo", "ES", "cánido"), ("zorro", "ES", "cánido"), ("gato", "ES", "felino"), ("león", "ES", "felino"), ("tigre", "ES", "felino"),
        ("martes", "ES", "día"), ("jueves", "ES", "día"), ("lunes", "ES", "día")]


def test_reflexion_encuentra_parecidos_con_motivo():
    mem, _ = _mem(BASE)
    r = R.reflexionar(mem)
    sp = [(h["s"], h["o"], h["por"]) for h in r["hechos"] if h["p"] == "SE_PARECE_A"]
    assert sp, r["informe"]
    assert any({a, b} <= {"PERRO", "LOBO", "ZORRO"} for a, b, _ in sp) and any({a, b} <= {"GATO", "LEÓN", "TIGRE"} for a, b, _ in sp)
    assert all(por for _, _, por in sp)
    assert not any({a, b} & {"PERRO", "GATO"} == {a, b} for a, b, _ in sp)         # perro y gato no son del mismo tipo concreto en esta memoria


def test_reflexion_es_determinista_y_no_repite():
    mem, _ = _mem(BASE)
    a, b = R.reflexionar(mem)["hechos"], R.reflexionar(mem)["hechos"]
    assert [(h["s"], h["p"], h["o"]) for h in a] == [(h["s"], h["p"], h["o"]) for h in b]
    assert len({(h["s"], h["p"], h["o"]) for h in a}) == len(a)


def test_cartucho_reflexion_monta_y_se_retira():
    mem, d = _mem(BASE)
    base = os.path.join(d, "c")
    r = R.reflexionar(mem)
    R.guardar(r, mem, base)
    assert "reflexion" in cartuchos.activos(base)
    mem2 = MemoryStore(os.path.join(d, "m2.json"))
    cartuchos.montar(mem2, base)
    assert any(h.get("cart") == "reflexion" and h.get("por") for h in mem2.nexos)
    assert not mem2.facts and not mem2.opposites                                  # los nexos NO se mezclan con los hechos que usa el razonamiento
    cartuchos.retirar("reflexion", base)
    cartuchos.montar(mem2, base)
    assert not mem2.nexos


def test_reflexion_ignora_su_propio_cartucho():
    mem, d = _mem(BASE)
    base = os.path.join(d, "c")
    r1 = R.reflexionar(mem)
    R.guardar(r1, mem, base)
    cartuchos.montar(mem, base)
    assert mem.nexos
    r2 = R.reflexionar(mem)
    assert [(h["s"], h["p"], h["o"]) for h in r1["hechos"]] == [(h["s"], h["p"], h["o"]) for h in r2["hechos"]]


def test_palabras_similares():
    mem, _ = _mem([])
    r = C.antes("Dime palabras similares a coche", mem)
    assert r and "Sinónimos" in r and "auto" in r.lower()
    assert C.antes("¿Qué se parece a un coche?", mem)


def test_sentidos_geometricos_y_cubiertos():
    for pal, exp in (("círculo", ("figura", "forma", "óvalo")), ("esfera", ("figura", "forma", "sólido")), ("línea", ("longitud", "extensión", "forma", "figura"))):
        c = C.conceptos(pal)[0]
        assert any(x in " ".join(C.cadena(c, 5)).lower() for x in exp), (pal, C.cadena(c, 5))
    assert "cubiertos" in C.describir("tenedor", None)


def test_saltamontes_no_es_plural():
    from src.language.dialogue import Conversation
    from src.language.qa import QA
    mem, _ = _mem([("saltamontes", "ES", "insecto")])
    conv = Conversation(mem, _P(), lambda m, p: QA(m, p.parse, lambda f: {}))
    r = conv.say("¿Qué es un saltamontes?")
    assert r.startswith("El saltamontes es un insecto"), r


@pytest.fixture()
def srv():
    from src.web.motor import Motor
    from src.web.servidor import crear_servidor
    mem, d = _mem(BASE)
    base = os.path.join(d, "c")
    os.makedirs(base)
    m = Motor(mem, _P(), base)
    s = crear_servidor(m, 0)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_address[1]}"
    s.shutdown()
    s.server_close()


def test_api_reflexion(srv):
    g = json.loads(urllib.request.urlopen(srv + "/api/reflexion").read())
    assert g["informe"] is None
    rq = urllib.request.Request(srv + "/api/reflexion", b"{}", {"Content-Type": "application/json", "X-LCM-Web": "1"})
    r = json.loads(urllib.request.urlopen(rq).read())
    assert r["ok"] and r["informe"]["nexos"] > 0
    g = json.loads(urllib.request.urlopen(srv + "/api/reflexion").read())
    assert g["activo"] and g["informe"]["nexos"] == r["informe"]["nexos"]
    k = json.loads(urllib.request.urlopen(srv + "/api/concepto?k=PERRO").read())
    assert any(f["origen"] == "reflexion" and f["por"] for f in k["nexos"])
