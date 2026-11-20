"""Auditoría de LECTURA: qué pasa con cada frase de un texto al leerlo.
Para cada frase que tiene una pregunta literal (L, V, I) en los bancos de temas:
  - forma de la frase (con sujeto, sin sujeto, «se…», coordinada con «y», adverbio delante, «Su…»)
  - si deja en el núcleo un hecho con el dato, y si ese hecho cuelga del tema correcto
  - si la pregunta literal se acierta y POR DÓNDE: hecho del núcleo, regla de exposición, cita del texto, fábrica o nada
    python -m lab.lectura.audita dev test ...        (por defecto, todos los temas conocidos; nunca el examen grande)
    python -m lab.lectura.audita -v ...               (lista las frases que no se leen bien)"""
import importlib, json, re, shutil, sys
from collections import Counter, defaultdict

sys.path.insert(0, ".")
from lab.banco import motor, veredicto
from src.nucleo20 import exposicion as X
from src.nucleo20.morfo import sa
from src.nucleo20 import morfo as M

CONOCIDOS = "dev test test2 test3 test4 test5 test6 test7 test8 test9 test10".split()
_ADV = r"^(?:En|Cuando|Si|Después|Despues|Antes|Para|Con|Al|Durante|Por|Hoy|Antiguamente|Debajo|Dentro|Desde|Según|A los|A las|De|Allí|Primero|Luego)\b"


def forma(f):
    t = f.strip().rstrip(".")
    sn, _ = X.sujeto(t)
    coord = bool(re.search(r"(?:,| )\s*(?:y|pero)\s+(?:se\s+|no\s+|l[oa]s?\s+)?[a-záéíóúñü]+(?:an|en|a|e|ó|aron|ieron)\b", t)) and len(t.split()) > 6
    if sn:
        return "con sujeto + «y» verbo" if coord else "con sujeto"
    if re.match(r"^(?:Su|Sus)\b", t):
        return "«Su…»"
    if re.match(r"^Se\b", t):
        return "sin sujeto, «Se…»"
    if re.match(_ADV, t):
        return "adverbio o preposición delante"
    return "sin sujeto, verbo delante"


def ruta(r):
    r = r or ""
    if re.search(r"En el texto pone|el texto dice|Lo dice el texto|Me dijiste", r):
        return "cita"
    if re.search(r"he aprendido|aprendí|Lo junto", r):
        return "exposición"
    if re.search(r"Lo sé porque|de fábrica|suele", r):
        return "fábrica"
    if re.match(r"^\W*(?:No lo sé|No sé|No me has|No he entendido|No conozco|No lo tengo|Eso queda fuera)", r):
        return "nada"
    return "núcleo"


def _claves(crit):
    return [sa(k.strip("^*").lower()) for g in crit.split(";") for k in g.split("|") if k.strip() and not k.strip().startswith("!") and k.strip("^") not in ("si", "no", "ABST")]


def _raiz(w):
    w = sa(w.lower())
    w = sa(M.singular(w)) if len(w) > 3 else w
    return w[:5]


def audita(conjuntos, verboso=False):
    filas = []
    for conj in conjuntos:
        for tema in importlib.import_module("lab.aprender." + conj).TEMAS:
            mo = motor()
            mo.chat(tema["intro"] + "\n" + "\n".join(f for f, _ in tema["frases"]))
            c = mo._n20
            hechos = []
            for h in c.F:
                try:
                    hechos.append((sa(c.frase(h).lower()), sa(c.disp(h["s"]).lower()) if h.get("s") else ""))
                except Exception:                        # noqa
                    pass
            tema_ant = None
            for f, sondas in tema["frases"]:
                sn, _ = X.sujeto(f.rstrip("."))
                fm = forma(f)
                esperado = sn or tema_ant
                for t, q, crit in sondas:
                    if t not in ("L", "V", "I") or crit in ("ANY",):
                        continue
                    ks = [k for k in _claves(crit) if len(k) > 2]
                    con_dato = [h for h in hechos if any(k[:5] in h[0] for k in ks)]
                    estado = "sin hecho"
                    if con_dato:
                        estado = "hecho"
                        if not sn and esperado and t == "L":
                            cab = [_raiz(w) for w in esperado.split() if sa(w.lower()) not in ("el", "la", "los", "las", "un", "una", "de", "del")]
                            if cab and not any(any(r in h[1] or r in h[0].split(" se ")[0] for r in cab[:2]) for h in con_dato):
                                estado = "hecho en otro tema"
                    r = mo.chat(q).get("respuesta")
                    v = veredicto(crit, r)
                    filas.append({"conj": conj, "tema": tema["nombre"], "frase": f, "forma": fm, "t": t, "q": q, "r": r, "ok": v == "OK", "ruta": ruta(r), "hecho": estado})
                if sn:
                    tema_ant = sn
            shutil.rmtree(mo._tmp, ignore_errors=True)
    return filas


def resumen(filas):
    out = {}
    for clave in ["TOTAL"] + sorted({f["forma"] for f in filas}):
        fs = [f for f in filas if clave == "TOTAL" or f["forma"] == clave]
        n = len(fs)
        out[clave] = {"n": n, "ok": round(100 * sum(f["ok"] for f in fs) / n, 1),
                      "hecho": round(100 * sum(f["hecho"] == "hecho" for f in fs) / n, 1),
                      "otro_tema": sum(f["hecho"] == "hecho en otro tema" for f in fs),
                      "sin_hecho": round(100 * sum(f["hecho"] == "sin hecho" for f in fs) / n, 1),
                      "rutas": dict(Counter(f["ruta"] for f in fs if f["ok"]))}
    return out


def imprime(res, titulo):
    print("==", titulo)
    print(f"   {'forma de la frase':34} {'n':>4} {'acierta':>8} {'hecho':>7} {'otro tema':>10} {'sin hecho':>10}   por dónde acierta")
    for k, v in res.items():
        print(f"   {k:34} {v['n']:4d} {v['ok']:7.1f}% {v['hecho']:6.1f}% {v['otro_tema']:10d} {v['sin_hecho']:9.1f}%   {v['rutas']}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    conj = args or CONOCIDOS
    filas = audita(conj, "-v" in sys.argv)
    res = resumen(filas)
    imprime(res, "LECTURA " + " ".join(conj))
    json.dump({"resumen": res, "filas": filas}, open("lab/lectura/ultima.json", "w"), indent=1, ensure_ascii=False)
    if "-v" in sys.argv:
        for f in filas:
            if not f["ok"] or f["hecho"] != "hecho":
                print(f"  [{f['forma'][:14]}] {'OK ' if f['ok'] else 'MAL'} {f['hecho'][:10]:10} {f['ruta'][:6]:6} | {f['frase'][:70]} | {f['q'][:45]} | {(f['r'] or '')[:60]}")
