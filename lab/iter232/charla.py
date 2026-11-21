"""Corre conversaciones libres y enseña la transcripción con su veredicto. python -m lab.iter232.charla <módulo> [id…] [-q]"""
import importlib, json, shutil, sys
from lab.banco import motor, veredicto


def corre(mod, ids=(), callado=False):
    C = importlib.import_module("lab.iter232." + mod).C
    tot = [0, 0, 0]; filas = []
    for c in C:
        if ids and c["id"] not in ids:
            continue
        mo = motor()
        if not callado:
            print(f"\n######## {c['id']} · {c['ctx']}")
        for q, crit in c["turnos"]:
            try:
                o = mo.chat(q); r, err = o.get("respuesta"), o.get("error")
            except Exception as e:                       # noqa
                r, err = None, repr(e)[:200]
            v = veredicto(crit, r, err) if crit else None
            if v:
                tot[0] += 1; tot[1] += v == "OK"; tot[2] += v in ("MAL", "ALUCINA")
            filas.append({"id": c["id"], "q": q, "crit": crit, "r": r, "v": v})
            if not callado:
                print(f"  {'·' if v is None else 'OK ' if v == 'OK' else 'XX ' + v[:4]:8s} > {q[:110]}\n             {(r or 'ERR ' + str(err))[:230]}")
        shutil.rmtree(mo._tmp, ignore_errors=True)
    print(f"\n== {mod}  n={tot[0]}  acierto={100 * tot[1] / max(1, tot[0]):.1f}%  falsas={tot[2]}")
    json.dump(filas, open(f"lab/iter232/ultimo_{mod}.json", "w"), ensure_ascii=False, indent=1)
    return filas


if __name__ == "__main__":
    a = [x for x in sys.argv[2:] if not x.startswith("-")]
    corre(sys.argv[1], a, "-q" in sys.argv)
