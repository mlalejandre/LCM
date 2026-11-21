"""MEMORIA DE RELACIONES: del análisis sintáctico a lo que el LCM necesita guardar.

De cada oración sale una relación:  sujeto(s) — verbo — objeto / atributo — complementos (cada uno con su preposición)
y cada pregunta se analiza con el MISMO analizador: la palabra interrogativa ocupa un hueco (sujeto, objeto, complemento con «de», tiempo,
lugar, cantidad) y se contesta con lo que llena ese hueco en una relación guardada que tenga el mismo verbo y las mismas piezas.

No hay patrones de frase: lo que decide es la función que el analizador aprendió para cada palabra."""
from __future__ import annotations

import os
import re

from .analiza import palabras
from .datos import frases_de

_TIEMPO = ("año", "siglo", "dia", "mes", "hora", "semana", "epoca", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
_NUMS = {"uno", "un", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "veinte", "veinticinco", "treinta", "cuarenta", "cincuenta", "sesenta",
         "setenta", "ochenta", "noventa", "cien", "ciento", "doscientos", "trescientas", "trescientos", "quinientos", "mil", "millon", "varios", "cientos", "miles", "docena", "medio", "mitad"}
_VACIAS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "a", "en", "y", "o", "e", "que", "se", "su", "sus", "lo", "al", "del", "mas", "muy", "este", "esta", "estos", "estas", "es", "son"}


def sa(s):
    return s.lower().translate(str.maketrans("áéíóúü", "aeiouu"))


def _lema(w):
    try:
        from ..nucleo20 import tema as T
        return T.lema(w)
    except Exception:                                    # noqa
        return sa(w)


def limpia(texto):
    """Quita lo que deja un PDF: números de nota pegados («solar1», «propia,10»), líneas partidas y líneas sueltas de tabla."""
    ls = []
    for l in texto.splitlines():
        l = l.strip()
        if not l or re.fullmatch(r"[\d\s.,°%±×\-–*º?~()]+", l):
            continue
        ls.append(l)
    t = " ".join(ls)
    t = re.sub(r"(?<=[a-záéíóúñ»])\d{1,3}(?:\s\d{1,3})*(?![\d.,]*\d)\b", "", t)   # solar1 -> solar ; años12 13 14 -> años
    t = re.sub(r"(?<=[.,;:»)])\s?\d{1,3}(?:\s\d{1,3})*(?=\s+[A-ZÁÉÍÓÚÑ]|\s*$)", "", t)   # «propia,10 El» -> «propia, El»
    t = re.sub(r"\s+\d{1,3}(?:\s\d{1,3}){0,2}\s+(?=[A-ZÁÉÍÓÚÑ][a-záéíóúñ])", " ", t)   # «. 9 El Sol»
    t = re.sub(r"(?<=[a-záéíóúñ»)][,;.:])\d{1,3}(?:\s\d{1,3})*(?=\s)", "", t)        # «la masa,10 y…» -> «la masa, y…»
    t = re.sub(r"\s{2,}", " ", t)
    return t


def _mismo_verbo(a, b):
    """El mismo verbo aunque el lema no haya salido igual («excluyo»/«excluir»): mismo principio."""
    if a == b or (a in ("ser", "estar") and b in ("ser", "estar")):
        return True
    n = min(len(a), len(b))
    k = 0
    while k < n and a[k] == b[k]:
        k += 1
    return k >= 5 or (k >= 4 and k >= n - 2)


