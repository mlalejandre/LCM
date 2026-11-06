"""limpieza.py: deja el proyecto en TABULA RASA y, si quieres, lo vuelve a levantar y a entrenar TODO, con un solo comando.

  python limpieza.py                          # ENSAYO: muestra que se quitaria y que se conserva (no toca nada)
  python limpieza.py --aplicar                # limpia (MUEVE todo a ../LCM_antes_de_tabula_rasa_<fecha>/, recuperable)
  python limpieza.py --aplicar --reconstruir  # limpia y RECONSTRUYE + REENTRENA todo automaticamente (venv, dependencias, tests,
                                              # verificacion, reproduce, comparacion de metricas). No hace falta ningun otro comando.

Que hace, en orden (si algo falla, se para ANTES de quitar nada):
  1. Regenera LCM_construir_desde_cero.py y reproducibilidad/manifiesto.json DESDE TU PROYECTO ACTUAL (para que la reconstruccion
     sea fiel a tu copia, no a otra). Desactivable con --no-refrescar.
  2. Ensayo de reconstruccion: escribe el constructor en una carpeta temporal y comprueba que cada archivo sale IDENTICO al tuyo.
  3. Te pide confirmacion (escribe TABULA RASA).
  4. Mueve (o borra, con --borrar) todo lo del proyecto. Se conserva: limpieza.py, LCM_construir_desde_cero.py, reproducibilidad/,
     .git/, .venv/ y venv/, regenta.* / libro.*, y cualquier archivo de la raiz que no sea del proyecto (tus textos, parche-N.py...).
  5. Con --reconstruir: ejecuta el constructor (modo todo: entorno, tests, verificacion, reentrenamiento y comparacion con la referencia).

Opciones:
  --borrar                 borrar de verdad en vez de mover (sin copia)
  --reconstruir [MODO]     MODO = todo (por defecto) | menu | archivos (solo escribe los archivos)
  --libro RUTA             texto en espanol para el oido (por defecto regenta.rtf/.txt de la raiz)
  --rapido, --semilla N    se pasan al reentrenamiento
  --conservar-ud           no toca data/ud/ (los corpus se pueden bajar de nuevo con scripts.get_data, fijados al commit del manifiesto)
  --conservar ARCHIVO      (repetible) conserva ese archivo o carpeta de la raiz
  --no-refrescar           no regenera el constructor ni el manifiesto (usa los que hay)
  --sin-manifiesto         permite limpiar sin reproducibilidad/manifiesto.json (no recomendado)
"""
import argparse
import datetime
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GENERADOS = {"checkpoints", "memory", "reports", "data", "_archivo", ".parche_backups", ".pytest_cache", "__pycache__", ".vscode", ".github",
             ".DS_Store"}          # carpetas que crea el propio proyecto al usarse
SIEMPRE = {"limpieza.py", "LCM_construir_desde_cero.py", "reproducibilidad", ".git", ".venv", "venv", "env", ".env"}
LIBROS = ("regenta.rtf", "regenta.txt", "libro.txt", "libro.rtf")
FRASE = "TABULA RASA"
BUILDER = "LCM_construir_desde_cero.py"


def tam(p: Path) -> int:
    if p.is_file() or p.is_symlink():
        return p.stat().st_size if p.exists() else 0
    total = 0
    for base, _, files in os.walk(p):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(base, f))
            except OSError:
                pass
    return total


def mb(n: int) -> str:
    return f"{n / 1e6:,.1f} MB"


def leer_constructor(path: Path) -> dict:
    src = path.read_text(encoding="utf-8")
    compile(src, str(path), "exec")
    ns = {}
    exec(src[: src.rindex("\ndef main")] if "\ndef main" in src else src, ns)      # solo el diccionario FILES (no ejecuta main)
    files = ns.get("FILES")
    if not isinstance(files, dict):
        raise ValueError("no encuentro el diccionario FILES")
    return files


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd).returncode == 0


