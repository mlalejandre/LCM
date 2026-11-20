"""limpieza.py: deja el proyecto en TABULA RASA para probar LCM_construir_desde_cero.py.

Uso (desde la raiz del proyecto):
  python limpieza.py                      # ENSAYO: solo muestra que se quitaria y que se conserva
  python limpieza.py --aplicar            # lo hace: MUEVE todo a ../LCM_antes_de_tabula_rasa_<fecha>/ (recuperable) tras pedirte confirmacion
  python limpieza.py --aplicar --borrar   # lo BORRA de verdad (sin copia), tambien con confirmacion
Opciones:
  --conservar-ud        no toca data/ud/ (los corpus UD pesan y se pueden bajar de nuevo con scripts.get_data)
  --conservar ARCHIVO   (repetible) conserva ese archivo o carpeta de la raiz (p. ej. tu texto: --conservar mi_texto.txt)
  --sin-manifiesto      permite limpiar aunque no exista reproducibilidad/manifiesto.json (no recomendado)

Solo se quita lo que es del proyecto (lo que trae el constructor + lo que genera el uso: checkpoints, memory, reports, data...).
Cualquier otro archivo de la raiz (tus textos, parche-N.py, notas...) se conserva y se avisa.
SIEMPRE se conservan: este archivo, LCM_construir_desde_cero.py, reproducibilidad/ (manifiesto: fija las versiones de UD y las metricas
de referencia), .git/, .venv/ y venv/ (tu entorno de Python), y los textos de libro de la raiz (regenta.rtf/.txt, libro.*).
Se quita TODO lo demas: codigo, tests, datos, pesos (checkpoints), memoria, informes, copias de parches...

Despues de limpiar:
  python LCM_construir_desde_cero.py
  source .venv/bin/activate && pip install -r requirements.txt
  python -m pytest -q tests && python -m scripts.reproduce --libro tu_texto.txt && python -m scripts.manifiesto --verificar --metricas
"""
import argparse
import datetime
import os
import shutil
import sys
from pathlib import Path

GENERADOS = {"checkpoints", "memory", "reports", "data", "_archivo", ".parche_backups", ".pytest_cache", "__pycache__", ".vscode", ".github",
             ".DS_Store"}          # carpetas que crea el propio proyecto al usarse
SIEMPRE = {"limpieza.py", "LCM_construir_desde_cero.py", "reproducibilidad", ".git", ".venv", "venv", "env", ".env"}
LIBROS = ("regenta.rtf", "regenta.txt", "libro.txt", "libro.rtf")
FRASE = "TABULA RASA"


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


def comprobar_constructor(path: Path) -> int:
    src = path.read_text(encoding="utf-8")
    compile(src, str(path), "exec")
    ns = {}
    # solo se lee el diccionario FILES (sin ejecutar main): se evalua el trozo hasta 'def main'
    head = src[: src.rindex("\ndef main")]
    exec(head, ns)
    return ns["FILES"]


def main():
    ap = argparse.ArgumentParser(description="Tabula rasa del proyecto LCM")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--borrar", action="store_true", help="borrar de verdad en vez de mover a ../LCM_antes_de_tabula_rasa_<fecha>")
    ap.add_argument("--conservar-ud", action="store_true")
    ap.add_argument("--conservar", action="append", default=[])
    ap.add_argument("--sin-manifiesto", action="store_true")
    a = ap.parse_args()

    root = Path.cwd()
    if not (root / "src").is_dir() or not (root / "scripts").is_dir():
        sys.exit("[!] Ejecuta esto desde la raiz del proyecto LCM (donde estan src/ y scripts/).")
    builder = root / "LCM_construir_desde_cero.py"
    if not builder.exists():
        sys.exit("[!] Falta LCM_construir_desde_cero.py en la raiz: sin el no podrias reconstruir nada.\n"
                 "    Crealo antes con:  python -m scripts.empaquetar_todo")
    try:
        files = comprobar_constructor(builder)
        n_files = len(files)
    except Exception as exc:
        sys.exit(f"[!] LCM_construir_desde_cero.py no es valido ({type(exc).__name__}: {exc}). Regeneralo con scripts.empaquetar_todo.")
    if n_files < 50:
        sys.exit(f"[!] LCM_construir_desde_cero.py solo contiene {n_files} archivos: parece incompleto. Regeneralo con scripts.empaquetar_todo.")
    if not (root / "reproducibilidad" / "manifiesto.json").exists() and not a.sin_manifiesto:
        sys.exit("[!] Falta reproducibilidad/manifiesto.json (guarda los commits de UD y las metricas de referencia).\n"
                 "    Crealo antes con:  python -m scripts.manifiesto --guardar     (o usa --sin-manifiesto)")

    keep_names = set(SIEMPRE) | set(LIBROS) | set(a.conservar)
    del_names = {rel.split("/")[0] for rel in files} | GENERADOS            # lo que es del proyecto (lo trae el constructor o lo genera el uso)
    keep, remove = [], []
    for p in sorted(root.iterdir(), key=lambda x: x.name):
        if p.name in keep_names:
            keep.append((p, "se conserva"))
        elif p.name not in del_names:
            keep.append((p, "se conserva: no es del proyecto (tuyo)"))
        elif p.name == "data" and a.conservar_ud and (p / "ud").exists():
            keep.append((p / "ud", "se conserva (corpus UD)"))
            for q in sorted(p.iterdir()):
                if q.name != "ud":
                    remove.append(q)
        else:
            remove.append(p)

    print(f"Proyecto: {root}")
    print(f"Constructor valido: {builder.name} ({n_files} archivos)\n")
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
    if not a.aplicar:
        print("\n[ENSAYO] No se ha tocado nada. Para hacerlo:  python limpieza.py --aplicar" + (" --borrar" if a.borrar else ""))
        return
    if not remove:
        print("[OK] Ya esta en tabula rasa.")
        return
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
    print("Ahora:\n  python LCM_construir_desde_cero.py\n  source .venv/bin/activate && pip install -r requirements.txt\n"
          "  python -m pytest -q tests\n  python -m scripts.reproduce --libro tu_texto.txt\n  python -m scripts.manifiesto --verificar --metricas")


if __name__ == "__main__":
    main()
