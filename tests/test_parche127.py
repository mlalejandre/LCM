"""parche-127: LECTURA DE ENTIDADES (el LCM contesta sobre cualquier texto leido: familias de nombres, tipos de pregunta, honestidad).
Todo con arboles hechos a mano: no necesita torch ni la escuela entrenada."""
import os
import tempfile

from src.language import lectura_ent as L
from src.language.lector_ud import LectorUD
from src.memory.store import MemoryStore


def _arbol(spec):
    """spec: lista de (forma, upos, cabeza 1-based (0 = raiz), relacion, lema) -> bloque de texto como lo guarda el lector."""
    return "\n".join("\t".join([f, u, str(h), d, l]) for f, u, h, d, l in spec)


def _frase(mem, txt, spec, k, par=0):
    mem.add_texto(txt, [_arbol(spec)], "", 0, k, par)


def _mem():
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    # 0 Marie Curie nació en Varsovia en 1867.
    _frase(mem, "Marie Curie nació en Varsovia en 1867.", [
        ("Marie", "PROPN", 3, "nsubj", "Marie"), ("Curie", "PROPN", 1, "flat", "Curie"), ("nació", "VERB", 0, "root", "nacer"), ("en", "ADP", 5, "case", "en"),
        ("Varsovia", "PROPN", 3, "obl", "Varsovia"), ("en", "ADP", 7, "case", "en"), ("1867", "NUM", 3, "obl", "1867"), (".", "PUNCT", 3, "punct", ".")], 0)
    # 1 Pierre Curie murió en París en 1906.
    _frase(mem, "Pierre Curie murió en París en 1906.", [
        ("Pierre", "PROPN", 3, "nsubj", "Pierre"), ("Curie", "PROPN", 1, "flat", "Curie"), ("murió", "VERB", 0, "root", "morir"), ("en", "ADP", 5, "case", "en"),
        ("París", "PROPN", 3, "obl", "París"), ("en", "ADP", 7, "case", "en"), ("1906", "NUM", 3, "obl", "1906"), (".", "PUNCT", 3, "punct", ".")], 1)
    # 2 Marie descubrió el radio.
    _frase(mem, "Marie descubrió el radio.", [
        ("Marie", "PROPN", 2, "nsubj", "Marie"), ("descubrió", "VERB", 0, "root", "descubrir"), ("el", "DET", 4, "det", "el"), ("radio", "NOUN", 2, "obj", "radio"), (".", "PUNCT", 2, "punct", ".")], 2)
    # 3 Su padre, Guillermo Kahlo, era fotógrafo.
    _frase(mem, "Frida nació en Coyoacán, donde su padre, Guillermo Kahlo, era fotógrafo.", [
        ("Frida", "PROPN", 2, "nsubj", "Frida"), ("nació", "VERB", 0, "root", "nacer"), ("en", "ADP", 4, "case", "en"), ("Coyoacán", "PROPN", 2, "obl", "Coyoacán"), (",", "PUNCT", 12, "punct", ","),
        ("donde", "ADV", 12, "advmod", "donde"), ("su", "DET", 8, "det", "su"), ("padre", "NOUN", 12, "nsubj", "padre"), (",", "PUNCT", 10, "punct", ","), ("Guillermo", "PROPN", 8, "appos", "Guillermo"),
        ("Kahlo", "PROPN", 10, "flat", "Kahlo"), (",", "PUNCT", 10, "punct", ","), ("era", "AUX", 14, "cop", "ser"), ("fotógrafo", "NOUN", 4, "acl", "fotógrafo"), (".", "PUNCT", 2, "punct", ".")], 3)
    return mem


class _Conv:
    def __init__(self, mem):
        self.m, self.parser = mem, None


