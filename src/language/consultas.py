"""Normalizador de PREGUNTAS (parche-90). Muchas formas de preguntar lo mismo se reducen a una forma canonica que el pipeline ya sabe contestar:
"Dime que compra Ana" / "¿Sabes donde vive Pedro?" / "¿Que es lo que compra Ana?" / "¿En que ciudad vive X?" / "¿De que trabaja X?" /
"¿Quien es el papa de X?" / "¿Cual es mi nombre?" / "5 x 6". Es reescritura determinista de la frase (no toca afirmaciones). Lo que se aprende aqui sirve
para todas las preguntas de la misma familia, con cualquier nombre."""
import re
from typing import Optional, Tuple

_V = {"a": "[aá]", "e": "[eé]", "i": "[ií]", "o": "[oó]", "u": "[uú]"}


def _a(s: str) -> str:
    return "".join(_V.get(c, c) for c in s)


_INT = r"(qu[eé]|qui[eé]nes|qui[eé]n|d[oó]nde|cu[aá]ndo|c[oó]mo|cu[aá]l(?:es)?|cu[aá]nt[oa]s?|por qu[eé]|en qu[eé]|a qu[eé]|de qu[eé]|con qu[eé]|para qu[eé])"
_PRE = re.compile(r"^(?:oye[, ]+)?(?:sabes|sabr[ií]as|me puedes decir|puedes decirme|podr[ií]as decirme|me dices|dime|dec[ií]me|por favor dime)\s+" + _INT + r"\b(.*)$", re.I)
_LOQUE = re.compile(r"^qu[eé] es (?:lo|el|la) que (.+)$", re.I)
_CIUDAD = re.compile(r"^(?:en )?qu[eé] (?:ciudad|pa[ií]s|lugar|sitio|pueblo|barrio|provincia|regi[oó]n|localidad) (vive|viv[ií]a|est[aá]|trabaja|estudia|naci[oó]|nace|duerme|reside) (.+)$", re.I)
_PROF = re.compile(r"^(?:a qu[eé] se dedica|de qu[eé] trabaja|en qu[eé] trabaja|cu[aá]l es la profesi[oó]n de|cu[aá]l es el trabajo de|qu[eé] profesi[oó]n tiene|qu[eé] hace de profesi[oó]n) (.+)$", re.I)
_PAPA = re.compile(r"^(qui[eé]n es (?:el|la)) (pap[aá]|mam[aá]) (de .+)$", re.I)
_NOMBRE = re.compile(r"^(?:cu[aá]l es mi nombre|c[oó]mo es mi nombre|qu[eé] nombre tengo|c[oó]mo se llama este usuario)$", re.I)
_ARIT = re.compile(r"^(\d+(?:[.,]\d+)?)\s*([x×*+\-−/÷:])\s*(\d+(?:[.,]\d+)?)\s*[=?]*$")
_QMAS = re.compile(r"^qui[eé]n es (m[aá]s|menos) (\w+)\s*,?\s+(?:(?:el|la) )?(\w+) o (?:(?:el|la) )?(\w+)$", re.I)
_OPW = {"x": "por", "×": "por", "*": "por", "+": "más", "-": "menos", "−": "menos", "/": "entre", "÷": "entre", ":": "entre"}


def _strip(raw: str) -> str:
    return raw.strip().lstrip("¿¡").rstrip("?!. ").strip()


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def canonical(raw: str) -> str:
    """Devuelve la forma canonica de una pregunta, o `raw` sin tocar si no reconoce ninguna familia."""
    if not raw or len(raw) > 160:
        return raw
    body = _strip(raw)
    asked = raw.strip().endswith("?") or raw.strip().startswith("¿")
    m = _ARIT.match(body)
    if m and (m.group(2) not in "-:" or re.search(r"\s" + re.escape(m.group(2)) + r"\s", body)):
        return f"¿Cuánto es {m.group(1)} {_OPW[m.group(2)]} {m.group(3)}?"
    m = _PRE.match(body)
    if m:
        word = m.group(1)
        accented = any(c in word.lower() for c in "áéíóú")
        if accented or asked:
            return "¿" + _cap(word) + m.group(2).rstrip() + "?"
    m = _LOQUE.match(body)
    if m:
        return f"¿Qué {m.group(1)}?"
    m = _CIUDAD.match(body)
    if m:
        return f"¿Dónde {m.group(1)} {m.group(2)}?"
    m = _PROF.match(body)
    if m:
        return f"¿Qué es {m.group(1)}?"
    m = _PAPA.match(body)
    if m:
        return f"¿{_cap(m.group(1))} {'padre' if m.group(2).lower().startswith('pap') else 'madre'} {m.group(3)}?"
    if _NOMBRE.match(body):
        return "¿Cómo me llamo?"
    return raw


def quien_mas(raw: str) -> Optional[Tuple[str, str, str, str]]:
    """"¿Quien es mas alta, Ana o Luisa?" -> ("más", "alta", "Ana", "Luisa")."""
    m = _QMAS.match(_strip(raw))
    if not m:
        return None
    return m.group(1).lower().replace("mas", "más"), m.group(2), m.group(3), m.group(4)
