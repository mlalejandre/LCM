"""Construye data/definiciones.json.gz: el GRAFO DE DEFINICIONES del diccionario de conceptos.
Cada glosa de WordNet ("a domesticated carnivorous mammal that ...") se lee y sus palabras se enlazan a otros conceptos del diccionario (desambiguadas con el uso y el dominio del concepto que se define).
Ademas se guardan las demas relaciones de WordNet que conceptos.json.gz no trae: similar (adjetivos), atributo (cualidad), derivado, implica, causa, tema, usos ("sirve para...") y acciones ("el que hace...").
Uso: python -m scripts.construir_definiciones <carpeta wordnet>   (necesita data/conceptos.json.gz). Fuentes y licencias: data/CONCEPTOS_LICENCIAS.txt"""
import gzip
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PTR = {"&": "sim", "=": "attr", "+": "deriv", "*": "entrana", ">": "causa", ";c": "tema", "^": "ver", "\\": "pert", "<": "participio", "$": "grupo"}
STOP = set("""a an the of or and in on at to for with by from as is are be been being was were that which who whom whose this these those it its their his her not no than then there into onto over under about against between through during before after above below up down out off very can may will would should could have has had having do does did done also often usually especially mainly chiefly sometimes one two three some any each such other another more most less least many much both either neither same own so too only just s t
used use using esp etc usu e g i ie eg like make made makes making take taken takes taking give given gives having being become becomes became one's someone something somebody person people thing things kind type sort form way part member members group""".split())
FUNC = set("""cut write cook carry hold eat drink play measure clean wash open close dig drive travel fly listen see look build store protect cover tell show pay buy sell heat cool light sweep mix paint draw sew wear
sail ride sleep sit rest dress hit strike catch throw kick wipe dry fasten tie lock tighten tighten pour spread carve chop slice grind grate stir whip bake boil fry roast brew fish hunt farm plant grow harvest
teach heal treat cure defend judge sing dance act speak read learn study clip comb brush shave mop scrub polish sharpen sand saw drill hammer nail screw cross connect transport lift lower move spin turn print copy record
photograph film watch weigh count calculate compute navigate steer brake pull push shoot fire guard rescue repair fix mend bake knit weave stitch bind wrap pack carry sleep wake sound ring call send receive""".split())


def leer(wn):
    syn = {}
    for pos in ("noun", "verb", "adj", "adv"):
        for ln in open(os.path.join(wn, "data." + pos), encoding="latin-1"):
            if ln.startswith("  "):
                continue
            head, _, gloss = ln.partition("|")
            p = head.split(" ")
            sid = f"{p[0]}-{p[2].replace('s', 'a')}"
            nw = int(p[3], 16)
            i = 4 + 2 * nw
            ptrs = []
            for k in range(int(p[i])):
                sym, o2, pos2, _st = p[i + 1 + 4 * k:i + 5 + 4 * k]
                ptrs.append((sym, f"{o2}-{pos2.replace('s', 'a')}"))
            g = gloss.strip()
            g = re.split(r'\s*;\s*"', g)[0]
            syn[sid] = {"ptr": ptrs, "gloss": g}
    return syn


def excepciones(wn):
    ex = {}
    for pos in ("noun", "verb", "adj", "adv"):
        for ln in open(os.path.join(wn, pos + ".exc"), encoding="utf-8"):
            f = ln.split()
            if len(f) >= 2:
                ex.setdefault(f[0], f[1])
    return ex


