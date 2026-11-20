"""Mide una iteración: dev y ciego (solo agregados del ciego). Registra en lab/historial.jsonl."""
import sys, json, time, os
from lab.banco import correr, imprime
from lab.generador import generar
etq = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 12; sems = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "1").split(",")]
out = {"etiqueta": etq, "t": time.strftime("%Y-%m-%d %H:%M"), "nucleo20": os.environ.get("LCM_NUCLEO20", "1")}
for split in ("dev", "ciego"):
    D = []
    for s in sems:
        D += generar(split, n, s)
    t0 = time.time(); filas, res = correr(D); res["seg"] = round(time.time() - t0, 1); res["dialogos"] = len(D)
    # desglose ciego: formulaciones nuevas no se distinguen por turno; se informa el agregado
    out[split] = res
    imprime(res, f"{etq} · {split} ({len(D)} diálogos, {res['seg']} s)")
    if split == "dev":
        json.dump(filas, open("lab/ultimo_dev.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
open("lab/historial.jsonl", "a", encoding="utf-8").write(json.dumps(out, ensure_ascii=False) + "\n")
