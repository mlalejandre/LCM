"""Graba lo que predice la ESCUELA para cada frase de los examenes (parche-75).

    python -m scripts.grabar_arboles                 # corre scripts.check y graba reports/arboles.json + reports/paquete.zip
    python -m scripts.grabar_arboles --extra f.txt   # ademas graba las frases de f.txt (una por linea)
    python -m scripts.grabar_arboles --sin-check     # solo graba --extra, sin correr los examenes

Todo lo que sigue a la escuela (extractor, preguntas, memoria, dialogo, coherencia, efectos) es codigo simbolico y determinista. Si se
graba la salida cruda de la escuela, esa parte se puede reproducir en cualquier maquina con scripts.replay, sin torch ni pesos.
Se graba la salida SIN arreglos (antes de _fix_name_verb, _fix_name_adj y los lemas irregulares), para poder probar arreglos nuevos.
Sube reports/paquete.zip (informe + arboles + historial): es lo unico que hace falta.
"""
import argparse
import datetime
import json
import os
import sys
import zipfile

import src.language.school_parser as sp

REC = {}


def clave(forms):
    return "\x1f".join(forms)


def instalar_grabador():
    original = sp.predict_trees

    def grabando(model, batch, device, scripts):
        res = original(model, batch, device, scripts)
        for forms, pred in zip(batch, res):
            REC[clave(forms)] = [list(x) for x in pred]
        return res

    sp.predict_trees = grabando


def empaquetar(extra=()):
    os.makedirs("reports", exist_ok=True)
    with zipfile.ZipFile("reports/paquete.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in ("reports/informe.txt", "reports/arboles.json", "reports/historial.json", "reports/ciclo.txt", *extra):
            if os.path.exists(f):
                z.write(f, os.path.basename(f))
    print(f"[Paquete listo: reports/paquete.zip ({os.path.getsize('reports/paquete.zip') // 1024} KB): subelo a la conversacion]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra")
    ap.add_argument("--sin-check", action="store_true")
    args = ap.parse_args()
    sys.argv = [sys.argv[0]]                      # eval_preguntas.blocks() lee sys.argv[1] como ruta: que no vea nuestros argumentos
    instalar_grabador()
    if not args.sin_check:
        from scripts import check
        check.main()
    if args.extra:
        import torch
        from src.language.ud import load_school
        device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        model, scripts = load_school(device=device)
        parser = sp.SchoolParser(model, device, scripts)
        n = 0
        for line in open(args.extra, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    parser.tree(line)
                    n += 1
                except Exception as exc:          # noqa
                    print(f"  (no se pudo grabar {line!r}: {exc})")
        print(f"Frases extra grabadas: {n}")
    os.makedirs("reports", exist_ok=True)
    json.dump({"version": 1, "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "n": len(REC), "arboles": REC},
              open("reports/arboles.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Arboles grabados: {len(REC)} -> reports/arboles.json")
    empaquetar()


if __name__ == "__main__":
    main()
