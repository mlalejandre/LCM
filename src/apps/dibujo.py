"""Aplicación de dibujo: genera una figura geométrica en SVG, determinista. El LCM solo elige figura, color y cantidad."""
from __future__ import annotations

import math

from .registro import App, ErrorApp, registra

FIGURAS = {"círculo": "m", "circulo": "m", "cuadrado": "m", "triángulo": "m", "triangulo": "m", "rectángulo": "m", "rectangulo": "m",
           "estrella": "f", "rombo": "m", "pentágono": "m", "pentagono": "m", "hexágono": "m", "hexagono": "m", "óvalo": "m", "ovalo": "m",
           "elipse": "f", "línea": "f", "linea": "f", "corazón": "m", "corazon": "m"}
CANON = {"circulo": "círculo", "triangulo": "triángulo", "rectangulo": "rectángulo", "pentagono": "pentágono", "hexagono": "hexágono",
         "ovalo": "óvalo", "linea": "línea", "corazon": "corazón"}
PLURAL = {"círculo": "círculos", "cuadrado": "cuadrados", "triángulo": "triángulos", "rectángulo": "rectángulos", "estrella": "estrellas",
          "rombo": "rombos", "pentágono": "pentágonos", "hexágono": "hexágonos", "óvalo": "óvalos", "elipse": "elipses", "línea": "líneas",
          "corazón": "corazones"}
SINGULAR = {v: k for k, v in PLURAL.items()}
SINGULAR.update({"circulos": "círculo", "triangulos": "triángulo", "rectangulos": "rectángulo", "pentagonos": "pentágono", "hexagonos": "hexágono",
                 "ovalos": "óvalo", "lineas": "línea"})


def canon(f: str) -> str:
    f = f.lower()
    f = SINGULAR.get(f, f)
    return CANON.get(f, f)


def _hex_color(color):
    if not color:
        return "#555555"
    try:
        from src.vision.sample import datos_muestra
        return datos_muestra(color)["hex"]
    except Exception:
        return "#555555"


def _poligono(cx, cy, r, n, giro=-90):
    return " ".join(f"{cx + r * math.cos(math.radians(giro + 360 * i / n)):.1f},{cy + r * math.sin(math.radians(giro + 360 * i / n)):.1f}" for i in range(n))


def _estrella(cx, cy, r):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        a = math.radians(-90 + 36 * i)
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return " ".join(pts)


def _forma(f, cx, cy, r, col):
    if f == "círculo":
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}"/>'
    if f == "cuadrado":
        return f'<rect x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" fill="{col}"/>'
    if f == "rectángulo":
        return f'<rect x="{cx - r * 1.4:.1f}" y="{cy - r * 0.8:.1f}" width="{2.8 * r:.1f}" height="{1.6 * r:.1f}" fill="{col}"/>'
    if f == "triángulo":
        return f'<polygon points="{_poligono(cx, cy + r * 0.15, r * 1.1, 3)}" fill="{col}"/>'
    if f == "rombo":
        return f'<polygon points="{_poligono(cx, cy, r, 4)}" fill="{col}"/>'
    if f == "pentágono":
        return f'<polygon points="{_poligono(cx, cy, r, 5)}" fill="{col}"/>'
    if f == "hexágono":
        return f'<polygon points="{_poligono(cx, cy, r, 6, 0)}" fill="{col}"/>'
    if f == "estrella":
        return f'<polygon points="{_estrella(cx, cy, r * 1.1)}" fill="{col}"/>'
    if f in ("óvalo", "elipse"):
        return f'<ellipse cx="{cx}" cy="{cy}" rx="{r * 1.4:.1f}" ry="{r * 0.85:.1f}" fill="{col}"/>'
    if f == "línea":
        return f'<line x1="{cx - r}" y1="{cy}" x2="{cx + r}" y2="{cy}" stroke="{col}" stroke-width="8" stroke-linecap="round"/>'
    if f == "corazón":
        return (f'<path d="M{cx},{cy + r} C{cx - 1.6 * r:.1f},{cy - 0.2 * r:.1f} {cx - 0.7 * r:.1f},{cy - 1.4 * r:.1f} {cx},{cy - 0.45 * r:.1f} '
                f'C{cx + 0.7 * r:.1f},{cy - 1.4 * r:.1f} {cx + 1.6 * r:.1f},{cy - 0.2 * r:.1f} {cx},{cy + r} Z" fill="{col}"/>')
    raise ErrorApp(f"no sé dibujar «{f}»")


def _dibuja(piezas):
    """piezas: lista de (figura, color|None, cantidad). Devuelve {svg, piezas, alt}."""
    elems = []
    for f, c, n in piezas:
        f = canon(f)
        if f not in PLURAL:
            raise ErrorApp(f"no sé dibujar «{f}»")
        if not 1 <= int(n) <= 12:
            raise ErrorApp("Dibujo entre una y doce figuras de cada clase.")
        elems += [(f, c)] * int(n)
    if not elems or len(elems) > 24:
        raise ErrorApp("No hay nada que dibujar.")
    ancho = 120 * len(elems)
    cuerpo = "".join(_forma(f, 60 + 120 * i, 60, 40, _hex_color(c)) for i, (f, c) in enumerate(elems))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="120" viewBox="0 0 {ancho} 120">'
           f'<rect width="100%" height="100%" fill="#ffffff"/>{cuerpo}</svg>')
    return {"svg": svg, "piezas": [list(p) for p in piezas], "alt": ", ".join(f"{n} {f}{' ' + c if c else ''}" for f, c, n in piezas)}


registra(App("dibujo", "dibujo", _dibuja, (1, 1), "svg", 0, nombre_humano="la aplicación de dibujo", concepto="aplicación de dibujo",
             lexico={"verbo": ["dibuja", "dibújame", "dibujame", "dibujes", "dibujar", "pinta", "píntame", "pintame", "pintes", "pintar", "muestra", "muéstrame",
                               "muestrame", "enseña", "enséñame", "enseñame", "haz", "hazme", "traza", "trázame", "dibújalo", "me dibujas", "me pintas"],
                     "figuras": sorted(set(CANON.get(f, f) for f in FIGURAS))},
             ejemplos=[("dibuja un círculo", "círculo"), ("pinta un triángulo rojo", "triángulo"), ("dibuja dos círculos", "círculos")]))
