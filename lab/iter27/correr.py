"""Ronda 2.7: tandas de 10 interacciones de charla libre. python -m lab.iter27.correr N  (ejecuta la tanda N y anota el primer intento)."""
import importlib, json, os, sys
from lab.banco import correr, imprime

def main():
    k = int(sys.argv[1])
    mod = importlib.import_module(f"lab.iter27.t{k:02d}")
    f, r = correr(mod.D, verboso=True)
    imprime(r, f"ITER27 T{k:02d}")
    reg = "lab/iter27/primer_intento.json"
    d = json.load(open(reg)) if os.path.exists(reg) else {}
    if str(k) not in d:
        d[str(k)] = {"n": r["n"], "acierto": r["acierto"], "falsas": r["falsas"]}
        json.dump(d, open(reg, "w"), indent=1)

if __name__ == "__main__":
    main()
