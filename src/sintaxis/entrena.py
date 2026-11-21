"""Entrena el analizador con frases analizadas a mano. python -m src.sintaxis.entrena [--epocas N] [--minutos M] [--sigue]
Mide ANTES de entrenar (red sin entrenar y una línea base ingenua) y después de cada pasada, en total y por longitud de frase."""
from __future__ import annotations

import argparse, json, os, random, time
from collections import Counter

import torch
import torch.nn.functional as F

from .datos import lee_conllu
from .medir import mide, tabla
from .modelo import Analizador, Vocab

AQUI = os.path.dirname(os.path.abspath(__file__))
UD = os.path.join(AQUI, "..", "..", "data", "ud")
RUTA = os.path.join(AQUI, "analizador.pt")
DIARIO = os.path.join(AQUI, "..", "..", "reports", "sintaxis_entrenamiento.json")


def carga(parte):
    fs = []
    for corpus in ("es_ancora", "es_gsd"):
        p = os.path.join(UD, f"{corpus}-ud-{parte}.conllu")
        if os.path.exists(p):
            fs += lee_conllu(p)
    return fs


_SIN_TILDE = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")


def descuidada(f):
    """La misma frase como la teclea alguien con prisa: sin tildes, sin mayúscula inicial, sin «¿» ni punto final. El análisis no cambia;
    solo se quitan palabras-signo (y se recolocan las cabezas)."""
    quita = {i for i, (w, u, h, r) in enumerate(f) if w in ("¿", "¡") or (i == len(f) - 1 and w == "." and random.random() < 0.7)}
    if any(h - 1 in quita for i, (w, u, h, r) in enumerate(f) if i not in quita and h > 0):
        quita = set()
    mapa, k = {0: 0}, 0
    for i in range(len(f)):
        if i not in quita:
            k += 1; mapa[i + 1] = k
    out = []
    for i, (w, u, h, r) in enumerate(f):
        if i in quita:
            continue
        w2 = w.translate(_SIN_TILDE) if random.random() < 0.8 else w
        if not out and random.random() < 0.7:
            w2 = w2.lower()
        out.append((w2, u, mapa[h], r))
    return out or f


def lotes(fs, V, tam=48, orden="largo", baraja=True, ruido=0.0):
    if ruido:
        fs = [descuidada(f) if random.random() < ruido else f for f in fs]
    idx = sorted(range(len(fs)), key=lambda i: len(fs[i]))
    bs = [idx[i:i + tam] for i in range(0, len(idx), tam)]
    if baraja and orden != "curriculo":
        random.shuffle(bs)
    for b in bs:
        n = max(len(fs[i]) for i in b)
        X = torch.zeros(len(b), n, 6, dtype=torch.long)
        U = torch.full((len(b), n), -100, dtype=torch.long); H = U.clone(); R = U.clone()
        for k, i in enumerate(b):
            for j, (f, u, h, r) in enumerate(fs[i]):
                X[k, j] = torch.tensor(V.rasgos(f))
                U[k, j] = V.u2i.get(u, 0); H[k, j] = h; R[k, j] = V.r2i.get(r, 0)
        yield b, X, U, H, R


@torch.no_grad()
def predice(modelo, V, fs, tam=96):
    modelo.eval()
    out = [None] * len(fs)
    for b, X, U, H, R in lotes(fs, V, tam, baraja=False):
        Hs, tags, arcos = modelo(X)
        mask = (X[..., 0] == 0)
        n = X.size(1)
        arcos = arcos.masked_fill(torch.cat([torch.zeros(len(b), 1, dtype=torch.bool), mask], 1).unsqueeze(1), -1e9)
        for d in range(n):
            arcos[:, d, d + 1] = -1e9                    # nadie depende de sí mismo
        cab = arcos.argmax(-1)
        for k in range(len(b)):                          # una sola raíz: la de mayor puntuación
            L = len(fs[b[k]])
            rz = (cab[k, :L] == 0).nonzero().flatten().tolist()
            mejor = int(arcos[k, :L, 0].argmax())
            if len(rz) != 1:
                for d in rz:
                    if d != mejor:
                        arcos[k, d, 0] = -1e9
                        cab[k, d] = arcos[k, d].argmax()
                cab[k, mejor] = 0
        fun = modelo.funciones(Hs, cab).argmax(-1)
        tg = tags.argmax(-1)
        for k, i in enumerate(b):
            L = len(fs[i])
            out[i] = [(V.upos[tg[k, j]], int(cab[k, j]), V.rels[fun[k, j]]) for j in range(L)]
    return out


