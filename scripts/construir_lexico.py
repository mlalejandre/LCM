"""Construye data/lexico_es.json (sinonimos, antonimos, hiperonimos) a partir de datos abiertos:
  - Multilingual Central Repository (MCR) espanol, via Open Multilingual WordNet 1.4 (CC BY 3.0, http://adimen.si.ehu.es/web/MCR/)
  - Princeton WordNet 3.0 (relaciones entre sentidos; licencia WordNet, https://wordnet.princeton.edu/license-and-commercial-use)
Uso: python -m scripts.construir_lexico <carpeta omw-1.4> <carpeta wordnet>   (las dos carpetas salen de nltk_data: corpora/omw-1.4 y corpora/wordnet)"""
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def nrm(w):
    w = unicodedata.normalize("NFD", w.lower().replace("_", " "))
    return "".join(c for c in w if unicodedata.category(c) != "Mn").strip()


def main(omw, wn):
    spa = {}
    for ln in open(os.path.join(omw, "mcr", "wn-data-spa.tab"), encoding="utf-8"):
        if ln.startswith("#") or "\t" not in ln:
            continue
        sid, typ, lem = (ln.rstrip("\n").split("\t") + ["", "", ""])[:3]
        if typ == "lemma" and lem:
            spa.setdefault(sid, [])
            lem = lem.replace("_", " ")
            if lem not in spa[sid]:
                spa[sid].append(lem)
    hyp, ant = {}, {}
    for pos in ("noun", "verb", "adj", "adv"):
        for ln in open(os.path.join(wn, "data." + pos), encoding="latin-1"):
            if ln.startswith("  "):
                continue
            p = ln.split(" ")
            off, ss = p[0], p[2].replace("s", "a")
            sid = f"{off}-{ss}"
            nw = int(p[3], 16)
            i = 4 + 2 * nw
            for k in range(int(p[i])):
                sym, o2, pos2, _st = p[i + 1 + 4 * k:i + 5 + 4 * k]
                tid = f"{o2}-{pos2.replace('s', 'a')}"
                if sym in ("@", "@i"):
                    hyp.setdefault(sid, []).append(tid)
                elif sym == "!":
                    ant.setdefault(sid, []).append(tid)
    allids = sorted(set(spa) | set(hyp) | set(ant) | {t for v in hyp.values() for t in v} | {t for v in ant.values() for t in v})
    num = {s_: i for i, s_ in enumerate(allids)}
    out = {"v": 2, "fuente": "MCR spa (CC BY 3.0) + Princeton WordNet 3.0", "n": len(allids),
           "syn": {str(num[s_]): v for s_, v in spa.items()}, "pos": {str(num[s_]): s_[-1] for s_ in spa},
           "hyp": {str(num[s_]): [num[t] for t in v] for s_, v in hyp.items()},
           "ant": {str(num[s_]): [num[t] for t in v] for s_, v in ant.items() if s_ in spa and any(t in spa for t in v)}}
    out["ant"] = {k: [j for j in v if allids[j] in spa] for k, v in out["ant"].items()}
    dst = os.path.join(ROOT, "data", "lexico_es.json")
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ids = allids
    print(f"lexico: {len(spa)} sentidos con lemma espanol, {len(out['hyp'])} con hiperonimo, {len(out['ant'])} con antonimo -> {dst} ({os.path.getsize(dst) // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
