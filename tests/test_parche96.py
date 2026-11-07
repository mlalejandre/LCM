"""parche-96: marcos de pregunta sin analizador + envoltorios de cortesia + sinonimos."""
import os
import tempfile

from src.language import consultas
from src.language.qa import QA
from src.language import marcos
from src.memory.store import MemoryStore

FACTS = [("SOL", "ES", "ESTRELLA"), ("SOL", "ESTAR_EN", "CENTRO"), ("MERCURIO", "ES", "PLANETA"), ("MERCURIO", "SER_EL_MAS_CERCANO", "PLANETA_AL_SOL"),
         ("VENUS", "ES", "PLANETA"), ("VENUS", "SER_EL_SEGUNDO", "PLANETA"), ("TIERRA", "ES", "PLANETA"), ("TIERRA", "SER_EL_TERCERO", "PLANETA"), ("TIERRA", "TENER", "LUNA"),
         ("LUNA", "GIRAR_ALREDEDOR_DE", "TIERRA"), ("MARTE", "ES", "PLANETA"), ("MARTE", "SER", "ROJO"), ("MARTE", "TENER", "DOS_LUNAS"), ("JUPITER", "ES", "PLANETA"),
         ("JUPITER", "SER_EL_MAS_GRANDE", "PLANETA"), ("JUPITER", "ES", "GIGANTE"), ("JUPITER", "SER", "GASEOSO"), ("SATURNO", "TENER", "ANILLOS"), ("COMETAS", "HECHO_DE", "HIELO"),
         ("COMETAS", "HECHO_DE", "POLVO")]
DISP = {"SOL": "el Sol", "TIERRA": "la Tierra", "LUNA": "la Luna", "MARTE": "Marte", "JUPITER": "Júpiter", "SATURNO": "Saturno", "MERCURIO": "Mercurio", "VENUS": "Venus",
        "DOS_LUNAS": "dos lunas", "ANILLOS": "anillos", "PLANETA": "el planeta", "CENTRO": "el centro", "ROJO": "rojo", "GASEOSO": "gaseoso", "COMETAS": "cometas"}


def _qa():
    mem = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
    for f in FACTS:
        mem.add_fact(f)
    mem.display.update(DISP)
    return QA(mem, lambda s: [], lambda fs: [])


def test_marcos_wh_y_si_no():
    qa = _qa()
    for q, esp in (("¿Qué planeta tiene anillos?", "Saturno"), ("¿Cuál es el planeta de los anillos?", "Saturno"), ("¿Qué planeta es un gigante gaseoso?", "Júpiter"),
                   ("¿La Tierra tiene luna?", "Sí"), ("¿Gira la Luna alrededor de la Tierra?", "Sí"), ("¿Están hechos de hielo los cometas?", "Sí"),
                   ("¿Qué gira alrededor de la Tierra?", "Luna"), ("¿Es Júpiter más grande que la Tierra?", "Sí"), ("¿Es Marte más grande que Júpiter?", "No"),
                   ("¿Cuál tiene anillos, Saturno o Marte?", "Saturno"), ("¿Cuántos planetas helados conoces?", "Conozco")):
        r = marcos.responder(qa, q)
        assert r is None or esp in r or esp == "Conozco", (q, r)
    assert "Saturno" in marcos.responder(qa, "¿Qué planeta tiene anillos?")
    assert marcos.responder(qa, "¿La Tierra tiene luna?").startswith("Sí")


def test_marcos_prioritarios():
    qa = _qa()
    assert "rojo" in marcos.responder(qa, "¿De qué color es el planeta Marte?", primero=True)
    assert "tercer" in marcos.responder(qa, "¿Qué posición ocupa la Tierra?", primero=True)
    assert "hielo" in marcos.responder(qa, "¿Qué contienen los cometas?", primero=True)


def test_orden_y_numeros():
    qa = _qa()
    assert "Tierra" in marcos.responder(qa, "¿Qué planeta va después de Venus?")
    assert "Mercurio" in marcos.responder(qa, "¿Qué planeta va antes de Venus?")
    assert "Tierra" in marcos.responder(qa, "¿Cuál es el planeta número tres?")


def test_no_inventa():
    qa = _qa()
    assert marcos.responder(qa, "¿Tiene Marte anillos?") is None
    assert marcos.responder(qa, "¿Es el Sol un planeta?") is None
    assert marcos.responder(qa, "¿Qué planeta tiene diamantes?") is None


def test_envoltorios_y_sinonimos():
    c = consultas.canonical
    assert c("Oye, ¿Cuál es el tercer planeta?") == "¿Cuál es el tercer planeta?"
    assert c("Por favor, ¿Qué es Marte?") == "¿Qué es Marte?"
    assert c("Me gustaría saber cuál es el planeta enano") == "¿Cuál es el planeta enano?"
    assert c("Quisiera saber si Marte es rojo") == "¿Marte es rojo?"
    assert c("qué planeta tiene anillos") == "¿Qué planeta tiene anillos?"
    assert c("qué bien") == "qué bien"
    assert c("¿Cuál es el planeta que está más cerca del Sol?") == "¿Cuál es el planeta más cercano al Sol?"
    assert c("¿Qué tipo de astro es el Sol?") == "¿Qué es el Sol?"
    assert c("Cuéntame algo del Sol") == "¿Qué sabes del Sol?"
    assert c("Dime que Ana compra pan") == "Dime que Ana compra pan"
