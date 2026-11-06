"""Test de DISCURSO (parche-43, Fase 2): textos de 2 frases donde la segunda usa un pronombre ("Ella trabaja...") o tiene el
sujeto omitido ("Trabaja en un banco"). Formato como eval_frases: texto <TAB> s|p|o;s|p|o
Si existe src/language/discourse.py (parche siguiente) se usa su resolucion; si no, se lee cada frase por separado (LINEA BASE).

REGLA (fijada antes de medir): se da por buena la resolucion de sujetos si >= 70 % de los textos salen enteros (relajado).
"""
import sys

import torch

from scripts.eval_frases import key, load_gold
from src.language.school_parser import SchoolParser
from src.language.ud import load_school


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)
    try:
        from src.language.discourse import parse_text
        mode = "con resolucion de sujetos"
    except ImportError:
        import re

        def parse_text(parser, text):
            out = []
            for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
                out += parser.parse(sent) or []
            return out
        mode = "LINEA BASE (cada frase por separado)"
    gold = load_gold(sys.argv[1] if len(sys.argv) > 1 else "data/discurso_ciego.tsv")
    good = tp = fp = fn = 0
    bad = []
    for text, g in gold:
        pred = {(t["s"], t["p"], t["o"], t["neg"]) for t in parse_text(parser, text)}
        gk = {(s, key(p), o, n) for s, p, o, n in g}
        pk = {(s, key(p), o, n) for s, p, o, n in pred}
        tp += len(gk & pk); fp += len(pk - gk); fn += len(gk - pk)
        if gk == pk:
            good += 1
        else:
            bad.append((text, sorted(g), sorted(pred)))
    n = len(gold)
    print(f"Test de discurso ({n} textos) [{mode}]: textos enteros bien {good / n:.1%} | "
          f"precision {tp / max(tp + fp, 1):.1%}, cobertura {tp / max(tp + fn, 1):.1%}")
    for text, g, p in bad:
        print(text)
        print("   esperado:", g)
        print("   obtenido:", p)
    print(f"\nCriterio (>= 70 %): {'CUMPLE' if good / n >= .70 else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
