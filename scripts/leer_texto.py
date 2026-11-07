"""Lee un texto en lenguaje natural y lo convierte en un CARTUCHO de conocimiento (parche-91).

  python -m scripts.leer_texto data/textos/sistema_solar.txt            crea cartuchos/sistema_solar.json y lo INSERTA (activo)
  python -m scripts.leer_texto mi_texto.txt --nombre astronomia         con otro nombre
  python -m scripts.leer_texto mi_texto.txt --prueba                    lee y mide, sin crear cartucho

El texto se lee sobre una memoria de usar y tirar (fabrica + cartuchos activos), asi que el cartucho contiene SOLO lo que aporta el texto y no tu memoria
personal. Retirarlo: python -m scripts.cartucho retirar NOMBRE.  Escribe reports/lectura.txt (aprendido / no entendido / autoexamen de retencion)."""
import argparse
import os
import sys
import tempfile
from datetime import date

import torch

from src.language.dialogue import Conversation
from src.language.ingesta import comprobar, informe, leer, preparar
from src.language.qa import QA
from src.language.school_parser import SchoolParser
from src.language.ud import load_school
from src.memory import cartuchos
from src.memory.store import MemoryStore
from src.reasoning.lessons import deduce_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo")
    ap.add_argument("--nombre", default=None)
    ap.add_argument("--prueba", action="store_true", help="no crear cartucho")
    a = ap.parse_args()
    if not os.path.exists(a.archivo):
        sys.exit(f"No encuentro {a.archivo}")
    nombre = a.nombre or os.path.splitext(os.path.basename(a.archivo))[0].lower().replace(" ", "_")
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    try:
        from src.language.school_learn import load_overrides
        ov = load_overrides()
    except Exception:                                                     # noqa
        ov = None
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts, ov) if ov is not None else SchoolParser(model, device, scripts)
    with tempfile.TemporaryDirectory() as d:
        mem = MemoryStore(os.path.join(d, "lectura.json"))
        mem.today = parser.today = date.today()
        from src.language.semilla import load_seed
        load_seed(mem, parser)
        cartuchos.montar(mem, excluir=nombre)                             # contexto: fabrica + cartuchos activos (para entender referencias)
        snap = cartuchos.instantanea(mem)
        conv = Conversation(mem, parser, lambda m, p: QA(m, p.parse, lambda facts: deduce_all(facts, m.active_lessons())))
        frases, titulos = preparar(open(a.archivo, encoding="utf-8").read())
        rep = leer(conv, mem, frases)
        chk = comprobar(conv, mem, rep["hechos_nuevos"])
        contenido = cartuchos.delta(mem, snap)
    text = informe(rep, titulos, chk)
    os.makedirs("reports", exist_ok=True)
    open("reports/lectura.txt", "w", encoding="utf-8").write(text)
    print(text)
    if a.prueba:
        print("\n[--prueba: no se ha creado ningun cartucho]")
        return
    ruta = cartuchos.guardar_cartucho(nombre, contenido, {"fuente": a.archivo, "frases": len(frases), "no_entendidas": [f for f, _ in rep["no_entendidas"]]})
    cartuchos.insertar(nombre)
    print(f"\n[Cartucho «{nombre}» creado ({len(contenido['hechos'])} hechos) en {ruta} e INSERTADO. Pregunta en python -m scripts.think. Retirarlo: python -m scripts.cartucho retirar {nombre}]")


if __name__ == "__main__":
    main()
