"""Mide la memoria de relaciones con el texto del sistema solar. python -m lab.sintaxis.solar_mide <ruta del texto> [-v]"""
import re, sys, time
from lab.banco import veredicto
from lab.sintaxis.solar_preguntas import P
from src.sintaxis.relaciones import Memoria


def responde(M, q):
    m = re.match(r"^¿?\s*qu[eé] (?:me )?(?:puedes decir|sabes) (?:de|del|sobre|acerca de)(?: el| la| los| las)? (.+?)\??$", q.strip(), re.I)
    if m:
        s = M.sobre(m.group(1))
        return (" ".join(s), None) if s else ("No lo sé: eso no lo he leído.", None)
    r = M.pregunta(q)
    if not r:
        return "No lo sé: eso no lo he leído.", None
    return r["respuesta"], r


if __name__ == "__main__":
    t0 = time.time()
    M = Memoria().lee(open(sys.argv[1], encoding="utf-8").read())
    print(f"leído en {time.time() - t0:.1f} s: {M.frases} frases, {len(M.R)} relaciones, {len(M.N)} cantidades")
    ok = 0
    for q, c in P:
        a, r = responde(M, q)
        v = veredicto(c, a, None); ok += v == "OK"
        print(f"{v[:4]:4s} | {q[:52]:52s} | {a[:150]}")
    print(f"\nMEMORIA DE RELACIONES: {ok} de {len(P)}")
