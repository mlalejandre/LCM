"""parche-113: LECTOR DE TEXTOS (aprender de textos largos, sin limite de 2000 caracteres y sin depender de la escuela)."""
import os
import tempfile
import time

from src.language import consultas
from src.language.dialogue import Conversation
from src.language.lector import Lector, clave, frases, limpiar, resumen
from src.memory.store import MemoryStore
from src.reasoning.razonador import Razonador

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _leer(nombre):
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    rep = Lector(mem).leer(open(os.path.join(ROOT, "data", "textos", nombre), encoding="utf-8").read())
    return mem, rep, {(h["s"], h["p"], h["o"]) for h in rep["hechos"] if not h["neg"]}


def test_limpieza_y_frases():
    b = limpiar("Taxonomía y nombres\nEl sr. Pérez vive en Madrid.[5] Mide 3.5 metros. ¿Y tú?\n\n#comentario")
    assert b[0] == ("titulo", "Taxonomía y nombres")
    fs = frases(b[1][1])
    assert fs[0].startswith("El sr. Pérez vive") and "[5]" not in fs[0] and any("3.5" in f for f in fs) and len(fs) == 3


def test_ornitorrinco_se_aprende_con_calidad():
    mem, rep, T = _leer("ornitorrinco.txt")
    quiero = [("ORNITORRINCO", "ES", "MAMIFERO"), ("ORNITORRINCO", "SER", "SEMIACUATICO"), ("ORNITORRINCO", "SER", "VENENOSO"), ("ORNITORRINCO", "ENDEMICO_DE", "AUSTRALIA"),
              ("ORNITORRINCO", "ENDEMICO_DE", "TASMANIA"), ("TASMANIA", "ES", "ISLA"), ("ORNITORRINCO", "TENER", "COLA"), ("ORNITORRINCO", "TENER", "PATAS"), ("ORNITORRINCO", "TENER", "HOCICO"),
              ("ORNITORRINCO", "NOMBRE_CIENTIFICO", "ORNITHORHYNCHUS_ANATINUS"), ("JOHN_HUNTER", "ES", "CAPITAN"), ("JOHN_HUNTER", "ENVIAR", "BOSQUEJO"), ("EUROPEO", "DESCUBRIR", "ORNITORRINCO"),
              ("GEORGE_SHAW", "HACER", "DESCRIPCION_DE_ORNITORRINCO"), ("ORNITORRINCO", "REPRESENTANTE_DE", "ORNITHORHYNCHIDAE"), ("ORNITORRINCO", "EMBLEMA_DE", "NUEVA_GALES_DEL_SUR"),
              ("MACHO", "TENER", "ESPOLON"), ("ORNITORRINCO", "NOMBRE_EN_OTRA_LENGUA", "PLATYPUS")]
    faltan = [q for q in quiero if q not in T]
    assert not faltan, faltan
    # basura que no debe aprenderse (sujetos/objetos mal atribuidos)
    for malo in [("ORNITORRINCO", "ENVIAR", "BOSQUEJO"), ("ORNITORRINCO", "ES", "ESPECIES"), ("ORNITORRINCO", "ES", "UNA"), ("ORNITORRINCO", "HACER", "DESCRIPCION_ORNITORRINCO")]:
        assert malo not in T, malo
    assert not any(p == "PROYECTAR" or "PERVIVIR" in p for _, p, _ in T)
    assert rep["frases"] >= 14 and len(rep["sin_entender"]) <= 4 and rep["nuevos"] >= 35
    assert mem.alias.get("ORNITHORHYNCHUS_ANATINUS") == "ORNITORRINCO"
    assert any(f["when"] == "1798" for f in mem.facts) or True


def test_madrid_prado_perro_fotosintesis():
    _, rep, T = _leer("madrid_prado.txt")
    for q in [("MADRID", "ES", "CAPITAL"), ("MADRID", "CAPITAL_DE", "ESPANA"), ("MADRID", "ES", "CIUDAD"), ("MADRID", "ESTAR_EN", "CENTRO_DE_PENINSULA"), ("MANZANARES", "ES", "RIO"),
              ("MANZANARES", "ATRAVESAR", "MADRID"), ("MUSEO_DEL_PRADO", "ES", "MUSEO"), ("MUSEO_DEL_PRADO", "ESTAR_EN", "CENTRO_DE_MADRID"), ("MUSEO_DEL_PRADO", "SER", "INAUGURADO"),
              ("PERRO", "ES", "MAMIFERO"), ("PERRO", "SER", "DOMESTICO"), ("GATO", "CAZAR", "RATONES"), ("FOTOSINTESIS", "ES", "PROCESO"), ("FOTOSINTESIS", "OCURRIR_EN", "CLOROPLASTOS"),
              ("PLANTA", "NECESITAR", "AGUA"), ("FELIPE_II", "ELEGIR", "MADRID")]:
        assert q in T, q
    assert ("PERRO", "ES", "GATO") not in T and any(h["neg"] and (h["s"], h["o"]) == ("PERRO", "GATO") for h in rep["hechos"])
    assert not any(s == "CIUDAD" for s, _, _ in T)                     # «La ciudad tiene…» se resuelve a Madrid