def refrescar(root: Path) -> None:
    """Regenera constructor + manifiesto desde el proyecto actual y comprueba una reconstruccion en una carpeta temporal."""
    if not (root / "scripts" / "empaquetar_todo.py").exists() or not (root / "scripts" / "manifiesto.py").exists():
        sys.exit("[!] Falta scripts/empaquetar_todo.py o scripts/manifiesto.py (instala el parche de reproducibilidad). "
                 "Usa --no-refrescar para limpiar con el constructor que ya tienes.")
    print("1/2 Regenerando el constructor y el manifiesto desde tu proyecto actual ...")
    if not run([sys.executable, "-m", "scripts.empaquetar_todo"], root) or not run([sys.executable, "-m", "scripts.manifiesto", "--guardar"], root):
        sys.exit("[!] No se pudo regenerar el constructor/manifiesto. No se ha tocado nada.")
    print("2/2 Ensayo de reconstruccion en una carpeta temporal ...")
    sys.path.insert(0, str(root))
    from scripts.manifiesto import tracked
    mios = [f for f in tracked(str(root)) if (root / f).is_file()]
    tmp = Path(tempfile.mkdtemp(prefix="lcm_ensayo_"))
    try:
        shutil.copy(root / BUILDER, tmp / BUILDER)
        r = subprocess.run([sys.executable, BUILDER, "--sin-menu"], cwd=tmp, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"[!] El constructor no se ejecuta en limpio:\n{r.stderr[-800:]}\nNo se ha tocado nada.")
        malos = [f for f in mios if f != BUILDER and (not (tmp / f).is_file() or (tmp / f).read_bytes() != (root / f).read_bytes())]
        if malos:
            sys.exit("[!] La reconstruccion NO es identica a tu proyecto en estos archivos (no se limpia nada):\n   " + "\n   ".join(malos[:20]))
        print(f"    OK: {len(mios)} archivos se reconstruyen identicos.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Tabula rasa del proyecto LCM (y reconstruccion opcional)")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--borrar", action="store_true", help="borrar de verdad en vez de mover a ../LCM_antes_de_tabula_rasa_<fecha>")
    ap.add_argument("--reconstruir", nargs="?", const="todo", choices=["todo", "menu", "archivos"])
    ap.add_argument("--libro")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--semilla", type=int)
    ap.add_argument("--conservar-ud", action="store_true")
    ap.add_argument("--conservar", action="append", default=[])
    ap.add_argument("--no-refrescar", action="store_true")
    ap.add_argument("--sin-manifiesto", action="store_true")
    a = ap.parse_args()

    root = Path.cwd()
    if not (root / "src").is_dir() or not (root / "scripts").is_dir():
        sys.exit("[!] Ejecuta esto desde la raiz del proyecto LCM (donde estan src/ y scripts/).")
    builder = root / BUILDER
    if a.aplicar and not a.no_refrescar:
        refrescar(root)                          # antes de quitar NADA; si falla, se para aqui
    if not builder.exists():
        sys.exit(f"[!] Falta {BUILDER} en la raiz: sin el no podrias reconstruir nada. Crealo con:  python -m scripts.empaquetar_todo")
    try:
        files = leer_constructor(builder)
    except Exception as exc:
        sys.exit(f"[!] {BUILDER} no es valido ({type(exc).__name__}: {exc}). Regeneralo con scripts.empaquetar_todo.")
    if len(files) < 50:
        sys.exit(f"[!] {BUILDER} solo contiene {len(files)} archivos: parece incompleto. Regeneralo con scripts.empaquetar_todo.")
    if not (root / "reproducibilidad" / "manifiesto.json").exists() and not a.sin_manifiesto:
        sys.exit("[!] Falta reproducibilidad/manifiesto.json. Crealo con:  python -m scripts.manifiesto --guardar     (o usa --sin-manifiesto)")

    keep_names = set(SIEMPRE) | set(LIBROS) | set(a.conservar)
    del_names = {rel.split("/")[0] for rel in files} | GENERADOS
    keep, remove = [], []
    for p in sorted(root.iterdir(), key=lambda x: x.name):
        if p.name in keep_names:
            keep.append((p, "se conserva"))
        elif p.name not in del_names:
            keep.append((p, "se conserva: no es del proyecto (tuyo)"))
        elif p.name == "data" and a.conservar_ud and (p / "ud").exists():
            keep.append((p / "ud", "se conserva (corpus UD)"))
            remove += [q for q in sorted(p.iterdir()) if q.name != "ud"]
        else:
            remove.append(p)

    print(f"\nProyecto: {root}")
    print(f"Constructor valido: {BUILDER} ({len(files)} archivos)\n")
    print("SE CONSERVA:")
    for p, why in keep:
        print(f"   = {p.relative_to(root)}{'/' if p.is_dir() else ''}   ({why})")
    print("\nSE QUITA:")
    total = 0
    for p in remove:
        s = tam(p)
        total += s
        print(f"   - {p.relative_to(root)}{'/' if p.is_dir() else ''}   {mb(s)}")
    print(f"\nTotal a quitar: {len(remove)} elementos, {mb(total)}")
    destino = None
    if not a.borrar:
        destino = root.parent / ("LCM_antes_de_tabula_rasa_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        print(f"Destino (recuperable): {destino}")
    else:
        print("MODO BORRAR: sin copia, no se puede deshacer.")
    if a.reconstruir:
        print(f"Despues se reconstruye en modo '{a.reconstruir}'" + (" y se reentrena TODO." if a.reconstruir == "todo" else "."))
    if not a.aplicar:
        print("\n[ENSAYO] No se ha tocado nada. Para hacerlo:  python limpieza.py --aplicar" + (" --borrar" if a.borrar else "")
              + " --reconstruir" * (not a.reconstruir) + "   (con --reconstruir se vuelve a levantar y entrenar todo solo)")
        return
    if not remove:
        print("[OK] Ya esta en tabula rasa.")
    else:
        print(f"\nEscribe exactamente  {FRASE}  para continuar (cualquier otra cosa cancela): ", end="")
        if input().strip() != FRASE:
            sys.exit("\n[CANCELADO] No se ha tocado nada.")
        if destino:
            destino.mkdir(parents=True, exist_ok=False)
        for p in remove:
            if destino:
                shutil.move(str(p), str(destino / p.name))
            elif p.is_dir() and not p.is_symlink():
                shutil.rmtree(p)
            else:
                p.unlink()
        print(f"\n[HECHO] {len(remove)} elementos {'movidos a ' + str(destino) if destino else 'borrados'}.")
    if not a.reconstruir:
        print("Ahora:  python LCM_construir_desde_cero.py        (escribe todo y abre el menu; la opcion 7 lo hace todo en orden)")
        return
    cmd = [sys.executable, BUILDER]
    if a.reconstruir == "archivos":
        cmd.append("--sin-menu")
    elif a.reconstruir == "todo":
        cmd.append("--todo")
        if a.libro:
            cmd += ["--libro", a.libro]
        if a.rapido:
            cmd.append("--rapido")
        if a.semilla is not None:
            cmd += ["--semilla", str(a.semilla)]
    print("\n=== Reconstruyendo: " + " ".join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd)) + " ===\n", flush=True)
    sys.exit(subprocess.run(cmd, cwd=root).returncode)


if __name__ == "__main__":
    main()
