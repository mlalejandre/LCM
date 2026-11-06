"""Genera UN solo archivo (LCM_construir_desde_cero.py) con TODO el codigo, datos pequenos de prueba, tests y documentos del proyecto.

  python -m scripts.empaquetar_todo                 # escribe LCM_construir_desde_cero.py en la raiz
  python -m scripts.empaquetar_todo --salida X.py

Para reconstruir el proyecto en una carpeta VACIA:
  mkdir LCM && cd LCM && cp /donde/este/LCM_construir_desde_cero.py . && python LCM_construir_desde_cero.py
  python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
  python -m pytest -q tests && python -m scripts.reproduce --libro tu_texto.txt && python -m scripts.manifiesto --verificar

No incluye: pesos (checkpoints), datasets generados (.pkl), corpus UD (se descargan con scripts.get_data), ningun libro, ni tu memoria.
Las huellas de lo empaquetado salen en reproducibilidad/manifiesto.json (python -m scripts.manifiesto --guardar).
"""
import argparse
import base64
import datetime
import os
import sys

sys.path.insert(0, os.getcwd())
from scripts.manifiesto import tracked  # noqa: E402

HEADER = '''"""LCM: construir el proyecto DESDE CERO (generado por scripts/empaquetar_todo.py el {fecha}).

Uso, en una carpeta vacia (o en la del proyecto tras limpieza.py):
    python LCM_construir_desde_cero.py              # escribe {n} archivos y abre un MENU guiado:
                                                    #   1 entorno e instalacion · 2 tests · 3 verificar codigo · 4 reentrenar todo
                                                    #   5 comparar resultados · 6 hablar con el modelo · 7 todo en orden
    python LCM_construir_desde_cero.py --sin-menu   # solo escribe los archivos (copias en .parche_backups/ si cambian)
    python LCM_construir_desde_cero.py --todo --libro tu_texto.txt [--rapido] [--semilla N]   # sin preguntar nada
({tests}). Guia completa: docs/REPRODUCIR.md
"""
import base64, datetime, sys
from pathlib import Path

FILES = {{
'''

