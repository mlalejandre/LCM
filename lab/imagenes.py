"""Imágenes sintéticas para las pruebas multimodales: color liso y figuras simples sobre un fondo."""
import io
import math

from PIL import Image, ImageDraw

RGB = {"rojo": (220, 38, 38), "azul": (37, 99, 235), "verde": (22, 163, 74), "amarillo": (250, 204, 21), "negro": (10, 10, 10), "blanco": (250, 250, 250),
       "naranja": (249, 115, 22), "rosa": (244, 114, 182), "morado": (126, 34, 206), "marron": (120, 63, 4), "gris": (128, 128, 128), "turquesa": (0, 200, 200)}


def png(color, lado=48):
    b = io.BytesIO()
    Image.new("RGB", (lado, lado), RGB.get(color, color)).save(b, "PNG")
    return b.getvalue()


def figura(forma, color, fondo="blanco", lado=96, escala=0.6, aspecto=1.0):
    im = Image.new("RGB", (lado, lado), RGB.get(fondo, fondo))
    d = ImageDraw.Draw(im)
    w = lado * escala; h = w / aspecto
    x0, y0 = (lado - w) / 2, (lado - h) / 2
    c = RGB.get(color, color)
    if forma == "circulo":
        d.ellipse([x0, y0, x0 + w, y0 + h], fill=c)
    elif forma in ("cuadrado", "rectangulo"):
        d.rectangle([x0, y0, x0 + w, y0 + h], fill=c)
    elif forma == "triangulo":
        d.polygon([(lado / 2, y0), (x0, y0 + h), (x0 + w, y0 + h)], fill=c)
    elif forma == "estrella":
        pts = []
        for k in range(10):
            r = (w / 2) * (1 if k % 2 == 0 else 0.4)
            a = -math.pi / 2 + k * math.pi / 5
            pts.append((lado / 2 + r * math.cos(a), lado / 2 + r * math.sin(a)))
        d.polygon(pts, fill=c)
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def img(texto, datos, nombre="foto.png"):
    return {"texto": texto, "imagen": datos, "nombre": nombre}


def escena(arriba, abajo, fondo="blanco", ancho=96, alto=192, vertical=True):
    """Dos figuras en una misma imagen: arriba=(forma, color) y abajo=(forma, color).
    Con vertical=False, «arriba» va a la izquierda y «abajo» a la derecha."""
    im = Image.new("RGB", (ancho, alto) if vertical else (alto, ancho), RGB.get(fondo, fondo))
    for k, (forma, color) in enumerate((arriba, abajo)):
        sub = Image.open(io.BytesIO(figura(forma, color, fondo=fondo, lado=ancho)))
        im.paste(sub, (0, k * ancho) if vertical else (k * ancho, 0))
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()
