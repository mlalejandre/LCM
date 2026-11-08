"""parche-131: tras «No conozco X: ¿me lo explicas?» la pregunta SIGUIENTE se contesta como cualquier pregunta.

Antes, mientras esperaba la explicacion («Mongolia es un pais»), cualquier mensaje -incluida una pregunta clara- se trataba como conversacion y salia
algo como «Conozco 1: León.» en vez de la respuesta del texto. Ahora una pregunta cancela la espera; una explicacion («es un pais de Asia») sigue sirviendo."""
from src.language.dialogue import Conversation


class _ParserFalso:
    today = None

    def parse(self, texto, tema=None):
        return []


def _conv(tmp_path):
    from src.language.qa import QA
    from src.memory.store import MemoryStore
    mem = MemoryStore(str(tmp_path / "m.json"))
    return Conversation(mem, _ParserFalso(), lambda m, p: QA(m, p.parse, lambda facts: {}))


def test_una_pregunta_cancela_la_espera_antes_de_contestar(tmp_path, monkeypatch):
    c = _conv(tmp_path)
    c.m.textos = ["texto leido"]                                                                # hay un texto leido: la pregunta debe poder contestarse con el
    vistas = []
    original = c._say1

    def espia(raw):
        vistas.append(c.d.pending)                                                              # lo que ve el contestador al empezar
        return original(raw)

    monkeypatch.setattr(c, "_say1", espia)
    c.d.pending = ("define", "Mongolia")
    c.say("¿Cuántas horas al día está inactivo el león?")
    assert vistas and vistas[0] is None


def test_una_pregunta_aritmetica_tambien_se_contesta(tmp_path):
    c = _conv(tmp_path)
    c.d.pending = ("define", "Mongolia")
    assert "45" in c.say("¿Cuánto es 15 por 3?")
    assert c.d.pending is None


def test_sin_signos_de_pregunta_la_espera_sigue_viva(tmp_path):
    c = _conv(tmp_path)
    c.d.pending = ("define", "Mongolia")
    c.say("Es un país de Asia.")
    assert c.d.pending is None                      # la explicacion se consume como siempre


def test_otras_esperas_no_se_tocan(tmp_path):
    c = _conv(tmp_path)
    c.d.pending = ("name", "")
    c.say("Marcos")
    assert c.d.user == "Marcos"