FOOTER = '''}


# ----------------------------------------------------------------------------------------------------------------------
# Asistente interactivo (solo biblioteca estandar). Uso:
#   python LCM_construir_desde_cero.py                  -> escribe los archivos y abre el menu
#   python LCM_construir_desde_cero.py --sin-menu       -> solo escribe los archivos
#   python LCM_construir_desde_cero.py --todo [--libro mi_texto.txt] [--rapido] [--semilla N]   -> hace todo en orden, sin preguntar
# ----------------------------------------------------------------------------------------------------------------------
import argparse
import os
import subprocess

ROOT = Path.cwd()
LIBROS = ("regenta.rtf", "regenta.txt", "libro.txt", "libro.rtf")
OPT = {"libro": None, "rapido": False, "semilla": None}


def write_files():
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    wrote = same = 0
    for rel, content in FILES.items():
        if content.startswith("\\0b64:"):
            content = base64.b64decode(content[5:]).decode("utf-8")
        path = ROOT / rel
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                same += 1
                continue
            bak = ROOT / ".parche_backups" / stamp / rel
            bak.parent.mkdir(parents=True, exist_ok=True)
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        wrote += 1
    for d in ("checkpoints", "memory", "reports"):
        (ROOT / d).mkdir(exist_ok=True)
    print(f"[OK] {wrote} archivos escritos, {same} ya estaban igual.")


def venv_python():
    for rel in (".venv/bin/python", ".venv/Scripts/python.exe", "venv/bin/python", "venv/Scripts/python.exe"):
        if (ROOT / rel).exists():
            return str(ROOT / rel)
    return None


def py():
    return venv_python() or sys.executable


def run(args, quiet=False):
    print("\\n$ " + " ".join(args), flush=True)
    r = subprocess.run(args, cwd=ROOT)
    if r.returncode != 0 and not quiet:
        print(f"[!] El comando termino con codigo {r.returncode}.")
    return r.returncode == 0


def has_torch():
    return subprocess.run([py(), "-c", "import torch, numpy, tqdm, pytest"], cwd=ROOT, capture_output=True).returncode == 0


def find_book():
    if OPT["libro"]:
        return OPT["libro"]
    for f in LIBROS:
        if (ROOT / f).exists():
            return f
    return None


def step_entorno():
    if not venv_python():
        print("Creando el entorno de Python (.venv) ...")
        if not run([sys.executable, "-m", "venv", ".venv"]):
            return False
    print("Instalando dependencias (puede tardar unos minutos la primera vez) ...")
    return run([py(), "-m", "pip", "install", "-r", "requirements.txt"])


def step_tests():
    return run([py(), "-m", "pytest", "-q", "tests"])


def step_codigo():
    if not (ROOT / "reproducibilidad" / "manifiesto.json").exists():
        print("Aun no hay reproducibilidad/manifiesto.json (se crea con:  python -m scripts.manifiesto --guardar  en tu proyecto original).")
        print("Lo creo ahora a partir de lo que acabo de escribir?  (sirve para comprobar copias futuras)")
        return run([py(), "-m", "scripts.manifiesto", "--guardar"])
    return run([py(), "-m", "scripts.manifiesto", "--verificar"])


def step_reentrenar():
    book = find_book()
    args = [py(), "-m", "scripts.reproduce"]
    if book:
        args += ["--libro", book]
    else:
        print("[aviso] No hay texto en espanol (regenta.rtf/.txt) ni --libro: se saltan los pasos que dependen de el (el oido saldra distinto).")
    if OPT["rapido"]:
        args.append("--rapido")
    if OPT["semilla"] is not None:
        args += ["--semilla", str(OPT["semilla"])]
    return run(args)


def step_resultados():
    return run([py(), "-m", "scripts.manifiesto", "--verificar", "--metricas"])


def step_hablar():
    return run([py(), "-m", "scripts.think"])


def estado():
    ck = ROOT / "checkpoints"
    pesos = [f for f in ("lcm_reasoner.pt", "ear.pt", "school.pt") if (ck / f).exists()]
    print("\\nEstado:")
    print(f"   entorno Python (.venv) .... {'si' if venv_python() else 'no'}   |   dependencias .... {'si' if venv_python() and has_torch() else 'no / sin comprobar'}")
    print(f"   pesos entrenados .......... {len(pesos)}/3 ({', '.join(pesos) or 'ninguno'})")
    print(f"   texto en espanol .......... {find_book() or 'no encontrado (usa --libro o pon regenta.rtf/.txt aqui)'}")


MENU = [
    ("1", "Preparar el entorno (crear .venv e instalar dependencias)", step_entorno),
    ("2", "Comprobar el codigo con los tests (51)", step_tests),
    ("3", "Verificar que el codigo es identico al original (manifiesto)", step_codigo),
    ("4", "Reentrenar TODO desde cero (reproduce; tarda desde decenas de minutos a horas)", step_reentrenar),
    ("5", "Comprobar los resultados contra la referencia", step_resultados),
    ("6", "Hablar con el modelo (think)", step_hablar),
    ("7", "Hacer 1 -> 5 en orden, sin parar", None),
]


def hacer_todo():
    for key, label, fn in MENU[:5]:
        print(f"\\n=== {key}. {label} ===")
        if not fn():
            print(f"[!] Se para en el paso {key}. Arreglalo y repite desde el menu.")
            return False
    print("\\n[OK] Todo hecho. Ahora puedes probar:  python -m scripts.think")
    return True


def menu():
    if not any((ROOT / "checkpoints" / f).exists() for f in ("ear.pt", "school.pt", "lcm_reasoner.pt")):
        try:
            r = input("\\nNo hay pesos entrenados. ¿Lo hago TODO automaticamente (entorno, tests, verificacion, reentrenamiento y comparacion)? [S/n]: ").strip().lower()
        except EOFError:
            return
        if r in ("", "s", "si", "y", "yes"):
            if OPT["libro"] is None and find_book() is None:
                OPT["libro"] = input("Ruta de tu texto en espanol (Enter = sin texto): ").strip() or None
            hacer_todo()
            return
    while True:
        estado()
        print("\\n¿Que quieres hacer?")
        for key, label, _ in MENU:
            print(f"   {key}) {label}")
        print("   0) Salir")
        try:
            choice = input("Elige un numero: ").strip()
        except EOFError:
            return
        if choice in ("0", "q", ""):
            return
        if choice == "7":
            hacer_todo()
            continue
        item = next((m for m in MENU if m[0] == choice), None)
        if not item:
            print("Opcion no valida.")
            continue
        if choice == "4":
            if not has_torch():
                print("Primero hace falta el entorno: elige la opcion 1.")
                continue
            if OPT["libro"] is None and find_book() is None:
                OPT["libro"] = input("Ruta de tu texto en espanol (Enter = sin texto): ").strip() or None
            r = input("¿Modo rapido (salta las evaluaciones opcionales)? [s/N]: ").strip().lower()
            OPT["rapido"] = r in ("s", "si", "y")
        item[2]()


def main():
    ap = argparse.ArgumentParser(description="Construye el proyecto LCM desde cero y te guia para probarlo.")
    ap.add_argument("--sin-menu", action="store_true", help="solo escribe los archivos")
    ap.add_argument("--todo", action="store_true", help="escribe, instala, prueba, reentrena y verifica sin preguntar")
    ap.add_argument("--libro", help="texto en espanol para el oido")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--semilla", type=int)
    a = ap.parse_args()
    OPT.update(libro=a.libro, rapido=a.rapido, semilla=a.semilla)
    write_files()
    if a.sin_menu:
        print("Siguiente:  python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python -m pytest -q tests")
        return
    if a.todo:
        sys.exit(0 if hacer_todo() else 1)
    if not sys.stdin.isatty():
        print("(sin terminal interactiva: no abro el menu; usa --todo o ejecuta de nuevo en una terminal)")
        return
    menu()


if __name__ == "__main__":
    main()
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="LCM_construir_desde_cero.py")
    a = ap.parse_args()
    files = [f for f in tracked() if f != a.salida and os.path.exists(f)]
    body = []
    for f in files:
        text = open(f, encoding="utf-8").read()
        if "'''" in text or text.endswith("\\") or "\0" in text or "\r" in text:
            enc = "\0b64:".replace("\0", "\\0") + base64.b64encode(text.encode("utf-8")).decode("ascii")
            body.append(f"    {f!r}: {enc!r},\n".replace("\\\\0b64", "\\0b64"))
        else:
            body.append(f"    {f!r}: r'''{text}''',\n")
    ntests = sum(1 for f in files if f.startswith("tests/test_"))
    out = HEADER.format(fecha=datetime.date.today().isoformat(), n=len(files), tests=f"{ntests} ficheros de tests unitarios") + "".join(body) + FOOTER
    open(a.salida, "w", encoding="utf-8").write(out)
    compile(out, a.salida, "exec")
    print(f"[OK] {a.salida}: {len(files)} archivos, {len(out) // 1024} KB")


if __name__ == "__main__":
    main()
