"""parche-127: preguntas sobre LO LEIDO.

Cada frase que lee el lector queda guardada con el arbol de la escuela (mem.textos). Aqui se construye, sobre esas frases, un indice de
ENTIDADES (nombres propios: «Lamine», «Yamal» y «Lamine Yamal» son la misma persona) y se contesta segun el TIPO de pregunta
(quien es, que sabes de, cuando, donde, cuantos, con/contra quien, que <cosa>, si/no, por que...) sacando la respuesta del arbol de la
frase mejor puntuada. Nada de listas de dominio: solo gramatica (UD), idf de lemas y distancia de edicion para erratas.
Si no se sabe, se dice (y se muestra la frase mas cercana); nunca se inventa."""
from __future__ import annotations

import copy
import math
import os
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

# ====================================================== utilidades ========================================================================


def nrm(s) -> str:
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


CONEC = {"de", "del", "la", "las", "los", "el", "da", "do", "di", "van", "von", "y"}
CONEC_NOMBRE = CONEC - {"y"}
MESES = {"enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "setiembre", "octubre", "noviembre", "diciembre"}
LIGEROS = {"ser", "estar", "haber", "hacer", "poder", "deber", "ir", "seguir", "quedar", "llegar", "volver", "dejar", "lograr", "conseguir"}
TIEMPO = {"temporada", "ano", "anos", "minuto", "dia", "mes", "momento", "semana", "epoca", "fecha", "hora", "tarde", "noche", "manana", "siglo", "decada", "periodo", "etapa", "jornada"}
STOPQ = set("""el la los las un una unos unas de del al a en por para con sin sobre entre hacia hasta desde ante contra tras segun y o u e ni pero si no que se lo le les me te nos os
mi tu su sus mis tus es son fue fueron era eran esta estan estaba esto eso ese esa estos esas este aquel aquella muy mas menos tan tanto ya aun asi como cuando donde quien quienes cual cuales cuanto
cuanta cuantos cuantas porque por que sabes sabe dime dame hablame cuentame explicame favor puedes podrias oye hola gracias""".split())
WH = {"quien", "quienes", "cual", "cuales", "cuanto", "cuanta", "cuantos", "cuantas", "cuando", "donde", "adonde", "como", "que"}
PREPS = {"con", "contra", "ante", "a", "de", "del", "para", "por", "sobre", "en", "desde", "hacia", "entre", "sin", "tras", "segun", "hasta", "frente"}
CLASE_PREP = {"contra": {"contra", "ante", "frente", "vs"}, "ante": {"contra", "ante", "frente"}, "con": {"con", "junto"}, "a": {"a", "ante", "para"},
              "de": {"de", "del"}, "para": {"para", "por", "a"}, "por": {"por"}, "sobre": {"sobre"}, "en": {"en"}, "desde": {"desde"}, "hacia": {"hacia"}}
NEG = {"no", "nunca", "jamas", "tampoco", "ni", "sin"}
PERFIL_RX = [
    re.compile(r"^(?:y )?(?:quien|quienes|que) (?:es|son|fue|fueron|era|eran|sera) (?P<x>.+)$"),
    re.compile(r"^(?:que|cuanto|cuantas cosas|algo) (?:sabes|sabe|conoces|se) (?:de|del|sobre|acerca de|respecto a|de lo de)\s+(?P<x>.+)$"),
    re.compile(r"^(?:hablame|cuentame|dime|explicame|resumeme|describeme|informame|ensenaname)(?: algo| todo| mas| un poco| lo que sepas| lo que sabes)?(?: de| del| sobre| acerca de)\s+(?P<x>.+)$"),
    re.compile(r"^(?:dame|quiero|necesito|busco)(?: toda| mas| algo de)? (?:la )?(?:informacion|datos|detalles) (?:de|del|sobre|acerca de)\s+(?P<x>.+)$"),
    re.compile(r"^(?:y )?(?P<x>.+?)(?: que (?:es|fue|hizo|hace|sabes))$"),
]
ART = re.compile(r"^(?:el|la|los|las|un|una|unos|unas|al|del)\s+")


def damerau(a: str, b: str, tope: int = 2) -> int:
    """Distancia de edicion con trasposiciones (OSA). Corta si pasa del tope."""
    if abs(len(a) - len(b)) > tope:
        return tope + 1
    prev2, prev = None, list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            c = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + c)
            if prev2 is not None and i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
        if min(prev) > tope:
            return tope + 1
    return prev[-1]


def raiz(w: str) -> str:
    """Raiz tosca para emparejar verbo/nombre/plural: debutar~debut, selecciones~seleccion."""
    w = nrm(w)
    if len(w) >= 6:
        w = re.sub(r"(?:ar|er|ir|ando|iendo|ado|ido|aron|ieron|aba|ia)$", "", w)
    elif len(w) >= 5:
        w = re.sub(r"(?:es|s)$", "", w)
    return w[:6] if len(w) > 6 else w


class T:
    __slots__ = ("i", "f", "nf", "u", "h", "d", "l", "nl")

    def __init__(self, i, f, u, h, d, l):
        self.i, self.f, self.nf, self.u, self.h, self.d, self.l, self.nl = i, f, nrm(f), u, h, d, l, nrm(l or f)


def _tokens_texto(txt: str) -> List[T]:
    return [T(i, m, "X", -1, "dep", m.lower()) for i, m in enumerate(re.findall(r"\d+(?:[.,]\d+)+|\w+|[^\w\s]", txt))]


def _es_inicial(t: "T", sig: Optional["T"]) -> bool:
    return len(t.f) == 1 and t.f.isupper() and sig is not None and sig.f == "."


class Frase:
    def __init__(self, ent: dict, n: int):
        self.n, self.texto, self.sec, self.doc, self.k = n, ent.get("t", ""), ent.get("sec", ""), ent.get("d", 0), ent.get("k", 0)
        self.par = ent.get("p", 0)
        self.impl_w: Dict[str, float] = {}
        self.tok: List[T] = []
        arranques: List[int] = []
        self.n_main = None
        for blk in ent.get("r") or []:
            off = len(self.tok)
            arranques.append(off)
            if blk.startswith("@\n"):                                              # incisos (rayas, parentesis): se leen, pero no mandan en el sujeto de la frase
                if self.n_main is None:
                    self.n_main = off
                blk = blk[2:]
            for ln in blk.split("\n"):
                c = ln.split("\t")
                if len(c) < 5:
                    continue
                try:
                    h = int(c[2])
                except ValueError:
                    h = 0
                self.tok.append(T(len(self.tok), c[0], c[1], off + h - 1 if h > 0 else -1, c[3], c[4]))
        self.con_arbol = bool(self.tok)
        if not self.tok:
            self.tok = _tokens_texto(self.texto)
        else:
            self._enlazar_relativos(arranques)
        if self.n_main is None:
            self.n_main = len(self.tok)
        n_ = len(self.tok)
        for t in self.tok:                                                      # arboles con ciclos o cabezas fuera de rango: se cortan
            x, pasos = t.h, 0
            while 0 <= x < n_ and pasos <= n_:
                if x == t.i:
                    t.h = -1
                    break
                x, pasos = self.tok[x].h, pasos + 1
            if t.h >= n_ or pasos > n_:
                t.h = -1
        self.hij: Dict[int, List[int]] = defaultdict(list)
        for t in self.tok:
            if t.h >= 0:
                self.hij[t.h].append(t.i)
        if self.con_arbol:
            try:
                if self._reparar():
                    self.hij = defaultdict(list)
                    for t in self.tok:
                        if t.h >= 0:
                            self.hij[t.h].append(t.i)
            except Exception:                                                                        # noqa  (un arbol raro nunca debe romper la lectura)
                pass
        self.ment: List[Tuple[int, int, frozenset, str, tuple]] = []
        self.fams: Set[str] = set()
        self.impl: Set[str] = set()
        self.suj: Optional[str] = None
        self.ctx_fams: Dict[str, float] = {}
        self.ctx_lem: Dict[str, float] = {}
        self.ctx_raices: Dict[str, float] = {}
        self.lem: Set[str] = set()
        self.raices: Set[str] = set()
        for t in self.tok:
            if t.u in ("NOUN", "VERB", "ADJ", "PROPN", "NUM", "X") and t.nl not in LIGEROS and len(t.nl) > 1:
                self.lem.add(t.nl)
                self.raices.add(raiz(t.nl))

    def _enlazar_relativos(self, arranques: List[int]) -> None:
        """Un tramo que empieza por «quien/que/donde» (frase larga troceada) es una oracion de relativo del tramo anterior:
        su raiz pasa a colgar del ultimo nombre de ese tramo, para que no se le atribuya al sujeto de la frase."""
        tk = self.tok
        for n_blk, a in enumerate(arranques):
            if n_blk == 0 or a >= len(tk):
                continue
            j = a
            while j < len(tk) and tk[j].u in ("PUNCT", "CCONJ", "ADP", "DET"):
                j += 1
            if j >= len(tk) or j >= (arranques[n_blk + 1] if n_blk + 1 < len(arranques) else len(tk)):
                continue
            rel = tk[j]
            if not (rel.nl in ("quien", "quienes", "cuyo", "cuya", "cuyos", "cuyas") or (rel.nl == "que" and rel.u == "PRON")
                    or (rel.nl == "donde" and rel.u == "ADV")):
                continue
            raiz_ = rel.h if rel.h >= 0 else None
            if raiz_ is None:
                continue
            while tk[raiz_].h >= a and tk[raiz_].h != raiz_:
                raiz_ = tk[raiz_].h
            if tk[raiz_].h >= 0:
                continue
            k = a - 1
            while k >= 0 and tk[k].u not in ("NOUN", "PROPN"):
                k -= 1
            if k < 0:
                continue
            while tk[k].d == "flat" and tk[k].h >= 0:
                k = tk[k].h
            tk[raiz_].h, tk[raiz_].d = k, "acl:relcl"

    # ---- reparacion de errores tipicos del arbol ----------------------------------------------------------------------------------
    def _romano(self, i: int) -> bool:
        t = self.tok[i]
        return bool(re.fullmatch(r"[IVXLCDM]{1,6}", t.f)) and t.u in ("NUM", "X", "PROPN", "NOUN", "ADJ") and i > 0 and self.tok[i - 1].u == "PROPN"

    def _reparar(self) -> bool:
        """El parser estadistico falla de forma sistematica en tres cosas que el resto de la lectura necesita bien:
        1) el sujeto que va tras un complemento circunstancial («En 1254 el rey Alfonso le concedio…») sale como complemento;
        2) con un pronombre clitico delante («donde los recogio el portaaviones») el sujeto pospuesto sale como objeto;
        3) las enumeraciones «Nombre, cargo, Nombre, cargo» cuelgan los cargos del nombre equivocado.
        Se corrigen aqui, de forma general, antes de que nadie lea el arbol."""
        tk, n = self.tok, len(self.tok)
        cambio = False
        hij = self.hij
        for v in tk:                                                                          # «orbita lunar», «luz solar»: un infinitivo pegado a un nombre sin preposicion es un adjetivo
            if v.u == "VERB" and v.i > 0 and tk[v.i - 1].u == "NOUN" and v.d in ("xcomp", "acl", "amod", "dep", "conj") and re.fullmatch(r"[a-z]+(?:ar|er|ir)", v.f) \
                    and not _sinonimos(v.nf, "VERB") and all(tk[c].d in ("nummod", "nmod", "det", "case", "punct") for c in hij.get(v.i, ())):
                v.u, v.h, v.d = "ADJ", v.i - 1, "amod"
                cambio = True
        for v in tk:
            if v.u != "VERB" or v.d in ("amod", "acl", "acl:relcl", "xcomp") or not v.d:
                continue
            hs = [tk[c] for c in hij.get(v.i, ())]
            if any(c.d in ("nsubj", "nsubj:pass", "csubj", "csubj:pass") for c in hs):
                continue
            cl = [c for c in hs if c.d == "obj" and c.u == "PRON" and c.nl in ("lo", "la", "los", "las", "el") and c.i < v.i]
            pos = [c for c in hs if c.d in ("obj", "obl") and c.i > v.i and c.u in ("NOUN", "PROPN") and not any(tk[x].d == "case" for x in hij.get(c.i, ()))
                   and (c.u == "PROPN" or any(tk[x].d == "det" for x in hij.get(c.i, ())))]
            if cl and pos and not any(c.d == "obj" and c.i > v.i and c.u in ("NOUN", "PROPN") and c is not pos[0] for c in hs):
                pos[0].d = "nsubj"
                cambio = True
                continue
            pre = [c for c in hs if c.d == "obl" and c.i < v.i and c.u in ("NOUN", "PROPN") and c.nl not in TIEMPO and c.nl not in MESES and not c.f.isdigit()
                   and not any(tk[x].d == "case" for x in hij.get(c.i, ())) and (c.u == "PROPN" or any(tk[x].d == "det" for x in hij.get(c.i, ())))]
            if pre and not any(c.d == "obj" and c.i < v.i and c.u in ("NOUN", "PROPN") for c in hs):
                pre.sort(key=lambda c: -c.i)
                pre[0].d = "nsubj"
                cambio = True
        # ---- «Nombre, cargo de X, Nombre, cargo de Y»: cada cargo es aposicion del nombre que lo precede --------------------------------------
        segs, a = [], 0
        for i, t in enumerate(tk):
            if t.f in (",", ";", ":"):
                segs.append((a, i - 1))
                a = i + 1
        if a <= n - 1:
            segs.append((a, n - 1))
        segs = [(x, y) for x, y in segs if x <= y]
        pares = []
        for k in range(1, len(segs)):
            a2, b2 = segs[k]
            while b2 > a2 and tk[b2].u == "PUNCT":
                b2 -= 1
            if tk[segs[k][0] - 1].f != ",":
                continue
            j = a2
            while j <= b2 and tk[j].u in ("DET", "ADJ"):
                j += 1
            if j > b2 or tk[j].u != "NOUN" or tk[j].nl in TIEMPO or tk[j].nl in MESES or any(tk[x].u in ("VERB", "AUX") and not (tk[x].d in ("acl", "acl:relcl")) for x in range(a2, b2 + 1)):
                continue
            e = segs[k - 1][1]
            while e >= segs[k - 1][0] and tk[e].u == "PUNCT":
                e -= 1
            if e < segs[k - 1][0] or not (tk[e].u == "PROPN" or self._romano(e)):
                continue
            s_ = e
            while s_ - 1 >= segs[k - 1][0] and (tk[s_ - 1].u == "PROPN" or self._romano(s_ - 1)
                                               or (tk[s_ - 1].nl in ("de", "del") and s_ - 2 >= segs[k - 1][0] and tk[s_ - 2].u == "PROPN")):
                s_ -= 1
            raiz_rol = next((x for x in range(a2, b2 + 1) if tk[x].u == "NOUN" and (tk[x].h < a2 or tk[x].h > b2 or tk[x].h < 0)), j)
            pares.append((s_, raiz_rol, (a2, b2)))
        def _desc(x):
            return set(self.sub(x))
        for s_, r_, _ in pares:
            if (tk[r_].h != s_ or tk[r_].d != "appos") and s_ not in _desc(r_):
                tk[r_].h, tk[r_].d = s_, "appos"
                cambio = True
        if len(pares) >= 2:
            primero = pares[0][0]
            for s_, _, _ in pares[1:]:
                if any(a3 <= tk[s_].h <= b3 for _, _, (a3, b3) in pares) and s_ != primero and primero not in _desc(s_):
                    tk[s_].h, tk[s_].d = primero, "conj"
                    cambio = True
        return cambio

    # ---- arbol -----------------------------------------------------------------------------------------------------------------
    def sub(self, i: int, saltar=lambda t: False) -> List[int]:
        out, pila, vistos = [], [i], set()
        while pila:
            x = pila.pop()
            if x in vistos:
                continue
            vistos.add(x)
            out.append(x)
            for c in self.hij.get(x, []):
                if not saltar(self.tok[c]):
                    pila.append(c)
        return sorted(out)

    def np(self, i: int) -> Tuple[int, int]:
        """Sintagma nominal que cuelga de i, sin oraciones de relativo, coordinaciones ni incisos."""
        def saltar(t):
            if t.d == "conj" and t.u == "PROPN" and t.h >= 0 and self.tok[t.h].u == "PROPN" and t.i >= 2 and self.tok[t.i - 1].nf in ("y", "e", ",") \
                    and self.tok[t.i - 1].d in ("cc", "punct") and self.tok[t.i - 2].u == "PROPN" and not any(self.tok[k].u in ("VERB", "AUX") for k in range(i, t.i)):
                return False                                                                           # «Castilla y León», «Ávila, Béjar y Zamora»: la coordinacion de nombres propios es un solo sintagma
            if t.d.startswith(("acl", "advcl", "conj", "cc", "parataxis", "punct", "mark", "xcomp", "ccomp")):
                return True
            return t.d == "appos" and t.i > 0 and self.tok[t.i - 1].f == ","
        ix = self.sub(i, saltar)
        a, b = ix[0], ix[-1]
        while b > a and self.tok[b].u == "PUNCT":
            b -= 1
        while a < b and self.tok[a].u == "PUNCT":
            a += 1
        return a, b

    def texto_span(self, a: int, b: int) -> str:
        toks = self.tok[a:b + 1]
        piezas, k = [], 0
        while k < len(toks):
            f = toks[k].f
            sig = toks[k + 1].f.lower() if k + 1 < len(toks) else ""
            if f.lower() in ("de", "a") and sig == "el":
                piezas.append(r"(?:" + re.escape(f) + r"\s+el|" + ("del" if f.lower() == "de" else "al") + ")")
                k += 2
                continue
            piezas.append(re.escape(f))
            k += 1
        m = re.search(r"\s*".join(piezas), self.texto, re.I) if piezas else None
        if m:
            return m.group(0)
        return detok([t.f for t in toks])

    # ---- menciones de entidades --------------------------------------------------------------------------------------------------
    def _es_prop(self, i: int) -> bool:
        t, n = self.tok[i], len(self.tok)
        if t.u == "PROPN":
            return True
        if self._romano(i):
            return True                                                                                   # «Alfonso X», «Felipe VI»: el numeral romano es parte del nombre
        if t.u in ("X", "NOUN", "ADJ") and len(t.f) >= 2 and t.f.isupper() and not any(c.isdigit() for c in t.f) and t.nf not in ("la", "el"):
            return True
        if t.u == "NOUN" and i > 0 and i + 1 < n and t.f[:1].isupper() and not t.f.isupper() and self.tok[i + 1].u == "PROPN" and self.tok[i + 1].f[:1].isupper() \
                and self.tok[i - 1].f not in (".", ":", ";", "—", "-", "«", '"', "(", "¿", "[") and self.tok[i - 1].u != "PUNCT":
            return True                                                                                   # «Cabo Verde», «Costa Rica»: el sustantivo con mayuscula pegado a un nombre propio es parte del nombre
        if len(t.f) == 1 and t.f.isupper() and i + 1 < n and self.tok[i + 1].f == ".":                  # iniciales: F. C. Barcelona
            der = i + 2 < n and (self.tok[i + 2].u in ("PROPN", "X") or (len(self.tok[i + 2].f) == 1 and self.tok[i + 2].f.isupper()))
            izq = i > 0 and (self.tok[i - 1].u == "PROPN" or self.tok[i - 1].f == ".")
            return bool(der or izq)
        return False

    def menciones(self):
        n, i, out = len(self.tok), 0, []
        while i < n:
            if not self._es_prop(i) or (self.tok[i].u != "PROPN" and i == 0 and self.tok[i].f.lower() in STOPQ):
                i += 1
                continue
            j = i
            while True:
                k = j + 1
                if k >= n:
                    break
                if self._es_prop(k):
                    j = k
                    continue
                if self.tok[k].f == "-" and k + 1 < n and self._es_prop(k + 1) and self.tok[j].u == "PROPN":
                    j = k + 1
                    continue
                if self.tok[k].f == "." and (_es_inicial(self.tok[j], self.tok[k]) or len(self.tok[j].f) == 1) and k + 1 < n and self._es_prop(k + 1):
                    j = k
                    continue
                if self.tok[k].nf in ("el", "la", "los", "las") and j > i and len(self.tok[j].nf) > 2 and not self._romano(j) and _palabra_comun(self.tok[j].nf) and self.tok[j].nf not in MESES:
                    break                                                                                 # «Durante la Edad Media el Ebro fue…»: el articulo tras un adjetivo corriente abre otro sintagma
                if self.tok[k].nf in CONEC_NOMBRE:
                    m = k
                    while m < n and self.tok[m].nf in CONEC_NOMBRE and m - k < 2:
                        m += 1
                    if m < n and self._es_prop(m):
                        j = m
                        continue
                break
            toks = self.tok[i:j + 1]
            def _val(t):
                return t.nf not in CONEC and (len(t.nf) > 1 or self._romano(t.i)) and not t.nf.isdigit() and t.f != "."
            clave = frozenset(t.nf for t in toks if _val(t))
            nums = [t for t in toks if t.nf.isdigit()]
            if clave and not (nums and len(toks) == len(nums)):
                orden = tuple(t.nf for t in toks if _val(t))
                out.append((i, j, clave, detok([t.f for t in toks]), orden))
            i = j + 1
        self.ment = out


