from src.language.qa import QA, is_question, rewrite, same_pred
from src.memory.store import MemoryStore


def stub(table):
    def parse(sentence):
        return table.get(sentence)
    return parse


def mem(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("marta", "escribir", "novela"))
    m.note_surface(("marta", "escribir", "novela"), "{s} escribió {o}", "Marta", "una novela")
    m.add_fact(("pedro", "vivir_en", "madrid"))
    m.note_surface(("pedro", "vivir_en", "madrid"), "{s} vive en {o}", "Pedro", "Madrid")
    m.add_fact(("luis", "comer", "carne"), neg=True)
    m.note_surface(("luis", "comer", "carne"), "{s} come {o}", "Luis", "carne")
    return m


def t(s, p, o, neg=False):
    return {"s": s, "p": p, "o": o, "neg": neg}


def test_is_question():
    assert is_question("¿Quién vive en Madrid?") and is_question("Vive Pedro en Madrid?")
    assert not is_question("Pedro vive en Madrid.")


def test_rewrite_kinds():
    assert rewrite("¿Quién escribió una novela?")[0][0] == "Xqx escribió una novela."
    assert rewrite("¿Qué escribió Marta?")[0][-1] == "Marta escribió Xqx."
    assert rewrite("¿A quién llamó Pedro?")[0][0] == "Pedro llamó a Xqx."
    c, k = rewrite("¿Vive Pedro en Madrid?")
    assert k == "si_no" and "Pedro vive en Madrid." in c


def test_same_pred():
    assert same_pred("escribir", "escribio") and same_pred("vivir_en", "VIVIR_EN")
    assert not same_pred("vivir_en", "vivir_con") and same_pred("conocer_a", "conocer")


def test_answers(tmp_path):
    m = mem(tmp_path)
    parse = stub({
        "Xqx escribió una novela.": [t("xqx", "escribir", "novela")],
        "Marta escribió Xqx.": [t("marta", "escribir", "xqx")],
        "Pedro vive en Madrid.": [t("pedro", "vivir_en", "madrid")],
        "Luis come carne.": [t("luis", "comer", "carne")],
        "Pedro vive en Sevilla.": [t("pedro", "vivir_en", "sevilla")],
        "Ana vive en Madrid.": [t("ana", "vivir_en", "madrid")],
    })
    qa = QA(m, parse)
    assert "Marta escribió una novela" in qa.answer("¿Quién escribió una novela?")
    assert "una novela" in qa.answer("¿Qué escribió Marta?")
    assert qa.answer("¿Pedro vive en Madrid?").startswith("Sí")
    assert qa.answer("¿Luis come carne?").startswith("No.")
    assert "No lo sé" in qa.answer("¿Ana vive en Madrid?") or "no me consta" in qa.answer("¿Ana vive en Madrid?")
    assert "No he entendido" in qa.answer("¿Cosa rara?")


def test_deduction_is_labelled(tmp_path):
    m = mem(tmp_path)
    parse = stub({"Pedro vive en Sevilla.": [t("pedro", "vivir_en", "sevilla")]})
    qa = QA(m, parse, deduce=lambda facts: {("PEDRO", "VIVIR_EN", "SEVILLA")})
    assert "deduzco" in qa.answer("¿Pedro vive en Sevilla?")


def test_memory_roundtrip(tmp_path):
    m = mem(tmp_path)
    m.save()
    m2 = MemoryStore(str(tmp_path / "m.json"))
    assert m2.surface["ESCRIBIR"] == "{s} escribió {o}" and m2.display["MARTA"] == "Marta"


def test_irregular_lemma_rescued_by_surface_form(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("perro", "muerder_a", "cartero"))
    m.note_surface(("perro", "muerder_a", "cartero"), "{s} muerde a {o}", "el perro", "el cartero")
    q = {"s": "xqx", "p": "mendar_a", "o": "cartero", "neg": False, "template": "{s} muerde a {o}"}
    qa = QA(m, lambda x: [q] if x.startswith("Xqx") else None)
    assert "perro" in qa.answer("¿Quién muerde al cartero?")


def test_yesno_with_article_and_alternative_hole(tmp_path):
    c, k = rewrite("¿Enseña la maestra matemáticas?")
    assert "la maestra enseña matemáticas." in c
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("rosa", "leer", "libro"))
    m.note_surface(("rosa", "leer", "libro"), "{s} lee {o}", "Rosa", "un libro")
    qa = QA(m, lambda x: [t("rosa", "leer", "zurita")] if x == "Rosa lee Zurita." else None)    # Xqx no se lee, Zurita si
    assert "libro" in qa.answer("¿Qué lee Rosa?")


