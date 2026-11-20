"""LCM 2.1 · Afinado conversacional de la Escuela.

Parte de la Escuela ya entrenada (checkpoints/school.pt) y la afina con frases conversacionales cortas con árbol conocido
(src/language/ud_conv.py) mezcladas con frases reales de UD para que no olvide lo aprendido. No reentrena desde cero.

    python -m scripts.afinar_escuela              # afina, mide y decide (guarda copia de la Escuela anterior)
    python -m scripts.afinar_escuela --medir      # solo mide la Escuela actual
    python -m scripts.afinar_escuela --restaurar  # vuelve a la Escuela anterior

REGLA DE DECISIÓN (fijada antes de medir). La Escuela afinada se adopta solo si, frente a la anterior:
  1) en frases conversacionales con vocabulario reservado: categoría +3 puntos o más, y lema no peor;
  2) en UD test: categoría no baja más de 0,5 puntos, dependencia no más de 1,0, lema no más de 0,5.
Si no cumple, se restaura la anterior y se informa.

Variables: AFINAR_EPOCAS (3), AFINAR_CONV (24000), AFINAR_UD (12000 frases UD por época), AFINAR_LR (4e-4), LCM_SEED (0).
"""
import json, os, random, shutil, sys, time

import torch

from src.language import ud_conv
from src.language.ud import find_files, load_school, predict_trees, read_conllu, save_school, school_loss, _clean

CK, META, PREV = "checkpoints/school.pt", "checkpoints/school_meta.json", "checkpoints/school_previa.pt"
INFORME = "reports/escuela21.json"


def medir(model, scripts, sents, device="cpu"):
    trees = predict_trees(model, [[w[0] for w in s] for s in sents], device, scripts)
    tot = up = ua = la = lem = perf = 0
    for s, t in zip(sents, trees):
        bien = True
        for w, (u, h, r, lm) in zip(s, t):
            if w[1] == "PUNCT":
                continue
            tot += 1; up += u == w[1]; ua += h == w[2]; la += (h == w[2] and r == w[3]); lem += lm == _clean(w[4])
            bien = bien and u == w[1] and lm == _clean(w[4])
        perf += bien
    return {"categoria": round(100 * up / tot, 2), "dependencia": round(100 * ua / tot, 2), "funcion": round(100 * la / tot, 2), "lema": round(100 * lem / tot, 2),
            "frases_perfectas": round(100 * perf / len(sents), 2), "n": len(sents)}


def carga_ud(split):
    out = []
    for f in find_files(split):
        out += read_conllu(f)[0]
    return out


def mide_todo(model, scripts):
    import copy
    m = copy.deepcopy(model).to("cpu")
    conv = ud_conv.make(3000, "eval", seed=777)
    r = {"conversacional": medir(m, scripts, conv)}
    test = carga_ud("test")
    if test:
        r["ud_test"] = medir(m, scripts, test)
    return r


def cumple(antes, despues):
    c, c0 = despues["conversacional"], antes["conversacional"]
    ok = c["categoria"] >= c0["categoria"] + 3 and c["lema"] >= c0["lema"]
    if "ud_test" in antes:
        u, u0 = despues["ud_test"], antes["ud_test"]
        ok = ok and u["categoria"] >= u0["categoria"] - 0.5 and u["dependencia"] >= u0["dependencia"] - 1.0 and u["lema"] >= u0["lema"] - 0.5
    return ok


def main():
    if "--restaurar" in sys.argv:
        if not os.path.exists(PREV):
            sys.exit("[!] No hay Escuela anterior guardada (checkpoints/school_previa.pt).")
        shutil.copyfile(PREV, CK)
        print("[OK] Restaurada la Escuela anterior.")
        return
    seed = int(os.environ.get("LCM_SEED", "0"))
    torch.manual_seed(seed)
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(CK, META, device="cpu")
    antes = mide_todo(model, scripts)
    print("ANTES  ", json.dumps(antes, ensure_ascii=False))
    if "--medir" in sys.argv:
        return
    EPOCAS = int(os.environ.get("AFINAR_EPOCAS", 3)); NCONV = int(os.environ.get("AFINAR_CONV", 24000)); NUD = int(os.environ.get("AFINAR_UD", 12000))
    LR = float(os.environ.get("AFINAR_LR", 4e-4)); BATCH = 64
    ud = carga_ud("train")
    if not ud:
        print("[aviso] No encuentro data/ud (python -m scripts.get_data). Afino solo con frases conversacionales y menos pasos, para no olvidar.")
        EPOCAS, LR = min(EPOCAS, 1), min(LR, 2e-4)
    conv = ud_conv.make(NCONV, "train", seed=seed + 11)
    rng = random.Random(seed)
    model = model.to(device); model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    pasos = EPOCAS * ((len(conv) + min(NUD, len(ud))) // BATCH)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=LR, total_steps=max(pasos, 1), pct_start=0.1)
    print(f"Afinado: {EPOCAS} épocas, {len(conv)} conversacionales + {min(NUD, len(ud))} UD por época, lr {LR}, dispositivo {device}", flush=True)
    t0 = time.time(); hecho = 0
    for ep in range(EPOCAS):
        datos = conv + (rng.sample(ud, min(NUD, len(ud))) if ud else [])
        rng.shuffle(datos)
        nb = len(datos) // BATCH
        for b in range(nb):
            loss, _ = school_loss(model, datos[b * BATCH:(b + 1) * BATCH], device, scripts)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            if hecho < pasos:
                sched.step()
            hecho += 1
            if b == 0 or (b + 1) % 50 == 0 or b == nb - 1:
                per = (time.time() - t0) / hecho
                print(f"  época {ep + 1}/{EPOCAS} lote {b + 1}/{nb} | pérdida {loss.item():.3f} | {per:.2f} s/lote | quedan ~{per * (pasos - hecho) / 60:.0f} min", flush=True)
    model.eval()
    despues = mide_todo(model, scripts)
    print("DESPUÉS", json.dumps(despues, ensure_ascii=False))
    ok = cumple(antes, despues)
    os.makedirs("reports", exist_ok=True)
    json.dump({"antes": antes, "despues": despues, "adoptada": ok, "epocas": EPOCAS, "conv": len(conv), "ud": min(NUD, len(ud)), "lr": LR, "dispositivo": device,
               "fecha": time.strftime("%Y-%m-%d %H:%M")}, open(INFORME, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if ok:
        if not os.path.exists(PREV):
            shutil.copyfile(CK, PREV)
        save_school(model.to("cpu"), scripts, CK, META)
        print("[OK] CUMPLE la regla: Escuela afinada guardada en checkpoints/school.pt (la anterior queda en checkpoints/school_previa.pt).")
    else:
        print("[NO ADOPTADA] No cumple la regla fijada: se conserva la Escuela anterior. Detalle en", INFORME)


if __name__ == "__main__":
    main()
