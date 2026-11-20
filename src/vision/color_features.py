# LCM_VISION_01_GENERATED
"""Extraccion cromatica auditable para imagenes predominantemente uniformes.

Esto es percepcion por reglas, NO un modelo visual entrenado.
`fraccion` mide cobertura de pixeles, no probabilidad calibrada.
"""
from __future__ import annotations

import colorsys
import io
from collections import Counter

COLORES = ("ROJO", "VERDE", "AZUL", "AMARILLO", "BLANCO", "NEGRO", "NARANJA", "ROSA", "MORADO", "MARRON", "GRIS")
NOMBRES = {c: c.lower() for c in COLORES}
MAX_BYTES = 8_000_000
MAX_PIXELS = 4_000_000
UMBRALES_DOMINANCIA = 0.85


def clasificar_rgb(rgb):
    """Clasificacion conservadora de un pixel RGB (0..255)."""
    r, g, b = (max(0, min(255, int(x))) / 255 for x in rgb[:3])
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h *= 360
    if v <= 0.16:
        return "NEGRO"
    if s <= 0.12:
        if v >= 0.86:
            return "BLANCO"
        return "GRIS" if 0.30 <= v <= 0.75 else None       # LCM 2.3: zonas muertas entre gris, blanco y negro
    if (h >= 330 or h <= 12) and 0.18 <= s < 0.60 and v >= 0.80:
        return "ROSA"                                       # rojo claro poco saturado
    if s < 0.27 or v < 0.24:
        return None
    if h <= 16 or h >= 345:
        return "ROJO"
    if 19 <= h <= 40:
        if v >= 0.80:
            return "NARANJA"
        return "MARRON" if v <= 0.62 else None
    if 43 <= h <= 75:
        return "AMARILLO"
    if 84 <= h <= 169:
        return "VERDE"
    if 198 <= h <= 255:
        return "AZUL"
    if 262 <= h <= 299:
        return "MORADO"
    if 300 <= h <= 340:
        return "ROSA" if v >= 0.70 else ("MORADO" if v <= 0.60 else None)
    return None


def analizar_imagen(datos: bytes) -> dict:
    """Devuelve identificacion o abstencion. Rechaza formatos/tamanos inseguros."""
    if not isinstance(datos, bytes) or not datos:
        raise ValueError("No se recibieron bytes de imagen.")
    if len(datos) > MAX_BYTES:
        raise ValueError("La imagen supera el limite de 8 MB.")
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError as exc:
        raise RuntimeError("Falta Pillow. Instala: pip install -r requirements-vision.txt") from exc
    try:
        with Image.open(io.BytesIO(datos)) as img:
            if img.format not in ("PNG", "JPEG", "WEBP"):
                raise ValueError("Formato no admitido. Usa PNG, JPEG o WebP.")
            ancho, alto = img.size
            if ancho < 1 or alto < 1 or ancho * alto > MAX_PIXELS:
                raise ValueError("Dimensiones de imagen no admitidas (maximo 4 MP).")
            img = ImageOps.exif_transpose(img)
            img.thumbnail((96, 96))
            img = img.convert("RGBA")
            obtener_pixeles = getattr(img, "get_flattened_data", None)
            pixeles = [p[:3] for p in (obtener_pixeles() if obtener_pixeles else img.getdata()) if p[3] >= 128]
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError("La imagen no se puede leer o esta danada.") from exc
    if not pixeles:
        return {"concepto": None, "fraccion": 0.0, "mensaje": "La imagen no contiene pixeles opacos.",
                "distribucion": {}, "tamano": [ancho, alto], "metodo": "HSV-reglas"}
    conteos = Counter(clasificar_rgb(p) or "OTRO" for p in pixeles)
    dominante, n = conteos.most_common(1)[0]
    fraccion = n / len(pixeles)
    concepto = dominante if dominante in COLORES and fraccion >= UMBRALES_DOMINANCIA else None
    if concepto:
        mensaje = f"El color predominante es {concepto.lower()} ({fraccion:.1%} de los pixeles analizados)."
    else:
        mensaje = "Color no determinado: imagen mixta, tonalidad ambigua o color fuera del catalogo."
    return {"concepto": concepto, "fraccion": round(fraccion, 4), "mensaje": mensaje,
            "distribucion": dict(sorted(conteos.items())), "tamano": [ancho, alto], "metodo": "HSV-reglas"}
