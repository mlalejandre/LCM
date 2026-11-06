import os
from pathlib import Path

OUTPUT_FILE = "LCM_PROYECTO_COMPLETO.txt"
IGNORED_DIRS = {".venv", "venv", "__pycache__", ".git", "checkpoints", "data"}
IGNORED_EXTS = {".pt", ".pkl", ".pyc", ".DS_Store"}

def build_tree(dir_path: Path, prefix: str = "") -> list:
    lines = []
    items = sorted([p for p in dir_path.iterdir() if p.name not in IGNORED_DIRS])
    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{item.name}")
        if item.is_dir():
            sub_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(build_tree(item, sub_prefix))
    return lines

def export():
    root = Path.cwd()
    print(f"[*] Empaquetando proyecto desde: {root}")

    out = []
    out.append("=" * 80)
    out.append(" PROYECTO LARGE CONCEPTUAL MODEL (LCM) - ARQUITECTURA Y FUENTE")
    out.append("=" * 80)
    out.append("\nARBOL DE DIRECTORIOS:")
    out.append(root.name)
    out.extend(build_tree(root))
    out.append("\n" + "=" * 80 + "\n")

    count = 0
    for root_dir, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for fname in sorted(filenames):
            fp = Path(root_dir) / fname
            if fp.suffix in IGNORED_EXTS or fname in [OUTPUT_FILE, "expandir.py"]:
                continue
            rel = fp.relative_to(root)
            out.append("\n" + "=" * 80)
            out.append(f"ARCHIVO: {rel}")
            out.append("=" * 80 + "\n")
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    out.append(f.read())
                count += 1
            except Exception as e:
                out.append(f"[Error de lectura: {e}]")

    out_path = root / OUTPUT_FILE
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print(f"[+] {count} archivos empaquetados en: {OUTPUT_FILE}")
    print(f"[+] Peso total: {out_path.stat().st_size / 1024:.2f} KB")

if __name__ == "__main__":
    export()
