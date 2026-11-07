"""parche-118: anclaje de conceptos (entidad / conocido / nuevo) y concordancia del antecedente de las relativas."""
import os
import tempfile

from src.language.anclaje import anclar
from src.language.lector_ud import ExtractorUD, LectorUD
from src.memory.store import MemoryStore


def test_relativa_concuerda_con_su_antecedente():
    rows = [("Goku", "PROPN", 3, "nsubj", "goku"), ("se", "PRON", 3, "expl", "el"), ("muestra", "VERB", 0, "root", "mostrar"), ("como", "ADP", 6, "case", "como"),
            ("un", "DET", 6, "det", "uno"), ("niño", "NOUN", 3, "obl", "nino"), ("de", "ADP", 9, "case", "de"), ("once", "NUM", 9, "nummod", "once"),
            ("años", "NOUN", 6, "nmod", "ano"), ("que", "PRON", 11, "nsubj", "que"), ("practica", "VERB", 9, "acl", "practicar"),
            ("las", "DET", 13, "det", "el"), ("artes", "NOUN", 11, "obj", "arte"), (".", "PUNCT", 3, "punct", ".")]
    hs = {(h["s"], h["p"], h["o"]) for h in ExtractorUD().oracion(rows)}
    assert ("NINO_DE_ONCE_ANO", "PRACTICAR", "ARTE") in hs and not any(s == "ONCE_ANO" and p == "PRACTICAR" for s, p, _ in hs)


class _P:
    def tree(self, s):
        return [("El", "DET", 2, "det", "el"), ("león", "NOUN", 5, "nsubj", "león"), ("es", "AUX", 5, "cop", "ser"), ("un", "DET", 5, "det", "uno"),
                ("saiyajin", "NOUN", 0, "root", "saiyajin"), (".", "PUNCT", 5, "punct", ".")]


def test_anclaje_distingue_conocido_y_nuevo():
    m = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
    rep = LectorUD(m, _P()).leer("El león es un saiyajin.")
    an = rep["anclaje"]
    assert an["conceptos"]["LEON"]["estado"] == "conocido" and "felino" in an["conceptos"]["LEON"]["clase"]
    assert an["conceptos"]["SAIYAJIN"]["estado"] == "nuevo"
    assert "Conceptos:" in __import__("src.language.lector", fromlist=["resumen"]).resumen(rep)


def test_lemas_verbales_no_se_duplican():
    from src.language.school_parser import SchoolParser
    assert SchoolParser._lema_regular("revelará", "revelar") == "revelar"
    assert SchoolParser._lema_regular("cocina", "cocina") == "cocinar"
    from src.language.lector_ud import Arbol
    A = Arbol([("insuflarle", "VERB", 0, "root", "insuflarle")])
    assert A.l(0) == "insuflar"


def test_sentido_por_contexto():
    from src.language.anclaje import Anclaje
    m = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
    a = Anclaje(m)
    cola_cuerpo = a.estado("COLA", False, 0, ["mono", "pelo", "animal"])
    assert "parte" in " ".join(cola_cuerpo["clase"]) or "cuerpo" in " ".join(cola_cuerpo["clase"])
