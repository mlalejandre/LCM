"""Vacuna para relaciones NUEVAS (parche-33).

Fallo visto en tu Mac: tras  "Marta escribio una novela"  (relacion ESCRIBIO recien creada) el razonador contesto
NOVELA HIJO_DE MARTA. Una relacion nueva no tiene regla: lo correcto es SIN_CONCLUSION.

REGLA DE DECISION (fijada ANTES de medir). Tras aprender 3 reglas y dormir, se crean 6 relaciones nuevas:
  - se adopta  inoculate  si los falsos positivos con ellas bajan a <= 10 %,
  - las reglas nuevas no bajan mas de 3 puntos, la fabrica se mantiene >= 98 % y el canario no se revierte.
"""
import os
import random
import tempfile

import torch

from scripts.evaluate_online import RULES, lessons_for
from scripts.evaluate_sleep import setup
from scripts.evaluate_stress import load_model
from src.memory import MemoryStore
from src.memory.sleep import SleepCycle
from src.training.online import OnlineLearner

NEW = ["ESCRIBIO", "TRABAJA_EN", "PROFESORA_DE", "COME", "LLEGO_A", "CANTA_EN"]


def fp(learner, preds, people, n=40):
    rng = random.Random(11)
    ls = []
    for q in preds:
        for _ in range(n):
            x, y = rng.sample(people, 2)
            ls.append(([(x, q, y)], (x, "SIN_CONCLUSION", "NINGUNA")))
    return 1 - learner.exact(*learner.encode(ls))


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    base, space, people, core, canary, old = setup(device)
    torch.manual_seed(0)
    model = load_model(base, space, device)
    learner = OnlineLearner(model, space, core, canary, device=device, steps=40)
    memory = MemoryStore(os.path.join(tempfile.mkdtemp(), "mem.json"))
    rng = random.Random(7)
    tests = [learner.encode(lessons_for(r, people[90:], 40, random.Random(99))) for r in RULES]
    for rule in RULES:
        lessons = lessons_for(rule, people[:90], 3, rng)
        if learner.learn(lessons, replay_core=True, replay_lessons=False, guard=True)["accepted"]:
            for p, c in lessons:
                memory.add_lesson(p, c)
    SleepCycle(learner, memory, seed=3).run(ledger=None)
    for q in NEW:                                   # igual que hace think al crear una relacion
        space.add_concept(q, features={"predicate": 1, "relation": 1, f"identity:{q}": 0.5}, kind="predicate")
    model.set_space(space)
    model.to(device)
    acc = lambda: sum(learner.exact(*t) for t in tests) / len(tests)
    a0, f0, o0 = acc(), fp(learner, NEW, people[90:]), learner.exact(*old)
    print(f"\nANTES de la vacuna: reglas {a0:.0%} | fabrica {o0:.0%} | falsos positivos con relaciones nuevas {f0:.0%}")
    info = learner.inoculate(NEW)
    a1, f1, o1 = acc(), fp(learner, NEW, people[90:]), learner.exact(*old)
    print(f"DESPUES           : reglas {a1:.0%} | fabrica {o1:.0%} | falsos positivos con relaciones nuevas {f1:.0%}   ({info})")
    ok = info.get("done") and f1 <= 0.10 and a1 >= a0 - 0.03 and o1 >= 0.98
    print(f"\nDecision: falsos positivos {f0:.0%} -> {f1:.0%}; reglas {a0:.0%} -> {a1:.0%}; fabrica {o1:.0%} => "
          f"{'VACUNA ADOPTADA' if ok else 'NO ADOPTADA'}")


if __name__ == "__main__":
    main()
