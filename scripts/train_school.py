"""Escuela de espanol v2: entrena el oido con frases reales anotadas (UD) + frases cortas sinteticas, y mide (parche-30/34).

Necesita  data/ud/UD_Spanish-GSD/*.conllu  y  data/ud/UD_Spanish-AnCora/*.conllu.
Antes de reentrenar, mide la escuela anterior con  python -m scripts.eval_frases  (es la linea base).

REGLA DE DECISION (fijada ANTES de medir):
  1) en las frases UD de prueba: categoria >= 94 %, UAS >= 85 %  (no peor que v1 por mas de 1 punto: 94.8 / 86.0),
  2) lema (forma base) >= 90 % en esas frases,
  3) test de conversacion (scripts.eval_frases, relajado) >= 75 % y +10 puntos sobre v1.
"""
import os
import random
import time

import torch

from src.language.ear import Ear
from src.language import ud_synth
from src.language.extract import triples
from src.language.ud import (School, apply_script, build_scripts, find_files, predict_trees, read_conllu, save_school,
                             school_loss)

EPOCHS = int(os.environ.get("SCHOOL_EPOCHS", 10))
SYNTH = int(os.environ.get("SCHOOL_SYNTH", 6000))
BATCH = 64


def load(split):
    sents, skipped, n = [], 0, 0
    for f in find_files(split):
        s, k = read_conllu(f)
        sents += s; skipped += k; n += 1
    return sents, skipped, n


def evaluate(model, sents, device, scripts):
    # Se mide en la CPU con una copia del modelo: en la GPU del Mac (MPS) la medicion se quedaba parada minutos.
    # Cambiar con SCHOOL_EVAL_DEVICE=mps si se quiere medir en la GPU.
    import copy
    dev_eval = os.environ.get("SCHOOL_EVAL_DEVICE", "cpu")
    t_a = time.time()
    m_eval = copy.deepcopy(model).to(dev_eval) if dev_eval != str(device) else model
    trees = predict_trees(m_eval, [[w[0] for w in s] for s in sents], dev_eval, scripts)
    print(f"    (predecir {len(sents)} frases en {dev_eval}: {time.time()-t_a:.1f}s)", flush=True)
    t_b = time.time()
    tot = up = ua = la = lem = 0
    same = with_gold = 0
    for s, t in zip(sents, trees):
        for w, (u, h, r, lm) in zip(s, t):
            tot += 1
            up += u == w[1]
            ua += h == w[2]
            la += (h == w[2]) and (r == w[3])
            from src.language.ud import _clean
            lem += lm == _clean(w[4])
        gold = triples([(w[0], w[1], w[2], w[3], w[4]) for w in s])
        if gold:
            with_gold += 1
            pred = triples([(w[0], u, h, r, lm) for w, (u, h, r, lm) in zip(s, t)])
            same += set(pred) == set(gold)
    print(f"    (comparar con el arbol humano: {time.time()-t_b:.1f}s)", flush=True)
    model.train()
    return up / tot, ua / tot, la / tot, lem / tot, same / max(with_gold, 1), with_gold


