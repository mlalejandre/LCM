"""Ciclo automatico (parche-75): aplica uno o varios parches, mide TODO, vuelve atras solo si algo deja de cumplir y empaqueta el resultado.

    python -m scripts.ciclo parche-76.py parche-77.py     # aplica los parches EN ORDEN, mide y guarda el manifiesto si todo cumple
    python -m scripts.ciclo                               # sin parches: solo mide, graba arboles y empaqueta (estado actual)

Pasos: 1) copia de seguridad de src/scripts/tests/data(*.tsv,*.txt)  2) aplica cada parche  3) mide con scripts.grabar_arboles
(tests + 22 examenes + arboles)  4) si TODO CUMPLE: manifiesto --guardar; si no: restaura la copia de seguridad  5) escribe reports/ciclo.txt y
reports/paquete.zip (informe + arboles + historial + ciclo). NO hace commits ni pushes: al final imprime los comandos para que los hagas tu.
Una sola subida (paquete.zip) basta para la siguiente iteracion.
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DIRS = ("src", "scripts", "tests")


def snapshot(root: Path, stamp: str) -> Path:
    dest = root / ".ciclo_backups" / stamp
    for d in DIRS:
        shutil.copytree(root / d, dest / d, ignore=shutil.ignore_patterns("__pycache__"))
    (dest / "data").mkdir(parents=True, exist_ok=True)
    for f in (root / "data").glob("*"):
        if f.is_file() and f.suffix in (".tsv", ".txt"):
            shutil.copy2(f, dest / "data" / f.name)
    for f in ("reports/historial.json",):
        if (root / f).exists():
            (dest / "reports").mkdir(exist_ok=True)
            shutil.copy2(root / f, dest / f)
    olds = sorted(p for p in (root / ".ciclo_backups").iterdir() if p.is_dir())
    for old in olds[:-5]:                                   # se conservan solo las 5 ultimas copias
        shutil.rmtree(old, ignore_errors=True)
    return dest


def restore(root: Path, dest: Path) -> None:
    for d in DIRS:
        shutil.rmtree(root / d)
        shutil.copytree(dest / d, root / d)
    for f in (root / "data").glob("*"):
        if f.is_file() and f.suffix in (".tsv", ".txt"):
            f.unlink()
    for f in (dest / "data").glob("*"):
        shutil.copy2(f, root / "data" / f.name)
    if (dest / "reports" / "historial.json").exists():
        shutil.copy2(dest / "reports" / "historial.json", root / "reports" / "historial.json")


def run(cmd, root: Path, log):
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    log((r.stdout or "") + (r.stderr or ""))
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parches", nargs="*")
    ap.add_argument("--cmd-medir", default=f"{sys.executable} -m scripts.grabar_arboles", help="orden que mide y empaqueta")
    ap.add_argument("--cmd-manifiesto", default=f"{sys.executable} -m scripts.manifiesto --guardar")
    args = ap.parse_args()
    root = Path.cwd()
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    lines = []
    log = lambda s="": (lines.append(s), print(s))
    log(f"CICLO {stamp}")
    snap = snapshot(root, stamp)
    ok_apply = True
    for p in args.parches:
        src = Path(p)
        if not src.is_file():
            log(f"  PARCHE NO ENCONTRADO: {p}"); ok_apply = False; break
        tmp = root / f"_parche_ciclo_{src.stem.replace('-', '_')}.py"
        shutil.copy2(src, tmp)
        try:
            code = run([sys.executable, str(tmp)], root, lambda s: log("    " + s.replace("\n", "\n    ").rstrip()))
        finally:
            tmp.unlink(missing_ok=True)
        log(f"  parche {src.name}: {'aplicado' if code == 0 else 'FALLO (codigo %s)' % code}")
        if code != 0:
            ok_apply = False
            break
    todo_cumple = False
    if ok_apply:
        code = run(args.cmd_medir.split(), root, lambda s: None)
        inf = root / "reports" / "informe.txt"
        text = inf.read_text(encoding="utf-8") if inf.exists() else ""
        resumen = next((l for l in text.splitlines() if l.startswith("RESUMEN:")), "RESUMEN: (no hay informe)")
        tests = next((l for l in text.splitlines() if l.startswith("TESTS UNITARIOS")), "TESTS UNITARIOS: (sin dato)")
        todo_cumple = "TODO CUMPLE" in resumen and " failed" not in tests and " error" not in tests
        log(f"  {tests}")
        log(f"  {resumen.split('  {')[0]}")
        cambios = [l.strip() for l in text.splitlines() if "MEJORA" in l or "EMPEORA" in l]
        for l in cambios:
            log(f"    {l}")
    if todo_cumple:
        run(args.cmd_manifiesto.split(), root, lambda s: log("  " + s.strip()))
        log("RESULTADO: TODO CUMPLE. Cambios conservados y manifiesto guardado.")
        st = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True).stdout.strip()
        log("\nArchivos cambiados (git status --short):\n" + (st or "  (ninguno / no es un repositorio git)"))
        log("\nPara publicarlo (lo haces tu; revisa antes que no entra nada no deseado):\n  git add -A && git commit -m \"<mensaje>\" && git push")
    else:
        restore(root, snap)
        log("RESULTADO: NO SE CUMPLEN LOS CRITERIOS (o fallo un parche). Se ha RESTAURADO la copia de seguridad: el proyecto queda como estaba.")
        log(f"  Copia usada: {snap}")
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports" / "ciclo.txt").write_text("\n".join(lines), encoding="utf-8")
    sys.argv = [sys.argv[0]]
    import zipfile
    with zipfile.ZipFile(root / "reports" / "paquete.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in ("informe.txt", "arboles.json", "historial.json", "ciclo.txt", "razonamiento.json", "lector_bench.json", "ultima_lectura.txt"):
            if (root / "reports" / f).exists():
                z.write(root / "reports" / f, f)
    print(f"\n[Sube reports/paquete.zip a la conversacion]")
    return 0 if todo_cumple else 1


if __name__ == "__main__":
    sys.exit(main())
