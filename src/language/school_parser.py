"""La escuela dentro de la conversacion (parche-32/34): frase libre -> proposiciones, sin plantillas."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence

from .extract import surface, triples_full
from .irregulares import IRREG
from .lexicon import norm as _norm
from .ud import School, predict_trees


class SchoolParser:
    def __init__(self, model: School, device="cpu", scripts: Sequence = (), overrides: Optional[Dict[str, str]] = None):
        self.model, self.device, self.scripts = model.to(device).eval(), device, list(scripts)
        self.overrides = {**IRREG, **(overrides or {})}      # forma -> lema, ensenados con ENTENDI (verbos irregulares)

    @staticmethod
    def _forms(sentence: str):
        text = re.sub(r"\bdel\b", "de el", sentence, flags=re.I)
        text = re.sub(r"\bal\b", "a el", text, flags=re.I)
        forms = re.findall(r"\w+|[^\w\s]", text)
        if forms and forms[-1] not in ".!?;:":
            forms.append(".")                      # el entrenamiento siempre veia la frase cerrada con signo de puntuacion
        return forms

    def tree(self, sentence: str):
        """[(forma, upos, head, deprel, lema)] por palabra."""
        forms = self._forms(sentence)[:40]
        pred = predict_trees(self.model, [forms], self.device, self.scripts)[0]
        rows = [(f, u, h, r, l) for f, (u, h, r, l) in zip(forms, pred)]
        rows = self._fix_name_verb(rows)
        return [(f, u, h, r, (self.overrides.get(f.lower()) or self.overrides.get(_norm(f)) or l) if u == "VERB" else l) for f, u, h, r, l in rows]

    @staticmethod
    def _fix_name_verb(rows):
        """"Ana duerme." / "Andres cocina pasta.": la escuela lee nombre + palabra en minuscula como un nombre compuesto (flat).
        Un nombre propio no sigue en minusculas: esa palabra es el verbo (parche-55)."""
        rows = [list(x) for x in rows]
        for k in range(1, len(rows)):                      # "mas baja que Clara": un nombre tras "que" no es sujeto, es el termino comparado
            if rows[k][3] == "csubj" and rows[k - 1][3] == "mark" and rows[k - 1][0].lower() == "que":
                rows[k][3] = "nmod"
        for k, (f, u, h, r, l) in enumerate(rows):
            # "Sara vino.": "vino" (verbo) leido como NOUN raiz con sujeto nombre propio y sin determinante
            if (r == "root" and u in ("NOUN", "ADJ", "ADV") and _norm(f) in IRREG and
                    any(x[3] == "nsubj" and x[2] == k + 1 and x[1] in ("PROPN", "NOUN") for x in rows) and
                    not any(x[3] == "det" and x[2] == k + 1 for x in rows)):
                rows[k][1] = "VERB"
                continue
            if r != "flat" or not f[:1].islower() or h < 1 or h - 1 >= k or u == "PUNCT":
                continue
            name = h - 1
            if not rows[name][0][:1].isupper() or rows[name][3] not in ("root", "nsubj"):
                continue
            name_head, name_rel = rows[name][2], rows[name][3]
            if name_rel == "nsubj" and name_head != k + 1 and name_head != 0:
                continue                                    # el nombre es sujeto de OTRO verbo: no tocar
            rows[k][1], rows[k][2], rows[k][3] = "VERB", 0, "root"
            rows[name][2], rows[name][3] = k + 1, "nsubj"
            first_obj = True
            for j in range(k + 1, len(rows)):
                if rows[j][2] == name + 1 or (rows[j][3] == "flat" and rows[j][2] == k + 1):
                    if rows[j][3] == "flat" and rows[j][1] in ("NOUN", "ADJ", "PROPN") and first_obj:
                        rows[j][1] = "NOUN" if rows[j][1] == "ADJ" else rows[j][1]
                        rows[j][2], rows[j][3] = k + 1, "obj"
                        first_obj = False
                    elif rows[j][3] != "flat":
                        rows[j][2] = k + 1
                    else:
                        rows[j][2] = k + 1
            break
        return [tuple(x) for x in rows]

    def parse(self, sentence: str, topic: Optional[str] = None) -> Optional[List[Dict]]:
        """None si no es una afirmacion analizable (pregunta, demasiado corta o larga); si no, lista de proposiciones."""
        if "?" in sentence or "¿" in sentence:
            return None
        from datetime import date
        from src.language.fechas import extract_abs
        sentence, abs_iv, abs_disp = extract_abs(sentence, getattr(self, "today", None) or date.today())
        forms = self._forms(sentence)
        if not 3 <= len(forms) <= 40:         # 3 = "Envia paquetes ." (sujeto omitido)
            return None
        tree = self.tree(sentence)
        found = triples_full(tree, entities_only=True, default_subject=topic)
        if not found and topic and sentence[:1].isupper():
            # "Bebe agua.": con mayuscula inicial la escuela puede leer el verbo como nombre; se reintenta en minuscula
            tree2 = self.tree(sentence[:1].lower() + sentence[1:])
            alt = triples_full(tree2, entities_only=True, default_subject=topic)
            if alt:
                tree, found = tree2, alt
        for t in found:
            t.update(surface(tree, t))
            if abs_iv and not t.get("when"):
                t["when"], t["when_disp"] = "abs:" + abs_iv, abs_disp
        return found