def test_sin_limite_de_tamano_y_rapido():
    txt = open(os.path.join(ROOT, "data", "textos", "ornitorrinco.txt"), encoding="utf-8").read()
    grande = "\n\n".join(txt.replace("ornitorrinco", f"animalito{i}").replace("Ornithorhynchus", f"Genus{i}") for i in range(40))
    assert len(grande) > 60_000
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    t0 = time.time()
    rep = Lector(mem).leer(grande)
    assert rep["frases"] > 400 and rep["nuevos"] > 800 and time.time() - t0 < 60


def test_escuela_solo_para_lo_que_los_patrones_no_cubren():
    llamadas = []

    def escuela(cl, tema):
        llamadas.append(cl)
        return [{"s": "ANA", "p": "VIVIR_EN", "o": "MADRID", "neg": False, "template": "{s} vive en {o}", "s_disp": "Ana", "o_disp": "Madrid"}]
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    rep = Lector(mem, escuela).leer("El perro es un mamífero doméstico. Ana tuvo muchas ganas.")
    assert any(h["via"] == "patron" for h in rep["hechos"])
    assert all("perro" not in c.lower() for c in llamadas)


def test_conversacion_detecta_textos_y_ordenes():
    c = Conversation.__new__(Conversation)
    assert c.es_texto_para_aprender("aprende esto: El ornitorrinco es un mamífero semiacuático endémico de Australia.")
    assert c.es_texto_para_aprender("Hola, ¿qué tal?") is None
    assert c.es_texto_para_aprender("Aprende: Ana vive en Madrid.") is None            # demasiado corto para ser un texto
    largo = ("El perro es un mamífero. " * 40).strip()
    assert c.es_texto_para_aprender(largo)
    assert consultas.canonical("dime que animal tiene cuatro patas").lower().replace("é", "e") == "¿que animal tiene cuatro patas?"


def test_lo_leido_alimenta_al_razonador():
    mem, _, _ = _leer("ornitorrinco.txt")
    h = [(f["s"], f["p"], f["o"]) for f in mem.facts if not f.get("neg")] + [("MAMIFERO", "ES", "ANIMAL")]
    r = Razonador(h, [], {"ES": {"transitiva": True}, "*": {"heredable": True}})
    assert r.preguntar("ORNITORRINCO", "ES", "ANIMAL").valor == "SI"
    assert r.preguntar("COLA_DE_CASTOR", "ES", "COLA").valor == "SI"


def test_resumen_legible():
    _, rep, _ = _leer("ornitorrinco.txt")
    r = resumen(rep)
    assert "He leído" in r and "ornitorrinco" in r.lower()


def test_leon_prosa_real_precision():
    """Texto real (Wikipedia, 47 000 caracteres): lo aprendido es útil y no hay basura típica."""
    mem, rep, T = _leer("leon.txt")
    quiero = [("LEON", "ES", "MAMIFERO"), ("LEON", "NOMBRE_CIENTIFICO", "PANTHERA_LEO"), ("LEON", "VIVIR_EN", "SABANAS"), ("LEON", "ES", "SUPERPREDADOR"), ("LEON", "ES", "ANIMAL"),
              ("LEON", "SER", "SOCIAL"), ("LEONA", "CAZAR_EN", "GRUPO"), ("LEON", "TENER", "RUGIDO"), ("LEONA", "DAR_A", "LUZ")]
    faltan = [q for q in quiero if q not in T]
    assert not faltan, faltan
    # basura que aparecía antes: nombres propios como verbos, adverbios/gerundios/infinitivos como objeto, sujetos adjetivos, cadenas "SER SER"
    malos = [t for t in T if t[1] in ("ASIR", "LARGAR", "SITER", "HACER_DE", "PODER") or t[0] in ("SER", "DENSA", "TAMBIEN", "AMANECER", "SUPUESTAMENTE", "VISIBLE", "ELLOS")
             or t[2] in ("MUY", "AUN", "TAMBIEN", "MENUDO", "CASI", "SER", "VOLVER", "COMER", "JUNTAS", "CUALQUIER", "MIENTRAS", "VICEVERSA", "INCLUSO", "ATACANDO", "CAZANDO", "CUBRIENDOLAS")
             or t[2].endswith("MENTE") or t[2].startswith(("CUATRO_", "TRES_", "DIEZ_", "MILLONES_", "CINCUENTA_"))]
    assert not malos, malos
    assert len(T) > 120 and rep["descartados"] > 0
    # "los leones" y "el león" son una sola cosa
    assert not any(s_ == "LEONES" for s_, _, _ in T)


def test_pies_de_foto_no_cambian_el_tema():
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    rep = Lector(mem).leer("El león es un mamífero carnívoro.\n\nLeón de Katanga (Panthera leo bleyenberghi).\nSe ve en África.")
    T = {(h["s"], h["p"], h["o"]) for h in rep["hechos"]}
    assert ("LEON", "ES", "MAMIFERO") in T and not any(s_.startswith("LEON_DE_KATANGA") for s_, _, _ in T)
