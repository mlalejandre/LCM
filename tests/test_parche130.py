"""parche-130: el coste por pregunta deja de crecer con el cuadrado de la memoria.

(1) src/reasoning/lessons.py: la deduccion indexa los hechos por predicado y por (predicado, sujeto) en vez de recorrer toda la memoria en cada premisa.
(2) src/language/marcos.py: la clave normalizada de cada nombre se calcula una sola vez y los hechos se buscan por sujeto.

La mejora NO puede cambiar ni una respuesta: estas pruebas comparan, con hechos al azar, el resultado nuevo con la implementacion anterior copiada tal cual."""
import random
from types import SimpleNamespace

import pytest

from src.language import marcos
from src.reasoning import lessons as L


# ---- la implementacion ANTERIOR, copiada tal cual, como referencia ---------------------------------------------------------
def _matches_ref(prem, known, bind, used):
    if not prem:
        yield dict(bind), list(used)
        return
    s, p, o = prem[0]
    for f in known:
        if f[1] != p:
            continue
        new, ok = dict(bind), True
        for term, val in ((s, f[0]), (o, f[2])):
            if term.startswith("?"):
                if term in new:
                    ok &= new[term] == val
                else:
                    ok &= val not in new.values()
                    new[term] = val
            else:
                ok &= term == val
            if not ok:
                break
        if ok:
            yield from _matches_ref(prem[1:], known, new, used + [f])


def _apply_ref(facts, lessons, is_var=lambda n: True, rounds=3, cap=200, defaults=True):
    known = {tuple(x.upper() for x in f) for f in facts}
    rules = [L.generalize(l, is_var) for l in list(lessons) + (L.DEFAULT_LESSONS if defaults else []) if not l.get("archived")]
    derived = {}
    for _ in range(rounds):
        new = {}
        for prem, concl in rules:
            for bind, used in _matches_ref(prem, sorted(known), {}, []):
                out = tuple(bind.get(x, x) for x in concl)
                if any(x.startswith("?") for x in out) or out in known or out in derived or out in new:
                    continue
                new[out] = used
        if not new:
            break
        derived.update(new)
        known |= set(new)
        if len(derived) >= cap:
            break
    return derived


PREDS = ["ES", "PARTE_DE", "TENER", "MADRE_DE", "HIJO_DE", "VIVE_EN"]
LECCIONES = [
    {"premises": [["a", "MADRE_DE", "b"]], "conclusion": ["b", "HIJO_DE", "a"], "archived": False},
    {"premises": [["a", "VIVE_EN", "b"], ["b", "PARTE_DE", "c"]], "conclusion": ["a", "VIVE_EN", "c"], "archived": False},
    {"premises": [["a", "TENER", "b"], ["b", "ES", "c"], ["a", "ES", "d"]], "conclusion": ["a", "TENER", "c"], "archived": False},
]


def _hechos(rng, n, ents):
    out = set()
    while len(out) < n:
        out.add((rng.choice(ents), rng.choice(PREDS), rng.choice(ents)))
    return sorted(out)


@pytest.mark.parametrize("semilla", range(12))
def test_deduccion_indexada_igual_que_la_anterior(semilla):
    rng = random.Random(semilla)
    ents = [f"E{i}" for i in range(rng.choice([5, 9, 14]))]
    hechos = _hechos(rng, rng.choice([8, 20, 45]), ents)
    nuevo = L.apply_lessons(hechos, LECCIONES)
    viejo = _apply_ref(hechos, LECCIONES)
    assert list(nuevo.items()) == list(viejo.items())                      # mismas conclusiones, mismos hechos de apoyo y MISMO orden


def test_deduccion_con_variables_marcadas_y_reglas_por_defecto():
    hechos = [("A", "ES", "B"), ("B", "ES", "C"), ("C", "ES", "D"), ("X", "PARTE_DE", "Y"), ("Y", "PARTE_DE", "Z")]
    nuevo = L.apply_lessons(hechos, [])
    assert list(nuevo.items()) == list(_apply_ref(hechos, []).items())
    assert ("A", "ES", "D") in nuevo and ("X", "PARTE_DE", "Z") in nuevo and ("Y", "TENER", "X") in nuevo
    sin = L.apply_lessons(hechos, [], defaults=False)
    assert sin == {} and _apply_ref(hechos, [], defaults=False) == {}


