"""Lee un libro (RTF o TXT), saca sus frases y mide que entiende el oido de lenguaje REAL (parche-17).

Uso:  python -m scripts.read_book [archivo]        (por defecto busca regenta.rtf / regenta.txt)
Escribe: data/libro.txt (texto limpio) y reports/libro_muestras.txt (ejemplos para revisar).
No entrena nada: solo mide y descubre que relaciones usa el libro.
"""
import os
import random
import re
import sys
from collections import Counter

import torch

from src.language.book import rtf_to_text, sentences
from src.language.book_vocab import extract_vocab, save_vocab
from src.language.corpus import base_pool, es_pool
from src.language.ear import Ear, predict
from src.language.lexicon import PREPS, norm, tokenize

COP = {"es", "era", "fue", "eran", "son", "seran", "sera", "fueron"}
ARTS = {"el", "la", "los", "las", "un", "una", "unos", "unas"}


def find_file(argv):
    for cand in argv[1:] + ["regenta.rtf", "regenta.txt"]:
        if os.path.exists(cand):
            return cand
    raise SystemExit("No encuentro el libro. Ponlo en la carpeta del proyecto como regenta.rtf o pasa la ruta.")


def mine_relations(sents, top=30, min_count=3):
    c = Counter()
    for s in sents:
        t = tokenize(s)
        for i in range(len(t) - 2):
            if t[i] in COP:
                j = i + 1
                if j < len(t) and t[j] in ARTS:
                    j += 1
                if j + 1 < len(t) and t[j].isalpha() and len(t[j]) >= 4 and t[j + 1] in PREPS and t[j] not in ARTS:
                    c[(t[j], t[j + 1])] += 1
    return [(h, p, n) for (h, p), n in c.most_common(top) if n >= min_count]


def main():
    path = find_file(sys.argv)
    raw = open(path, "rb").read().decode("utf-8", errors="ignore") if not path.endswith(".rtf") else open(path, "rb").read().decode("latin-1")
    text = rtf_to_text(raw) if path.endswith(".rtf") else raw
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    open("data/libro.txt", "w", encoding="utf-8").write(text)
    sents = sentences(text)
    toks_all = tokenize(text)
    print(f"Libro: {path} | {len(text)/1e6:.2f} M caracteres | {len(toks_all)} palabras | {len(sents)} frases/clausulas utiles")
    mid = len(text) // 2
    print("\n--- Fragmento del texto convertido (compruebalo: debe leerse bien, con tildes) ---")
    print(text[mid:mid + 500].replace("\n", " / "))
    print("--- fin del fragmento ---")
    cnt = Counter(toks_all)
    print("Veces: era=%d es=%d fue=%d de=%d hijo=%d hija=%d marido=%d mujer=%d amigo=%d" % tuple(
        cnt[w] for w in ("era", "es", "fue", "de", "hijo", "hija", "marido", "mujer", "amigo")))
    nouns = Counter()
    for a, b, c in zip(toks_all, toks_all[1:], toks_all[2:]):
        if a in ARTS and len(b) >= 4 and c in ("de", "del") and b.isalpha():
            nouns[b] += 1
    print("Sustantivos mas frecuentes en 'el/la <x> de': " + ", ".join(f"{w} ({n})" for w, n in nouns.most_common(25)))
    rels = mine_relations(sents)
    print("\nRelaciones del tipo 'es/era <nombre> de ...' mas frecuentes en el libro:")
    print("  " + ", ".join(f"{h} {p} ({n})" for h, p, n in rels[:25]))
    vocab = extract_vocab(text, sents)
    save_vocab(vocab)
    print(f"\nVocabulario REAL guardado en data/libro_vocab.json: {len(vocab['names'])} nombres propios, {len(vocab['nouns'])} sustantivos, "
          f"{len(vocab['adjs'])} adjetivos, {len(vocab['advs'])} adverbios, {len(vocab['clauses'])} clausulas.")
    print("  Nombres:", ", ".join(vocab["names"][:20]))
    print("  Adjetivos:", ", ".join(vocab["adjs"][:20]))
    if not os.path.exists("checkpoints/ear.pt"):                      # reproduccion desde cero: el oido se entrena DESPUES (parche-62)
        print("\n[i] Todavia no existe checkpoints/ear.pt: se salta la medicion con el oido. Ya estan guardados data/libro.txt y data/libro_vocab.json.\n"
              "    Orden desde cero: read_book -> pretrain_ear -> train_ear. Si quieres la medicion, repite  python -m scripts.read_book  al final.")
        return
    cands = {}
    for p in base_pool() + es_pool():
        cands[p[1]] = p[0]
    for k in "hijo hija padre madre marido mujer hermano hermana amigo amiga primo prima tio tia sobrino sobrina criado criada".split():
        cands[f"{k} de"] = f"{k}_de".upper()
    cands = [(n, t) for t, n in cands.items()]
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    ear = Ear()
    ear.load_state_dict(torch.load("checkpoints/ear.pt", map_location="cpu"))
    ear.to(device)
    rng = random.Random(0)
    sample = rng.sample(sents, min(8000, len(sents)))
    outs = predict(ear, [tokenize(s) for s in sample], cands, device)
    ok = [(s, o) for s, o in zip(sample, outs) if o["confidence"] >= 0.8]
    print(f"\nDe {len(sample)} clausulas reales al azar, el oido acepta {len(ok)} ({len(ok)/len(sample):.1%}) como afirmaciones de relacion.")
    print("(En una novela casi todo es descripcion: lo esperable es que acepte muy pocas, y que las aceptadas sean de verdad relaciones.)")
    lines = ["=== ACEPTADAS (revisa si de verdad son afirmaciones de relacion) ==="]
    for s, o in rng.sample(ok, min(40, len(ok))):
        lines.append(f"{s}\n    -> {'NO ' if o['negated'] else ''}{o['subject']} {o['predicate']} {o['object']}   ({o['confidence']:.0%})")
    lines.append("\n=== RECHAZADAS AL AZAR (deberian ser prosa sin relacion) ===")
    rej = [(s, o) for s, o in zip(sample, outs) if o["confidence"] < 0.8]
    for s, o in rng.sample(rej, min(15, len(rej))):
        lines.append(f"{s}   ({o['confidence']:.0%})")
    open("reports/libro_muestras.txt", "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines[:30]))
    print("\n(Ejemplos completos en reports/libro_muestras.txt: pegame ese archivo o sus primeras lineas)")


if __name__ == "__main__":
    main()
