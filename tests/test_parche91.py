"""parche-91: preparacion de textos, cartuchos (insertar/retirar sin restos) y poda."""
import json
import os

from src.language.ingesta import clasificar, comprobar, limpiar, preparar
from src.memory import cartuchos
from src.memory.store import MemoryStore


def test_preparar_texto():
    txt = "# comentario\nEl Sistema Solar\nEl Sol es una estrella (la más cercana). Además, Marte es rojo; Venus es caliente.\n"
    frases, titulos = preparar(txt)
    assert titulos == ["El Sistema Solar"]
    assert frases == ["El Sol es una estrella.", "Marte es rojo.", "Venus es caliente."]


def test_limpiar_conectores_y_parentesis():
    assert limpiar("Sin embargo, la Luna gira (despacio) alrededor de la Tierra.") == "La Luna gira alrededor de la Tierra."
    assert limpiar("también tiene anillos.") == "Tiene anillos."


def test_clasificar():
    assert clasificar("Entendido: MARTE SER ROJO.") == "aprendida"
    assert clasificar("No he entendido «x». ¿Puedes decirlo con una frase más simple?") == "no_entendida"
    assert clasificar("Vale.") == "otra"


class _Conv:
    def say(self, q):
        return "Marte es rojo y tiene dos lunas."


class _Mem:
    display = {"MARTE": "Marte", "ROJO": "rojo", "LUNAS": "dos lunas"}


def test_comprobar_retencion():
    hechos = [{"s": "MARTE", "p": "SER", "o": "ROJO"}, {"s": "MARTE", "p": "TENER", "o": "LUNAS"}, {"s": "MARTE", "p": "SER", "o": "AZUL"}]
    ok, total, fallos = comprobar(_Conv(), _Mem(), hechos)
    assert (ok, total) == (2, 3) and fallos[0][1] == "azul"


def _crear(tmp, nombre, hechos, disp):
    mem = MemoryStore(str(tmp / "tmp.json"))
    snap = cartuchos.instantanea(mem)
    for s, p, o in hechos:
        mem.add_fact((s, p, o), source="texto")
    for k, v in disp.items():
        mem.display[k] = v
    mem.opposites.append(["frio", "caliente"])
    cartuchos.guardar_cartucho(nombre, cartuchos.delta(mem, snap), {"fuente": "t.txt"}, base=str(tmp / "c"))
    cartuchos.insertar(nombre, base=str(tmp / "c"))


def test_cartuchos_insertar_y_retirar_sin_restos(tmp_path):
    base = str(tmp_path / "c")
    _crear(tmp_path, "solar", [("MARTE", "SER", "ROJO")], {"MARTE": "Marte"})
    _crear(tmp_path, "tabla", [("HIERRO", "SER", "METAL")], {"HIERRO": "el hierro"})
    mem = MemoryStore(str(tmp_path / "personal.json"))
    mem.add_fact(("ANA", "VIVIR_EN", "MADRID"))
    mem.add_fact(("MARTE", "SER", "ROJO"))                       # el usuario ya lo habia dicho: su hecho manda
    mem.display["ANA"] = "Ana"
    assert dict(cartuchos.montar(mem, base=base)) == {"solar": 0, "tabla": 1}
    assert mem.display["HIERRO"] == "el hierro" and ["frio", "caliente"] in mem.opposites
    mem.save()                                                    # lo personal se guarda SIN lo de los cartuchos
    data = json.load(open(mem.path, encoding="utf-8"))
    assert [(f["s"], f["o"]) for f in data["facts"]] == [("ANA", "MADRID"), ("MARTE", "ROJO")] and "HIERRO" not in data["display"] and ["frio", "caliente"] not in data["opposites"]
    cartuchos.retirar("tabla", base=base)                         # retirar uno: el otro y lo personal siguen
    cartuchos.montar(mem, base=base)
    assert not any(f["s"] == "HIERRO" for f in mem.facts) and "HIERRO" not in mem.display and ["frio", "caliente"] in mem.opposites
    assert any(f["s"] == "ANA" for f in mem.facts) and mem.display["ANA"] == "Ana"
    cartuchos.retirar("solar", base=base)
    cartuchos.montar(mem, base=base)
    assert ["frio", "caliente"] not in mem.opposites and {f["s"] for f in mem.facts} == {"ANA", "MARTE"}   # lo del usuario no se pierde
    assert [x[:2] for x in cartuchos.listar(base)] == [("solar", False), ("tabla", False)]


def test_poda_simula_y_no_toca_protegidos(tmp_path, monkeypatch):
    from scripts import poda
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "parche-12.py").write_text("x")
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "a.tmp").write_text("x")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x")
    c = [os.path.relpath(p, str(tmp_path)) for p, _ in poda.candidatos(str(tmp_path))]
    assert sorted(c) == ["__pycache__", "parche-12.py"]
