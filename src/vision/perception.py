# LCM_VISION_01_GENERATED
"""Servicio sin interfaz grafica: imagen -> concepto -> memoria con procedencia."""
from .color_features import analizar_imagen
from .concept_alignment import registrar_observacion


def procesar_imagen(mem, datos: bytes, nombre: str = "imagen") -> dict:
    try:
        resultado = analizar_imagen(datos)
    except (ValueError, RuntimeError) as exc:
        return {"error": str(exc)}
    color = resultado.get("concepto")
    resultado["aprendido"] = []
    if not color:
        # Una observación no identificada sigue teniendo identidad perceptiva,
        # pero nunca se registra un color arbitrario en la memoria.
        import hashlib
        resultado['entidad']='IMAGEN_'+hashlib.sha256(datos).hexdigest()[:12].upper()
        from src.multimodal.events import desde_vision
        resultado['observacion']=desde_vision(resultado).serializar()
        resultado["respuesta"] = resultado["mensaje"]
        return resultado
    entidad, nuevo = registrar_observacion(mem, datos, color)
    mem.save()
    resultado["entidad"] = entidad
    resultado["aprendido"] = [{"s": entidad, "p": "TENER_COLOR", "o": color, "origen": "vision"}] if nuevo else []
    from src.multimodal.events import desde_vision
    resultado['observacion']=desde_vision(resultado).serializar()
    resultado["respuesta"] = f"He observado una imagen de color {color.lower()}. Lo vinculo con el concepto {color}."
    return resultado
