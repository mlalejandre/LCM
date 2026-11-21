"""LCM 2.25 · Frases compuestas en la conversación.

Una persona no habla con frases sueltas: «Pelo las patatas y las corto en rodajas», «A Sara le gusta el cine y a Hugo el fútbol»,
«Pablo tiene treinta años y yo veinticinco». El núcleo entiende bien cada frase simple; aquí solo se parte la compuesta en simples,
reponiendo lo que la segunda mitad calla: el pronombre («las» = las patatas), el verbo («a Hugo [le gusta] el fútbol») o la unidad
(«yo [tengo] veinticinco [años]»). Es gramática de la lengua; no sabe nada del mundo.
"""
from __future__ import annotations

import os
import re

from . import morfo as M
from .morfo import sa

_ADV = r"(?:luego|después|despues|también|tambien|al final|por último|por ultimo|entonces|ya|además|ademas|más tarde|mas tarde|enseguida)"
_T = ("pres", "pret", "imp", "fut")
_DET = r"(?:el|la|los|las|un|una|unos|unas|mi|mis|tu|tus|su|sus|este|esta|estos|estas|ese|esa|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|varios|varias|muchos|muchas|\d+)"
_SIG = {"en", "con", "a", "al", "de", "del", "por", "para", "sobre", "hasta", "desde", "el", "la", "los", "las", "un", "una", "unos", "unas", "muy", "bien", "mal", "despues", "luego", "siempre",
        "cada", "mucho", "poco", "ahi", "alli", "aqui", "dentro", "fuera", "encima", "debajo", "todos", "todas", "sin", "entre", "hacia", "despacio", "rapido"}
_NO_V = {"para", "como", "sobre", "entre", "bajo", "una", "uno", "casa", "cara", "vino", "nada", "cerca", "tarde", "modo", "lado", "se", "sé", "me", "te", "le", "les", "lo", "la", "los", "las",
         "no", "nos", "os", "mi", "tu", "su", "si", "sí", "ya"}


def _fin(w):
    """Análisis de `w` como verbo conjugado: [(lema, tiempo, persona)]."""
    w = w.lower().strip(",.;:")
    if sa(w) in _NO_V or len(w) < 2:
        return []
    try:
        return [a for a in (M.analizar(w) or []) if len(a) > 2 and a[1] in _T]
    except Exception:                                    # noqa
        return []


def _part(w):
    try:
        return any(len(a) > 1 and a[1] == "part" for a in (M.analizar(w.lower()) or [])) or re.search(r"(?:ado|ido|to|so|cho)$", w.lower()) is not None
    except Exception:                                    # noqa
        return False


def _primer_verbo(ws):
    """Posición y análisis del primer verbo conjugado de la frase (saltando «he comprado»: cuenta el auxiliar)."""
    for i, w in enumerate(ws):
        if i > 0 and sa(ws[i - 1].lower()) in ("el", "la", "los", "las", "un", "una", "mi", "mis", "tu", "su", "sus", "del", "al", "de"):
            continue
        an = _fin(w)
        if an and i == 0 and len(ws) > 1 and any(a[2] in ("3s", "3p") for a in _fin(ws[1])) and all(a[2] in ("1s", "2s") for a in an):
            continue                                     # «Leo pesa…»: un nombre que se escribe como un verbo («leo»); el verbo es el siguiente
        if an:
            return i, an
    return -1, []


