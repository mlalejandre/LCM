"""Vocabulario REAL sacado de un libro: nombres, sustantivos, adjetivos, adverbios y clausulas de relleno (parche-18)."""
import json
import re
import zlib
from collections import Counter

from .lexicon import norm, tokenize

ARTS = {"el", "la", "los", "las", "un", "una", "unos", "unas"}
RELATION_WORDS = set("hijo hija padre madre marido mujer hermano hermana amigo amiga primo prima tio tia sobrino sobrina "
                     "abuelo abuela criado criada dueno duena".split())
NOT_NOUN = set("mismo misma otro otra todo toda cual cuales poco mucho tanto tanta mas menos algo nada esto eso aquel aquella "
               "estos esos ese esa este esta cada solo sola ambos tales tal".split())
ADJ_END = ("o", "a", "e", "al", "ar", "oso", "osa", "ico", "ica", "ble", "nte", "or", "ivo", "iva", "ido", "ida")


def _split(word):
    return zlib.crc32(word.encode()) % 5 == 0          # ~20 % reservado para medir (nunca entra en entrenamiento)


def extract_vocab(text, clauses, max_names=500, max_nouns=1500, max_adjs=600, max_advs=150, max_clauses=20000):
    words = [(m.group(0), m.start()) for m in re.finditer(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", text)]
    lower = Counter(norm(w) for w, _ in words if w[0].islower())
    caps = Counter()
    for w, pos in words:
        if len(w) >= 3 and w[0].isupper() and w[1:].islower():
            before = text[max(0, pos - 3):pos].rstrip(" \t")
            if before and before[-1] not in ".!?¿¡\"—–\n:":
                caps[norm(w)] += 1
    names = [w for w, n in caps.most_common() if n >= 3 and lower[w] <= n * 0.05 and w.isalpha()][:max_names]
    toks = [norm(w) for w, _ in words]
    freq = Counter(toks)
    top_words = {w for w, _ in freq.most_common(150)}           # palabras muy frecuentes: funcion o verbos, no vocabulario
    after_art = Counter(b for a, b in zip(toks, toks[1:]) if a in ARTS and len(b) >= 4 and b not in NOT_NOUN and b not in top_words)
    nameset = set(names)
    nouns = [w for w, n in after_art.most_common() if n >= 5 and w not in nameset and not w.endswith("mente")
             and not w.endswith(("ando", "iendo", "ar", "er", "ir"))][:max_nouns]
    nounset = set(nouns)
    after_noun = Counter(b for a, b in zip(toks, toks[1:]) if a in nounset and len(b) >= 5 and b not in NOT_NOUN
                         and b not in nameset and b.endswith(ADJ_END) and b not in ARTS and b not in top_words
                         and not b.endswith(("aba", "ia", "ian", "aban", "ando", "iendo", "ron", "mente")))
    adjs = [w for w, n in after_noun.most_common() if n >= 3][:max_adjs]
    cnt = Counter(toks)
    advs = [w for w, n in cnt.most_common() if w.endswith("mente") and len(w) >= 7 and n >= 5][:max_advs]
    keep = []
    for c in clauses:
        t = tokenize(c)
        if 4 <= len(t) <= 28 and "?" not in t:          # tambien las que mencionan padre, marido...: son negativos utiles
            keep.append(" ".join(t))
    return {
        "names": names, "advs": advs, "clauses": keep[:max_clauses],
        "nouns": [["la" if n.endswith(("a", "ion", "dad", "tud")) else "el", n] for n in nouns],
        "adjs": adjs,
    }


def save_vocab(vocab, path="data/libro_vocab.json"):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(vocab, handle, ensure_ascii=False)


def load_vocab(path="data/libro_vocab.json"):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def split_vocab(vocab):
    """Devuelve (entrenamiento, prueba) con una particion fija por palabra."""
    def part(items, keyfn):
        tr = [x for x in items if not _split(keyfn(x))]
        te = [x for x in items if _split(keyfn(x))]
        return tr, te
    out = {}
    for k, key in (("names", lambda x: x), ("advs", lambda x: x), ("adjs", lambda x: x),
                   ("clauses", lambda x: x), ("nouns", lambda x: x[1])):
        out[k] = part(vocab.get(k, []), key)
    return {k: v[0] for k, v in out.items()}, {k: v[1] for k, v in out.items()}
