"""parche-126: numeros como un token, cantidades con unidad, fechas completas, locuciones, verbo+infinitivo, condicional, finales, conceptos basura, fichas y segmentacion."""
import os
import tempfile

from src.language.lector import frases, limpiar
from src.language.lector_ud import ExtractorUD, LectorUD, _basura
from src.language.school_parser import SchoolParser
from src.memory.store import MemoryStore


def _hs(rows):
    return {(h["s"], h["p"], h["o"], h.get("q", ""), h.get("when", "")) for h in ExtractorUD().oracion(rows)}


def test_un_numero_es_un_token():
    assert SchoolParser._forms("Mide 3.2 metros y pesa 1,5 kg.") == ["Mide", "3.2", "metros", "y", "pesa", "1,5", "kg", "."]
    assert SchoolParser._forms("Nació en 1999.") == ["Nació", "en", "1999", "."]


def test_cifra_con_unidad_es_cantidad_no_concepto():
    rows = [("Aboim", "PROPN", 2, "nsubj", "aboim"), ("tiene", "VERB", 0, "root", "tener"), ("11,68", "NUM", 4, "nummod", "11,68"), ("km", "NOUN", 2, "obj", "km"),
            ("²", "SYM", 4, "punct", "²"), ("de", "ADP", 7, "case", "de"), ("superficie", "NOUN", 4, "nmod", "superficie"), (".", "PUNCT", 2, "punct", ".")]
    hs = _hs(rows)
    assert ("ABOIM", "TENER", "SUPERFICIE", "11,68 km²", "") in hs
    assert not any("11_68" in s or "11_68" in o for s, _, o, _, _ in hs)


def test_millones_y_cifras_en_palabras():
    rows = [("Venus", "PROPN", 2, "nsubj", "venus"), ("evaporó", "VERB", 0, "root", "evaporar"), ("hace", "VERB", 2, "advcl", "hacer"), ("715", "NUM", 5, "nummod", "715"),
            ("millones", "NOUN", 3, "obj", "millon"), ("de", "ADP", 7, "case", "de"), ("años", "NOUN", 3, "obl", "ano"), (".", "PUNCT", 2, "punct", ".")]
    hs = _hs(rows)
    assert any(o == "ANO" and q == "715 millones de años" for _, _, o, q, _ in hs) and not any("MILLON" in o for _, _, o, _, _ in hs)


def test_fecha_completa_y_dia_mes():
    rows = [("El", "DET", 2, "det", "el"), ("16", "NUM", 8, "obl", "16"), ("de", "ADP", 4, "case", "de"), ("diciembre", "NOUN", 2, "nmod", "diciembre"), ("de", "ADP", 6, "case", "de"),
            ("1850", "NUM", 4, "nmod", "1850"), ("Venus", "PROPN", 8, "nsubj", "venus"), ("alcanzó", "VERB", 0, "root", "alcanzar"), ("la", "DET", 10, "det", "el"),
            ("distancia", "NOUN", 8, "obj", "distancia"), (".", "PUNCT", 8, "punct", ".")]
    hs = ExtractorUD().oracion(rows)
    h = next(x for x in hs if x["p"] == "ALCANZAR")
    assert h["when"] == "abs:1850-12-16/1850-12-16" and h["when_disp"] == "el 16 de diciembre de 1850"


def test_locuciones_no_son_hechos():
    rows = [("Goku", "PROPN", 2, "nsubj", "goku"), ("vive", "VERB", 0, "root", "vivir"), ("en", "ADP", 4, "case", "en"), ("realidad", "NOUN", 2, "obl", "realidad"), (".", "PUNCT", 2, "punct", ".")]
    assert not any(o == "REALIDAD" for _, _, o, _, _ in _hs(rows))
    rows = [("Goku", "PROPN", 2, "nsubj", "goku"), ("vive", "VERB", 0, "root", "vivir"), ("en", "ADP", 4, "case", "en"), ("Madrid", "PROPN", 2, "obl", "madrid"), (".", "PUNCT", 2, "punct", ".")]
    assert ("GOKU", "VIVIR_EN", "MADRID", "", "") in _hs(rows)


