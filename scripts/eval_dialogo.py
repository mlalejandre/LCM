"""Test de CONVERSACION (parche-54): turnos U: con subcadena esperada. Criterio fijado ANTES de medir: >= 75 % (test propio), >= 60 % (test ciego)."""
import os
import sys
import tempfile
from datetime import date

import torch

from src.language.dialogue import Conversation
from src.language.lexicon import norm
from src.language.qa import QA
from src.language.school_parser import SchoolParser
from src.language.ud import load_school
from src.memory.store import MemoryStore
from src.reasoning.lessons import deduce_all


def blocks(path):
    cur, today = [], None
    seed = [False]
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#"):
            continue
        if line.startswith("HOY:"):
            today = line[4:].strip()
        elif line.startswith("SEMILLA:"):
            seed[0] = True
        elif not line.strip():
            if cur:
                yield cur, today, seed[0]
            cur = []
        elif line.startswith("U:"):
            body = line[2:].strip()
            turn, _, exp = body.partition("\t")
            cur.append((turn.strip(), exp.strip()))
    if cur:
        yield cur, today, seed[0]


def run(path="data/dialogo_prueba.tsv", quiet=False):
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)
    total = good = 0
    bad = []
    for turns, today, seeded in blocks(path):
        with tempfile.TemporaryDirectory() as d:
            mem = MemoryStore(os.path.join(d, "m.json"))
            mem.today = parser.today = date.fromisoformat(today) if today else None
            conv = Conversation(mem, parser, lambda m, p: QA(m, p.parse, lambda facts: deduce_all(facts, m.active_lessons())))
            if seeded:
                from src.language.semilla import load_seed
                load_seed(mem, parser)
            for turn, exp in turns:
                ans = conv.say(turn)
                if not exp:
                    continue
                total += 1
                a = norm(ans)
                ok = (norm(exp[1:]) not in a) if exp.startswith("!") else (norm(exp) in a)
                if ok:
                    good += 1
                else:
                    bad.append((turn, exp, ans))
    return good, total, bad


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/dialogo_prueba.tsv"
    good, total, bad = run(path)
    rate = good / max(total, 1)
    print(f"Test de conversacion: {good}/{total} = {rate:.1%}")
    for turn, exp, ans in bad:
        print(f"  FALLO {turn}  esperado={exp}  obtenido={ans}")
    limit = .60 if "ciego" in path or "ciega" in path else .70 if ("coherencia" in path or "definiciones" in path or "nucleo_prueba" in path) else .75
    print(f"\nCriterio (>= {limit:.0%}): {'CUMPLE' if rate >= limit else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
