"""Poda segura (parche-91):  python -m scripts.poda            (SIMULA: solo lista lo que sobra y cuanto pesa)
                              python -m scripts.poda --aplicar  (MUEVE lo listado a _poda/<fecha>/ conservando rutas; no borra nada)
Candidatos: caches (__pycache__, .pytest_cache, *.pyc, .DS_Store), copias de parches (.parche_backups), parche-NN.py ya aplicados en la raiz (git guarda su
historia), paquetes zip de la raiz y de reports/, ficheros .tmp y data/autoexamen.tsv (se regenera). NUNCA toca .git, .venv, checkpoints, memory, cartuchos, data ni src.
Haz commit antes de aplicar. Para deshacer: mueve de vuelta lo que hay en _poda/."""
import os
import re
import shutil
import sys
import time

PROTEGIDO = {".git", ".venv", "venv", "checkpoints", "memory", "cartuchos", "src", "tests", "configs", "_poda", "node_modules"}
ROOT = "."


def _size(p):
    if os.path.isfile(p):
        return os.path.getsize(p)
    return sum(os.path.getsize(os.path.join(a, f)) for a, _, fs in os.walk(p) for f in fs if os.path.exists(os.path.join(a, f)))


def candidatos(root=ROOT):
    out = []
    for dirpath, dirs, files in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        top = rel_dir.split(os.sep)[0]
        if top in PROTEGIDO and top != "src" and top != "tests":
            dirs[:] = []
            continue
        for d in list(dirs):
            if d in (".git", ".venv", "venv", "_poda", "checkpoints", "memory", "cartuchos"):
                dirs.remove(d)
            elif d in ("__pycache__", ".pytest_cache", ".parche_backups", ".mypy_cache", ".ruff_cache"):
                out.append((os.path.join(dirpath, d), "cache o copia temporal"))
                dirs.remove(d)
        for f in files:
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, root)
            if f in (".DS_Store",) or f.endswith((".pyc", ".tmp")):
                out.append((p, "temporal"))
            elif os.path.dirname(rel) == "" and re.fullmatch(r"parche-\d+\.py", f):
                out.append((p, "parche ya aplicado (git guarda su historia)"))
            elif f.endswith(".zip") and os.path.dirname(rel) in ("", "reports"):
                out.append((p, "paquete zip (se regenera con scripts.ciclo)"))
            elif rel == os.path.join("data", "autoexamen.tsv"):
                out.append((p, "generado (se regenera)"))
    return sorted(out)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    c = candidatos()
    total = 0
    for p, why in c:
        s = _size(p)
        total += s
        print(f"  {s / 1024:9.1f} KB  {p}   [{why}]")
    print(f"\n{len(c)} elementos, {total / 1024 / 1024:.1f} MB.")
    if "--aplicar" not in argv:
        print("(simulacion: no se ha tocado nada. Para moverlos a _poda/:  python -m scripts.poda --aplicar)")
        return 0
    dest = os.path.join("_poda", time.strftime("%Y%m%d-%H%M%S"))
    for p, _ in c:
        t = os.path.join(dest, os.path.relpath(p, ROOT))
        os.makedirs(os.path.dirname(t), exist_ok=True)
        shutil.move(p, t)
    print(f"Movidos a {dest}. Si todo va bien, puedes borrar _poda/ (y anadirlo a .gitignore).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