def lemas(w, ex, tiene):
    out = [w]
    if w in ex:
        out.append(ex[w])
    for suf, rep in (("ies", "y"), ("es", ""), ("s", ""), ("ing", ""), ("ing", "e"), ("ed", ""), ("ed", "e"), ("ied", "y"), ("er", ""), ("est", ""), ("ly", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            b = w[:-len(suf)] + rep
            out.append(b)
            if len(b) > 3 and b[-1] == b[-2] and suf in ("ing", "ed", "er", "est"):
                out.append(b[:-1])
    return [x for x in dict.fromkeys(out) if tiene(x)]


def main(wn):
    with gzip.open(os.path.join(ROOT, "data", "conceptos.json.gz"), "rt", encoding="utf-8") as fh:
        d = json.load(fh)
    ids = d["ids"]
    num = {s: i for i, s in enumerate(ids)}
    syn = leer(wn)
    ex = excepciones(wn)
    en = {int(k): v for k, v in d["lem"]["en"].items()}
    es = {int(k) for k in d["lem"]["es"]}
    fen = {int(k): v for k, v in d["fen"].items()}
    idx = {}
    for c, ws in en.items():
        for w in ws:
            idx.setdefault(w.lower(), []).append(c)
    hyp = {int(k): v for k, v in d["hyp"].items()}
    lex = d["lex"]
    pos = [s[-1] for s in ids]

    def sentidos(w, host):
        best, bs = None, 0.0
        for c in idx.get(w, []):
            if c == host:
                continue
            f = fen.get(c, {}).get(w, 0)
            s = (f + 1.0) * (3.0 if lex[c] == lex[host] else 1.0) * (1.5 if c in es else 1.0)
            if s > bs:
                best, bs = c, s
        return best

    out = {k: {} for k in ("sim", "attr", "deriv", "entrana", "causa", "tema", "ver", "pert", "participio", "grupo", "gl", "uso", "hace")}
    for s in ids:
        c = num[s]
        for sym, t in syn[s]["ptr"]:
            k = PTR.get(sym)
            if k and t in num:
                out[k].setdefault(str(c), []).append(num[t])
    tiene = lambda x: x in idx

    def verbo(w0, c):
        for lw in lemas(w0, ex, tiene):
            v = mejor(lw, "v")
            if v is not None and lw in FUNC:
                return v
        for lw in lemas(w0, ex, tiene):
            v = mejor(lw, "v")
            if v is not None and v in out["deriv"].get(str(c), []):
                return v
        return None

    def mejor(lw, ps):
        """Sentido mas usado del lema para esa categoria; None si ese sentido no tiene nombre en espanol (mejor callar que elegir un sentido raro)."""
        cand = [x for x in idx.get(lw, []) if pos[x] == ps]
        if not cand:
            return None
        b = max(cand, key=lambda x: (fen.get(x, {}).get(lw, 0), 0))
        return b if b in es else None
    for s in ids:
        c = num[s]
        g = syn[s]["gloss"].lower()
        g = re.sub(r"\([^)]*\)", " ", g)
        toks = re.findall(r"[a-z]+(?:-[a-z]+)?", g)
        host = {w.lower() for w in en.get(c, [])}
        h1 = set()
        for t in hyp.get(c, []):
            h1 |= {w.lower() for w in en.get(t, [])}
        enl = []
        for w in toks:
            if w in STOP or w in host or len(w) < 3:
                continue
            for lw in lemas(w, ex, tiene):
                x = sentidos(lw, c)
                if x is not None:
                    if x not in enl and x not in hyp.get(c, []):
                        enl.append(x)
                    break
        if enl:
            out["gl"][str(c)] = enl[:12]
        m = re.search(r"\bused (?:for|to|in|as|by|when)\s+((?:\w+(?:-\w+)?\s*){1,4})", g)
        if m:
            fr = m.group(1).split()
            w0 = fr[0]
            for k_ in (1, 2):
                if w0 in ("the", "a", "an") and len(fr) > 1:
                    fr = fr[1:]
                    w0 = fr[0]
            vb = verbo(w0, c)
            obj = None
            for w in fr[1:]:
                if w in STOP:
                    continue
                for lw in lemas(w, ex, tiene):
                    obj = mejor(lw, "n")
                    if obj is not None:
                        break
                if obj is not None:
                    break
            if vb is not None:
                out["uso"][str(c)] = [vb, obj]
            elif w0 not in STOP:
                for lw in lemas(fr[-1], ex, tiene):
                    o_ = mejor(lw, "n")
                    if o_ is not None:
                        out["uso"][str(c)] = [None, o_]
                        break
        m = re.search(r"\b(?:who|that|which)\s+(?!is\b|are\b|was\b|were\b|has\b|have\b|can\b|may\b|will\b|does\b|do\b|would\b|could\b|must\b|should\b|had\b|did\b|not\b|used\b)(\w+)((?:\s+\w+){0,3})", g)
        if m and pos[c] == "n" and lex[c] in (18, 3, 24, 5) or (m and d["lexnames"].get(str(lex[c]), "") == "noun.person"):
            v0 = m.group(1)
            vb = verbo(v0, c)
            if vb is not None:
                obj = None
                for w in m.group(2).split():
                    if w in STOP:
                        if obj is not None:
                            break
                        continue
                    for lw in lemas(w, ex, tiene):
                        obj = mejor(lw, "n")
                        if obj is not None:
                            break
                out["hace"][str(c)] = [vb, obj]
    out["v"] = 1
    dst = os.path.join(ROOT, "data", "definiciones.json.gz")
    with gzip.open(dst, "wt", encoding="utf-8", compresslevel=9) as fh:
        json.dump(out, fh, separators=(",", ":"))
    print("definiciones ->", dst, os.path.getsize(dst) // 1024, "KB;", {k: len(v) for k, v in out.items() if isinstance(v, dict)})


if __name__ == "__main__":
    main(sys.argv[1])
