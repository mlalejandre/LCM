"""LCM 2.0 · núcleo conversacional unificado (grafo único de entidades, relaciones y marcos)."""
from .dialogo import Conversador
from .preguntas import Preguntador


class Nucleo20(Preguntador, Conversador):
    """Núcleo completo: afirmaciones + preguntas + trato social sobre un único grafo."""


def activo(parser) -> bool:
    """Solo se activa con la Escuela real (modelo entrenado); con analizadores de prueba, no interviene."""
    import os
    if os.environ.get("LCM_NUCLEO20", "1") == "0":
        return False
    return parser is not None and hasattr(parser, "tree") and getattr(parser, "model", None) is not None
