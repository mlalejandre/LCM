"""Test de PREGUNTAS (parche-35): ensena frases a una memoria vacia, hace preguntas y comprueba la respuesta.
Formato en data/preguntas_prueba.tsv. No usa el oido ni el razonador: mide escuela + QA (lo que cambia en este parche).

REGLA DE DECISION (fijada ANTES de medir): la Fase 1 se da por buena si acierta >= 70 % de las preguntas.
Con data/preguntas_ciegas.tsv (test ciego, escrito antes de medir) el criterio es >= 80 %.
Se informa tambien por tipo (si/no, quien, que/donde...) y las respuestas fallidas.
"""
import os
import sys
import tempfile

import torch

from src.language.lexicon import norm
from src.language.qa import QA
from src.language.school_parser import SchoolParser
from src.language.ud import load_school
from src.memory.store import MemoryStore


def blocks(path="data/preguntas_prueba.tsv"):
    path = sys.argv[1] if len(sys.argv) > 1 else path
    cur = {"H": [], "P": [], "R": [], "HOY": None}
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#"):
            continue
        if not line.strip():
            if cur["H"] or cur["P"]:
                yield cur
            cur = {"H": [], "P": [], "R": [], "HOY": None}
        elif line.startswith("HOY:"):
            cur["HOY"] = line[4:].strip()
        elif line.startswith("R:"):
            cur["R"].append(line[2:].strip())
        elif line.startswith("H:"):
            cur["H"].append(line[2:].strip())
        elif line.startswith("P:"):
            q, exp = line[2:].strip().split("\t")
            cur["P"].append((q.strip(), exp.strip()))
    if cur["H"] or cur["P"]:
        yield cur


def add_rule(mem, parser, text):
    """"Si A entonces B": cada mitad se lee con la escuela y se guarda como leccion."""
    body = text.strip().rstrip(".")
    low = norm(body)
    if not low.startswith("si ") or " entonces " not in low:
        return False
    a, b = body[3:].split(" entonces ", 1) if " entonces " in body else (None, None)
    pa, pb = parser.parse(a + "."), parser.parse(b + ".")
    if not pa or not pb or len(pb) != 1:
        return False
    mem.add_lesson([(t["s"], t["p"], t["o"]) for t in pa], (pb[0]["s"], pb[0]["p"], pb[0]["o"]))
    return True


def make_deduce(mem):
    from src.reasoning.lessons import deduce_all
    return lambda facts: deduce_all(facts, mem.active_lessons())


def ok(answer, expected):
    a = norm(answer)
    if expected == "SI":
        return a.startswith("si")
    if expected == "NO":
        return a.startswith("no.")
    if expected == "NOSE":
        return "no lo se" in a or "no me consta" in a
    return norm(expected) in a


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)
    total = good = 0
    bad = []
    for b in blocks():
        with tempfile.TemporaryDirectory() as d:
            mem = MemoryStore(os.path.join(d, "m.json"))
            if b.get("HOY"):
                from datetime import date
                mem.today = parser.today = date.fromisoformat(b["HOY"])
            else:
                mem.today = parser.today = None
            for sent in b["H"]:
                for t in parser.parse(sent) or []:
                    tr = (t["s"], t["p"], t["o"])
                    mem.add_fact(tr, source=sent, neg=t["neg"], when=t.get("when", ""), when_disp=t.get("when_disp", ""), quant=t.get("q", ""))
                    mem.note_surface(tr, t.get("template"), t.get("s_disp"), t.get("o_disp"))
            for rule in b.get("R", []):
                add_rule(mem, parser, rule)
            qa = QA(mem, parser.parse, make_deduce(mem))
            for q, exp in b["P"]:
                ans = qa.answer(q)
                total += 1
                if ok(ans, exp):
                    good += 1
                else:
                    kind, t = qa.read(q)
                    from src.language.qa import rewrite
                    bad.append((q, exp, ans + f"\n        [diagnostico] reescrito={rewrite(q)} leido={t}"
                                f" | memoria={[(f['s'], f['p'], f['o'], f.get('neg')) for f in mem.facts]}"))
    rate = good / max(total, 1)
    print(f"Test de preguntas: {good}/{total} = {rate:.1%}")
    for q, exp, ans in bad:
        print(f"  FALLO {q}  esperado={exp}  obtenido={ans}")
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    limit = .75 if ("deduccion" in arg or "conceptos" in arg or "tiempo" in arg or "herencia" in arg or "fechas" in arg) else .80 if "ciegas" in arg else .70
    if "estados" in arg or "cantidad" in arg:
        limit = .60 if "ciegas" in arg else .70
    print(f"\nCriterio (>= {limit:.0%}): {'CUMPLE' if rate >= limit else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
