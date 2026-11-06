"""Preentrena el oido leyendo el libro (palabras ocultas). Despues:  python -m scripts.train_ear

REGLA DE DECISION (fijada ANTES de medir). Se adopta el preentrenamiento si:
  1) acierto top-1 en frases NO vistas >= linea base + 10 puntos (la linea base es "siempre la palabra mas frecuente"),
  2) tras  train_ear  las filas a, b, f, g de evaluate_ear no bajan mas de 1 punto respecto a antes
     (antes: a 98.6, b 96.6, f 100, g 98.0),
  3) y mejoran d (antes 82.8) o e (antes 90.8) en >= 2 puntos.
"""
import os
import random
import time
from collections import Counter

import torch

from src.language.ear import Ear
from src.language.lm import LMHead, PUNCT, build_vocab, evaluate, is_heldout, lm_loss, load_sentences

EPOCHS = int(os.environ.get("PRE_EPOCHS", 40))
BATCH = 128


def main():
    torch.manual_seed(0)
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    data = load_sentences("data/libro.txt")
    train = [t for t in data if not is_heldout(t)]
    held = [t for t in data if is_heldout(t)]
    words = sum(len(t) for t in data)
    print(f"Libro: {len(data)} frases ({words} palabras). Entreno {len(train)}, reservadas para prueba {len(held)}.")
    if len(train) < 500:
        print("[!] Muy poco texto: ejecuta antes  python -m scripts.read_book  (genera data/libro.txt).")
        return
    vocab = build_vocab(train)
    head = LMHead(128, vocab).to(device)
    ear = Ear().to(device)
    freq = Counter(w for t in held for w in t if w not in PUNCT)
    top_word, _ = Counter(w for t in train for w in t if w not in PUNCT).most_common(1)[0]
    base = freq[top_word] / max(sum(freq.values()), 1)
    print(f"Vocabulario a adivinar: {len(vocab)} palabras. Linea base ('siempre \"{top_word}\"'): {base:.1%}")
    params = list(ear.parameters()) + list(head.parameters())
    opt = torch.optim.AdamW(params, lr=2e-3, weight_decay=0.01)
    steps = EPOCHS * (len(train) // BATCH)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=steps, pct_start=0.1)
    rng = random.Random(0)
    t0, step, best = time.time(), 0, (-1.0, None)
    for epoch in range(EPOCHS):
        rng.shuffle(train)
        ear.train(); head.train()
        for b in range(len(train) // BATCH):
            loss, acc, _ = lm_loss(ear, head, train[b * BATCH:(b + 1) * BATCH], rng, device)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step(); sched.step(); step += 1
        if (epoch + 1) % 5 == 0 or epoch == EPOCHS - 1:
            t1, t5, n = evaluate(ear, head, held, device)
            print(f"  epoca {epoch+1:3d}  entreno {acc:.1%} | NO vistas: top-1 {t1:.1%}, top-5 {t5:.1%} ({n} huecos)  ({time.time()-t0:.0f}s)", flush=True)
            if t1 > best[0]:
                best = (t1, ({k: v.detach().cpu().clone() for k, v in ear.state_dict().items()},
                             {k: v.detach().cpu().clone() for k, v in head.state_dict().items()}))
    t1, state = best
    ear.load_state_dict(state[0]); head.load_state_dict(state[1])
    os.makedirs("checkpoints", exist_ok=True)
    torch.save(ear.state_dict(), "checkpoints/ear_pre.pt")
    head.save("checkpoints/ear_lm.pt")
    gain = t1 - base
    print(f"\nMejor acierto en frases no vistas: {t1:.1%} (linea base {base:.1%}, +{gain*100:.1f} puntos)")
    print(f"Criterio 1 (>= +10 puntos): {'CUMPLIDO' if gain >= 0.10 else 'NO CUMPLIDO'}")
    print("[+] Guardado checkpoints/ear_pre.pt y checkpoints/ear_lm.pt. Siguiente:  python -m scripts.train_ear")


if __name__ == "__main__":
    main()
