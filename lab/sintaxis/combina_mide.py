"""LCM + memoria de relaciones: el LCM contesta como siempre; si no sabe o solo copia la frase, contesta la memoria con la pieza exacta."""
import re, shutil, sys
from lab.banco import motor, veredicto
from lab.sintaxis.general_mide import clase
from lab.sintaxis.solar_mide import responde
from src.sintaxis.relaciones import Memoria, limpia

ABS = r"no lo s[eé]|no s[eé] qui[eé]n|no me has|no lo he le[ií]do|no aparece|no me consta|no tengo|no he entendido"


def combina(a, m, q=""):
    """Primero la memoria de relaciones (da la pieza exacta y sabe con qué seguridad). Si no tiene nada, el LCM de siempre; pero si el LCM
    solo copia una frase del texto, esa frase tiene que hablar de lo que se pregunta: si no, es mejor decir que no se sabe."""
    if m is not None:
        return m
    if "En el texto pone" in a:
        from src.sintaxis.relaciones import _lema, _VACIAS, sa
        from src.sintaxis.analiza import palabras
        cita = a.split("«", 1)[-1]
        en_cita = {_lema(w) for w in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", cita)}
        pide = {_lema(p["forma"]) for p in palabras(q) if p["cat"] in ("NOUN", "PROPN")}
        if pide and not pide <= en_cita:
            return "No lo sé: eso no lo he leído."
    return a


def corre(nombre, texto, preguntas, tot):
    M = Memoria().lee(texto)
    mo = motor()
    mo.chat("Te voy a leer un texto.\n" + limpia(texto)[:7500])
    c = {"lcm": 0, "memoria": 0, "juntos": 0}
    mal = {"lcm": 0, "memoria": 0, "juntos": 0}
    for q, cr in preguntas:
        a = mo.chat(q).get("respuesta") or ""
        mm, r = responde(M, q)
        m = mm if r is not None or "No lo sé" not in mm else None
        j = combina(a, m, q)
        for k, x in (("lcm", a), ("memoria", mm), ("juntos", j)):
            cl = clase(cr, x); c[k] += cl == "bien"; mal[k] += cl == "mal"
        if clase(cr, j) != "bien" and "-v" in sys.argv:
            print(f"      {q[:48]:48s} | LCM: {a[:70]} | MEM: {mm[:50]}")
    shutil.rmtree(mo._tmp, ignore_errors=True)
    n = len(preguntas)
    print(f"{nombre:10s} n={n:2d}   LCM {c['lcm']:2d} (mal {mal['lcm']})   memoria {c['memoria']:2d} (mal {mal['memoria']})   juntos {c['juntos']:2d} (mal {mal['juntos']})")
    for k in c:
        tot[k][0] += c[k]; tot[k][1] += mal[k]
    tot["n"] += n


if __name__ == "__main__":
    from lab.sintaxis.general_examen import T
    from lab.sintaxis.solar_preguntas import P
    tot = {"lcm": [0, 0], "memoria": [0, 0], "juntos": [0, 0], "n": 0}
    for t in T:
        corre(t["id"], t["texto"], t["preguntas"], tot)
    print(f"GENERAL    n={tot['n']}   LCM {tot['lcm']}   memoria {tot['memoria']}   juntos {tot['juntos']}   (aciertos, respuestas equivocadas)")
    tot2 = {"lcm": [0, 0], "memoria": [0, 0], "juntos": [0, 0], "n": 0}
    corre("solar", open("/tmp/solar_crudo.txt", encoding="utf-8").read(), P, tot2)
