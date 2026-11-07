"""parche-112: razonador general (reglas y propiedades como datos), verificador independiente, banco de razonamiento y cartuchos razon_*."""
import copy
import json
import os
import tempfile

from scripts import razonar_bench as B
from src.language.qa import QA
from src.memory import cartuchos
from src.memory.store import MemoryStore
from src.reasoning.razonador import Prueba, Razonador, Verificador, explicar

H = [("ANA", "PADRE_DE", "LUIS"), ("LUIS", "PADRE_DE", "PEDRO"), ("PEDRO", "PADRE_DE", "MARTA"), ("MAMIFERO", "ES", "ANIMAL"), ("PERRO", "ES", "MAMIFERO"), ("REX", "ES", "PERRO"),
     ("MAMIFERO", "TIENE", "PELO"), ("AVE", "VUELA", "SI"), ("PINGUINO", "ES", "AVE"), ("PAKO", "ES", "PINGUINO"), ("A", "ALTURA", "5"), ("B", "ALTURA", "9")]
P = {"ES": {"transitiva": True}, "*": {"heredable": True}, "PADRE_DE": {"inversa": "HIJO_DE", "subprop": "ANTEPASADO_DE"}, "ANTEPASADO_DE": {"transitiva": True, "asimetrica": True},
     "MAS_ALTO": {"compara": {"atributo": "ALTURA", "op": ">"}}}
R = [{"id": "abuelo", "si": [["?X", "PADRE_DE", "?Y"], ["?Y", "PADRE_DE", "?Z"]], "entonces": ["?X", "ABUELO_DE", "?Z"]}]
NEG = [("PINGUINO", "VUELA", "SI")]


def _rz():
    return Razonador(H, R, P, NEG), Verificador(H, R, P, NEG)


def test_si_no_desconocido_con_prueba_valida():
    r, v = _rz()
    for q, esp in [(("ANA", "ABUELO_DE", "PEDRO"), "SI"), (("REX", "ES", "ANIMAL"), "SI"), (("REX", "TIENE", "PELO"), "SI"), (("PAKO", "VUELA", "SI"), "NO"),
                   (("MARTA", "ANTEPASADO_DE", "ANA"), "NO"), (("A", "MAS_ALTO", "B"), "NO"), (("B", "MAS_ALTO", "A"), "SI"), (("REX", "TIENE", "ALAS"), "DESCONOCIDO"),
                   (("ANA", "ABUELO_DE", "MARTA"), "DESCONOCIDO")]:
        x = r.preguntar(*q)
        assert x.valor == esp, (q, x.valor)
        if esp != "DESCONOCIDO":
            assert v.ok(x.prueba)[0], q


def test_excepcion_gana_a_la_regla_general_y_el_verificador_la_exige():
    r, v = _rz()
    x = r.preguntar("PAKO", "VUELA", "SI")
    assert x.valor == "NO" and x.prueba.regla == "herencia_neg" and v.ok(x.prueba)[0]


def test_verificador_rechaza_pruebas_falsas():
    r, v = _rz()
    x = r.preguntar("ANA", "ABUELO_DE", "PEDRO")
    malo = Prueba.de_dict(x.prueba.a_dict())
    malo.hijos[0].atomo = ("ANA", "PADRE_DE", "MARTA")
    assert not v.ok(malo)[0]
    inventado = Prueba(("ANA", "PADRE_DE", "MARTA"), "hecho")
    assert not v.ok(inventado)[0]
    cadena = r.preguntar("REX", "ES", "ANIMAL").prueba
    roto = Prueba.de_dict(cadena.a_dict())
    roto.hijos[0].atomo = ("OTRO", "ES", "PERRO")
    assert not v.ok(roto)[0]


def test_consultar_contar_extremo_ruta_y_explicar():
    r, _ = _rz()
    assert [c["s"] for c in r.consultar(None, "ABUELO_DE", "PEDRO")] == ["ANA"]
    assert r.contar("ANA", "ANTEPASADO_DE", None) == 3
    assert r.extremo("ALTURA")["entidad"] == "B"
    assert len(r.ruta("ANA", "MARTA", "ANTEPASADO_DE").hijos) == 3
    txt = r.explicar(r.preguntar("ANA", "ABUELO_DE", "PEDRO"))
    assert "regla abuelo" in txt and txt.startswith("1.")


def test_ciclos_y_presupuesto_no_cuelgan():
    h = [("A", "VA_A", "B"), ("B", "VA_A", "C"), ("C", "VA_A", "A")]
    r = Razonador(h, [{"id": "x", "si": [["?X", "R", "?Y"], ["?Y", "R", "?X"]], "entonces": ["?X", "R", "?Y"]}], {"VA_A": {"transitiva": True}})
    assert r.preguntar("A", "VA_A", "C").valor == "SI" and r.preguntar("A", "VA_A", "Z").valor == "DESCONOCIDO"
    pobre = Razonador(h, [], {"VA_A": {"transitiva": True}}, presupuesto=1)
    assert pobre.preguntar("A", "VA_A", "Z").valor in ("DESCONOCIDO", "SI")


def test_banco_de_razonamiento_umbrales():
    res = B.ejecutar(semilla=7, n=40, k=12)
    g = res["global"]
    assert g["n"] > 400 and all(res["por_dominio"][d] for d in B.DOMINIOS) and all(res["por_nivel"][n] for n in range(1, 9))
    assert g["exactitud"] >= .97 and g["prueba_valida"] >= .99 and g["falsa_certeza"] <= .005, B.texto(res)


def test_cartucho_con_reglas_y_propiedades_se_monta_y_se_desmonta():
    d = tempfile.mkdtemp()
    json.dump({"hechos": [], "reglas": R, "propiedades": {"X_ES": {"transitiva": True}}}, open(os.path.join(d, "razon_t.json"), "w"))
    mem = MemoryStore(os.path.join(d, "m.json"))
    cartuchos.insertar("razon_t", d)
    cartuchos.montar(mem, d)
    assert any(r["id"] == "abuelo" for r in mem.reglas) and "X_ES" in mem.propiedades
    cartuchos.desmontar(mem, "razon_t")
    assert not mem.reglas and "X_ES" not in mem.propiedades


def test_qa_razona_cuando_la_memoria_no_sabe():
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "m.json"))
    mem.reglas, mem.propiedades = copy.deepcopy(R), copy.deepcopy(P)
    for f in H:
        mem.add_fact(f, source="t")
    qa = QA.__new__(QA)
    qa.m = mem
    v = qa.razonar("REX", "ES", "ANIMAL")
    assert v and v[0] == "SI" and "perro" in v[1].lower()
    assert qa.razonar("REX", "TIENE", "ALAS") is None


def test_base_de_reglas_trae_parentesco_y_clases():
    from scripts.construir_razonamiento import PROPIEDADES, REGLAS
    h = [("ANA", "PADRE_DE", "LUIS"), ("LUIS", "PADRE_DE", "PEDRO"), ("LUIS", "PADRE_DE", "JUAN"), ("ALA_X", "ES", "ALA"), ("ALA", "PARTE_DE", "AVE")]
    r = Razonador(h, REGLAS, PROPIEDADES)
    assert r.preguntar("ANA", "ABUELO_DE", "PEDRO").valor == "SI" and r.preguntar("PEDRO", "HERMANO_DE", "JUAN").valor == "SI"
    assert r.preguntar("ALA_X", "PARTE_DE", "AVE").valor == "SI"
