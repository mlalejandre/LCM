"""parche-122: sujetos cuantificados (el 90 % de X, la mayoría de X) y pasiva refleja con el paciente delante del verbo."""
import os
import re
import tempfile

from src.language.lector_ud import ExtractorUD, LectorUD
from src.memory.store import MemoryStore


def _rows(txt):
    return [(m.group(2), m.group(3), int(m.group(4)), m.group(5), m.group(6)) for m in re.finditer(r"(\d+):(.+?)/([A-Z]+)->(\d+):(\w+)\[(.*?)\](?= \d+:|$)", txt)]


T_PORCENTAJE = ("1:El/DET->3:det[el] 2:90/NUM->3:nummod[90] 3:%/SYM->10:nsubj[%] 4:de/ADP->6:case[de] 5:las/DET->6:det[el] 6:hemorragias/NOUN->3:nmod[hemorragia] "
                "7:intracraneales/ADJ->6:amod[intracraneal] 8:corresponden/VERB->0:root[corresponder] 9:a/ADP->11:case[a] 10:la/DET->11:det[el] 11:hipertensión/NOUN->8:obl[hipertension] 12:./PUNCT->8:punct[.]")
T_PORCENTAJE = T_PORCENTAJE.replace("3:%/SYM->10:nsubj[%]", "3:%/SYM->8:nsubj[%]")
T_REFLEJA = ("1:El/DET->2:det[el] 2:Día/PROPN->8:obl[dia] 3:Mundial/PROPN->2:amod[mundial] 4:de/ADP->6:case[de] 5:la/DET->6:det[el] 6:Hipertensión/PROPN->2:nmod[hipertension] "
             "7:se/PRON->8:expl[el] 8:celebra/VERB->0:root[celebrar] 9:el/DET->10:det[el] 10:17/NUM->8:obl[17] 11:de/ADP->12:case[de] 12:mayo/NOUN->10:nmod[mayo] 13:./PUNCT->8:punct[.]")


def test_sujeto_porcentaje_no_generaliza():
    hs = ExtractorUD().oracion(_rows(T_PORCENTAJE))
    h = [x for x in hs if x["p"] == "CORRESPONDER_A"][0]
    assert h["s"] == "HEMORRAGIA" and h["q"] == "90 %"


def test_pasiva_refleja_con_paciente_delante():
    hs = {(h["s"], h["p"]) for h in ExtractorUD().oracion(_rows(T_REFLEJA))}
    assert any(p == "SE_CELEBRAR" for _, p in hs)


class _P:
    def tree(self, s):
        return _rows(T_PORCENTAJE)


def test_la_cantidad_se_guarda_en_la_memoria():
    m = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
    LectorUD(m, _P()).leer("El 90 % de las hemorragias intracraneales corresponden a la hipertensión.")
    f = [x for x in m.facts if x["p"] == "CORRESPONDER_A"][0]
    assert f.get("q") == "90 %"


def test_el_tema_envejece():
    """El sujeto omitido solo se hereda del tema de las frases inmediatas; uno viejo ya no es «el sujeto de esta frase»."""
    ex = ExtractorUD()
    ex.oracion([("Goku", "PROPN", 2, "nsubj", "goku"), ("vence", "VERB", 0, "root", "vencer"), ("a", "ADP", 4, "case", "a"), ("Freezer", "PROPN", 2, "obj", "freezer"), (".", "PUNCT", 2, "punct", ".")])
    frag = [("Radiografía", "NOUN", 0, "root", "radiografía"), (".", "PUNCT", 1, "punct", ".")]
    sin_sujeto = [("compra", "VERB", 0, "root", "comprar"), ("pan", "NOUN", 1, "obj", "pan"), (".", "PUNCT", 1, "punct", ".")]
    ex.oracion(frag)
    ex.oracion(frag)
    ex.oracion(frag)
    assert not any(h["s"] == "GOKU" for h in ex.oracion(sin_sujeto))


def test_texto_del_documento_y_correlativas_no_son_hechos():
    ex = ExtractorUD()
    aviso = _rows("1:Este/DET->2:det[este] 2:artículo/NOUN->4:nsubj[artículo] 3:necesita/VERB->0:root[necesitar] 4:referencias/NOUN->3:obj[referencia] 5:./PUNCT->3:punct[.]")
    aviso = [("Este", "DET", 2, "det", "este"), ("artículo", "NOUN", 3, "nsubj", "artículo"), ("necesita", "VERB", 0, "root", "necesitar"), ("referencias", "NOUN", 3, "obj", "referencia"), (".", "PUNCT", 3, "punct", ".")]
    assert ex.oracion(aviso) == []
    cuanto = [("cuanto", "ADV", 3, "advmod", "cuanto"), ("más", "ADV", 3, "advmod", "más"), ("grande", "ADJ", 0, "root", "grande"), (".", "PUNCT", 3, "punct", ".")]
    assert ex.oracion(cuanto) == []


def test_infinitivo_con_clitico_da_su_infinitivo():
    from src.language.lector_ud import Arbol
    for forma, esperado in (("llevarla", "llevar"), ("disponerse", "disponer"), ("insuflarle", "insuflar")):
        assert Arbol([(forma, "VERB", 0, "root", forma + "r")]).l(0) == esperado


def test_termino_de_comparacion_no_es_sujeto_ni_tema():
    ex = ExtractorUD()
    ex.oracion([("Venus", "PROPN", 3, "nsubj", "venus"), ("es", "AUX", 3, "cop", "ser"), ("planeta", "NOUN", 0, "root", "planeta"), (".", "PUNCT", 3, "punct", ".")])
    rows = [("a", "ADP", 7, "advmod", "a"), ("el", "DET", 1, "fixed", "el"), ("igual", "ADJ", 1, "fixed", "igual"), ("que", "SCONJ", 1, "fixed", "que"),
            ("Mercurio", "PROPN", 7, "nsubj", "mercurio"), (",", "PUNCT", 5, "punct", ","), ("carece", "VERB", 0, "root", "carecer"), ("de", "ADP", 9, "case", "de"),
            ("satélites", "NOUN", 7, "obl", "satélite"), (".", "PUNCT", 7, "punct", ".")]
    hs = {(h["s"], h["p"], h["o"]) for h in ex.oracion(rows)}
    assert not any(s == "MERCURIO" for s, _, _ in hs)
    assert ex.principal.key == "VENUS"
