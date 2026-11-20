"""LCM 2.3 · formas simples por reglas auditables (no es un modelo entrenado).

Una figura de un color sobre un fondo de otro: se separa la figura del fondo (el color de los bordes),
se mide qué parte de su caja rellena y su proporción, y se decide entre círculo, cuadrado, rectángulo,
óvalo y triángulo. Si no encaja claramente en ninguna, se abstiene."""
from __future__ import annotations

import io
from collections import Counter

from .color_features import clasificar_rgb

UMBRAL_DIF = 60          # distancia RGB mínima para considerar un píxel parte de la figura


def _dist(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


def analizar_forma(datos: bytes) -> dict:
    """{'forma', 'color_figura', 'color_fondo', 'relleno', 'aspecto'} o {'forma': None, ...}."""
    from PIL import Image
    with Image.open(io.BytesIO(datos)) as img:
        img = img.convert("RGB")
        img.thumbnail((96, 96))
        w, h = img.size
        px = img.load()
        borde = [px[x, 0] for x in range(w)] + [px[x, h - 1] for x in range(w)] + [px[0, y] for y in range(h)] + [px[w - 1, y] for y in range(h)]
        fondo, n_f = Counter(borde).most_common(1)[0]
        if n_f < 0.8 * len(borde):
            return {"forma": None, "motivo": "el fondo no es uniforme"}
        fig = [(x, y) for y in range(h) for x in range(w) if _dist(px[x, y], fondo) > UMBRAL_DIF]
        out = {"forma": None, "color_fondo": clasificar_rgb(fondo), "color_figura": None, "relleno": 0.0, "aspecto": 0.0}
        if len(fig) < 0.03 * w * h or len(fig) > 0.9 * w * h:
            out["motivo"] = "no hay una figura separada del fondo"
            return out
        xs = [p[0] for p in fig]; ys = [p[1] for p in fig]
        bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        relleno = len(fig) / (bw * bh)
        aspecto = bw / bh
        cols = Counter(clasificar_rgb(px[x, y]) or "OTRO" for x, y in fig)
        c, n = cols.most_common(1)[0]
        out.update(relleno=round(relleno, 3), aspecto=round(aspecto, 3), color_figura=c if c != "OTRO" and n >= 0.85 * len(fig) else None)
        cuadrada = 0.87 <= aspecto <= 1.15
        puntas = _puntas(set(fig), min(xs), min(ys), bw, bh)
        if 0.26 <= relleno <= 0.42 and 0.8 <= aspecto <= 1.25 and puntas == 5:
            out["forma"] = "ESTRELLA"                        # 2.10: cinco puntas alrededor del centro
            return out
        if relleno >= 0.93:
            out["forma"] = "CUADRADO" if cuadrada else "RECTANGULO"
        elif 0.74 <= relleno <= 0.83:
            out["forma"] = "CIRCULO" if cuadrada else "OVALO"
        elif 0.44 <= relleno <= 0.56:
            out["forma"] = "TRIANGULO"
        else:
            out["motivo"] = "la figura no se parece claramente a ninguna forma que conozca"
        return out


def _puntas(fig, x0, y0, bw, bh, n=120):
    """Cuántas veces entra la figura al recorrer un círculo alrededor de su centro (una estrella de 5 puntas: 5)."""
    import math
    cx, cy = x0 + bw / 2, y0 + bh / 2
    r = 0.78 * min(bw, bh) / 2
    dentro = [(int(round(cx + r * math.cos(2 * math.pi * k / n))), int(round(cy + r * math.sin(2 * math.pi * k / n)))) in fig for k in range(n)]
    return sum(1 for k in range(n) if dentro[k] and not dentro[k - 1])


def _clasifica(fig, px):
    """Forma y color de un conjunto de píxeles (los mismos umbrales que analizar_forma)."""
    xs = [p[0] for p in fig]; ys = [p[1] for p in fig]
    bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    relleno = len(fig) / (bw * bh)
    aspecto = bw / bh
    cols = Counter(clasificar_rgb(px[x, y]) or "OTRO" for x, y in fig)
    c, n = cols.most_common(1)[0]
    forma = None
    cuadrada = 0.87 <= aspecto <= 1.15
    if 0.26 <= relleno <= 0.42 and 0.8 <= aspecto <= 1.25 and _puntas(set(fig), min(xs), min(ys), bw, bh) == 5:
        forma = "ESTRELLA"
    elif relleno >= 0.93:
        forma = "CUADRADO" if cuadrada else "RECTANGULO"
    elif 0.74 <= relleno <= 0.83:
        forma = "CIRCULO" if cuadrada else "OVALO"
    elif 0.44 <= relleno <= 0.56:
        forma = "TRIANGULO"
    return {"forma": forma, "color_figura": c if c != "OTRO" and n >= 0.85 * len(fig) else None,
            "caja": (min(xs), min(ys), max(xs), max(ys)), "centro": (min(xs) + bw / 2, min(ys) + bh / 2)}


def analizar_escena(datos: bytes, maximo=4) -> dict:
    """LCM 2.10 · varias figuras sobre un fondo: cada una con su forma y color, y cómo están colocadas.
    {'figuras': [...], 'relaciones': [(i, rel, j)]} con rel en sobre (encima), bajo (debajo), izquierda, derecha, dentro.
    Si hay menos de dos figuras o más de 'maximo', devuelve {'figuras': []}."""
    from PIL import Image
    with Image.open(io.BytesIO(datos)) as img:
        img = img.convert("RGB")
        img.thumbnail((192, 192))
        w, h = img.size
        px = img.load()
        borde = [px[x, 0] for x in range(w)] + [px[x, h - 1] for x in range(w)] + [px[0, y] for y in range(h)] + [px[w - 1, y] for y in range(h)]
        fondo, n_f = Counter(borde).most_common(1)[0]
        if n_f < 0.8 * len(borde):
            return {"figuras": []}
        es_fig = [[_dist(px[x, y], fondo) > UMBRAL_DIF for x in range(w)] for y in range(h)]
        visto = [[False] * w for _ in range(h)]
        comps = []
        for y in range(h):
            for x in range(w):
                if es_fig[y][x] and not visto[y][x]:
                    pila, comp = [(x, y)], []
                    visto[y][x] = True
                    while pila:
                        a, b = pila.pop()
                        comp.append((a, b))
                        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            c_, d_ = a + da, b + db
                            if 0 <= c_ < w and 0 <= d_ < h and es_fig[d_][c_] and not visto[d_][c_]:
                                visto[d_][c_] = True
                                pila.append((c_, d_))
                    if len(comp) >= 0.004 * w * h:
                        comps.append(comp)
        if len(comps) < 2 or len(comps) > maximo:
            return {"figuras": []}
        figs = [_clasifica(c, px) for c in comps]
        rels = []
        for i, a in enumerate(figs):
            for j, b in enumerate(figs):
                if i == j:
                    continue
                (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = a["caja"], b["caja"]
                if ax0 >= bx0 and ay0 >= by0 and ax1 <= bx1 and ay1 <= by1:
                    rels.append((i, "dentro", j)); continue
                solapa_x = min(ax1, bx1) - max(ax0, bx0) > 0
                solapa_y = min(ay1, by1) - max(ay0, by0) > 0
                if ay1 < by0 and solapa_x:
                    rels.append((i, "sobre", j))
                elif ay0 > by1 and solapa_x:
                    rels.append((i, "bajo", j))
                elif ax1 < bx0 and solapa_y:
                    rels.append((i, "izquierda", j))
                elif ax0 > bx1 and solapa_y:
                    rels.append((i, "derecha", j))
        return {"figuras": figs, "relaciones": rels, "fondo": clasificar_rgb(fondo)}
