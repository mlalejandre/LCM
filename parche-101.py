"""parche-101: ARREGLA el cuelgue de `scripts.check` / el ciclo en texto_solar5 (traza tuya): `extract.surface` recorria los adjetivos de un arbol con ciclo (salida del analizador real) sin recordar los ya visitados y no terminaba nunca (CPU 80%, memoria creciendo). Ahora los recuerda. No cambia ningun resultado en arboles bien formados."""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALL_EDITS = [('src/language/extract.py', '        while todo:\n            c = todo.pop()\n            amods.add(c)\n            todo += _children(tree, c)', '        while todo:\n            c = todo.pop()\n            if c in amods:                              # parche-101: un arbol con ciclo (cabeza que se apunta a si misma) no puede dejarlo en bucle\n                continue\n            amods.add(c)\n            todo += _children(tree, c)', 'parche-101: un arbol con ciclo')]
NEW_FILES = {}

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
    print(f"parche-101 instalado. Copias en {bk}" if plan else "parche-101: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

