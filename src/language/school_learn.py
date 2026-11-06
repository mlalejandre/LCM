"""La escuela aprende de tus correcciones (parche-49, Fase 2). Sin UD ni LLM.

ENTENDI sujeto relacion objeto  dice cual era la lectura correcta de tu ultima frase. De esa lectura se construye el arbol que la
escuela debio dar (sujeto -> nsubj del verbo, objeto -> obj/obl, verbo -> raiz con su lema) y se hace un ajuste PEQUENO:
  - las correcciones anteriores se repasan junto con la nueva (consolidacion),
  - para no olvidar, se repasan tambien frases de texto normal con SU PROPIA lectura anterior (autodestilacion),
  - si la frase no queda bien, o el canario (test de conversacion) baja mas de una frase, se REVIERTE.
Solo verbos con sujeto y objeto escritos en la frase; relaciones copulativas ("es madre de") aun no."""
from __future__ import annotations

import copy
import json
import os
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import torch

from .lexicon import norm
from .school_parser import SchoolParser
from .ud import edit_script, predict_trees, school_loss

LOG = os.path.join("memory", "correcciones_escuela.jsonl")
LEMAS = os.path.join("memory", "lemas_irregulares.json")


def load_overrides(path: str = LEMAS) -> Dict[str, str]:
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}


