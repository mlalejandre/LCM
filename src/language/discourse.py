"""Discurso (parche-44, Fase 2): varias frases seguidas. El sujeto de la frase anterior (el "tema") sustituye a "el/ella" y es el
sujeto de un verbo sin sujeto escrito ("Ana vive en Madrid. Trabaja en un banco." -> ana trabajar_en banco). Sin LLM."""
import re
from typing import Dict, List, Optional

from .extract import PRON_SUBJ


def split_sentences(text: str) -> List[str]:
    return [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]


def next_topic(found: List[Dict], topic: Optional[str]) -> Optional[str]:
    """Tema tras una frase: el sujeto de su primera proposicion (si no es un pronombre)."""
    for t in found:
        if t["s"] not in PRON_SUBJ:
            return t["s"]
    return topic


def parse_text(parser, text: str, topic: Optional[str] = None) -> List[Dict]:
    out: List[Dict] = []
    for sent in split_sentences(text):
        found = parser.parse(sent, topic=topic) or []
        topic = next_topic(found, topic)
        out += found
    return out
