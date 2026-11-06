"""Reproduce el proyecto de principio a fin con UN comando.

  python -m scripts.reproduce                    # todo (necesita internet para UD y un libro/texto en espanol)
  python -m scripts.reproduce --libro mi_texto.txt
  python -m scripts.reproduce --desde train_school
  python -m scripts.reproduce --lista            # solo muestra los pasos
  python -m scripts.reproduce --semilla 7        # otra semilla global (LCM_SEED) para todos los entrenamientos
  python -m scripts.reproduce --rapido           # salta lo opcional y largo (pretrain_ear, evaluaciones online)

Cada paso es un modulo de scripts/. Si uno falla, se para y se dice cual (arreglalo y repite con --desde <paso>).
Las salidas se guardan en reports/reproduce_<paso>.log. Los criterios de aceptacion de cada paso estan escritos en sus
docstrings y se fijaron ANTES de medir; reports/RESULTADOS.md recoge lo que obtuvimos nosotros.
"""
import argparse
import json
import os
import subprocess
import sys
import time

# (nombre, modulo, args, opcional/largo, necesita libro)
STEPS = [
    ("tests_unitarios", "pytest", ["-q", "tests"], False, False),
    ("prepare_concepts", "scripts.prepare_concepts", [], False, False),
    ("train_reasoner", "scripts.train_reasoner", [], False, False),
    ("evaluate_reasoner", "scripts.evaluate_reasoner", [], False, False),
    ("read_book", "scripts.read_book", [], False, True),
    ("pretrain_ear", "scripts.pretrain_ear", [], True, True),
    ("train_ear", "scripts.train_ear", [], False, False),
    ("evaluate_ear", "scripts.evaluate_ear", [], False, False),
    ("read_book_medida", "scripts.read_book", [], True, True),      # ahora que el oido existe: mide cuantas frases del libro acepta (informativo)
    ("get_data", "scripts.get_data", [], False, False),
    ("train_school", "scripts.train_school", [], False, False),
    ("eval_frases", "scripts.eval_frases", [], False, False),
    ("eval_preguntas", "scripts.eval_preguntas", [], False, False),
    ("check_todo", "scripts.check", [], False, False),          # TODAS las pruebas de conversacion/razonamiento (parche-54..59)
    ("evaluate_online", "scripts.evaluate_online", [], True, False),
    ("evaluate_negatives", "scripts.evaluate_negatives", [], True, False),
    ("evaluate_inoculate", "scripts.evaluate_inoculate", [], True, False),
    ("evaluate_sleep", "scripts.evaluate_sleep", [], True, False),
    ("verificar_manifiesto", "scripts.manifiesto", ["--verificar"], False, False),    # mismo codigo que el manifiesto
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--libro", help="texto en espanol (.txt/.rtf) para el oido; por defecto regenta.rtf/.txt si existe")
    ap.add_argument("--desde", help="empezar en este paso")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--semilla", type=int, help="semilla global (LCM_SEED); por defecto 0, la de la referencia")
    ap.add_argument("--lista", action="store_true")
    a = ap.parse_args()
    names = [s[0] for s in STEPS]
    if a.desde and a.desde not in names:
        sys.exit(f"Paso desconocido. Pasos: {', '.join(names)}")
    if a.lista:
        print("\n".join(f"{i + 1:2d}. {n}" for i, n in enumerate(names)))
        return
    os.makedirs("reports", exist_ok=True)
    env = dict(os.environ, LCM_SEED=str(a.semilla if a.semilla is not None else os.environ.get("LCM_SEED", "0")), PYTHONHASHSEED="0", PYTHONUNBUFFERED="1")
    summary = []
    started = a.desde is None
    for name, mod, args, optional, needs_book in STEPS:
        if name == a.desde:
            started = True
        if not started or (a.rapido and optional):
            continue
        if needs_book and name in ("read_book", "read_book_medida"):
            if a.libro:
                args = [a.libro]
            elif not any(os.path.exists(f) for f in ("regenta.rtf", "regenta.txt")):
                print("[!] Salto read_book y los pasos que dependen del texto: pasa --libro tu_texto.txt "
                      "(cualquier novela o texto largo en espanol).")
                continue
        if needs_book and name == "pretrain_ear" and not os.path.exists("data/libro.txt"):
            continue
        print(f"\n=== {name} ===", flush=True)
        t0 = time.time()
        with open(os.path.join("reports", f"reproduce_{name}.log"), "w", encoding="utf-8") as log:
            p = subprocess.Popen([sys.executable, "-m", mod] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, env=env)
            tail = []
            for line in p.stdout:
                log.write(line)
                print(line, end="")
                tail.append(line)
            p.wait()
        summary.append({"paso": name, "codigo": p.returncode, "segundos": round(time.time() - t0, 1), "semilla": env["LCM_SEED"]})
        json.dump(summary, open("reports/reproduce_resumen.json", "w"), indent=1)
        if p.returncode != 0:
            sys.exit(f"\n[!] Fallo en '{name}' (codigo {p.returncode}). Log: reports/reproduce_{name}.log\n"
                     f"    Arreglalo y repite con:  python -m scripts.reproduce --desde {name}")
        print(f"[ok] {name} ({time.time() - t0:.0f}s)")
    print("\n[OK] Fin. Ahora prueba la conversacion:  python -m scripts.think")


if __name__ == "__main__":
    main()
