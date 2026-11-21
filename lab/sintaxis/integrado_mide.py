"""El LCM completo (con o sin la capa de sintaxis, según LCM_SIN_SINTAXIS) con siete textos de temas distintos.\npython -m lab.sintaxis.integrado_mide [-v] [texto_del_sistema_solar.txt]"""
import shutil, sys
from lab.banco import motor
from lab.sintaxis.general_examen import T
from lab.sintaxis.general_mide import clase
from lab.sintaxis.solar_preguntas import P

def corre(nombre, texto, preguntas):
    mo = motor()
    mo.chat("Te voy a leer un texto.\n" + texto.strip())
    c = {"bien": 0, "se abstiene": 0, "mal": 0}
    for q, cr in preguntas:
        a = mo.chat(q).get("respuesta") or ""
        k = clase(cr, a); c[k] += 1
        if "-v" in sys.argv and k != "bien":
            print(f"      {k:11s} {q[:46]:46s} | {a[:110]}")
    shutil.rmtree(mo._tmp, ignore_errors=True)
    print(f"{nombre:9s} bien {c['bien']:2d}/{len(preguntas)}  se abstiene {c['se abstiene']}  mal {c['mal']}")
    return c

if __name__ == "__main__":
    tot = {"bien": 0, "se abstiene": 0, "mal": 0}
    for t in T:
        c = corre(t["id"], t["texto"], t["preguntas"])
        for k in tot: tot[k] += c[k]
    print(f"GENERAL   bien {tot['bien']}/72  se abstiene {tot['se abstiene']}  mal {tot['mal']}")
    otros = [a for a in sys.argv[1:] if not a.startswith("-")]
    if otros:                                            # python -m lab.sintaxis.integrado_mide <texto.txt>: además, el texto del sistema solar con sus preguntas
        corre("solar", open(otros[0], encoding="utf-8").read(), P)
