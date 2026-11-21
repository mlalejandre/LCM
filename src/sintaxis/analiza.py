"""Usar el analizador entrenado: de una frase a sus partes (sujeto dicho o implícito, verbos, predicado, complementos con su preposición).
python -m src.sintaxis.analiza "Mi tío Manuel vive en Navarra y le gusta cazar jabalíes." """
from __future__ import annotations

import os, sys

from .datos import frases_de, trocea

_C = {}
RUTA = os.environ.get("LCM_ANALIZADOR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "analizador.pt")


def _carga():
    if "m" not in _C:
        import torch                                     # solo hace falta si el analizador está entrenado
        from .modelo import Analizador, Vocab
        ck = torch.load(RUTA, map_location="cpu")
        V = Vocab(ck["vocab"]["w"], ck["vocab"]["upos"], ck["vocab"]["rels"])
        m = Analizador(len(V.w), len(V.upos), len(V.rels))
        m.load_state_dict(ck["modelo"]); m.eval()
        _C["m"], _C["V"] = m, V
    return _C["m"], _C["V"]


def palabras(frase):
    """[{i, forma, cat, cabeza, funcion, seguro}] — `seguro` es la probabilidad que el modelo da a la cabeza elegida."""
    import torch
    with torch.no_grad():
        return _palabras(frase)


def _palabras(frase):
    import torch
    m, V = _carga()
    ws = trocea(frase)
    if not ws:
        return []
    X = torch.tensor([[V.rasgos(w) for w in ws]])
    H, tags, arcos = m(X)
    n = len(ws)
    for d in range(n):
        arcos[0, d, d + 1] = -1e9
    P = arcos.softmax(-1)
    cab = arcos.argmax(-1)
    rz = (cab[0] == 0).nonzero().flatten().tolist()
    mejor = int(arcos[0, :, 0].argmax())
    if len(rz) != 1:
        for d in rz:
            if d != mejor:
                arcos[0, d, 0] = -1e9
                cab[0, d] = arcos[0, d].argmax()
        cab[0, mejor] = 0
    fun = m.funciones(H, cab).argmax(-1)
    tg = tags.argmax(-1)
    return [{"i": j + 1, "forma": ws[j], "cat": V.upos[tg[0, j]], "cabeza": int(cab[0, j]), "funcion": V.rels[fun[0, j]], "seguro": round(float(P[0, j, cab[0, j]]), 2)} for j in range(n)]


def _rama(ps, i, sin=()):
    """Las palabras que cuelgan de la palabra i (ella incluida), en orden."""
    ids = {i}
    cambio = True
    while cambio:
        cambio = False
        for p in ps:
            if p["cabeza"] in ids and p["i"] not in ids and p["funcion"] not in sin:
                ids.add(p["i"]); cambio = True
    return [p for p in ps if p["i"] in ids]


def _txt(r):
    return " ".join(p["forma"] for p in r if p["cat"] != "PUNCT")


def oraciones(frase):
    """Las oraciones de una frase: [{verbo, sujeto, sujeto_tipo, objeto, complementos:[(prep, texto)], atributo, predicado, seguro}]."""
    ps = palabras(frase)
    out = []
    nucleos = [p for p in ps if p["funcion"] in ("root", "conj", "ccomp", "xcomp", "advcl", "acl", "parataxis") and (p["cat"] in ("VERB", "AUX") or any(q["cabeza"] == p["i"] and q["funcion"] == "cop" for q in ps))]
    if not nucleos:
        nucleos = [p for p in ps if p["funcion"] == "root"]
    for v in nucleos:
        hijos = [p for p in ps if p["cabeza"] == v["i"]]
        sub = [h for h in hijos if h["funcion"] in ("nsubj", "csubj")]
        cop = next((h for h in hijos if h["funcion"] == "cop"), None)
        o = {"verbo": (cop["forma"] if cop else v["forma"]), "tipo": v["funcion"], "sujeto": None, "sujeto_tipo": "implícito"}
        aux = [h["forma"] for h in hijos if h["funcion"] == "aux"]
        if aux:
            o["verbo"] = " ".join(aux + [o["verbo"]])
        if sub:
            o["sujeto"] = _txt(_rama(ps, sub[0]["i"], sin=("acl",)))
            o["sujeto_nucleo"] = sub[0]["forma"]
            o["sujeto_tipo"] = "explícito"
        elif v["funcion"] in ("conj", "xcomp", "advcl") and out:
            o["sujeto"] = out[0].get("sujeto"); o["sujeto_tipo"] = "el mismo que el anterior" if o["sujeto"] else "implícito"
        if cop:
            o["atributo"] = _txt(_rama(ps, v["i"], sin=("nsubj", "csubj", "cop", "conj", "cc", "punct", "obl", "advmod", "aux", "mark", "advcl", "parataxis")))
        ob = [h for h in hijos if h["funcion"] == "obj"]
        if ob:
            o["objeto"] = _txt(_rama(ps, ob[0]["i"], sin=("acl",)))
        io = [h for h in hijos if h["funcion"] in ("iobj", "expl")]
        if io:
            o["pronombres"] = [h["forma"] for h in io]
        comps = []
        for h in hijos:
            if h["funcion"] in ("obl", "nmod") or (h["funcion"] == "obj" and any(q["cabeza"] == h["i"] and q["funcion"] == "case" for q in ps)):
                prep = " ".join(q["forma"] for q in ps if q["cabeza"] == h["i"] and q["funcion"] == "case")
                comps.append((prep.lower(), _txt([q for q in _rama(ps, h["i"]) if not (q["cabeza"] == h["i"] and q["funcion"] == "case")])))
        if comps:
            o["complementos"] = comps
        mod = [h["forma"] for h in hijos if h["funcion"] == "advmod"]
        if mod:
            o["adverbios"] = mod
        o["determinantes"] = [(q["forma"], next((x["forma"] for x in ps if x["i"] == q["cabeza"]), "")) for q in _rama(ps, v["i"], sin=("conj", "parataxis")) if q["cat"] == "DET"]
        o["seguro"] = min([v["seguro"]] + [h["seguro"] for h in hijos if h["funcion"] in ("nsubj", "obj", "obl", "cop")])
        out.append(o)
    return out


def enseña(texto):
    for f in frases_de(texto):
        print("\n«" + f + "»")
        ps = palabras(f)
        print("   " + "  ".join(f"{p['forma']}/{p['cat']}" for p in ps))
        for o in oraciones(f):
            print(f"   · verbo: {o['verbo']}   sujeto: {o['sujeto'] or '—'} ({o['sujeto_tipo']})" + (f"   atributo: {o['atributo']}" if o.get("atributo") else "")
                  + (f"   objeto: {o['objeto']}" if o.get("objeto") else "") + ("   " + "; ".join(f"[{p}] {t}" for p, t in o.get("complementos", [])) if o.get("complementos") else "") + f"   (seguridad {o['seguro']})")


if __name__ == "__main__":
    enseña(" ".join(sys.argv[1:]))
