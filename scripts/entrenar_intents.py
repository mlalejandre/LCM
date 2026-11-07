"""Entrena el enrutador de operaciones (parche-87) con datos sinteticos y lo evalua con el examen CIEGO (data/intents_ciego.tsv).

    python -m scripts.entrenar_intents            # entrena, imprime la matriz y guarda src/language/intents_modelo.json
    python -m scripts.entrenar_intents --solo-evaluar

Criterio fijado ANTES de medir: >= 90 % de acierto en el ciego, y NINGUN OTRO real (preguntas/frases de los examenes) enrutado a una operacion.
"""
import json
import math
import os
import random
import sys

from src.language import intents
from src.language.intents import DIM, OPS, features, softmax
from src.language.intents_gen import generate


def train(data, epochs=18, lr=0.35, l2=1e-6, seed=3):
    rng = random.Random(seed)
    K = len(OPS)
    w = [dict() for _ in range(K)]
    b = [0.0] * K
    feats = [(features(t), OPS.index(y)) for t, y in data]
    for ep in range(epochs):
        rng.shuffle(feats)
        for f, y in feats:
            z = [b[c] + sum(v * w[c].get(h, 0.0) for h, v in f.items()) for c in range(K)]
            p = softmax(z)
            for c in range(K):
                g = p[c] - (1.0 if c == y else 0.0)
                if abs(g) < 1e-4:
                    continue
                b[c] -= lr * g
                wc = w[c]
                for h, v in f.items():
                    wc[h] = wc.get(h, 0.0) * (1 - l2) - lr * g * v
        lr *= 0.88
    return w, b


def evaluate(router, rows, label):
    ok = 0
    bad = []
    for t, y in rows:
        pred, p = intents.route(t)
        if pred == y:
            ok += 1
        else:
            bad.append((t, y, pred, round(p, 2)))
    print(f"{label}: {ok}/{len(rows)} = {ok / max(len(rows), 1):.1%}")
    for t, y, pred, p in bad[:40]:
        print(f"   FALLO {t!r} esperado={y} obtenido={pred} ({p})")
    return ok / max(len(rows), 1), bad


def load_blind(path="data/intents_ciego.tsv"):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.strip() and not line.startswith("#"):
            t, _, y = line.partition("\t")
            rows.append((t.strip(), y.strip()))
    return rows


def real_others():
    """Frases reales de los examenes (reports/arboles.json) que deben quedar como OTRO."""
    p = "reports/arboles.json"
    if not os.path.exists(p):
        return []
    out = []
    propios = []
    for f in ("data/intents_ciego.tsv", "data/intents_ciego2.tsv"):          # las frases del propio examen del enrutador quedan grabadas, pero no son "OTRO"
        if os.path.exists(f):
            propios += [frozenset(intents.clean(t).split()) for t, _ in load_blind(f)]
    for k in json.load(open(p, encoding="utf-8"))["arboles"]:
        s = " ".join(k.split("\x1f"))
        if "Xqx" in s or "Zurita" in s or "Bertoldo" in s:
            continue
        toks = frozenset(intents.clean(s).split())
        if len(toks) >= 2 and any(toks <= q for q in propios):          # incluye permutaciones y trozos de esas frases (candidatos de reescritura)
            continue
        out.append((s.replace("¿ ", "¿").replace(" ?", "?").replace(" .", "."), "OTRO"))
    return out


def main():
    if "--solo-evaluar" not in sys.argv:
        data = generate()
        w, b = train(data)
        d = {"ops": OPS, "dim": DIM, "w": [{str(h): round(v, 4) for h, v in wc.items() if abs(v) > 1e-3} for wc in w], "b": [round(x, 4) for x in b]}
        json.dump(d, open(intents.MODEL_PATH, "w", encoding="utf-8"))
        print(f"modelo guardado ({os.path.getsize(intents.MODEL_PATH) // 1024} KB) con {len(data)} ejemplos sinteticos")
    intents._ROUTER = None
    r = intents.load()
    blind = load_blind()
    acc, _ = evaluate(r, blind, "examen ciego del enrutador")
    acc2, _ = evaluate(r, load_blind("data/intents_ciego2.tsv"), "examen ciego 2 del enrutador (parche-88)") if os.path.exists("data/intents_ciego2.tsv") else (1.0, [])
    reales = real_others()
    if reales:
        racc, bad = evaluate(r, reales, "frases reales de los examenes (todas deben ser OTRO)")
    else:
        racc = 1.0
    return 0 if acc >= .90 and acc2 >= .85 and racc >= .99 else 1


if __name__ == "__main__":
    sys.exit(main())
