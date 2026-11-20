# LCM_VISION_01_GENERATED
"""Experimento OPCIONAL: perceptron RGB -> 6 identidades conceptuales.

No sustituye a la percepcion HSV de produccion y NO aprende imagenes naturales.
Los ejemplos sinteticos tienen una prueba separada con otra semilla.
"""
from __future__ import annotations

import colorsys
import random

from .color_features import COLORES


def muestras(n_por_color=200, semilla=42):
    rng = random.Random(semilla)
    entradas, etiquetas = [], []
    hue = {"ROJO": (0, 10), "VERDE": (128, 27), "AZUL": (224, 22), "AMARILLO": (58, 11)}
    for idx, color in enumerate(COLORES):
        for _ in range(n_por_color):
            if color == "BLANCO":
                h, s, v = rng.random(), rng.uniform(0.0, 0.09), rng.uniform(0.88, 1.0)
            elif color == "NEGRO":
                h, s, v = rng.random(), rng.random(), rng.uniform(0.0, 0.13)
            else:
                centro, margen = hue[color]
                h = ((centro + rng.uniform(-margen, margen)) % 360) / 360
                s, v = rng.uniform(0.52, 1.0), rng.uniform(0.45, 1.0)
            entradas.append(list(colorsys.hsv_to_rgb(h, s, v)))
            etiquetas.append(idx)
    order = list(range(len(etiquetas)))
    rng.shuffle(order)
    return [entradas[i] for i in order], [etiquetas[i] for i in order]


def construir_modelo():
    import torch.nn as nn
    return nn.Sequential(nn.Linear(3, 48), nn.ReLU(), nn.Linear(48, 48), nn.ReLU(), nn.Linear(48, len(COLORES)))


def evaluar_modelo(modelo, semilla=2027, n=100):
    import torch
    x, y = muestras(n_por_color=n, semilla=semilla)
    with torch.no_grad():
        logits = modelo(torch.tensor(x, dtype=torch.float32))
        pred = logits.argmax(dim=-1).tolist()
    return sum(int(a == b) for a, b in zip(pred, y)) / len(y)


def entrenar(salida, epocas=70, semilla=42):
    import torch
    torch.manual_seed(semilla)
    torch.set_num_threads(min(torch.get_num_threads(), 4))
    modelo = construir_modelo()
    x, y = muestras(n_por_color=300, semilla=semilla)
    x = torch.tensor(x, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.long)
    opt = torch.optim.Adam(modelo.parameters(), lr=0.004)
    mejor, estado = -1, None
    for _ in range(epocas):
        modelo.train()
        order = torch.randperm(len(y))
        for ix in order.split(128):
            opt.zero_grad()
            loss = torch.nn.functional.cross_entropy(modelo(x[ix]), y[ix])
            loss.backward()
            opt.step()
        modelo.eval()
        valid = evaluar_modelo(modelo, semilla=semilla + 1, n=60)
        if valid > mejor:
            mejor = valid
            estado = {k: v.detach().clone() for k, v in modelo.state_dict().items()}
    modelo.load_state_dict(estado)
    from pathlib import Path
    ruta = Path(salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"version": 1, "etiquetas": list(COLORES), "state_dict": estado}, ruta)
    return mejor


def cargar(ruta):
    import torch
    ckpt = torch.load(ruta, map_location="cpu", weights_only=True)
    if ckpt.get("version") != 1 or ckpt.get("etiquetas") != list(COLORES):
        raise ValueError("Checkpoint incompatible con LCM Vision 0.1.")
    modelo = construir_modelo()
    modelo.load_state_dict(ckpt["state_dict"])
    modelo.eval()
    return modelo