def detok(formas: List[str]) -> str:
    s = ""
    for k, f in enumerate(formas):
        if not s:
            s = f
        elif f in ",.;:)»!?%" or s[-1] in "(«¿¡" or (f == "-" and s[-1].isalnum()) or s.endswith("-") and f[:1].isalnum() and k > 0 and formas[k - 1] == "-":
            s += f
        else:
            s += " " + f
    s = re.sub(r"\bde el\b", "del", s)
    s = re.sub(r"\ba el\b", "al", s)
    return s


# ====================================================== indice ============================================================================


class Indice:
    def __init__(self, textos: List[dict]):
        self.n_textos = len(textos)
        self.fr = [Frase(e, k) for k, e in enumerate(textos)]
        for f in self.fr:
            f.menciones()
        self._familias()
        self._idf()
        self._sujetos()

    # ---- familias: «Lamine», «Yamal», «Lamine Yamal» -> la misma entidad ---------------------------------------------------------
    def _familias(self):
        cuenta: Counter = Counter()
        sup: Dict[frozenset, Counter] = defaultdict(Counter)
        orden: Dict[frozenset, Counter] = defaultdict(Counter)
        for f in self.fr:
            for _, _, k, s_, o_ in f.ment:
                cuenta[k] += 1
                sup[k][s_] += 1
                orden[k][o_] += 1
        comunes_ini = set()
        conector = {k: any(re.search(r"\b(?:de|del|la|las|los|el)\b", s_) for s_ in sup[k]) for k in cuenta}
        ord_k = {k: orden[k].most_common(1)[0][0] for k in cuenta}

        def sub_difuso(a, b):
            return all(any(x == y or _prefijo(x, y) for y in b) for x in a)

        def encaja(a, b):
            """El nombre corto a es el apellido o el nombre de pila del largo b («Yamal» en «Lamine Yamal»), no «España» dentro de «Supercopa de España».
            Tambien «Copa del Mundo» y «Copa Mundial de Futbol» (mundo ~ mundial): cada palabra del corto tiene su par en el largo."""
            if a == b:
                return False
            if a < b:
                if len(a) >= 2:
                    return True
                (x,) = tuple(a)
                o = ord_k[b]
                if not o or len(o) > 3:
                    return False
                if not conector[b]:
                    return o[-1] == x or o[0] == x
                return o[-1] == x and cuenta[a] <= 3 * cuenta[b] and o[0] not in comunes_ini
            if len(a) >= 2 and len(a) <= len(b) and sub_difuso(a, b):
                return len(a) < len(b) or cuenta[a] < cuenta[b] or (cuenta[a] == cuenta[b] and sorted(a) < sorted(b))
            return False
        claves = sorted(cuenta, key=lambda k: (-len(k), -cuenta[k]))
        raiz_de: Dict[frozenset, frozenset] = {}

        def resolver(a, pila=()):
            if a in raiz_de:
                return raiz_de[a]
            sups = sorted((b for b in claves if b not in pila and encaja(a, b)), key=lambda b: -cuenta[b])
            if not sups:
                raiz_de[a] = a
            else:
                rs = [resolver(b, pila + (a,)) for b in sups]
                if len(sups) == 1 or cuenta[sups[0]] >= 2 * cuenta[sups[1]] or len(set(rs)) == 1:
                    raiz_de[a] = rs[0]
                else:
                    raiz_de[a] = a
            return raiz_de[a]
        for a in claves:
            resolver(a)
        self.cuenta, self.raiz_de = cuenta, raiz_de
        self.fam_id: Dict[frozenset, str] = {r: "+".join(sorted(r)) for r in set(raiz_de.values())}
        self.disp: Dict[str, str] = {}
        self.tokens_fam: Dict[str, Set[str]] = defaultdict(set)
        self.claves_fam: Dict[str, List[frozenset]] = defaultdict(list)
        disp_c: Dict[str, Counter] = defaultdict(Counter)
        for k, r in raiz_de.items():
            fid = self.fam_id[r]
            self.tokens_fam[fid] |= set(k)
            self.claves_fam[fid].append(k)
            for s_, c in sup[k].items():
                disp_c[fid][s_] += c
        for fid, c in disp_c.items():
            self.disp[fid] = max(c, key=lambda s_: (len(s_.split()), c[s_]))
        self.n_fam = Counter()
        for k, r in raiz_de.items():
            self.n_fam[self.fam_id[r]] += cuenta[k]
        n_prop: Counter = Counter()
        n_com: Counter = Counter()
        for f in self.fr:
            dentro = set()
            for a, b, k, _, _ in f.ment:
                dentro.update(range(a, b + 1))
                for t in k:
                    n_prop[t] += 1
            for t in f.tok:
                if t.i not in dentro and t.u not in ("PROPN", "PUNCT") and not t.nf.isdigit():
                    n_com[t.nf] += 1
        self.n_prop, self.n_com = n_prop, n_com
        self.vocab_all: Dict[str, Set[str]] = defaultdict(set)
        for fid, toks in self.tokens_fam.items():
            for t in toks:
                self.vocab_all[t].add(fid)
        self.vocab_ent: Dict[str, Set[str]] = defaultdict(set)         # token normalizado -> familias que lo llevan
        for fid, toks in self.tokens_fam.items():
            for t in toks:
                if 3 * n_prop[t] >= n_com[t]:                               # «goles» o «partidos» dentro de una cabecera de tabla, «fisica» en «Nobel de Fisica», no son nombres
                    self.vocab_ent[t].add(fid)
        for f in self.fr:
            for _, _, k, _, _ in f.ment:
                f.fams.add(self.fam_id[raiz_de[k]])
        # gentilicios: «los portugueses», «españoles», «barcelonista» son menciones de Portugal, España, Barcelona (nombre de un solo token)
        simples = {}
        for fid, d in self.disp.items():
            if len(d.split()) == 1:
                tn = nrm(d)
                if len(tn) >= 6 and tn.isalpha():
                    simples.setdefault(tn[:5], []).append((tn, fid))
        if simples:
            for f in self.fr:
                dentro = set()
                for a, b, _, _, _ in f.ment:
                    dentro.update(range(a, b + 1))
                for t in f.tok:
                    if t.u not in ("ADJ", "NOUN", "PROPN") or len(t.nf) < 6 or not t.nf.isalpha() or (t.i in dentro and t.u == "NOUN"):      # «Seleccion Española»: el gentilicio dentro de un nombre tambien nombra al pais
                        continue
                    for tn, fid in simples.get(t.nf[:5], ()):
                        if tn == t.nf:
                            continue
                        p_ = 0
                        while p_ < min(len(tn), len(t.nf)) and tn[p_] == t.nf[p_]:
                            p_ += 1
                        if p_ >= max(5, 0.75 * len(tn)) and abs(len(t.nf) - len(tn)) <= 5:
                            f.fams.add(fid)
        self._tema_nominal()

    def _tema_nominal(self):
        """Textos cuyo protagonista no es un nombre propio sino un sustantivo («El leon es un mamifero...», «El ornitorrinco es...»): ese sustantivo
        hace de entidad, para que las frases que hablan de el sin nombrarlo y las preguntas que lo nombran se encuentren."""
        por_doc: Dict[int, List[Frase]] = defaultdict(list)
        for f in self.fr:
            por_doc[f.doc].append(f)
        for d, fs in por_doc.items():
            fs.sort(key=lambda f: f.k)
            suj = None
            for f in fs[:2]:
                suj = next((t for t in f.tok if t.d.startswith("nsubj") and t.u == "NOUN" and len(t.nl) >= 4 and t.nl not in LIGEROS), None)
                if suj:
                    break
            if suj is None:
                continue
            formas = {t.nf for f in fs for t in f.tok if t.u == "NOUN" and t.nl == suj.nl}
            con = [f for f in fs if any(t.u == "NOUN" and t.nl == suj.nl for t in f.tok)]
            if len(con) < max(2, min(4, 0.15 * len(fs))) or len(con) < 0.03 * len(fs):
                continue
            fid = "t:" + suj.nl + (":%d" % d if len(por_doc) > 1 else "")
            self.disp[fid] = suj.f.lower()
            self.tokens_fam[fid] = set(formas)
            self.claves_fam[fid] = [frozenset({x}) for x in formas]
            self.n_fam[fid] = len(con)
            self.fam_id[frozenset({"~" + fid})] = fid
            for x in formas:
                self.vocab_ent[x].add(fid)
            for f in con:
                f.fams.add(fid)

    def especifica(self, e: str) -> bool:
        """Entidad poco repetida (no el protagonista): si la pregunta la nombra, la frase debe tratarla de verdad."""
        d = getattr(self, "_df_fam", None)
        if d is None:
            d = Counter(x for f in self.fr for x in f.fams)
            self._df_fam = d
        return d.get(e, 0) <= max(3.0, 0.12 * len(self.fr))

    def familia_de(self, k: frozenset) -> str:
        return self.fam_id[self.raiz_de[k]]

    def _idf(self):
        N = max(1, len(self.fr))
        df: Counter = Counter()
        dfr: Counter = Counter()
        self.comunes: Set[str] = set()
        self.formas: Dict[str, str] = {}
        for f in self.fr:
            for w in f.lem:
                df[w] += 1
            for w in f.raices:
                dfr[w] += 1
            for t in f.tok:
                if t.u not in ("PROPN", "PUNCT"):
                    self.comunes.add(t.nf)
                    self.comunes.add(t.nl)
                if t.u in ("VERB", "NOUN", "ADJ", "AUX"):
                    self.formas.setdefault(t.nf, t.nl)
        self.idf = {w: math.log((N + 1) / (c + 0.5)) + 0.3 for w, c in df.items()}
        self.idf_r = {w: math.log((N + 1) / (c + 0.5)) + 0.3 for w, c in dfr.items()}
        self.idf_max = max(list(self.idf.values()) + [1.0])
        self.vocab_lem = set(df)

    # ---- sujeto omitido y posesivos: «Es un delantero zurdo» se dice de quien venia siendo el protagonista ---------------------------
    def _sujetos(self):
        por_doc: Dict[int, List[Frase]] = defaultdict(list)
        for f in self.fr:
            por_doc[f.doc].append(f)
        self.protagonista: Dict[int, Optional[str]] = {}
        for d, fs in por_doc.items():
            fs.sort(key=lambda f: f.k)
            def _orden(f):                                                   # orden de aparicion en la frase (los conjuntos no tienen orden estable)
                vistos = []
                for a_, b_, k_, _, _ in f.ment:
                    x_ = self.familia_de(k_)
                    if x_ in f.fams and x_ not in vistos:
                        vistos.append(x_)
                return vistos + sorted(f.fams - set(vistos))
            c = Counter(x for f in fs for x in _orden(f))
            tema = c.most_common(1)[0][0] if c else None
            self.protagonista[d] = tema
            for f in fs:
                sujeto_fam, prodrop = None, False
                for r in (t for t in f.tok if t.h < 0 and t.i < f.n_main):
                    hs = f.hij.get(r.i, [])
                    explicito = any(f.tok[c_].d.startswith(("nsubj", "csubj")) for c_ in hs)
                    for c_ in hs:
                        if f.tok[c_].d.startswith(("nsubj", "csubj")):
                            for a, b, k, _, _ in f.ment:
                                if a <= c_ <= b:
                                    sujeto_fam = self.familia_de(k)
                    fin = r.u == "VERB" and not re.search(r"(?:ndo|ar|er|ir|ado|ido|ada|ida|ados|idos)$", r.nf)
                    if r.u in ("VERB", "AUX", "ADJ") and not explicito and fin:
                        prodrop = True
                pos = any(t.nf in ("su", "sus", "le", "lo", "la", "les") and t.u in ("DET", "PRON") for t in f.tok)
                if tema and (prodrop or pos):
                    peso = 0.85 if pos else 0.7
                    for x in {tema, self.protagonista[d]} - {None}:
                        f.impl.add(x)
                        f.impl_w[x] = max(f.impl_w.get(x, 0), peso)
                f.suj = sujeto_fam
                if sujeto_fam:
                    tema = sujeto_fam
                f.impl -= f.fams
            tema_par: Dict[Tuple[int, str], Set[str]] = {}                       # tema del parrafo: lo que nombra su primera frase y lo que se repite en varias
            _grupo: Dict[Tuple[int, str], List[Frase]] = defaultdict(list)
            for f in fs:
                if f.par:
                    _grupo[(f.par, f.sec)].append(f)
            for kg, gr in _grupo.items():
                cnt = Counter(x for g in gr for x in g.fams)
                tema_par[kg] = set(gr[0].fams) | {x for x, n_ in cnt.items() if n_ >= 3}
            for j, f in enumerate(fs):                                          # contexto del parrafo: lo que dicen las frases de al lado, con menos peso cuanto mas lejos
                for jj, g in enumerate(fs):
                    if g is f:
                        continue
                    dist = abs(jj - j)
                    mismo = (f.par and g.par == f.par) or (not f.par and dist <= 2)
                    if not mismo or g.sec != f.sec:
                        continue
                    w = 0.55 / (1 + 0.15 * (dist - 1))
                    for x in g.fams | g.impl:
                        if x not in f.fams and x not in f.impl:
                            f.ctx_fams[x] = max(f.ctx_fams.get(x, 0), max(w, 0.6) if x in tema_par.get((f.par, f.sec), ()) else w)
                    for x in g.lem:
                        f.ctx_lem[x] = max(f.ctx_lem.get(x, 0), w)
                    for x in g.raices:
                        f.ctx_raices[x] = max(f.ctx_raices.get(x, 0), w)


def indice(mem) -> Optional[Indice]:
    tx = getattr(mem, "textos", None)
    if not tx:
        return None
    ant = getattr(mem, "_ind_lec", None)
    if ant is not None and ant.n_textos == len(tx):
        return ant
    ind = Indice(tx)
    try:
        mem._ind_lec = ind
    except Exception:                                                          # noqa
        pass
    return ind


# ====================================================== analisis de la pregunta ==========================================================
class Clave:
    __slots__ = ("nl", "kind", "w", "alts", "rz")

    def __init__(self, nl, kind, w, alts=()):
        self.nl, self.kind, self.w, self.alts, self.rz = nl, kind, w, tuple(alts), raiz(nl)


class Q:
    def __init__(self, raw):
        self.raw = raw
        self.tipo = "si_no"
        self.prep = ""
        self.x = ""
        self.ents: List[str] = []
        self.ents_ctx = False
        self.debiles: Set[str] = set()
        self.corr: List[Tuple[str, str]] = []
        self.claves: List[Clave] = []
        self.verbo: Optional[Clave] = None
        self.foco: Optional[Clave] = None
        self.desconocidos: List[str] = []
        self.toks: List[Tuple[str, str, str]] = []


def _palabra_comun(w: str) -> bool:
    """La palabra es un sustantivo/adjetivo corriente del idioma y no un topónimo o nombre: el lexico la da con sinonimos propios."""
    return len(_sinonimos(w, "NOUN")) >= 2


def _lex_conoce(w: str) -> bool:
    try:
        from . import lexico
        return lexico.conoce(w)
    except Exception:                                                                # noqa
        return False


GENERICOS = LIGEROS | {"tener", "dar", "poner", "tomar", "pasar", "salir", "venir", "llevar", "sacar", "decir", "ver", "mover", "aparecer", "tocar", "pedir", "traer", "meter", "cambiar",
                       "producir", "presentar", "mostrar", "formar", "obtener", "colocar", "echar", "ocupar", "acabar", "terminar", "empezar", "comenzar", "salirse", "tratar", "usar", "utilizar"}


_GRUPOS_VERBO = [
    "ganar obtener conseguir recibir lograr vencer derrotar triunfar", "morir fallecer perecer expirar sucumbir", "fundar crear establecer instituir", "descubrir hallar encontrar detectar",
    "escribir redactar publicar componer", "marcar anotar convertir", "rechazar declinar desestimar descartar", "nombrar designar elegir escoger", "crecer aumentar incrementar",
    "vivir habitar residir", "cazar capturar atrapar", "comer alimentarse nutrirse devorar ingerir", "llamar denominar apodar bautizar", "empezar comenzar iniciar",
    "terminar acabar finalizar concluir", "abrir inaugurar", "construir edificar levantar erigir", "inventar idear desarrollar", "contener guardar conservar custodiar atesorar", "alojar acoger hospedar albergar",
    "situar ubicar localizar", "proteger defender resguardar", "sustituir reemplazar relevar suplir", "decir afirmar declarar manifestar asegurar", "pensar creer opinar",
    "estudiar cursar", "tener contar poseer", "casar desposar", "matar asesinar", "dirigir liderar capitanear", "participar intervenir", "ayudar asistir auxiliar", "enfermar padecer sufrir",
]
MEDIDA_DE = {"medir": ["longitud", "altura", "extension", "tamano", "anchura", "profundidad", "dimension", "largo", "alto", "ancho"], "pesar": ["peso", "masa"],
             "costar": ["coste", "precio", "valor", "importe"], "durar": ["duracion", "tiempo"], "tardar": ["tiempo", "duracion"], "cobrar": ["sueldo", "salario"],
             "habitar": ["habitantes", "poblacion"], "poblar": ["habitantes", "poblacion"]}
EQUIV: Dict[str, List[str]] = {}
for _g in _GRUPOS_VERBO:                                                              # equivalencias corrientes del idioma (no de ningun texto): «ganar un premio» ~ «recibir/obtener un premio»
    _ws = _g.split()
    for _w in _ws:
        EQUIV[_w] = [x for x in _ws if x != _w]
for _w, _al in MEDIDA_DE.items():                                                      # «cuanto mide» se contesta con «su longitud es de…»
    EQUIV[_w] = EQUIV.get(_w, []) + _al


def _sinonimos(w: str, pos: str) -> List[str]:
    base = list(EQUIV.get(w, ())) if pos == "VERB" else []
    try:
        from . import lexico
        out = [nrm(x) for x in lexico.sinonimos(w, {"VERB": "v", "NOUN": "n", "ADJ": "a"}.get(pos)) if " " not in x]
        wn = [x for x in out if x not in GENERICOS and x != w and x not in base]                # «nacer»→«tener», «jugar»→«mover»: sinonimos tan genericos que casan con cualquier frase
        return (base if base else wn[:4])[:8]                                      # lo curado manda; WordNet solo cuando no hay grupo (y entonces, pocos)
    except Exception:                                                                # noqa
        return base


def _filas_pregunta(raw: str, parser) -> List[Tuple[str, str, str]]:
    rows = []
    if parser is not None and hasattr(parser, "tree"):
        try:
            rows = parser.tree(raw) or []
        except Exception:                                                            # noqa
            rows = []
    if rows:
        out_ = []
        for r in rows:
            if r[1] == "PUNCT":
                continue
            if r[0].lower() == "está" and r[1] in ("DET", "PRON", "ADJ", "NOUN", "X"):
                out_.append(("esta", "VERB", "estar"))                           # «¿Está Machu Picchu en Chile?»: con tilde es el verbo, no el demostrativo
                continue
            out_.append(_sin_enclitico(nrm(r[0]), r[1], nrm(r[4] or r[0])))
        return out_
    return [(nrm(w), "X", nrm(w)) for w in re.findall(r"[\wáéíóúüñ]+", raw.lower())]


_ENCL = re.compile(r"^([a-z]{3,}(?:ar|er|ir))(lo|la|los|las|le|les|se|me|te)$")


