"""Coherencia de la memoria (parche-57, bloque D): cambio de estado y contradicciones.
- Relaciones que solo valen para UN valor a la vez (vivir en, trabajar en, estar en, estar + estado): un hecho nuevo
  sustituye al viejo, que pasa a PASADO (no se borra: "¿donde vivia Ana?").
- Contradicciones que no se pueden resolver solas (dos adjetivos opuestos con "ser", afirmar y negar lo mismo): se pregunta.
"""
import re
from typing import List, Optional, Tuple

from src.language.lexicon import norm

ANTONYMS = [("grande", "pequeno"), ("alto", "bajo"), ("feliz", "triste"), ("contento", "triste"), ("rapido", "lento"), ("caliente", "frio"),
            ("nuevo", "viejo"), ("limpio", "sucio"), ("lleno", "vacio"), ("fuerte", "debil"), ("bueno", "malo"), ("joven", "viejo"),
            ("rico", "pobre"), ("abierto", "cerrado"), ("vivo", "muerto"), ("enfermo", "sano"), ("claro", "oscuro"), ("largo", "corto"),
            ("gordo", "delgado"), ("ancho", "estrecho"), ("duro", "blando"), ("facil", "dificil"), ("seco", "mojado"), ("cerca", "lejos")]
FUNCTIONAL = ("VIVIR_EN", "TRABAJAR_EN", "ESTAR_EN", "ESTUDIAR_EN", "ESTAR")
_STEM = re.compile(r"(os|as|es|o|a|e|s)$")


def stem(word: str) -> str:
    return _STEM.sub("", norm(word))


def opposite(a: str, b: str, extra=()) -> bool:
    sa, sb = stem(a), stem(b)
    return any({stem(x), stem(y)} == {sa, sb} for x, y in list(ANTONYMS) + [tuple(e) for e in extra])


def classify(facts: List[dict], triple: Tuple[str, str, str], neg: bool, has_time: bool = False,
             ya_no: bool = False, extra=()) -> Tuple[str, Optional[dict]]:
    """-> (tipo, hecho_viejo): 'supersede' | 'negation' | 'antonym' | ('', None)."""
    s, p, o = (x.upper() for x in triple)
    for f in facts:
        same = (f["s"], f["p"], f["o"]) == (s, p, o)
        if same and bool(f.get("neg")) != neg:
            if neg and ya_no and p in FUNCTIONAL:
                return "supersede_neg", f                     # "Pedro ya no trabaja en X": el viejo pasa a pasado
            return "negation", f
    if neg or has_time:
        return "", None
    for f in facts:
        if f["s"] != s or f.get("neg") or f.get("when") or (f["p"], f["o"]) == (p, o):
            continue
        if p in FUNCTIONAL and f["p"] == p and f["o"] != o:
            return "supersede", f
        if p in ("SER", "ESTAR") and f["p"] in ("SER", "ESTAR") and opposite(f["o"], o, extra):
            return ("supersede" if p == "ESTAR" and f["p"] == "ESTAR" else "antonym"), f
    return "", None


def to_past(mem, old: dict, until_iso: str) -> None:
    """Quita el hecho de los vigentes y lo guarda como pasado."""
    mem.facts = [f for f in mem.facts if f is not old]
    old = dict(old)
    old["until"] = until_iso
    if not hasattr(mem, "past"):
        mem.past = []
    mem.past.append(old)
