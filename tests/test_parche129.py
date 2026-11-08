"""parche-129: lo que la persona cuenta en la conversacion (Marta nacio el 12 de octubre de 1982) frente a lo que dice un texto leido,
edad calculada con la fecha de hoy, comparaciones de edad, «afirmacion + pregunta» en un mensaje, peticiones que no se saben hacer,
y los casos de relaciones entre conceptos del parche-128 (Machu Picchu, Cervantes, fotosintesis, Trafalgar).

Estas pruebas NO usan la red neuronal de la escuela: los arboles sintacticos (de textos y preguntas) estan fijados en
tests/fixtures/parche129.json, asi que dan lo mismo en cualquier equipo. Fecha de referencia: 8 de noviembre de 2026."""
import copy
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from types import SimpleNamespace

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(RAIZ, "tests", "fixtures", "parche129.json")
HOY = datetime.date(2026, 11, 8)
_FX = None


def fixture():
    global _FX
    if _FX is None:
        with open(FIX, encoding="utf-8") as fh:
            _FX = json.load(fh)
    return _FX


class ParserCongelado:
    """Devuelve los arboles y lecturas de frases ya registrados (nunca llama a la red)."""
    def __init__(self, fx):
        self.trees, self.parses, self.today = fx["trees"], fx["parses"], None

    def tree(self, raw):
        return [tuple(r) for r in self.trees.get(raw, [])]

    def parse(self, sentence, topic=None, verbs=None):
        return copy.deepcopy(self.parses.get(sentence))