def save_overrides(ov: Dict[str, str], path: str = LEMAS) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(ov, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _key(p: str) -> str:
    head, _, prep = norm(p).partition("_")
    return head[:3] + "|" + ("" if prep == "a" else prep)


def target_tree(model, device, scripts, sentence: str, triple: Sequence[str]) -> Tuple[Optional[list], str]:
    forms = SchoolParser._forms(sentence)
    s, p, o = (norm(x) for x in triple)
    low = [norm(f) for f in forms]
    si = [i for i, w in enumerate(low) if w == s]
    oi = [i for i, w in enumerate(low) if w == o]
    if not si or not oi:
        return None, "no encuentro el sujeto y el objeto escritos tal cual en la frase"
    si, oi = si[0], (oi[-1] if oi[-1] != si[0] else oi[0])
    base, _, prep = p.partition("_")
    if base in ("es", "ser"):
        return None, "esa relacion no es un verbo de la frase (las copulativas aun no se aprenden)"
    pred = predict_trees(model, [forms], device, scripts)[0]
    vi = [i for i, w in enumerate(low) if w.startswith(base[:4]) and i not in (si, oi)]
    if not vi:                                  # verbo irregular ("muerde" -> morder): el verbo que la escuela ya ve, el mas cercano al sujeto
        vi = sorted((i for i, t in enumerate(pred) if t[0] == "VERB" and i not in (si, oi)), key=lambda i: abs(i - si))
    if not vi:
        return None, f"no encuentro en la frase el verbo de {p}"
    vi = vi[0]
    words = [[forms[j], *pred[j]] for j in range(len(forms))]       # [forma, upos, head, rel, lema]
    words[vi][1:4] = ["VERB", 0, "root"]
    words[vi][4] = base
    words[si][2:4] = [vi + 1, "nsubj"]
    if words[si][1] not in ("NOUN", "PROPN"):
        words[si][1] = "PROPN" if forms[si][:1].isupper() else "NOUN"
    words[oi][2:4] = [vi + 1, "obl" if prep else "obj"]
    if words[oi][1] not in ("NOUN", "PROPN"):
        words[oi][1] = "NOUN"
    if prep:
        for j in range(oi - 1, -1, -1):
            if low[j] == prep:
                words[j][1:4] = ["ADP", oi + 1, "case"]
                break
    for j, w in enumerate(words):
        if j not in (vi, si, oi) and w[2] == 0:
            w[2], w[3] = vi + 1, ("punct" if w[1] == "PUNCT" else "dep")
    return [tuple(w) for w in words], ""


def read_log(path: str = LOG) -> List[dict]:
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def append_log(sentence: str, triple: Sequence[str], path: str = LOG) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as h:
        h.write(json.dumps({"frase": sentence, "triple": [norm(x) for x in triple]}, ensure_ascii=False) + "\n")


def replay_sentences(path: str = "data/libro.txt", n: int = 300, seed: int = 0) -> List[str]:
    if not os.path.exists(path):
        return []
    from .book import sentences
    pool = [s for s in sentences(open(path, encoding="utf-8").read(), max_words=25) if "?" not in s and 5 <= len(s.split())]
    random.Random(seed).shuffle(pool)
    return pool[:n]


NAMES = ["Pedro", "Ana", "Luis", "Marta", "Sara", "Diego", "Elena", "Hugo", "Irene", "Raúl", "Nuria", "Tomás", "Laura", "Mario"]
VERBS = [("compra", "pan"), ("lee", "libros"), ("escribe", "cartas"), ("pinta", "cuadros"), ("vende", "coches"), ("abre", "la puerta"),
         ("toca", "la guitarra"), ("canta", "canciones"), ("bebe", "agua"), ("tiene", "un perro"), ("estudia", "historia")]
PLACES = ["Madrid", "Sevilla", "Bilbao", "Toledo", "Granada", "Valencia"]


def synthetic_replay(n: int = 200, seed: int = 0) -> List[str]:
    """Frases cortas de conversacion (con coordinaciones) para REPASAR con la lectura anterior de la escuela; no son frases de los tests."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        a, b = rng.sample(NAMES, 2)
        (v, o), (v2, o2) = rng.sample(VERBS, 2)
        city = rng.choice(PLACES)
        out.append(rng.choice([f"{a} {v} {o}.", f"{a} vive en {city}.", f"{a} y {b} {v[:-1]}an {o}.", f"{a} {v} {o} y {o2}.",
                               f"{a} {v} {o} y {v2} {o2}.", f"{a} vive en {city} y trabaja en {rng.choice(PLACES)}.",
                               f"{a} no {v} {o}.", f"{a} {v} {o} en {city}."]))
    return out


def learn_correction(model, device, scripts, sentence: str, triple: Sequence[str], extra: Sequence[dict] = (),
                     replay: Sequence[str] = (), steps: int = 30, lr: float = 3e-5, repeat: int = 4,
                     canary: Optional[Callable[[], float]] = None, tol: float = 0.0125,
                     overrides: Optional[Dict[str, str]] = None) -> Dict:
    target, reason = target_tree(model, device, scripts, sentence, triple)
    if target is None:
        return {"done": False, "reason": reason}
    before = canary() if canary else None
    state = copy.deepcopy(model.state_dict())
    old = [t for t in (target_tree(model, device, scripts, e["frase"], e["triple"])[0] for e in extra) if t]
    pool = [SchoolParser._forms(s) for s in replay]
    pseudo = []
    if pool:
        for forms, tr in zip(pool, predict_trees(model, pool, device, scripts)):
            pseudo.append([(f, *t) for f, t in zip(forms, tr)])
    rng = random.Random(0)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.0)
    model.train()
    for _ in range(steps):
        batch = [target] * repeat + old[-12:] + (rng.sample(pseudo, min(24, len(pseudo))) if pseudo else [])
        loss, _ = school_loss(model, batch, device, scripts)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    model.eval()
    s, p, o = (norm(x) for x in triple)
    parser = SchoolParser(model, device, scripts, overrides)
    check = lambda: any(t["s"] == s and t["o"] == o and _key(t["p"]) == _key(p) for t in (parser.parse(sentence) or []))
    fixed, note = check(), ""
    if not fixed and overrides is not None:
        # lema irregular ("muerde" -> morder): no cabe en los guiones de lema; se guarda como entrada del lexico (forma -> lema)
        verb = next((w[0] for w in target if w[3] == "root"), None)
        if verb and norm(p.partition("_")[0]) != norm(verb):
            overrides[verb.lower()] = p.partition("_")[0]
            fixed, note = check(), "lema irregular guardado: " + verb.lower() + " -> " + p.partition("_")[0]
            if not fixed:
                overrides.pop(verb.lower(), None)
    after = canary() if canary else None
    if not fixed or (before is not None and after < before - tol):
        model.load_state_dict(state)
        return {"done": False, "fixed": fixed, "canary": (before, after),
                "reason": "la frase no quedo bien" if not fixed else "empeoraba lo que ya sabia (canario)"}
    return {"done": True, "fixed": True, "canary": (before, after), "nota": note}