def ingenua(train, fs):
    """Línea base sin aprender estructura: la categoría más vista de cada palabra, y cada palabra depende de la anterior."""
    mas = {}
    cu = Counter()
    for f in train:
        for w, u, h, r in f:
            mas.setdefault(w.lower(), Counter())[u] += 1; cu[(u, r)] += 1
    rel_de = {}
    for (u, r), n in cu.most_common():
        rel_de.setdefault(u, r)
    out = []
    for f in fs:
        p = []
        for j, (w, u, h, r) in enumerate(f):
            pu = mas[w.lower()].most_common(1)[0][0] if w.lower() in mas else "NOUN"
            p.append((pu, j, rel_de.get(pu, "dep") if j else "root"))
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epocas", type=int, default=12)
    ap.add_argument("--minutos", type=float, default=60.0)
    ap.add_argument("--sigue", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(7); random.seed(7)
    t0 = time.time()
    train, dev = carga("train"), carga("dev")
    cnt = Counter(w.lower() if not w[:1].isdigit() else "0" for f in train for w, _, _, _ in f)
    V = Vocab([w for w, n in cnt.items() if n >= 2], sorted({u for f in train for _, u, _, _ in f}), sorted({r for f in train for _, _, _, r in f}))
    modelo = Analizador(len(V.w), len(V.upos), len(V.rels))
    opt = torch.optim.Adam(modelo.parameters(), lr=2e-3, betas=(0.9, 0.9))
    diario = {"frases_entrenamiento": len(train), "frases_medida": len(dev), "palabras_vocabulario": len(V.w), "pasadas": []}
    ep0 = 0
    if a.sigue and os.path.exists(RUTA):
        ck = torch.load(RUTA)
        modelo.load_state_dict(ck["modelo"]); opt.load_state_dict(ck["opt"]); ep0 = ck["epoca"]
        diario = json.load(open(DIARIO, encoding="utf-8"))
    else:
        m_ing = mide(dev, ingenua(train, dev))
        m0 = mide(dev, predice(modelo, V, dev))
        diario["linea_base_ingenua"] = m_ing; diario["sin_entrenar"] = m0
        print(f"{len(train)} frases para aprender, {len(dev)} para medir (no se usan para aprender), {len(V.w)} palabras\n")
        print("ANTES · línea base ingenua (categoría más vista; cada palabra depende de la anterior)\n" + tabla(m_ing))
        print("\nANTES · la red sin entrenar\n" + tabla(m0), flush=True)
    for ep in range(ep0 + 1, a.epocas + 1):
        modelo.train()
        tot = 0.0; nb = 0
        for b, X, U, H, R in lotes(train, V, orden="curriculo" if ep == 1 else "largo", ruido=0.3):   # la primera pasada, de las frases cortas a las largas
            # palabras poco vistas pasan a «desconocida» a veces, para que aprenda a apoyarse en la forma
            Xw = X.clone()
            azar = torch.rand(Xw[..., 0].shape) < 0.15
            Xw[..., 0] = torch.where(azar & (Xw[..., 0] > 1), torch.ones_like(Xw[..., 0]), Xw[..., 0])
            Hs, tags, arcos = modelo(Xw)
            mask = (X[..., 0] == 0)
            arcos = arcos.masked_fill(torch.cat([torch.zeros(len(b), 1, dtype=torch.bool), mask], 1).unsqueeze(1), -1e9)
            l = F.cross_entropy(tags.reshape(-1, tags.size(-1)), U.reshape(-1), ignore_index=-100) \
                + F.cross_entropy(arcos.reshape(-1, arcos.size(-1)), H.reshape(-1), ignore_index=-100) \
                + F.cross_entropy(modelo.funciones(Hs, H.clamp(min=0)).reshape(-1, len(V.rels)), R.reshape(-1), ignore_index=-100)
            opt.zero_grad(); l.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 5.0)
            opt.step()
            tot += float(l); nb += 1
            if time.time() - t0 > a.minutos * 60:
                break
        m = mide(dev, predice(modelo, V, dev))
        diario["pasadas"].append({"pasada": ep, "perdida": round(tot / max(1, nb), 3), "minutos": round((time.time() - t0) / 60, 1), "medida": m})
        torch.save({"modelo": modelo.state_dict(), "opt": opt.state_dict(), "epoca": ep, "vocab": {"w": list(V.w), "upos": V.upos, "rels": V.rels}}, RUTA)
        os.makedirs(os.path.dirname(DIARIO), exist_ok=True)
        json.dump(diario, open(DIARIO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\nDESPUÉS de la pasada {ep} · pérdida {tot / max(1, nb):.3f} · {(time.time() - t0) / 60:.1f} min\n" + tabla(m), flush=True)
        if time.time() - t0 > a.minutos * 60:
            print("(se acabó el tiempo de esta tanda; se puede seguir con --sigue)")
            break


if __name__ == "__main__":
    main()
