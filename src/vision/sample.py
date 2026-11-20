# LCM_VISION_01_GENERATED
"""Muestras PNG reproducibles de colores declarados, sin servicios externos ni LLM."""
from __future__ import annotations

import struct
import zlib

RGB = {
    "ROJO": (220, 38, 38),
    "VERDE": (22, 163, 74),
    "AZUL": (37, 99, 235),
    "AMARILLO": (250, 204, 21),
    "BLANCO": (250, 250, 250),
    "NEGRO": (23, 23, 23),
    "NARANJA": (249, 115, 22),
    "ROSA": (244, 114, 182),
    "MORADO": (126, 34, 206),
    "MARRON": (120, 63, 4),
    "GRIS": (128, 128, 128),
}


def muestra_png(color: str, ancho: int = 400, alto: int = 224) -> bytes:
    """PNG RGB real del color solicitado; admite solo colores del catálogo."""
    if not isinstance(color, str) or color.upper() not in RGB:
        raise ValueError("Color no disponible en Visión 0.1.")
    if not (1 <= ancho <= 1024 and 1 <= alto <= 1024):
        raise ValueError("Dimensiones no permitidas.")
    rgb = bytes(RGB[color.upper()])
    scanline = b"\x00" + rgb * ancho
    raw = scanline * alto
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 7)) + chunk(b"IEND", b""))


def datos_muestra(color: str) -> dict:
    color = color.upper()
    if color not in RGB:
        raise ValueError("Color no disponible.")
    return {"color": color, "hex": "#" + "".join(f"{v:02X}" for v in RGB[color]),
            "url": "/api/vision/muestra?color=" + color,
            "alt": "Muestra uniforme del color " + color.lower()}
