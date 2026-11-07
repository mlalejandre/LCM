"""Construye data/conceptos.json.gz: el DICCIONARIO DE CONCEPTOS del LCM.
Un concepto es un sentido universal (un synset de WordNet): el concepto "perro" es el mismo para "perro", "can", "dog" o "chien". Cada concepto lleva sus palabras en varios idiomas
(solo como nombres), su lugar en la jerarquia (es un tipo de...), sus partes/miembros/sustancias, su dominio (animal, artefacto, ...), su glosa y su frecuencia de uso.
Fuentes abiertas (ver data/CONCEPTOS_LICENCIAS.txt): Princeton WordNet 3.0; Open Multilingual WordNet 1.4 (MCR es/ca/gl/eu CC BY 3.0, MultiWordNet it CC BY 3.0, OpenWN-PT pt CC BY-SA 4.0, WOLF fr CeCILL-C).
Uso: python -m scripts.construir_conceptos <carpeta omw-1.4> <carpeta wordnet>   (de nltk_data: corpora/omw-1.4 y corpora/wordnet)"""
import gzip
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = [("es", "mcr/wn-data-spa.tab", "lemma"), ("ca", "mcr/wn-data-cat.tab", "lemma"), ("gl", "mcr/wn-data-glg.tab", "lemma"), ("eu", "mcr/wn-data-eus.tab", "lemma"),
         ("it", "ita/wn-data-ita.tab", "ita:lemma"), ("pt", "por/wn-data-por.tab", "lemma"), ("fr", "fra/wn-data-fra.tab", "fra:lemma")]
PTR_HYP, PTR_PART, PTR_MEMB, PTR_SUBST, PTR_ANT = {"@", "@i"}, {"%p"}, {"%m"}, {"%s"}, {"!"}


def main(omw, wn):
    syn = {}                                                    # id -> {"lex": n, "gloss": str, "en": [...], ptr: [(sym, id)]}
    for pos, ch in (("noun", "n"), ("verb", "v"), ("adj", "a"), ("adv", "r")):
        for ln in open(os.path.join(wn, "data." + pos), encoding="latin-1"):
            if ln.startswith("  "):
                continue
            head, _, gloss = ln.partition("|")
            p = head.split(" ")
            sid = f"{p[0]}-{p[2].replace('s', 'a')}"
            nw = int(p[3], 16)
            en = []
            for k in range(nw):
                w = p[4 + 2 * k].split("(")[0].replace("_", " ")
                if w not in en:
                    en.append(w)
            i = 4 + 2 * nw
            ptrs = []
            for k in range(int(p[i])):
                sym, o2, pos2, _st = p[i + 1 + 4 * k:i + 5 + 4 * k]
                ptrs.append((sym, f"{o2}-{pos2.replace('s', 'a')}"))
            syn[sid] = {"lex": int(p[1]), "gloss": gloss.split(";")[0].strip(), "en": en, "ptr": ptrs}
    lexnames = {int(a.split()[0]): a.split()[1] for a in open(os.path.join(wn, "lexnames"), encoding="utf-8") if a.strip()}
    freq, fen = {}, {}
    for ln in open(os.path.join(wn, "index.sense"), encoding="latin-1"):
        f = ln.split()
        if len(f) >= 4:
            ss = f[0].split("%")[1][0]
            ch = {"1": "n", "2": "v", "3": "a", "4": "r", "5": "a"}.get(ss)
            k_ = f"{f[1]}-{ch}"
            freq[k_] = freq.get(k_, 0) + int(f[3])
            fen.setdefault(k_, {})[f[0].split("%")[0].replace("_", " ").lower()] = int(f[3]) * 100 + max(0, 99 - int(f[2]))   # uso del sentido para ese lema (y orden de sentidos)
    lem = {}
    for lg, rel, typ in LANGS:
        d = {}
        for ln in open(os.path.join(omw, rel), encoding="utf-8"):
            if ln.startswith("#") or "\\t" in ln[:0]:
                continue
            f = ln.rstrip("\n").split("\t")
            if len(f) >= 3 and f[1] == typ and f[0] in syn:
                w = f[2].replace("_", " ")
                d.setdefault(f[0], [])
                if w not in d[f[0]]:
                    d[f[0]].append(w)
        lem[lg] = d
    keep = set(lem["es"])
    for s_ in syn:                                              # conceptos de uso comun (con frecuencia en WordNet) o con nombre en 2+ lenguas aunque falte el espanol
        if (freq.get(s_, 0) > 0 and s_.endswith("-n")) or sum(1 for lg in ("it", "pt", "fr", "ca", "gl") if s_ in lem[lg]) >= 2 and s_.endswith("-n"):
            keep.add(s_)
    todo = list(keep)
    while todo:                                                 # antepasados (es un tipo de...)
        s = todo.pop()
        for sym, t in syn[s]["ptr"]:
            if sym in PTR_HYP and t in syn and t not in keep:
                keep.add(t)
                todo.append(t)
    for s in list(keep):                                        # partes, miembros y sustancias (1 salto)
        for sym, t in syn[s]["ptr"]:
            if (sym in PTR_PART or sym in PTR_MEMB or sym in PTR_SUBST) and t in syn:
                keep.add(t)
    ids = sorted(keep)
    num = {s: i for i, s in enumerate(ids)}

    def rel(symset):
        out = {}
        for s in ids:
            tg = [num[t] for sym, t in syn[s]["ptr"] if sym in symset and t in num]
            if tg:
                out[str(num[s])] = tg
        return out
    out = {"v": 3, "ids": ids, "lex": [syn[s]["lex"] for s in ids], "lexnames": {str(k): v for k, v in lexnames.items()},
           "gloss": [syn[s]["gloss"][:140] for s in ids], "freq": [freq.get(s, 0) for s in ids], "fen": {str(num[s]): fen[s] for s in ids if s in fen},
           "lem": {"en": {str(num[s]): syn[s]["en"] for s in ids}}, "hyp": rel(PTR_HYP), "parte": rel(PTR_PART), "miembro": rel(PTR_MEMB), "sustancia": rel(PTR_SUBST), "ant": rel(PTR_ANT)}
    for lg, d in lem.items():
        out["lem"][lg] = {str(num[s]): v for s, v in d.items() if s in num}
    dst = os.path.join(ROOT, "data", "conceptos.json.gz")
    with gzip.open(dst, "wt", encoding="utf-8", compresslevel=9) as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"conceptos: {len(ids)} ({len(out['lem']['es'])} con palabra en espanol) -> {dst} ({os.path.getsize(dst) // 1024} KB)")
    for lg in out["lem"]:
        print("  ", lg, len(out["lem"][lg]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
