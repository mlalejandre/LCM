"""Traza de una paráfrasis: qué preguntas rehechas propone el sentido y por qué se aceptan o se rechazan.
Uso: python -m lab.lexico.traza <conjunto> "<trozo del nombre del tema>" "<pregunta>" ["<pregunta>"…]"""
import shutil, sys
from lab.banco import motor
from lab.aprender.banco import temas
from src.nucleo20 import sinonimia as S, lectura as L


def traza(conj, tema, qs):
    t = next(x for x in temas(conj) if tema in x["nombre"])
    mo = motor()
    mo.chat(t["intro"] + "\n" + "\n".join(f for f, _ in t["frases"]))
    n = mo._n20
    for q in qs:
        print("\n==", q)
        for duda in (False, True):
            for cand, cambios in S.por_sentido(n, q, duda=duda):
                n._reform = True
                try:
                    r = n._procesar_charla(cand)
                finally:
                    n._reform = False
                rr = (r or {}).get("respuesta") or ""
                c = L.cita(n, cand)
                print("  ", "DUDA" if duda else "SENT", cand, cambios)
                print("       núcleo:", (r or {}).get("estado"), rr[:90], "| tiempo", S.casa_tiempo(cambios, rr), "tipo", S.casa_tipo(q, rr), "firme", S.cita_firme(n, cand, cambios, rr))
                print("       cita:", (c or "")[:90], "| tiempo", S.casa_tiempo(cambios, c or ""), "firme", S.cita_firme(n, cand, cambios, c or ""))
        print("   =>", (mo.chat(q).get("respuesta") or "")[:160])
    shutil.rmtree(mo._tmp, ignore_errors=True)


if __name__ == "__main__":
    traza(sys.argv[1], sys.argv[2], sys.argv[3:])
