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


def _rama_ids(f, i):
    """Los índices (0..n-1) que cuelgan de la palabra i (ella incluida)."""
    ids, cambio = {i}, True
    while cambio:
        cambio = False
        for j, (w, u, h, r) in enumerate(f):
            if h - 1 in ids and j not in ids:
                ids.add(j); cambio = True
    return ids


def _reordena(f, orden, nuevos):
    """Frase nueva con las palabras de `f` en `orden` (índices viejos o None para las de `nuevos`), recolocando las cabezas."""
    mapa = {}
    k = 0
    for x in orden:
        k += 1
        if isinstance(x, int):
            mapa[x + 1] = k
    out, cola = [], iter(nuevos)
    for x in orden:
        if isinstance(x, int):
            w, u, h, r = f[x]
            out.append((w, u, mapa.get(h, 0) if h else 0, r))
        else:
            w, u, h_viejo, r = next(cola)
            out.append((w, u, mapa.get(h_viejo, 0) if h_viejo else 0, r))
    return out


def sa_(w):
    return w.lower().translate(_SIN_TILDE)


def pregunta_de(f):
    """De una frase analizada a mano, una PREGUNTA con su análisis correcto (aumento de datos; el corpus casi no trae preguntas).
    Se pregunta por el sujeto («¿Quién compró la casa?») o por el objeto («¿Qué compró Rosa?»). No inventa análisis: mueve las
    piezas del árbol que ya estaba bien analizado."""
    n = len(f)
    raiz = next((j for j, x in enumerate(f) if x[2] == 0), None)
    if raiz is None or f[raiz][1] not in ("VERB",) or sa_(f[raiz][0]) in ("hay", "habia", "hubo") or n > 30 or any(w in ('"', "«", "»", "-", "—", ":", ";", "(") for w, *_ in f):
        return None
    hijos = [j for j, x in enumerate(f) if x[2] == raiz + 1]
    if any(f[j][3] in ("cop", "mark") for j in hijos):
        return None
    suj = next((j for j in hijos if f[j][3] == "nsubj" and f[j][1] in ("NOUN", "PROPN")), None)
    obj = next((j for j in hijos if f[j][3] == "obj" and f[j][1] in ("NOUN", "PROPN") and not any(f[k][3] == "case" and f[k][2] == j + 1 for k in range(n))), None)
    fin = [j for j in range(n) if f[j][1] == "PUNCT" and j >= n - 1]
    cuerpo = [j for j in range(n) if j not in fin and f[j][0] not in ("¿", "?", "¡", "!")]
    if random.random() < 0.5 and suj is not None:
        rama = _rama_ids(f, suj)
        if max(rama) - min(rama) + 1 != len(rama):
            return None
        persona = f[suj][1] in ("PROPN", "PRON")
        wh = ("quién" if persona else "qué")
        orden = ["Q0"] + [j for j in cuerpo if j < min(rama)] + ["Q1"] + [j for j in cuerpo if j > max(rama)] + ["Q2"]
        nuevos = [("¿", "PUNCT", raiz + 1, "punct"), (wh, "PRON", raiz + 1, "nsubj"), ("?", "PUNCT", raiz + 1, "punct")]
    elif obj is not None:
        rama = _rama_ids(f, obj)
        if max(rama) - min(rama) + 1 != len(rama):
            return None
        grupo_v = sorted({raiz} | {j for j in hijos if f[j][3] in ("aux", "expl", "iobj") and f[j][1] in ("AUX", "PRON") and j < raiz})
        resto = [j for j in cuerpo if j not in rama and j not in grupo_v]
        sujeto = sorted(_rama_ids(f, suj)) if suj is not None and suj < raiz else []
        resto = [j for j in resto if j not in sujeto]
        orden = ["Q0", "Q1"] + grupo_v + sujeto + [j for j in resto] + ["Q2"]
        nuevos = [("¿", "PUNCT", raiz + 1, "punct"), ("Qué", "PRON", raiz + 1, "obj"), ("?", "PUNCT", raiz + 1, "punct")]
    else:
        return None
    marcas = iter(nuevos)
    orden2 = [x if isinstance(x, int) else None for x in orden]
    nv = [nuevos[int(x[1])] for x in orden if not isinstance(x, int)]
    out = _reordena(f, orden2, nv)
    if out and out[1][0][:1].islower() and random.random() < 0.8:
        w, u, h, r = out[1]; out[1] = (w[:1].upper() + w[1:], u, h, r)
    for j in range(2, len(out)):                         # la palabra que abría la frase ya no va en mayúscula (salvo nombres)
        w, u, h, r = out[j]
        if w[:1].isupper() and u not in ("PROPN",) and j > 1 and f[0][0] == w:
            out[j] = (w[:1].lower() + w[1:], u, h, r)
    return out


def lotes(fs, V, tam=48, orden="largo", baraja=True, ruido=0.0, preguntas=0.0):
    if preguntas:
        extra = []
        for f in fs:
            if random.random() < preguntas:
                g = pregunta_de(f)
                if g:
                    extra.append(g)
        fs = list(fs) + extra
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
        for b, X, U, H, R in lotes(train, V, orden="curriculo" if ep == 1 else "largo", ruido=0.3, preguntas=float(os.environ.get("LCM_PREGUNTAS_AUMENTO", "0"))):   # 2.33: aumento con preguntas probado y descartado (no mejoró); queda a 0   # la primera pasada, de las frases cortas a las largas
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
