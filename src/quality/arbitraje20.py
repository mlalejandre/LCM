"""LCM 2.0: arbitraje entre capas de diálogo.

Cada capa (1.6-1.9) conoce solo una parte de la memoria. Que una capa no encuentre
la relación no prueba que no conste: otra capa (o el conversador de base) puede
tenerla. Una abstención se retiene y solo se emite si nadie aporta una respuesta.
"""
from __future__ import annotations

import re
import unicodedata


def _n(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', str(s or '').casefold()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s).strip()


_ABST = ('no consta una relacion de ese tipo', 'no consta informacion suficiente', 'no consta ese hecho',
         'no consta', 'solo constan negaciones', 'no tengo ese dato', 'no dispongo de ese dato',
         'no tengo informacion', 'no tengo constancia', 'no puedo evaluar esa pregunta')

_VACIA = ('no lo se', 'no conozco', 'no he entendido', 'no se ', 'creo que hablas', 'creo que preguntas',
          'eso no me consta', 'no tengo informacion', 'no dispongo de informacion', 'no entiendo')


def es_abstencion(respuesta) -> bool:
    return isinstance(respuesta, str) and _n(respuesta).startswith(_ABST)


def respuesta_vacia(respuesta) -> bool:
    return not isinstance(respuesta, str) or not respuesta.strip() or _n(respuesta).lstrip('¡¿ ').startswith(_VACIA)


_ECO = re.compile(r"Entendido: ((?:[A-ZÁÉÍÓÚÑ0-9_]+ ){1,3}[A-ZÁÉÍÓÚÑ0-9_]+)\.")


def limpia_eco(respuesta: str, aprendido=None) -> str:
    """«Entendido: ANA VIVIR_EN MADRID.» -> «Entendido: Ana vive en Madrid.» (el eco interno de la tripleta no es lenguaje natural)."""
    if not isinstance(respuesta, str) or "Entendido: " not in respuesta:
        return respuesta
    if aprendido and _ECO.search(respuesta):
        textos = [str(a.get("texto", "")).strip().rstrip(".") for a in aprendido if isinstance(a, dict) and a.get("texto")]
        textos = [t for t in dict.fromkeys(textos) if t and not re.search(r"\b[A-ZÁÉÍÓÚÑ_]{4,}\b", t)]
        if textos and len(_ECO.findall(respuesta)) >= 1:
            resto = _ECO.sub("", respuesta).strip()
            return ("Entendido: " + "; ".join(t[:1].lower() + t[1:] if not t.split()[0].istitle() else t for t in textos[:3]) + ". " + resto).strip()
    out = _ECO.sub("Entendido.", respuesta)
    out = re.sub(r"(?:Entendido\.\s*){2,}", "Entendido. ", out).strip()
    return out


def abstencion_util(respuesta) -> bool:
    """Abstención de las capas anteriores que aporta algo («No sé qué es un X. ¿Me lo explicas?») y no es ruido."""
    if not isinstance(respuesta, str):
        return False
    r = _n(respuesta)
    if "no he entendido" in r or "no conozco «tu»" in r or "prueba con otra forma" in r or "creo que preguntas" in r or "creo que hablas" in r:
        return False
    return r.startswith(("no se que es", "no se que significa", "no se quien es")) and "¿me lo explicas" in r