def test_lessons_deduction():
    from src.reasoning.lessons import apply_lessons
    lesson = {"premises": [["ANA", "MADRE_DE", "LUIS"]], "conclusion": ["LUIS", "HIJO_DE", "ANA"], "archived": False}
    d = apply_lessons([("MARTA", "MADRE_DE", "PABLO")], [lesson])
    assert d == {("PABLO", "HIJO_DE", "MARTA"): [("MARTA", "MADRE_DE", "PABLO")]}
    assert apply_lessons([("PABLO", "HIJO_DE", "MARTA")], [lesson]) == {}          # no al reves
    two = {"premises": [["A", "PADRE_DE", "B"], ["B", "PADRE_DE", "C"]], "conclusion": ["A", "ABUELO_DE", "C"]}
    assert ("X", "ABUELO_DE", "Z") in apply_lessons([("X", "PADRE_DE", "Y"), ("Y", "PADRE_DE", "Z")], [two])


def test_yesno_prefers_reading_that_memory_recognises(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("marta", "madre_de", "pablo"))
    table = {"Es Marta madre de Pablo.": [t("marta", "es", "madre")], "Marta es madre de Pablo.": [t("marta", "madre_de", "pablo")]}
    assert QA(m, lambda x: table.get(x)).answer("¿Es Marta madre de Pablo?").startswith("Sí")


def test_template_from_sentence_and_names():
    from src.language.qa import template_from
    assert template_from("Luis es hijo de Ana", "LUIS", "ANA") == ("{s} es hijo de {o}", "Luis", "Ana")
    assert template_from("Pedro compró un coche", "PEDRO", "COCHE") == ("{s} compró un {o}", "Pedro", "coche")
    assert template_from("Ana es Ana", "ANA", "ANA") is None


def test_default_verbalisation_capitalised(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("marta", "madre_de", "pablo"))
    assert QA(m, lambda x: None).say(("PABLO", "HIJO_DE", "MARTA")).startswith("Pablo")


def test_time_expressions_extract_and_answer(tmp_path):
    from src.language.extract import triples_full, surface
    T = [("Pedro", "PROPN", 2, "nsubj", "pedro"), ("compró", "VERB", 0, "root", "comprar"), ("pan", "NOUN", 2, "obj", "pan"),
         ("ayer", "ADV", 2, "advmod", "ayer"), (".", "PUNCT", 2, "punct", ".")]
    (tr,) = triples_full(T, entities_only=True)
    assert (tr["s"], tr["p"], tr["o"], tr["when"], tr["when_disp"]) == ("pedro", "comprar", "pan", "ayer", "ayer")
    assert surface(T, tr)["template"] == "{s} compró {o}"
    # "en enero" no es un lugar: no genera comprar_en
    T2 = [("Luis", "PROPN", 2, "nsubj", "luis"), ("visitó", "VERB", 0, "root", "visitar"), ("Roma", "PROPN", 2, "obj", "roma"),
          ("en", "ADP", 5, "case", "en"), ("enero", "NOUN", 2, "obl", "enero"), (".", "PUNCT", 2, "punct", ".")]
    found = triples_full(T2, entities_only=True)
    assert [(t["p"], t["when"]) for t in found] == [("visitar", "enero")]
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("pedro", "comprar", "pan"), when="ayer", when_disp="ayer")
    m.note_surface(("pedro", "comprar", "pan"), "{s} compró {o}", "Pedro", "pan")
    table = {"Pedro compró pan.": [t("pedro", "comprar", "pan")],
             "Pedro compró pan ayer.": [dict(t("pedro", "comprar", "pan"), when="ayer")],
             "Pedro compró pan hoy.": [dict(t("pedro", "comprar", "pan"), when="hoy")]}
    qa = QA(m, lambda x: table.get(x))
    assert "ayer" in qa.answer("¿Cuándo compró Pedro pan?")
    assert qa.answer("¿Compró Pedro pan ayer?").startswith("Sí")
    assert qa.answer("¿Compró Pedro pan hoy?").startswith("No.")


def test_canon_plural():
    from src.reasoning.lessons import canon
    assert canon("POLIGONOS") == canon("POLIGONO") == "POLIGONO"
    assert canon("ANIMALES") == "ANIMAL"


def test_inherit_down_chain_not_up():
    from src.reasoning.lessons import inherit
    f = [("POLIGONOS", "TENER", "LADOS"), ("TRIANGULO", "ES", "POLIGONO"), ("POLIGONO", "ES", "FIGURA")]
    got = inherit(f)
    assert ("TRIANGULO", "TENER", "LADOS") in got
    assert ("FIGURA", "TENER", "LADOS") not in got
