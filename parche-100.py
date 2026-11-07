"""parche-100: `python -m scripts.check` (y el ciclo) muestran el AVANCE en pantalla: cada bloque terminado y cuál se está ejecutando, con segundos. No cambia ningún resultado."""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALL_EDITS = [('scripts/check.py', '    log = lambda s="": out.append(s)\n', '    import time as _time\n    _t0 = _time.time()\n\n    def log(s=""):                                            # parche-100: se ve el avance en pantalla (stderr), no solo al final\n        out.append(s)\n        if s and not s.startswith("   "):\n            print(f"[check {_time.time() - _t0:5.0f}s] {s.strip()[:150]}", file=sys.stderr, flush=True)\n', 'parche-100: se ve el avance'), ('scripts/check.py', '        g, t, bad = run_dialogo(path)\n        rate = g / max(t, 1)\n', '        print(f"[check {_time.time() - _t0:5.0f}s] ... ejecutando {name}", file=sys.stderr, flush=True)\n        g, t, bad = run_dialogo(path)\n        rate = g / max(t, 1)\n', '... ejecutando {name}')]
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
    print(f"parche-100 instalado. Copias en {bk}" if plan else "parche-100: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

