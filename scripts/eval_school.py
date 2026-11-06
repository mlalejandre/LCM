"""Diagnostico de la escuela de espanol (parche-31): por que las proposiciones del arbol predicho no coinciden.

No reentrena: carga checkpoints/school.pt y mide, sobre las frases de PRUEBA:
  - precision / cobertura / F1 de proposiciones SUELTAS (no de la frase entera),
  - de las proposiciones humanas que se pierden, POR QUE: no hay sujeto, otro objeto, otra relacion...,
  - 20 frases con error, con las proposiciones humanas y las predichas.
"""
import random
from collections import Counter, defaultdict

import torch

from src.language.extract import triples
from src.language.ud import find_files, load_school, predict_trees, read_conllu


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    test = []
    for f in find_files("test"):
        test += read_conllu(f)[0]
    trees = predict_trees(model, [[w[0] for w in s] for s in test], device, scripts)
    tp = fp = fn = 0
    why = Counter()
    bad = []
    for s, t in zip(test, trees):
        gold = set(triples([(w[0], w[1], w[2], w[3], w[4]) for w in s]))
        pred = set(triples([(w[0], u, h, r, lm) for w, (u, h, r, lm) in zip(s, t)]))
        tp += len(gold & pred); fp += len(pred - gold); fn += len(gold - pred)
        for g in gold - pred:
            same_s = [p for p in pred if p[0] == g[0]]
            if not pred:
                why["no predice ninguna proposicion en la frase"] += 1
            elif not same_s:
                why["sujeto distinto o no encontrado"] += 1
            elif any(p[2] == g[2] and p[1] != g[1] for p in same_s):
                why["sujeto y objeto bien, relacion distinta (verbo/preposicion)"] += 1
            elif any(p[1] == g[1] and p[2] != g[2] for p in same_s):
                why["sujeto y relacion bien, objeto distinto"] += 1
            else:
                why["sujeto bien, relacion y objeto distintos"] += 1
        if gold != pred and len(bad) < 400:
            bad.append((s, gold, pred))
    # --- extractor v1 (sin resolver "que") frente a v2, a nivel de frase ---
    def sent_match(resolve, lens):
        ok, tot = defaultdict(int), defaultdict(int)
        for s, t in zip(test, trees):
            g = set(triples([(w[0], w[1], w[2], w[3], w[4]) for w in s], resolve))
            if not g:
                continue
            p = set(triples([(w[0], u, h, r, lm) for w, (u, h, r, lm) in zip(s, t)], resolve))
            b = next(name for name, hi in lens if len(s) <= hi)
            tot[b] += 1; ok[b] += g == p
        return ok, tot
    lens = [("<= 8 palabras", 8), ("9-15", 15), ("16-25", 25), ("> 25", 99)]
    print("\nFrases enteras con proposicion iguales a las humanas, por longitud:")
    for resolve, name in ((False, "extractor v1"), (True, "extractor v2 (que resuelto)")):
        ok, tot = sent_match(resolve, lens)
        print(f"  {name}: " + " | ".join(f"{b}: {ok[b]/max(tot[b],1):.0%} (de {tot[b]})" for b, _ in lens) +
              f" | total {sum(ok.values())/max(sum(tot.values()),1):.1%}")
    # --- acierto por funcion sintactica (cabeza Y etiqueta correctas) ---
    rel_ok, rel_tot = Counter(), Counter()
    for s, t in zip(test, trees):
        for w, (u, h, r, lm) in zip(s, t):
            rel_tot[w[3]] += 1
            rel_ok[w[3]] += (h == w[2]) and (r == w[3])
    print("\nAcierto por funcion (el humano dice X: acerto cabeza y funcion?):")
    for r in ("nsubj", "obj", "obl", "nmod", "cop", "case", "flat", "acl", "advmod", "root"):
        print(f"  {r:7s} {rel_ok[r]/max(rel_tot[r],1):5.1%}  (de {rel_tot[r]})")
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    print(f"Proposiciones sueltas en {len(test)} frases de prueba: precision {prec:.1%}, cobertura {rec:.1%}, F1 {2*prec*rec/max(prec+rec,1e-9):.1%}")
    print(f"  (humanas: {tp+fn}, predichas: {tp+fp}, acertadas: {tp})")
    print("\nDe las proposiciones humanas que se pierden:")
    tot = sum(why.values()) or 1
    for k, v in why.most_common():
        print(f"  {v/tot:5.1%}  {k}")
    print("\n--- 20 frases con diferencias ---")
    for s, g, p in random.Random(1).sample(bad, min(20, len(bad))):
        print(" ".join(w[0] for w in s)[:150])
        print("   humano :", sorted(g))
        print("   predicho:", sorted(p))


if __name__ == "__main__":
    main()
