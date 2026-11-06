"""Experimento de NEGATIVOS (parche-20).

Problema: tras ensenar "X PADRE_DE Y => Y HIJO_DE X" el modelo aplicaba la regla a cualquier
frase de dos personas (p. ej. "Paco HIJO_DE Jose" -> "Jose HIJO_DE Paco").

REGLA DE DECISION (fijada ANTES de medir): se adoptan los negativos si
  - falsos positivos con relaciones NO vistas como negativo <= 10 % (y bajan >= 20 puntos frente a no usarlos),
  - la precision de las reglas nuevas no baja mas de 3 puntos,
  - el conocimiento de fabrica se mantiene >= 98 %.
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

HELD = ["AMIGO_DE", "VECINO_DE"]          # relaciones sin regla, que NUNCA se usan como negativo al entrenar


def fp_sets(learner, people, held_base):
    rng = random.Random(5)
    out = {}
    for label, preds in (("conclusion como premisa", [b for _, b in RULES]), ("relaciones NO vistas", HELD + held_base)):
        lessons = []
        for q in preds:
            for _ in range(30):
                x, y = rng.sample(people, 2)
                lessons.append(([(x, q, y)], (x, "SIN_CONCLUSION", "NINGUNA")))
        out[label] = learner.encode(lessons)
    return out


def run(name, use_neg, ctx, device):
    base, space, people, core, canary, old = ctx
    for q in HELD:
        if q not in space.concept_to_id:
            space.add_concept(q, features={"predicate": 1, "relation": 1, f"identity:{q}": 0.5}, kind="predicate")
    torch.manual_seed(0)
    model = load_model(base, space, device)
    learner = OnlineLearner(model, space, core, canary, device=device, steps=40, use_negatives=use_neg)
    safe_base = [q for q in learner.safe() if q not in HELD and q not in [x for r in RULES for x in r]]
    held_base = sorted(safe_base)[:3]
    learner.neg_exclude = set(HELD) | set(held_base)
    memory = MemoryStore(os.path.join(tempfile.mkdtemp(), "mem.json"))
    rng = random.Random(7)
    tests = [learner.encode(lessons_for(r, people[90:], 40, random.Random(99))) for r in RULES]
    fps = fp_sets(learner, people[90:], held_base)
    for rule in RULES:
        lessons = lessons_for(rule, people[:90], 3, rng)
        info = learner.learn(lessons, replay_core=True, replay_lessons=False, guard=True)
        if info["accepted"]:
            for p, c in lessons:
                memory.add_lesson(p, c)
    SleepCycle(learner, memory, seed=3).run(ledger=None, use_dreams=True, use_negatives=use_neg)
    acc = sum(learner.exact(*t) for t in tests) / len(tests)
    res = {k: 1 - learner.exact(*v) for k, v in fps.items()}
    fabrica = learner.exact(*old)
    print(f"\n--- {name} ---")
    print(f"  reglas nuevas (personas nunca vistas): {acc:5.0%} | fabrica {fabrica:5.0%}")
    for k, v in res.items():
        print(f"  falsos positivos, {k}: {v:5.0%}")
    return acc, fabrica, res


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    ctx = setup(device)
    print("=== NEGATIVOS: 3 reglas nuevas, 3 ejemplos cada una, luego un sueno ===")
    a = run("sin negativos (parche-14)", False, ctx, device)
    b = run("con negativos (parche-20)", True, ctx, device)
    held = "relaciones NO vistas"
    ok = b[2][held] <= 0.10 and (a[2][held] - b[2][held]) >= 0.20 and b[0] >= a[0] - 0.03 and b[1] >= 0.98
    print(f"\nDecision: falsos positivos {a[2][held]:.0%} -> {b[2][held]:.0%}; reglas {a[0]:.0%} -> {b[0]:.0%}; fabrica {b[1]:.0%} => "
          f"{'NEGATIVOS ADOPTADOS' if ok else 'NO ADOPTADOS'}")


if __name__ == "__main__":
    main()
