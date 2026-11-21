"""Mide el examen 2.33 en el LCM completo, por tipo de pregunta. python -m lab.sintaxis.mide233 [-v] [salida.json]"""
import json, shutil, sys
from collections import Counter
from lab.banco import motor
from lab.sintaxis.examen233 import T
from lab.sintaxis.general_mide import clase

if __name__ == "__main__":
    C = {}
    filas = []
    for t in T:
        mo = motor()
        mo.chat("Te voy a leer un texto.\n" + t["texto"].strip())
        for q, cr, tipo in t["preguntas"]:
            a = mo.chat(q).get("respuesta") or ""
            k = clase(cr, a)
            C.setdefault(tipo, Counter())[k] += 1
            filas.append({"texto": t["id"], "q": q, "tipo": tipo, "crit": cr, "r": a, "v": k})
            if "-v" in sys.argv and k != "bien":
                print(f"   {tipo:3s} {k:11s} {q[:46]:46s} | {a[:110]}")
        shutil.rmtree(mo._tmp, ignore_errors=True)
    tot = Counter()
    for tipo in ("lit", "sin", "pro", "abs"):
        c = C.get(tipo, Counter()); n = sum(c.values()); tot.update(c)
        print(f"{tipo:4s} n={n:2d}  bien {c['bien']:2d}  se abstiene {c['se abstiene']:2d}  mal {c['mal']:2d}")
    n = sum(tot.values())
    print(f"TOTAL n={n}  bien {tot['bien']} ({100 * tot['bien'] / n:.1f} %)  se abstiene {tot['se abstiene']}  mal {tot['mal']}")
    out = [a for a in sys.argv[1:] if a.endswith(".json")]
    if out:
        json.dump(filas, open(out[0], "w"), ensure_ascii=False, indent=1)