def _nombres(izq):
    """Los grupos «determinante + nombre» de la primera mitad: [(texto para repetir, género, número)]."""
    out = []
    for m in re.finditer(r"\b(" + _DET + r")\s+([a-záéíóúñü]+)", izq, re.I):
        det, nom = m.group(1).lower(), m.group(2).lower()
        if _fin(nom) and sa(det) in ("la", "los", "las", "lo") and m.start() > 0 and izq[:m.start()].rstrip().split()[-1:] and sa(izq[:m.start()].rstrip().split()[-1].lower()) in ("y", "que", "no"):
            continue
        pl = nom.endswith("s") and sa(det) not in ("el", "la", "un", "una", "mi", "tu", "su", "este", "esta", "ese", "esa")
        try:
            g = M.genero_sust(sa(M.singular(nom) if pl else nom))
        except Exception:                                # noqa
            g = None
        if sa(det) in ("la", "las", "una", "unas", "esta", "estas", "esa", "varias", "muchas"):
            g = "f"
        elif sa(det) in ("el", "los", "un", "unos", "este", "estos", "ese", "varios", "muchos"):
            g = "m"
        txt = m.group(0) if sa(det) in ("el", "la", "los", "las", "mi", "mis", "tu", "tus", "su", "sus", "este", "esta", "estos", "estas", "ese", "esa") \
            else ({("m", False): "el", ("f", False): "la", ("m", True): "los", ("f", True): "las"}[(g or "m", pl)] + " " + nom)
        out.append((txt, g or "m", "p" if pl else "s"))
    return out


def _clitica(izq, der):
    """«…y las corto en rodajas», «…y las he metido en el bolso»: el pronombre es un nombre de la primera mitad."""
    m = re.match(r"^(" + _ADV + r"\s+)?(lo|la|los|las)\s+(?:(he|has|ha|hemos|han|había|habia)\s+)?([a-záéíóúñü]+)\b(.*)$", der, re.I)
    if not m:
        return None
    adv, cl, aux, v, resto = m.group(1) or "", m.group(2).lower(), m.group(3), m.group(4), m.group(5)
    if aux:
        if not _part(v):
            return None
    else:
        an = _fin(v)
        if not an:
            return None
        sig = sa(resto.strip().split()[0].lower().strip(",")) if resto.strip() else ""
        if not all(a[2] in ("1s", "1p") for a in an) and (not sig or ":" in izq or re.search(r",\s+\S+(?:\s+\S+)?$", izq)):
            return None                                  # «…: la base, el eje y la tapa»: una lista de nombres, no un verbo con su pronombre
        if sig and sig not in _SIG and not sig.endswith(("mente",)) and not all(a[2] in ("1s", "1p") for a in an):
            return None                                  # «…y la cola corta»: artículo y nombre, no pronombre y verbo
    wi = izq.split()
    k, an_i = _primer_verbo(wi)
    if k < 0:
        return None                                      # la primera mitad no tiene verbo: «y» une nombres
    g, n = {"lo": ("m", "s"), "la": ("f", "s"), "los": ("m", "p"), "las": ("f", "p")}[cl]
    cands = [x for x in _nombres(" ".join(wi[k + 1:])) if x[1] == g and x[2] == n]
    if not cands:
        return None
    suj = ""
    tercera = (aux or "").lower() in ("ha", "han", "había", "habia") if aux else any(a[2] in ("3s", "3p") for a in _fin(v))
    if tercera and all(a[2] in ("3s", "3p") for a in an_i) and k > 0 and sa(wi[0].lower()) not in ("primero", "luego", "despues", "hoy", "ayer", "manana", "siempre", "nunca", "ya", "no", "se", "me", "te", "le",
                                                                                   "al", "por", "en", "a", "cuando", "si"):
        suj = " ".join(wi[:k]) + " "
        if sa(wi[k - 1].lower()) in ("se", "no", "me", "te", "le", "nos", "lo", "la", "los", "las"):
            suj = " ".join(wi[:k - 1]) + " " if k > 1 else ""
    return f"{adv}{suj}{(aux + ' ') if aux else ''}{v} {cands[-1][0]}{resto}".strip()


def _sin_verbo(s):
    ws = s.split()
    for i, w in enumerate(ws):
        if i > 0 and sa(ws[i - 1].lower()) in ("el", "la", "los", "las", "un", "una", "mi", "mis", "tu", "su", "sus", "del", "al", "de"):
            continue
        if _fin(w) and not (w[:1].isupper()):
            an = _fin(w)
            if not all(a[2] in ("1s",) for a in an) or i == 0 or sa(ws[i - 1].lower()) in ("yo", "no", "me", "lo", "la", "los", "las", "le", "les", "te", "se"):
                return False
    return True


