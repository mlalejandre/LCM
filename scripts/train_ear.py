"""Entrena el oido con oraciones generadas (espanol -> proposicion, con negacion y 'es un')."""
import os
import random
import time
import torch
from src.language.corpus import (CLAUSES_TRAIN, HEADS_TRAIN, NAMES_TRAIN, VERBS_TRAIN, PredicatePool, base_pool, es_pool, make,
                                 make_negatives)
from src.language.ear import Ear
from src.language.training import batch_loss
from src.language.lm import LMHead, is_heldout, lm_loss, load_sentences

N = int(os.environ.get("EAR_N", 60000))
EPOCHS = int(os.environ.get("EAR_EPOCHS", 8))
BATCH = 128


def main():
    torch.manual_seed(int(os.environ.get("LCM_SEED", "0")))
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    pool = base_pool() + es_pool() + PredicatePool(HEADS_TRAIN, VERBS_TRAIN).items
    data = make(N, pool, seed=1) + make_negatives(N // 2, seed=2)
    print(f"Vocabulario: {len(NAMES_TRAIN)} nombres, {len(CLAUSES_TRAIN)} clausulas de libro (si es 0: ejecuta scripts.read_book antes).")
    ear = Ear().to(device)
    # Preentrenamiento con texto corriente (parche-26): si existe, se parte de el y se sigue leyendo el libro mientras se afina.
    lm_head, book, lr = None, [], 2e-3
    if os.environ.get("EAR_PRE", "1") != "0" and os.path.exists("checkpoints/ear_pre.pt") and os.path.exists("checkpoints/ear_lm.pt"):
        ear.load_state_dict(torch.load("checkpoints/ear_pre.pt", map_location="cpu"))
        ear.to(device)
        lm_head = LMHead.load("checkpoints/ear_lm.pt", ear.d, device)
        book = [t for t in load_sentences("data/libro.txt") if not is_heldout(t)]
        lr = 1e-3
        print(f"[+] Parto del oido preentrenado ({len(book)} frases del libro se siguen leyendo mientras se afina).")
    else:
        print("[i] Sin preentrenamiento (ejecuta  python -m scripts.pretrain_ear  para leer el libro antes).")
    params = list(ear.parameters()) + (list(lm_head.parameters()) if lm_head is not None else [])
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=0.01)
    steps = EPOCHS * (len(data) // BATCH)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps, pct_start=0.1)
    rng = random.Random(int(os.environ.get("LCM_SEED", "0")))
    texts = sorted({p[1] for p in pool})
    t0 = time.time()
    step = 0
    for epoch in range(EPOCHS):
        rng.shuffle(data)
        ear.train()
        for b in range(len(data) // BATCH):
            loss, parts = batch_loss(ear, data[b * BATCH:(b + 1) * BATCH], texts, rng, device)
            if lm_head is not None:
                l_lm, _, _ = lm_loss(ear, lm_head, rng.sample(book, 48), rng, device)
                loss = loss + 0.3 * l_lm
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step(); sched.step(); step += 1
            if step % 200 == 0:
                print(f"  epoca {epoch+1} paso {step}/{steps} tags {parts[0]:.3f} relacion {parts[1]:.3f} negacion {parts[2]:.3f} ambito {parts[3]:.3f} ({time.time()-t0:.0f}s)", flush=True)
    os.makedirs("checkpoints", exist_ok=True)
    torch.save(ear.state_dict(), "checkpoints/ear.pt")
    print("[+] Oido guardado en checkpoints/ear.pt")


if __name__ == "__main__":
    main()
