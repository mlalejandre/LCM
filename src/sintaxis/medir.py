"""Métricas del análisis sintáctico, en total y por longitud de frase (de la más sencilla a la más compleja)."""
from __future__ import annotations

from collections import Counter, defaultdict

from .datos import tramo


def mide(oro, pred):
    """oro: [[(forma, upos, cabeza, rel)]]; pred: [[(upos, cabeza, rel)]]. Devuelve {tramo: métricas} con 'todo' incluido."""
    C = defaultdict(Counter)
    for g, p in zip(oro, pred):
        for k in ("todo", tramo(len(g))):
            c = C[k]
            c["frases"] += 1
            bien = True
            for i, ((f, u, h, r), (pu, ph, pr)) in enumerate(zip(g, p)):
                c["pal"] += 1
                c["upos"] += pu == u
                for cat in ("DET", "ADP", "VERB", "NOUN", "PRON"):
                    if u == cat:
                        c[cat + "_n"] += 1; c[cat + "_ok"] += pu == u
                if u != "PUNCT":
                    c["dep"] += 1
                    c["uas"] += ph == h
                    c["las"] += ph == h and pr == r
                    bien = bien and ph == h and pr == r
                for fn in ("nsubj", "obj", "iobj", "obl", "det", "case"):
                    if r == fn:
                        c[fn + "_oro"] += 1; c[fn + "_ok"] += pr == fn and ph == h
                    if pr == fn:
                        c[fn + "_pred"] += 1
            c["entera"] += bien
            ro = next((i for i, x in enumerate(g) if x[2] == 0), None)
            rp = next((i for i, x in enumerate(p) if x[1] == 0), None)
            c["raiz"] += ro is not None and ro == rp
            if ro is not None and g[ro][1] in ("VERB", "AUX"):                 # ¿la oración principal lleva sujeto dicho, o va implícito?
                so = any(x[2] == ro + 1 and x[3] == "nsubj" for x in g)
                sp = any(x[1] == ro + 1 and x[2] == "nsubj" for x in p)
                c["suj_casos"] += 1; c["suj_ok"] += so == sp
                if not so:
                    c["impl_n"] += 1; c["impl_ok"] += not sp
    out = {}
    for k, c in C.items():
        def pc(a, b):
            return round(100.0 * c[a] / c[b], 1) if c[b] else None
        def f1(fn):
            p = c[fn + "_ok"] / c[fn + "_pred"] if c[fn + "_pred"] else 0.0
            r = c[fn + "_ok"] / c[fn + "_oro"] if c[fn + "_oro"] else 0.0
            return round(100.0 * 2 * p * r / (p + r), 1) if p + r else 0.0
        out[k] = {"frases": c["frases"], "categoria": pc("upos", "pal"), "determinantes": pc("DET_ok", "DET_n"), "preposiciones": pc("ADP_ok", "ADP_n"),
                  "verbos": pc("VERB_ok", "VERB_n"), "cabeza": pc("uas", "dep"), "cabeza_y_funcion": pc("las", "dep"), "verbo_principal": pc("raiz", "frases"),
                  "sujeto_F1": f1("nsubj"), "objeto_F1": f1("obj"), "complemento_F1": f1("obl"), "sujeto_dicho_o_implicito": pc("suj_ok", "suj_casos"),
                  "sujeto_implicito_detectado": pc("impl_ok", "impl_n"), "frase_entera": pc("entera", "frases")}
    return out


ORDEN = ["1-5", "6-10", "11-20", "21-40", "41+", "todo"]


def tabla(m, claves=("categoria", "determinantes", "preposiciones", "cabeza", "cabeza_y_funcion", "verbo_principal", "sujeto_F1", "sujeto_implicito_detectado", "objeto_F1", "frase_entera")):
    ls = ["palabras    frases  " + " ".join(f"{k[:11]:>11s}" for k in claves)]
    for t in ORDEN:
        if t in m:
            ls.append(f"{t:10s} {m[t]['frases']:6d}  " + " ".join(f"{(m[t][k] if m[t][k] is not None else float('nan')):11.1f}" for k in claves))
    return "\n".join(ls)