def test_verbo_mas_infinitivo_afirma_el_infinitivo():
    rows = [("Chaytor", "PROPN", 2, "nsubj", "chaytor"), ("llegó", "VERB", 0, "root", "llegar"), ("a", "ADP", 4, "mark", "a"), ("firmar", "VERB", 2, "xcomp", "firmar"),
            ("como", "ADP", 6, "case", "como"), ("DC", "PROPN", 2, "obl", "dc"), (".", "PUNCT", 2, "punct", ".")]
    hs = _hs(rows)
    assert ("CHAYTOR", "FIRMAR_COMO", "DC", "", "") in hs and not any(p.startswith("LLEGAR") for _, p, _, _, _ in hs)


def test_condicional_de_poder_no_afirma():
    rows = [("El", "DET", 2, "det", "el"), ("croata", "NOUN", 4, "nsubj", "croata"), ("podría", "AUX", 4, "aux", "poder"), ("dar", "VERB", 0, "root", "dar"),
            ("un", "DET", 6, "det", "uno"), ("paso", "NOUN", 4, "obj", "paso"), (".", "PUNCT", 4, "punct", ".")]
    assert not _hs(rows)
    rows[2] = ("puede", "AUX", 4, "aux", "poder")
    assert any(p == "DAR" for _, p, _, _, _ in _hs(rows))


def test_con_el_objetivo_de_ayudar_el_sujeto_es_el_principal():
    rows = [("Greenspan", "PROPN", 2, "nsubj", "greenspan"), ("creó", "VERB", 0, "root", "crear"), ("una", "DET", 4, "det", "uno"), ("fundación", "NOUN", 2, "obj", "fundacion"),
            ("con", "ADP", 7, "case", "con"), ("el", "DET", 7, "det", "el"), ("objetivo", "NOUN", 2, "obl", "objetivo"), ("de", "ADP", 9, "mark", "de"), ("ayudar", "VERB", 7, "acl", "ayudar"),
            ("a", "ADP", 12, "case", "a"), ("los", "DET", 12, "det", "el"), ("niños", "NOUN", 9, "obl", "nino"), (".", "PUNCT", 2, "punct", ".")]
    hs = _hs(rows)
    assert ("GREENSPAN", "AYUDAR_A", "NINO", "", "") in hs and not any(s == "OBJETIVO" for s, _, _, _, _ in hs)


def test_conceptos_basura():
    assert _basura("AGUA_DE_CUAL") and _basura("ALBEDO_DE_ALBEDO_BOLOMETRICO") and _basura("3_C") and _basura("2000")
    assert not _basura("LEON_ASIATICO") and not _basura("NINO_DE_ONCE_ANO") and not _basura("_")


class _P:
    def tree(self, s):
        return [("Venus", "PROPN", 3, "nsubj", "venus"), ("es", "AUX", 3, "cop", "ser"), ("planeta", "NOUN", 0, "root", "planeta"), (".", "PUNCT", 3, "punct", ".")]


def test_fichas_clave_valor_se_guardan_como_hechos_del_tema():
    m = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
    LectorUD(m, _P()).leer("Radio medio: 6051,8 km\nVenus es planeta.\nPeriodo orbital: 224,7 días\nFamilia: Felidae")
    hs = {(f["s"], f["p"], f["o"], f.get("q", "")) for f in m.facts}
    assert ("VENUS", "TENER", "RADIO_MEDIO", "6051,8 km") in hs          # en espera hasta saber de qué se habla
    assert ("VENUS", "TENER", "PERIODO_ORBITAL", "224,7 días") in hs and ("VENUS", "TENER", "FAMILIA", "Felidae") in hs


def test_una_frase_con_dos_puntos_no_es_ficha():
    b = limpiar("Esto ocurrió así: el león cazó una cebra y se la comió.")
    assert b[0][0] == "parrafo"
    assert limpiar("Importante: no lo olvides")[0][0] != "ficha"
    assert limpiar("Radio medio: 6051,8 km") == [("ficha", "Radio medio\t6051,8 km")]


def test_segmentacion_abreviaturas_citas_y_vinetas():
    assert frases("Vino la Sra. Mª. García. Luego se fue.") == ["Vino la Sra. Mª. García.", "Luego se fue."]
    assert frases("Mide 3.5 m. Pesa 20 kg.") == ["Mide 3.5 m.", "Pesa 20 kg."]
    assert limpiar("Mide 3 m.[n. 1] Pesa 5 kg.[2]") == [("parrafo", "Mide 3 m. Pesa 5 kg.")]
    assert limpiar("• El león come carne.") == [("parrafo", "El león come carne.")]
