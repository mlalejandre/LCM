"""parche-98: LEXICO (sinonimos, antonimos, hiperonimos) a partir de data/lexico_es.json (MCR espanol CC BY 3.0 + Princeton WordNet; ver data/LEXICO_LICENCIA.txt).
Si el fichero no esta, todo devuelve vacio y el resto del modelo funciona igual (se puede retirar borrandolo). Es una AYUDA de ultimo recurso: la memoria manda."""
import json
import os
import re
import unicodedata

_F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "lexico_es.json")
_D = None


def nrm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if unicodedata.category(c) != "Mn").strip()


def st(w):
    w = nrm(w)
    return re.sub(r"(os|as|es|o|a|e|s)$", "", w) if len(w) > 3 else w


def _load():
    global _D
    if _D is None:
        _D = {"ok": False, "idx": {}, "syn": [], "pos": [], "hyp": {}, "ant": {}, "known": set()}
        try:
            d = json.load(open(_F, encoding="utf-8"))
        except (OSError, ValueError):
            return _D
        _D["syn"] = {int(k): v for k, v in d["syn"].items()}
        _D["pos"] = {int(k): v for k, v in d["pos"].items()}
        _D["hyp"] = {int(k): v for k, v in d["hyp"].items()}
        _D["ant"] = {int(k): v for k, v in d["ant"].items()}
        idx = {}
        for i, lems in _D["syn"].items():
            for lem in lems:
                k = st(lem) if " " not in lem else nrm(lem)
                idx.setdefault(k, []).append(i)
                _D["known"].add(nrm(lem))
        _D["idx"], _D["ok"] = idx, True
    return _D


def disponible():
    return _load()["ok"]


def conoce(w):
    """True si la palabra (sin tilde) es un lema del lexico: sirve para NO tomarla por errata."""
    return nrm(w) in _load()["known"]


def sentidos(w):
    d = _load()
    return d["idx"].get(st(w), [])


def sinonimos(w, pos=None):
    """Lemas que comparten algun sentido con w (sin w), en orden de aparicion. pos: 'n','v','a','r' o None."""
    d, out = _load(), []
    for i in sentidos(w):
        if pos and d["pos"].get(i) != pos:
            continue
        for lem in d["syn"].get(i, []):
            if st(lem) != st(w) and lem not in out:
                out.append(lem)
    return out


def antonimos(w):
    d, out = _load(), []
    for i in sentidos(w):
        for j in d["ant"].get(i, []):
            for lem in d["syn"].get(j, []):
                if lem not in out:
                    out.append(lem)
    return out


def hiperonimos(w, niveles=1):
    """Lemas de los hiperonimos (categorias mas generales); con niveles>1 sube por la jerarquia."""
    d, out, cur = _load(), [], set(sentidos(w))
    seen = set(cur)
    for _ in range(niveles):
        nxt = set()
        for i in cur:
            for j in d["hyp"].get(i, []):
                if j not in seen:
                    seen.add(j)
                    nxt.add(j)
                    for lem in d["syn"].get(j, [])[:2]:
                        if lem not in out:
                            out.append(lem)
        cur = nxt
    return out


def es_un_tipo_de(a, b, max_niv=6):
    """True si b esta por encima de a en la jerarquia de hiperonimos (un gato es un animal)."""
    d = _load()
    objetivo = set(sentidos(b))
    cur, seen = set(sentidos(a)), set()
    for _ in range(max_niv):
        if cur & objetivo:
            return True
        seen |= cur
        cur = {j for i in cur for j in d["hyp"].get(i, [])} - seen
        if not cur:
            return False
    return bool(cur & objetivo)


# ---- preguntas sobre palabras (ultimo recurso: la memoria manda) -----------------------------------------------------
def _lista(xs, n=6):
    xs = [x for x in xs if " " not in x][:n] or xs[:n]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def _nombre_pos(w):
    """Sentidos de w que son sustantivos (para definir) o, si no hay, cualquiera."""
    d = _load()
    ss = sentidos(w)
    return [i for i in ss if d["pos"].get(i) == "n"] or ss


def responder(raw):
    """Contesta preguntas sobre PALABRAS con el lexico. Devuelve None si no aplica o no sabe."""
    if not disponible():
        return None
    t = re.sub(r"\s+", " ", re.sub(r"[¡!¿?.,;:]", " ", nrm(raw))).strip()
    def orig(w):
        mm = next((x for x in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑüÜ]+", raw) if nrm(x) == w), None)
        return mm or w

    m = re.match(r"(?:cual es |cuales son |dime |dame )?(?:el |los |un |algun )?(?:sinonimos?|palabras? (?:parecidas?|equivalentes?)) (?:de |a |para )(?:la palabra )?(.+)$", t) \
        or re.match(r"(?:dime |dame |que |cual )?(?:otra|otras) palabras? (?:hay |existe |puedo usar |se puede usar )?(?:para|por|de) (?:la palabra )?(.+)$", t) \
        or re.match(r"como se dice (.+) de otra (?:forma|manera)$", t) or re.match(r"que palabra significa (?:lo mismo que|igual que) (.+)$", t)
    if m:
        w = m.group(1).strip().split()[-1] if len(m.group(1).split()) <= 3 else None
        if w:
            r = sinonimos(w)
            if r:
                return f"Según el léxico, otras palabras para «{orig(w)}»: {_lista(r)}."
        return None
    m = re.match(r"(?:cual es |cuales son |dime |dame )?(?:el |los |un |algun )?(?:antonimos?|opuestos?|contrarios?) (?:de |a )(?:la palabra )?(.+)$", t) \
        or re.match(r"(?:cual es )?lo (?:contrario|opuesto) (?:de|a) (.+)$", t) or re.match(r"que palabra significa lo contrario (?:de|que) (.+)$", t)
    if m and len(m.group(1).split()) <= 3:
        w = m.group(1).split()[-1]
        r = antonimos(w)
        if r:
            return f"Según el léxico, lo contrario de «{orig(w)}» es {_lista(r, 3)}."
        return None
    m = re.match(r"es (?:un |una |el |la )?(\w+) (?:un |una |el |la )?(?:tipo de |clase de )?(\w+)$", t)
    if m and not any(x[:1].isupper() for x in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]+", raw)[1:3]) and conoce(m.group(1)) and conoce(m.group(2)) and m.group(1) != m.group(2) and es_un_tipo_de(m.group(1), m.group(2)):
        return f"Según el léxico, sí: «{orig(m.group(1))}» es un tipo de «{orig(m.group(2))}» (según el sentido de la palabra)."
    m = re.match(r"que (?:es|son) (?:un |una |el |la |los |las )?(\w+)$", t)
    if m and conoce(m.group(1)) and not (re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]+", raw) or [""])[-1][:1].isupper():
        w = m.group(1)
        ss = _nombre_pos(w)
        h = []
        for i in ss:
            h = [x for j in _load()["hyp"].get(i, []) for x in _load()["syn"].get(j, [])[:2]]
            if h:
                break
        s_ = [x for x in sinonimos(w, "n") if " " not in x] if ss else []
        if h:
            return f"Según el léxico, «{orig(w)}» es un tipo de {_lista(h, 3)}." + (f" Otras palabras: {_lista(s_, 4)}." if s_ else "")
        if s_:
            return f"Según el léxico, «{orig(w)}» significa lo mismo que {_lista(s_, 4)}."
    return None
