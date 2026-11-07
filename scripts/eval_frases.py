"""Test de CONVERSACION (parche-34): 60 frases cortas y simples con las proposiciones correctas escritas a mano
(data/frases_prueba.tsv). Es la medida directa de lo que importa para dialogar; los corpus UD son prensa.

Formato:  frase <TAB> s|p|o;s|p|o   (un ~ delante del sujeto marca negacion). Las relaciones se escriben con la forma base
(vivir_en, escribir, madre_de...).
Comparacion principal "RELAJADA": sujeto y objeto exactos y relacion igual en sus 3 primeras letras + la misma preposicion
(porque los lemas de nombres/verbos varian entre convenciones). Se informa tambien la EXACTA.

REGLA DE DECISION (fijada ANTES de medir): la escuela v2 se adopta si, en este test, acierta >= 75 % de las frases enteras
(relajado) y mejora en >= 10 puntos a la escuela v1 (que se mide con este mismo test antes de reentrenar).
"""
import sys

import torch

from src.language.school_parser import SchoolParser
from src.language.ud import load_school
from src.language.lexicon import norm


# parche-71: la "a" personal (conocer a Pablo) no distingue la relacion (igual que qa.pred_key). Se conserva donde marca destino
# o receptor: ir/llegar/volver/venir/entrar/viajar/regresar/salir a..., dar/regalar/vender/prestar/entregar/mandar/enviar a...
_A_MARCA = {"ir", "llegar", "volver", "venir", "entrar", "viajar", "regresar", "salir", "dar", "regalar", "vender", "prestar",
            "entregar", "mandar", "enviar"}


def key(p):
    head, _, prep = p.partition("_")
    if prep == "a" and head not in _A_MARCA:
        prep = ""
    return head[:3] + "|" + prep


def load_gold(path="data/frases_prueba.tsv"):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        sent, gold = line.split("\t")
        g = set()
        for t in gold.split(";"):
            neg = t.startswith("~")
            s, p, o = t.lstrip("~").split("|")
            g.add((s, p, o, neg))
        out.append((sent, g))
    return out


def evaluate(parser, verbose=False, path="data/frases_prueba.tsv"):
    gold = load_gold(path)
    exact = relaxed = tp = fp = fn = 0
    rows = []
    for sent, g in gold:
        found = parser.parse(sent) or []
        pred = {(t["s"], t["p"], t["o"], t["neg"]) for t in found}
        e = pred == g
        rl = {(s, key(p), o, n) for s, p, o, n in pred} == {(s, key(p), o, n) for s, p, o, n in g}
        exact += e; relaxed += rl
        gk = {(s, key(p), o, n) for s, p, o, n in g}; pk = {(s, key(p), o, n) for s, p, o, n in pred}
        tp += len(gk & pk); fp += len(pk - gk); fn += len(gk - pk)
        rows.append((sent, g, pred, rl))
    n = len(gold)
    return exact / n, relaxed / n, tp / max(tp + fp, 1), tp / max(tp + fn, 1), rows


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)
    path = sys.argv[1] if len(sys.argv) > 1 else "data/frases_prueba.tsv"
    ex, rl, pr, rc, rows = evaluate(parser, path=path)
    print(f"Test de conversacion ({len(rows)} frases): frases enteras bien {rl:.1%} (relajado) / {ex:.1%} (exacto) | "
          f"proposiciones: precision {pr:.1%}, cobertura {rc:.1%}   [lema: {'si' if scripts else 'no (escuela antigua)'}]")
    bad = [r for r in rows if not r[3]]
    print(f"\n--- {len(bad)} frases con diferencias ---")
    for sent, g, p, _ in bad[:25]:
        print(sent)
        print("   esperado:", sorted(g))
        print("   obtenido:", sorted(p))
    limit = .60 if "largas" in path else .75       # frases largas (Fase 2): criterio fijado antes de medir
    print(f"\nCriterio (>= {limit:.0%} relajado): {'CUMPLE' if rl >= limit else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
