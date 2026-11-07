"""parche-115: lector guiado por la escuela (dependencias). Arboles escritos a mano, de campos distintos: lo comun es la GRAMATICA, no el tema."""
import os
import tempfile

from src.language.lector_ud import ExtractorUD, LectorUD, lector_para
from src.language.lector import Lector
from src.memory.store import MemoryStore


def arbol(txt):
    """'La/DET/2/det/el mitocondria/NOUN/5/nsubj/mitocondria ...' -> filas (forma, upos, cabeza, deprel, lema)"""
    return [(a, b, int(c), d, e) for a, b, c, d, e in (t.split("/") for t in txt.split())]


S = {
    "mito": "La/DET/2/det/el mitocondria/NOUN/5/nsubj/mitocondria es/AUX/5/cop/ser un/DET/5/det/uno orgánulo/NOUN/0/root/orgánulo que/PRON/7/nsubj/que produce/VERB/5/acl/producir energía/NOUN/7/obj/energía ././5/punct/.".replace("././", "./PUNCT/"),
    "electron": "El/DET/2/det/el electrón/NOUN/5/nsubj/electrón es/AUX/5/cop/ser una/DET/5/det/uno partícula/NOUN/0/root/partícula elemental/ADJ/5/amod/elemental con/ADP/8/case/con carga/NOUN/5/nmod/carga negativa/ADJ/8/amod/negativo ./PUNCT/5/punct/.",
    "heisenberg": "El/DET/2/det/el principio/NOUN/6/nsubj/principio de/ADP/4/case/de incertidumbre/NOUN/2/nmod/incertidumbre fue/AUX/6/aux/ser formulado/VERB/0/root/formular por/ADP/8/case/por Werner/PROPN/6/obl/Werner Heisenberg/PROPN/8/flat/Heisenberg en/ADP/11/case/en 1927/NUM/6/obl/1927 ./PUNCT/6/punct/.",
    "diabetes": "La/DET/2/det/el diabetes/NOUN/5/nsubj/diabetes es/AUX/5/cop/ser una/DET/5/det/uno enfermedad/NOUN/0/root/enfermedad crónica/ADJ/5/amod/crónico que/PRON/8/nsubj/que afecta/VERB/5/acl/afectar a/ADP/11/case/a el/DET/11/det/el metabolismo/NOUN/8/obj/metabolismo de/ADP/14/case/de la/DET/14/det/el glucosa/NOUN/11/nmod/glucosa ./PUNCT/5/punct/.",
    "colon": "Cristóbal/PROPN/3/nsubj/Cristóbal Colón/PROPN/1/flat/Colón llegó/VERB/0/root/llegar a/ADP/5/case/a América/PROPN/3/obl/América en/ADP/7/case/en 1492/NUM/3/obl/1492 ./PUNCT/3/punct/.",
    "madrid": "Madrid/PROPN/4/nsubj/Madrid es/AUX/4/cop/ser la/DET/4/det/el capital/NOUN/0/root/capital de/ADP/6/case/de España/PROPN/4/nmod/España ./PUNCT/4/punct/.",
    "teide": "El/DET/2/det/el Teide/PROPN/5/nsubj/Teide es/AUX/5/cop/ser un/DET/5/det/uno volcán/NOUN/0/root/volcán situado/VERB/5/acl/situar en/ADP/8/case/en Tenerife/PROPN/6/obl/Tenerife ./PUNCT/5/punct/.",
    "parlamento": "El/DET/2/det/el Parlamento/PROPN/3/nsubj/Parlamento aprueba/VERB/0/root/aprobar las/DET/5/det/el leyes/NOUN/3/obj/ley ./PUNCT/3/punct/.",
    "foton": "Los/DET/2/det/el fotones/NOUN/4/nsubj/fotón no/ADV/4/advmod/no transportan/VERB/0/root/transportar la/DET/6/det/el fuerza/NOUN/4/obj/fuerza electromagnética/ADJ/6/amod/electromagnético ./PUNCT/4/punct/.",
    "si": "Si/SCONJ/4/mark/si el/DET/3/det/el paciente/NOUN/4/nsubj/paciente toma/VERB/10/advcl/tomar el/DET/6/det/el fármaco/NOUN/4/obj/fármaco ,/PUNCT/10/punct/, la/DET/9/det/el fiebre/NOUN/10/nsubj/fiebre baja/VERB/0/root/bajar ./PUNCT/10/punct/.",
    "orni": "El/DET/2/det/el ornitorrinco/NOUN/5/nsubj/ornitorrinco es/AUX/5/cop/ser un/DET/5/det/uno mamífero/NOUN/0/root/mamífero ./PUNCT/5/punct/.",
    "cola": "Su/DET/2/det/su cola/NOUN/4/nsubj/cola es/AUX/4/cop/ser plana/ADJ/0/root/plano ./PUNCT/4/punct/.",
    "habita": "Habita/VERB/0/root/habitar en/ADP/3/case/en Australia/PROPN/1/obl/Australia ./PUNCT/1/punct/.",
    "hexagono": "Un/DET/2/det/uno hexágono/NOUN/3/nsubj/hexágono tiene/VERB/0/root/tener seis/NUM/5/nummod/seis lados/NOUN/3/obj/lado ./PUNCT/3/punct/.",
}


def hechos(*claves, ex=None):
    ex = ex or ExtractorUD()
    out = []
    for c in claves:
        out += ex.oracion(arbol(S[c]))
    return {(h["s"], h["p"], h["o"], bool(h["neg"])) for h in out}


