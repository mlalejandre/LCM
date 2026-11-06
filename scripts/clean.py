"""Limpieza del proyecto (parche-40). Por defecto solo MUESTRA lo que haria; con --aplicar lo hace.
Nada se borra a ciegas: lo dudoso se MUEVE a _archivo/<fecha>/ (ignorado por git) y se puede recuperar.
Se borran solo cosas regenerables (__pycache__, .pytest_cache). NO toca: data/, checkpoints/, memory/, src/, tests/.

  python -m scripts.clean              # ver
  python -m scripts.clean --aplicar    # hacer
"""
import datetime
import shutil
import sys
from pathlib import Path

KEEP_BACKUPS = 3
ARCHIVE = ["scripts/learn_book.py", "reports/libro_hechos.txt"]       # abandonados: el objetivo es aprender espanol, no el libro
MOVE_DOCS = {"comoejecutarenservidor.txt": "docs/comoejecutarenservidor.txt"}


def main():
    apply = "--aplicar" in sys.argv
    root = Path.cwd()
    if not (root / "src").is_dir():
        sys.exit("[!] Ejecuta esto desde la raiz del proyecto.")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    arch = root / "_archivo" / stamp
    todo = []
    for d in list(root.rglob("__pycache__")) + list(root.rglob(".pytest_cache")):
        if ".venv" in d.parts or "venv" in d.parts or "_archivo" in d.parts:
            continue
        todo.append(("borrar", d))
    for p in sorted((root / "reports").glob("reproduce_*.log")) + sorted((root / "reports").glob("libro_muestras.txt")):
        todo.append(("archivar", p))
    for rel in ARCHIVE:
        if (root / rel).exists():
            todo.append(("archivar", root / rel))
    for p in sorted((root / "memory").glob("*.tmp")) if (root / "memory").is_dir() else []:
        todo.append(("archivar", p))
    backups = sorted(p for p in (root / ".parche_backups").glob("*") if p.is_dir()) if (root / ".parche_backups").is_dir() else []
    for p in backups[:-KEEP_BACKUPS]:
        todo.append(("archivar", p))
    for src, dst in MOVE_DOCS.items():
        if (root / src).exists() and not (root / dst).exists():
            todo.append(("a docs/", root / src))
    if not todo:
        print("[OK] Nada que limpiar.")
        return
    for action, p in todo:
        print(f"  {action:9s} {p.relative_to(root)}")
        if not apply:
            continue
        if action == "borrar":
            shutil.rmtree(p, ignore_errors=True)
        elif action == "a docs/":
            (root / "docs").mkdir(exist_ok=True)
            shutil.move(str(p), str(root / MOVE_DOCS[p.name]))
        else:
            dest = arch / p.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(dest))
    print(f"\n[{'HECHO' if apply else 'ENSAYO'}] {len(todo)} elementos." +
          ("" if apply else "  Repite con --aplicar para hacerlo."))


if __name__ == "__main__":
    main()
