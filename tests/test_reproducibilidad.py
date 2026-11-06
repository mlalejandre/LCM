import os
import subprocess
import sys

from scripts.manifiesto import sha, tracked


def test_huellas_estables(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hola", encoding="utf-8")
    assert sha(str(f)) == sha(str(f)) and len(sha(str(f))) == 64


def test_se_vigila_el_codigo_y_no_los_pesos():
    files = tracked()
    assert "src/language/qa.py" in files and "data/semilla.txt" in files
    assert not any(f.startswith("checkpoints/") or f.endswith((".pkl", ".pt")) or f.startswith("data/ud/") for f in files)


def test_empaquetado_ida_y_vuelta(tmp_path):
    out = tmp_path / "todo.py"
    r = subprocess.run([sys.executable, "-m", "scripts.empaquetar_todo", "--salida", str(out)], capture_output=True, text=True, cwd=os.getcwd())
    assert r.returncode == 0, r.stderr
    dest = tmp_path / "nuevo"
    dest.mkdir()
    r = subprocess.run([sys.executable, str(out)], capture_output=True, text=True, cwd=dest)
    assert r.returncode == 0, r.stderr
    for f in ("src/language/qa.py", "data/semilla.txt", "scripts/reproduce.py", "tests/test_nucleo.py"):
        assert (dest / f).read_text(encoding="utf-8") == open(f, encoding="utf-8").read()


def test_el_constructor_trae_el_menu(tmp_path):
    out = tmp_path / "todo.py"
    subprocess.run([sys.executable, "-m", "scripts.empaquetar_todo", "--salida", str(out)], check=True, capture_output=True)
    src = out.read_text(encoding="utf-8")
    assert "def menu()" in src and "--sin-menu" in src and "--todo" in src
    r = subprocess.run([sys.executable, str(out), "--sin-menu"], capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0 and (tmp_path / "src" / "language" / "qa.py").exists()


def test_limpieza_se_empaqueta_y_compila():
    assert "limpieza.py" in tracked()
    compile(open("limpieza.py", encoding="utf-8").read(), "limpieza.py", "exec")
