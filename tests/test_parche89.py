"""parche-89: el autoexamen es determinista y esta bien formado."""
from scripts.autoexamen import generar


def test_autoexamen_determinista_y_bien_formado():
    a, ta = generar(3, 5)
    b, tb = generar(3, 5)
    assert a == b and ta == tb
    assert generar(3, 6)[0] != a
    assert any(l.startswith("U: ") and "\t" in l for l in a.splitlines())
    assert set(ta.values()) >= {"compra_que", "vive_donde", "aritmetica", "comparar"}


def test_aritmetica_esperada_coincide_con_la_habilidad():
    from src.language import skills
    import re
    txt, tags = generar(6, 9)
    for turn, tag in tags.items():
        if tag == "aritmetica":
            exp = [l for l in txt.splitlines() if l.startswith("U: " + turn + "\t")][0].split("\t")[1]
            nums = [int(x) for x in re.findall(r"\d+", turn)]
            assert str(nums[0] * nums[1]) == exp
