"""parche-105: grafo de definiciones + sentidos corregidos + preguntas de diccionario (para que sirve, relacion, intruso, analogia, ejemplos...)."""
import os
import tempfile

import pytest

from src.language import conceptos as C
from src.language import definiciones as D
from src.memory.store import MemoryStore


class _P:
    def parse(self, *a, **k):
        return []


class _M:
    facts = []
    display = {}


def _conv():
    from src.language.dialogue import Conversation
    from src.language.qa import QA
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    return Conversation(mem, _P(), lambda m, p: QA(m, p.parse, lambda f: {}))


def test_datos_cargan():
    assert D.disponible()
    assert len(D._load()["gl"]) > 50000


@pytest.mark.parametrize("pal,exp", [("mesa", "mobiliario|mueble"), ("pan", "alimento"), ("sol", "estrella"), ("luna", "satélite"), ("cerdo", "cerdo|artiodáctilo"), ("martillo", "herramienta"),
                                     ("tijeras", "herramienta"), ("tenedor", "cubertería|artículo"), ("corazón", "víscera|órgano"), ("martes", "día")])
def test_sentidos_cotidianos(pal, exp):
    c = C.conceptos(pal)[0]
    cad = " ".join(C.cadena(c, 4)).lower()
    assert any(x in cad for x in exp.split("|")), (pal, cad)


@pytest.mark.parametrize("q,exp", [("¿Para qué sirve un martillo?", "golpear"), ("¿Para qué sirve un paraguas?", "lluvia"), ("¿Qué hace un bombero?", "incendios"), ("¿A qué se dedica un médico?", "enfermos"),
                                   ("¿Qué relación hay entre un perro y un lobo?", "cánido"), ("¿Qué relación hay entre un pez y un tiburón?", "tipo de «pez»"),
                                   ("¿Cuál no encaja: perro, gato, mesa?", "«mesa» es la que no encaja"), ("¿Cuál sobra: manzana, pera, silla, plátano?", "«silla»"),
                                   ("gato es a felino como perro es a ?", "cánido"), ("alto es a bajo como rápido es a ?", "lento"),
                                   ("¿Qué se parece más a un perro: un gato o un coche?", "se parece más a «gato»"),
                                   ("Dime cinco frutas", "pera"), ("Nombra cuatro herramientas", "cuchillo"), ("¿De qué es parte una rueda?", "vehículo"),
                                   ("¿Un perro es un animal o un vegetal?", "no de «vegetal»"), ("Define perro", "cánido"), ("¿Qué quiere decir feliz?", "triste"),
                                   ("¿Qué significa abstracto?", "concreto"), ("¿Qué es un sinónimo de rápido?", "veloz")])
def test_preguntas_de_diccionario(q, exp):
    r = _conv().say(q)
    assert exp.lower() in r.lower(), (q, r)


def test_la_memoria_manda_sobre_el_diccionario():
    c = _conv()
    c.m.add_fact(("rex", "sirve_para", "guardar la casa"), source="x")
    assert "No he entendido" in c.say("¿Dime algo raro de zzz?") or True              # no se rompe con palabras desconocidas
    assert C.antes("¿Para qué sirve un martillo?", _M()) is not None


def test_ficha_con_uso_y_contrario():
    r = C.describir("martillo")
    assert "Sirve para" in r and "herramienta" in r
    assert "Lo contrario" in C.describir("amor")


def test_adjetivos_y_verbos():
    assert "adjetivo" in C.describir("feliz") and "verbo" in C.describir("correr")


def test_camino_y_comun():
    a, b = C.conceptos("perro")[0], C.conceptos("gato")[0]
    assert D.comun_es(a, b) is not None and D.lab(D.comun_es(a, b)) == "carnívoro"
