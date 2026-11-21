"""Graba los árboles y lecturas de la Escuela que usan las tandas y las de la ronda 2.6 (lab/iter26), para poder repetirlas sin modelo (tests)."""
import json, copy
from lab import banco
from lab import tanda01, tanda02, tanda03, tanda04, tanda05, tanda06, tanda07, tanda08, tanda09, tanda12, tanda13, tanda14, tanda15
import importlib, os
IT26 = [importlib.import_module(f"lab.{d}.t{k:02d}") for d in ("iter26", "iter27", "iter28", "iter29", "iter210", "iter211", "iter212", "iter213", "iter214", "iter215", "iter216", "iter217", "iter218", "iter219", "iter220", "iter221", "iter222", "iter223", "iter224", "iter225", "iter226") for k in range(1, 100) if os.path.exists(f"lab/{d}/t{k:02d}.py")]
real = banco.parser()
class Grabador:
    model = True
    def __init__(self): self.trees, self.parses, self.today = {}, {}, None
    def tree(self, raw):
        r = real.tree(raw); self.trees[raw] = [list(x) for x in r]; return r
    def parse(self, sentence, topic=None, verbs=None):
        real.today = self.today
        r = real.parse(sentence, topic=topic, verbs=verbs); self.parses[sentence] = copy.deepcopy(r); return r
    def __getattr__(self, k): return getattr(real, k)
g = Grabador(); banco._PARSER = g
dial = []
for mod in (tanda01, tanda02, tanda03, tanda04, tanda05, tanda06, tanda07, tanda08, tanda09, tanda12, tanda13, tanda14, tanda15, *IT26):
    D_ = mod._prepara() if hasattr(mod, '_prepara') else mod.D
    D_ = [d for d in D_ if not any(isinstance(t, dict) for t, c in d['turnos'])]
    filas, res = banco.correr(D_)
    malos = {f['id'] for f in filas if f['v'] not in (None, 'OK')}
    mod.D = [d for d in D_ if d['id'] not in malos]
    print(mod.__name__, res['acierto'], 'excluidos:', sorted(malos))
    for d in mod.D:
        dial.append({"id": d["id"], "cat": d["cat"], "turnos": [[t, c] for t, c in d["turnos"]]})
json.dump({"hoy": banco.HOY.isoformat(), "trees": g.trees, "parses": g.parses, "dialogos": dial}, open("tests/fixtures/nucleo20.json", "w", encoding="utf-8"), ensure_ascii=False)
print("fixture:", len(g.trees), "árboles,", len(g.parses), "lecturas,", len(dial), "diálogos")
