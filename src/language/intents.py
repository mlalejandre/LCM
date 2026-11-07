"""Enrutador de OPERACIONES (parche-87). Capa 1 de la arquitectura nueva: en vez de una regex por cada forma de preguntar, un clasificador pequeno
decide QUE OPERACION pide una frase (hora, fecha, calculo de fechas, identidad, ubicacion, capacidades...) o devuelve OTRO (= seguir con el
pipeline de siempre). Se entrena con datos sinteticos (src/language/intents_gen.py) y se evalua con un examen ciego distinto.

Sin dependencias (ni numpy ni torch): rasgos hash de palabras, bigramas y n-gramas de caracteres + regresion logistica multinomial en Python puro.
El modelo es un JSON (src/language/intents_modelo.json) que se regenera con  python -m scripts.entrenar_intents .
"""
from __future__ import annotations

import json
import math
import os
import re
import zlib
from typing import Dict, List, Tuple

from .lexicon import norm

DIM = 8192
MODEL_PATH = os.path.join(os.path.dirname(__file__), "intents_modelo.json")
OPS = ["OTRO", "HORA", "FECHA", "CALC_FECHA", "IDENTIDAD", "UBICACION", "CAPACIDAD", "ARITMETICA", "DIA_SEMANA", "DIAS_HASTA", "FUERA"]
THRESHOLD = 0.80
FUERA_START = {"pon", "ponme", "reproduce", "busca", "reserva", "compra", "envia", "enviame", "mandame", "manda", "abre", "llama", "descarga", "enciende", "apaga", "programa",
               "dime", "muestrame", "recomiendame", "pide", "cancela", "agenda", "cuentame", "traduce", "escribeme", "hazme", "quien", "que", "cual", "cuanto", "como", "donde",
               "cuando", "va", "hace", "oye", "por", "sabes", "me", "puedes", "podrias", "ayudame", "hay", "esta", "cuales", "a"}


def clean(text: str) -> str:
    t = norm(text)
    t = re.sub(r"[¡!¿?.,;:\"«»()]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def features(text: str) -> Dict[int, float]:
    t = clean(text)
    w = t.split()
    keys = ["w:" + x for x in w] + ["b:" + a + "_" + b for a, b in zip(w, w[1:])]
    if w:
        keys += ["f:" + w[0], "l:" + w[-1]]
    s = " " + t + " "
    keys += ["c:" + s[i:i + 3] for i in range(len(s) - 2)] + ["c4:" + s[i:i + 4] for i in range(len(s) - 3)]
    keys.append("n:" + str(min(len(w), 12)))
    keys.append("digit" if re.search(r"\d", t) else "nodigit")
    f: Dict[int, float] = {}
    for k in keys:
        h = zlib.crc32(k.encode("utf-8")) % DIM
        f[h] = f.get(h, 0.0) + 1.0
    nrm = math.sqrt(sum(v * v for v in f.values())) or 1.0
    return {h: v / nrm for h, v in f.items()}


def softmax(z: List[float]) -> List[float]:
    m = max(z)
    e = [math.exp(x - m) for x in z]
    s = sum(e)
    return [x / s for x in e]


class Router:
    def __init__(self, weights: List[Dict[str, float]], bias: List[float]):
        self.w = [{int(k): v for k, v in d.items()} for d in weights]
        self.b = bias

    def scores(self, text: str) -> List[float]:
        f = features(text)
        return softmax([self.b[c] + sum(v * self.w[c].get(h, 0.0) for h, v in f.items()) for c in range(len(OPS))])

    def route(self, text: str) -> Tuple[str, float]:
        p = self.scores(text)
        k = max(range(len(p)), key=p.__getitem__)
        return OPS[k], p[k]


_ROUTER = None


def load(path: str = MODEL_PATH):
    global _ROUTER
    if _ROUTER is None and os.path.exists(path):
        d = json.load(open(path, encoding="utf-8"))
        _ROUTER = Router(d["w"], d["b"])
    return _ROUTER


def route(text: str) -> Tuple[str, float]:
    """(operacion, confianza). ("OTRO", 0) si no hay modelo o no se llega al umbral."""
    r = load()
    if r is None or not text or len(text) > 200:
        return "OTRO", 0.0
    op, p = r.route(text)
    if op == "FUERA":
        # "fuera de alcance" es una clase abierta y peligrosa: solo si hay forma de pregunta/orden y mas confianza (si no, "Ana abre la puerta." seria FUERA)
        w = clean(text).split()
        if not (("?" in text or "¿" in text or (w and w[0] in FUERA_START)) and p >= 0.90):
            return "OTRO", p
    return (op, p) if op != "OTRO" and p >= THRESHOLD else ("OTRO", p)
