"""Compara el oido CON y SIN preentrenamiento con varias semillas (parche-27).

Una sola pasada no distingue efecto de ruido: entre reentrenamientos 'b' ya se movio varios puntos sin cambiar nada
relevante. Aqui se entrena y evalua  EAR_PRE=0  y  EAR_PRE=1  con 3 semillas cada uno y se comparan las MEDIAS.

REGLA DE DECISION (fijada antes de medir; es la misma de pretrain_ear, aplicada a medias):
  preentrenar se adopta si, en medias, a, b, f, g no bajan mas de 1 punto y d o e suben >= 2 puntos.
Reanudable: guarda cada resultado en reports/compare_ear.json. Tarda ~ 6 x (8-15 min) en el Mac.
"""
import json
import os
import re
import shutil
import statistics
import subprocess
import sys

OUT = "reports/compare_ear.json"
ROWS = "abecdfg"


def parse(text):
    res = {}
    for line in text.splitlines():
        m = re.match(r"\s+([a-g])\)[^\n]*?:\s+([\d.]+)%", line)
        if m:
            res[m.group(1)] = float(m.group(2))
    return res


def main():
    os.makedirs("reports", exist_ok=True)
    done = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for pre in ("0", "1"):
        for seed in ("0", "1", "2"):
            k = f"pre{pre}_seed{seed}"
            if k in done:
                continue
            print(f"--- {k}: entrenando...", flush=True)
            env = dict(os.environ, EAR_PRE=pre, LCM_SEED=seed)
            subprocess.run([sys.executable, "-m", "scripts.train_ear"], env=env, check=True, stdout=subprocess.DEVNULL)
            shutil.copy("checkpoints/ear.pt", f"checkpoints/ear_{k}.pt")
            out = subprocess.run([sys.executable, "-m", "scripts.evaluate_ear"], env=env, check=True, capture_output=True, text=True).stdout
            done[k] = parse(out)
            json.dump(done, open(OUT, "w"), indent=1)
            print("   ", done[k], flush=True)
    mean = {pre: {r: statistics.mean(done[f"pre{pre}_seed{s}"][r] for s in "012") for r in ROWS} for pre in "01"}
    spread = {pre: {r: max(done[f"pre{pre}_seed{s}"][r] for s in "012") - min(done[f"pre{pre}_seed{s}"][r] for s in "012") for r in ROWS} for pre in "01"}
    print("\nfila | sin preentrenar (media, rango) | con preentrenar (media, rango) | diferencia")
    for r in ROWS:
        print(f"  {r}  | {mean['0'][r]:5.1f}  ({spread['0'][r]:.1f}) | {mean['1'][r]:5.1f}  ({spread['1'][r]:.1f}) | {mean['1'][r]-mean['0'][r]:+.1f}")
    d = {r: mean["1"][r] - mean["0"][r] for r in ROWS}
    ok = all(d[r] >= -1.0 for r in "abfg") and (d["d"] >= 2.0 or d["e"] >= 2.0)
    print(f"\nDecision: {'PREENTRENAMIENTO ADOPTADO' if ok else 'NO ADOPTADO'}")
    best = "pre1_seed0" if ok else "pre0_seed0"
    shutil.copy(f"checkpoints/ear_{best}.pt", "checkpoints/ear.pt")
    print(f"[+] checkpoints/ear.pt = {best}")


if __name__ == "__main__":
    main()