def _solo_numero(s):
    from . import numerales as N
    try:
        c = N.a_cifras(s.strip())
    except Exception:                                    # noqa
        c = s
    return re.fullmatch(r"\s*\d+(?:[.,]\d+)?\s*", c or "") is not None


def _hueco(izq, der):
    """La segunda mitad calla el verbo: «a Hugo el fútbol», «yo veinticinco»."""
    if not _sin_verbo(der):
        return None
    m1 = re.match(r"^a\s+(.+?)\s+(le|les)\s+([a-záéíóúñü]+)\s+(.+)$", izq, re.I)
    m2 = re.match(r"^a\s+((?:mi\s+|mis\s+|el\s+|la\s+)?[A-Za-zÁÉÍÓÚÑáéíóúñü]+)\s+(.+)$", der)
    if m1 and m2 and sa(m2.group(2).strip().lower()) in ("no", "tampoco", "tambien", "si", "nada", "mucho", "poco"):
        return None                                      # «…pero a mí no»: eso lo entiende el núcleo
    if m1 and m2 and _fin(m1.group(3)) and sa(m1.group(3).lower()) not in ("ha", "han", "he"):
        return f"a {m2.group(1)} {m1.group(2)} {m1.group(3)} {m2.group(2)}"
    if m1 and m2:
        return None
    wi = izq.split()
    k, an = _primer_verbo(wi)
    if k <= 0 or k >= len(wi) - 1:
        return None
    m3 = re.match(r"^(yo|[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+|mi\s+[a-záéíóúñü]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+)?)\s+(.+)$", der)
    if not m3 or sa(wi[k - 1].lower()) in ("se", "me", "te", "le", "nos", "lo", "la", "los", "las", "no"):
        return None
    s2, o2 = m3.group(1), m3.group(2).strip()
    if len(o2.split()) > 5 or sa(o2.lower()) in ("no", "tampoco", "tambien", "si"):
        return None
    if k >= 2 and sa(wi[k - 1].lower()) == "se":
        return None                                      # «…se llama Pilar y mi suegro Antonio»: lo entiende el núcleo
    v = wi[k]
    if s2.lower() == "yo":
        v = M.conjugar(an[0][0], an[0][1], "1s") or v
    elif all(a[2] in ("1s", "1p") for a in an):
        v = M.conjugar(an[0][0], an[0][1], "3s") or v
    o1 = wi[k + 1:]
    if _solo_numero(o2):
        if not (len(o1) >= 2 and _solo_numero(" ".join(o1[:-1]))):
            return None
        o2 = o2 + " " + o1[-1]                           # «…treinta AÑOS y yo veinticinco [años]»
    elif not re.match(r"^(?:" + _DET + r"|en|con|de|a|al|por|para|\d)", sa(o2.lower())):
        return None
    return f"{s2[:1].upper() + s2[1:] if s2.lower() == 'yo' else s2} {v} {o2}"


def partes(texto):
    """La frase compuesta partida en simples, o None si no hay nada que partir (o no es seguro)."""
    if os.environ.get("LCM_SIN_COORDINA") or not texto or "?" in texto or "\n" in texto or len(texto) > 220:
        return None
    s = texto.strip().rstrip(".!").strip()
    if len(s.split()) < 4 or s.count(".") > 0:
        return None
    for m in re.finditer(r",?\s+(?:y|e|pero)\s+", s):
        izq, der = s[:m.start()].strip(), s[m.end():].strip()
        if len(izq.split()) < 2 or not der:
            continue
        r = _clitica(izq, der) or _hueco(izq, der)
        if r:
            cola = partes(r) if " y " in r else None     # «…, las frío y las escurro»
            return [izq + "."] + (cola or [r[:1].upper() + r[1:] + "."])
    return None
