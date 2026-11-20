"""LCM 2.13 · ÓRDENES DE DIBUJAR, PINTAR Y MOSTRAR.

«dibuja un círculo», «quiero que dibujes un cuadrado», «¿me pintas un triángulo rojo?», «enséñame el color naranja»:
es una orden, no un hecho que guardar. El LCM reconoce QUÉ figura(s), de qué color y cuántas, y la aplicación de dibujo
(`src.apps.dibujo`) genera la imagen. Verbos y figuras salen del léxico de esa aplicación.
"""
from __future__ import annotations

import base64
import re

from src.apps import registro as R
from src.apps import dibujo as D
from .morfo import sa
from .numerales import a_cifras

_COLORES = {"rojo": "ROJO", "roja": "ROJO", "rojos": "ROJO", "rojas": "ROJO", "azul": "AZUL", "azules": "AZUL", "verde": "VERDE", "verdes": "VERDE",
            "amarillo": "AMARILLO", "amarilla": "AMARILLO", "amarillos": "AMARILLO", "amarillas": "AMARILLO", "negro": "NEGRO", "negra": "NEGRO",
            "negros": "NEGRO", "negras": "NEGRO", "blanco": "BLANCO", "blanca": "BLANCO", "blancos": "BLANCO", "blancas": "BLANCO", "gris": "GRIS",
            "grises": "GRIS", "naranja": "NARANJA", "naranjas": "NARANJA", "morado": "MORADO", "morada": "MORADO", "morados": "MORADO", "moradas": "MORADO",
            "rosa": "ROSA", "rosas": "ROSA", "marron": "MARRON", "marrón": "MARRON", "marrones": "MARRON"}
_NOMBRE_COLOR = {"ROJO": "rojo", "AZUL": "azul", "VERDE": "verde", "AMARILLO": "amarillo", "NEGRO": "negro", "BLANCO": "blanco", "GRIS": "gris",
                 "NARANJA": "naranja", "MORADO": "morado", "ROSA": "rosa", "MARRON": "marrón"}
_FEM = {"estrella", "elipse", "línea"}


def _verbos():
    return sorted({sa(v.lower()) for v in R.app("dibujo").lexico["verbo"]}, key=len, reverse=True)


def _figura(w):
    w = sa(w.lower())
    for f in list(D.PLURAL) + list(D.SINGULAR) + list(D.CANON):
        if sa(f) == w:
            return D.canon(f)
    return None


_PRE = r"^(?:(?:oye|lcm|venga|ahora|y|por favor|porfa|vale)\s*,?\s+)*"
_PIDE = (r"(?:(?:quiero|quisiera|me gustaria|necesito)\s+que\s+(?:me\s+)?|(?:me\s+)?(?:puedes|podrias|sabes|sabrias)\s+(?:me\s+)?|"
         r"(?:me\s+)?(?:haces|haras)\s+(?:el\s+favor\s+de\s+)?)?(?:me\s+)?")


