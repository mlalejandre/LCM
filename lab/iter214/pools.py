import json, glob, collections, sys
sys.path.insert(0, ".")
from src.nucleo20 import conceptos as K
from src.nucleo20.morfo import sa
fq = {"NOUN": collections.Counter(), "ADJ": collections.Counter(), "VERB": collections.Counter()}
for f in glob.glob("data/ud/*/*.conllu"):
    for l in open(f, encoding="utf-8"):
        p = l.split("\t")
        if len(p) > 4 and p[3] in fq and p[2].isalpha() and p[2].islower():
            fq[p[3]][p[2]] += 1
L = json.load(open("data/lexico_es.json"))
syn, pos, hyp, ant = L["syn"], L["pos"], L["hyp"], L["ant"]
por_pal = collections.defaultdict(list)
for i, ws in syn.items():
    for w in ws:
        por_pal[(w, pos[i])].append(i)
def antonimos(w, p):
    out = []
    for i in por_pal.get((w, p), []):
        for j in ant.get(i, []):
            out += [x for x in syn.get(str(j), []) if " " not in x]
    return list(dict.fromkeys(out))
def hiper(w):
    out = []
    for i in por_pal.get((w, "n"), [])[:2]:
        for j in hyp.get(i, [])[:1]:
            out += syn.get(str(j), [])[:2]
    return out
nouns = [(w, c) for w, c in fq["NOUN"].most_common() if c >= 3 and not K._kb_clase(sa(w)) and (w, "n") in por_pal]
adjs = [(w, c, antonimos(w, "a")) for w, c in fq["ADJ"].most_common() if c >= 5]
adjs = [x for x in adjs if x[2]]
verbs = [(w, c, antonimos(w, "v")) for w, c in fq["VERB"].most_common() if c >= 10]
verbs = [x for x in verbs if x[2]]
json.dump({"nouns": [(w, c, hiper(w)) for w, c in nouns], "adjs": adjs, "verbs": verbs}, open("/tmp/pools.json", "w"), ensure_ascii=False)
print(len(nouns), len(adjs), len(verbs))
print(nouns[:60])
print(adjs[:40])