def main():
    torch.manual_seed(int(os.environ.get("LCM_SEED", "0")))
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    train, sk, nf = load("train")
    if not train:
        raise SystemExit("No encuentro data/ud/UD_Spanish-*/*-ud-train.conllu. Clona los repositorios dentro de la carpeta del proyecto.")
    dev, _, _ = load("dev")
    test, sk_t, _ = load("test")
    scripts = build_scripts(train)
    synth = ud_synth.make(ud_synth.mine(train), SYNTH, seed=5) if SYNTH else []
    print(f"Entreno: {len(train)} frases reales ({sk} omitidas por > 40 palabras) de {nf} corpus + {len(synth)} frases cortas sinteticas | "
          f"prueba: {len(test)} frases | {len(scripts)} guiones de lema", flush=True)
    print(f"Dispositivo: {device}", flush=True)
    ear = Ear()
    if os.environ.get("SCHOOL_PRE", "1") != "0" and os.path.exists("checkpoints/ear_pre.pt"):
        ear.load_state_dict(torch.load("checkpoints/ear_pre.pt", map_location="cpu"))
        print("[+] Parto del oido que ya leyo el libro (ear_pre.pt).", flush=True)
    model = School(ear, n_scripts=len(scripts)).to(device)
    data = train + synth
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=0.01)
    steps = EPOCHS * (len(data) // BATCH)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=steps, pct_start=0.1)
    rng = random.Random(0)
    nb = len(data) // BATCH
    firma = {"epochs": EPOCHS, "synth": SYNTH, "datos": len(data), "batch": BATCH}
    parcial = "checkpoints/school_partial.pt"
    start = 0
    if os.environ.get("SCHOOL_RESUME", "1") != "0" and os.path.exists(parcial):
        ck = torch.load(parcial, map_location="cpu")
        if ck.get("firma") == firma:
            model.load_state_dict(ck["model"]); opt.load_state_dict(ck["opt"]); sched.load_state_dict(ck["sched"])
            start = ck["epoch"]
            for _ in range(start):
                rng.shuffle(data)  # misma baraja que en una ejecucion sin cortes
            print(f"[+] Retomo desde la epoca {start} de {EPOCHS} (checkpoints/school_partial.pt).", flush=True)
    t0 = time.time()
    print(f"{EPOCHS} epocas x {nb} lotes de {BATCH} frases. Aviso de progreso cada 20 lotes.", flush=True)
    for epoch in range(start, EPOCHS):
        rng.shuffle(data)
        model.train()
        te = time.time()
        for b in range(nb):
            loss, parts = school_loss(model, data[b * BATCH:(b + 1) * BATCH], device, scripts)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step()
            if b == 0 or (b + 1) % 20 == 0 or b == nb - 1:
                done = epoch * nb + b + 1 - start * nb
                per = (time.time() - t0) / max(done, 1)
                left = per * (EPOCHS * nb - start * nb - done)
                print(f"  epoca {epoch+1}/{EPOCHS} lote {b+1}/{nb} | perdida {loss.item():.3f} | {per:.2f} s/lote | "
                      f"quedan ~{left/60:.0f} min", flush=True)
        torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(),
                    "epoch": epoch + 1, "firma": firma}, parcial)
        print(f"  [guardado punto de control: epoca {epoch+1} ({time.time()-te:.0f}s)]", flush=True)
        if dev and ((epoch + 1) % 2 == 0 or epoch == EPOCHS - 1):
            print(f"  midiendo en {len(dev)} frases de dev...", flush=True)
            te = time.time()
            u, a, l, lm, _, _ = evaluate(model, dev, device, scripts)
            print(f"  epoca {epoch+1:2d} | categoria {u:.1%} dependencia {a:.1%} +funcion {l:.1%} lema {lm:.1%} (dev) (medir: {time.time()-te:.0f}s, total {time.time()-t0:.0f}s)", flush=True)
    save_school(model, scripts)
    if os.path.exists(parcial):
        os.remove(parcial)
    print("Midiendo en las frases de prueba...", flush=True)
    u, a, l, lm, same, n = evaluate(model, test, device, scripts)
    print("\n=== ESCUELA v2: frases UD de PRUEBA (nunca vistas) ===")
    print(f"  categoria gramatical: {u:.1%}   [>= 94 %: {'CUMPLE' if u >= .94 else 'NO CUMPLE'}]")
    print(f"  a que palabra se une: {a:.1%}   [>= 85 %: {'CUMPLE' if a >= .85 else 'NO CUMPLE'}]   (+funcion {l:.1%})")
    print(f"  lema (forma base):    {lm:.1%}   [>= 90 %: {'CUMPLE' if lm >= .90 else 'NO CUMPLE'}]")
    print(f"  proposiciones iguales a las del arbol humano: {same:.1%} de {n} frases (informativo; era 35.5 % en v1)")
    print("[+] Guardado checkpoints/school.pt y checkpoints/school_meta.json. Ahora:  python -m scripts.eval_frases")


if __name__ == "__main__":
    main()
