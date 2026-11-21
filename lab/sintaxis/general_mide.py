"""Mide la comprensión de textos variados. python -m lab.sintaxis.general_mide [lcm]   (con «lcm» mide el LCM tal como está, sin el analizador)"""
import json, re, shutil, sys, time
from lab.banco import veredicto
from lab.sintaxis.general_examen import T


def con_memoria(t):
    from src.sintaxis.relaciones import Memoria
    from lab.sintaxis.solar_mide import responde
    M = Memoria().lee(t["texto"])
    return [(q, c, responde(M, q)[0]) for q, c in t["preguntas"]], len(M.R)


def con_lcm(t):
    from lab.banco import motor
    mo = motor()
    mo.chat("Te voy a leer un texto.\n" + t["texto"].strip())
    out = [(q, c, mo.chat(q).get("respuesta") or "") for q, c in t["preguntas"]]
    shutil.rmtree(mo._tmp, ignore_errors=True)
    return out, 0


def clase(c, a):
    v = veredicto(c, a, None)
    if v == "OK":
        return "bien"
    if re.search(r"no lo s[eé]|no s[eé] qui[eé]n|no me has|no lo he le[ií]do|no aparece|no me consta|no tengo", a.lower()):
        return "se abstiene" if c != "ABST" else "bien"
    return "mal"


if __name__ == "__main__":
    modo = "lcm" if "lcm" in sys.argv else "memoria"
    tot = {"bien": 0, "se abstiene": 0, "mal": 0}
    filas = []
    for t in T:
        rs, nrel = (con_lcm if modo == "lcm" else con_memoria)(t)
        c = {"bien": 0, "se abstiene": 0, "mal": 0}
        for q, cr, a in rs:
            k = clase(cr, a); c[k] += 1; tot[k] += 1
            filas.append({"texto": t["id"], "q": q, "crit": cr, "r": a, "v": k})
            if "-v" in sys.argv or k != "bien":
                print(f"   {k:11s} | {q[:50]:50s} | {a[:120]}")
        print(f"{t['id']:9s} {t['estilo'][:34]:34s} bien {c['bien']:2d}/{len(rs)}  se abstiene {c['se abstiene']}  mal {c['mal']}" + (f"  ({nrel} relaciones)" if nrel else ""))
    n = sum(tot.values())
    print(f"\nTOTAL ({modo}): bien {tot['bien']}/{n} = {100 * tot['bien'] / n:.1f} %   se abstiene {tot['se abstiene']}   mal {tot['mal']}")
    json.dump(filas, open(f"lab/sintaxis/res_general_{modo}.json", "w"), ensure_ascii=False, indent=1)
