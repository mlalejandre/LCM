"""Los sentidos de una palabra en la base de conceptos, con sus nombres en inglés y sus padres. Uso: python -m lab.lexico.mira palabra…"""
import gzip, json, sys
from src.nucleo20.morfo import sa
C = json.load(gzip.open("data/conceptos.json.gz", "rt"))
es = {int(k): v for k, v in C["lem"]["es"].items()}
en = {int(k): v for k, v in C["lem"]["en"].items()}
hyp = {int(k): v for k, v in C["hyp"].items()}
w2s = {}
for s, ws in es.items():
    for w in ws:
        w2s.setdefault(sa(w.lower()), []).append(s)
if __name__ == "__main__":
    for w in sys.argv[1:]:
        print("==", w)
        for s in w2s.get(sa(w), []):
            print("  ", s, C["ids"][s][-1], es[s][:5], "| en:", en.get(s, [])[:4], "| padre:", [(en.get(p, [])[:2], es.get(p, [])[:3]) for p in hyp.get(s, [])][:2], "|", (C["gloss"][s] if isinstance(C["gloss"], list) else C["gloss"].get(str(s), ""))[:60])