def _sin_enclitico(f: str, u: str, l: str) -> Tuple[str, str, str]:
    """«ficharlo» -> verbo «fichar»: el pronombre pegado al infinitivo no es parte de la palabra."""
    m = _ENCL.match(f)
    if m and u != "PROPN" and not f.endswith(("ase", "ese", "ose")) and (u in ("VERB", "X", "NOUN", "ADJ", "AUX") or l == f) \
            and (_lex_conoce(m.group(1)) or (m.group(2) in ("lo", "la", "los", "las", "le", "les", "se") and m.group(1).endswith("ar") and len(m.group(1)) >= 6)):
        return (m.group(1), "VERB", m.group(1))
    return (f, u, l)


def es_peticion(raw: str) -> bool:
    qn = " ".join(re.findall(r"[a-z0-9]+", nrm(raw)))
    return any(rx.match(qn) for rx in PERFIL_RX[1:4])


_WH_INI = re.compile(r"^(?:y |pero |entonces |oye |dime |sabes )?(?:(?:a|de|en|con|contra|por|para|desde|hasta|sobre|segun|hacia|entre|ante)(?: el| la| los| las)? )?"
                     r"(?:quien|quienes|que|cual|cuales|cuanto|cuanta|cuantos|cuantas|cuando|donde|adonde|como|por que|porque|para que)\b")


def parece_pregunta(raw: str) -> bool:
    """Pregunta escrita sin signos: empieza (tras una preposicion opcional) por una palabra interrogativa."""
    if "?" in raw or "\u00bf" in raw:
        return True
    qn = " ".join(re.findall(r"[a-z0-9]+", nrm(raw)))
    if not qn or len(qn.split()) > 25:
        return False
    return bool(_WH_INI.match(qn))


DESCRIPTIVA = re.compile(r"\b(?:primer[oa]?s?|ultim[oa]s?|unic[oa]s?|segund[oa]s?|tercer[oa]?s?|mejor(?:es)?|peor(?:es)?|mas|menos)\b")


def _perfil_x(qs: str) -> Optional[str]:
    for i, rx in enumerate(PERFIL_RX):
        m = rx.match(qs)
        if m:
            x = m.group("x")
            if i == 0 and (DESCRIPTIVA.search(x) or re.search(r"^\S+(?:\s+\S+){1,2}\s+(?:en|con|que|cuando|donde|para|por)\s", x)):          # «quien fue la primera mujer profesora en ...» describe, no pide un perfil
                return None
            return x
    return None


def buscar_ents(ind: Indice, toks: List[Tuple[str, str, str]], saltar: Set[int] = frozenset(), caps: Set[str] = frozenset()):
    """Familias de entidades que nombra la pregunta, aunque vengan a medias («yamal»), en minusculas o con errata («tamal»)."""
    res: Dict[int, str] = {}
    corr: List[Tuple[str, str]] = []
    desconocidos: List[str] = []
    ve = ind.vocab_ent
    if caps:                                                                     # una palabra escrita con mayuscula en mitad de la pregunta se toma por nombre
        ve = dict(ve)
        for t in caps:
            if t not in ve and t in ind.vocab_all:
                ve[t] = ind.vocab_all[t]
    for i, (nf, u, l) in enumerate(toks):
        if i in saltar or nf in STOPQ or nf in WH or len(nf) < 2 or nf.isdigit():
            continue
        v = None
        for c in (nf, l, nf[:-1] if nf.endswith("s") else "", nf[:-2] if nf.endswith("es") else ""):
            if c and c in ve:
                v = c
                break
        if v is None and nf not in ind.comunes and l not in ind.comunes and len(nf) >= 4:
            tope = 1 if len(nf) < 8 else 2
            mejor = None
            for e in ve:
                if len(e) < 4 or (len(e) == 4 and _lex_conoce(nf)):
                    continue
                d = damerau(nf, e, tope)
                if d <= tope and (mejor is None or d < mejor[0] or (d == mejor[0] and ind.n_fam[next(iter(ve[e]))] > ind.n_fam[next(iter(ve[mejor[1]]))])):
                    mejor = (d, e)
            if mejor and (not _lex_conoce(nf) or max(ind.n_fam[f] for f in ve[mejor[1]]) >= 3):
                v = mejor[1]
                corr.append((nf, v))
        if v is not None:
            res[i] = v
        elif nf not in ind.comunes and l not in ind.comunes and nf not in ind.formas and not _lex_conoce(nf) and not _lex_conoce(l) and len(nf) >= 3 \
                and not (len(l) >= 5 and any(_difuso(l, w) for w in ind.vocab_lem)):
            desconocidos.append(nf)
    qset = set(res.values())
    cand: Dict[str, float] = {}
    for fid, keys in ind.claves_fam.items():
        best = 0.0
        for K in keys:
            hit = len(K & qset)
            if hit:
                best = max(best, hit + (0.6 if hit == len(K) else 0.0) - (0.0 if len(K) == 1 else 0.0))
        if best:
            parcial = not any(K <= qset for K in keys)
            if parcial and (desconocidos or any(len(ve[t]) > 2 for t in qset)):
                continue
            if parcial and any((t not in caps or len(ve.get(t, ())) >= 2) and ind.n_com.get(t, 0) > 0 and ind.n_prop.get(t, 0) < 3 * ind.n_com.get(t, 0) for K in keys for t in (K & qset)):
                continue                                                         # «fisica» suelta no es «Nobel de Fisica»: tambien es una palabra comun
            cand[fid] = best
    for fid in list(cand):
        if not any(K <= qset for K in ind.claves_fam[fid]):
            hit = set().union(*[K & qset for K in ind.claves_fam[fid]])
            if any(g != fid and any(K <= qset and hit <= K for K in ind.claves_fam[g]) for g in cand):
                del cand[fid]
    hits = {fid: set().union(*[K & qset for K in ind.claves_fam[fid]]) for fid in cand}
    for fid in list(cand):                                                       # «Marie Curie» no es tambien «Pierre Curie» (basta que se llame «Curie» a secas)
        if any(g != fid and hits[fid] < hits[g] for g in cand):
            del cand[fid]
    if not cand:
        return [], corr, desconocidos, res
    top = max(cand.values())
    fams = sorted((f for f, s in cand.items() if s >= max(1.0, top * 0.55)), key=lambda f: (-cand[f], -ind.n_fam[f]))[:4]
    if len(fams) >= 2:                                      # «Cervantes» a secas: si una familia aparece mucho mas que la otra que comparte esa unica palabra, es de quien se habla
        for fa in list(fams):
            otros = [g for g in fams if g != fa and hits.get(g) == hits.get(fa) and len(hits.get(fa, ())) == 1 and all(t in caps for t in hits.get(fa, ()))]       # solo si la palabra va con mayuscula en la pregunta: «trofeo» suelto no es nombre
            pres_ = getattr(ind, "_pres_fam", None)
            if pres_ is None:
                pres_ = Counter(x for f_ in ind.fr for x in (f_.fams | f_.impl))
                ind._pres_fam = pres_
            if otros and all(pres_[fa] >= 2 * max(1, pres_[g]) for g in otros):
                fams = [g for g in fams if g == fa or g not in otros]
    # una familia cuyos tokens ya cubre otra mas completa de la misma pregunta no cuenta dos veces
    out = []
    for f in fams:
        if not any(g != f and ind.tokens_fam[f] < ind.tokens_fam[g] and cand[g] >= cand[f] for g in fams):
            out.append(f)
    return out, corr, desconocidos, res


def analizar(ind: Indice, raw: str, parser=None, ctx: Optional[List[str]] = None) -> Optional[Q]:
    q = Q(raw)
    toks = _filas_pregunta(raw, parser)
    if not toks:
        return None
    if toks and toks[0][1] in ("NOUN", "X", "ADJ"):                    # «¿Piso Collins la Luna?»: el verbo inicial sin sujeto delante se lee como sustantivo
        m_ = re.match(r"[¿¡\s]*([A-Za-zÁÉÍÓÚáéíóúñÑ]+)", raw)
        w0 = m_.group(1) if m_ else ""
        if w0 and nrm(w0) == toks[0][0] and re.search(r"(?:[óé]|[ií][óé]|aron|ieron|aba|aban|[ií]a|[ií]an)$", w0.lower()) and len(toks) >= 3 and toks[1][1] in ("PROPN", "DET") and nrm(w0) not in ind.n_prop:
            base = nrm(w0)
            cand = []
            if re.search(r"(?:o|aron|aba|aban)$", base):
                cand = [re.sub(r"(?:o|aron|aba|aban)$", "ar", base)]
            elif re.search(r"(?:io|ieron|ia|ian)$", base):
                st_ = re.sub(r"(?:io|ieron|ia|ian)$", "", base)
                cand = [st_ + "er", st_ + "ir"]
            lem_ = next((c_ for c_ in cand if c_ in ind.vocab_lem), cand[0] if cand else base)
            toks = [(toks[0][0], "VERB", lem_)] + toks[1:]
    q.toks = toks
    qs = " ".join(t[0] for t in toks)
    qs = re.sub(r"\bde el\b", "del", qs)
    qs = re.sub(r"\ba el\b", "al", qs)
    caps = {nrm(w_) for w_ in re.findall(r"\w+", raw)[1:] if w_[:1].isupper()}
    ents, corr, desc, pos_ent = buscar_ents(ind, toks, caps=caps)
    q.ents, q.corr, q.desconocidos = ents, corr, desc
    for e in ents:                                                               # entidad que solo se nombra con una palabra tambien comun («fisica» en «licenciatura en fisica»): vale menos
        toks_q = {res_ for res_ in pos_ent.values() if res_ in ind.tokens_fam.get(e, ())}
        cap = any(nrm(w_) in toks_q and w_[:1].isupper() for w_ in re.findall(r"\w+", raw)[1:])                       # escrito con mayuscula: el usuario lo da por nombre
        if not cap and len(toks_q) == 1 and all(ind.n_com.get(t, 0) > 0 and ind.n_prop.get(t, 0) < 3 * ind.n_com.get(t, 0) for t in toks_q) and len(ind.tokens_fam.get(e, ())) > 1:
            q.debiles.add(e)
        elif not cap and len(toks_q) == 1 and len(ind.tokens_fam.get(e, ())) == 1 and all(ind.n_prop.get(t, 0) <= 2 and _lex_conoce(t) and not ind.n_com.get(t, 0) for t in toks_q) \
                and all(_palabra_comun(t) for t in toks_q):
            q.debiles.add(e)                                                     # «familia» a secas es la palabra comun aunque el texto solo la escriba con mayuscula en «la Familia real»
    if re.search(r"\bcientific", qs):                                           # «como se llama cientificamente»: el adverbio no es un tema desconocido
        q.desconocidos = [d for d in desc if not d.startswith("cientific")]
    # ---- tipo ---------------------------------------------------------------------------------------------------------------------
    x = _perfil_x(qs)
    if x is not None:
        q.tipo, q.x = "perfil", x
    elif len(toks) <= 6 and ents and not any(u in ("VERB", "AUX") for _, u, _ in toks) and not any(n in WH for n, _, _ in toks):
        q.tipo, q.x = "perfil", qs
    else:
        nf = [t[0] for t in toks]
        for i in range(min(5, len(nf))):
            w = nf[i]
            prev = nf[i - 1] if i > 0 else ""
            sig = nf[i + 1] if i + 1 < len(nf) else ""
            if w in ("quien", "quienes"):
                q.tipo, q.prep = "quien", prev if prev in PREPS else ""
            elif w == "cuando":
                q.tipo, q.prep = "cuando", prev if prev in ("desde", "hasta") else ""
            elif w in ("donde", "adonde"):
                q.tipo, q.prep = "donde", prev if prev in ("de", "desde", "hacia", "por", "a") else ("a" if w == "adonde" else "")
            elif w in ("cuanto", "cuanta", "cuantos", "cuantas"):
                q.tipo = "cuanto"
            elif w == "por" and sig == "que":
                q.tipo = "porque"
            elif w == "para" and sig == "que":
                q.tipo = "para_que"
            elif w == "que" and sig in ("significa", "significan", "significaba", "quiere", "quieren"):
                q.tipo = "significado"
            elif w == "como" and sig in ("se", "es", "era") and any(t_ in nf[i + 1:i + 4] for t_ in ("llama", "llaman", "llamaba", "denomina", "denominan", "conoce", "conocen", "nombre")):
                q.tipo = "nombre"
            elif w == "como":
                q.tipo = "como"
            elif w in ("cual", "que") and "nombre" in nf[i + 1:i + 4]:
                q.tipo = "nombre"
            elif w in ("que", "cual", "cuales"):
                if sig in ("ano", "mes", "dia", "fecha", "momento", "epoca", "temporada", "minuto", "semana", "siglo", "decada"):
                    q.tipo = "cuando"
                elif sig in ("lugar", "estadio", "ciudad", "pais", "sitio", "sede", "campo", "region", "zona", "pueblo", "continente"):
                    q.tipo = "donde"
                elif sig in ("edad", "velocidad", "distancia", "altura", "peso", "longitud", "temperatura", "porcentaje", "profundidad", "superficie", "duracion", "ritmo", "altitud", "anchura", "extension", "capacidad") or (sig == "tiempo" and "llevaba" in nf):
                    q.tipo = "cuanto"
                else:
                    q.tipo, q.prep = "que", prev if prev in PREPS else ""
            else:
                continue
            q.x = " ".join(nf[i + 1:])
            break
    if q.tipo == "que" and q.prep in ("de", "a", "por") and any(l_ in ("morir", "fallecer", "enfermar", "perecer", "caer", "sucumbir") for _, _, l_ in toks):      # «de que murio»: la causa
        q.tipo, q.prep = "porque", ""
    # ---- claves -------------------------------------------------------------------------------------------------------------------
    usados = {i_ for i_, t_ in pos_ent.items() if any(t_ in ind.tokens_fam.get(e_, ()) for e_ in ents)}      # solo las palabras que dieron una entidad elegida; las de familias descartadas siguen siendo claves
    foco_i = None
    if q.tipo == "perfil" and not q.ents:                                       # «quien es el entrenador de la seleccion», «que es una seleccion»
        cop = next((i for i, t in enumerate(toks[:4]) if t[0] in ("es", "son", "fue", "fueron", "era", "eran")), None)
        if cop is not None and toks[0][0] in ("quien", "quienes", "que"):
            for i in range(cop + 1, min(len(toks), cop + 4)):
                if toks[i][1] in ("NOUN", "PROPN", "X") and toks[i][0] not in STOPQ:
                    foco_i = i
                    q.tipo = "quien" if toks[0][0].startswith("quien") else "def"
                    break
    if foco_i is None and q.tipo == "que" and toks and toks[0][0] in ("cual", "cuales"):       # «cual es el lema de…»: lo que se pide es ese sustantivo
        cop = next((i for i, t in enumerate(toks[:3]) if t[0] in ("es", "son", "fue", "fueron", "era", "eran")), None)
        if cop is not None:
            for i in range(cop + 1, min(len(toks), cop + 4)):
                if toks[i][1] in ("NOUN",) and toks[i][0] not in STOPQ and i not in usados:
                    foco_i = i
                    break
                if toks[i][1] not in ("DET", "ADJ", "NUM"):
                    break
    if foco_i is None and q.tipo in ("cuando", "donde") and toks and toks[0][0] in ("cuando", "donde", "adonde"):      # «cuando fue la final del Mundial»: el hecho por el que se pregunta es el sustantivo tras «ser»
        cop = next((i for i, t in enumerate(toks[:3]) if t[0] in ("fue", "es", "era", "sera", "son", "fueron", "eran")), None)
        if cop is not None:
            for i in range(cop + 1, min(len(toks), cop + 4)):
                if toks[i][1] in ("NOUN", "X") and toks[i][0] not in STOPQ and i not in usados:
                    foco_i = i
                    break
                if toks[i][1] not in ("DET", "ADJ", "NUM"):
                    break
    if foco_i is None and q.tipo == "quien":                                    # «contra quien jugo la final», «quien marco el gol»: lo que se pregunta gira en torno a ese sustantivo
        iv = next((i for i, t in enumerate(toks) if t[1] == "VERB" and t[0] not in STOPQ and t[2] not in LIGEROS), None)
        if iv is None:                                                          # «quien fue la primera mujer profesora»: el sustantivo tras la copula
            iv = next((i for i, t in enumerate(toks[:4]) if t[0] in ("es", "son", "fue", "fueron", "era", "eran")), None)
        if iv is not None:
            for i in range(iv + 1, min(len(toks), iv + 4)):
                if toks[i][1] in ("NOUN",) and toks[i][0] not in STOPQ and i not in usados:
                    foco_i = i
                    break
                if toks[i][1] not in ("DET", "ADJ", "NUM"):
                    break
    for i, (nf, u, l) in enumerate([] if foco_i is not None else toks):
        if nf in WH and i + 1 < len(toks) and toks[i + 1][1] in ("NOUN", "ADJ", "X") and toks[i + 1][0] not in STOPQ and (i + 1) not in usados:
            foco_i = i + 1
            break
    for i, (nf, u, l) in enumerate(toks):
        if i in usados or nf in STOPQ or nf in WH or len(nf) < 2:
            continue
        if u in ("DET", "ADP", "PRON", "CCONJ", "SCONJ", "PART", "INTJ", "SYM"):
            continue
        if u == "AUX" or (u == "VERB" and l in LIGEROS) or (u == "X" and l in LIGEROS):
            continue
        if q.tipo == "significado" and (l in ("significar", "querer", "decir") or nf in ("significa", "significan", "quiere", "decir")):
            continue
        if q.tipo == "para_que" and l == "servir":
            continue
        if q.tipo == "nombre" and (l in ("llamar", "denominar", "conocer", "recibir", "nombre") or nf in ("nombre", "llama", "llaman", "denomina", "conoce")):
            continue
        if l == "tener" and q.tipo == "cuanto" and any(t_[0] in ("edad", "anos") for t_ in toks):      # «que edad tenia»: «tener» no es lo que se busca
            continue
        if u not in ("NOUN", "PROPN", "ADJ", "NUM", "VERB", "X", "ADV"):
            continue
        if u == "ADV" and nf not in ind.comunes:
            continue
        lem = l if (l in ind.vocab_lem or nf not in ind.vocab_lem) else nf
        if u == "X" and nf in ind.formas:
            lem = ind.formas[nf]
        if i == foco_i:
            k = Clave(lem, "foco", 0.6 if (q.tipo == "cuanto" and lem in UNIDADES) else 2.0, _sinonimos(lem, u)[:3])      # «cuanto tiempo/peso/edad»: nombra la medida, no el asunto
            q.foco = k
        elif u == "VERB" or (u == "X" and nf in ind.formas and re.search(r"(?:ar|er|ir)$", lem)):
            k = Clave(lem, "verbo", 1.6, _sinonimos(lem, "VERB")[:6])
            if q.verbo is None:
                q.verbo = k
        else:
            k = Clave(lem, "cont", {"NOUN": 1.6, "PROPN": 1.6, "ADJ": 1.1, "NUM": 1.2}.get(u, 0.8), _sinonimos(lem, u)[:2] if u in ("NOUN", "ADJ") else ())
        q.claves.append(k)
    return q


# ====================================================== puntuacion de frases =============================================================
def _w_clave(ind: Indice, k: Clave) -> float:
    idf = ind.idf.get(k.nl)
    if idf is None:
        idf = ind.idf_r.get(k.rz, ind.idf_max)
    return k.w * (0.4 + 0.6 * min(1.0, idf / ind.idf_max))


def _prefijo(a: str, b: str) -> bool:
    if min(len(a), len(b)) < 5:
        return False
    p = 0
    while p < min(len(a), len(b)) and a[p] == b[p]:
        p += 1
    return p >= 4 and p >= 0.75 * min(len(a), len(b))


def _difuso(a: str, b: str) -> bool:
    """Verbos con cambio de vocal en la raiz o lematizacion dudosa: elegir/eligio, morir/murio, pedir/pidio."""
    if not (len(a) >= 5 and len(b) >= 5 and a[0] == b[0] and abs(len(a) - len(b)) <= 1 and damerau(a, b, 1) <= 1):
        return False
    if len(a) == len(b):                                                         # solo cambio de vocal tipico de la raiz (e/i, o/u), no crear/creer
        d = [(x, y) for x, y in zip(a, b) if x != y]
        return len(d) == 1 and (d[0] in (("e", "i"), ("i", "e"), ("o", "u"), ("u", "o"), ("o", "e"), ("e", "o")))
    return True


def _casa(k: Clave, lem, raices) -> float:
    if k.nl in lem:
        return 1.0
    if k.rz in raices:
        return 0.75
    if any(a in lem or raiz(a) in raices for a in k.alts):
        return 0.6
    if len(k.nl) >= 5 and any(_prefijo(k.nl, w) for w in lem):
        return 0.4
    if len(k.nl) >= 5 and any(_difuso(k.nl, w) for w in lem):
        return 0.55
    return 0.0


