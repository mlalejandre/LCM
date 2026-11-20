# LCM_VISION_01_GENERATED
"""Puente entre la percepcion visual y las identidades conceptuales del LCM."""
from __future__ import annotations

import hashlib
import re
import unicodedata

from .color_features import COLORES


def rasgos_color(color):
    return {"categoria:color": 1.0, f"identidad:cromatica:{color.lower()}": 1.0}


def asegurar_conceptos_en_memoria(mem):
    """No crea un vocabulario visual paralelo: usa la clave semantica existente."""
    mem.add_concept("COLOR", features={"categoria:propiedad": 1.0}, kind="category")
    for color in COLORES:
        mem.add_concept(color, features=rasgos_color(color), kind="color")
        if not any(f["s"] == color and f["p"] == "SER" and f["o"] == "COLOR" and not f.get("neg") for f in mem.facts):
            mem.add_fact((color, "SER", "COLOR"), source="vision:catalogo:0.1")
        mem.display.setdefault(color, color.lower())
    mem.display.setdefault("COLOR", "color")


def asegurar_conceptos_en_espacio(space):
    """Usa los conceptos de ConceptSpace existentes; si faltan, los incorpora.

    IMPORTANTE: si ya existe VERDE, conserva sus rasgos y vector original.
    """
    for nombre, rasgos, clase in [("COLOR", {"categoria:propiedad": 1.0}, "category")] + [
        (color, rasgos_color(color), "color") for color in COLORES
    ]:
        if nombre in space.concept_to_id:
            continue
        if space.embeddings is None:
            space.register_concept(nombre, es_text=nombre.lower(), features=rasgos, kind=clase)
        else:
            space.add_concept(nombre, es_text=nombre.lower(), features=rasgos, kind=clase)
    return {color: space.get_vector(color) for color in COLORES} if space.embeddings is not None else None


def registrar_observacion(mem, datos: bytes, color: str) -> tuple[str, bool]:
    if color not in COLORES:
        raise ValueError("No se registran colores no identificados.")
    asegurar_conceptos_en_memoria(mem)
    digest = hashlib.sha256(datos).hexdigest()[:12].upper()
    entidad = "IMAGEN_" + digest
    mem.add_concept(entidad, features={f"identidad:imagen:{digest}": 1.0}, kind="perception")
    mem.display.setdefault(entidad, "imagen " + digest[:6].lower())
    hecho = (entidad, "TENER_COLOR", color)
    existe = any((f["s"], f["p"], f["o"]) == hecho and not f.get("neg") for f in mem.facts)
    if not existe:
        mem.add_fact(hecho, source="vision:imagen:" + digest.lower())
    return entidad, not existe


def ultima_observacion(mem):
    for f in reversed(mem.facts):
        if (str(f.get("source", "")).startswith("vision:imagen:")
                and f.get("p") == "TENER_COLOR" and not f.get("neg")):
            return f
    return None


def _normalizar(texto: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFD", str(texto).lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", t).strip()


def es_pregunta_color_visual(texto: str) -> bool:
    """No secuestra preguntas generales como '¿De qué color es la hierba?'."""
    t = _normalizar(texto)
    if "color" not in t.split():
        return False
    palabras = set(t.split())
    if palabras.intersection({"imagen", "foto", "fotografia", "archivo", "adjunto", "esta", "esto", "este"}):
        return bool(palabras.intersection({"que", "cual", "dime", "indica", "tiene", "es"}))
    return t in {
        "que color es", "de que color es", "que color tiene", "cual es el color",
        "dime el color", "dime que color es", "que color ves", "de que color es esto",
        "y de que color es", "y el color", "que color tiene la imagen",
    }


def color_solicitado(texto: str):
    """Petición explícita de una muestra visual; no sustituye preguntas semánticas."""
    t = _normalizar(texto)
    if not t:
        return None
    palabras = set(t.split())
    acciones = {"muestra", "muestrame", "mostrar", "muestrame", "pon", "dame", "presenta",
                "presentame", "ensena", "ensename", "dibujame", "genera", "generame", "quiero",
                "ejemplo", "ver", "visualiza", "imagen", "cuadro", "representa"}
    # Se exige intención de ver una muestra, no solo una mención a verde.
    if not palabras.intersection(acciones):
        return None
    encontrados = [c for c in COLORES if c.lower() in palabras]
    return encontrados[0] if len(encontrados) == 1 else None


def responder_pregunta_visual(mem, texto: str, observacion_actual=None):
    """Interpreta la referencia a la imagen adjunta; permite abstención explícita."""
    if not es_pregunta_color_visual(texto):
        return None
    if observacion_actual is not None:
        color = observacion_actual.get("concepto")
        if not color:
            return observacion_actual.get("respuesta") or "No he podido identificar un color predominante."
        return (f"La imagen es de color {color.lower()}. Lo he identificado al analizar sus píxeles "
                "y lo he vinculado con ese concepto en la memoria del LCM.")
    f = ultima_observacion(mem)
    if f is None:
        return "Todavía no he observado ninguna imagen con un color identificable."
    return (f"La última imagen identificada tiene color {f['o'].lower()}. "
            "Lo sé por una observación visual guardada en mi memoria.")