def test_detecta_preguntas_sin_signos():
    for q in ["quien es lamine yamal", "donde nacio", "por que rechazo a marruecos", "en que equipo juega yamal", "contra quien debuto con españa", "cuantos años tiene", "¿Qué?"]:
        assert L.parece_pregunta(q), q
    for q in ["Ana ama a Luis", "hola", "el leon come carne", "Madrid es la capital"]:
        assert not L.parece_pregunta(q), q


def test_verbo_con_enclitico_es_el_verbo():
    assert L._sin_enclitico("ficharlo", "NOUN", "ficharlo") == ("fichar", "VERB", "fichar")
    assert L._sin_enclitico("convencerlo", "VERB", "convencer")[0] == "convencer"
    assert L._sin_enclitico("Lamine", "PROPN", "lamine")[1] == "PROPN"
    assert L._sin_enclitico("mesa", "NOUN", "mesa")[1] == "NOUN"


def test_sinonimos_curados_y_sin_ruido():
    assert "obtener" in L._sinonimos("ganar", "VERB") and "fallecer" in L._sinonimos("morir", "VERB")
    assert "tener" not in L._sinonimos("nacer", "VERB")
    assert "hacer" not in L._sinonimos("crear", "VERB")


def test_tronco_ignora_genero_y_numero():
    assert L._tronco("hijos") == L._tronco("hija") == L._tronco("hijo")


def test_contesta_donde_y_cuando_sobre_la_entidad_pedida():
    mem = _mem()
    conv = _Conv(mem)
    r = L.responder(conv, "¿Dónde nació Marie Curie?")
    assert r and "Varsovia" in r and "París" not in r
    r = L.responder(conv, "¿Cuándo murió Pierre Curie?")
    assert r and "1906" in r and "1867" not in r


def test_no_confunde_las_dos_curie():
    conv = _Conv(_mem())
    r = L.responder(conv, "¿Dónde murió Pierre Curie?")
    assert r and "París" in r and "Varsovia" not in r


def test_aposicion_responde_quien_era_su_padre():
    conv = _Conv(_mem())
    r = L.responder(conv, "¿Quién era el padre de Frida?")
    assert r and "Guillermo Kahlo" in r


def test_seguimiento_con_el_sujeto_de_la_conversacion():
    conv = _Conv(_mem())
    L.responder(conv, "¿Dónde nació Marie Curie?")
    r = L.responder(conv, "¿y cuándo nació?")
    assert r and "1867" in r


def test_honestidad_si_no_se_ha_leido_nada():
    conv = _Conv(_mem())
    r = L.responder(conv, "¿Dónde nació Albert Einstein?", final=True)
    assert r and ("no he leído" in r.lower() or "no aparece" in r.lower())
    assert "Varsovia" not in r
    r = L.responder(conv, "donde nacio einstein", final=True)                 # sin mayusculas ni signos
    assert r and "einstein" in r.lower() and "Varsovia" not in r


def test_ficha_biografica_entre_parentesis_se_lee_como_frases():
    lu = LectorUD.__new__(LectorUD)
    fs = lu._ficha("Marie Curie (Varsovia, 7 de noviembre de 1867 - Passy, 4 de julio de 1934) fue una física polaca.")
    assert "Marie Curie nació en Varsovia el 7 de noviembre de 1867." in fs
    assert "Marie Curie falleció en Passy el 4 de julio de 1934." in fs
    assert lu._ficha("Madrid (España) es la capital.") == []


def test_incisos_entre_rayas_se_guardan_aparte():
    lu = LectorUD.__new__(LectorUD)
    inc = lu._incisos("El mayor león documentado es un macho en un zoológico que pesó 454 kg —un récord mundial para el género—.")
    assert any("récord mundial" in x for x in inc)


def test_conceptos_basura_se_descartan_y_los_buenos_no():
    from src.language.lector_ud import _basura
    assert _basura("3_C") and _basura("ALBEDO_DE_ALBEDO_BOLOMETRICO")
    assert not _basura("MARIE_CURIE") and not _basura("MUSEO_DEL_PRADO")
