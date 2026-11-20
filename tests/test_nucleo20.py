"""LCM 2.0 · núcleo conversacional unificado. Repite 77 diálogos (tandas 1-6) con los árboles
de la Escuela congelados en tests/fixtures/nucleo20.json, así que da lo mismo en cualquier equipo y no necesita modelos.
Criterios por turno: 'ACK' (afirmación aceptada), 'ABST' (debe abstenerse: afirmar algo = alucinación),
o grupos 'a|b;!c;^d' (contiene alguno; no contiene; empieza por). Fecha de referencia: 18 de noviembre de 2026."""
import copy
import datetime
import json
import os
import re
import tempfile
import unicodedata

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(RAIZ, "tests", "fixtures", "nucleo20.json")
_FX = None


def fixture():
    global _FX
    if _FX is None:
        with open(FIX, encoding="utf-8") as fh:
            _FX = json.load(fh)
    return _FX


class EscuelaCongelada:
    """Devuelve árboles y lecturas ya registrados; `model` no nulo activa el núcleo como con la Escuela real."""
    model = True

    def __init__(self, fx):
        self.trees, self.parses, self.today = fx["trees"], fx["parses"], None

    def tree(self, raw):
        return [tuple(r) for r in self.trees.get(raw, [])]

    def parse(self, sentence, topic=None, verbs=None):
        return copy.deepcopy(self.parses.get(sentence))


def nr(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


_ABS = re.compile(r"\b(no lo se|no se\b|no conozco|no consta|no tengo (?:ese|esa|ningun|informacion|constancia|datos?|una prueba|forma)|no dispongo|no me (?:lo )?has (?:dicho|contado)|"
                  r"no puedo (?:saber|afirmar|establecer|responder|evaluar|determinar)|no he entendido|no entiendo|necesito (?:que|mas|una|saber)|"
                  r"no me consta|no estoy seguro|no sabria|¿me lo explicas|me lo explicas|a quien te refieres|de quien hablas|no has dicho|desconozco|nadie me (?:lo )?ha dicho|aun no me)")


def _pat(a):
    a = nr(a)
    return re.escape(a[:-1]) if a.endswith("*") else re.escape(a) + r"(?!\w)"


def _cumple(g, cab, abst=False):
    g = g.strip()
    if abst and "ABST" in g.lstrip("^").split("|"):       # «^no|ABST»: también vale abstenerse
        return True
    if g.startswith("!"):
        return not any(re.search(r"(?<!\w)" + _pat(a), cab) for a in g[1:].split("|"))
    if g.startswith("^"):
        return any(re.match(r"\W*" + _pat(a), cab) for a in g[1:].split("|"))
    return any(re.search(r"(?<!\w)" + _pat(a), cab) for a in g.split("|"))


def veredicto(crit, resp):
    if crit == "ANY":
        return True
    if not isinstance(resp, str) or not resp.strip():
        return False
    r = nr(re.sub(r"No he entendido «[^»]*»", "No he entendido", resp))
    if crit == "ACK":
        return not (_ABS.search(r) or "no he podido" in r)
    if crit == "ABST":
        return bool(_ABS.search(nr(resp)))
    try:                                                   # el mismo evaluador estricto que el laboratorio
        from lab.banco import veredicto as _v
        return _v(crit, resp) in (None, "OK")
    except ImportError:                                    # noqa
        pass
    return all(_cumple(g, r, bool(_ABS.search(nr(resp)))) for g in crit.split(";") if g.strip())


def _motor():
    from src.web.motor import Motor
    fx = fixture()
    d = tempfile.mkdtemp()
    mo = Motor.crear(ruta_memoria=os.path.join(d, "m.json"), carpeta_cartuchos=os.path.join(d, "cart"), parser=EscuelaCongelada(fx), semilla=True, log=lambda *a: None)
    mo.mem.today = datetime.date.fromisoformat(fx["hoy"])
    return mo


def _ids():
    try:
        return [d["id"] for d in fixture()["dialogos"]]
    except OSError:
        return []


@pytest.mark.skipif(not os.path.exists(os.path.join(RAIZ, "data", "semilla.txt")), reason="falta data/semilla.txt (conceptos de fábrica)")
@pytest.mark.parametrize("ident", _ids())
def test_dialogo(ident):
    d = next(x for x in fixture()["dialogos"] if x["id"] == ident)
    mo = _motor()
    malos = []
    for txt, crit in d["turnos"]:
        r = mo.chat(txt).get("respuesta", "")
        if not veredicto(crit, r):
            malos.append("%s | esperado %s | %s" % (txt, crit, str(r)[:160]))
    assert not malos, "\n".join(malos)


def test_nucleo_inactivo_con_analizadores_de_prueba():
    """Con un analizador sin modelo el núcleo no interviene: las capas 1.4-1.9 se comportan como antes."""
    from src.nucleo20 import activo

    class Falso:
        def tree(self, s):
            return []
    assert not activo(None) and not activo(Falso())
    assert activo(EscuelaCongelada({"trees": {}, "parses": {}}))


def test_no_alucina_sobre_desconocidos():
    mo = _motor()
    n = mo._nucleo20()
    assert n is not None
    r = n._abst("No lo sé.")
    assert r["estado"] == "abst"


def test_morfologia():
    from src.nucleo20 import morfo as M
    assert M.conjugar("vivir", "pres", "2s") == "vives" and M.conjugar("tener", "pres", "2s") == "tienes"
    assert M.conjugar("vivir", "imp", "3s") == "vivía" and M.conjugar("dormir", "pres", "3s") == "duerme"
    assert M.analizar("compró")[0] == ("comprar", "pret", "3s") and M.analizar("tengo")[0][:2] == ("tener", "pres")
    assert M.masc("cansada") == "cansado" and M.masc("verdes") == "verde" and M.singular("lápices") == "lápiz"


def test_pertinencia_documental():
    """tanda 0: una cita cuyo documento habla de la entidad consultada es pertinente aunque la frase use pronombres."""
    from src.quality.evidencia15 import pertinencia
    from types import SimpleNamespace
    mem = SimpleNamespace(textos=[{"t": "Machu Picchu es una antigua ciudad inca.", "d": 1}, {"t": "Fue construida por orden del emperador Pachacútec.", "d": 1},
                                  {"t": "Lamine Yamal nació en 2007.", "d": 2}])
    ok, _ = pertinencia("¿Quién ordenó construir Machu Picchu?", "Pachacútec. En el texto: «Fue construida por orden del emperador Pachacútec.»", mem)
    assert ok
    ok, _ = pertinencia("¿Cuándo nació María?", "En 2007. En el texto: «Lamine Yamal nació en 2007.»", mem)
    assert not ok
