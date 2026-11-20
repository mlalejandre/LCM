"""Banco de APRENDIZAJE: mide cómo aprende el LCM un tema con un texto. Uso: python -m lab.aprender.banco dev|test|setas [base|texto|frases]
Métricas: acierto y falsas por tipo de pregunta, y «frases cubiertas» = frases del texto cuyas sondas se aciertan todas."""
import importlib, json, sys
from collections import defaultdict
from lab.banco import motor, veredicto

NOMBRE = {"L": "literal", "P": "paráfrasis", "I": "inversa", "V": "vocabulario", "H": "herencia", "D": "deducción", "M": "combinar", "C": "charla", "G": "uso",
          "N": "no dicho", "K": "contradicción", "R": "retención"}


def temas(conjunto):
    if conjunto == "setas":
        from lab import aprender18 as A
        ls = A.TEXTO.split("\n")
        return [{"nombre": "setas", "intro": ls[0], "frases": [(x, []) for x in ls[1:]], "extra": [(t, q, c) for t, q, c in A.CONV if t != "-" or c],
                 "previo": [q for t, q, c in A.CONV[:2]]}]
    return importlib.import_module("lab.aprender." + conjunto).TEMAS


def corre_tema(tema, cond):
    import shutil
    mo = motor()
    filas = []
    for q in tema.get("previo", []):
        mo.chat(q)
    if cond == "texto":
        r = mo.chat(tema["intro"] + "\n" + "\n".join(f for f, _ in tema["frases"]))
        filas.append({"tema": tema["nombre"], "t": "-", "q": "(texto)", "r": r.get("respuesta"), "v": None, "k": -1})
    elif cond == "frases":
        for k, (f, _) in enumerate(tema["frases"]):
            r = mo.chat(f)
            filas.append({"tema": tema["nombre"], "t": "-", "q": f, "r": r.get("respuesta"), "v": None, "k": k})
    sondas = [(t, q, c, k) for k, (f, ss) in enumerate(tema["frases"]) for t, q, c in ss] + [(t, q, c, -1) for t, q, c in tema["extra"]]
    for t, q, c, k in sondas:
        try:
            o = mo.chat(q); resp, err = o.get("respuesta"), o.get("error")
        except Exception as e:                           # noqa
            resp, err = None, repr(e)[:200]
        v = veredicto(c, resp, err) if c else None
        filas.append({"tema": tema["nombre"], "t": t, "q": q, "crit": c, "r": resp if resp is not None else "ERR " + str(err), "v": v, "k": k})
    shutil.rmtree(mo._tmp, ignore_errors=True)
    return filas


def resumen(filas):
    d = defaultdict(lambda: [0, 0, 0])
    for f in filas:
        if not f["v"] or f["t"] == "-":
            continue
        for clave in (f["t"], "TOTAL"):
            d[clave][0] += 1; d[clave][1] += f["v"] == "OK"; d[clave][2] += f["v"] in ("MAL", "ALUCINA")
    porfrase = defaultdict(list)
    for f in filas:
        if f["v"] and f["k"] >= 0 and f["t"] != "-":
            porfrase[(f["tema"], f["k"])].append(f["v"] == "OK")
    cub = [all(v) for v in porfrase.values()]
    return {"tipos": {k: {"n": v[0], "ok": v[1], "falsas": v[2], "acierto": round(100 * v[1] / v[0], 1)} for k, v in d.items()},
            "frases_cubiertas": [sum(cub), len(cub)]}


def imprime(res, titulo):
    t = res["tipos"].get("TOTAL", {"n": 0, "acierto": 0, "falsas": 0})
    fc = res["frases_cubiertas"]
    print("== %s  n=%d  acierto=%.1f%%  falsas=%d  frases_cubiertas=%d/%d" % (titulo, t["n"], t["acierto"], t["falsas"], fc[0], fc[1]))
    print("   " + "  ".join("%s %d%%(%d)" % (NOMBRE.get(k, k)[:5], v["acierto"], v["n"]) for k, v in sorted(res["tipos"].items()) if k != "TOTAL"))


def main():
    conjunto = sys.argv[1] if len(sys.argv) > 1 else "dev"
    conds = sys.argv[2:] or ["base", "texto"]
    verb = "-v" in conds
    conds = [c for c in conds if c != "-v"]
    for cond in conds:
        filas = []
        for tema in temas(conjunto):
            fs = corre_tema(tema, cond)
            filas += fs
            imprime(resumen(fs), "%s/%s/%s" % (conjunto, tema["nombre"], cond))
            if verb:
                for f in fs:
                    if f["v"] not in (None, "OK") or f["t"] == "-":
                        print("   %s %-5s > %s\n            %s" % (f["t"], (f["v"] or "")[:5], f["q"][:90], (f["r"] or "")[:200]))
        res = resumen(filas)
        imprime(res, "TOTAL %s/%s" % (conjunto, cond))
        json.dump({"resumen": res, "filas": filas}, open("lab/res_aprender_%s_%s.json" % (conjunto, cond), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