def _numero_verbo(forma):
    """'s' o 'p' si el verbo (o su auxiliar) está en tercera persona del singular o del plural; '' si no se sabe."""
    try:
        from ..nucleo20 import morfo as M
        ps = {a[2] for a in (M.analizar(forma.lower()) or []) if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut")}
    except Exception:                                    # noqa
        return ""
    if ps == {"3s"} or ps <= {"1s", "3s"} and "3s" in ps:
        return "s"
    if ps == {"3p"}:
        return "p"
    return ""


def _persona(forma):
    """'1' si el verbo está en primera persona («tengo», «vamos»), '3' si en tercera, '' si no se sabe."""
    try:
        from ..nucleo20 import morfo as M
        ps = {a[2] for a in (M.analizar(forma.lower()) or []) if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut")}
    except Exception:                                    # noqa
        return ""
    if ps and ps <= {"1s", "1p"}:
        return "1"
    if ps & {"3s", "3p"}:
        return "3"
    return ""


def sim_concepto(a, b):
    """Cuánto se parecen dos conceptos (0–1) según los vectores del LCM: los de significado (léxico) y los de tema. 1 si son el mismo."""
    if _mismo_verbo(a, b):
        return 1.0
    if os.environ.get("LCM_SIN_SINONIMOS"):
        return 0.0
    s_ = 0.0
    try:
        from ..nucleo20 import vectores as V
        s_ = float(V.sim(a, b))
    except Exception:                                    # noqa
        return 0.0
    if s_ >= 0.8:
        return s_                                        # se parecen mucho (la regla de la 2.32: «dar»/«ofrecer» 0,80)
    if s_ >= SINONIMO_VECTOR and _comparten_concepto(a, b):
        return s_                                        # 2.33: comparten un concepto del léxico Y se parecen (medido con 18 + 18 parejas de desarrollo)
    return 0.0


SINONIMO_VECTOR = 0.70


def _comparten_concepto(a, b):
    try:
        from ..nucleo20 import acepciones as AC
        w2s, _ = AC._lex(); pos = AC._pos()
        A_ = {x for x in w2s.get(sa(a), ()) if pos.get(x) == "v"}
        B_ = {x for x in w2s.get(sa(b), ()) if pos.get(x) == "v"}
        return bool(A_ & B_)
    except Exception:                                    # noqa
        return False


_PRON = {"lo": ("m", "s", "obj"), "la": ("f", "s", "obj"), "los": ("m", "p", "obj"), "las": ("f", "p", "obj"), "le": ("", "s", "dat"), "les": ("", "p", "dat"),
         "el": ("m", "s", "suj"), "ella": ("f", "s", "suj"), "ellos": ("m", "p", "suj"), "ellas": ("f", "p", "suj"),
         "este": ("m", "s", "suj"), "esta": ("f", "s", "suj"), "estos": ("m", "p", "suj"), "estas": ("f", "p", "suj"),
         "ese": ("m", "s", "suj"), "esa": ("f", "s", "suj"), "esos": ("m", "p", "suj"), "esas": ("f", "p", "suj"), "aquel": ("m", "s", "suj"), "aquella": ("f", "s", "suj")}
_DET_G = {"el": ("m", "s"), "la": ("f", "s"), "los": ("m", "p"), "las": ("f", "p"), "un": ("m", "s"), "una": ("f", "s"), "unos": ("m", "p"), "unas": ("f", "p"),
          "este": ("m", "s"), "esta": ("f", "s"), "estos": ("m", "p"), "estas": ("f", "p"), "ese": ("m", "s"), "esa": ("f", "s"), "esos": ("m", "p"), "esas": ("f", "p"),
          "nuestro": ("m", "s"), "nuestra": ("f", "s"), "nuestros": ("m", "p"), "nuestras": ("f", "p"), "varios": ("m", "p"), "varias": ("f", "p"), "muchos": ("m", "p"), "muchas": ("f", "p"),
          "pocos": ("m", "p"), "pocas": ("f", "p"), "todos": ("m", "p"), "todas": ("f", "p"), "otro": ("m", "s"), "otra": ("f", "s"), "otros": ("m", "p"), "otras": ("f", "p"), "al": ("m", "s"), "del": ("m", "s")}
RECENCIA = [1.0, 0.7, 0.45, 0.3]                       # misma frase, la anterior, dos antes, tres antes


def _es_persona(lema, cat):
    if cat == "PROPN":
        return True
    try:
        from ..nucleo20 import acepciones as AC
        return any(AC.es_persona(x) for x in AC.sentidos(lema))
    except Exception:                                    # noqa
        return False


class Memoria:
    def __init__(self):
        self.R = []          # relaciones
        self.N = []          # sintagmas con número: (número, lema del nombre, texto, frase)
        self.frases = 0
        self.vistas = set()
        self.ultimo_sujeto = None
        self.disc = []                                   # lo mencionado antes: [(sintagma, género, número, papel, nº de frase, persona, posición)]
        self._cur = []

    # ------------------------------------------------------------------ leer
    def _cierra(self):
        self.disc = [x for x in self.disc + self._cur if self.frases - x[4] < len(RECENCIA)]
        self._cur = []

    def lee(self, texto, limpiar=True):
        t = limpia(texto) if limpiar else texto
        for f in frases_de(t):
            if 3 <= len(f.split()) <= 70 and f not in self.vistas:
                self.vistas.add(f)
                self.frases += 1
                try:
                    self._frase(f)
                except Exception:                        # noqa
                    pass
                self._cierra()
        return self

    @staticmethod
    def _hijos(ps, i, fn=None):
        return [p for p in ps if p["cabeza"] == i and (fn is None or p["funcion"] in fn)]

    def _rama(self, ps, i, sin=("acl", "advcl", "parataxis", "appos"), quita_caso=True):
        ids = {i}
        cambio = True
        while cambio:
            cambio = False
            for p in ps:
                if p["cabeza"] in ids and p["i"] not in ids and p["funcion"] not in sin and not (p["cabeza"] == i and p["funcion"] in ("conj", "cc", "punct")):
                    ids.add(p["i"]); cambio = True
        r = [p for p in ps if p["i"] in ids and p["cat"] != "PUNCT"]
        if quita_caso:
            r = [p for p in r if not (p["cabeza"] == i and p["funcion"] in ("case", "mark"))]
        return r

    def _txt(self, r):
        t = " ".join(p["forma"] for p in r)
        return re.sub(r"\ba el\b", "al", re.sub(r"\bde el\b", "del", t))

    def _miembros(self, ps, n):
        """Un nombre y los que van con él: coordinados («Júpiter y Saturno») y aposiciones («los planetas, Mercurio, Venus…»)."""
        out = [n]
        for h in self._hijos(ps, n["i"], ("conj", "appos")):
            out += self._miembros(ps, h)
        return out

    def _gn(self, ps, n):
        """Género y número de un sintagma: por su determinante; si no, por la terminación del nombre."""
        dets = [p for p in ps if p["cabeza"] == n["i"] and p["funcion"] == "det"]
        for d in dets:
            g = _DET_G.get(sa(d["forma"]))
            if g:
                return g
        def por_final(w, cat):
            num_ = "p" if w.endswith("s") and cat != "PROPN" else "s"
            base = w[:-1] if num_ == "p" else w
            gen_ = "f" if base.endswith(("a", "cion", "dad", "tud")) else ("m" if base.endswith(("o", "or", "an", "on")) else "")
            return gen_, num_
        gen, num = por_final(sa(n["forma"]), n["cat"])
        if n["cat"] == "PROPN" or not gen:               # «Mi vecina Carmen»: el nombre propio no dice nada; lo dice «vecina»
            for q in ps:
                if q["cabeza"] == n["i"] and q["funcion"] in ("amod", "appos", "flat", "nmod") and q["cat"] in ("NOUN", "ADJ"):
                    g2, n2 = por_final(sa(q["forma"]), q["cat"])
                    if g2:
                        return g2, num
        return gen, num

    def _antecedentes(self, ps, n):
        """Candidatos para un pronombre, con su probabilidad: concuerdan en género y número; pesa lo reciente, el mismo papel y si es persona."""
        g, num, tipo = _PRON[sa(n["forma"])]
        verbo = n["cabeza"]
        cand = []
        for (sn, ga, na, rol, k, per, pos) in self.disc + self._cur:
            if k == self.frases and pos >= n["i"]:
                continue                                 # de la misma frase, solo lo que va antes
            if k == self.frases and rol == "nsubj" and sn.get("_verbo") == verbo:
                continue                                 # «el macho LO protege»: lo no es el macho
            d = self.frases - k
            if d >= len(RECENCIA) or na != num or (g and ga and ga != g):
                continue
            pt = RECENCIA[d]
            if tipo == "suj":
                pt *= (1.0 + (0.5 if rol == "nsubj" else 0.0) + (0.4 if per else 0.0)) * (1.0 if per else 0.4)
            elif tipo == "obj":
                pt *= 1.0 + (0.4 if rol == "obj" else 0.0)
            else:
                pt *= 1.0 + (0.5 if per else -0.5)
            cand.append((pt, sn))
        mejor = {}
        for pt, sn in cand:
            k_ = sn["txt"].lower()
            if k_ not in mejor or pt > mejor[k_][0]:
                mejor[k_] = (pt, sn)
        tot = sum(x[0] for x in mejor.values())
        return sorted(((x[0] / tot, x[1]) for x in mejor.values()), key=lambda z: -z[0]) if tot else []

    def _sn(self, ps, n, fuera=()):
        if n["cat"] == "PRON" and sa(n["forma"]) in _PRON and not os.environ.get("LCM_SIN_PRONOMBRES"):
            alts = self._antecedentes(ps, n)
            if alts:
                top = alts[0][1]
                return {"txt": top["txt"], "h": top["h"], "hs": top["hs"], "lemas": top["lemas"], "prep": " ".join(sa(p["forma"]) for p in self._hijos(ps, n["i"], ("case",))),
                        "cat": top["cat"], "alts": [(round(p_, 3), a_) for p_, a_ in alts[:4]], "p": round(alts[0][0], 3)}
        r = self._rama(ps, n["i"])
        ms = self._miembros(ps, n)
        todo = self._rama(ps, n["i"], sin=("acl", "advcl", "parataxis"))
        ids = set()
        def baja(i):
            ids.add(i)
            for p in ps:
                if p["cabeza"] == i and p["funcion"] not in ("acl", "advcl", "parataxis") and p["i"] not in ids and not (i == n["i"] and p["funcion"] in fuera):
                    baja(p["i"])
        baja(n["i"])
        completo = [p for p in ps if p["i"] in ids and not (p["cabeza"] == n["i"] and p["funcion"] in ("case", "mark"))]
        while completo and completo[-1]["cat"] == "PUNCT":
            completo.pop()
        while completo and completo[0]["cat"] == "PUNCT":
            completo.pop(0)
        txt = re.sub(r"\s+([,.;:])", r"\1", self._txt(completo))
        return {"txt": txt, "h": _lema(n["forma"]), "hs": [_lema(m["forma"]) for m in ms], "lemas": {_lema(p["forma"]) for p in completo if sa(p["forma"]) not in _VACIAS and p["cat"] != "PUNCT"},
                "prep": " ".join(sa(p["forma"]) for p in self._hijos(ps, n["i"], ("case",))), "cat": n["cat"]}

    def _frase(self, f):
        ps = palabras(f)
        por_i = {p["i"]: p for p in ps}
        for p in ps:                                     # sintagmas con número («ocho planetas», «cuatro planetas enanos»)
            if p["funcion"] == "nummod" and p["cabeza"] in por_i:
                n = por_i[p["cabeza"]]
                self.N.append((p["forma"].lower(), _lema(n["forma"]), self._sn(ps, n), f))
        ctx = {_lema(p["forma"]) for p in ps if p["cat"] in ("NOUN", "PROPN", "VERB", "ADJ", "NUM")}
        self._cur = []
        for p in ps:                                     # lo que se menciona en esta frase, para los pronombres que vengan
            if p["cat"] in ("NOUN", "PROPN") and p["funcion"] in ("nsubj", "obj", "obl", "iobj", "nmod", "root", "dislocated"):
                sn_ = self._sn(ps, p)
                sn_["_verbo"] = p["cabeza"]
                g_, n_ = self._gn(ps, p)
                self._cur.append((sn_, g_, n_, "nsubj" if p["funcion"] == "dislocated" else p["funcion"], self.frases, _es_persona(_lema(p["forma"]), p["cat"]), p["i"]))
        hechas = {}
        nucleos = [p for p in ps if (p["cat"] in ("VERB", "AUX") and p["funcion"] not in ("aux", "cop")) or self._hijos(ps, p["i"], ("cop",))]
        for v in sorted(nucleos, key=lambda p: (p["funcion"] != "root", p["i"])):
            hijos = self._hijos(ps, v["i"])
            cop = next((h for h in hijos if h["funcion"] == "cop"), None)
            suj = next((h for h in hijos if h["funcion"] == "nsubj"), None)
            if not os.environ.get("LCM_SIN_CONCORDANCIA"):
                nv = _numero_verbo(next((h["forma"] for h in hijos if h["funcion"] in ("aux", "cop")), v["forma"]))
                rechazado = False
                if suj is not None and suj["cat"] in ("NOUN", "PROPN") and nv and self._gn(ps, suj)[1] != nv and not self._hijos(ps, suj["i"], ("conj",)):
                    suj = None; rechazado = True                          # «Su hijo lo conduce LOS DOMINGOS»: un sujeto plural no va con «conduce»
                if suj is None:
                    dis = next((h for h in hijos if h["funcion"] == "dislocated" and h["cat"] in ("NOUN", "PROPN") and (not nv or self._gn(ps, h)[1] == nv or self._hijos(ps, h["i"], ("conj",)))), None)
                    if dis is not None:
                        cl = next((h for h in hijos if h["funcion"] == "obj" and h["cat"] == "PRON" and sa(h["forma"]) in _PRON), None)
                        doble = cl is not None and self._gn(ps, dis) == _PRON[sa(cl["forma"])][:2] and any(h["funcion"] == "nsubj" for h in hijos) and not rechazado
                        if not doble:
                            suj = dis                    # «Una vecina LOS llamó»: lo dislocado es el sujeto si no es el objeto repetido por el pronombre
            S = None
            if suj is not None and sa(suj["forma"]) in ("que", "quien", "cual", "cuales") and v["funcion"] == "acl" and v["cabeza"] in por_i:
                S = self._sn(ps, por_i[v["cabeza"]])     # relativa: el sujeto es aquello de lo que se habla
            elif suj is not None:
                S = self._sn(ps, suj)
            elif v["funcion"] == "root" and next((h for h in hijos if h["i"] < v["i"] and h["funcion"] in ("amod", "nmod", "obl", "appos") and any(q["cat"] == "DET" for q in self._rama(ps, h["i"])) and not self._hijos(ps, h["i"], ("case",))), None) is not None:
                h0 = next(h for h in hijos if h["i"] < v["i"] and h["funcion"] in ("amod", "nmod", "obl", "appos") and any(q["cat"] == "DET" for q in self._rama(ps, h["i"])) and not self._hijos(ps, h["i"], ("case",)))
                S = self._sn(ps, h0)                     # «Los dos más grandes, Júpiter y Saturno, están…»: va delante, con artículo y sin preposición
            elif v["funcion"] == "acl" and v["cabeza"] in por_i and por_i[v["cabeza"]]["cat"] in ("NOUN", "PROPN"):
                S = self._sn(ps, por_i[v["cabeza"]])     # «un planeta formado por…»
            elif v["funcion"] in ("conj", "xcomp", "advcl") and v["cabeza"] in hechas:
                S = hechas[v["cabeza"]].get("S")         # hereda el de la oración de la que cuelga
            heredado = False
            if S is None and v["funcion"] == "root" and v["cat"] in ("VERB", "AUX", "ADJ", "NOUN"):
                per = _persona(next((h["forma"] for h in hijos if h["funcion"] in ("aux", "cop")), v["forma"]))
                if per == "1":
                    S = {"txt": "yo", "h": "yo", "hs": ["yo"], "lemas": {"yo"}, "prep": "", "cat": "PRON"}
                elif per == "3" and self.ultimo_sujeto is not None and not (any(sa(h["forma"]) == "se" for h in hijos) and not any(sa(h["forma"]) in ("lo", "la", "los", "las") for h in hijos)):
                    S = self.ultimo_sujeto; heredado = True          # «Tienen dos hijos…»: se sigue hablando de los mismos
            r = {"S": S, "src": f, "ctx": ctx, "seg": v["seguro"] * (0.8 if heredado else 1.0), "neg": any(sa(h["forma"]) in ("no", "nunca", "jamas") for h in hijos if h["funcion"] == "advmod"), "C": [], "O": None, "A": None}
            if cop is not None and v["cat"] in ("NOUN", "PROPN", "PRON", "NUM") or (cop is not None and v["cat"] == "ADJ" and _lema(cop["forma"]) == "ser" and not self._hijos(ps, v["i"], ("obl",))):
                r["v"] = "ser"
                r["A"] = self._sn(ps, v, fuera=("nsubj", "csubj", "cop", "advmod", "obl", "mark", "cc", "aux", "punct", "expl", "iobj"))
                rel_at = [h for h in hijos if h["funcion"] == "acl"]
                if rel_at:                               # «objetos helados pequeños conformados por hielo»: la relativa va con el atributo
                    r["A"] = dict(r["A"]); r["A"]["txt"] = self._txt([p for p in ps if p["i"] >= v["i"] and p["i"] <= max(q["i"] for q in self._rama(ps, rel_at[-1]["i"], quita_caso=False)) and p["cat"] != "PUNCT" or (p["cabeza"] == v["i"] and p["funcion"] in ("det", "amod") and p["i"] < v["i"])])
                    r["A"]["lemas"] = r["A"]["lemas"] | {_lema(q["forma"]) for q in self._rama(ps, rel_at[-1]["i"])}
                rel = [h for h in hijos if h["funcion"] == "acl"]
            else:
                r["v"] = _lema(v["forma"])
            ob = next((h for h in hijos if h["funcion"] == "obj"), None)
            if ob is not None:
                r["O"] = self._sn(ps, ob)
            for h in hijos:
                if h["funcion"] in ("obl", "nmod", "iobj") or (h["funcion"] == "advcl" and sa(h["forma"]) == "hace"):
                    c = self._sn(ps, h)
                    if h["funcion"] == "advcl":          # «hace unos 4600 millones de años»
                        c = dict(c); c["txt"] = self._txt([p for p in self._rama(ps, h["i"], quita_caso=False)]); c["prep"] = "hace"
                        c["lemas"] = {_lema(p["forma"]) for p in self._rama(ps, h["i"])}
                    c["tiempo"] = c["prep"] == "hace" or any(l in _TIEMPO for l in c["lemas"]) or bool(re.search(r"\b1\d{3}\b|\b20\d{2}\b", c["txt"]))
                    r["C"].append(c)
                elif h["funcion"] == "advcl" and any(sa(q["forma"]) in ("porque", "pues") or (sa(q["forma"]) == "que" and any(sa(z["forma"]) == "ya" for z in self._hijos(ps, h["i"]))) for q in self._hijos(ps, h["i"], ("mark",))):
                    c = self._sn(ps, h); c = dict(c); c["prep"] = "porque"; c["tiempo"] = False
                    r["C"].append(c)
                elif h["funcion"] in ("ccomp", "xcomp", "csubj") and r["O"] is None:
                    r["O"] = dict(self._sn(ps, h))       # «descubre QUE alrededor de Júpiter rotan satélites»: la oración entera
                    ids_ = {x_["i"] for x_ in hijos if x_["funcion"] in ("ccomp", "xcomp", "csubj")}   # si hay varias piezas de oración, van juntas
                    cambio_ = True
                    while cambio_:
                        cambio_ = False
                        for q_ in ps:
                            if q_["cabeza"] in ids_ and q_["i"] not in ids_:
                                ids_.add(q_["i"]); cambio_ = True
                    todo_ = [q_ for q_ in ps if q_["i"] in ids_ and q_["cat"] != "PUNCT" and not (q_["funcion"] == "mark" and q_["i"] == min(ids_))]
                    r["O"]["txt"] = self._txt(todo_)
                    r["O"]["lemas"] = {_lema(q_["forma"]) for q_ in todo_ if sa(q_["forma"]) not in _VACIAS}
            if v["funcion"] == "root":                   # «hace unos 4600 millones de años»: expresión de tiempo hecha; se toma entera
                mt = re.search(r"\bhace\s+(?:(?:unos|unas|casi|aproximadamente|más de|menos de)\s+)?[\wáéíóúñ.,\s]{1,28}?\b(?:años|siglos|días|meses|semanas|horas|minutos)\b", f, re.I)
                if mt:
                    lt = {_lema(x) for x in re.findall(r"[\wáéíóúñ]+", mt.group(0))}
                    r["C"] = [c for c in r["C"] if not (c["lemas"] <= lt or c["prep"] == "hace")]
                    if r["O"] is not None and r["O"]["h"] in lt:
                        r["O"] = None
                    r["C"].append({"txt": mt.group(0), "h": "hace", "hs": ["hace"], "lemas": lt, "prep": "hace", "cat": "NOUN", "tiempo": True})
            hechas[v["i"]] = r
            if v["funcion"] == "root" and suj is not None and S is not None and S["cat"] in ("NOUN", "PROPN"):
                self.ultimo_sujeto = S
            for x_ in [r["S"], r["O"]] + r["C"]:            # un pronombre ya resuelto también puede ser antecedente («se LO entrega… el macho LO protege»)
                if x_ is not None and x_.get("alts"):
                    pron_ = next((p for p in ps if p["cat"] == "PRON" and sa(p["forma"]) in _PRON and _PRON[sa(p["forma"])][2] != "dat"), None)
                    if pron_ is not None:
                        g_, n_, t_ = _PRON[sa(pron_["forma"])]
                        self._cur.append((dict(x_, alts=None), g_, n_, "obj" if t_ == "obj" else "nsubj", self.frases, False, pron_["i"]))
            if v["funcion"] == "acl" and v["seguro"] < 0.70:
                continue                                 # no está claro de quién se dice: no se guarda
            if r["S"] is not None or r["O"] is not None or r["A"] is not None or r["C"]:
                self.R.append(r)

    # ------------------------------------------------------------------ preguntar
    def _casa_sn(self, sn, lemas, cabeza=None):
        """¿Habla este sintagma de lo que se pregunta? Todas las palabras de la pregunta deben estar en él (o ser uno de sus miembros).
        Si es un pronombre, cada antecedente posible cuenta con su probabilidad."""
        if sn is None or not lemas:
            return 0.0
        if sn.get("alts"):
            return max((p_ * self._casa_sn(dict(a_, alts=None), lemas, cabeza) for p_, a_ in sn["alts"] if p_ >= 0.1), default=0.0)
        if cabeza and cabeza not in sn["hs"] and cabeza not in sn["lemas"]:
            return 0.0
        dentro = sum(1 for l in lemas if l in sn["lemas"])
        if dentro < len(lemas):
            return 0.0
        return 1.0 + (0.5 if cabeza in sn["hs"] else 0.0) - 0.02 * max(0, len(sn["lemas"]) - len(lemas))

    def pregunta(self, q):
        """Devuelve {"respuesta", "fuente", "seguro"} o None si no hay nada que encaje (y entonces el LCM debe decir que no lo sabe).
        La pregunta se analiza con el mismo analizador. Da unas piezas (nombres) y un verbo; se busca una relación con ese verbo en la que
        encajen todas las piezas, y se contesta con la pieza que falta, del tipo que pide la palabra interrogativa."""
        q = q.strip()
        q = re.sub(r"^(¿?\s*)(que|quien|quienes|cual|cuales|donde|cuando|cuanto|cuantos|cuanta|cuantas|como)\b",
                   lambda m: m.group(1) + {"que": "qué", "quien": "quién", "quienes": "quiénes", "cual": "cuál", "cuales": "cuáles", "donde": "dónde", "cuando": "cuándo", "cuanto": "cuánto",
                                           "cuantos": "cuántos", "cuanta": "cuánta", "cuantas": "cuántas", "como": "cómo"}[m.group(2).lower()], q, flags=re.I)
        q = re.sub(r"^((?:de|por|con|en|a|para)\s+)que\b", r"\1qué", q, flags=re.I)
        if not q.startswith("¿"):
            q = "¿" + q
        if not q.endswith("?"):
            q += "?"
        ps = palabras(q)
        por_i = {p["i"]: p for p in ps}
        wh = next((p for p in ps if sa(p["forma"]) in ("que", "quien", "quienes", "cual", "cuales", "donde", "cuando", "cuanto", "cuantos", "cuanta", "cuantas", "como")), None)
        if wh is None:
            return None
        w = sa(wh["forma"])
        prep_wh = sa(por_i[wh["i"] - 1]["forma"]) if wh["i"] > 1 and por_i[wh["i"] - 1]["cat"] == "ADP" else ""
        causa = prep_wh == "por" and w == "que"
        if causa:
            prep_wh = "porque"
        nombre_wh = por_i.get(wh["i"] + 1) if wh["i"] + 1 in por_i and por_i[wh["i"] + 1]["cat"] == "NOUN" and (w.startswith("cuant") or w == "que") else None
        verbos = [p for p in ps if p["cat"] in ("VERB", "AUX") or (p["cat"] == "ADJ" and self._hijos(ps, p["i"], ("cop",)))]
        cop = [p for p in ps if p["funcion"] == "cop" or (p["cat"] == "AUX" and _lema(p["forma"]) in ("ser", "estar"))]
        lleno = [p for p in verbos if p not in cop and _lema(p["forma"]) not in ("ser", "estar", "haber")]
        vl = _lema(lleno[0]["forma"]) if lleno else ("ser" if cop else (_lema(verbos[0]["forma"]) if verbos else "ser"))
        # las piezas que da la pregunta: cada nombre que no cuelga de otro nombre, con todo su sintagma
        dados = []
        for h in ps:
            if h is wh or h is nombre_wh or h["cat"] not in ("NOUN", "PROPN"):
                continue
            pad = por_i.get(h["cabeza"])
            if pad is not None and pad["cat"] in ("NOUN", "PROPN") and pad is not nombre_wh and h["funcion"] in ("nmod", "flat", "conj", "appos", "amod", "compound"):
                continue
            dados.append(self._sn(ps, h))
        ctx_q = {_lema(p["forma"]) for p in ps if p["cat"] in ("NOUN", "PROPN", "VERB", "ADJ", "NUM")}
        # ---- cantidad: «¿cuántos planetas tiene X?», «¿cuánto tarda…?»
        if w.startswith("cuant"):
            n = nombre_wh
            cand = []
            for r in self.R:                             # primero, en la relación que encaja con la pregunta: la pieza que lleva un número
                sv = sim_concepto(r["v"], vl)
                if sv <= 0 or r["neg"]:
                    continue
                args = [x for x in [r["S"], r["O"], r["A"]] + r["C"] if x is not None]
                nucleo_ = [x for x in (r["S"], r["O"], r["A"]) if x is not None]
                if dados and not all(any(self._casa_sn(x, sn["lemas"], sn["h"]) > 0 for x in nucleo_) for sn in dados):
                    continue                             # lo que da la pregunta tiene que ser el sujeto o el objeto, no un complemento («…en la Luna»)
                for x in args:
                    con_num = bool(re.search(r"\d", x["txt"])) or bool(x["lemas"] & _NUMS)
                    if not con_num or any(x["lemas"] <= sn["lemas"] for sn in dados):
                        continue
                    if n is not None and _lema(n["forma"]) != x["h"]:
                        continue                         # «¿cuántas abejas?» no se contesta con «tres TIPOS de abejas»
                    if n is None and re.search(r"\bveces\b", x["txt"]):
                        continue                         # «seis veces menos» compara, no mide
                    cand.append((sv * r["seg"] + 0.1 * len(ctx_q & r["ctx"]), x, r))
            if cand:
                cand.sort(key=lambda z: -z[0])
                pt, x, r = cand[0]
                txt = ((x["prep"] + " ") if x.get("prep") and x["prep"] not in ("hace",) and prep_wh else "") + x["txt"]
                return {"respuesta": txt[:1].upper() + txt[1:] + ".", "fuente": r["src"], "seguro": round(min(1.0, float(pt)), 2)}
            if n is None:
                return None
            ln = _lema(n["forma"])
            extra = {_lema(p["forma"]) for p in self._rama(ps, n["i"]) if p["cat"] in ("ADJ", "NOUN") and p is not n}
            otros = set().union(*[sn["lemas"] for sn in dados]) if dados else set()
            votos = {}
            for num, lema, sn, src in self.N:
                if lema != ln or not extra <= sn["lemas"]:
                    continue
                if not extra and (sn["lemas"] - {ln, _lema(num)}) & {"enano", "menor", "terrestre", "exterior", "interior", "gigante", "cercano", "alejado", "grande"}:
                    continue                             # «cuatro planetas enanos» no contesta a «¿cuántos planetas?»
                peso = 1.0 + sum(1.0 for o in otros if o in {_lema(x) for x in re.findall(r"[a-záéíóúñ]+", src.lower())})
                d = votos.setdefault(num, [0.0, sn["txt"], src]); d[0] += peso
            if not votos:
                return None
            num, (pt, txt, src) = max(votos.items(), key=lambda x: x[1][0])
            return {"respuesta": txt[:1].upper() + txt[1:] + ".", "fuente": src, "seguro": round(min(1.0, pt / 3.0), 2)}
        if not dados:
            return None
        if w == "como" and not vl.startswith("llam"):
            return None                                  # el modo («¿cómo…?») no es una pieza de la relación: no se contesta desde aquí
        mejores = []
        for r in self.R:
            sv = sim_concepto(r["v"], vl)                # el mismo verbo, o uno que significa algo parecido según los vectores del LCM
            if r["neg"] or sv <= 0:
                continue
            huecos = {"S": r["S"], "O": r["O"], "A": r["A"]}
            usados, pt, ok = set(), float(r["seg"]) * sv + 0.1 * len((ctx_q & r["ctx"])), True
            for sn in dados:
                mejor = (0.0, None)
                for k, x in list(huecos.items()) + [("C%d" % i, c) for i, c in enumerate(r["C"])]:
                    c_ = self._casa_sn(x, sn["lemas"], sn["h"])
                    if k.startswith("C"):
                        c_ *= 0.8                        # lo que se pregunta suele ser el sujeto o el objeto, no un complemento
                    if c_ > mejor[0] and k not in usados:
                        mejor = (c_, k)
                if mejor[1] is None:
                    ok = False
                    break
                usados.add(mejor[1]); pt += mejor[0]
            if not ok:
                continue
            comps = [(("C%d" % i), c) for i, c in enumerate(r["C"]) if ("C%d" % i) not in usados]
            resp = None
            if w == "cuando":
                resp = next((c for _, c in comps if c.get("tiempo")), None)
            elif w == "donde":
                resp = next((c for _, c in comps if not c.get("tiempo") and c["prep"].split(" ")[0] in ("en", "entre", "sobre", "dentro", "a", "hasta", "desde", "alrededor", "cerca", "tras", "bajo")), None)
            elif causa:
                resp = next((c for _, c in comps if c["prep"] == "porque"), None)
            elif w == "como" and r["v"].startswith("llam"):
                resp = r["O"] if "O" not in usados and r["O"] is not None else next((c for _, c in comps), None)
            elif prep_wh:
                resp = next((c for _, c in comps if not c.get("tiempo") and c["prep"].split(" ")[-1:] == [prep_wh]), None) \
                    or (next((c for _, c in comps if not c.get("tiempo") and c["prep"] in ("de", "por", "con")), None) if prep_wh in ("de", "por", "con") else None)
            elif w.startswith("quien"):
                resp = r["S"] if "S" not in usados else (r["O"] if "O" not in usados else None)
            elif r["v"] in ("ser", "estar") and vl in ("ser", "estar"):
                resp = r["A"] if "A" not in usados else (r["S"] if "S" not in usados else None)
            else:
                orden_ = ["O", "S"] if "S" in usados else ["S", "O"]
                resp = next((huecos[k] for k in orden_ if k not in usados and huecos[k] is not None), None) or next((c for _, c in comps if not c.get("tiempo")), None)
                if resp is r["S"] and resp is not None and resp.get("cat") == "PROPN" and w == "que" and nombre_wh is None:
                    resp = None                          # «¿qué…?» no se contesta con el nombre propio del sujeto (para eso se pregunta «¿quién?»)
            if resp is None or not resp.get("txt") or sa(resp["txt"]) in ("que", "lo", "la", "se", "le", "yo"):
                continue
            if resp["lemas"] <= (ctx_q | {_lema(p["forma"]) for p in ps}):
                continue                                 # todo lo que diría ya está en la pregunta
            if any(resp["lemas"] <= sn["lemas"] or sn["lemas"] <= resp["lemas"] for sn in dados):
                continue                                 # contestar con lo mismo que se pregunta no es contestar
            if nombre_wh is not None and _lema(nombre_wh["forma"]) not in resp["lemas"] and not r["v"] == "ser":
                pt -= 0.3                                # «¿qué planetas…?»: mejor si la respuesta habla de planetas
            mejores.append((pt, r, resp))
        if not mejores:
            return None
        mejores.sort(key=lambda x: -x[0])
        pt, r, resp = mejores[0]
        # probabilidad de la mejor frente a las que dicen OTRA cosa (las que dicen lo mismo la refuerzan)
        igual = sum(x[0] for x in mejores if x[2]["lemas"] == resp["lemas"] or x[2]["h"] == resp["h"])
        total = sum(x[0] for x in mejores[:6])
        prob = igual / total if total > 0 else 0.0
        pre = (resp.get("prep") + " ") if resp.get("prep") and resp.get("prep") not in ("hace", "porque") and (w in ("cuando", "donde") or prep_wh) else ""
        if causa:
            pre = "Porque "
        txt = (pre + resp["txt"]).strip()
        txt = re.sub(r"\b([Aa]) el\b", lambda m: m.group(1) + "l", re.sub(r"\b([Dd]e) el\b", lambda m: m.group(1) + "l", txt))
        return {"respuesta": txt[:1].upper() + txt[1:] + ".", "fuente": r["src"], "seguro": round(float(min(1.0, r["seg"]) * prob), 2), "prob": round(prob, 2), "verbo": vl,
                "otras": [x[2]["txt"] for x in mejores[1:3] if x[2]["lemas"] != resp["lemas"]]}

    def grafo(self):
        """El GRAFO DE CONCEPTOS que sale de lo leído: nodos = conceptos; aristas = (concepto, dimensión, concepto) donde la dimensión es
        el verbo y el papel o la preposición («componer·de», «ser», «descubrir·objeto», «vivir·en»). Cada arista lleva su peso (la seguridad
        del análisis, sumada si se repite) y el contexto en que se dijo, para elegir entre varias por probabilidad según de qué se hable."""
        A = {}
        for r in self.R:
            if r["S"] is None or r["neg"]:
                continue
            for o in r["S"]["hs"]:
                destinos = []
                if r["A"] is not None:
                    destinos.append(("ser", r["A"]))
                if r["O"] is not None:
                    destinos.append((r["v"] + "·objeto", r["O"]))
                for c in r["C"]:
                    destinos.append((r["v"] + "·" + (c["prep"] or "con"), c))
                for dim, x in destinos:
                    for d in x["hs"]:
                        a = A.setdefault((o, dim, d), {"peso": 0.0, "veces": 0, "ctx": set()})
                        a["peso"] += float(r["seg"]); a["veces"] += 1; a["ctx"] |= r["ctx"]
        return A

    def vecinos(self, concepto, ctx=()):
        """Con qué se relaciona un concepto y con qué probabilidad, dado un contexto (palabras de las que se está hablando)."""
        c = _lema(concepto)
        ctx = {_lema(x) for x in ctx}
        out = []
        for (o, dim, d), a in self.grafo().items():
            if o == c or d == c:
                out.append([a["peso"] * (1.0 + 0.5 * len(ctx & a["ctx"])), o, dim, d])
        tot = sum(x[0] for x in out) or 1.0
        return sorted(((round(x[0] / tot, 3), x[1], x[2], x[3]) for x in out), reverse=True)

    def sobre(self, tema, k=4):
        """«¿Qué me puedes decir de X?»: las relaciones en las que X es el sujeto."""
        lem = {_lema(w) for w in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", tema) if sa(w) not in _VACIAS}
        out, vistos = [], set()
        for r in self.R:
            s = r["S"]
            if s is None or not lem or not lem <= (s["lemas"] | set(s["hs"])) or r["src"] in vistos:
                continue
            if len(s["lemas"]) > len(lem) + 3:
                continue
            vistos.add(r["src"]); out.append(r["src"])
            if len(out) >= k:
                break
        if not out:                                      # no es sujeto de nada: las frases donde aparece con otro papel
            nucleo = {l for l in lem if l not in ("planeta", "estrella", "satelite", "cosa")} or lem
            for r in self.R:
                for x in [r["O"], r["A"]] + r["C"] + [r["S"]]:
                    if x is not None and nucleo <= (x["lemas"] | set(x["hs"])) and r["src"] not in vistos and len(r["src"]) < 260:
                        vistos.add(r["src"]); out.append(r["src"])
                        break
                if len(out) >= 2:
                    break
        return out
