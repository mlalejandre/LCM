"""Regenera data/vocabulario.txt (palabras conocidas para corregir erratas en PREGUNTAS). Nunca lo reduce: suma textos, cartuchos y extras.
Uso: python -m scripts.vocabulario"""
import glob
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def nrm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if unicodedata.category(c) != "Mn")


def main():
    voc = set()
    out = os.path.join(ROOT, "data", "vocabulario.txt")
    for f in [out, os.path.join(ROOT, "data", "vocabulario_extra.txt")]:
        if os.path.exists(f):
            voc |= {nrm(l.strip()) for l in open(f, encoding="utf-8") if l.strip() and not l.startswith("#")}
    for f in glob.glob(os.path.join(ROOT, "data", "textos", "*.txt")):
        voc |= set(nrm(w) for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]{4,}", open(f, encoding="utf-8").read()))
    for f in glob.glob(os.path.join(ROOT, "cartuchos", "*.json")):
        try:
            txt = json.dumps(json.load(open(f, encoding="utf-8")), ensure_ascii=False)
        except (OSError, ValueError):
            continue
        voc |= set(nrm(w) for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]{4,}", txt.replace("_", " ")))
    voc = {w for w in voc if re.fullmatch(r"[a-zñ]{4,}", w)}
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# Palabras conocidas (para corregir erratas en PREGUNTAS). Se regenera con: python -m scripts.vocabulario\n")
        fh.write("\n".join(sorted(voc)) + "\n")
    print(f"vocabulario: {len(voc)} palabras")


if __name__ == "__main__":
    main()