def _nr(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def _cumple(g, cabeza):
    g = g.strip()
    if g.startswith("!"):
        return not any(_nr(a) in cabeza for a in g[1:].split("|"))
    if g.startswith("^"):
        if re.match(r"\W*no lo se\b", cabeza):
            return False
        return any(re.match(r"\W*" + re.escape(_nr(a)) + r"\b", cabeza) for a in g[1:].split("|"))
    return any(_nr(a) in cabeza for a in g.split("|"))


def motor_de(clave):
    from src.web.motor import Motor
    fx = fixture()
    d = tempfile.mkdtemp()
    ruta = os.path.join(d, "m.json")
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(fx["memorias"][clave], fh, ensure_ascii=False)
    mo = Motor.crear(ruta_memoria=ruta, carpeta_cartuchos=os.path.join(d, "cart"), parser=ParserCongelado(fx), semilla=False, log=lambda *a: None)
    mo.mem.today = HOY
    return mo


def ejecuta(nombre):
    """Respuestas (en orden) de la conversacion registrada con ese nombre."""
    for n, clave, msgs in fixture()["flujos"]:
        if n == nombre:
            mo = motor_de(clave)
            return msgs, [mo.chat(q).get("respuesta", "") for q, _ in msgs]
    raise KeyError(nombre)


def _comprueba(nombre):
    msgs, resp = ejecuta(nombre)
    malos = []
    for (q, esperado), r in zip(msgs, resp):
        cabeza = _nr(r).split("en el texto:")[0]
        if not all(_cumple(g, cabeza) for g in esperado.split(";") if g.strip()):
            malos.append((q, esperado, r[:200]))
    assert not malos, "\n".join("%s | esperado %s | %s" % m for m in malos)


def _nombres_de_flujos():
    return [n for n, _, _ in fixture()["flujos"]]


@pytest.mark.parametrize("nombre", ["machu", "cervantes", "foto", "trafalgar", "yamal", "cervantes2"])
def test_conversaciones_registradas(nombre):
    _comprueba(nombre)


def test_afirmacion_y_pregunta_en_un_mensaje_en_conversacion_nueva():
    msgs, resp = ejecuta("yamal")                                                      # la segunda conversacion de «yamal» es la combinada
    mo = motor_de("yamal")
    r1 = mo.chat("marta nació el dia 12 de octubre de 1982 que edad tiene hoy?")["respuesta"]
    r2 = mo.chat("que día nació Marta?")["respuesta"]
    assert "44 años" in r1 and "Entendido" in r1
    assert "12 de octubre de 1982" in r2 and "2007" not in r2


def test_misma_pregunta_misma_respuesta():
    mo = motor_de("trafalgar")
    a = mo.chat("¿Quién ganó la batalla?")["respuesta"]
    b = mo.chat("¿Quién ganó la batalla?")["respuesta"]
    assert a == b and _nr(a).startswith("horatio nelson")


def test_mismas_respuestas_con_distinta_semilla_de_hash(tmp_path):
    """El orden de un conjunto de Python no puede cambiar lo que se contesta."""
    guion = tmp_path / "g.py"
    guion.write_text("import json, sys\nsys.path.insert(0, %r)\nfrom tests import test_parche129 as t\n"
                     "print(json.dumps([t.ejecuta(n)[1] for n in ('trafalgar', 'yamal')], ensure_ascii=False))\n" % RAIZ, encoding="utf-8")
    salidas = []
    for semilla in ("1", "2", "3"):
        r = subprocess.run([sys.executable, str(guion)], capture_output=True, text=True, cwd=RAIZ, env=dict(os.environ, PYTHONHASHSEED=semilla))
        assert r.returncode == 0, r.stderr[-800:]
        salidas.append(r.stdout.strip().splitlines()[-1])
    assert salidas[0] == salidas[1] == salidas[2]


# ------------------------------------------------------------------------------------------- piezas sueltas (sin textos ni parser)
def _mem(*hechos, textos=()):
    fs = []
    for i, (s, p, o, cuando, fuente) in enumerate(hechos):
        fs.append({"s": s, "p": p, "o": o, "when_abs": cuando, "source": fuente, "t": float(i), "neg": False, "archived": False})
    return SimpleNamespace(facts=fs, display={"MARTA": "marta", "PEDRO": "pedro", "ANA_LOPEZ": "Ana López"}, textos=list(textos), today=HOY)


MARTA = ("MARTA", "NACER", "_", "1982-10-12/1982-10-12", "marta nació el día 12 de octubre de 1982")


def test_fecha_con_dia_delante_del_numero():
    from src.language.fechas import extract_abs
    limpia, iv, disp = extract_abs("Marta nació el día 12 de octubre de 1982.", HOY)
    assert iv == "1982-10-12/1982-10-12" and "día" not in limpia and limpia.startswith("Marta nació")
    assert extract_abs("Ana compró pan el 5 de noviembre.", HOY)[1] == "2026-11-05/2026-11-05"


@pytest.mark.parametrize("pregunta,esperado", [
    ("¿Qué día nació Marta?", "Marta nació el 12 de octubre de 1982."),
    ("que día nació marta?", "Marta nació el 12 de octubre de 1982."),
    ("¿Cuándo nació Marta?", "Marta nació el 12 de octubre de 1982."),
    ("¿En qué fecha nació Marta?", "Marta nació el 12 de octubre de 1982."),
    ("¿En qué año nació Marta?", "Marta nació en 1982."),
    ("¿En qué mes nació Marta?", "Marta nació en octubre de 1982."),
    ("¿Qué edad tiene Marta?", "Marta tiene 44 años (nació el 12 de octubre de 1982)."),
    ("¿Qué edad tiene Marta hoy?", "Marta tiene 44 años (nació el 12 de octubre de 1982)."),
    ("¿Cuántos años tiene marta?", "Marta tiene 44 años (nació el 12 de octubre de 1982)."),
    ("¿Cuántos años cumple Marta?", "Marta tiene 44 años (nació el 12 de octubre de 1982)."),
])
def test_vida_fecha_y_edad_desde_lo_que_dijo_la_persona(pregunta, esperado):
    from src.language import vida
    assert vida.responder(pregunta, _mem(MARTA)) == esperado


def test_vida_cumpleanos_y_edad_el_dia_del_cumple():
    from src.language import vida
    r = vida.responder("¿Cuándo cumple años Marta?", _mem(MARTA))
    assert "12 de octubre" in r and "338 días" in r and "45 años" in r
    m = _mem(MARTA)
    m.today = datetime.date(2026, 10, 12)
    assert "tiene 44 años" in vida.responder("¿Qué edad tiene Marta?", m)
    m.today = datetime.date(2026, 10, 11)
    assert "tiene 43 años" in vida.responder("¿Qué edad tiene Marta?", m)


def test_vida_solo_año_o_con_fallecimiento_o_sin_fecha():
    from src.language import vida
    m = _mem(("PEDRO", "NACER", "_", "1990-01-01/1990-12-31", "pedro nació en 1990"))
    assert "entre 35 y 36 años" in vida.responder("¿Qué edad tiene Pedro?", m)
    m = _mem(MARTA, ("MARTA", "MORIR", "_", "2020-03-01/2020-03-01", "marta murió el 1 de marzo de 2020"))
    assert "murió con 37 años" in vida.responder("¿Qué edad tiene Marta?", m)
    m = _mem(("ANA_LOPEZ", "VIVIR_EN", "MADRID", None, "Ana López vive en Madrid"))
    assert "no sé cuándo nació" in vida.responder("¿Qué edad tiene Ana López?", m)
    assert vida.responder("¿Qué edad tiene Luis?", m) is None


def test_los_hechos_de_un_texto_no_son_de_la_conversacion():
    from src.language import vida
    frase = "Marta nació el 12 de octubre de 1982."
    m = _mem(("MARTA", "NACER", "_", "1982-10-12/1982-10-12", frase), textos=[{"t": frase}])
    assert vida.responder("¿Qué edad tiene Marta?", m) is None
    assert vida.entidades_de_conversacion(m, "¿qué día nació marta?") == []
    m2 = _mem(MARTA)
    assert vida.entidades_de_conversacion(m2, "¿qué día nació marta?") == ["marta"]
    assert vida.entidades_de_conversacion(m2, "¿qué día nació marta?", lambda w: w == "marta") == []


@pytest.mark.parametrize("mensaje,esperado", [
    ("marta nació el dia 12 de octubre de 1982 que edad tiene hoy?", ("marta nació el dia 12 de octubre de 1982", "que edad tiene hoy")),
    ("Pedro nació en 1990, ¿cuántos años tiene?", ("Pedro nació en 1990", "cuántos años tiene")),
    ("Ana vive en Madrid y trabaja allí. ¿Dónde trabaja Ana?", ("Ana vive en Madrid y trabaja allí", "Dónde trabaja Ana")),
    ("¿Cuándo nació Marta?", None),
    ("dime que día nació marta", None),
    ("Marta dice que Pedro vive en Madrid?", None),
    ("Pedro llegó cuando salió el sol, verdad?", None),
    ("Si hoy es 9 de junio, ¿qué día será pasado mañana?", None),
    ("Si hoy es dia 3 de febrero que día fue ayer?", None),
    ("Hoy es 1 de enero; ¿qué día fue ayer?", None),
    ("Supongamos que hoy es 31 de diciembre. ¿Qué día es mañana?", None),
])
def test_separar_afirmacion_y_pregunta(mensaje, esperado):
    from src.language import vida
    assert vida.partir(mensaje) == esperado


def test_comparar_edades_con_nacimientos_de_la_conversacion_y_de_un_texto():
    from src.language import vida
    m = _mem(MARTA, ("PEDRO", "NACER", "_", "1990-01-01/1990-12-31", "pedro nació en 1990"))
    texto = {"yamal": ("Lamine Yamal", (2007, 7, 13)), "luis": ("Luis de la Fuente", None)}
    res = lambda n: next((v for k, v in texto.items() if k in n.lower()), None)
    r = vida.comparar_edades("¿Quién es mayor, Marta o Pedro?", m, res)
    assert r.startswith("Marta es mayor que Pedro") and "unos 8 años" in r
    assert vida.comparar_edades("¿Es Pedro mayor que Marta?", m, res).startswith("No. Pedro es menor que Marta")
    assert "24 años y 9 meses" in vida.comparar_edades("¿Quién es mayor, Marta o Yamal?", m, res)
    assert vida.comparar_edades("¿Quién nació antes, Yamal o Marta?", m, res).startswith("Marta nació antes")
    assert "24 años y 9 meses de diferencia" in vida.comparar_edades("¿Cuántos años se llevan Marta y Yamal?", m, res)
    assert vida.comparar_edades("¿Quién es más joven, Marta o Yamal?", m, res).startswith("Lamine Yamal es más joven que Marta")
    assert "No sé cuándo nació Luis de la Fuente" in vida.comparar_edades("¿Quién es mayor, Marta o Luis?", m, res)
    assert vida.comparar_edades("¿Quién es mayor, Marta o Zacarías?", m, res) is None


@pytest.mark.parametrize("texto,esperado", [
    ("puedes contarme un cuento?", True), ("¿puedes cantar?", True), ("¿Sabes bailar?", True), ("¿Podrías escribirme un poema?", True),
    ("¿Puedes decirme cuándo nació Yamal?", False), ("¿puedes decirme si Yamal nació en 2007?", False), ("¿Quién ganó la batalla?", False), ("Marta sabe cantar", False),
])
def test_peticiones_que_no_se_saben_hacer(texto, esperado):
    from src.language import vida
    assert vida.pide_capacidad(texto) is esperado


@pytest.mark.parametrize("texto,esperado", [
    ("¿Puedes decirme cuántos años tiene Yamal?", "¿cuántos años tiene Yamal?"),
    ("me puedes decir dónde nació Yamal", "¿dónde nació Yamal?"),
    ("¿Puedes decirme si Yamal nació en Esplugas?", "¿Yamal nació en Esplugas?"),
    ("¿Puedes decirme la hora?", None),
    ("¿Quién ganó?", "¿Quién ganó?"),
])
def test_cortesia_delante_de_la_pregunta(texto, esperado):
    from src.language import lectura_ent
    assert lectura_ent.sin_cortesia(texto) == esperado