def test_definicion_y_relativa():
    T = hechos("mito")
    assert ("MITOCONDRIA", "ES", "ORGANULO", False) in T and ("MITOCONDRIA", "PRODUCIR", "ENERGIA", False) in T


def test_cualidades_partes_y_con():
    T = hechos("electron")
    assert ("ELECTRON", "ES", "PARTICULA", False) in T and ("ELECTRON", "SER", "ELEMENTAL", False) in T and ("ELECTRON", "TENER", "CARGA", False) in T


def test_pasiva_con_agente_y_fecha():
    ex = ExtractorUD()
    hs = ex.oracion(arbol(S["heisenberg"]))
    h = [x for x in hs if x["p"] == "FORMULAR"]
    assert h and h[0]["s"] == "WERNER_HEISENBERG" and h[0]["o"] == "PRINCIPIO_DE_INCERTIDUMBRE" and h[0]["when"] == "1927"


def test_complemento_con_de_y_objeto_con_a():
    assert ("DIABETES", "AFECTAR", "METABOLISMO_DE_GLUCOSA", False) in hechos("diabetes")
    assert ("DIABETES", "SER", "CRONICO", False) in hechos("diabetes")


def test_nombre_propio_compuesto_destino_y_fecha():
    hs = ExtractorUD().oracion(arbol(S["colon"]))
    assert any(h["s"] == "CRISTOBAL_COLON" and h["p"] == "LLEGAR_A" and h["o"] == "AMERICA" and h["when"] == "1492" for h in hs)


def test_capital_de_y_localizacion_participial():
    T = hechos("madrid")
    assert ("MADRID", "ES", "CAPITAL", False) in T and ("MADRID", "CAPITAL_DE", "ESPANA", False) in T
    assert ("TEIDE", "ESTAR_EN", "TENERIFE", False) in hechos("teide") and ("TEIDE", "ES", "VOLCAN", False) in hechos("teide")


def test_negacion_y_adjetivo_que_subclasifica():
    T = hechos("foton")
    assert ("FOTON", "TRANSPORTAR", "FUERZA_ELECTROMAGNETICO", True) in T and ("FUERZA_ELECTROMAGNETICO", "ES", "FUERZA", False) in T


def test_condicional_no_se_afirma():
    assert hechos("si") == set()


def test_sujeto_omitido_y_posesivo_usan_el_tema():
    ex = ExtractorUD()
    T = hechos("orni", "cola", "habita", ex=ex)
    assert ("COLA_DE_ORNITORRINCO", "SER", "PLANO", False) in T
    assert ("ORNITORRINCO", "HABITAR_EN", "AUSTRALIA", False) in T        # «Habita…» tras «Su cola…» sigue siendo el ornitorrinco


def test_cantidades():
    T = hechos("hexagono")
    assert ("HEXAGONO", "TENER", "SEIS_LADO", False) in T and ("SEIS_LADO", "ES", "LADO", False) in T


class _Parser:
    """Parser de mentira: devuelve el arbol escrito a mano para la frase (el real es la escuela entrenada)."""
    def __init__(self, tabla):
        self.tabla = tabla

    def tree(self, s):
        return arbol(self.tabla[s.strip()])


def test_lector_ud_lee_textos_y_registra_en_memoria():
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    p = _Parser({"El ornitorrinco es un mamífero.": S["orni"], "Su cola es plana.": S["cola"], "Habita en Australia.": S["habita"], "Los fotones no transportan la fuerza electromagnética.": S["foton"]})
    L = lector_para(mem, p)
    assert isinstance(L, LectorUD)
    rep = L.leer("El ornitorrinco es un mamífero. Su cola es plana. Habita en Australia.\n\nLos fotones no transportan la fuerza electromagnética.")
    T = {(h["s"], h["p"], h["o"]) for h in rep["hechos"]}
    assert ("ORNITORRINCO", "ES", "MAMIFERO") in T and ("ORNITORRINCO", "HABITAR_EN", "AUSTRALIA") in T and rep["frases"] == 4 and not rep["sin_entender"]


def test_sin_escuela_se_usa_el_lector_de_patrones():
    d = tempfile.mkdtemp()
    assert type(lector_para(MemoryStore(os.path.join(d, "m.json")), None)) is Lector


def test_lo_ya_sabido_manda_sobre_el_texto():
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    mem.add_fact(("FOTON", "TRANSPORTAR", "FUERZA_ELECTROMAGNETICO"), neg=False)
    p = _Parser({"Los fotones no transportan la fuerza electromagnética.": S["foton"]})
    rep = lector_para(mem, p).leer("Los fotones no transportan la fuerza electromagnética.")
    assert rep.get("conflictos") and not any(h["neg"] for h in rep["hechos"])


def test_gold_real_sin_romperse():
    """Arboles de referencia reales (UD): el extractor no debe fallar nunca y debe dar hechos en una parte razonable de frases."""
    import os as _os
    f = _os.path.join(_os.path.dirname(__file__), "..", "data", "lector_bench", "gold_muestra.tsv")
    n = hs = 0
    for ln in open(f, encoding="utf-8"):
        rows = [tuple(int(x) if x.isdigit() and i == 2 else x for i, x in enumerate(t.split("/"))) for t in ln.split()]
        rows = [(a, b, int(c), d, e) for a, b, c, d, e in rows]
        n += 1
        hs += bool(ExtractorUD().oracion(rows))
    assert n >= 100 and hs / n > 0.45
