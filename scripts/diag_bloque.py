"""Diagnostico de un bloque de examen (parche-73).

    python -m scripts.diag_bloque data/cantidad_prueba.tsv "mas alto"

El primer argumento es el fichero de examen (formato H:/P:/R:); el segundo, un texto que debe aparecer (sin tildes, en minusculas) en
alguna linea del bloque. No cambia nada del sistema: solo lee.
"""
import os
import sys
import tempfile
import unicodedata

import torch

from scripts.eval_preguntas import add_rule, blocks, make_deduce, ok
from src.language.qa import QA, rewrite
from src.language.school_parser import SchoolParser
from src.language.ud import load_school
from src.memory.store import MemoryStore
from src.reasoning.lessons import compare


def plano(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def arbol(parser, sentence):
    try:
        return " ".join(f"{i + 1}:{w[0]}/{w[1]}->{w[2]}:{w[3]}({w[4] if len(w) > 4 else ''})" for i, w in enumerate(parser.tree(sentence)))
    except Exception as exc:                                   # noqa
        return f"(sin arbol: {exc})"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    path, filtro = sys.argv[1], plano(sys.argv[2])
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)
    n = 0
    for b in blocks(path):
        texto = plano(" ".join(b["H"] + [q for q, _ in b["P"]] + b.get("R", [])))
        if filtro not in texto:
            continue
        n += 1
        print("=" * 100)
        print(f"BLOQUE {n}")
        facts = []
        with tempfile.TemporaryDirectory() as d:
            mem = MemoryStore(os.path.join(d, "m.json"))
            for sent in b["H"]:
                print(f"\nH: {sent}\n   arbol: {arbol(parser, sent)}")
                for t in parser.parse(sent) or []:
                    tr = (t["s"], t["p"], t["o"])
                    print(f"   proposicion: {tr} neg={t['neg']}")
                    mem.add_fact(tr, source=sent, neg=t["neg"], when=t.get("when", ""), when_disp=t.get("when_disp", ""), quant=t.get("q", ""))
                    mem.note_surface(tr, t.get("template"), t.get("s_disp"), t.get("o_disp"))
                    if not t["neg"]:
                        facts.append(tr)
            for rule in b.get("R", []):
                add_rule(mem, parser, rule)
            print("\ncompare() sobre esas proposiciones:")
            deducidas = compare(facts)
            for k in sorted(deducidas):
                print("   ", k)
            if not deducidas:
                print("    (nada deducido)")
            qa = QA(mem, parser.parse, make_deduce(mem))
            for q, exp in b["P"]:
                try:
                    cands, kind = rewrite(q)
                except Exception as exc:                       # noqa
                    cands, kind = [f"(error: {exc})"], "?"
                ans = qa.answer(q)
                print(f"\nP: {q}\n   reescritura: {kind} {cands[:2]}\n   esperado={exp}  obtenido={ans}  -> {'OK' if ok(ans, exp) else 'FALLO'}")
    if n == 0:
        print(f"Ningun bloque de {path} contiene {sys.argv[2]!r}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