def _casa_ctx(k: Clave, f: Frase) -> float:
    m = 0.0
    if k.nl in f.ctx_lem:
        m = f.ctx_lem[k.nl]
    elif k.rz in f.ctx_raices:
        m = 0.75 * f.ctx_raices[k.rz]
    return m


def nivel_ent(f: Frase, e: str) -> float:
    if e in f.fams:
        return 1.0
    base = f.impl_w.get(e, 0.7) if e in f.impl else f.ctx_fams.get(e, 0.0)
    if e.startswith("t:") and (e.count(":") < 2 or e.endswith(":%d" % f.doc)):           # todo el texto trata de su sustantivo-tema (se dice «leona», «felino»...)
        base = max(base, 0.5)
    return base


W_ENT = 1.5


def puntuar(ind: Indice, q: Q, f: Frase) -> Tuple[float, float]:
    tot = got = 0.0
    for e in q.ents:
        m = nivel_ent(f, e)
        if q.ents_ctx:                                   # la entidad de la conversacion solo suma si aparece
            if m:
                tot += W_ENT * 0.6
                got += W_ENT * 0.6 * m
            continue
        if e in q.debiles:                               # entidad dudosa: suma si aparece, no resta si no
            if m:
                tot += W_ENT * 0.6
                got += W_ENT * 0.6 * m
            continue
        tot += W_ENT
        got += W_ENT * m
    for k in q.claves:
        w = _w_clave(ind, k)
        if k.kind == "verbo" and k.nl in EVENTO and len(q.claves) > 1:
            w *= 0.3                                                         # «que pasa con X»: el verbo es un comodin, lo que cuenta es X
        tot += w
        m = _casa(k, f.lem, f.raices)
        if m < 0.75:
            m = max(m, _casa_ctx(k, f) * (0.5 if k.kind == "foco" else 1.0))      # aquello por lo que se pregunta debe estar en la frase, no solo cerca
        if m < 0.75 and k is q.foco and k.nl in CATEGORIAS and q.tipo == "que" and q.verbo:
            vm_ = _casa(q.verbo, f.lem, f.raices)
            if vm_ >= 0.75 or any(t.u == "NOUN" and t.nl in AGENTIVO.get(q.verbo.nl, ()) for t in f.tok):
                m = 0.8                                                           # «que obra escribio»: la frase da el ejemplar (el titulo) y no la palabra de la clase
        got += w * m
    for d in q.desconocidos:
        tot += 1.5
    return got, (got / tot if tot else 0.0)


def ranking(ind: Indice, q: Q, n: int = 12) -> List[Tuple[float, float, Frase]]:
    out = []
    for f in ind.fr:
        g, c = puntuar(ind, q, f)
        if g > 0:
            out.append((g - 0.002 * len(f.tok) - 0.0001 * f.k, c, f))
    out.sort(key=lambda x: -x[0])
    return out[:n]


# ====================================================== extraccion de la respuesta sobre el arbol ========================================
def cap(s: str) -> str:
    s = s.strip()
    return s[:1].upper() + s[1:] if s else s


