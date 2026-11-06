"""Conocimiento de fabrica (parche-59, bloque C): frases en espanol (data/semilla.txt) que se cargan por el camino normal del lenguaje.
No hay hechos escritos a mano: todo pasa por la escuela, igual que si lo dijera la persona. Los hechos quedan con importancia alta
y fuente "semilla" para que "¿Como lo sabes?" diga que es conocimiento de fabrica."""
import copy
import os
import tempfile
from typing import Optional

SEED_KEY = "__semilla__"
_CACHE = {}
KEYS = ("facts", "alias", "opposites", "verb_isa", "defs", "surface", "display")


def sentences(path: str = "data/semilla.txt"):
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            yield line


def build(parser, path: str = "data/semilla.txt"):
    """Procesa las frases con un dialogo y una memoria de usar y tirar. Devuelve (snapshot, frases_sin_entender)."""
    from src.language.dialogue import Dialogue, n
    from src.memory.store import MemoryStore
    with tempfile.TemporaryDirectory() as d:
        mem = MemoryStore(os.path.join(d, "seed.json"))
        dlg = Dialogue(mem)
        miss = []
        for sent in sentences(path):
            r = dlg._definitions(sent, n(sent), None)
            cont = sent
            if r:
                cont = r[1]
                if not cont:
                    continue
            found = parser.parse(cont) or []
            if not found:
                miss.append(sent)
                continue
            for t in found:
                tr = (t["s"], t["p"], t["o"])
                mem.add_fact(tr, source="semilla", neg=t["neg"], quant=t.get("q", ""))
                mem.note_surface(tr, t.get("template"), t.get("s_disp"), t.get("o_disp"))
        for f in mem.facts:
            f["imp"] = 5.0
        mem.display = {k: v[:1].lower() + v[1:] for k, v in mem.display.items()}          # sin nombres propios: "Verde" -> "verde"
        snap = {k: copy.deepcopy(getattr(mem, k)) for k in KEYS}
    return snap, miss


def load_seed(mem, parser, path: str = "data/semilla.txt") -> int:
    """Mezcla la semilla en la memoria (una sola vez). Devuelve cuantos hechos anade."""
    if SEED_KEY in mem.defs:
        return 0
    key = id(parser)
    if key not in _CACHE:
        _CACHE[key] = build(parser, path)[0]
    snap = _CACHE[key]
    have = {(f["s"], f["p"], f["o"], bool(f.get("neg"))) for f in mem.facts}
    added = 0
    for f in snap["facts"]:
        if (f["s"], f["p"], f["o"], bool(f.get("neg"))) not in have:
            mem.facts.append(copy.deepcopy(f))
            added += 1
    for a, b in snap["alias"].items():
        mem.alias.setdefault(a, b)
    for pair in snap["opposites"]:
        if pair not in mem.opposites:
            mem.opposites.append(list(pair))
    for k, v in snap["verb_isa"].items():
        mem.verb_isa.setdefault(k, v)
    for k, v in snap["defs"].items():
        mem.defs.setdefault(k, v)
    for k, v in snap["surface"].items():
        mem.surface.setdefault(k, v)
    for k, v in snap["display"].items():
        mem.display.setdefault(k, v)
    mem.defs[SEED_KEY] = "1"
    return added
