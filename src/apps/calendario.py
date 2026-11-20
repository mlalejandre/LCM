"""Aplicaciones de calendario y reloj: días de la semana y horas, por cálculo modular (sin memoria)."""
from __future__ import annotations

from .registro import App, ErrorApp, registra

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_SIN = {"miercoles": "miércoles", "sabado": "sábado"}


def dia_indice(d: str) -> int:
    d = _SIN.get(d.lower(), d.lower())
    if d not in DIAS:
        raise ErrorApp(f"«{d}» no es un día de la semana")
    return DIAS.index(d)


def _dia_mas(dia, n):
    return DIAS[(dia_indice(dia) + int(n)) % 7]


def _hora_mas(h, m, dh, dm=0):
    t = (int(h) * 60 + int(m) + int(dh) * 60 + int(dm)) % (24 * 60)
    return (t // 60, t % 60)


registra(App("dia_semana", "calendario", _dia_mas, (2, 2), "día+", 0, nombre_humano="el calendario semanal", concepto="operación de calendario",
             lexico={"relativo": {"mañana": 1, "pasado mañana": 2, "ayer": -1, "anteayer": -2, "antes de ayer": -2, "hoy": 0}},
             ejemplos=[("si hoy es lunes, ¿qué día será mañana?", "martes"), ("si hoy es viernes, ¿qué día fue ayer?", "jueves")]))
registra(App("hora_mas", "calendario", _hora_mas, (3, 4), "h+", 0, nombre_humano="el reloj", concepto="operación de calendario",
             lexico={"duracion": ["tarda", "dura", "tardo", "tardamos", "durará", "tardará"]},
             ejemplos=[("si el tren sale a las 10 y tarda 3 horas, ¿a qué hora llega?", "13")]))
