"""Frases CORTAS y simples con arbol conocido, hechas con las palabras reales del corpus (parche-34).

Los corpus UD son prensa: casi no hay frases como "Pedro vive en Madrid". Aqui se mina de las propias frases UD el
vocabulario (nombres propios, verbos conjugados con su lema, sustantivos con su articulo) y se combina en marcos simples.
Sintacticamente son correctas; semanticamente pueden ser absurdas ("Pedro abrio la lluvia"), y no importa: ensenan estructura.
Es un APOYO para el hueco de frases cortas, no un sustituto del espanol real.
"""
from __future__ import annotations

import random
from typing import List, Sequence

DET_LEMMA = {"el": "el", "la": "el", "un": "uno", "una": "uno"}


def mine(sents: Sequence[Sequence[tuple]]) -> dict:
    names, nouns, verbs_obj, verbs_obl, verbs_any = set(), {}, {}, {}, {}
    for s in sents:
        n = len(s)
        for j, (form, upos, head, rel, lemma) in enumerate(s):
            if upos == "PROPN" and rel in ("nsubj", "obj", "obl", "nmod") and form[:1].isupper() and form.isalpha() and len(form) > 2 \
                    and not any(w[3] == "flat" and w[2] == j + 1 for w in s):
                names.add(form)
            if upos == "NOUN" and j > 0 and s[j - 1][1] == "DET" and s[j - 1][2] == j + 1 and s[j - 1][3] == "det" \
                    and s[j - 1][0].lower() in DET_LEMMA and form.isalpha() and form.islower():
                nouns[(s[j - 1][0].lower(), form)] = lemma
            if upos == "VERB" and form.islower() and form.isalpha() and lemma != form and not form.endswith(("ndo", "ado", "ido", "ada", "ida", "ados", "idos", "adas", "idas")) \
                    and lemma.endswith(("ar", "er", "ir")):
                kids = [(k, w) for k, w in enumerate(s) if w[2] == j + 1]
                if any(w[3] == "aux" for _, w in kids):
                    continue
                subj = [w for _, w in kids if w[3] == "nsubj" and w[1] == "PROPN"]
                if not subj:
                    continue
                verbs_any[(form, lemma)] = 1
                if any(w[3] == "obj" and w[1] == "NOUN" for _, w in kids):
                    verbs_obj[(form, lemma)] = 1
                for k, w in kids:
                    if w[3] == "obl" and w[1] in ("PROPN", "NOUN"):
                        preps = [x[0].lower() for x in s if x[2] == k + 1 and x[3] == "case"]
                        if preps and preps[0] in ("en", "con", "para", "desde", "por", "a", "de", "hacia", "sobre"):
                            verbs_obl[(form, lemma, preps[0])] = 1
    return {"names": sorted(names), "nouns": [(d, n, l) for (d, n), l in nouns.items()], "v_obj": sorted(verbs_obj),
            "v_obl": sorted(verbs_obl), "v_any": sorted(verbs_any)}


class _B:
    """Constructor de frases con referencias por etiqueta."""

    def __init__(self):
        self.w = []
        self.lab = {}

    def add(self, label, form, upos, rel, head_label, lemma=None):
        self.lab[label] = len(self.w) + 1
        self.w.append([form, upos, head_label, rel, lemma if lemma is not None else form.lower()])

    def done(self) -> List[tuple]:
        return [(f, u, 0 if h is None else self.lab[h], r, l) for f, u, h, r, l in self.w]


def _np(b, rng, voc, label, head_label, rel, allow_det=True):
    """Anade un sintagma nominal: nombre propio o 'det nombre'. Devuelve la palabra nucleo (etiqueta)."""
    if rng.random() < 0.5 or not allow_det:
        b.add(label, rng.choice(voc["names"]), "PROPN", rel, head_label)
    else:
        d, n, l = rng.choice(voc["nouns"])
        b.add(label + "d", d, "DET", "det", label)
        b.add(label, n, "NOUN", rel, head_label, l)
    return label


def make(voc: dict, n: int, seed: int = 0) -> List[List[tuple]]:
    rng = random.Random(seed)
    out = []
    if not (voc["names"] and voc["nouns"] and voc["v_any"]):
        return out
    while len(out) < n:
        b = _B()
        frame = rng.choice(["svo", "svo", "sobl", "sobl", "neg", "cop_de", "cop", "detsubj"])
        try:
            if frame in ("svo", "neg") and voc["v_obj"]:
                v = rng.choice(voc["v_obj"])
                b.add("s", rng.choice(voc["names"]), "PROPN", "nsubj", "v")
                if frame == "neg":
                    b.add("no", "no", "ADV", "advmod", "v")
                b.add("v", v[0], "VERB", "root", None, v[1])
                d, nn, l = rng.choice(voc["nouns"])
                b.add("od", d, "DET", "det", "o")
                b.add("o", nn, "NOUN", "obj", "v", l)
            elif frame == "sobl" and voc["v_obl"]:
                v = rng.choice(voc["v_obl"])
                b.add("s", rng.choice(voc["names"]), "PROPN", "nsubj", "v")
                b.add("v", v[0], "VERB", "root", None, v[1])
                b.add("p", v[2], "ADP", "case", "o")
                _np(b, rng, voc, "o", "v", "obl")
            elif frame == "cop_de":
                d, nn, l = rng.choice(voc["nouns"])
                b.add("s", rng.choice(voc["names"]), "PROPN", "nsubj", "n")
                b.add("c", "es", "AUX", "cop", "n", "ser")
                b.add("nd", d, "DET", "det", "n")
                b.add("n", nn, "NOUN", "root", None, l)
                b.add("p", "de", "ADP", "case", "o")
                b.add("o", rng.choice(voc["names"]), "PROPN", "nmod", "n")
            elif frame == "cop":
                d, nn, l = rng.choice(voc["nouns"])
                b.add("s", rng.choice(voc["names"]), "PROPN", "nsubj", "n")
                b.add("c", "es", "AUX", "cop", "n", "ser")
                b.add("nd", d, "DET", "det", "n")
                b.add("n", nn, "NOUN", "root", None, l)
            elif frame == "detsubj" and voc["v_obj"]:
                v = rng.choice(voc["v_obj"])
                d, nn, l = rng.choice(voc["nouns"])
                b.add("sd", d.capitalize(), "DET", "det", "s")
                b.add("s", nn, "NOUN", "nsubj", "v", l)
                b.add("v", v[0], "VERB", "root", None, v[1])
                d2, n2, l2 = rng.choice(voc["nouns"])
                b.add("od", d2, "DET", "det", "o")
                b.add("o", n2, "NOUN", "obj", "v", l2)
            else:
                continue
            root = next(k for k in b.lab if b.w[b.lab[k] - 1][3] == "root")
            b.add("dot", ".", "PUNCT", "punct", root)
            out.append(b.done())
        except (IndexError, KeyError):
            continue
    return out
