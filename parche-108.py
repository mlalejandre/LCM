"""parche-108: inserta los cartuchos mundo_* (del parche-107) en cartuchos/activos.json para que el LCM los use y la interfaz los muestre. Se retiran desde la interfaz (Cartuchos). Uso: python -m scripts.ciclo parche-108.py"""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
import base64, json, zlib
ALL_EDITS = []
NEW_FILES = {}
SOFT = []
BLOB = ""

def main(root: Path = ROOT) -> int:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    bk = root / ".parche_backups" / stamp
    texts, changed = {}, set()
    for rel, old, new, marca in ALL_EDITS:                              # comprobar TODO antes de escribir nada
        p = root / rel
        if not p.is_file():
            print(f"FALTA {rel}: no se toca nada."); return 1
        txt = texts[rel] if rel in texts else p.read_text(encoding="utf-8")
        if marca in txt:
            texts[rel] = txt; continue
        if txt.count(old) != 1:
            print(f"ERROR {rel}: un trozo a cambiar aparece {txt.count(old)} veces (debe ser 1): {old[:70]!r}. No se toca nada."); return 1
        texts[rel] = txt.replace(old, new); changed.add(rel)
    plan = [(root / rel, rel, texts[rel]) for rel in sorted(changed)]
    pa = root / "cartuchos" / "activos.json"
    try:
        actuales = json.loads(pa.read_text(encoding="utf-8")) if pa.exists() else []
    except ValueError:
        actuales = []
    mundo = sorted(p.stem for p in (root / "cartuchos").glob("mundo_*.json"))
    if not mundo:
        print("No hay cartuchos mundo_*: aplica antes el parche-107."); return 1
    nuevos = [m for m in mundo if m not in actuales]
    if nuevos:
        pa.parent.mkdir(parents=True, exist_ok=True)
        if pa.exists():
            (bk / "cartuchos").mkdir(parents=True, exist_ok=True); shutil.copy2(pa, bk / "cartuchos" / "activos.json")
        pa.write_text(json.dumps(actuales + nuevos, ensure_ascii=False, indent=1), encoding="utf-8"); print(f"  insertados {len(nuevos)} cartuchos: " + ", ".join(nuevos))
    for rel, content in NEW_FILES.items():
        p = root / rel
        if not p.exists() or p.read_text(encoding="utf-8") != content:
            plan.append((p, rel, content))
    for p, rel, txt in plan:
        if p.exists():
            (bk / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, bk / rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
        if rel.endswith(".py"):
            py_compile.compile(str(p), doraise=True)
        print(f"  escrito {rel}")

    for rel, marca, bloque, antes in SOFT:                              # documentacion: tolerante, nunca bloquea
        p = root / rel
        try:
            t = p.read_text(encoding="utf-8") if p.exists() else ""
            if marca in t:
                continue
            if antes and antes in t:
                t = t.replace(antes, bloque + antes, 1)
            else:
                t = t + ("" if t.endswith("\n") or not t else "\n") + bloque
            if p.exists():
                (bk / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, bk / rel)
            p.write_text(t, encoding="utf-8"); print(f"  actualizado {rel}")
        except Exception as e:
            print(f"  (aviso) no se pudo actualizar {rel}: {e!r}")
    print(f"parche-108 instalado. Copias en {bk}" if plan else "parche-108: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

