"""Mide el oido con la regla fijada de antemano (parche-16).

REGLA (parche-18, ademas: f) rechaza >= 90 % de lo que no es afirmacion y g) acepta >= 90 % de las validas): el oido se adopta si
  (a) nombres nuevos + relaciones conocidas, (b) RELACIONES NUEVAS, y (e) frases "es un"/"son"
  aciertan >= 95 % la proposicion completa (sujeto, relacion, objeto Y polaridad), y
  (c)+(d) MARCOS DE FRASE NUNCA VISTOS suben a >= 60 % (en parche-15 eran ~30 %).
"""
import torch
from src.language.corpus import (CLAUSES_TEST, HEADS_TEST, HEADS_TRAIN, VERBS_TEST, VERBS_TRAIN, PredicatePool, base_pool,
                                 es_pool, make, make_negatives)
from src.language.ear import Ear, predict


def candidates():
    seen = {}
    for p in base_pool() + es_pool() + PredicatePool(HEADS_TRAIN, VERBS_TRAIN).items + PredicatePool(HEADS_TEST, VERBS_TEST).items:
        seen[p[1]] = p[0]
    return [(n, t) for t, n in seen.items()]


def score(ear, data, cands, device):
    outs = predict(ear, [x["tokens"] for x in data], cands, device)
    n = len(data)
    full = sum((o["subject"], o["predicate"], o["object"], o["negated"]) == (*x["triple"], x["neg"]) for o, x in zip(outs, data))
    s = sum(o["subject"] == x["triple"][0] for o, x in zip(outs, data))
    p = sum(o["predicate"] == x["triple"][1] for o, x in zip(outs, data))
    o_ = sum(o["object"] == x["triple"][2] for o, x in zip(outs, data))
    g = sum(o["negated"] == x["neg"] for o, x in zip(outs, data))
    return full / n, (s / n, p / n, o_ / n, g / n)


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    ear = Ear()
    ear.load_state_dict(torch.load("checkpoints/ear.pt", map_location="cpu"))
    ear.to(device)
    cands = candidates()
    train_pool = base_pool() + PredicatePool(HEADS_TRAIN, VERBS_TRAIN).items
    test_pool = PredicatePool(HEADS_TEST, VERBS_TEST).items
    cases = {
        "a) nombres nuevos, relaciones conocidas": make(1000, train_pool, 11, "test"),
        "b) RELACIONES NUEVAS, nombres nuevos": make(1000, test_pool, 12, "test"),
        "e) 'es un' / 'son' (nombres y categorias nuevos)": make(1000, es_pool(), 15, "test"),
        "c) MARCOS NUEVOS, relaciones conocidas": make(1000, train_pool + es_pool(), 13, "test", held_frames=True),
        "d) MARCOS NUEVOS + relaciones nuevas": make(1000, test_pool, 14, "test", held_frames=True),
    }
    res = {}
    print("=== EVALUACION DEL OIDO (proposicion + polaridad, exacta) ===")
    for name, data in cases.items():
        full, (s, p, o, g) = score(ear, data, cands, device)
        res[name[0]] = full
        print(f"  {name}: {full:6.1%}   (sujeto {s:.0%}, relacion {p:.0%}, objeto {o:.0%}, polaridad {g:.0%})")
    negs = make_negatives(1500, 21, "test")
    outs = predict(ear, [x["tokens"] for x in negs], cands, device)
    rej = sum(o["confidence"] < 0.8 for o in outs) / len(negs)
    pos = cases["a) nombres nuevos, relaciones conocidas"]
    outs = predict(ear, [x["tokens"] for x in pos], cands, device)
    acc = sum(o["confidence"] >= 0.8 for o in outs) / len(pos)
    print(f"  f) RECHAZA lo que no es una afirmacion (prosa, preguntas, fragmentos; {len(CLAUSES_TEST)} clausulas reales de prueba): {rej:6.1%}")
    print(f"  g) ACEPTA (confianza >= 80 %) las afirmaciones validas de (a): {acc:6.1%}")
    ok = all(res[k] >= 0.95 for k in "abe") and all(res[k] >= 0.60 for k in "cd") and rej >= 0.90 and acc >= 0.90
    print("\nDecision:", "OIDO ADOPTADO" if ok else "NO ADOPTADO del todo (ver filas por debajo del umbral)")


if __name__ == "__main__":
    main()
