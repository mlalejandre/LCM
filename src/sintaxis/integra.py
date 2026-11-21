"""INTEGRACIÓN con el LCM. Dos enganches, los dos después de que el núcleo haya hecho lo suyo:

  · al LEER un texto (varias frases de una vez): el texto se guarda y de él se saca la memoria de relaciones con el analizador entrenado;
  · al PREGUNTAR: manda el LCM. La memoria de relaciones solo entra cuando el LCM no sabe o se limita a copiar una frase del texto:
    entonces da la pieza exacta si la tiene con seguridad; y si la frase copiada no habla de lo que se pregunta, se dice «no lo sé».
    (Medido: poner la memoria por delante bajaba los bancos de lectura del propio LCM; así no baja ninguno.)

Solo actúa si el analizador está entrenado (existe src/sintaxis/analizador.pt) y no se ha apagado con LCM_SIN_SINTAXIS=1."""
from __future__ import annotations

import os
import re

MAX_TEXTO = 80000
_ABS = r"no lo s[eé]|no s[eé] qui[eé]n|no me has|no lo he le[ií]do|no aparece|no me consta|no tengo|no he entendido"


def activo():
    if os.environ.get("LCM_SIN_SINTAXIS"):
        return False
    from .analiza import RUTA
    return os.path.exists(RUTA)


def _memoria(nuc):
    ts = nuc.usuario.get("sintaxis_textos") or []
    if not ts:
        return None
    m = getattr(nuc, "_sint_mem", None)
    if m is None or m[0] != len(ts):
        from .relaciones import Memoria
        M = Memoria()
        for t in ts:
            M.lee(t, limpiar=False)
        m = nuc._sint_mem = (len(ts), M)
    return m[1]


def es_texto(texto):
    """¿Es un texto para leer (no una frase de conversación)? Varias frases o varias líneas, y sin ser una pregunta."""
    t = texto.strip()
    return "?" not in t[-2:] and (t.count("\n") >= 1 or len(re.findall(r"[.!]\s+[A-ZÁÉÍÓÚÑ¿¡]", t)) >= 2) and len(t.split()) >= 15


def lee(nuc, texto):
    """Guarda el texto (limpio) para la memoria de relaciones."""
    if not activo() or not es_texto(texto):
        return False
    from .relaciones import limpia
    t = limpia(texto)
    ts = nuc.usuario.setdefault("sintaxis_textos", [])
    if t in ts:
        return False
    ts.append(t)
    while sum(len(x) for x in ts) > MAX_TEXTO and len(ts) > 1:
        ts.pop(0)
    nuc._sint_mem = None
    return True


def responde(nuc, pregunta, r):
    """Devuelve la respuesta definitiva (dict) o None para dejar la del LCM."""
    if not activo() or not pregunta or len(pregunta) > 300:
        return None
    q = pregunta.strip()
    if "?" not in q and not re.match(r"^(?:qu[eé]|qui[eé]n(?:es)?|cu[aá]l(?:es)?|d[oó]nde|cu[aá]ndo|cu[aá]nt[oa]s?|c[oó]mo|de qu[eé]|por qu[eé]|con qu[eé]|a d[oó]nde)\b", q, re.I):
        return None
    M = _memoria(nuc)
    if M is None:
        return None
    a = (r or {}).get("respuesta") or ""
    try:
        m = re.match(r"^¿?\s*qu[eé] (?:me )?(?:puedes decir|sabes|me cuentas) (?:de|del|sobre|acerca de)(?: el| la| los| las)? (.+?)\??$", q, re.I)
        if m:
            fs = M.sobre(m.group(1))
            if fs and (re.search(_ABS, a.lower()) or "En el texto pone" in a or not a):
                return dict(r or {}, respuesta="En el texto pone: «" + "» «".join(fs[:3]) + "»", estado="ok", origen="sintaxis")
            return None
        x = M.pregunta(q)
    except Exception:                                    # noqa
        return None
    flojo = (not a) or bool(re.search(_ABS, a.lower())) or "En el texto pone" in a or "tal como lo dices" in a
    if not flojo:
        return None                                      # el LCM ha contestado por sí mismo (lo sabe, lo deduce o lo tiene en sus conceptos): manda él
    cita_ = "En el texto pone" in a or "tal como lo dices" in a
    if cita_ and os.environ.get("LCM_SINT_NO_CITAS"):
        return None
    if (not cita_) and os.environ.get("LCM_SINT_NO_ABST"):
        return None
    if x is not None and x.get("seguro", 0) >= float(os.environ.get("LCM_SINT_SEGURO", SEGURO)):
        return dict(r or {}, respuesta=x["respuesta"], estado="ok", origen="sintaxis", fuente_texto=x["fuente"], seguridad=x["seguro"])
    if "En el texto pone" in a and os.environ.get("LCM_SINT_VERIFICA_CITA"):   # opcional (medido: en los bancos del LCM quitaba más citas buenas que malas)   # la cita del LCM tiene que hablar de lo que se pregunta
        from .analiza import palabras
        from .relaciones import _lema
        cita = a.split("«", 1)[-1]
        en_cita = {_lema(w) for w in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", cita)}
        pide = {_lema(p["forma"]) for p in palabras(q) if p["cat"] in ("NOUN", "PROPN")}
        if pide and not pide <= en_cita:
            return dict(r or {}, respuesta="No lo sé: eso no lo he leído.", estado="abst", origen="sintaxis")
    return None


SEGURO = 0.50