def test_deduce_all_no_cambia():
    hechos = [("PERRO", "ES", "MAMIFERO"), ("REX", "ES", "PERRO"), ("MAMIFERO", "ES", "ANIMAL"), ("PERRO", "TENER", "PATAS")]
    out = L.deduce_all(hechos, [])
    assert ("REX", "ES", "MAMIFERO") in out and ("REX", "ES", "ANIMAL") in out and ("REX", "TENER", "PATAS") in out


def test_indice_conserva_el_orden_de_los_hechos():
    ind = L._Indice(sorted([("B", "ES", "C"), ("A", "ES", "B"), ("A", "TENER", "X"), ("A", "ES", "Z")]))
    assert ind.candidatos("ES", "A", False) == [("A", "ES", "B"), ("A", "ES", "Z")]
    assert ind.candidatos("ES", None, True) == [("A", "ES", "B"), ("A", "ES", "Z"), ("B", "ES", "C")]
    assert list(ind.candidatos("NO", "A", False)) == []


# ---- marcos -----------------------------------------------------------------------------------------------------------------
def _marcos(hechos):
    qa = SimpleNamespace(m=SimpleNamespace(facts=hechos), say=lambda t, neg=False: " ".join(t))
    return marcos.Marcos(qa)


def test_marcos_of_igual_que_la_busqueda_lineal():
    rng = random.Random(7)
    nombres = ["Mercurio", "la Tierra", "SISTEMA_SOLAR", "Plutón", "dos lunas", "Júpiter", "anillos", "planeta rojo", "Los planetas"]
    hechos = [{"s": rng.choice(nombres), "p": rng.choice(["ES", "TENER", "SER_EL_TERCERO", "GIRAR_ALREDEDOR_DE", "HECHO_DE"]), "o": rng.choice(nombres)} for _ in range(120)]
    hechos.append({"s": "Marte", "p": "ES", "o": "planeta", "neg": True})
    mc = _marcos(hechos)
    for sk in {mc.key(f["s"]) for f in mc.facts} | {"nada"}:
        for kind in (None, "ser", "estar", "tener", "giro", "cont"):
            esperado = [f for f in mc.facts if mc.key(f["s"]) == sk and (kind is None or marcos._fam(f["p"], kind))]
            assert mc.of(sk, kind) == esperado
    assert all(not f.get("neg") for f in mc.facts)


def test_marcos_clave_y_palabras_memoizadas_dan_lo_mismo():
    assert marcos._clave("Los_PLANETAS Rojos") == " ".join(marcos.st(w) for w in marcos.norm("Los PLANETAS Rojos").split())
    f = {"s": "Mercurio", "p": "SER_EL_MAS_CERCANO_A", "o": "el Sol"}
    mc = _marcos([f])
    assert mc.fw(f) == {marcos.st(w) for w in ("el", "sol", "mas", "cercano", "a")}
    assert marcos._palabras("el Sol", "ES") == {marcos.st(w) for w in marcos.norm("el Sol").split()}


# ---- scripts.recursos ---------------------------------------------------------------------------------------------------------
def test_recursos_energia_y_formato():
    from scripts import recursos
    assert recursos.energia_wh(3600, 15) == 15.0                           # 1 hora de CPU a 15 W = 15 Wh
    assert abs(recursos.energia_wh(0.04, 15) - 0.04 * 15 / 3600) < 1e-12
    assert recursos.miles(3526419) == "3.526.419" and recursos.miles(0) == "0"
    assert recursos.mediana([5, 1, 9]) == 5 and recursos.mediana([]) == 0
    assert all(0 < wh < 1 for wh in recursos.LLM_WH.values())


def test_recursos_se_importa_sin_arrancar_nada():
    import importlib
    m = importlib.import_module("scripts.recursos")
    assert callable(m.main) and len(m.PREGUNTAS) >= 10
