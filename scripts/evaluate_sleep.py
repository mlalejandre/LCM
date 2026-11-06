"""Experimento del ciclo de sueno (parche-14).

REGLA DE DECISION (fijada ANTES de medir): los "suenos" (repaso generativo desde
esquemas) se adoptan si, frente al sueno que solo repasa lecciones, suben la
generalizacion media de las reglas nuevas >= 5 puntos Y el conocimiento de fabrica
se mantiene >= 98 %. Si no, se descartan.

Protocolo: se ensenan 3 reglas nuevas con 3 ejemplos cada una, aprendiendo de
forma rapida y ligera ("vigilia": 40 pasos, solo repaso de fabrica). Luego se mide,
se duerme (segun la variante) y se vuelve a medir con personas nunca vistas.
"""
import os
import random
import tempfile
import torch
from scripts.evaluate_online import RULES, build_space, lessons_for
from scripts.evaluate_stress import load_model
from src.memory import MemoryStore
from src.memory.sleep import SleepCycle
from src.training.online import OnlineLearner
import pickle

K = 3


def setup(device):
    base, space, people = build_space()
    tr = pickle.load(open("data/concept_train_dataset.pkl", "rb")).tensors
    va = pickle.load(open("data/concept_val_dataset.pkl", "rb")).tensors
    te = pickle.load(open("data/concept_test_dataset.pkl", "rb")).tensors
    g = torch.Generator().manual_seed(1)
    ci = torch.randperm(len(tr[0]), generator=g)[:4000]
    vi = torch.randperm(len(va[0]), generator=g)[:300]
    oi = torch.randperm(len(te[0]), generator=g)[:600]
    return base, space, people, tuple(t[ci] for t in tr), tuple(t[vi] for t in va), tuple(t[oi] for t in te)


def measure(learner, tests, old):
    new = [learner.exact(*t) for t in tests]
    return new, learner.exact(*old)


def run_variant(name, sleep_kwargs, ctx, device):
    base, space, people, core, canary, old = ctx
    torch.manual_seed(0)
    model = load_model(base, space, device)
    learner = OnlineLearner(model, space, core, canary, device=device, steps=40)
    memory = MemoryStore(os.path.join(tempfile.mkdtemp(), "mem.json"))
    rng = random.Random(7)
    tests = [learner.encode(lessons_for(r, people[90:], 40, random.Random(99))) for r in RULES]
    for rule in RULES:
        lessons = lessons_for(rule, people[:90], K, rng)
        info = learner.learn(lessons, replay_core=True, replay_lessons=False, guard=True)
        if info["accepted"]:
            for p, c in lessons:
                memory.add_lesson(p, c)
    new_b, old_b = measure(learner, tests, old)
    line = f"  antes de dormir : reglas nuevas {' '.join(f'{x:4.0%}' for x in new_b)} (media {sum(new_b)/3:4.0%}) | fabrica {old_b:4.0%}"
    print(f"\n--- {name} ---\n{line}")
    if sleep_kwargs is None:
        return sum(new_b) / 3, old_b, sum(new_b) / 3, old_b
    cycle = SleepCycle(learner, memory, seed=3)
    rep = cycle.run(ledger=None, **sleep_kwargs)
    new_a, old_a = measure(learner, tests, old)
    print(f"  despues de dormir: reglas nuevas {' '.join(f'{x:4.0%}' for x in new_a)} (media {sum(new_a)/3:4.0%}) | fabrica {old_a:4.0%}"
          f" | lecciones archivadas {rep['compressed']} | revertido {rep['consolidate']['rolled_back']}")
    return sum(new_b) / 3, old_b, sum(new_a) / 3, old_a


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    ctx = setup(device)
    print("=== CICLO DE SUENO: 3 reglas nuevas, 3 ejemplos cada una ===")
    print("Regla: adoptar suenos si +5 pp frente a solo-lecciones y fabrica >= 98 %.")
    res = {}
    res["sin sueno"] = run_variant("sin sueno", None, ctx, device)
    res["solo lecciones"] = run_variant("sueno: solo repaso de lecciones", dict(use_dreams=False), ctx, device)
    res["con suenos"] = run_variant("sueno: lecciones + suenos (esquemas)", dict(use_dreams=True), ctx, device)
    a, b = res["solo lecciones"][2], res["con suenos"][2]
    verdict = (b - a >= 0.05) and res["con suenos"][3] >= 0.98
    print(f"\nDecision: suenos {b:.0%} vs solo lecciones {a:.0%} (diferencia {100*(b-a):+.1f} pp); "
          f"fabrica {res['con suenos'][3]:.0%} -> {'ADOPTADOS' if verdict else 'NO ADOPTADOS'}")


if __name__ == "__main__":
    main()
