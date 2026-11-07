"""Empaqueta el proyecto en UN txt para pasarmelo en otra conversacion, gastando los menos tokens posibles.

Uso (desde la raiz del proyecto):
    python exportar.py                 # modo normal: codigo fuente + tests + informe actual (lo necesario para seguir trabajando)
    python exportar.py --cambios       # solo los archivos modificados segun git (git status) + informe: lo mas barato entre parches
    python exportar.py --sin-tests     # normal pero sin tests/
    python exportar.py --todo          # como antes (casi todo), por si hace falta
    python exportar.py --max-kb 200    # corta archivos de texto mas grandes que esto (por defecto 150)

Que se queda fuera SIEMPRE (no aporta o se regenera): entornos, git, caches, copias de seguridad de parches, pesos/datos/checkpoints,
volcados antiguos, el manifiesto de reproducibilidad, arboles grabados, LCM_construir_desde_cero.py (copia duplicada del proyecto),
paquetes/zip, binarios y .DS_Store. El arbol de directorios se limita a carpetas de codigo.
"""
import argparse
import os
import subprocess
from pathlib import Path

OUTPUT_FILE = "LCM_PROYECTO_COMPLETO.txt"

# carpetas que nunca se recorren
IGNORED_DIRS = {".venv", "venv", "__pycache__", ".git", ".github", "checkpoints", "data", ".parche_backups", ".ciclo_backups",
                ".pytest_cache", "node_modules", "reproducibilidad", "docs"}
IGNORED_EXTS = {".pt", ".pth", ".pkl", ".pyc", ".npy", ".npz", ".zip", ".gz", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".conllu", ".tsv"}
IGNORED_NAMES = {OUTPUT_FILE, ".DS_Store", "expandir.py", "exportar.py", "LCM_construir_desde_cero.py", "manifiesto.json", "LICENSE",
                 ".gitignore", "historial.json", "arboles.json", "paquete.zip", "replay_informe.txt", "requirements.txt"}
# de reports/ solo lo que informa del estado actual
REPORTS_OK = {"informe.txt", "ciclo.txt"}
# archivos de la raiz que si interesan (documentacion corta de estado)
ROOT_OK = {"README.md", "LCM_EVOLUCION.md", "Makefile", "conftest.py", "parche.py"}


def _git_cambiados(root: Path):
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True).stdout
    except Exception:
        return None
    files = []
    for line in out.splitlines():
        p = line[3:].split(" -> ")[-1].strip().strip('"')
        if p.endswith("/"):
            files += [str(f.relative_to(root)) for f in (root / p).rglob("*") if f.is_file()]
        else:
            files.append(p)
    return files


def _incluir(rel: Path, args) -> bool:
    parts = rel.parts
    if any(p in IGNORED_DIRS for p in parts[:-1]) or rel.name in IGNORED_NAMES or rel.suffix in IGNORED_EXTS:
        return False
    if args.todo:
        return True
    if parts[0] == "reports":
        return rel.name in REPORTS_OK
    if parts[0] == "tests":
        return not args.sin_tests
    if len(parts) == 1:
        return rel.suffix == ".py" and rel.name not in ("limpieza.py",) or rel.name in ROOT_OK
    return parts[0] in ("src", "scripts", "configs") and rel.suffix in (".py", ".json", ".yaml", ".yml", ".md", ".txt", ".cfg", ".toml")


def _tree(root: Path, files):
    dirs = sorted({str(p.parent) for p in files if str(p.parent) != "."})
    lines = [root.name]
    lines += [f"  {d}/" for d in dirs]
    lines.append(f"  ({len(files)} archivos)")
    return lines


def export():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cambios", action="store_true")
    ap.add_argument("--sin-tests", action="store_true")
    ap.add_argument("--todo", action="store_true")
    ap.add_argument("--max-kb", type=int, default=150)
    args = ap.parse_args()
    root = Path.cwd()

    if args.cambios:
        ch = _git_cambiados(root)
        if ch is None:
            print("[!] git no disponible: uso el modo normal.")
            args.cambios = False
        else:
            cand = [Path(p) for p in ch if (root / p).is_file()]
            files = [p for p in cand if _incluir(p, args)]
            for r in REPORTS_OK:                       # el informe siempre acompana
                if (root / "reports" / r).is_file() and Path("reports") / r not in files:
                    files.append(Path("reports") / r)
    if not args.cambios:
        files = []
        for d, dirs, names in os.walk(root):
            dirs[:] = [x for x in dirs if x not in IGNORED_DIRS]
            for n in names:
                rel = (Path(d) / n).relative_to(root)
                if _incluir(rel, args):
                    files.append(rel)
    files = sorted(set(files))

    out = ["=" * 60, " LCM - proyecto (" + ("solo cambios" if args.cambios else "todo" if args.todo else "normal") + ")", "=" * 60]
    out += _tree(root, files)
    count, cut = 0, 0
    for rel in files:
        fp = root / rel
        try:
            txt = fp.read_text(encoding="utf-8")
        except Exception:
            continue                                    # binarios / no utf-8: fuera
        if len(txt) > args.max_kb * 1024:
            txt = txt[: args.max_kb * 1024] + f"\n[... recortado a {args.max_kb} KB ...]"
            cut += 1
        out.append(f"\n##### {rel}\n{txt.rstrip()}")
        count += 1

    out_path = root / OUTPUT_FILE
    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    kb = out_path.stat().st_size / 1024
    print(f"[+] {count} archivos en {OUTPUT_FILE} ({kb:.0f} KB, ~{int(kb * 1024 / 3.5 / 1000)}k tokens aprox.)" + (f"; {cut} recortados" if cut else ""))


if __name__ == "__main__":
    export()