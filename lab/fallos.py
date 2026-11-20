import json, sys
fs = json.load(open("lab/ultimo_dev.json"))
vistos = set(); n = 0
cat = sys.argv[1] if len(sys.argv) > 1 else None
for i, f in enumerate(fs):
    if f["v"] in (None, "OK") or (cat and f["cat"] != cat): continue
    clave = (f["cat"], f["crit"][:6], f["v"], " ".join(f["q"].split()[:2]))
    if clave in vistos: continue
    vistos.add(clave); n += 1
    ctx = [x for x in fs[max(0, i - 3):i] if x["id"] == f["id"]]
    print("[%s] %s" % (f["id"], f["v"]))
    for x in ctx[-2:]: print("      . %s -> %s" % (x["q"], str(x["r"])[:90]))
    print("      > %s\n        %s      <-- %s" % (f["q"], str(f["r"])[:170], f["crit"]))
print(n, "tipos de fallo")