def orden(texto):
    """-> {"piezas": [(figura, COLOR|None, n)], "colores": [COLOR], "verbo": v} | {"desconocido": obj, "verbo": v} | None."""
    t = sa((texto or "").lower()).strip(" ¿?¡!.")
    t = re.sub(r"\s+", " ", t)
    verbos = "|".join(re.escape(v) for v in _verbos())
    m = re.match(_PRE + _PIDE + rf"({verbos}|dibujar|pintar|mostrar|ensenar)(?:me|nos|lo|la)?\s+(.+?)(?:\s*,?\s*(?:por favor|porfa))?$", t)
    if not m:
        return None
    verbo, obj = m.group(1), a_cifras(m.group(2), articulos=False)
    dibujar = verbo.startswith(("dibuj", "pint", "traz"))
    trozos = [x.strip() for x in re.split(r"\s*,\s*|\s+y\s+|\s+e\s+", obj) if x.strip()]
    piezas, colores = [], []
    for x in trozos:
        mx = re.match(r"^(?:(?:un|una|el|la|los|las|unos|unas|(\d+))\s+)?(?:(?:muestra\s+)?(?:del?\s+)?(?:el\s+)?color\s+)?([a-zñ]+)(?:\s+(?:de\s+color\s+|en\s+)?([a-zñ]+))?$", x)
        if not mx:
            return {"desconocido": x, "verbo": verbo} if dibujar else None
        n = int(mx.group(1) or 1)
        a, b = mx.group(2), mx.group(3)
        f = _figura(a)
        if f:
            col = _COLORES.get(b) if b else None
            if b and not col:
                return {"desconocido": x, "verbo": verbo} if dibujar else None
            piezas.append((f, col, n))
        elif a in _COLORES and not b:
            colores.append(_COLORES[a])
        else:
            return {"desconocido": x, "verbo": verbo} if dibujar else None
    if not piezas and not colores:
        return None
    if not dibujar and not re.search(r"\b(?:color|circulo|cuadrado|triangulo|rectangulo|estrella|rombo|pentagono|hexagono|ovalo|elipse|corazon|linea)", obj):
        return None                                   # «enséñame verde» no basta: «muestra»/«enseña» piden figura o «el color X»
    return {"piezas": piezas, "colores": colores, "verbo": verbo}


def _art(f, n):
    if n == 1:
        return ("una " if f in _FEM else "un ") + f
    return f"{n} {D.PLURAL.get(f, f + 's')}" if n > 2 else f"dos {D.PLURAL.get(f, f + 's')}"


def _col(f, c, n):
    if not c:
        return ""
    w = _NOMBRE_COLOR[c]
    if w.endswith("o") and f in _FEM:
        w = w[:-1] + "a"
    if n > 1 and w[-1] in "aeo":
        w += "s"
    elif n > 1 and w not in ("naranja", "rosa"):
        w += "es"
    return " " + w


def describe(piezas, colores):
    xs = [_art(f, n) + _col(f, c, n) for f, c, n in piezas] + [f"una muestra del color {_NOMBRE_COLOR[c]}" for c in colores]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def ejecuta(o):
    """Llama a la aplicación de dibujo (o a la muestra de color) y devuelve (texto, imagen, traza)."""
    trazas, imagen = [], None
    if o["piezas"]:
        v, tr = R.ejecuta("dibujo", o["piezas"])
        trazas.append(tr)
        svg = v["svg"]
        imagen = {"tipo": "svg", "svg": svg, "url": "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode(), "alt": "Dibujo: " + describe(o["piezas"], [])}
    if o["colores"]:
        from src.vision.sample import datos_muestra
        m = datos_muestra(o["colores"][0])
        if imagen is None:
            imagen = m
        else:
            imagen = dict(imagen, muestras=[datos_muestra(c) for c in o["colores"]])
        trazas.append({"app": "muestra_color", "familia": "dibujo", "args": o["colores"], "valor": m["hex"], "version": "1.0"})
    if o["piezas"] and not o["colores"]:
        total = sum(n for _, _, n in o["piezas"])
        fem = all(D.canon(f) in _FEM for f, _, _ in o["piezas"])
        hecho = ("hecha" if fem else "hecho") + ("s" if total > 1 else "")
        txt = f"Aquí tienes {describe(o['piezas'], [])}, {hecho} con la aplicación de dibujo."
    elif o["colores"] and not o["piezas"]:
        txt = f"He creado {describe([], o['colores'])}."
    else:
        txt = f"Aquí tienes {describe(o['piezas'], o['colores'])}."
    return txt, imagen, trazas


def no_se(o):
    figs = ", ".join(sorted({D.canon(f) for f in ("círculo", "cuadrado", "triángulo", "rectángulo", "estrella", "rombo", "hexágono", "corazón")}))
    return (f"No sé dibujar «{o['desconocido']}»: solo dibujo figuras geométricas ({figs}…), con color si quieres, "
            "y muestras de color.")
