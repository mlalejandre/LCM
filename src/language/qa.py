"""Preguntas y respuestas en espanol (parche-35, Fase 1). Sin LLM.

Una pregunta se reescribe como afirmacion con un hueco ("Xqx") y se lee con la MISMA escuela que lee las afirmaciones:
  "Quien escribio una novela?"   -> "Xqx escribio una novela."    (hueco = sujeto)
  "Que escribio Marta?"          -> "Marta escribio Xqx."         (hueco = objeto)
  "Vive Pedro en Madrid?"        -> "Pedro vive en Madrid."       (si/no)
Luego se busca en la memoria (con la misma tolerancia de relacion que el test de conversacion) y, si no esta, se intenta
DEDUCIR con las lecciones aprendidas. Se contesta con las palabras que uso la persona (plantillas y nombres guardados).
Cuando no se sabe, se dice "no lo se" (mundo abierto): no se inventa.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .lexicon import norm

MODAL_VERBS = {"puede", "pueden", "debe", "deben", "quiere", "quieren", "podia", "queria", "pudo", "debia"}
HOLE = "Xqx"
HOLES = ("Xqx", "Zurita", "Bertoldo")      # parche-41: si la escuela no lee uno, se prueba otro nombre inventado
DETS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus", "mi", "mis", "tu", "tus"}
WH = {"quien", "quienes", "que", "cual", "cuales"}
ADV = {"donde": "en", "como": "con"}


def template_from(raw: str, s: str, o: str):
    """Plantilla "{s} es hijo de {o}" sacada de la frase tal como la dijo la persona (para frases que entiende el oido de plantillas
    o las dos mitades de una regla). Devuelve (plantilla, como_se_escribia_s, como_se_escribia_o) o None."""
    words = re.findall(r"\w+|[^\w\s]", raw)
    low = [norm(w) for w in words]
    si = [i for i, w in enumerate(low) if w == norm(s)]
    oi = [i for i, w in enumerate(low) if w == norm(o)]
    if not si or not oi or si[0] == oi[0]:
        return None
    toks = []
    for i, w in enumerate(words):
        if not re.match(r"\w", w):
            continue
        toks.append("{s}" if i == si[0] else "{o}" if i == oi[0] else (w.lower() if i == 0 else w))
    text = " ".join(toks).replace(" de el ", " del ").replace(" a el ", " al ")
    return text, words[si[0]], words[oi[0]]


def is_question(text: str) -> bool:
    t = text.strip()
    return t.startswith("¿") or t.endswith("?")


def pred_key(p: str) -> str:
    head, _, prep = norm(p).partition("_")
    head = {"tia": "tio"}.get(head, head)                       # tio/tia, hijo/hija... (parche-59)
    return head[:3] + "|" + ("" if prep == "a" else prep)      # la "a" personal (conocer a Pablo) no distingue la relacion


def same_pred(a: str, b: str) -> bool:
    if pred_key(a) != pred_key(b):
        return False
    ha, hb = a.lower().partition("_")[0], b.lower().partition("_")[0]
    if ha != hb and ha[-2:] in ("ar", "er", "ir") and hb[-2:] in ("ar", "er", "ir") and ha[-2:] != hb[-2:]:
        return False                                  # venir / vender: mismas 3 letras, verbos distintos
    return True


def _words(text: str) -> List[str]:
    return re.findall(r"\w+", text.replace("¿", " ").replace("?", " "), flags=re.U)


def rewrite(question: str, hole: str = HOLE) -> Tuple[List[str], str]:
    cands, kind = _rewrite(question, hole)
    caps = [c[:1].upper() + c[1:] for c in cands if c[:1].islower()]
    return cands + [c for c in caps if c not in cands], kind


def _rewrite(question: str, hole: str = HOLE) -> Tuple[List[str], str]:
    """Devuelve (candidatos de afirmacion, tipo). tipo: 'sujeto' | 'objeto' | 'si_no'. Lista vacia si no se sabe."""
    w = _words(question)
    if not w:
        return [], ""
    low = [norm(x) for x in w]
    prep = ""
    i = 0
    if low[0] in ("a", "de", "con", "en", "para", "por") and len(low) > 1 and low[1] in WH:
        prep, i = w[0].lower(), 1
    if low[0] == "cuando" and len(w) >= 3:                       # "Cuando compro Pedro pan?" -> frase sin el "cuando"
        rest = w[1:]
        cands = [" ".join(rest) + "."]
        if len(rest) >= 3 and norm(rest[1]) in DETS:
            cands.append(" ".join([rest[1], rest[2], rest[0].lower()] + rest[3:]) + ".")
        cands.append(" ".join([rest[1], rest[0].lower()] + rest[2:]) + ".")
        return cands, "cuando"
    if low[i] in ADV and prep == "":
        prep, hole_at = ADV[low[i]], i
        rest = w[i + 1:]
        if len(rest) < 2:
            return [], ""
        # "Donde estudia Luis musica?" -> "Luis estudia musica en Xqx" (el verbo detras del sujeto, el hueco al final)
        c0 = []
        k_ = len(rest)
        while k_ > 1 and (rest[k_ - 1][:1].isupper() or (norm(rest[k_ - 1]) in ("y", "e") and k_ - 2 >= 1 and rest[k_ - 2][:1].isupper())):
            k_ -= 1                                   # parche-81: "Donde tienen una casa Andrea y Bruno?" -> sujeto coordinado al final
        if k_ < len(rest) and k_ > 2 and rest[k_][:1].isupper():
            c0 = [" ".join(rest[k_:] + [rest[0]] + rest[1:k_] + [prep, hole]) + "."]
        if len(rest) >= 3 and norm(rest[1]) in DETS and not c0:       # parche-83: "Donde juegan los ninos?" -> "los ninos juegan en Xqx"
            c0 = [" ".join([rest[1], rest[2], rest[0]] + rest[3:] + [prep, hole]) + "."]
        return c0 + [" ".join([rest[1], rest[0]] + rest[2:] + [prep, hole]) + "."], "objeto"
    if low[i] in WH:
        rest = w[i + 1:]
        if not rest:
            return [], ""
        pre = [prep] if prep else []
        if i == 0 and low[0] in ("quien", "quienes") and low[1:2] == ["es"] and len(rest) == 2 and rest[1][:1].isupper():
            return [" ".join(rest[1:] + [rest[0], hole]) + "."], "objeto"           # "Quien es Marta?" -> definicion de Marta
        if i == 0 and not prep:
            # "Quien escribio X?" -> hueco sujeto ; "Que escribio Marta?" -> hueco objeto
            cands = []
            if low[0] in ("quien", "quienes"):
                cands.append(" ".join([hole] + rest) + ".")
            if len(rest) >= 3 and norm(rest[0]) in MODAL_VERBS and norm(rest[1])[-2:] in ("ar", "er", "ir") and low[0] not in ("quien", "quienes"):
                cands.append(" ".join([rest[2], rest[0], rest[1], hole] + rest[3:]) + ".")      # "Que quiere comer Ana?"
            if len(rest) >= 2:
                cands.append(" ".join(rest[1:] + [rest[0], hole]) + ".")
            return cands, "sujeto" if low[0] in ("quien", "quienes") else "objeto"
        if len(rest) >= 3 and rest[1][:1].isupper():           # parche-81: "A quien regalo Ruben un libro?" -> "Ruben regalo un libro a Xqx"
            return [" ".join([rest[1], rest[0]] + rest[2:] + pre + [hole]) + ".", " ".join(rest[1:] + [rest[0]] + pre + [hole]) + "."], "objeto"
        if len(rest) >= 2:                                     # "A quien llamo Pedro?" -> "Pedro llamo a Xqx"
            return [" ".join(rest[1:] + [rest[0]] + pre + [hole]) + "."], "objeto"
        return [], ""
    # si / no: la frase tal cual, y la version con el verbo detras del sujeto ("Vive Pedro en Madrid")
    cands = [" ".join(w) + "."]
    if len(w) >= 3 and norm(w[1]) in DETS:                      # "Ensena la maestra matematicas" -> "la maestra ensena matematicas"
        cands.append(" ".join([w[1], w[2], w[0].lower()] + w[3:]) + ".")
    if len(w) >= 2:
        cands.append(" ".join([w[1], w[0].lower()] + w[2:]) + ".")
    if len(w) >= 3 and norm(w[0]) in ("es", "esta", "son", "estan", "era", "estaba"):                  # "Esta triste Ana" -> "Ana esta triste"
        cands.append(" ".join([w[2], w[0].lower(), w[1]] + w[3:]) + ".")
    if len(w) >= 3 and norm(w[0]) in MODAL_VERBS and norm(w[1])[-2:] in ("ar", "er", "ir"):       # "Debe estudiar Luis matematicas"
        cands.append(" ".join([w[2], w[0].lower(), w[1]] + w[3:]) + ".")
    return cands, "si_no"


from src.reasoning.lessons import canon


class QA:
    """memory: MemoryStore (con .facts, .surface, .display). parse: frase -> lista de dicts {s,p,o,neg} o None.
    deduce: opcional, (lista de hechos (s,p,o) sin negar) -> conjunto de (s,p,o) deducidos."""

    def __init__(self, memory, parse: Callable[[str], Optional[List[Dict]]],
                 deduce: Optional[Callable[[Sequence[Tuple[str, str, str]]], set]] = None):
        self.m, self.parse, self.deduce = memory, parse, deduce
        self._tpl = None
        self._alts = []
        self.support = {}

    # ---- lectura de la pregunta ------------------------------------
    def read(self, question: str):
        kind = ""
        for hole in HOLES:
            cands, kind = rewrite(question, hole)
            alts = []
            for c in cands:
                found = self.parse(c)
                if not found:
                    continue
                for t in found:
                    if kind in ("si_no", "cuando"):
                        alts.append(t)
                        if len(alts) == 1:
                            self._alts = alts            # todas las lecturas posibles; answer() prefiere la que encaja con la memoria
                        continue
                    if hole.lower() in (t["s"], t["o"]):
                        t = dict(t)
                        for k in ("s", "o"):
                            if t[k] == hole.lower():
                                t[k] = norm(HOLE)           # el resto del codigo usa un unico nombre de hueco
                        return ("sujeto" if t["s"] == norm(HOLE) else "objeto"), t
            if kind in ("si_no", "cuando"):
                if alts:
                    for a_ in alts:                          # "Un cuadrado es una figura": dos sustantivos, no adjetivo (parche-59)
                        if kind == "si_no" and a_["p"] == "ser" and all((a_.get(k) or "").lower().startswith(("un ", "una ", "el ", "la ", "los ", "las ")) for k in ("s_disp", "o_disp")):
                            a_["p"] = "es"
                    a0 = alts[0]
                    ind = lambda d: (d or "").lower().startswith(("un ", "una "))
                    if kind == "si_no" and a0["p"] in ("es", "ser") and ind(a0.get("s_disp")) and ind(a0.get("o_disp")) \
                            and a0.get("template", "").startswith("es {o} {s}"):
                        sw = dict(a0)                       # "¿Es un A un B?": A es el sujeto (parche-58)
                        sw["s"], sw["o"], sw["s_disp"], sw["o_disp"] = a0["o"], a0["s"], a0["o_disp"], a0["s_disp"]
                        sw["template"] = "{s} es {o}"
                        self._alts = [sw]                    # parche-77: solo la lectura "A es el sujeto" (antes tambien la invertida)
                        return kind, sw
                    return kind, a0
                break
        return kind, None

    # ---- memoria ----------------------------------------------------
    def _facts(self, neg=False):
        return [(f["s"], f["p"], f["o"]) for f in self.m.facts if bool(f.get("neg", False)) == neg]

    def _whens(self, fact):
        """[(clave, como se dijo)] de las veces que se guardo ese hecho (no negado)."""
        return [(f.get("when", ""), f.get("when_disp", "")) for f in self.m.facts
                if (f["s"], f["p"], f["o"]) == tuple(fact) and not f.get("neg")]

    def _today(self):
        from datetime import date
        return getattr(self.m, "today", None) or date.today()

    def _when_ok(self, fact, when):
        """El hecho se dijo con ese tiempo: misma clave, o fechas absolutas que se contienen ("ayer" = "el 5 de noviembre")."""
        from src.language.fechas import resolve, contains
        want = resolve(when, self._today())
        for f in self.m.facts:
            if (f["s"], f["p"], f["o"]) != tuple(fact) or f.get("neg"):
                continue
            if f.get("when", "") == when:
                return True
            if want and f.get("when_abs") and contains(f["when_abs"], want):
                return True
        return False

    def _q(self, fact):
        return next((f.get("q") for f in self.m.facts if (f["s"], f["p"], f["o"]) == tuple(fact) and not f.get("neg")), "")

    def _abs_of(self, fact):
        for f in self.m.facts:
            if (f["s"], f["p"], f["o"]) == tuple(fact) and not f.get("neg") and f.get("when_abs"):
                return f["when_abs"], f.get("when", "")
        return None, ""

    # ---- estados, acciones y lo que dicen otros (parche-55) --------------
    def _special_texto(self, t, question, facts, says):
        """parche-93: familias de preguntas que salen al leer textos. Devuelve None si la frase no es de estas familias."""
        import re

        def stem(w):
            return re.sub(r"(os|as|es|o|a|e)$", "", w)

        COMPL = r"((?:a|al|a la|del|de|de la|de los|de las|en|en el|en la) .+)"
        # a) superlativos y ordinales: "¿Cual es el planeta mas cercano al Sol?" / "¿Que planeta es el mas grande?" / "¿Cual es el tercer planeta?"
        ORD = {"primer": "primero", "primero": "primero", "primera": "primero", "segundo": "segundo", "segunda": "segundo", "tercer": "tercero", "tercero": "tercero",
               "tercera": "tercero", "cuarto": "cuarto", "cuarta": "cuarto", "quinto": "quinto", "quinta": "quinto", "sexto": "sexto", "sexta": "sexto",
               "septimo": "septimo", "septima": "septimo", "octavo": "octavo", "octava": "octavo", "noveno": "noveno", "novena": "noveno",
               "decimo": "decimo", "decima": "decimo", "ultimo": "ultimo", "ultima": "ultimo"}
        want = None
        t_sup = re.sub(r" que (?:conoces|sabes|tienes|hay)$", "", t)         # parche-95: "el planeta mas grande que conoces"
        m = re.fullmatch(r"(?:cual|que|quien) (?:es|era|fue) (?:(?:el|la) )?(?:(\w+) )?(mas|menos) (\w+)(?: " + COMPL + ")?", t_sup)
        if m:
            want = ("sup", m.group(2), m.group(3), m.group(1), m.group(4))
        if not want:
            m = re.fullmatch(r"que (\w+) (?:es|era|fue) (?:el|la) (mas|menos) (\w+)(?: " + COMPL + ")?", t_sup)
            if m:
                want = ("sup", m.group(2), m.group(3), m.group(1), m.group(4))
        if not want:
            m = re.fullmatch(r"(?:cual|que|quien) (?:es|era|fue) (?:el|la) (\w+) (\w+)(?: " + COMPL + ")?", t)
            if m and m.group(1) in ORD:
                want = ("ord", ORD[m.group(1)], None, m.group(2), m.group(3))
        if not want:
            m = re.fullmatch(r"que (\w+) (?:es|era|fue) (?:el|la) (\w+)(?: " + COMPL + ")?", t)
            if m and m.group(2) in ORD:
                want = ("ord", ORD[m.group(2)], None, m.group(1), m.group(3))
        if want:
            kind, a, adj, noun, comp = want
            key = ("ser_el_" + a + "_" + adj) if kind == "sup" else ("ser_el_" + a)
            ck = "_".join(comp.split()) if comp else ""
            hit = []
            for f in facts:
                fp = f["p"].lower()
                if f.get("neg") or not fp.startswith("ser_el_"):
                    continue
                if kind == "sup":
                    if not (fp.startswith("ser_el_" + a + "_") and stem(fp[len("ser_el_" + a + "_"):]) == stem(adj)):
                        continue
                elif fp != key:
                    continue
                fo = f["o"].lower()
                if noun and not (fo == noun or fo.startswith(noun + "_") or fo.startswith(noun[:-1] + "_") or fo == noun[:-1]):
                    continue
                if ck and not fo.endswith(ck):
                    continue
                hit.append(f)
            if hit:
                return says(hit)
            return "No lo sé."
        # c) "¿De que estan hechos los cometas?" / "¿De que esta compuesta la Tierra?"
        m = re.fullmatch(r"de que (?:esta|estan|es|son) (?:hech[oa]s?|formad[oa]s?|compuest[oa]s?|constituid[oa]s?) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and f["p"] in ("HECHO_DE", "FORMADO_DE", "FORMADO_POR", "COMPUESTO_DE", "COMPUESTO_POR", "CONSTITUIDO_POR", "CONSTITUIDO_DE") and not f.get("neg")]
            if fs:
                out = []
                for nm in dict.fromkeys(f["s"] for f in fs):
                    objs = [self._disp(f["o"]).lower() for f in fs if f["s"] == nm]
                    d = self._disp(nm)
                    pl = d.lower().startswith(("los ", "las ")) or canon(nm) != nm.upper() or nm.upper().endswith("S")
                    out.append(f"{d[:1].upper() + d[1:]} {'están hechos' if pl else 'está hecho'} de {' y '.join(objs)}.")
                return " ".join(out)
        # b) "¿Alrededor de que gira la Luna?" / "¿Cerca de que vive Ana?": pregunta con la preposicion por delante
        m = re.fullmatch(r"(alrededor de|cerca de|lejos de|detras de|delante de|encima de|debajo de|dentro de|fuera de|junto a|sobre|con|desde|hacia|para|por|sin|entre|en|a|de) que (\w+) (.+)", t)
        if m:
            prep, verb, rest = m.group(1), m.group(2), m.group(3)
            names = self._subject_in(rest.split())
            suf = "_" + prep.replace(" ", "_").upper()
            base = [f for f in facts if f["s"] in names and f["p"].endswith(suf) and not f.get("neg")]
            vs = re.sub(r"(an|en|a|e)$", "", verb)
            fs = [f for f in base if f["p"].lower().startswith(vs[:3])] or base
            if names and fs:
                return says(fs)
        # d) "¿Que planetas son helados?": miembros de una clase con una cualidad
        m = re.fullmatch(r"(?:que|cuales|cuantos|cuantas) (\w+?)s? (?:son|es|eran) (\w+)", t)
        if m and m.group(2) not in ("un", "una", "el", "la", "los", "las"):
            cls, adj = m.group(1), m.group(2)
            cls_keys = {cls.upper(), cls.upper() + "E", cls.upper() + "ES"}
            members = [f["s"] for f in facts if f["p"] == "ES" and f["o"] in cls_keys and not f.get("neg")]
            have = [x for x in dict.fromkeys(members)
                    if any(g["s"] == x and g["p"] in ("SER", "ESTAR") and not g.get("neg") and stem(g["o"].lower()) == stem(adj) for g in facts)]
            if members and have:
                names_ = [self._disp(x) for x in have]
                names_ = [n_[:1].upper() + n_[1:] if i == 0 else n_ for i, n_ in enumerate(names_)]
                joined = names_[0] if len(names_) == 1 else ", ".join(names_[:-1]) + " y " + names_[-1]
                plural = len(have) > 1
                adj_t = adj if not plural or adj.endswith("s") else adj + ("es" if adj[-1] not in "aeiou" else "s")
                return f"{joined} {'son' if plural else 'es'} {cls}{'s' if plural else ''} {adj_t}."
        # e) "¿Que es Pluton?" cuando de el se sabe una clase Y cualidades: "Pluton es un planeta enano."
        m = re.fullmatch(r"que (?:es|son) (\w+)", t)
        if m and not getattr(self, "_in_past", False):
            names = self._subject_in([m.group(1)])
            for nm in sorted(names):
                cls_ = [f["o"] for f in facts if f["s"] == nm and f["p"] == "ES" and not f.get("neg")]
                adjs = [f["o"] for f in facts if f["s"] == nm and f["p"] == "SER" and not f.get("neg")]
                if cls_ and adjs:
                    def indef(o_):
                        d_ = self._disp(o_)
                        art = re.match(r"(el|la|los|las|un|una|unos|unas)\s+", d_, flags=re.I)
                        fem = art.group(1).lower() in ("la", "las", "una", "unas") if art else o_.upper().endswith("A")
                        d_ = re.sub(r"^(el|la|los|las|un|una|unos|unas)\s+", "", d_, flags=re.I)
                        return ("una " if fem else "un ") + d_.lower()
                    adj_t = " ".join(self._disp(a_).lower() for a_ in dict.fromkeys(adjs))
                    d = self._disp(nm)
                    pl_ = t.startswith("que son") or d.lower().startswith(("los ", "las ")) or nm.upper().endswith("S")
                    if pl_ and len(set(cls_)) == 1:                          # parche-98: "Los asteroides son rocas pequeñas" (no "El asteroides es una rocas")
                        d = re.sub(r"^(el|la) ", lambda m_: "los " if m_.group(1).lower() == "el" else "las ", d, flags=re.I)
                        if not re.match(r"(los|las) ", d, re.I):
                            d = "los " + d
                        c_ = re.sub(r"^(el|la|los|las|un|una|unos|unas)\s+", "", self._disp(cls_[0]), flags=re.I).lower()
                        c_ = c_ if c_.endswith("s") else c_ + ("es" if c_[-1] not in "aeiou" else "s")
                        return f"{d[:1].upper() + d[1:]} son {c_} {adj_t}."
                    if len(set(cls_)) == 1:
                        return f"{d} es {indef(cls_[0])} {adj_t}."
                    return f"{d} es {' y '.join(indef(c_) for c_ in dict.fromkeys(cls_))}, {adj_t}."
        # f) "¿De que se compone el Sistema Solar?" / "¿Que incluye X?": definicion por enumeracion (conjunto_de)
        m = re.fullmatch(r"(?:de que (?:se compone|esta compuesto|esta compuesta|esta formado|esta formada|consta|esta constituido|esta constituida)|"
                         r"que (?:contiene|incluye|abarca|comprende)|que hay en|cuales son las partes de|que partes tiene) (.+)", t)
        if m:
            ws = [w for w in m.group(1).split() if w not in ("el", "la", "los", "las")]
            names = {"_".join(ws).upper()} & {f["s"] for f in facts} or self._subject_in(ws)
            fs = [f for f in facts if f["s"] in names and f["p"] == "CONJUNTO_DE" and not f.get("neg")]
            if fs:
                objs = [re.sub(r"^(el|la|los|las|un|una|unos|unas)\s+", "", self._disp(f["o"]).lower()) for f in fs]
                d = self._disp(fs[0]["s"])
                joined = objs[0] if len(objs) == 1 else ", ".join(objs[:-1]) + " y " + objs[-1]
                return f"{d[:1].upper() + d[1:]} está formado por {joined}."
        # g) listas y recuentos de una clase: "¿Cuales son los planetas que conoces?" / "¿Cuantos planetas hay?"
        m = (re.fullmatch(r"(cuantos|cuantas) (\w+) (?:hay|conoces|existen|tienes|sabes|conocemos)(?: .+)?", t)
             or re.fullmatch(r"(cuales|nombra|enumera|lista|cita|menciona|dime|di|muestrame) (?:son )?(?:los|las) (\w+)(?: que (?:conoces|sabes|tienes|hay|existen))?(?: (?:de|del|en|de la|de los) .+)?", t)
             or re.fullmatch(r"(que) (\w+) (?:conoces|sabes|tienes|existen|hay)(?: .+)?", t))
        if m and m.group(2) not in ("hora", "dia", "fecha", "cosas", "cosa", "veces"):
            cls = m.group(2)
            keys = {cls.upper(), cls.upper()[:-1], cls.upper()[:-2], cls.upper() + "E"}
            mem_ = []
            for f in facts:
                if f["p"] == "ES" and f["o"] in keys and not f.get("neg") and f["s"] not in keys and f["s"] not in mem_:
                    mem_.append(f["s"])
            if mem_:
                disp = [self._disp(x) for x in mem_]
                disp = [d_[:1].upper() + d_[1:] if d_[:2].islower() and d_.split()[0] not in ("el", "la", "los", "las") else d_ for d_ in disp]
                joined = disp[0] if len(disp) == 1 else ", ".join(disp[:-1]) + " y " + disp[-1]
                if m.group(1) in ("cuantos", "cuantas"):
                    return f"Conozco {len(mem_)} {cls if len(mem_) != 1 else cls[:-1]}: {joined}."
                fem = bool(re.match(r"(la|una)\s", self._disp(cls.upper()[:-1]).lower())) if cls.endswith("s") else False
                return f"{'Las' if fem else 'Los'} {cls} que conozco son: {joined}." if cls.endswith("s") else f"Conozco: {joined}."
        return None

    def _subject_in(self, words):
        """Nombres de la memoria que aparecen en las palabras ("la casa" -> CASA)."""
        toks = {canon(w.upper()) for w in words if w not in DETS}
        return {f["s"] for f in self.m.facts if canon(f["s"]) in toks}

    def special(self, question):
        import re
        t = re.sub(r"\s+", " ", re.sub(r"[¡!¿?.,;:]", " ", norm(question))).strip()
        facts = [f for f in self.m.facts]
        def says(fs):
            out = []
            for f in fs:
                x = self.say((f["s"], f["p"], f["o"]), neg=bool(f.get("neg"))) + "."
                if x not in out:
                    out.append(x)
            return " ".join(out[:6])
        sp93 = self._special_texto(t, question, facts, says)                # parche-93: preguntas sobre textos (superlativos, ordinales, ...)
        if sp93:
            return sp93
        m = re.fullmatch(r"que (?:es|son) ((?:un|una|el|la|los|las) \w+)", t)
        if m and not getattr(self, "_in_past", False):
            # "¿Que es un triangulo?": se contesta con lo que la memoria sabe (guardado o deducido), sin depender de como la escuela lea la pregunta
            names = sorted(self._subject_in(m.group(1).split()))
            if names:
                nm = names[0]
                objs = [f["o"] for f in facts if f["s"] == nm and f["p"] == "ES" and not f.get("neg")]
                try:
                    objs += [o_ for (_, _, o_) in self.derived(nm, "ES", None)]
                except Exception:
                    pass
                objs = list(dict.fromkeys(objs))
                if objs:
                    def cls(o_):
                        d_ = self._disp(o_).lower()
                        return d_ if re.match(r"(un|una)\s", d_) else ("una " if o_.endswith("A") else "un ") + d_
                    art = m.group(1).split()[0]
                    subj = self._disp(nm).lower()
                    subj = subj if re.match(r"(un|una|el|la|los|las)\s", subj) else f"{art} {subj}"
                    if t.startswith("que son") or subj.startswith(("los ", "las ")):          # parche-98: "Los asteroides son rocas" (no "es una rocas")
                        subj = re.sub(r"^(el|la) ", lambda m_: "los " if m_.group(1) == "el" else "las ", subj)
                        subj = subj if subj.startswith(("los ", "las ")) else "los " + subj
                        pls = []
                        for o_ in objs[:3]:
                            c_ = re.sub(r"^(el|la|los|las|un|una|unos|unas)\s+", "", self._disp(o_).lower())
                            pls.append(c_ if c_.endswith("s") else c_ + ("es" if c_[-1] not in "aeiou" else "s"))
                        return f"{subj.capitalize()} son {' y '.join(pls)}."
                    return f"{subj.capitalize()} es {' y '.join(cls(o_) for o_ in objs[:3])}."
        m = re.fullmatch(r"de que color (?:es|son|era) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            colors = {f["s"] for f in facts if f["p"] == "ES" and canon(f["o"]) == "COLOR"}
            fs = [f for f in facts if f["s"] in names and f["p"] in ("SER", "ESTAR") and f["o"] in colors | {c.replace("O", "A") for c in colors}
                  or (f["s"] in names and f["p"] in ("SER", "ESTAR") and any(norm(f["o"])[:-1] == c[:-1].lower() for c in colors))]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"para que (?:sirve|sirven|se usa|se usan|se utiliza|se utilizan) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and f["p"] == "SERVIR_PARA"]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"que (?:sirve|sirven|se usa|se usan|se utiliza|se utilizan) para (.+)", t)
        if m:
            key = "_".join(m.group(1).split()).upper()
            fs = [f for f in facts if f["p"] == "SERVIR_PARA" and canon(f["o"]) == canon(key)]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"es (\w+) (?:lo contrario|lo opuesto|el contrario|el opuesto) de (\w+)", t)
        if m:
            from src.reasoning.coherence import opposite
            if opposite(m.group(1), m.group(2), getattr(self.m, "opposites", [])):
                return f"Sí, {m.group(1)} es lo contrario de {m.group(2)}."
            return "No lo sé."
        m = re.fullmatch(r"(?:como|que nombre) (?:se llama|tiene) (.+)", t)
        if m:                                                    # parche-86: "¿Como se llama el perro de Irene?" -> hecho (PERRO_DE_IRENE, LLAMARSE, TOBY)
            key = "_".join(re.sub(r"^(el|la|mi|su|un|una)\s+", "", m.group(1)).split()).upper()
            fs = [f for f in facts if f["p"] == "LLAMARSE" and f["s"] == key and not f.get("neg")]
            if fs:
                disp = getattr(self.m, "display", {})
                return f"{disp.get(key, key.replace('_', ' ').title())} se llama {disp.get(fs[-1]['o'], fs[-1]['o'].title())}."
        m = re.fullmatch(r"(?:cual|que) (?:es|seria) (?:lo contrario|lo opuesto|el contrario|el opuesto) de (\w+)", t)
        if m:                                                    # parche-84: el contrario es simetrico ("Alto es lo contrario de bajo" -> "¿Cual es lo contrario de bajo?")
            x = m.group(1).upper()
            outs = []
            for f in facts:
                if f["p"] == "CONTRARIO_DE" and not f.get("neg"):
                    if norm(f["o"]).upper() == x:
                        outs.append(f["s"])
                    elif norm(f["s"]).upper() == x:
                        outs.append(f["o"])
            for a_, b_ in getattr(self.m, "opposites", []):
                if norm(b_).upper() == x:
                    outs.append(a_)
                elif norm(a_).upper() == x:
                    outs.append(b_)
            outs = list(dict.fromkeys(self._disp(o_).lower() if str(o_).isupper() else str(o_) for o_ in outs))
            if outs:
                return f"Lo contrario de {m.group(1)} es {' o '.join(outs)}."
        m = re.fullmatch(r"por que (.+)", t)
        if m:
            words = m.group(1).split()
            names = self._subject_in(words)
            fs = [f for f in facts if f["s"] in names and f["p"].endswith("_PORQUE") and any(norm(w)[:3] == f["p"][:3].lower() for w in words)]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"(?:a |de |con |en |para )?cuant[oa]s (.+)", t)
        if m:
            words = m.group(1).split()
            tener = [k for k, w in enumerate(words) if w in ("tiene", "tienen", "tuvo", "tenia", "tendra")]
            if tener:
                noun = words[tener[0] - 1] if tener[0] else ""
                names = self._subject_in(words[tener[0] + 1:])
                stem = lambda x: re.sub(r"(os|as|es|o|a|e|s)$", "", x.lower())
                fs = [f for f in facts if f["s"] in names and f["p"].startswith("TENER") and not f.get("neg")
                      and any(stem(part) == stem(noun) for part in norm(f["o"]).split("_"))]
                return says(fs) if fs else "No lo sé."
            for pat in (r"(?i)cuánt[oa]s(?:\s+\w+)?", r"(?i)cuánt[oa]s"):         # con o sin sustantivo ("cuantos hijos" / "cuantos")
                q2 = re.sub(pat, "qué", question, count=1)
                kind, tt = self.read(q2)
                if tt and kind in ("objeto", "sujeto"):
                    s_ = None if tt["s"] == norm(HOLE) else tt["s"]
                    o_ = None if tt["o"] == norm(HOLE) else tt["o"]
                    hits = self.lookup(s_, tt["p"], o_)
                    vals = list(dict.fromkeys(f[2] if kind == "objeto" else f[0] for f in hits))
                    if vals:
                        return f"{len(vals)}: " + ", ".join(self._disp(v) for v in vals) + "."
            return "No lo sé."
        m = re.fullmatch(r"donde \w+ (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and not f.get("neg") and any("_" + w in f["p"] for w in ("ENCIMA", "DEBAJO", "DENTRO", "FUERA", "CERCA", "LEJOS", "DELANTE", "DETRAS", "JUNTO", "ENFRENTE", "ALREDEDOR"))]
            if fs:
                return says(fs)
        m = re.fullmatch(r"que (?:hace|hizo|ha hecho|esta haciendo|hacia) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and not f.get("neg") and f["p"] not in ("ES",)]
            return says(fs) if fs else None
        m = re.fullmatch(r"como (?:es|esta|son|estan|era|estaba|fue) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and f["p"] in ("SER", "ESTAR")]
            return says(fs) if fs else None
        m = re.fullmatch(r"es|(?:es|esta|son|estan|era|estaba) (.+)", t)
        if m and m.group(1):
            words = m.group(1).split()
            names = self._subject_in(words)
            fs = [f for f in facts if f["s"] in names and f["p"] in ("SER", "ESTAR")]
            if fs:
                subj = {canon(x.upper()) for x in words if canon(x.upper()) in {canon(f["s"]) for f in fs}}
                adjs = [w for w in words if w not in DETS and canon(w.upper()) not in subj]
                stem = lambda x: re.sub(r"(os|as|es|o|a|e|s)$", "", x.lower())
                hit = [f for f in fs if any(stem(a) == stem(norm(f["o"])) for a in adjs)]
                if hit:
                    f = hit[0]
                    return ("No. " if f.get("neg") else "Sí. ") + says([f])
                if any(w in DETS for w in words[1:]):            # "¿Es un gorrión un pájaro?": no es adjetivo, que lo vea la ruta normal
                    return None
                return "Eso no me consta; solo sé " + says([f for f in fs if not f.get("neg")][:3] or fs[:3])
            return None
        m = re.fullmatch(r"quien (?:es|esta|son|estan|era|estaba) (.+)", t)
        if m:
            stem = lambda x: re.sub(r"(os|as|es|o|a|e|s)$", "", x.lower())
            words = [w for w in m.group(1).split() if w not in DETS]
            hit = [f for f in facts if f["p"] in ("SER", "ESTAR") and not f.get("neg") and any(stem(w) == stem(norm(f["o"])) for w in words)]
            if hit:
                return says(hit)
        m = re.fullmatch(r"que (?:dice|dijo|cree|creia|piensa|opina|afirma|asegura|comenta|cuenta) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and f["p"].endswith("_QUE")]
            return says(fs) if fs else None
        m = re.fullmatch(r"quien (?:dice|dijo|cree|piensa|opina|afirma|asegura|comenta|cuenta) que (.+)", t)
        if m:
            key = "_".join(m.group(1).split())
            fs = [f for f in facts if f["p"].endswith("_QUE") and f["o"].lower() == key]
            return says(fs) if fs else None
        return None

    def timeline(self, question):
        """Preguntas de orden: "que paso primero / ultimo / antes de X / despues de X" con fechas absolutas (parche-53)."""
        import re
        from src.language.fechas import extract_abs, resolve, before, after, parse_iv, fmt
        q = norm(question).strip(" ¿?.!")
        m = re.fullmatch(r"que (?:paso|ocurrio|sucedio|hice|hizo)\s*(primero|ultimo|al final|antes|despues)?(?:\s+(?:de|del)\s+(.+))?", q)
        if not m:
            return None
        mode, ref = m.group(1) or "", m.group(2)
        dated = []
        seen = set()
        for f in self.m.facts:
            if f.get("neg") or not f.get("when_abs"):
                continue
            key = ((f["s"], f["p"], f["o"]), f["when_abs"])
            if key not in seen:
                seen.add(key)
                dated.append((parse_iv(f["when_abs"])[0], f["when_abs"], (f["s"], f["p"], f["o"])))
        if mode in ("antes", "despues"):
            if not ref:
                return None
            _, iv, _ = extract_abs("el " + ref, self._today())
            iv = iv or resolve("_".join(w for w in ref.replace("el ", "").replace("la ", "").split()
                                          if w not in ("ultimo",)).replace("ano_", "ano_"), self._today())
            if not iv:
                return None
            pick = [d for d in dated if (before if mode == "antes" else after)(d[1], iv)]
            if not pick:
                return "No lo sé: no tengo nada con fecha " + mode + " de " + fmt(iv) + "."
        elif mode in ("primero", "ultimo", "al final"):
            if not dated:
                return "No lo sé: no tengo hechos con fecha."
            edge = min(d[0] for d in dated) if mode == "primero" else max(d[0] for d in dated)
            pick = [d for d in dated if d[0] == edge]
        else:
            return None
        pick.sort(key=lambda d: d[0])
        return " ".join(self.say(d[2]) + "." for d in pick)[:800]

    def lookup(self, s, p, o, neg=False, when=""):
        """Hechos de memoria que encajan; s u o pueden ser None (hueco). La relacion encaja si sus lemas se parecen o si
        se dijo con la misma forma verbal (rescata lemas irregulares: muerde -> muerder / mendar)."""
        out = []
        tpl = self._tpl
        surf = getattr(self.m, "surface", {})
        for fs, fp, fo in self._facts(neg):
            same = same_pred(fp, p) or bool(tpl and surf.get(fp.upper()) == tpl)
            al = lambda x: canon(getattr(self.m, "alias", {}).get(x.upper(), x.upper()))          # sinonimos ensenados
            if (s is None or fs == s.upper() or canon(fs) == canon(s) or al(fs) == al(s)) and \
                    (o is None or fo == o.upper() or canon(fo) == canon(o) or al(fo) == al(o)) and same \
                    and (not when or self._when_ok((fs, fp, fo), when)):
                out.append((fs, fp, fo))
        return out

    def derived(self, s, p, o):
        if self.deduce is None:
            return []
        try:
            got = self.deduce([(f["s"], f["p"], f["o"]) for f in self.m.facts if not f.get("neg") and not f.get("q")])
        except Exception:
            return []
        got = dict(got) if isinstance(got, dict) else {k: [] for k in got}
        from src.reasoning.lessons import verb_derive
        for k, v in verb_derive([(f["s"], f["p"], f["o"]) for f in self.m.facts if not f.get("neg") and not f.get("q")],
                                getattr(self.m, "verb_isa", {})).items():
            got.setdefault(k, v)
        self.support = dict(got)
        have = set(self._facts(False))
        return [f for f in got if f not in have and (s is None or f[0] == s.upper()) and (o is None or f[2] == o.upper())
                and same_pred(f[1], p)]

    # ---- parche-112: razonador general (reglas y propiedades de relacion como DATOS de los cartuchos) --------------------------
    def _razonador(self):
        m = self.m
        props, reglas = getattr(m, "propiedades", None), getattr(m, "reglas", None)
        if not props and not reglas:
            return None
        sig = (len(m.facts), len(reglas or []), len(props or {}))
        if getattr(self, "_rz_sig", None) != sig:
            from src.reasoning.razonador import Razonador
            fs = [f for f in m.facts if not f.get("q") and not f.get("archived")]
            self._rz = Razonador([(f["s"], f["p"], f["o"]) for f in fs if not f.get("neg")], list(reglas or []), dict(props or {}),
                                 [(f["s"], f["p"], f["o"]) for f in fs if f.get("neg")])
            self._rz_sig = sig
        return self._rz

    @staticmethod
    def _nom(x):
        return x.replace("_", " ").lower()

    def razonar(self, s, p, o):
        """(valor, texto) con valor SI/NO si el razonador lo demuestra o lo refuta; None si no sabe. La memoria y las lecciones mandan: esto solo actua al fallar."""
        try:
            rz = self._razonador()
            if rz is None or not s or not o:
                return None
            r = rz.preguntar(s.upper(), p.upper(), o.upper())
            if r.valor not in ("SI", "NO") or r.prueba is None:
                return None
            from src.reasoning.razonador import explicar
            pasos = explicar(r.prueba, self._nom)
            return r.valor, pasos
        except Exception:
            return None

    # ---- decir ------------------------------------------------------
    def _disp(self, name):
        d = getattr(self.m, "display", {}).get(name.upper())
        return d or name.replace("_", " ").title()

    @staticmethod
    def _agree(tpl, s_txt):
        """parche-93: concordancia sujeto-verbo al reutilizar una plantilla: "Urano giran" -> "Urano gira"; "Los asteroides es" -> "Los asteroides son"."""
        import re
        m = re.match(r"\{s\}\s+(\w+)", tpl)
        if not m:
            return tpl
        verb, low = m.group(1), s_txt.lower()
        plural = low.startswith(("los ", "las ", "unos ", "unas ", "todos ", "todas ", "algunos ", "algunas ")) or " y " in low
        new = None
        if plural:
            new = {"es": "son", "esta": "están", "está": "están"}.get(verb)
        elif len(verb) > 3 or verb in ("son", "van"):
            new = {"son": "es", "estan": "está", "están": "está"}.get(verb)
            if new is None and re.search(r"(an|en)$", verb) and verb not in ("estan", "están") and not re.search(r"(?i)^(juan|ruben|joan|carmen|german|adan|efren)$", verb):
                new = verb[:-1]
        return tpl[:m.start(1)] + new + tpl[m.end(1):] if new else tpl

    def say(self, fact, neg=False):
        s, p, o = fact
        tpl = None
        for k, v in getattr(self.m, "surface", {}).items():
            if k == p.upper() or same_pred(k, p):
                tpl = v
                break
        if tpl is None and p.upper().startswith(("MAS_", "MENOS_")) and p.upper().endswith("_QUE"):
            kind, _, rest = p.lower().partition("_")
            tpl = "{s} es " + kind + " " + rest[:-4] + " que {o}"
        if tpl is None:
            base, _, prep = p.lower().partition("_")
            fixed = {"ser": "{s} es {o}", "estar": "{s} está {o}", "estar_en": "{s} está en {o}", "tener": "{s} tiene {o}",
                     "parte_de": "{s} es parte de {o}"}      # hechos que salen de efectos o de la semilla (parche-59)
            tpl = fixed.get(p.lower()) or "{s} " + base + (" " + prep if prep else "") + " {o}"
        o_txt = self._disp(o)
        if p.upper() in ("SER", "ESTAR") and o.upper() not in getattr(self.m, "display", {}):
            o_txt = o.replace("_", " ").lower()                  # adjetivos en minuscula: "la puerta está abierta"
        if p.upper() == "ES" and not neg:                       # parche-95: "Plutón es un planeta" (no "el planeta") si la clase tiene 3 o mas miembros
            mm_ = re.match(r"(el|la) (\w+)$", o_txt, re.I)
            if mm_ and len({f["s"] for f in self.m.facts if f["p"] == "ES" and f["o"] == o.upper() and not f.get("neg")}) >= 3:
                o_txt = ("un " if mm_.group(1).lower() == "el" else "una ") + mm_.group(2)
        tpl = self._agree(tpl, self._disp(s))
        text = tpl.format(s=self._disp(s), o=o_txt).replace(" de el ", " del ").replace(" a el ", " al ")
        text = text.replace(" _", "").strip()
        ws = [d for _, d in self._whens(fact) if d] if not neg else []
        if ws:
            text += " " + ws[0]
            iv, key = self._abs_of(fact)
            if iv and not key.isdigit():
                from src.language.fechas import fmt
                if fmt(iv) not in ws[0]:
                    text += " (" + fmt(iv) + ")"
        until = next((f.get("until") for f in self.m.facts if (f["s"], f["p"], f["o"]) == tuple(fact) and f.get("until")), None)
        if until and getattr(self, "_in_past", False):
            import re as _re
            lem = p.lower().partition("_")[0]
            if lem[-2:] in ("ar", "er", "ir") and len(lem) > 3:                # vive -> vivia, trabaja -> trabajaba
                pres, imp = (lem[:-2] + "a", lem[:-2] + "aba") if lem.endswith("ar") else (lem[:-2] + "e", lem[:-2] + "ía")
                text = _re.sub(r"\b" + pres + r"\b", imp, text, count=1)
            from src.language.fechas import fmt as _fmt
            text += f" (hasta el {_fmt(until + '/' + until)})"
        text = text[0].upper() + text[1:]
        return ("No es cierto que " + text[0].lower() + text[1:]) if neg else text

    def _because(self, fact):
        sup = self.support.get(fact)
        return (" (porque " + " y ".join(self.say(x) for x in sup) + ")") if sup else ""

    # ---- respuesta --------------------------------------------------
    def _wants_past(self, question: str) -> bool:
        """Pregunta en pasado ("antes", imperfecto de un verbo que conozco: vivia, trabajaba)."""
        import re
        t = norm(question)
        if re.search(r"\b(antes|antiguamente|anteriormente|antano)\b", t):
            return True
        heads = {f["p"].lower().partition("_")[0][:-2] for f in list(self.m.facts) + list(getattr(self.m, "past", [])) if len(f["p"]) > 4}
        for w in re.findall(r"\w+", t):
            if re.search(r"(aba|abas|aban|ia|ias|ian)$", w) and re.sub(r"(aba|abas|aban|ia|ias|ian)$", "", w) in heads:
                return True
        return False

    def answer(self, question: str) -> str:
        from src.language import marcos                                 # parche-96: marcos de pregunta sin analizador (leen los hechos directamente)
        inpast = getattr(self, "_in_past", False)
        if not inpast:
            try:
                pri = marcos.responder(self, question, primero=True)
            except Exception:                                           # noqa
                pri = None
            if pri:
                return pri
        r = self._answer_base(question)
        if r.startswith(("No lo sé", "No he entendido", "No conozco", "No sé", "Creo que hablas", "Creo que preguntas", "Eso no me consta")) and not inpast:
            try:
                alt = marcos.responder(self, question)
            except Exception:                                           # noqa
                alt = None
            if alt:
                return alt
        if r.startswith("Sí") and not inpast:
            r = self._calificador_sin_respaldo(question, r)
        return r

    def _calificador_sin_respaldo(self, question: str, r: str) -> str:
        """parche-102: "¿Es Venus un planeta rojo?" no puede contestarse "Sí. Venus es un planeta." si nada dice que Venus sea rojo: el calificador no se ignora."""
        import unicodedata

        def nm(w):
            return "".join(c for c in unicodedata.normalize("NFD", str(w).lower().replace("_", " ")) if unicodedata.category(c) != "Mn").strip()
        q = re.match(r"^[¿\s]*(?:es|son|era|eran)\s+(.+?)\s+(?:un|una|unos|unas|el|la|los|las)\s+(\w+)\s+([a-záéíóúñ]+)\s*\??\s*$", question.strip(), re.I)
        if not q:
            return r
        x, cls, adj = nm(q.group(1)), nm(q.group(2)), nm(q.group(3))
        x = re.sub(r"^(el|la|los|las)\s+", "", x)
        if len(adj) < 4 or adj in (cls, x) or adj in nm(r) or adj in ("mas", "menos", "como", "pero", "mismo", "misma", "otro", "otra"):
            return r
        raiz = adj[:-1] if adj[-1] in "oasey" else adj
        mine = [f for f in self.m.facts if nm(f["s"]) == x and not f.get("neg")]
        if not mine:
            return r
        for f in mine:
            if raiz in nm(f["o"]) or raiz in nm(f["p"]):
                return r
        for f in self.m.facts:                              # tambien vale que lo diga la clase ("los planetas son rojos") o un alias
            if nm(f["s"]) in (cls, nm(cls) + "s") and (raiz in nm(f["o"]) or raiz in nm(f["p"])):
                return r
        disp = self._disp(mine[0]["s"])
        cdisp = next((self._disp(f["o"]) for f in mine if str(f["p"]).upper() == "ES" and nm(f["o"]) == cls), cls)
        if not re.match(r"(un|una|el|la)\s", cdisp.lower()):
            cdisp = "un " + cdisp
        return f"No lo sé: sé que {disp} es {cdisp}, pero no que sea {q.group(3)}."

    def _answer_base(self, question: str) -> str:
        past = getattr(self.m, "past", [])
        if past and self._wants_past(question):
            saved = self.m.facts
            self.m.facts = list(past)
            self._in_past = True
            try:
                r = self._answer(question)
            finally:
                self.m.facts, self._in_past = saved, False
            if not r.startswith(("No lo sé", "Eso no me consta", "No he entendido")):
                return r
        return self._answer(question)

    def _answer(self, question: str) -> str:
        self._alts = []
        tl = self.timeline(question)
        if tl:
            return tl
        sp = self.special(question)
        if sp:
            return sp
        kind, t = self.read(question)
        if kind in ("si_no", "cuando") and len(self._alts) > 1:
            for alt in self._alts:                          # "Es Marta madre de Pablo" se puede leer mal; vale la que la memoria reconoce
                a_s, a_o = alt["s"], alt["o"]
                if self.lookup(a_s, alt["p"], a_o) or self.lookup(a_s, alt["p"], a_o, neg=True) or self.derived(a_s, alt["p"], a_o):
                    t = alt
                    break
        self._tpl = (t or {}).get("template")
        if t is None:
            return "No he entendido la pregunta. Prueba con otra forma (por ejemplo: ¿Quién escribió una novela?)."
        s = None if t["s"] == norm(HOLE) else t["s"]
        o = None if t["o"] == norm(HOLE) else t["o"]
        p = t["p"]
        when = t.get("when", "")
        if kind == "cuando":
            hits = self.lookup(s, p, o)
            if not hits:
                return "No lo sé."
            if any(d for f in hits for _, d in self._whens(f)):
                return " ".join(dict.fromkeys(self.say(f) + "." for f in hits))[:600]
            return "No lo sé: sé que " + self.say(hits[0]).rstrip(".") + ", pero no cuándo."
        if kind == "si_no" and when and self.lookup(s, p, o):
            if self.lookup(s, p, o, when=when):
                return "Sí. " + self.say(self.lookup(s, p, o, when=when)[0]) + "."
            hits = self.lookup(s, p, o)
            if any(d for f in hits for _, d in self._whens(f)):
                return "No. Según lo que sé: " + self.say(hits[0]) + "."
            return "No lo sé: sé que " + self.say(hits[0]).rstrip(".") + ", pero no cuándo."
        if kind == "si_no":
            hits = self.lookup(s, p, o, neg=False)
            if hits and all(self._q(f) for f in hits):
                return "No lo sé con certeza: solo sé que " + self.say(hits[0])[0].lower() + self.say(hits[0])[1:] + "."
            if hits:
                return "Sí. " + self.say(self.lookup(s, p, o)[0]) + "."
            if p.upper().startswith(("MAS_", "MENOS_")) and s and o:
                opp = ("MENOS_" if p.upper().startswith("MAS_") else "MAS_") + p.upper().split("_", 1)[1]
                inv = self.lookup(s, opp, o) or self.derived(s, opp, o)
                if inv:
                    return "No. " + self.say(inv[0]) + self._because(inv[0]) + "."
            if self.lookup(s, p, o, neg=True):
                return "No. " + self.say(self.lookup(s, p, o, neg=True)[0], neg=True) + "."
            d = self.derived(s, p, o)
            if d:
                return "Sí, lo deduzco: " + self.say(d[0]) + self._because(d[0]) + "."
            rz = self.razonar(s, p, o) if s and o else None
            if rz:
                return ("Sí, lo razono:\n" if rz[0] == "SI" else "No, lo razono:\n") + rz[1]
            if self.lookup(s, p, None) or self.lookup(None, p, o):
                return "Eso no me consta; solo sé " + "; ".join(dict.fromkeys(self.say(f) for f in (self.lookup(s, p, None) or self.lookup(None, p, o))[:3])) + "."
            return "No lo sé."
        hits = self.lookup(s, p, o, when=when)
        ded = [] if (hits and s is not None and o is not None) else self.derived(s, p, o)
        if hits and ded and (s is None or o is None):          # pregunta abierta: lo dicho y tambien lo deducido (parche-59)
            more = [d for d in ded if d not in hits][:3]
            return " ".join(dict.fromkeys([self.say(f) + "." for f in hits] + [self.say(f) + "." for f in more]))[:600]
        if hits:
            return " ".join(dict.fromkeys(self.say(f) + "." for f in hits))[:600]
        if ded:
            return "Lo deduzco: " + " ".join(dict.fromkeys(self.say(f) + self._because(f) + "." for f in ded[:5]))
        if (s is None) != (o is None) and p:
            try:
                rz = self._razonador()
                sol = rz.consultar(s and s.upper(), p.upper(), o and o.upper(), 12) if rz else []
            except Exception:
                sol = []
            if sol:
                ents = [x["o"] if s else x["s"] for x in sol]
                return "Lo razono: " + ", ".join(self._nom(e) for e in ents) + "."
        return "No lo sé."

