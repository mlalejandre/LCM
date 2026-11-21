"""Auditoría del DICCIONARIO: para cada paráfrasis fallada, qué palabra de la pregunta no está en el texto y cómo la ve el léxico frente a
cada palabra del texto (enlace, peso, vectores, puentes). Uso: python -m lab.lexico.audita <prefijo de resultados> [conjunto…]"""
import glob, json, re, sys, types
from lab.aprender.banco import temas
from src.nucleo20 import sinonimia as S, vectores as V
from src.nucleo20.morfo import sa
from src.nucleo20 import morfo as M


def vocab(tema):
    nuc = types.SimpleNamespace(usuario={"leido": [{"frases": [f for f, _ in tema["frases"]]}]}, F=[], notas=[])
    return S.vocabulario(nuc)


def fuera(q, verbos, nombres):
    out = []
    ws = re.findall(r"[a-záéíóúñü]+", q.lower())
    for i, w in enumerate(ws):
        if i == 0 or len(w) < 4:
            continue
        an = [] if (w in S._NO_VERBO or ws[i - 1] in S._DETS) else S.analiza(w)
        if an:
            l = sa(an[0][0])
            if l not in S._FUNC and l not in verbos:
                out.append(("v", l))
        else:
            b = sa(M.singular(w))
            if b not in nombres and sa(w) not in nombres:
                out.append(("n", b))
    return out


def ficha(a, b):
    t, p = V.parentesco(a, b)
    return {"enlace": t, "peso": round(p, 2), "vec": round(V.sim(a, b), 2), "puente": V.puente(a, b), "afin": round(S._afin(a, b), 2)}


if __name__ == "__main__":
    pre = sys.argv[1]
    for f in sorted(glob.glob(f"lab/iter224/{pre}_*_texto.json")):
        conj = f.split(pre + "_")[1][:-11]
        if sys.argv[2:] and conj not in sys.argv[2:]:
            continue
        d = json.load(open(f)); filas = d["filas"] if isinstance(d, dict) else d
        T = {t["nombre"]: t for t in temas(conj)}
        for x in filas:
            if x.get("t") != "P" or x.get("v") in (None, "OK"):
                continue
            verbos, nombres = vocab(T[x["tema"]])
            print(f"\n[{conj}] {x['v']} {x['q']}  ({x['crit']})\n    -> {(x['r'] or '')[:110]}")
            for k, l in fuera(x["q"], verbos, nombres):
                cs = sorted(((ficha(l, c), c) for c in (verbos if k == "v" else nombres)), key=lambda z: -(z[0]["afin"] + z[0]["vec"] + z[0]["peso"] + 0.1 * z[0]["puente"]))[:4]
                print("   ", k, l, "|", "; ".join(f"{c} {fi['enlace'] or '-'} p{fi['peso']} v{fi['vec']} i{fi['puente']} a{fi['afin']}" for fi, c in cs if fi['enlace'] or fi['vec'] > .2 or fi['puente']))
