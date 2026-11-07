"""parche-120: el sujeto omitido (tema del discurso) solo se hereda en verbos conjugados y que concuerdan en número."""
from src.language.lector_ud import ExtractorUD


def _arbol(frase):
    # (forma, upos, cabeza, relacion, lema)
    return frase


def test_infinitivo_sin_sujeto_no_hereda_el_tema():
    ex = ExtractorUD()
    ex.oracion([("Goku", "PROPN", 2, "nsubj", "goku"), ("vence", "VERB", 0, "root", "vencer"), ("a", "ADP", 4, "case", "a"), ("Freezer", "PROPN", 2, "obj", "freezer"), (".", "PUNCT", 2, "punct", ".")])
    assert ex.principal.key == "GOKU"
    rows = [("mientras", "SCONJ", 3, "mark", "mientras"), ("Pilaf", "PROPN", 3, "nsubj", "pilaf"), ("estaba", "VERB", 0, "root", "estar"), ("a", "ADP", 5, "case", "a"),
            ("punto", "NOUN", 3, "fixed", "punto"), ("de", "ADP", 7, "mark", "de"), ("desear", "VERB", 5, "advcl", "desear"), ("conquistar", "VERB", 7, "xcomp", "conquistar"),
            ("el", "DET", 10, "det", "el"), ("mundo", "NOUN", 8, "obj", "mundo"), (".", "PUNCT", 3, "punct", ".")]
    hs = {(h["s"], h["p"], h["o"]) for h in ex.oracion(rows)}
    assert ("GOKU", "CONQUISTAR", "MUNDO") not in hs


def test_plural_no_hereda_tema_singular_y_pasiva_si():
    ex = ExtractorUD()
    ex.oracion([("Goku", "PROPN", 2, "nsubj", "goku"), ("vence", "VERB", 0, "root", "vencer"), ("a", "ADP", 4, "case", "a"), ("Freezer", "PROPN", 2, "obj", "freezer"), (".", "PUNCT", 2, "punct", ".")])
    hs = {(h["s"], h["p"], h["o"]) for h in ex.oracion([("buscan", "VERB", 0, "root", "buscar"), ("la", "DET", 3, "det", "el"), ("esfera", "NOUN", 1, "obj", "esfera"), (".", "PUNCT", 1, "punct", ".")])}
    assert not any(s == "GOKU" for s, _, _ in hs)
    pas = [("Fue", "AUX", 2, "aux", "ser"), ("creado", "VERB", 0, "root", "crear"), ("por", "ADP", 4, "case", "por"), ("Toriyama", "PROPN", 2, "obl", "toriyama"), (".", "PUNCT", 2, "punct", ".")]
    assert ("TORIYAMA", "CREAR", "GOKU") in {(h["s"], h["p"], h["o"]) for h in ex.oracion(pas)}


def test_participio_pospuesto_no_forma_parte_del_concepto():
    ex = ExtractorUD()
    rows = [("La", "DET", 2, "det", "el"), ("comisión", "NOUN", 3, "nsubj", "comisión"), ("decide", "VERB", 0, "root", "decidir"), ("el", "DET", 5, "det", "el"), ("límite", "NOUN", 3, "obj", "límite"), (".", "PUNCT", 3, "punct", ".")]
    rows[1] = ("comisión", "NOUN", 3, "nsubj", "comisión")
    rows = [("La", "DET", 2, "det", "el"), ("comisión", "NOUN", 4, "nsubj", "comisión"), ("encargada", "ADJ", 2, "amod", "encargado"), ("decide", "VERB", 0, "root", "decidir"), ("el", "DET", 6, "det", "el"), ("límite", "NOUN", 4, "obj", "límite"), (".", "PUNCT", 4, "punct", ".")]
    hs = {(h["s"], h["p"], h["o"]) for h in ex.oracion(rows)}
    assert ("COMISION", "DECIDIR", "LIMITE") in hs
