"""Experimento de aprendizaje al vuelo y olvido (parche-13).

Se enseñan, UNA TRAS OTRA, tres relaciones nuevas (con 5 ejemplos cada una) y se mide
despues de cada una: (a) si aprende la nueva, (b) si recuerda las anteriores nuevas,
(c) si conserva lo que sabia de fabrica. Variantes:
  sin_repaso      : solo ejemplos nuevos  (esperable: olvido catastrofico)
  sin_repaso+guardia: igual, pero revierte si rompe lo anterior
  repaso_base     : mezcla ejemplos del entrenamiento original
  repaso_total    : base + lecciones aprendidas antes
"""
import copy
import os
import pickle
import random
import torch
from scripts.evaluate_stress import load_model
from src.training.online import OnlineLearner

RULES = [("PADRE_DE", "HIJO_DE"), ("JEFE_DE", "SUBORDINADO_DE"), ("DUENO_DE", "PERTENENCIA_DE")]
K_EXAMPLES = 5


def build_space():
    with open("data/concept_space.pkl", "rb") as handle:
        base = pickle.load(handle)
    space = copy.deepcopy(base)
    for a, b in RULES:
        for name in (a, b):
            space.add_concept(name, features={"predicate": 1, "relation": 1, f"identity:{name}": 0.5}, kind="predicate")
    people = []
    for i in range(120):
        name = f"PERSONA_{i:03d}"
        space.add_concept(name, features={"individual": 1, "person": 1, f"identity:{name}": 0.5}, kind="entity")
        people.append(name)
    return base, space, people


def lessons_for(rule, pool, n, rng):
    a, b = rule
    chosen = set()
    while len(chosen) < n:
        chosen.add(tuple(rng.sample(pool, 2)))
    return [([(x, a, y)], (y, b, x)) for x, y in sorted(chosen)]


def run_variant(name, base, space, people, core, canary, old_eval, replay_core, replay_lessons, guard, device):
    rng = random.Random(7)
    torch.manual_seed(0)
    model = load_model(base, space, device)
    learner = OnlineLearner(model, space, core, canary, device=device)
    held_out = people[90:]
    tests = [learner.encode(lessons_for(rule, held_out, 40, random.Random(99))) for rule in RULES]
    rows = []
    for step, rule in enumerate(RULES):
        info = learner.learn(lessons_for(rule, people[:90], K_EXAMPLES, rng),
                             replay_core=replay_core, replay_lessons=replay_lessons, guard=guard)
        learned = [learner.exact(*tests[i]) for i in range(step + 1)]
        rows.append((step + 1, info["accepted"], learned, learner.exact(*old_eval)))
    print(f"\n--- {name} ---")
    for step, accepted, learned, old in rows:
        txt = " ".join(f"{x:5.0%}" for x in learned)
        print(f"  tras regla {step}: {'aceptada ' if accepted else 'REVERTIDA'} | reglas nuevas [{txt}] | conocimiento de fabrica {old:5.0%}")
    return rows


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    base, space, people = build_space()
    with open("data/concept_train_dataset.pkl", "rb") as handle:
        train = pickle.load(handle).tensors
    with open("data/concept_val_dataset.pkl", "rb") as handle:
        val = pickle.load(handle).tensors
    with open("data/concept_test_dataset.pkl", "rb") as handle:
        test = pickle.load(handle).tensors
    gen = torch.Generator().manual_seed(1)
    core_idx = torch.randperm(len(train[0]), generator=gen)[:4000]
    core = tuple(t[core_idx] for t in train)
    canary_idx = torch.randperm(len(val[0]), generator=gen)[:300]
    canary = tuple(t[canary_idx] for t in val)
    old_idx = torch.randperm(len(test[0]), generator=gen)[:600]
    old_eval = tuple(t[old_idx] for t in test)

    print("=== APRENDIZAJE AL VUELO: 3 reglas nuevas, 5 ejemplos cada una ===")
    print(f"(cada columna de 'reglas nuevas' es una regla, medida con personas nunca vistas)")
    run_variant("sin_repaso", base, space, people, core, canary, old_eval, False, False, False, device)
    run_variant("sin_repaso + guardia", base, space, people, core, canary, old_eval, False, False, True, device)
    run_variant("repaso_base", base, space, people, core, canary, old_eval, True, False, True, device)
    run_variant("repaso_total (base + lecciones)", base, space, people, core, canary, old_eval, True, True, True, device)


if __name__ == "__main__":
    main()
