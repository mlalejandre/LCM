"""Banco del lector de textos en varios campos (parche-115).
Mide, con la escuela real, cuantos de los hechos esperados aparecen (cobertura) y cuantos hechos PROHIBIDOS (creencias, condicionales...) se afirman,
y vuelca TODO lo extraido para auditarlo a mano (la precision se audita, no se adivina con una lista).  El codigo no sabe de ningun campo.
Uso: python -m scripts.lector_bench          (necesita la escuela entrenada)  ->  reports/lector_bench.json + resumen por pantalla"""
import json
import os
import re
import sys
import tempfile

STOP = {"DE", "DEL", "EL", "LA", "LOS", "LAS", "UN", "UNA", "A", "EN", "Y"}


def _tok(k):
    return {t[:-1] if len(t) > 4 and t.endswith("S") else t for t in re.split(r"_+", k.upper()) if t and t not in STOP}


def _casa(esp, got):
    a, b = _tok(esp), _tok(got)
    return bool(a and b) and (a <= b or b <= a)


def _casa_p(esp, got):
    return esp == got or esp.split("_")[0] == got.split("_")[0]


def encaja(esp, hs):
    return any(_casa(esp[0], h["s"]) and _casa_p(esp[1], h["p"]) and (esp[2] == "_" and h["o"] == "_" or esp[2] != "_" and _casa(esp[2], h["o"])) for h in hs)


def ejecutar(parser, banco="data/lector_bench/campos.json"):
    from src.language.lector_ud import lector_para
    from src.memory.store import MemoryStore
    campos = json.load(open(banco, encoding="utf-8"))
    res = {"campos": {}, "global": {}}
    tot_e = tot_ok = tot_proh = tot_f = tot_h = 0
    for c in campos:
        mem = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))
        rep = lector_para(mem, parser).leer(c["texto"])
        hs = [h for h in rep["hechos"]]
        ok = [e for e in c["esperados"] if encaja(e, hs)]
        proh = [p for p in c.get("prohibidos", []) if encaja(p, hs)]
        res["campos"][c["campo"]] = {"frases": rep["frases"], "hechos": len(hs), "esperados": len(c["esperados"]), "acertados": len(ok),
                                     "cobertura": round(len(ok) / max(1, len(c["esperados"])), 3), "prohibidos_afirmados": proh,
                                     "faltan": [e for e in c["esperados"] if e not in ok], "sin_entender": [x["frase"] for x in rep["sin_entender"]],
                                     "extraido": [f"{h['s']} {'NO ' if h['neg'] else ''}{h['p']} {h['o']}" for h in hs]}
        tot_e += len(c["esperados"]); tot_ok += len(ok); tot_proh += len(proh); tot_f += rep["frases"]; tot_h += len(hs)
    res["global"] = {"cobertura": round(tot_ok / max(1, tot_e), 3), "prohibidos_afirmados": tot_proh, "hechos_por_frase": round(tot_h / max(1, tot_f), 2)}
    return res


def texto(res):
    L = ["LECTOR (escuela) - banco multi-campo: cobertura de hechos esperados / prohibidos afirmados / hechos por frase"]
    for k, v in res["campos"].items():
        L.append(f"  {k:18s} {v['acertados']}/{v['esperados']} = {v['cobertura']:.0%}   prohibidos={len(v['prohibidos_afirmados'])}   hechos={v['hechos']} en {v['frases']} frases")
        for e in v["faltan"]:
            L.append(f"      falta: {e[0]} {e[1]} {e[2]}")
    g = res["global"]
    L.append(f"  GLOBAL: cobertura {g['cobertura']:.0%}, prohibidos afirmados {g['prohibidos_afirmados']}, {g['hechos_por_frase']} hechos/frase")
    return "\n".join(L)


def main():
    import torch
    from src.language.school_parser import SchoolParser
    from src.language.ud import load_school
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    res = ejecutar(SchoolParser(model, device, scripts))
    os.makedirs("reports", exist_ok=True)
    json.dump(res, open("reports/lector_bench.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(texto(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
