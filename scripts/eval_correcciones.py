"""Mide si la escuela APRENDE de las correcciones (parche-49). Todo en memoria: NO modifica checkpoints/school.pt.
Formato y criterios fijados antes de medir: data/correcciones_prueba.tsv.  Uso: python -m scripts.eval_correcciones"""
import copy
import sys

import torch

from scripts.eval_frases import evaluate, key
from src.language.school_learn import _key, learn_correction, replay_sentences, synthetic_replay
from src.language.school_parser import SchoolParser
from src.language.ud import load_school

FRASES, LARGAS = "data/frases_prueba.tsv", "data/frases_largas_ciegas.tsv"


def read(path="data/correcciones_prueba.tsv"):
    teach, test, test2 = [], [], []
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        kind, sent, gold = line.rstrip("\n").split("\t")
        s, p, o = gold.split("|")
        (teach if kind == "TEACH" else test2 if kind == "TEST2" else test).append((sent, (s, p, o)))
    return teach, test, test2


def score(parser, items):
    good, rows = 0, []
    for sent, (s, p, o) in items:
        found = parser.parse(sent) or []
        ok = any(t["s"] == s and t["o"] == o and _key(t["p"]) == _key(p) for t in found) and len(found) == 1
        good += ok
        rows.append((sent, ok, [(t["s"], t["p"], t["o"]) for t in found]))
    return good, rows


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    overrides = {}
    parser = SchoolParser(model, device, scripts, overrides)
    teach, test, test2 = read()
    base_test, _ = score(parser, test)
    base_test2, _ = score(parser, test2)
    base_conv = evaluate(parser, path=FRASES)[1]
    base_long = evaluate(parser, path=LARGAS)[1]
    print(f"ANTES: frases de prueba bien {base_test}/{len(test)} (TEST2: {base_test2}/{len(test2)}) | conversacion {base_conv:.1%} | largas {base_long:.1%}")
    replay = replay_sentences(n=150) + synthetic_replay(200)
    print(f"(repaso con {len(replay)} frases: texto normal + frases cortas de conversacion)")
    taught, done = [], 0
    canary = lambda: evaluate(parser, path=FRASES)[1]
    for sent, trip in teach:
        info = learn_correction(model, device, scripts, sent, trip, extra=taught, replay=replay, canary=canary, overrides=overrides)
        print(f"  ENTENDI {sent!r} -> {info}")
        if info["done"]:
            done += 1
            taught.append({"frase": sent, "triple": list(trip)})
    ok_taught, _ = score(parser, teach)
    after_test, rows = score(parser, test)
    after_test2, rows2 = score(parser, test2)
    conv = evaluate(parser, path=FRASES)[1]
    long_ = evaluate(parser, path=LARGAS)[1]
    print(f"\nDESPUES: ensenadas bien {ok_taught}/{len(teach)} | frases nuevas bien {after_test}/{len(test)} (TEST2: {after_test2}/{len(test2)}) | conversacion {conv:.1%} | largas {long_:.1%}")
    for sent, ok, found in rows + rows2:
        if not ok:
            print(f"   FALLO {sent} -> {found}")
    c1 = ok_taught == len(teach)
    c2 = (after_test + after_test2) / (len(test) + len(test2)) >= .5 and after_test + after_test2 > base_test + base_test2
    c3 = conv >= base_conv - .0125 - 1e-9 and long_ >= base_long - .037 - 1e-9
    print(f"\nCriterios: (1) ensenadas {'CUMPLE' if c1 else 'NO CUMPLE'} | (2) generaliza {'CUMPLE' if c2 else 'NO CUMPLE'} | (3) sin regresion {'CUMPLE' if c3 else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