def cita(f: Frase, span: str = "", maxlen: int = 250) -> str:
    t = f.texto.strip()
    if len(t) <= maxlen:
        return t
    p = t.lower().find(span.lower()) if span else -1
    if p < 0:
        corte = t.rfind(", ", 0, maxlen)
        if corte < maxlen * 0.5:
            corte = t.rfind(" ", 0, maxlen)
        return t[:corte].rstrip(" ,;") + "…"
    ini, fin = max(0, p - maxlen // 2), min(len(t), p + len(span) + maxlen // 2)
    if ini > 0:
        j = t.find(" ", ini)
        ini = j + 1 if 0 <= j < p else ini
    if fin < len(t):
        j = t.rfind(" ", p, fin)
        fin = j if j > p else fin
    return ("…" if ini > 0 else "") + t[ini:fin].strip(" ,;") + ("…" if fin < len(t) else "")


def _coincide(t: T, k: Clave) -> bool:
    return t.nl == k.nl or raiz(t.nl) == k.rz or t.nl in k.alts or raiz(t.nl) in {raiz(a) for a in k.alts} or (len(k.nl) >= 5 and _prefijo(k.nl, t.nl)) \
        or (k.kind == "verbo" and t.u in ("VERB", "ADJ", "AUX") and _difuso(k.nl, t.nl))


def _grado(t: T, k: Clave) -> int:
    return 0 if t.nl == k.nl else (1 if raiz(t.nl) == k.rz else (2 if t.nl in k.alts else 3))


def ajeno(f: Frase, i: int, ok: Set[str], ind: Indice) -> bool:
    """El token i cuelga de una oracion de relativo cuyo antecedente no es lo que se pregunta («..., quien debuto con 16 anos»)."""
    x, pasos = i, 0
    while x >= 0 and pasos <= len(f.tok):
        pasos += 1
        t = f.tok[x]
        if t.d.startswith("acl") and t.h >= 0:
            ant = t.h
            for a, b, k, _, _ in f.ment:
                if a <= ant <= b:
                    return ind.familia_de(k) not in ok                              # una oracion de relativo sobre otra entidad nombrada no es de lo que se pregunta
            return False
        x = t.h
    return False


def _sujeto_ajeno(ind: Indice, f: Frase, v, ok: Set[str]) -> bool:
    for c in f.hij.get(v.i, []):
        if f.tok[c].d.startswith("nsubj"):
            a, b = f.np(c)
            ms = [m for m in _mencion_en(f, a, b)]
            if ms and all(ind.familia_de(m[2]) not in ok for m in ms):
                return True
    return False


def anclas(ind: Indice, f: Frase, q: Q) -> List[int]:
    out = []
    for k in ([q.verbo] if q.verbo else []) + ([q.foco] if q.foco else []) + [c for c in q.claves if c is not q.verbo and c is not q.foco]:
        for t in f.tok:
            if t.u != "PUNCT" and _coincide(t, k):
                out.append(t.i)
        if out:
            break
    if not out:
        out = [a for a, b, k, _, _ in f.ment if ind.familia_de(k) in q.ents]
    ords = {k.nl for k in q.claves if k.nl in ("primero", "segundo", "tercero", "cuarto", "quinto", "sexto", "septimo", "octavo", "noveno", "decimo", "ultimo")}
    if ords:
        pos = [t.i + 1 for t in f.tok if (t.nl in ords or t.nf in ords or nrm(t.l or "") in ords or t.nf.rstrip("oa") in {o.rstrip("oa") for o in ords}) and t.i + 1 < len(f.tok)]
        if pos:
            return pos
    return out or [0]


def _dist(i: int, anc: List[int]) -> int:
    return min(abs(i - a) for a in anc)


def _mencion_en(f: Frase, a: int, b: int):
    return [m for m in f.ment if m[0] >= a and m[1] <= b]


NUMW = re.compile(r"(?:millon|millones|billon|billones|docena|un|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|dieciseis|diecisiete|dieciocho|diecinueve|veinte|veinti\w+|treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa|cien|ciento|doscientos|trescientos|cuatrocientos|quinientos|mil|medio|media)")
TEMPN = {"tiempo", "epoca", "edad", "era", "siglo", "decada", "periodo", "etapa", "fase", "dia", "noche", "mes", "ano", "semana", "hora", "minuto", "segundo",
         "momento", "vida", "nacimiento", "infancia", "juventud", "madurez", "verano", "invierno", "primavera", "otono", "final", "principio", "inicio", "comienzo",
         "dias", "meses", "anos", "semanas", "horas", "minutos", "siglos", "decadas", "finales", "principios", "mediados", "comienzos"}
UNID_T = {"segundo", "minuto", "hora", "dia", "semana", "mes", "ano", "siglo", "decada", "milenio", "segundos", "minutos", "horas", "dias", "semanas", "meses", "anos", "siglos"}


def _relativos_tiempo(f: Frase) -> List[Tuple[int, int, float]]:
    """Locuciones de tiempo sin fecha: «desde los tiempos de la Antigua Roma», «a partir de los 165 dias de vida», «hasta una semana despues de su nacimiento»."""
    tk, n, out = f.tok, len(f.tok), []
    for i, t in enumerate(tk):
        k = None
        edad_ = False
        if t.nf in ("desde", "hasta", "tras", "durante", "en", "entre", "dentro"):
            k = i + 1
        elif t.nf == "a" and i + 2 < n and tk[i + 1].nf == "partir" and tk[i + 2].nf == "de":
            k = i + 3
        elif t.nf == "a" and i + 2 < n and tk[i + 1].nf in ("finales", "principios", "mediados", "comienzos") and tk[i + 2].nf == "de":
            k = i + 1
        elif t.nf == "a" and i + 1 < n and tk[i + 1].nf in ("los", "las") and i + 2 < n and (tk[i + 2].u == "NUM" or NUMW.fullmatch(tk[i + 2].nf)):
            k = i + 1
            edad_ = True
        if k is None:
            continue
        j = k
        while j < n and (tk[j].nf in ("el", "la", "los", "las", "un", "una", "unos", "unas", "aproximadamente", "casi", "unos", "mas", "menos", "de")
                         or tk[j].u == "NUM" or NUMW.fullmatch(tk[j].nf)) and j - k < 5:
            j += 1
        if j >= n or tk[j].nf not in TEMPN or j == k and tk[j].nf in ("final", "principio", "inicio", "comienzo", "mes", "ano", "dia", "momento"):
            continue
        if tk[j].nf in ("final", "principio", "inicio", "comienzo") and not (j + 1 < n and tk[j + 1].nf == "de"):
            continue                                                                  # «combatio hasta el final» no es una fecha
        fin, cal = j, (0.3 if edad_ and tk[j].nf in ("ano", "anos") else 0.55)                  # «murio a los 76 años»: es una edad, no una fecha
        if tk[j].nf in ("tiempo", "tiempos", "epoca", "edad", "era", "periodo", "etapa", "fase", "siglo", "finales", "principios", "mediados", "comienzos") and j + 2 < n and tk[j + 1].nf == "de":
            m = j + 2
            while m < n and m - j <= 5 and tk[m].u in ("DET", "NOUN", "PROPN", "ADJ", "NUM") :
                m += 1
            fin = m - 1
        elif j + 1 < n and tk[j + 1].nf in ("despues", "antes") and j + 3 < n and tk[j + 2].nf == "de":
            m = j + 3
            while m < n and m - j <= 5 and tk[m].u in ("DET", "NOUN", "PROPN", "ADJ", "NUM"):
                m += 1
            fin = m - 1
        elif j + 1 < n and tk[j + 1].nf == "de" and j + 2 < n and tk[j + 2].nf in ("vida", "edad"):
            fin = j + 2
        elif j == k and tk[j].nf not in ("tiempo", "epoca", "siglo", "decada"):
            continue
        if tk[i].nf == "en" and fin == j and tk[j].nf not in ("momento", "epoca", "tiempo", "etapa", "periodo", "siglo", "decada"):
            continue
        out.append((i, fin, cal))
    return out


def tiempos(f: Frase) -> List[Tuple[int, int, float]]:
    """Expresiones de fecha de la frase: (desde, hasta, calidad). Fecha completa > mes y año > solo año o temporada."""
    n, out, i = len(f.tok), [], 0
    tk = f.tok
    while i < n:
        t = tk[i]
        j, cal = None, 0.0
        if re.fullmatch(r"\d{1,2}", t.nf) and i + 2 < n and tk[i + 1].nf == "de" and tk[i + 2].nf in MESES:
            j, cal = i + 2, 1.0
            if j + 2 < n and tk[j + 1].nf == "de" and re.fullmatch(r"\d{4}", tk[j + 2].nf):
                j += 2
        elif t.nf in MESES and t.u != "VERB":
            j, cal = i, 0.6
            if i + 2 < n and tk[i + 1].nf == "de" and re.fullmatch(r"\d{4}", tk[i + 2].nf):
                j, cal = i + 2, 0.8
        elif re.fullmatch(r"(?:1[0-9]|20)\d\d", t.nf):
            j, cal = i, 0.35
            if i + 2 < n and tk[i + 1].f == "-" and re.fullmatch(r"\d{2}", tk[i + 2].nf):
                j = i + 2
        elif t.nf == "hace" and i + 2 < n and (tk[i + 1].u == "NUM" or tk[i + 1].nf in ("un", "una")) and re.match(r"(?:ano|mes|dia|semana|hora|minuto|siglo|decada)", tk[i + 2].nf):
            j, cal = i + 2, 0.6
        if j is None:
            i += 1
            continue
        a = i
        if a > 0 and tk[a - 1].nf in ("el", "en", "desde", "hasta", "durante", "tras", "a"):
            a -= 1
            if a > 0 and tk[a - 1].nf in ("en", "desde", "hasta", "durante", "tras") and tk[a].nf == "el":
                a -= 1
        if re.fullmatch(r"(?:1[0-9]|20)\d\d", t.nf) and a < i and False:
            pass
        if re.fullmatch(r"(?:1[0-9]|20)\d\d", t.nf) and i > 0 and tk[a].nf in ("temporada", "ano", "campana", "curso", "edicion") or (re.fullmatch(r"(?:1[0-9]|20)\d\d", t.nf) and i > 0 and tk[i - 1].nf in ("temporada", "ano", "campana", "curso", "edicion")):
            a = i - 1
            if a > 0 and tk[a - 1].nf in ("la", "el", "en", "durante"):
                a -= 1
                if a > 0 and tk[a - 1].nf in ("en", "durante"):
                    a -= 1
        out.append((a, j, cal))
        i = j + 1
    for a, b, cal in _relativos_tiempo(f):
        if not any(a <= x[1] and x[0] <= b for x in out):
            out.append((a, b, cal))
        else:
            out = [x for x in out if not (a <= x[0] and x[1] <= b)] + [(a, b, max(cal, 0.6))]
    return out


def _verbo_encima(f: Frase, v, k) -> bool:
    """El verbo v cuelga (gerundio, participio, subordinada) del verbo por el que se pregunta: «marco su primer gol, jugando contra Granada en ...»."""
    x, pasos = v.h, 0
    while x >= 0 and pasos < 12:
        if f.tok[x].u in ("VERB", "AUX") and _coincide(f.tok[x], k):
            return True
        x, pasos = f.tok[x].h, pasos + 1
    return False


def _cabeza_span(f: Frase, a: int, b: int) -> int:
    """Token del tramo [a, b] cuya cabeza queda fuera del tramo (la raiz del sintagma)."""
    for x in range(a, b + 1):
        h = f.tok[x].h
        if h < a or h > b:
            return x
    return a


def _verbo_de(f: Frase, i: int):
    """Primer verbo (VERB/AUX) por encima del token i en el arbol."""
    x, pasos = f.tok[i].h, 0
    while x >= 0 and pasos < 12:
        if f.tok[x].u in ("VERB", "AUX"):
            return f.tok[x]
        x, pasos = f.tok[x].h, pasos + 1
    return None


def ext_cuando(ind, f, q, anc):
    ts = tiempos(f)
    if not ts:
        return None
    ok = set(q.ents)
    cls_ = CLASE_PREP.get(q.prep, {q.prep}) if q.prep in ("desde", "hasta") else None

    def _p(sp_):                                                                # «desde cuando»: la fecha que viene tras «desde» (o «hasta») manda
        if cls_ is None:
            return 0
        return -25 if (sp_[0] > 0 and f.tok[sp_[0] - 1].nf in cls_) or f.tok[sp_[0]].nf in cls_ else 25
    def _gob(s):                                                               # el verbo del que cuelga la fecha: «en 1254 ... concedio» ≠ «en 1255 ... otorgo»
        v_ = _verbo_de(f, _cabeza_span(f, s[0], s[1]))
        if v_ is None:
            return 0
        if q.verbo and q.verbo.nl not in GENERICOS:
            if _coincide(v_, q.verbo):
                return 1 if _grado(v_, q.verbo) <= 2 else 0
            if _verbo_encima(f, v_, q.verbo):
                return 0
            if any(_coincide(t_, q.verbo) and t_.u in ("VERB", "AUX") for t_ in f.tok):
                return -1
        vs_ = {x_.i for x_ in ((f.tok[a_] if f.tok[a_].u in ("VERB", "AUX") else _verbo_de(f, a_)) for a_ in anc if f.tok[a_].u != "PUNCT") if x_ is not None}      # el verbo que gobierna aquello por lo que se pregunta («los primeros estatutos»)
        if vs_:
            return 1 if v_.i in vs_ else -1
        return 0
    def _expl(s_):
        return any(x_.nf in MESES or re.fullmatch(r"\d{4}", x_.nf) for x_ in f.tok[s_[0]:s_[1] + 1])
    def _dur_rel(s_):                                                           # «tras tres dias de viaje»: una duracion, no la fecha, si la frase da una fecha explicita
        if _expl(s_):
            return 0
        pre_ = f.tok[s_[0] - 1].nf if s_[0] > 0 else ""
        return 14 if (pre_ in ("tras", "durante", "despues") or f.tok[s_[0]].nf in ("tras", "durante", "despues")) and any(_expl(o_) for o_ in ts if o_ is not s_) else 0
    a, b, cal = min(ts, key=lambda s: (_dist((s[0] + s[1]) // 2, anc) + (30 if ajeno(f, s[0], ok, ind) else 0) - 8 * s[2] + _p(s) - 20 * _gob(s) + _dur_rel(s)))
    sp = f.texto_span(a, b)
    if cls_ is not None and _p((a, b)) > 0:
        cal *= 0.25
    g_ = _gob((a, b))
    if g_ > 0:
        cal = cal + 0.4 * (1.0 - cal)
    elif g_ < 0:
        cal *= 0.5
    return sp, sp, cal * (0.3 if ajeno(f, a, ok, ind) else 1.0)


LOCADJ = {"endemico", "originario", "nativo", "natural", "oriundo", "tipico", "propio", "habitante", "residente", "autoctono"}


def ext_donde(ind, f, q, anc):
    if q.prep == "de":                                                          # «de donde era su padre»: «fotografo de origen aleman»
        for t in f.tok:
            if t.nl in ("origen", "procedencia", "ascendencia") and t.u == "NOUN":
                hij = [c for c in f.hij.get(t.i, []) if f.tok[c].u in ("ADJ", "PROPN", "NOUN") and f.tok[c].d in ("amod", "nmod", "appos", "flat")]
                if hij:
                    b = max(hij)
                    a = t.i - 1 if t.i > 0 and f.tok[t.i - 1].nf == "de" else t.i
                    sp = f.texto_span(a, b)
                    return sp, sp, 0.95
    prohibidos = set(q.ents)
    for t in f.tok:                                                  # «endemico del este de Australia y de la isla de Tasmania»
        if t.nl in LOCADJ and t.u in ("ADJ", "NOUN") and t.i + 2 < len(f.tok) and f.tok[t.i + 1].nf in ("de", "del"):
            b = t.i + 1
            while b + 1 < len(f.tok) and b - t.i < 14 and f.tok[b + 1].u in ("DET", "NOUN", "PROPN", "ADJ", "ADP", "CCONJ", "NUM") and f.tok[b + 1].f not in (",", ".", ";"):
                b += 1
            while f.tok[b].u in ("ADP", "CCONJ", "DET"):
                b -= 1
            sp = f.texto_span(t.i + 1, b)
            if len(sp) > 4:
                return sp, sp, 1.0
    for estricto in (True, False):
        best = None
        for t in f.tok:
            if t.d == "case" and t.u == "ADP" and t.nf in ("en", "desde", "hacia", "por", "entre", "dentro", "cerca", "a", "ante", "sobre") and not (q.prep in ("por", "desde", "hacia") and t.nf != q.prep) \
                    and not (t.nf == "por" and q.prep != "por"):
                if not estricto and t.nf not in ("en", "por", "desde", "hacia", "dentro", "cerca") :
                    continue
                if t.nf in ("a", "ante", "sobre") and not (q.tipo == "donde" and q.prep in ("a", "hacia")):
                    continue
                a, b = f.np(t.h)
                tx = f.tok[a:b + 1]
                if any(x.nf in MESES or re.fullmatch(r"\d{4}", x.nf) or x.nf in TIEMPO or x.u == "NUM" for x in tx):
                    continue
                ms = _mencion_en(f, a, b)
                ini_ = t.i
                if estricto:
                    if not ms or all(ind.familia_de(m[2]) in prohibidos for m in ms):
                        continue
                    pro_ = [m for m in ms if ind.familia_de(m[2]) in prohibidos]
                    if pro_:                                  # «desde el Centro Kennedy, en Florida»: lo que se pregunta es lo que acompaña al nombre, no el nombre
                        k_ = max(m[1] for m in pro_) + 1
                        while k_ <= b and f.tok[k_].u == "PUNCT":
                            k_ += 1
                        if k_ > b or not any(m[0] >= k_ for m in ms):
                            continue
                        ini_ = k_
                elif f.tok[t.h].u not in ("NOUN", "PROPN"):
                    continue
                d = _dist(t.i, anc)
                if q.prep == "a" and t.nf != "a":
                    d += 2                                                        # «a donde se traslado»: el destino va con «a»
                if q.verbo and q.verbo.nl not in GENERICOS:
                    v_ = _verbo_de(f, t.i)
                    if v_ is not None and not (_coincide(v_, q.verbo) and _grado(v_, q.verbo) <= 2) and any(_coincide(x_, q.verbo) and x_.u in ("VERB", "AUX") for x_ in f.tok) \
                            and not _verbo_encima(f, v_, q.verbo):
                        d += 25                                                   # «murio ..., sus cenizas fueron esparcidas en un lugar secreto»: ese lugar es de otra accion
                if best is None or d < best[0]:
                    best = (d, ini_, b)
        if best:
            sp = f.texto_span(best[1], best[2])
            return sp, sp, (1.0 if estricto else 0.5) * (0.5 if best[0] >= 25 else 1.0)
    return None


def _es_num(t) -> bool:
    return t.u == "NUM" or t.nf.isdigit() or (t.u in ("DET", "ADJ", "X") and bool(NUMW.fullmatch(t.nf)) and t.nf not in ("un", "una", "uno", "media", "medio"))


def _cantidades(f: Frase):
    out = []
    n = len(f.tok)
    for t in f.tok:                              # «un millon de visitantes», «una docena de huevos»: «un» + sustantivo colectivo + «de» + lo contado
        if t.u == "NOUN" and t.nf in ("millon", "billon", "docena", "centenar", "millar") and t.i >= 1 and f.tok[t.i - 1].nf in ("un", "una") and t.i + 2 < n and f.tok[t.i + 1].nf == "de":
            k_ = t.i + 2
            while k_ < n and f.tok[k_].u == "DET":
                k_ += 1
            if k_ < n and f.tok[k_].u in ("NOUN", "PROPN"):
                a_ = t.i - 1
                while a_ >= 1 and (f.tok[a_ - 1].nf in ("casi", "aproximadamente", "unos", "unas", "exactamente") or (a_ >= 2 and f.tok[a_ - 1].nf == "de" and f.tok[a_ - 2].nf in ("mas", "menos", "cerca", "alrededor"))):
                    a_ -= 1 if f.tok[a_ - 1].nf != "de" else 2
                out.append((k_, a_, t.i))
    for t in f.tok:
        if not _es_num(t) or t.nf in MESES:
            continue
        h = None
        if t.d in ("nummod", "det") and t.h >= 0 and f.tok[t.h].u in ("NOUN", "PROPN"):
            h = t.h
        elif t.i + 1 < n and f.tok[t.i + 1].u in ("NOUN", "X", "SYM") and f.tok[t.i + 1].nf not in MESES:
            h = t.i + 1
        elif t.i + 2 < n and _es_num(f.tok[t.i + 1]) and f.tok[t.i + 2].u in ("NOUN", "X"):
            h = t.i + 2
        if h is None or h < t.i:
            continue
        a = t.i
        while a > 0 and _es_num(f.tok[a - 1]):
            a -= 1
        while a > 1 and _es_num(f.tok[a - 2]) and (f.tok[a - 1].f in ("-", "–", "—") or f.tok[a - 1].nf in ("a", "y", "o")):          # «180-190 kg», «de 205 a 334 cm»
            a -= 2
            while a > 0 and _es_num(f.tok[a - 1]):
                a -= 1
        b_ = h
        if f.tok[h].nl in COLECTIVOS and h + 2 < n and f.tok[h + 1].nf == "de":
            k_ = h + 2
            while k_ < n and f.tok[k_].u in ("DET", "ADJ") and f.tok[k_].nf in ("los", "las", "sus", "estos", "estas", "unos", "unas"):
                k_ += 1
            if k_ < n and f.tok[k_].u in ("NOUN", "PROPN"):
                h = k_                                                      # «un millon de visitantes»: lo contado es lo que sigue a «de»
        while a >= 1 and (f.tok[a - 1].nf in ("casi", "aproximadamente", "unos", "unas", "exactamente") or (a >= 2 and f.tok[a - 1].nf == "de" and f.tok[a - 2].nf in ("mas", "menos", "cerca", "alrededor"))):
            a -= 1 if f.tok[a - 1].nf != "de" else 2                    # «mas de un millon»: la cifra lleva su aproximacion
        out.append((h, a, b_))
    return out


COLECTIVOS = {"millon", "billon", "docena", "centenar", "millar", "decena", "cuarto", "mitad", "par"}
_T_ = {"segundo", "minuto", "hora", "dia", "semana", "mes", "ano", "siglo", "decada", "milenio"}
_D_ = {"metro", "kilometro", "km", "cm", "centimetro", "milimetro", "milla", "pie", "pulgada", "m", "mm"}
UNIDADES = {"ritmo": {"km", "kilometro", "metro", "milla", "m"}, "tiempo": _T_, "duracion": _T_, "edad": {"ano", "mes", "dia", "semana"}, "distancia": _D_, "longitud": _D_, "altura": _D_, "largo": _D_, "ancho": _D_,
            "profundidad": _D_, "tamano": _D_ | {"hectarea", "kg"}, "peso": {"kg", "kilo", "kilogramo", "gramo", "g", "tonelada", "libra", "t"},
            "velocidad": {"km", "kilometro", "metro", "milla", "m"}, "porcentaje": {"%", "ciento"}, "superficie": {"hectarea", "km2", "kilometro", "metro"},
            "temperatura": {"grado", "c"}, "altitud": _D_, "anchura": _D_, "extension": _D_ | {"hectarea", "km2", "kilometro"}, "capacidad": {"litro", "hectometro", "metro", "kg", "tonelada", "persona", "plaza"}}


VERBO_UNIDAD = {"pesar": "peso", "medir": "longitud", "durar": "duracion", "tardar": "duracion", "costar": "precio", "cobrar": "precio", "ganar": "precio", "vivir": "edad", "correr": "velocidad",
                "volar": "velocidad", "nadar": "velocidad", "saltar": "altura", "crecer": "altura"}
UNIDADES["precio"] = {"euro", "dolar", "peso", "libra", "yen", "franco", "millon", "mil", "moneda"}


def ext_cuanto(ind, f, q, anc):
    try:
        from . import relaciones as _R
        r_ = _R.ext_cuanto_rico(ind, f, q, anc)
    except Exception:                                                                       # noqa
        if os.environ.get("LCM_DEBUG"):
            raise
        r_ = None
    if r_:
        return r_
    cs = _cantidades(f)
    if q.foco:
        un = UNIDADES.get(q.foco.nl)
        cs = [c for c in cs if _coincide(f.tok[c[0]], q.foco) or (un is not None and (f.tok[c[0]].nl in un or f.tok[c[0]].nf in un))]
    elif q.verbo and q.verbo.nl in VERBO_UNIDAD and not any(t_[0] in ("veces", "vez") for t_ in q.toks):      # «cuanto pesa»: la cantidad lleva una unidad de peso, no un porcentaje
        un = UNIDADES[VERBO_UNIDAD[q.verbo.nl]]
        cs = [c for c in cs if f.tok[c[0]].nl in un or f.tok[c[0]].nf in un]
    if not cs:
        return None
    ok = set(q.ents)
    h, a, b = min(cs, key=lambda c: _dist(c[0], anc) + (30 if ajeno(f, c[0], ok, ind) else 0))
    sp = f.texto_span(a, b)
    return sp, sp, 1.0


def _nombre_cerca(ind, f, q, anc, maximo=6, excluir=()):
    fam_q = set(q.ents)
    mejor = None
    for a, b, k, s_, _ in f.ment:
        fid = ind.familia_de(k)
        if fid in fam_q or fid in excluir:
            continue
        d = min(abs(a - x) if a > x else abs(x - b) for x in anc)
        if d <= maximo and (mejor is None or d < mejor[0]):
            mejor = (d, s_)
    return mejor[1] if mejor else None


IRREG_PART = re.compile(r"(?:des|in|pre|trans|sus|re|sobre)?(?:crit|vist|hech|dich|puest|muert|abiert|cubiert|rot|vuelt|resuelt|impres|frit|satisfech|compuest|supuest|previst|propuest|expuest|impuest|dispuest)[oa]s?$")


def _agente_por(ind, f, i: int, fam_q, lim: int = 10):
    """Complemento agente «... por Carlos Linneo» cerca del participio i (el arbol de estas frases largas suele colgarlo mal)."""
    n = len(f.tok)
    for j in range(i + 1, min(n - 1, i + lim + 1)):
        t = f.tok[j]
        if t.f in (".", ";"):
            break
        if t.nf == "por" and t.u == "ADP":
            for a, b, k, s_, _ in f.ment:
                if j < a <= j + 3 and ind.familia_de(k) not in fam_q:
                    return s_
            break
    return None


MANDO = {"mandar", "comandar", "dirigir", "capitanear", "liderar", "gobernar", "encabezar"}


def _mando(ind, f, q, fam_q):
    """«la flota britanica, mandada por Nelson, con la escuadra combinada, al mando de Villeneuve»: quien manda es el agente cuyo complemento es lo que se pregunta."""
    otros = {k.nl for k in q.claves if k.kind in ("cont", "foco") and k.nl not in LIGEROS} | {k.rz for k in q.claves if k.kind in ("cont", "foco")}
    ents_w = set()
    for e in q.ents:
        ents_w |= set(e.split("+"))
    cands = []
    for t in f.tok:
        ag = pac = None
        if t.nf == "mando" and t.u == "NOUN" and t.i >= 1 and f.tok[t.i - 1].nf in ("al", "a", "el", "bajo") and t.i + 1 < len(f.tok) and f.tok[t.i + 1].nf in ("de", "del"):
            k = t.i + 2
            while k < len(f.tok) and f.tok[k].u == "DET":
                k += 1
            ms = [m for m in f.ment if m[0] >= k and m[0] <= k + 3]
            if ms:
                ag = ms[0]
            j = t.i - 1
            while j >= 0 and (f.tok[j].u in ("PUNCT", "ADP", "DET") or f.tok[j].nf in ("al", "a")):
                j -= 1
            pac = j
        elif t.u in ("VERB", "ADJ") and _coincide(t, q.verbo) and (re.search(r"(?:ad[oa]s?|id[oa]s?)$", t.nf) or IRREG_PART.match(t.nf)):
            for c in f.hij.get(t.i, []):
                if f.tok[c].d.startswith("obl") and any(f.tok[x].nf == "por" and f.tok[x].d == "case" for x in f.hij.get(c, [])):
                    a_, b_ = f.np(c)
                    ms = _mencion_en(f, a_, b_)
                    if ms:
                        ag = ms[0]
            j = t.i - 1
            while j >= 0 and f.tok[j].u == "PUNCT":
                j -= 1
            pac = j
        if ag is not None and pac is not None and pac >= 0 and ind.familia_de(ag[2]) not in fam_q:
            a_, b_ = f.np(pac)
            palabras = {x.nl for x in f.tok[a_:b_ + 1]} | {x.nf for x in f.tok[a_:b_ + 1]} | {raiz(x.nl) for x in f.tok[a_:b_ + 1]}
            pts = sum(1 for o in otros if o in palabras) + sum(1 for w in ents_w if w in palabras)
            cands.append((pts, -ag[0], ag[3]))
    if not cands:
        return None
    cands.sort(reverse=True)
    if len(cands) >= 2 and cands[0][0] == cands[1][0]:
        return None
    return cands[0][2] if cands[0][0] > 0 else None


def ext_quien_pl(ind, f, q, anc):
    r = ext_quien(ind, f, q, anc)
    if not r or not r[0] or not re.search(r"\bquienes\b", nrm(q.raw)):
        return r
    for m in f.ment:
        if m[3] == r[0]:
            h = next((k for k in range(m[0], m[1] + 1) if f.tok[k].h < m[0] or f.tok[k].h > m[1]), m[0])
            sibs, pila = [m], [h]
            while pila:
                x = pila.pop()
                for c in f.hij.get(x, []):
                    if f.tok[c].d == "conj":
                        mc = next((mm for mm in f.ment if mm[0] <= c <= mm[1]), None)
                        if mc and mc not in sibs:
                            sibs.append(mc)
                            pila.append(c)
            if len(sibs) >= 2:
                sibs.sort(key=lambda mm: mm[0])
                nom = [mm[3] for mm in sibs]
                txt = ", ".join(nom[:-1]) + " y " + nom[-1]
                return txt, txt, r[2]
    return r


def ext_quien(ind, f, q, anc):
    fam_q = set(q.ents)
    ment = [(a, b, s_, ind.familia_de(k)) for a, b, k, s_, _ in f.ment]
    sin_verbo_ = bool(q.verbo) and q.verbo.nl not in GENERICOS and not any(t.u != "PUNCT" and _coincide(t, q.verbo) and _grado(t, q.verbo) <= 1 for t in f.tok)
    if q.prep and not sin_verbo_:
        cls = CLASE_PREP.get(q.prep, {q.prep})
        best = None
        for t in f.tok:                                                          # «..., con quien se caso»: el antecedente de «quien» es la persona nombrada, no el sustantivo mas cercano
            if t.nf in ("quien", "quienes") and t.i > 0 and f.tok[t.i - 1].nf in cls and f.tok[t.i - 1].u == "ADP":
                for m in sorted([m for m in ment if m[1] < t.i - 1 and m[3] not in fam_q], key=lambda m: -m[1]):
                    SKIP_ = ("de", "del", "en", "para", "por", "sobre", "entre", "desde", "hasta", "segun")
                    x_, dentro_ = m[0], False
                    for _ in range(5):                                           # un nombre que cuelga de «de la Escuela de Fisica y Quimica» no es el antecedente
                        if x_ < 0:
                            break
                        if any(f.tok[c].d == "case" and f.tok[c].nf in SKIP_ for c in f.hij.get(x_, [])):
                            dentro_ = True
                            break
                        x_ = f.tok[x_].h
                    if not dentro_:
                        return m[2], m[2], 1.0
        for t in f.tok:                                                          # «una estudiante serbia con la que se casaria»: el antecedente del relativo es la persona a la que se refiere el sustantivo
            if t.nf == "que" and t.u == "PRON" and t.i >= 2 and f.tok[t.i - 1].nf in ("la", "el", "los", "las") and f.tok[t.i - 2].nf in cls and f.tok[t.i - 2].u == "ADP" \
                    and t.h >= 0 and f.tok[t.h].d in ("acl", "acl:relcl") and f.tok[t.h].h >= 0:
                n_ = f.tok[f.tok[t.h].h]
                cand_ = []
                if n_.d == "appos" and n_.h >= 0:
                    cand_ = [m for m in ment if m[0] <= n_.h <= m[1]]
                if not cand_:
                    cand_ = [m for m in ment if m[0] <= n_.i <= m[1]] or [m for m in ment if any(f.tok[c].d == "appos" and m[0] <= c <= m[1] for c in f.hij.get(n_.i, []))]
                cand_ = [m for m in cand_ if m[3] not in fam_q]
                if cand_:
                    return cand_[0][2], cand_[0][2], 1.0
        for t in f.tok:
            if t.d == "case" and t.nf in cls and t.u == "ADP":
                a, b = f.np(t.h)
                ms = [m for m in ment if m[0] >= a and m[1] <= b and m[3] not in fam_q]
                if not ms:
                    continue
                d = _dist(t.i, anc)
                if best is None or d < best[0]:
                    best = (d, ms[0][2])
        if best:
            return best[1], best[1], 1.0
    if q.verbo and not q.prep:
        vs_ = [v for v in f.tok if (v.u in ("VERB", "AUX") or (v.u == "ADJ" and (re.search(r"(?:ad[oa]s?|id[oa]s?)$", v.nf) or IRREG_PART.match(v.nf)))) and _coincide(v, q.verbo)]
        vs_.sort(key=lambda v: (min(_grado(v, q.verbo), 1) if _grado(v, q.verbo) != 2 else 2, v.i))                 # el verbo mismo antes que un sinonimo: «en 1255 el papa le otorgo…» y no «en 1254 el rey le concedio…»
        if q.foco:
            def _bajo_foco(v):
                x_, n_ = v.h, 0
                while x_ >= 0 and n_ < 4:
                    if f.tok[x_].u in ("NOUN", "PROPN") and _coincide(f.tok[x_], q.foco) and any(f.tok[c_].d == "cop" for c_ in f.hij.get(x_, [])):
                        return True
                    x_, n_ = f.tok[x_].h, n_ + 1
                return False
            vs_ = [v for v in vs_ if not _bajo_foco(v)]                                   # «la ciudad mas poblada de las que bana el rio»: «bana» describe a la ciudad, no es la accion de la pregunta
        mando_ = _mando(ind, f, q, fam_q) if (q.verbo.nl in MANDO) else None
        if mando_:
            return mando_, mando_, 1.0
        for v in vs_:
            if True:
                fg = {0: 1.0, 1: 1.0, 2: 0.7, 3: 0.85}.get(_grado(v, q.verbo), 0.85)           # un sinonimo del verbo vale menos que el verbo mismo
                es_part = bool(re.search(r"(?:ad[oa]s?|id[oa]s?)$", v.nf) or IRREG_PART.match(v.nf)) and not any(f.tok[x].nl == "haber" for x in range(max(0, v.i - 3), v.i))
                pasivo = es_part and (v.u == "ADJ" or v.d in ("amod", "acl", "acl:relcl") or any(f.tok[x].d in ("aux:pass", "cop") for x in f.hij.get(v.i, [])) or v.u == "VERB")      # «descritas por Linneo»: el sujeto es lo descrito, no quien lo hizo
                for c in f.hij.get(v.i, []):
                    ct = f.tok[c]
                    if ct.d.startswith("nsubj") and ct.u != "PRON" and not pasivo:
                        a, b = f.np(c)
                        ms = _mencion_en(f, a, b)
                        if ms and ind.familia_de(ms[0][2]) in fam_q:
                            for c2 in f.hij.get(v.i, []):                           # «la Casa Azul acogio a Trotsky» ← «quien se alojo en la Casa Azul»
                                if f.tok[c2].d in ("obj", "iobj") and f.tok[c2].u in ("PROPN", "NOUN"):
                                    ms2 = [m for m in _mencion_en(f, *f.np(c2)) if ind.familia_de(m[2]) not in fam_q]
                                    if ms2:
                                        return ms2[0][3], ms2[0][3], 0.9 * fg
                            continue
                        sp = ms[0][3] if ms else f.texto_span(a, b)
                        return sp, sp, 1.0 * fg
                    if ct.d.startswith("obl") and any(f.tok[x].nf == "por" and f.tok[x].d == "case" for x in f.hij.get(c, [])):
                        a, b = f.np(c)
                        while b + 1 < len(f.tok) and f.tok[b + 1].h == ct.h and f.tok[b + 1].u in ("NOUN", "ADJ") and f.tok[b + 1].d.startswith(("obl", "amod")) \
                                and not any(f.tok[x].d == "case" for x in f.hij.get(b + 1, [])) and not any(f.tok[x].d == "det" for x in f.hij.get(b + 1, [])):
                            b += 1                                                    # «por piratas berberiscos»: el analizador deja el adjetivo suelto
                        ms = _mencion_en(f, a, b)
                        sp = ms[0][3] if ms else re.sub(r"^por\s+", "", f.texto_span(a, b))
                        return sp, sp, 1.0 * fg
                ag = _agente_por(ind, f, v.i, fam_q)
                if ag:
                    return ag, ag, 0.95 * fg
                impl = sorted((x for x in f.impl if x not in fam_q), key=lambda x: (-f.impl_w.get(x, 0.7), x))             # orden estable: primero el de mas peso
                if impl:
                    return ind.disp[impl[0]], ind.disp[impl[0]], 0.6
        for n_ in f.tok:                              # «tras el pago de un rescate por los frailes»: el sustantivo de accion lleva su agente
            if n_.u == "NOUN" and _coincide(n_, q.verbo) and _grado(n_, q.verbo) <= 3 and len(n_.nl) >= 4:
                for p_ in f.tok[n_.i + 1:n_.i + 9]:
                    if p_.u in ("VERB",) or p_.f in (",", ".", ";"):
                        break
                    if p_.nf == "por" and p_.u == "ADP" and p_.i + 1 < len(f.tok):
                        a_, b_ = f.np(p_.h) if p_.h > p_.i else (p_.i + 1, p_.i + 1)
                        a_ = max(a_, p_.i + 1)
                        ms_ = _mencion_en(f, a_, b_)
                        sp_ = ms_[0][3] if ms_ else f.texto_span(a_, b_)
                        if (ind.familia_de(ms_[0][2]) not in fam_q) if ms_ else bool(sp_):
                            return sp_, sp_, 0.9
    if q.foco and not q.prep:                                                   # «su padre, Guillermo Kahlo»: el nombre en aposicion al sustantivo por el que se pregunta
        otros_ = [k_.nl for k_ in q.claves if k_ is not q.foco and k_ is not q.verbo and k_.kind in ("cont", "foco")]
        mejor_ap = None
        for t in f.tok:
            if t.u in ("NOUN", "PROPN") and _coincide(t, q.foco) and _grado(t, q.foco) == 0:
                for c in f.hij.get(t.i, []):
                    if f.tok[c].d == "appos" and f.tok[c].u == "PROPN":
                        ms = [m for m in _mencion_en(f, *f.np(c)) if ind.familia_de(m[2]) not in fam_q]
                        if ms:
                            hay_ = {f.tok[x].nl for x in f.sub(t.i)}
                            pts_ = sum(1 for o_ in otros_ if o_ in hay_)                # «piloto del modulo de mando»: el cargo cuyo complemento tambien esta en la pregunta
                            if mejor_ap is None or pts_ > mejor_ap[0]:
                                mejor_ap = (pts_, ms[0][3])
        for t in f.tok:                                                          # «Michael Collins, piloto del modulo de mando»: el cargo cuelga del nombre
            if t.u == "NOUN" and t.d == "appos" and t.h >= 0 and f.tok[t.h].u == "PROPN" and _coincide(t, q.foco) and _grado(t, q.foco) == 0:
                ms = [m for m in _mencion_en(f, *f.np(t.h)) if ind.familia_de(m[2]) not in fam_q]
                if ms:
                    hay_ = {f.tok[x].nl for x in f.sub(t.i)}
                    pts_ = sum(1 for o_ in otros_ if o_ in hay_)
                    if mejor_ap is None or pts_ > mejor_ap[0]:
                        mejor_ap = (pts_, ms[0][3])
        if mejor_ap:
            return mejor_ap[1], mejor_ap[1], 1.25
    if q.foco and not q.prep:                                                   # «quien fue la primera mujer profesora»: el sujeto de esa frase copulativa (a veces omitido)
        for t in f.tok:
            if t.u in ("NOUN", "PROPN") and _coincide(t, q.foco) and any(f.tok[c].d == "cop" for c in f.hij.get(t.i, [])):
                for c in f.hij.get(t.i, []):
                    if f.tok[c].d.startswith("nsubj") and f.tok[c].u != "PRON":
                        a, b = f.np(c)
                        ms = _mencion_en(f, a, b)
                        sp = ms[0][3] if ms else f.texto_span(a, b)
                        return sp, sp, 0.95
                impl = sorted((x for x in f.impl if x not in fam_q), key=lambda x: (-f.impl_w.get(x, 0.7), x))             # orden estable: primero el de mas peso
                if impl:
                    return ind.disp[impl[0]], ind.disp[impl[0]], 0.8
    if True:                                                                    # «quien marco el gol» -> «un solitario gol de Merino»; «a quien sustituyo» -> «en reemplazo de Dani Olmo»
        for k in ([q.verbo] if q.verbo else []) + ([c_ for c_ in q.claves if c_.kind in ("cont", "foco")] if not q.prep else []):
            for t in f.tok:
                if t.u != "NOUN" or not _coincide(t, k):
                    continue
                if k.kind == "verbo" and _grado(t, k) == 1 and re.search(r"(?:miento|cion|aje|ura)$", t.nl):      # «lugar de entrenamiento» no es «quien entrena»
                    continue
                for c in f.hij.get(t.i, []):
                    if f.tok[c].d.startswith("nmod") and f.tok[c].u in ("PROPN", "NOUN"):
                        a, b = f.np(c)
                        ms = [m for m in _mencion_en(f, a, b) if ind.familia_de(m[2]) not in fam_q]
                        if ms and not ajeno(f, c, fam_q, ind):
                            return ms[0][3], ms[0][3], 0.85
    if q.foco:
        best = None
        for t in f.tok:
            if _coincide(t, q.foco) and t.u in ("NOUN", "PROPN", "ADJ"):
                for a, b, s_, fid in ment:
                    if fid in fam_q:
                        continue
                    d = (_grado(t, q.foco), a - t.i if a > t.i else t.i - b)
                    if d[1] <= 5 and (best is None or d < best[0]):
                        best = (d, s_)
        if best:
            return best[1], best[1], 0.9
    if q.verbo and not q.prep:                                                  # agente de un participio aunque el verbo sea otro: «muerto por Lennox Anderson»
        for v in f.tok:
            if v.u in ("VERB", "ADJ") and (re.search(r"(?:ad[oa]s?|id[oa]s?)$", v.nf) or IRREG_PART.match(v.nf)):
                for c in f.hij.get(v.i, []):
                    ct = f.tok[c]
                    if ct.d.startswith("obl") and any(f.tok[x].nf == "por" and f.tok[x].d == "case" for x in f.hij.get(c, [])):
                        a, b = f.np(c)
                        ms = [m for m in _mencion_en(f, a, b) if ind.familia_de(m[2]) not in fam_q]
                        if ms:
                            return ms[0][3], ms[0][3], 0.45
                ag = _agente_por(ind, f, v.i, fam_q, 8)
                if ag:
                    return ag, ag, 0.45
    claves = ([q.verbo] if q.verbo else []) + ([q.foco] if q.foco else [])
    if claves and any(_grado(t, k) <= 1 and (k.kind != "verbo" or t.u in ("VERB", "AUX")) for t in f.tok for k in claves if t.u != "PUNCT" and _coincide(t, k)):      # «entrena» no es «entrenamiento»
        nm = _nombre_cerca(ind, f, q, anc)
        if nm:
            return nm, nm, 0.4
    return None


EVENTO = {"pasar", "ocurrir", "suceder", "acontecer", "acaecer", "sucederle", "ocurrirle"}


def _aposicion_de(f: Frase, i: int) -> Optional[int]:
    """«poliomielitis, una enfermedad que...», «Las dos Fridas, uno de sus cuadros mas famosos»: la palabra por la que se pregunta describe a otra, y esa otra es la respuesta."""
    x = i
    for _ in range(3):
        t = f.tok[x]
        if t.d == "appos" and t.h >= 0:
            return t.h
        a, _b = f.np(x)                                                          # el analizador a veces las deja como hermanas: «contrajo poliomielitis, una enfermedad que...»
        if a >= 2 and f.tok[a - 1].f == "," and f.tok[a].u in ("DET", "PRON", "NUM") and f.tok[a - 2].u in ("NOUN", "PROPN") and f.tok[a - 2].h in (t.h, x):
            y = a - 2
            while f.tok[y].d.startswith("flat") and f.tok[y].h >= 0:
                y = f.tok[y].h
            return y
        if t.h < 0:
            return None
        x = t.h
    return None


AGENTIVO = {"escribir": {"autor", "escritor", "novelista", "poeta", "dramaturgo"}, "pintar": {"pintor", "autor"}, "componer": {"compositor", "autor"}, "crear": {"creador", "autor"},
            "construir": {"constructor", "arquitecto"}, "disenar": {"disenador", "arquitecto"}, "esculpir": {"escultor", "autor"}, "inventar": {"inventor"}, "descubrir": {"descubridor"},
            "fundar": {"fundador"}, "publicar": {"autor", "editor"}, "dirigir": {"director"}}
CITA_N = {"frase", "palabra", "lema", "eslogan", "expresion", "cita", "inscripcion", "leyenda", "grito", "consigna", "mensaje", "divisa", "proverbio", "refran", "dicho", "motto"}
HABLA = {"decir", "pronunciar", "gritar", "exclamar", "escribir", "afirmar", "declarar", "proclamar"}


def _entrecomillado(f, q):
    foco_ok = bool(q.foco) and nrm(q.foco.nl) in CITA_N
    verbo_ok = bool(q.verbo) and q.verbo.nl in HABLA and not q.foco
    if not (foco_ok or verbo_ok):
        return None
    qs_ = list(re.finditer(r"[«\"“]([^»\"”]{3,})[»\"”]", f.texto))
    if not qs_:
        return None
    if foco_ok and not any(t.u in ("NOUN", "PROPN") and _coincide(t, q.foco) for t in f.tok):
        return None
    if verbo_ok and not any(_coincide(t, q.verbo) for t in f.tok):
        return None
    m = qs_[0]
    sp = "«" + m.group(1) + "»"
    return sp, sp, 1.0


def _predicado_cual(f, q, t):
    """«¿Cual es el lema de…?» <- «Su lema es X»;  «¿Cual es el mayor embalse?» <- «…el de Mequinenza, que es el mayor de la cuenca»;  «¿Cuales son los afluentes…?» <- «…son el Aragon, el Gallego y el Segre»."""
    plural = nrm(q.raw).lstrip("¿ ").startswith("cuales ")
    adjs_q = [k.nl for k in q.claves if k.kind == "cont" and any(tk[2] == k.nl and tk[1] == "ADJ" for tk in q.toks)]
    sup_q = re.search(r"\bmas (\w+)", nrm(q.raw))
    if sup_q and not any(x.u == "ADJ" and (nrm(x.f) == sup_q.group(1) or nrm(x.l or x.f)[:5] == sup_q.group(1)[:5]) or nrm(x.f) == sup_q.group(1) for x in f.tok):
        pass
    # --- cabeza copulativa: con el arbol si sostiene la frase, y si no, en lineal
    c_ = None
    if t.d.startswith("nsubj") and t.h >= 0 and (f.tok[t.h].nl == "ser" or any(f.tok[c].d == "cop" for c in f.hij.get(t.h, []))):
        k0 = next((c for c in f.hij.get(t.h, []) if f.tok[c].d == "cop"), None)
        c_ = k0 if k0 is not None else t.h
    if c_ is None and not t.d.startswith("root"):
        c_ = next((x.i for x in f.tok[t.i + 1:t.i + 13] if x.nl == "ser" and x.u in ("AUX", "VERB")), None)
        if c_ is not None and any(x.u == "VERB" and x.nl != "ser" for x in f.tok[t.i + 1:c_]):
            c_ = None
    if c_ is None or f.tok[c_].nf == "sido" or (c_ + 1 < len(f.tok) and re.search(r"(?:ad[oa]s?|id[oa]s?)$", f.tok[c_ + 1].nf) and f.tok[c_ + 1].u in ("VERB", "ADJ")) \
            or (c_ > 0 and f.tok[c_ - 1].nl == "haber"):
        return None                                                                    # «ha sido comparado»: pasiva, no atribucion
    if sup_q and not any(x.nf.startswith(sup_q.group(1)[:5]) or nrm(x.l or "").startswith(sup_q.group(1)[:5]) for x in f.tok):
        return None                                                                    # «la universidad mas antigua»: la frase debe decir ese adjetivo
    # --- relativa: «X, que es el mayor de la cuenca» -> X
    if c_ > 0 and f.tok[c_ - 1].nf == "que" and c_ >= 3 and f.tok[c_ - 2].f == ",":
        j = c_ - 3
        m_ = next((m for m in f.ment if m[0] <= j <= m[1]), None)
        if m_:
            return m_[3], m_[3], 0.95
    e_ = len(f.tok)
    for x in f.tok[c_ + 1:]:
        if x.f in (",", ".", ";", ":", "(") and not (plural and x.f == "," and x.i + 1 < len(f.tok) and f.tok[x.i + 1].u in ("DET", "PROPN", "NOUN")) \
                or x.nf in ("que", "aunque", "pero", "mientras") or (x.nf in ("y", "e") and x.i + 1 < len(f.tok) and f.tok[x.i + 1].nf in ("su", "sus", "este", "esta", "estos", "estas") and not plural):
            e_ = x.i
            break
        if plural and x.nf in ("mientras", "aunque", "pero"):
            e_ = x.i
            break
    if plural:
        for x in f.tok[c_ + 1:e_]:
            if x.u == "VERB" and x.i > c_ + 1:
                e_ = x.i
                break
    while e_ - 1 > c_ and f.tok[e_ - 1].f in (",", "y", "e"):
        e_ -= 1
    if e_ > c_ + 1:
        sp = f.texto_span(c_ + 1, e_ - 1)
        if len(sp) > 1:
            return sp, sp, 0.95
    return None


def _miembro_pregunta(f, q, a: int, b: int):
    """«dióxido de carbono del aire y agua del suelo» + «¿qué toman las plantas del suelo?»: el miembro de la enumeracion que lleva lo que la pregunta anade."""
    n = len(f.tok)
    e, k = b, b + 1
    while k < n:
        t = f.tok[k]
        if t.u in ("VERB", "AUX") or t.f in (".", ";", ":"):
            break
        if t.f == ",":
            nx = f.tok[k + 1] if k + 1 < n else None
            if nx is None or nx.u in ("CCONJ", "SCONJ", "PRON", "ADV"):
                break
        if t.u in ("NOUN", "PROPN", "ADP", "DET", "ADJ", "CCONJ", "NUM") or t.f == ",":
            e, k = k, k + 1
            continue
        break
    miembros, ini = [], a
    for k in range(a + 1, e + 1):
        t = f.tok[k]
        if (t.nf in ("y", "e", "o", "u") or t.f == ",") and k + 1 <= e and f.tok[k + 1].u in ("DET", "NOUN", "PROPN", "NUM"):
            miembros.append((ini, k - 1))
            ini = k + 1
    miembros.append((ini, e))
    if len(miembros) < 2:
        return None
    pal = {k_.nl for k_ in q.claves if k_.kind in ("cont", "foco")} | {k_.rz for k_ in q.claves if k_.kind in ("cont", "foco")}
    pal -= {t_[2] for t_ in q.toks if t_[1] in ("VERB", "AUX", "PRON", "DET", "ADP")}
    pts = []
    for (i, j) in miembros:
        hay = {x.nl for x in f.tok[i:j + 1]} | {raiz(x.nl) for x in f.tok[i:j + 1]}
        pts.append(len(pal & hay))
    mx = max(pts)
    if mx == 0 or pts.count(mx) != 1:
        if mx == 0 and e - a <= 12 and all(j - i <= 6 for i, j in miembros):
            return f.texto_span(a, e)                                          # «producen glucosa y oxigeno»: sin nada que distinga, se contestan todos los miembros
        return None
    i, j = miembros[pts.index(mx)]
    while i < j and f.tok[i].u == "DET":
        i += 1
    return f.texto_span(i, j)


def ext_que(ind, f, q, anc):
    r_q = _entrecomillado(f, q)
    if r_q:
        return r_q
    if q.verbo and q.verbo.nl in EVENTO and not q.foco:                          # «que le paso el 17 de septiembre»: lo que cuenta la frase entera
        for c_ in q.claves:
            if c_.kind != "cont" or c_.nl in LIGEROS or c_.nl.isdigit():
                continue
            for s_ in f.tok:                                                   # «el oxigeno se libera a la atmosfera» <- «¿que pasa con el oxigeno?»
                if s_.u == "NOUN" and _coincide(s_, c_) and _grado(s_, c_) == 0 and s_.d.startswith("nsubj") and s_.h >= 0 and f.tok[s_.h].u == "VERB" and f.tok[s_.h].i > s_.i:
                    v_ = f.tok[s_.h]
                    a_ = v_.i - 1 if (v_.i >= 1 and f.tok[v_.i - 1].nf == "se") else v_.i
                    fin_ = v_.i
                    while fin_ + 1 < len(f.tok) and f.tok[fin_ + 1].f not in (",", ";", "."):
                        fin_ += 1
                    sp_ = f.texto_span(a_, fin_)
                    if sp_:
                        return sp_, sp_, 1.0
        return "", "", 0.7
    if q.verbo and q.verbo.nl in AGENTIVO:                          # «autor de Don Quijote»: lo que escribio
        for t in f.tok:
            if t.u == "NOUN" and t.nl in AGENTIVO[q.verbo.nl] and t.i + 1 < len(f.tok) and f.tok[t.i + 1].nf in ("de", "del"):
                c_ = next((x for x in f.hij.get(t.i, []) if f.tok[x].d == "nmod" and x > t.i), None)
                if c_ is not None:
                    a_, b_ = f.np(c_)
                    sp_ = f.texto_span(a_, b_)
                    sp_ = re.sub(r"^(?:de|del)\s+", "", sp_)
                    sp_ = re.sub(r",\s+(?:la|el|las|los|una|un)\s.*$", "", sp_) if sp_[:1].isupper() else sp_       # «Don Quijote de la Mancha, la primera novela moderna»: el titulo sin su aposicion
                    if sp_:
                        return sp_, sp_, 0.9
    if q.foco:
        best = None
        for t in f.tok:
            if t.u in ("NOUN", "PROPN") and _coincide(t, q.foco):
                if t.i + 2 < len(f.tok) and f.tok[t.i + 1].f == ":" and t.nl not in TIEMPO and not ajeno(f, t.i, set(q.ents), ind):
                    fin_ = t.i + 2
                    while fin_ + 1 < len(f.tok) and f.tok[fin_ + 1].f not in (".", ";"):
                        fin_ += 1
                    sp_ = f.texto_span(t.i + 2, fin_)
                    if sp_:
                        return sp_, sp_, 1.0                                           # «dos sectores: el agricola y el urbano»: la enumeracion tras los dos puntos
                h_ = _aposicion_de(f, t.i)
                if h_ is not None and f.tok[h_].u in ("PROPN", "NOUN") and not _coincide(f.tok[h_], q.foco):
                    a, b = f.np(h_)
                    sp = f.texto_span(a, b)
                    if sp:
                        d = (-1, _dist(t.i, anc), 0)
                        if best is None or d < best[0]:
                            best = (d, sp)
                        continue
                if nrm(q.raw).lstrip("¿ ").startswith(("cual ", "cuales ")) and t.d == "root" and any(f.tok[c].d == "cop" for c in f.hij.get(t.i, [])):
                    sj_ = next((c for c in f.hij.get(t.i, []) if f.tok[c].d.startswith("nsubj")), None)
                    if sj_ is not None:
                        ms_ = _mencion_en(f, *f.np(sj_))
                        if ms_ and ind.familia_de(ms_[0][2]) not in set(q.ents):
                            return ms_[0][3], ms_[0][3], 1.0                              # «Zaragoza es la ciudad mas poblada»: el sujeto de la frase copulativa
                if nrm(q.raw).lstrip("¿ ").startswith(("cual ", "cuales ")) and not ajeno(f, t.i, set(q.ents), ind):
                    r_cual = _predicado_cual(f, q, t)
                    if r_cual:
                        return r_cual
                a, b = f.np(t.i)
                sp = f.texto_span(a, b)
                d = (_grado(t, q.foco), _dist(t.i, anc) + (30 if ajeno(f, t.i, set(q.ents), ind) else 0), -(b - a))
                if nrm(q.raw).lstrip("¿ ").startswith(("cual ", "cuales ")):
                    continue                                                           # «cual es X»: repetir el sintagma por el que se pregunta no contesta nada
                if best is None or d < best[0]:
                    best = (d, sp)
        return (best[1], best[1], 1.0) if best else None
    if q.verbo:
        for v in f.tok:
            if v.u == "VERB" and _coincide(v, q.verbo):
                for c in f.hij.get(v.i, []):
                    if f.tok[c].d == "obj" and c > v.i and f.tok[c].u == "NOUN" and v.d in ("acl", "acl:relcl") and v.h >= 0 and f.tok[v.h].u in ("NOUN", "PROPN") \
                            and any(f.tok[x].nf == "que" and f.tok[x].d in ("mark", "obj", "nsubj") for x in f.hij.get(v.i, [])) and any(f.tok[x].d == "det" for x in f.hij.get(c, [])) \
                            and not any(f.tok[x].d == "case" for x in f.hij.get(c, [])):
                        ant_ = v.h
                        qi_ = next((x for x in f.hij.get(v.i, []) if f.tok[x].nf == "que"), None)
                        if f.tok[ant_].d.startswith("nmod") and f.tok[ant_].h >= 0 and f.tok[f.tok[ant_].h].u in ("NOUN", "PROPN") and qi_ is not None and qi_ > 0 and f.tok[qi_ - 1].f == ",":
                            ant_ = f.tok[ant_].h                                         # «una rana sobre una calavera, que…»: la coma separa el relativo del complemento y lo refiere al nucleo
                        a, b = f.np(ant_)                                                # «una rana, que deben encontrar los estudiantes»: el postverbal es el sujeto; lo que se encuentra es el antecedente
                        sp = f.texto_span(a, b)
                        return sp, sp, 0.9
                    if f.tok[c].d in ("obj", "iobj") and f.tok[c].u != "PRON" and not any(f.tok[x].d == "case" for x in f.hij.get(c, [])):
                        a, b = f.np(c)
                        sp = f.texto_span(a, b)
                        if f.tok[c].d == "obj" and c > v.i:
                            mq_ = _miembro_pregunta(f, q, a, b)
                            if mq_:
                                return mq_, mq_, 0.8
                        return sp, sp, 0.8
                    if f.tok[c].d in ("obj", "iobj") and f.tok[c].nf == "que" and v.d in ("acl", "acl:relcl") and v.h >= 0 and f.tok[v.h].u in ("NOUN", "PROPN"):
                        a, b = f.np(v.h)                                                 # «una rana ..., que deben encontrar los estudiantes»: lo que se encuentra es el antecedente del relativo
                        sp = f.texto_span(a, b)
                        return sp, sp, 0.9
                    if f.tok[c].d in ("nsubj", "nsubj:pass") and f.tok[c].u == "NOUN" and f.tok[c].i > v.i and not q.ents_ctx and q.verbo.nl in ("aparecer", "existir", "figurar", "surgir", "haber", "yacer", "habitar"):
                        a, b = f.np(c)                                                   # «En ella aparece una famosa rana»: el sujeto pospuesto es lo que aparece
                        sp = f.texto_span(a, b)
                        return sp, sp, 0.8
    return None


def ext_def(ind, f, q, anc):
    r_q = _entrecomillado(f, q)
    if r_q:
        return r_q
    if not q.foco:
        return None
    for t in f.tok:                               # «clorofila, el pigmento verde que absorbe la luz»: lo que sigue a la coma define al nombre
        if t.u == "NOUN" and _coincide(t, q.foco) and _grado(t, q.foco) == 0 and t.i + 3 < len(f.tok) and f.tok[t.i + 1].f == ",":
            k = t.i + 2
            while k < len(f.tok) and f.tok[k].u == "DET":
                k += 1
            if k < len(f.tok) and f.tok[k].u == "NOUN" and k > t.i + 2:
                fin = k
                while fin + 1 < len(f.tok) and f.tok[fin + 1].f not in (",", ".", ";"):
                    fin += 1
                seg = f.tok[t.i + 2:fin + 1]
                antes_que = []
                for x in seg:
                    if x.nf in ("que", "donde", "cuyo", "cuya"):
                        break
                    antes_que.append(x)
                if not any(x.u == "CCONJ" for x in antes_que) and not any(x.u == "VERB" for x in antes_que) and fin >= k:
                    sp_ = f.texto_span(t.i + 2, fin)
                    if sp_:
                        return sp_, sp_, 1.0
    for t in f.tok:
        if t.u in ("NOUN", "PROPN") and _coincide(t, q.foco):
            cop = any(f.tok[c].d == "cop" for c in f.hij.get(t.i, []))
            suj = t.d.startswith("nsubj") and t.h >= 0 and (f.tok[t.h].nl == "ser" or any(f.tok[c].d == "cop" for c in f.hij.get(t.h, [])))
            if (t.d == "root" and cop) or suj or t.d == "appos":
                return "", "", 1.0
            if any(f.tok[c].d.startswith("acl") for c in f.hij.get(t.i, [])):          # «el de los nomadas, que se mueven por grandes territorios»
                return "", "", 0.8
    return None


CONSEC = [("razon", "por", "la", "cual"), ("razon", "por", "la", "que"), ("motivo", "por", "el", "cual"), ("motivo", "por", "el", "que"), ("por", "lo", "que"), ("por", "lo", "cual"),
          ("por", "eso"), ("por", "ello"), ("de", "ahi", "que"), ("por", "este", "motivo"), ("por", "esta", "razon")]


def _causa_previa(f, q):
    """«…, donde perdio el uso de la mano izquierda, razon por la cual se le aposto el Manco»: lo que se pregunta es la consecuencia; la causa es la clausula anterior."""
    nf = [t.nf for t in f.tok]
    cl = [k for k in q.claves if k.kind in ("verbo", "cont", "foco") and k.nl not in GENERICOS]
    for i in range(len(nf)):
        for pat in CONSEC:
            if tuple(nf[i:i + len(pat)]) != pat:
                continue
            ant = [t for t in f.tok[:i] if t.u != "PUNCT"]
            pos = [t for t in f.tok[i + len(pat):] if t.u != "PUNCT"]
            ma = sum(1 for k in cl if any(_coincide(t, k) for t in ant))
            mp = sum(1 for k in cl if any(_coincide(t, k) for t in pos))
            if mp <= ma or mp == 0:
                continue
            ini = 0
            for j in range(i - 1, -1, -1):
                if nf[j] in ("donde", "cuando", "mientras", "pues") and j < i - 2:
                    ini = j + 1
                    break
            fin = i - 1
            while fin > ini and f.tok[fin].u == "PUNCT":
                fin -= 1
            if fin - ini >= 2:
                sp = f.texto_span(ini, fin)
                return sp, sp, 1.0
    return None


def ext_causa(ind, f, q, anc):
    r_prev = _causa_previa(f, q)
    if r_prev:
        return r_prev
    for t in f.tok:                      # «recibio el Nobel, no por la relatividad, sino por su explicacion del efecto fotoelectrico»
        if t.nf == "sino" and t.i + 2 < len(f.tok) and f.tok[t.i + 1].nf in ("por", "a", "debido", "gracias", "para") and any(f.tok[j].nf == "no" for j in range(max(0, t.i - 12), t.i)):
            b = len(f.tok) - 1
            for x in f.tok[t.i + 2:]:
                if x.f in (".", ";"):
                    b = x.i - 1
                    break
            sp = f.texto_span(t.i + 1, b)
            if len(sp) > 6:
                return sp, sp, 1.0
    for t in f.tok:
        if (t.nf in ("porque", "debido") or (t.nf == "ya" and t.i + 1 < len(f.tok) and f.tok[t.i + 1].nf == "que") or t.nf in ("gracias",)) and t.i > 0:
            b = len(f.tok) - 1
            for x in f.tok[t.i + 3:]:
                if x.f in (".", ";"):
                    b = x.i - 1
                    break
            sp = f.texto_span(t.i, b)
            if len(sp) > 8:
                return sp, sp, 1.0
    for t in f.tok:                                                  # «a causa de una anemia», «como consecuencia de», «por culpa de»
        if t.nf in ("causa", "consecuencia", "culpa", "raiz", "efecto") and t.i >= 1 and t.i + 1 < len(f.tok) and f.tok[t.i + 1].nf == "de" and f.tok[t.i - 1].nf in ("a", "por", "como", "de"):
            a = t.i - 1
            if t.nf == "consecuencia" and a >= 1 and f.tok[a - 1].nf == "como":
                a -= 1
            b = len(f.tok) - 1
            for y in f.tok[t.i + 2:]:
                if y.f in (".", ";"):
                    b = y.i - 1
                    break
            sp = f.texto_span(a, b)
            if len(sp) > 8:
                return sp, sp, 1.0
    if q.verbo:                                                      # «se cazaba por su piel»: la causa es el «por ...» pegado al verbo preguntado
        for v in f.tok:
            if v.u in ("VERB", "AUX") and _coincide(v, q.verbo) and _grado(v, q.verbo) <= 2:
                for x in f.tok[v.i + 1:v.i + 5]:
                    if x.f in (",", ".", ";"):
                        break
                    if x.nf == "por" and x.u == "ADP" and x.i + 1 < len(f.tok):
                        a, b = f.np(f.tok[x.i].h if f.tok[x.i].h > x.i else x.i + 1)
                        b = max(b, x.i + 1)
                        sp = f.texto_span(x.i, b)
                        if len(sp) > 6:
                            return sp, sp, 0.85
    for t in f.tok:                                                  # «se debe a un gen recesivo», «deben su coloracion a un gen»
        if t.nl == "deber" and t.u in ("VERB", "AUX") and t.i > 0:
            for x in f.tok[t.i + 1:t.i + 6]:
                if x.nf == "a" and x.u == "ADP":
                    b = len(f.tok) - 1
                    for y in f.tok[x.i + 2:]:
                        if y.f in (".", ";"):
                            b = y.i - 1
                            break
                    sp = f.texto_span(x.i, b)
                    if len(sp) > 6:
                        return sp, sp, 0.95
    mejor = None
    for t in f.tok:                                                  # «obtuvo el Nobel por el descubrimiento del polonio»: un «por ...» que no es el agente de un participio
        if t.nf == "por" and t.u == "ADP" and t.i > 1 and t.i + 2 < len(f.tok):
            ant = f.tok[t.i - 1]
            if f.tok[t.i + 1].nf in ("lo", "ello", "eso", "esto", "tanto") or (f.tok[t.i + 1].nf in ("la", "el") and f.tok[t.i + 2].nf in ("cual", "que")):
                continue                                                          # «por lo que», «por la cual»: conector de consecuencia, no causa
            if re.search(r"(?:ad[oa]s?|id[oa]s?)$", ant.nf) or IRREG_PART.match(ant.nf) or f.tok[t.i + 1].u == "PROPN":
                continue
            sig_ = f.tok[t.i + 1]
            if sig_.u == "NUM" or sig_.nf in ("mas", "menos", "medio", "media", "poco", "mucho", "tanto", "ahora", "entonces") or _es_num(sig_) \
                    or any(x_.nl in TEMPN or x_.nl in UNID_T for x_ in f.tok[t.i + 1:t.i + 4] if x_.u == "NOUN"):
                continue                                                      # «por mas de un ano», «por 2 a 1», «por tercera vez»: duracion o marcador, no causa
            b = t.i + 1
            while b + 1 < len(f.tok) and b - t.i < 10 and f.tok[b + 1].u in ("DET", "NOUN", "PROPN", "ADJ", "ADP", "CCONJ", "NUM") and f.tok[b + 1].f not in (",", ".", ";"):
                b += 1
            while f.tok[b].u in ("ADP", "CCONJ", "DET"):
                b -= 1
            d = _dist(t.i, anc)
            if b > t.i and (mejor is None or d < mejor[0]):
                mejor = (d, t.i, b)
    if mejor:
        sp = f.texto_span(mejor[1], mejor[2])
        return sp, sp, 0.6
    for t in f.tok:                                                  # «lo motivaron a rechazar», «para convencerlo»: causa o motivo dicho con un verbo
        if t.nl in ("motivar", "deber", "causar", "provocar", "llevar", "explicar", "razon", "motivo") and t.i > 0 and t.nl not in {c.nl for c in q.claves}:
            sp = f.texto
            return "", "", 0.3
    return None


FUNCION = {"permitir", "ayudar", "facilitar", "evitar", "impedir", "proteger", "servir", "favorecer", "hacer", "causar", "provocar", "ofrecer", "aumentar", "reducir", "mejorar"}


USO = {"utilizar", "usar", "emplear", "servir", "aprovechar"}


def ext_finalidad(ind, f, q, anc):
    neg = {t.i for t in f.tok if t.nf == "no"}
    if q.verbo and q.verbo.nl in USO:                         # «la glucosa se utiliza como fuente de energia»
        for v in f.tok:
            if v.u in ("VERB", "AUX") and (v.nl in USO or _coincide(v, q.verbo)):
                for k in range(v.i + 1, min(len(f.tok), v.i + 10)):
                    if f.tok[k].f in (",", ";", "."):
                        break
                    if f.tok[k].nf == "como" and k + 1 < len(f.tok):
                        fin = k
                        while fin + 1 < len(f.tok) and f.tok[fin + 1].f not in (",", ";", "."):
                            fin += 1
                        sp = f.texto_span(k, fin)
                        return sp, sp, 1.0

    for t in f.tok:
        if t.nf == "para" and t.i + 1 < len(f.tok) and f.tok[t.i + 1].u == "VERB" and t.i > 0:
            b = len(f.tok) - 1
            for x in f.tok[t.i + 2:]:
                if x.f in (".", ";", ","):
                    b = x.i - 1
                    break
            sp = f.texto_span(t.i, b)
            return sp, sp, 0.3 if any(i < t.i and t.i - i <= 8 for i in neg) else 1.0
    for t in f.tok:                                                  # «hace que parezca mas grande», «le permite sobrevivir», «ayuda al leon en los combates»
        if t.nl in FUNCION and t.u == "VERB" and t.i > 0 and not any(i < t.i and t.i - i <= 3 for i in neg):
            if t.nl == "hacer" and not (t.i + 1 < len(f.tok) and f.tok[t.i + 1].nf == "que"):
                continue
            b = len(f.tok) - 1
            for x in f.tok[t.i + 1:]:
                if x.f in (".", ";"):
                    b = x.i - 1
                    break
            sp = f.texto_span(t.i, b)
            if len(sp) > 12:
                return sp, sp, 0.8
    return None


def ext_nombre(ind, f, q, anc):
    """«como se llama X», «cual es el nombre cientifico de X»: «llamado Y», «conocido como Y», o el binomio entre parentesis tras X."""
    tk, n = f.tok, len(f.tok)
    cient = "cientifico" in nrm(q.raw) or "cientificamente" in nrm(q.raw)
    for m in re.finditer(r"([^\W\d_]+)\s*\(([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [a-záéíóúñ]{2,})(?: [a-záéíóúñ]{2,})?)\)", f.texto):        # el parser no ve los parentesis: «El leon (Panthera leo)»
        w = nrm(m.group(1))
        if any(w in ind.tokens_fam.get(e, ()) for e in q.ents) or any(w == c_.nl or w == nrm(c_.nl) for c_ in q.claves) or any(_coincide(T(0, m.group(1), "NOUN", -1, "dep", w), c_) for c_ in q.claves):
            return m.group(2), m.group(2), 1.0
    for i, t in enumerate(tk):
        if t.f == "(" and i + 3 < n and i > 0:
            cierre = next((j for j in range(i + 1, min(n, i + 6)) if tk[j].f == ")"), None)
            if cierre and cierre - i in (3, 4) and tk[i + 1].f[:1].isupper() and tk[i + 2].f[:1].islower() and all(x.f.isalpha() for x in tk[i + 1:cierre]):
                if any(a <= i - 1 <= b + 1 and ind.familia_de(k) in q.ents for a, b, k, _, _ in f.ment) or any(_coincide(tk[i - 1], c_) for c_ in q.claves) or any(tk[i - 1].nf in ind.tokens_fam.get(e, ()) for e in q.ents):
                    sp = f.texto_span(i + 1, cierre - 1)
                    return sp, sp, 1.0 if cient or True else 0.6
    if cient:
        return None
    for k in q.claves:                                                       # «su hermana Bronislawa», «el rio Manzanares»: sustantivo + nombre propio
        if k.kind not in ("cont", "foco"):
            continue
        for t in tk:
            if t.u == "NOUN" and _coincide(t, k) and t.i + 1 < n and tk[t.i + 1].u == "PROPN":
                for a, b, kk, s_, _ in f.ment:
                    if a == t.i + 1:
                        return s_, s_, 0.95
    for i, t in enumerate(tk):
        if t.nl in ("llamar", "denominar", "conocer", "apodar", "bautizar") and (t.u in ("VERB", "ADJ", "AUX")):
            j = i + 1
            if j < n and tk[j].nf in ("como", "por"):
                j += 1
            if j < n and tk[j].u in ("PROPN", "NOUN", "X", "ADJ", "DET") and not tk[j].f == ",":
                m = j
                while m < n and m - j < 6 and tk[m].u in ("PROPN", "NOUN", "X", "ADJ", "DET", "ADP", "NUM") and tk[m].f not in (",", ".", ";"):
                    if tk[m].u == "ADP" and tk[m].nf not in ("de", "del"):
                        break
                    m += 1
                if m > j:
                    sp = f.texto_span(j, m - 1)
                    return sp, sp, 0.9
    return None


def ext_significado(ind, f, q, anc):
    """«que significa Platypus»: lo que va entre comillas tras la palabra, o «significa ...»."""
    m = re.search(r"significa(?:ndo)?\s+([^,.;]{3,80})", f.texto)
    if m:
        return m.group(1).strip(), m.group(1).strip(), 0.95
    citas = re.findall(r"[«‘“\"]([^»’”\"]{2,60})[»’”\"]", f.texto)
    if citas:
        return citas[-1], citas[-1], 0.9
    return None


EXT = {"significado": ext_significado, "nombre": ext_nombre, "def": ext_def, "cuando": ext_cuando, "donde": ext_donde, "cuanto": ext_cuanto, "quien": ext_quien_pl, "que": ext_que, "porque": ext_causa, "para_que": ext_finalidad}


# ====================================================== composicion ======================================================================
def _negada(f: Frase, anc: List[int]) -> bool:
    for a in anc:
        for j in range(max(0, a - 3), min(len(f.tok), a + 2)):
            if f.tok[j].nf in NEG and f.tok[j].u in ("ADV", "PART", "ADP", "CCONJ", "SCONJ", "X"):
                return True
        for c in f.hij.get(a, []):
            if f.tok[c].nf in NEG and f.tok[c].d in ("advmod", "case", "neg", "cc"):
                return True
    return False


def perfil(ind: Indice, fid: str, n: int = 5) -> List[Frase]:
    cands = []
    primera = min([f.k for f in ind.fr if fid in f.fams] or [0])
    for f in ind.fr:
        explicita = fid in f.fams
        if not (explicita or fid in f.impl):
            continue
        sc = 1.0 if explicita else 0.1
        ms = [(a, b, k) for a, b, k, _, _ in f.ment if ind.familia_de(k) == fid]
        for t in f.tok:
            if t.d.startswith("nsubj") and any(a <= t.i <= b for a, b, _ in ms):
                h = f.tok[t.h] if t.h >= 0 else None
                if h is not None and (any(f.tok[c].d == "cop" for c in f.hij.get(h.i, [])) or h.nl == "ser"):
                    sc += 2.5 + (1.0 if any(f.tok[c].nf in ("es", "son") for c in f.hij.get(h.i, [])) or h.nf in ("es", "son") else 0.0)
                else:
                    sc += 1.5
        if f.suj == fid:
            sc += 1.0
        for a, b, _ in ms:
            if b + 2 < len(f.tok) and f.tok[b + 1].f == "," and f.tok[b + 2].u in ("DET", "NOUN", "ADJ", "NUM"):
                sc += 1.0
            if a <= 3:
                sc += 0.5
        if f.k == primera:
            sc += 0.8
        if tiempos(f):
            sc += 0.4
        dig = sum(1 for t in f.tok if t.u == "NUM" or t.nf.isdigit())
        if dig > 0.35 * max(1, len(f.tok)):
            sc -= 3.0
        if len(f.texto) > 240:
            sc -= 1.0
        if len(f.tok) < 4:
            sc -= 1.5
        if re.match(r"\W*(?:«|\")", f.texto):
            sc -= 1.0
        cands.append([sc, f])
    elegidas, secs = [], Counter()
    while cands and len(elegidas) < n:
        usados = set().union(*[e.lem for e in elegidas]) if elegidas else set()
        for c in cands:
            sim = len(c[1].lem & usados) / max(1, len(c[1].lem))
            c.append(c[0] - 1.2 * secs[c[1].sec] - 1.5 * sim)
        cands.sort(key=lambda c: (-c[-1], c[1].k))
        sc, f = cands[0][0], cands[0][1]
        cands = [[c[0], c[1]] for c in cands[1:]]
        elegidas.append(f)
        secs[f.sec] += 1
    resto = sorted(elegidas[1:], key=lambda f: (f.doc, f.k))
    return elegidas[:1] + resto


def _prefijo_corr(q: Q) -> str:
    if not q.corr:
        return ""
    return " ".join(f"(Entiendo «{a}» como «{cap(b)}».)" for a, b in q.corr) + " "


def contestar(ind: Indice, q: Q, final: bool = False) -> Optional[Tuple[str, List[str]]]:
    """-> (texto, familias de contexto) o None."""
    pre = _prefijo_corr(q)
    # ---------------- perfil: «quien es X», «que sabes de X», «hablame de X» --------------------------------------------------------
    if q.tipo == "perfil":
        if q.ents:
            try:
                from . import relaciones as _R0
                r0 = _R0.parentesco(ind, q)
            except Exception:                                                                # noqa
                if os.environ.get("LCM_DEBUG"):
                    raise
                r0 = None
            if r0:
                return pre + r0, q.ents
        if q.ents:
            fid = q.ents[0]
            fs = perfil(ind, fid)
            if not fs:
                return None
            return pre + ind.disp[fid] + ", por lo que he leído:\n" + "\n".join("• «" + cita(f, "", 230) + "»" for f in fs), [fid]
        return None
    if q.tipo != "perfil" and not getattr(q, "_sub", False):
        try:
            from . import relaciones as _R
            r_rel = _R.intentar(ind, q, final)
        except Exception:                                                                   # noqa  (una pregunta rara nunca debe romper la conversacion)
            if os.environ.get("LCM_DEBUG"):
                raise
            r_rel = None
        if r_rel:
            return pre + r_rel[0], r_rel[1]
    if q.desconocidos and (not q.ents or q.ents_ctx) and q.tipo != "si_no":     # el tema de la pregunta es una palabra que nunca se ha leido: contestar con otra cosa seria inventar
        return None
    rk = ranking(ind, q, 500 if q.tipo == "nombre" else 12)
    if not rk:
        return None
    mejor_g, mejor_c, mejor_f = rk[0]
    es_ctx = q.ents_ctx
    lst = _lista(ind, q, rk, mejor_c)
    if lst:
        return pre + lst, q.ents
    if q.tipo in EXT:
        # ---- la mejor respuesta concreta entre las mejores frases (puntuacion de la frase + calidad de lo extraido) -------------------
        cands = []
        for g, c, f in rk:
            if c < max(0.3, 0.55 * mejor_c) or (q.ents and not es_ctx and any(nivel_ent(f, e) == 0 for e in q.ents if e not in q.debiles)):
                continue
            r = EXT[q.tipo](ind, f, q, anclas(ind, f, q))
            if r and r[0] and re.match(r"(?:(?:en|de|desde|hasta|por|a|con)\s+)?(?:este|esta|estos|estas|ese|esa|esos|esas|aquel|aquella|dicho|dicha|dichos|dichas|tal)\b", nrm(r[0])):
                r = (r[0], r[1], r[2] * 0.3)                                  # «en esta area»: no dice nada sin la frase anterior
            if r and q.foco and q.tipo in ("quien", "que", "donde", "cuanto"):
                s0_ = next((t_[0] for t_ in q.toks if t_[2] == q.foco.nl and t_[1] == "NOUN"), None)
                if s0_ and not any(t.nf == s0_ for t in f.tok if t.u == "NOUN") and any(t.nl == q.foco.nl for t in f.tok):
                    r = (r[0], r[1], r[2] * 0.85)                             # «su padre» no es «sus padres»: el numero tambien cuenta
            if r and q.verbo and q.verbo.nl not in GENERICOS and q.tipo in ("quien", "que", "cuando", "donde", "causa", "porque", "para_que", "como"):
                gt_ = [t for t in f.tok if t.u != "PUNCT" and _coincide(t, q.verbo)]
                gv = [_grado(t, q.verbo) for t in gt_]
                if q.ents and q.tipo != "quien" and gt_ and all(_sujeto_ajeno(ind, f, t, set(q.ents)) for t in gt_ if t.u in ("VERB", "AUX")) and any(t.u in ("VERB", "AUX") for t in gt_):
                    r = (r[0], r[1], r[2] * 0.3)                              # «En 1906 Pierre murio...»: el que hace la accion es otra persona nombrada
                if not gv:
                    r = (r[0], r[1], r[2] * 0.75) if (c >= 0.65 or q.tipo not in ("porque", "causa", "para_que", "como")) else None       # la frase ni siquiera lleva el verbo por el que se pregunta: la respuesta sale de su vecindad, no de la accion
                elif min(gv) == 2 and not q.foco:
                    r = (r[0], r[1], r[2] * 0.85)                             # solo lo nombra un sinonimo
            if r:
                flojas = 0 if es_ctx else sum(1 for e in q.ents if nivel_ent(f, e) < 0.6 and ind.especifica(e) and e not in q.debiles)
                def _tvg(gmax):
                    return bool(q.verbo) and q.verbo.nl not in GENERICOS and q.tipo in ("quien", "cuando", "donde") \
                        and any((t.u in ("VERB", "AUX") or (t.u == "ADJ" and (re.search(r"(?:ad[oa]s?|id[oa]s?)$", t.nf) or IRREG_PART.match(t.nf)))) and _coincide(t, q.verbo) and _grado(t, q.verbo) <= gmax
                                and not (q.ents and (_sujeto_ajeno(ind, f, t, set(q.ents)) or ajeno(f, t.i, set(q.ents), ind))) for t in f.tok) \
                        and all(nivel_ent(f, e) >= 0.65 for e in q.ents if e not in q.debiles) and (q.tipo != "cuando" or bool(re.search(r"\d", r[0])))
                tv_ = (1 if _tvg(1) else (0.5 if _tvg(2) else 0))
                anyo_ = 0.0
                if q.tipo in ("quien", "que", "donde", "causa", "porque", "para_que", "como", "cuanto", "nombre"):
                    ys_ = set(re.findall(r"(?<!\d)\d{4}(?!\d)", q.raw))
                    if ys_ and not any(y_ in f.texto for y_ in ys_):
                        anyo_ = 1.2                                         # «¿con quien se caso en 1903?»: la frase de otro año no responde
                cands.append((g + 1.6 * r[2] - 0.8 * flojas - anyo_, c, f, r, tv_))
        if cands:
            if any(x[4] == 1 for x in cands):                                    # una frase con el verbo por el que se pregunta gana a otra que solo comparte los sustantivos
                cands = [(x[0] + (0 if x[4] else -1.5),) + x[1:] for x in cands]
            cands = [x[:4] for x in cands]
            cands.sort(key=lambda x: -x[0])
            _, c, f, (resp, sp, cal) = cands[0]
            solida = bool(q.ents) and not es_ctx and all(nivel_ent(f, e) >= 1.0 for e in q.ents)      # la entidad por la que se pregunta esta en la frase: se admite menos cobertura
            if c >= (0.4 if (final or (solida and cal >= 0.6)) else 0.5) and (final or not resp or cal >= 0.5 or q.tipo != "quien"):      # una extraccion de poca calidad (un nombre que pasaba por ahi) solo vale como ultimo recurso
                if not resp:
                    return pre + "Según el texto: «" + cita(f) + "»", q.ents
                return pre + cap(resp) + ". En el texto: «" + cita(f, sp) + "»", q.ents
        if q.tipo in ("porque", "causa"):                                      # «de que murio»: la frase de al lado dice «la causa fue ...»
            for g, c, f in rk[:3]:
                if c < 0.5:
                    continue
                nx = _siguiente(ind, f)
                ce = _causa_explicita(nx) if nx is not None else None
                if ce:
                    return pre + cap(ce) + ". En el texto: «" + cita(nx) + "»", q.ents
        # ---- sin extraccion: la frase mas cercana, solo si encaja bien --------------------------------------------------------------
        if mejor_c >= (0.45 if final else 0.65) and not es_ctx and not _pide_capacidad(q):
            return pre + "Lo más cercano que he leído: «" + cita(mejor_f) + "»", q.ents
        return None
    # ---------------- si/no -------------------------------------------------------------------------------------------------------------
    if q.tipo in ("si_no", "como"):
        if q.tipo == "si_no":
            for g, c, f in rk:
                if c < 0.5:
                    break
                def _clave_ok(k):
                    if any(_coincide(t, k) and (k.kind != "verbo" or (t.u in ("VERB", "AUX") and _grado(t, k) != 2)) for t in f.tok if t.u != "PUNCT"):
                        return True
                    if k.kind == "cont" and k.nl.isdigit() and q.ents and all(nivel_ent(f, e) >= 0.6 for e in q.ents):
                        return True                                               # «el Apolo 11»: el numero es parte del nombre y la frase habla de el sin repetirlo
                    if k.kind == "cont" and _casa_ctx(k, f) >= 0.5 and any(t.u == "PRON" and t.nf in ("lo", "la", "los", "las", "le", "les", "ellos", "ellas", "el", "ella") for t in f.tok):
                        return True                                               # «los recogio»: el pronombre recoge lo dicho antes
                    return False
                if all(_clave_ok(k) for k in q.claves if not (k.kind == "verbo" and k.nl in LIGEROS)) \
                        and all(nivel_ent(f, e) >= 0.45 for e in q.ents) and not q.desconocidos:
                    neg = _negada(f, anclas(ind, f, q))
                    return pre + ("No." if neg else "Sí.") + " En el texto: «" + cita(f) + "»", q.ents
            if ausente(ind, q):
                return None
            if mejor_c >= 0.5 and (final or q.ents) and not (es_ctx and not final) and not _pide_capacidad(q):
                return pre + "No lo sé con certeza. Lo más parecido que he leído: «" + cita(mejor_f) + "»", q.ents
            return None
        if mejor_c >= (0.45 if final else 0.65) and not _pide_capacidad(q):
            return pre + "Lo más cercano que he leído: «" + cita(mejor_f) + "»", q.ents
    return None


def _pide_capacidad(q: Q) -> bool:
    """parche-129: «¿puedes cantar?» se le pide algo a quien contesta; una frase suelta del texto con una palabra parecida no es la respuesta."""
    try:
        from src.language import vida
        return vida.pide_capacidad(getattr(q, "raw", "") or "")
    except Exception:                                                           # noqa
        return False


def _siguiente(ind: Indice, f: Frase) -> Optional[Frase]:
    dk = getattr(ind, "_dk", None)
    if dk is None:
        dk = ind._dk = {(x.doc, x.k): x for x in ind.fr}
    return dk.get((f.doc, f.k + 1))


def _causa_explicita(f: Frase) -> Optional[str]:
    """«La causa oficial fue una embolia pulmonar»: el sujeto es la palabra causa/motivo/razon y lo que se predica es la respuesta."""
    for t in f.tok:
        if t.nl in ("causa", "motivo", "razon") and t.d.startswith("nsubj") and t.h >= 0 and f.tok[t.h].u in ("NOUN", "PROPN", "ADJ"):
            a, b = f.np(t.h)
            sp = f.texto_span(a, b)
            if sp:
                return sp
    return None


def _tronco(w: str) -> str:
    """Sin genero ni numero: hijo/hija/hijos -> hij."""
    w = w[:-1] if w.endswith("s") and len(w) > 3 else w
    return w[:-1] if len(w) > 3 and w[-1] in "aeo" else w


CATEGORIAS = {"obra", "libro", "escrito", "texto", "titulo", "pais", "nacion", "lugar", "persona", "personaje", "cosa", "objeto", "nombre", "animal", "planta", "ciudad", "region", "territorio"}   # clases genericas: el texto da el ejemplar («Don Quijote»), no la palabra de la clase


def ausente(ind: Indice, q: Q) -> Optional[str]:
    """Palabra de contenido de la pregunta (sustantivo/verbo propio) que no aparece en ninguna frase leida, ni sus sinonimos: de eso no hay nada."""
    tr = getattr(ind, "_troncos", None)
    if tr is None:
        tr = ind._troncos = {_tronco(w) for w in list(ind.idf) + list(ind.vocab_all)}
    for k in q.claves:
        if k.kind not in ("cont", "foco") or k.w < 1.5 or k.nl in LIGEROS:
            continue
        if k.nl in CATEGORIAS and k is q.foco and q.tipo in ("que", "cual") and q.verbo:
            continue
        if k.nl in ind.idf or k.rz in ind.idf_r or k.nl in ind.vocab_all or _tronco(k.nl) in tr:
            continue
        if any(a in ind.idf or raiz(a) in ind.idf_r or _tronco(a) in tr for a in k.alts):
            continue
        if len(k.nl) >= 5 and any(_prefijo(k.nl, w) for w in ind.idf):
            continue
        return k.nl
    return None


def _plural_foco(q: Q) -> bool:
    return bool(q.foco) and any(t[1] == "NOUN" and t[0].endswith("s") and t[0] != t[2] and (t[2] == q.foco.nl or t[0] == q.foco.nl) for t in q.toks)


def _lista(ind: Indice, q: Q, rk, mejor_c: float) -> Optional[str]:
    """«Que premios ha ganado», «que records batio»: pregunta en plural -> varias frases distintas que hablan de eso, en el orden del texto."""
    if q.tipo != "que" or not _plural_foco(q) or q.foco.nl in UNIDADES:
        return None
    hallazgos = []
    for g, c, f in rk:
        if c < max(0.45, 0.6 * mejor_c):
            continue
        if q.ents and not q.ents_ctx and any(nivel_ent(f, e) == 0 for e in q.ents if e not in q.debiles):
            continue
        if not any(t.u in ("NOUN", "PROPN") and _coincide(t, q.foco) and _grado(t, q.foco) <= 1 for t in f.tok):
            continue
        if any(f.k == h.k and f.doc == h.doc for _, h in hallazgos):
            continue
        hallazgos.append((g, f))
    if len(hallazgos) < 2:
        return None
    hallazgos = sorted(hallazgos, key=lambda x: -x[0])[:4]
    hallazgos.sort(key=lambda x: (x[1].doc, x[1].k))
    return "He leído varias cosas sobre eso:\n" + "\n".join("• «" + cita(f, "", 230) + "»" for _, f in hallazgos)


def sin_datos(ind: Indice, q: Q) -> Optional[str]:
    """Honestidad cuando no hay nada: se dice que no se ha leido, en vez de inventar o contestar otra cosa."""
    if q.desconocidos and (not q.ents or q.ents_ctx):
        return "No he leído nada sobre «" + " ".join(q.desconocidos[:3]) + "»."
    au = ausente(ind, q)
    if au and q.tipo != "perfil":
        return "En lo que he leído no aparece nada sobre «" + au + "»" + (" de " + ind.disp[q.ents[0]] if q.ents and not q.ents_ctx else "") + "."
    if q.ents and q.ents_ctx:                                                    # el sujeto se dedujo de la conversacion: no se le atribuye la pregunta
        pf = _protagonista_global(ind)
        return "No he leído nada que conteste a eso." + (" Prueba con «¿qué sabes de " + ind.disp[pf] + "?»." if pf else "")
    if q.ents:
        return "De " + ind.disp[q.ents[0]] + " no he leído nada que conteste a eso. Prueba con «¿qué sabes de " + ind.disp[q.ents[0]] + "?»."
    return None


# ====================================================== entrada ==========================================================================
def _priors(ind: Indice, conv, final: bool) -> List[List[str]]:
    """De quien se habla cuando la pregunta no lo dice: lo ultimo preguntado, lo anterior y, siempre, el protagonista del texto."""
    out = []
    ctx = getattr(conv, "_lec_ctx", None)
    if ctx:
        out.append(list(ctx))
    for h in reversed(getattr(conv, "_lec_hist", None) or []):
        if h and list(h) not in out:
            out.append(list(h))
    fid = _protagonista_global(ind)
    if fid and [fid] not in out:
        out.append([fid])
    return out


def _protagonista_global(ind: Indice) -> Optional[str]:
    gl = Counter()
    for d, fid in ind.protagonista.items():
        if fid:
            gl[fid] += 1
    for fid, _ in gl.most_common(1):
        return fid
    return None


_CORTES = re.compile(r"^[¿\s]*(?:(?:y|oye|por favor|entonces|pues)[,\s]+)*(?:me\s+)?(?:puedes|podr[ií]as|sabr[ií]as|ser[ií]as tan amable de|ser[ií]as capaz de)\s+"
                     r"(?:decirme|indicarme|explicarme|contarme|mencionarme|aclararme|decirnos|decir|indicar|explicar|contar|aclarar)\s+(?P<resto>.+?)[?\s]*$", re.I)
_WH_RESTO = re.compile(r"^(?:cuando|donde|quien|quienes|como|cual|cuales|cuanto|cuanta|cuantos|cuantas|que|por que|para que|a que|en que|de que|con que|a quien|de quien|con quien|adonde)\b")


def sin_cortesia(raw: str) -> Optional[str]:
    """«¿Puedes decirme cuantos anos tiene X?» es la pregunta «¿cuantos anos tiene X?»; «puedes decirme la hora» es una peticion que el texto no contesta (None)."""
    m = _CORTES.match(raw or "")
    if not m:
        return raw
    resto = m.group("resto").strip()
    if re.match(r"^si\s+\S", resto, re.I):
        return "¿" + re.sub(r"^si\s+", "", resto, flags=re.I) + "?"
    if _WH_RESTO.match(nrm(resto)):
        return "¿" + resto + "?"
    imp = "Dime " + resto
    return imp if es_peticion(imp) else None


def responder(conv, raw: str, final: bool = False) -> Optional[str]:
    mem = getattr(conv, "m", None)
    ind = indice(mem) if mem is not None else None
    if ind is None:
        return None
    raw = sin_cortesia(raw)                                                     # parche-129: «¿puedes decirme cuando nacio X?»
    if raw is None:
        return None
    ind._parser = getattr(conv, "parser", None)
    ind._conv = conv
    q = analizar(ind, raw, getattr(conv, "parser", None))
    if q is None:
        return None
    explicito = bool(q.ents) or bool(q.corr)
    if not explicito:                                                           # parche-129: se pregunta por alguien del que solo se habla en la conversacion («marta nacio...»): no es el protagonista del texto
        try:
            from src.language import vida
            if vida.entidades_de_conversacion(mem, raw, lambda w_: w_ in ind.idf or w_ in ind.vocab_all):
                return None
        except Exception:                                                       # noqa
            pass
    solo = False
    if not explicito and q.tipo != "perfil":                                    # una pregunta que se sostiene sola no necesita la entidad de la conversacion
        q0 = copy.copy(q)
        q0.ents, q0.ents_ctx = [], False
        rk0 = ranking(ind, q0, 1)
        solo = bool(rk0) and rk0[0][1] >= 0.62 and rk0[0][0] / rk0[0][1] >= 2.0
    if not explicito and q.tipo != "perfil" and not solo:
        opciones = []
        prot_ = _protagonista_global(ind)
        for n_, pr in enumerate(_priors(ind, conv, final)):
            q2 = copy.copy(q)
            q2.ents, q2.ents_ctx = list(pr), True
            rk = ranking(ind, q2, 1)
            if rk:
                opciones.append((rk[0][0] * (1.0 if n_ == 0 else (0.95 if pr == [prot_] else 0.87)), n_, q2))          # a igualdad, manda lo ultimo de lo que se hablaba
        if not opciones:
            if final:
                conv._lec_ctx = None
                return sin_datos(ind, q)
            return None
        opciones.sort(key=lambda o: (-o[0], o[1]))
        for _, _, q2 in opciones:                                                      # si el primer sujeto no contesta, el siguiente (lo anterior, el protagonista)
            r = contestar(ind, q2, final)
            if r is not None:
                texto, nuevo_ctx = r
                return texto
        if final:
            q0 = copy.copy(q)
            q0.ents, q0.ents_ctx = [], False                                          # sin sujeto deducido: que hable la pregunta sola
            r = contestar(ind, q0, True)
            if r is not None:
                return r[0]
            conv._lec_ctx = None
            return sin_datos(ind, opciones[0][2])
        return None
    elif not explicito and not solo:
        if not final:
            return None
    r = contestar(ind, q, final)
    if r is None:
        if final:
            conv._lec_ctx = None
            return sin_datos(ind, q)
        return None
    texto, nuevo_ctx = r
    if nuevo_ctx and not q.ents_ctx:
        prev = getattr(conv, "_lec_ctx", None)
        if prev and list(prev) != list(nuevo_ctx):
            hist = [h for h in (getattr(conv, "_lec_hist", None) or []) if list(h) != list(prev)] + [list(prev)]
            conv._lec_hist = hist[-3:]
        conv._lec_ctx = list(nuevo_ctx)
    return texto
