"""Lector de textos guiado por la ESCUELA (parche-115).

Idea: la comprension no depende del tema. Cada frase se analiza con el parser de dependencias de la escuela (entrenado con corpus generales)
y las relaciones salen de FUNCIONES GRAMATICALES, nunca de palabras de un campo:

    sujeto + verbo (+ objeto / complemento con preposicion)          ->  (S, VERBO[_PREP], O)
    cópula + nombre / adjetivo / complemento                         ->  (S, ES, clase), (S, SER, cualidad), (S, ES_PREP, X)
    pasiva con agente                                                 ->  (agente, VERBO, paciente)
    aposicion, relativas, participios, coordinacion, posesivo «su X», anafora y sujeto omitido (tema del discurso)
    cantidades («25 cantones», «180 kg»), fechas (obl con año), negacion

Conceptos: nucleo + nombre propio compuesto + complementos con «de» (X_DE_Y) + adjetivos que lo subclasifican (LEON_ASIATICO ES LEON).
Precision: se omiten oraciones hipoteticas/concesivas (si, aunque...), citas y creencias (ccomp), epistemicos (quizá, supuestamente...), comparativos.
No hay listas de palabras de ningun campo; solo clases cerradas de la gramatica (preposiciones, negacion, subordinantes).
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Set, Tuple

from .lector import Lector, _h, clave, frases, limpiar, nrm

Row = Tuple[str, str, int, str, str]       # forma, upos, cabeza (1-based, 0 = raiz), deprel, lema

# ---- clases cerradas de la gramatica (no son vocabulario de un campo) ----
NEGACION = {"no", "nunca", "jamás", "jamas", "tampoco", "ni"}
SUBORD_HIPOTETICA = {"si", "aunque", "aun", "pese", "salvo", "excepto", "mientras", "cuanto", "siempre", "a menos", "como", "tal", "supuesto"}
EPISTEMICOS = {"quizá", "quizás", "quiza", "quizas", "probablemente", "posiblemente", "supuestamente", "aparentemente", "presuntamente", "seguramente", "acaso", "tal vez", "teóricamente"}
COMPARATIVO = {"más", "mas", "menos", "tan", "tanto", "mejor", "peor"}
CONDICIONALES = {"si", "salvo", "excepto", "siempre", "cuanto"}
COPULAS = {"ser", "estar", "parecer", "resultar", "quedar", "permanecer"}
ATRIBUTIVOS = {"considerar", "llamar", "denominar", "nombrar", "declarar", "conocer", "calificar", "proclamar", "designar", "elegir"}   # «se considera X», «es conocido como X»
LOCATIVOS = {"encontrar", "situar", "ubicar", "hallar", "localizar", "emplazar", "asentar"}
DEMOSTRATIVOS = {"este", "esta", "estos", "estas", "ese", "esa", "esos", "esas", "aquel", "aquella", "dicho", "dicha"}
POSESIVOS = {"su", "sus"}
PRON_ANAF = {"él", "el", "ella", "ellos", "ellas", "esto", "eso", "ello", "lo", "se"}
PRON_REL = {"que", "quien", "quienes", "cual", "cuales", "donde", "cuyo", "cuya", "cuyos", "cuyas"}
NUM_PAL = {"un", "uno", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "veinte", "treinta", "cuarenta", "cincuenta", "cien", "mil", "millón", "millones"}


class Arbol:
    def __init__(self, rows: List[Row]):
        self.r = rows
        self.n = len(rows)
        self.h = [x[2] - 1 for x in rows]
        self._sanear()
        self.k: List[List[int]] = [[] for _ in rows]
        for i, h in enumerate(self.h):
            if 0 <= h < self.n:
                self.k[h].append(i)

    def _sanear(self):
        """La escuela predice cada cabeza por separado: puede dar ciclos (una palabra colgando de sí misma o dos de la otra).
        Un ciclo haría que los recorridos no acaben nunca: se corta soltando una palabra del ciclo (queda como raíz suelta)."""
        n = self.n
        for i in range(n):
            if not (0 <= self.h[i] < n) or self.h[i] == i:
                self.h[i] = -1 if self.h[i] == i or not (0 <= self.h[i] < n) else self.h[i]
        for i in range(n):
            ruta, x = [], i
            while 0 <= x < n and x not in ruta:
                ruta.append(x)
                x = self.h[x]
            if 0 <= x < n:                                    # volvió a un nodo de la ruta: ciclo
                self.h[ruta[-1]] = -1

    def f(self, i):
        return self.r[i][0]

    def u(self, i):
        return self.r[i][1]

    def d(self, i):
        return self.r[i][3]

    def l(self, i):
        lm = (self.r[i][4] or "").strip()
        return (lm if lm and lm != "_" else self.r[i][0]).lower()

    def hijos(self, i, *rels) -> List[int]:
        return [j for j in self.k[i] if self.r[j][3] in rels]

    def sub(self, i) -> List[int]:
        out, st, vistos = [], [i], {i}
        while st:
            x = st.pop()
            out.append(x)
            for y in self.k[x]:
                if y not in vistos:
                    vistos.add(y)
                    st.append(y)
        return sorted(out)


class C:
    """Un concepto: clave, texto, y los hechos de clasificacion que lo acompañan."""
    __slots__ = ("key", "disp", "propio", "idx", "extra", "base")

    def __init__(self, key, disp, propio=False, idx=-1, base=None):
        self.key, self.disp, self.propio, self.idx, self.base = key, disp, propio, idx, base
        self.extra: List[dict] = []


def _participio_masc(form: str) -> str:
    f = form.lower()
    return re.sub(r"([ai])d([ao])s?$", lambda m: m.group(1) + "d" + "o", f)


def _tpl_verbo(form: str, lema: str) -> str:
    f = form.lower()
    if f.endswith(("an", "en")) and len(f) > 3 and f != lema:
        return f[:-1]
    return f


def _sub(c: "C", key: str, disp: str, propio=None) -> "C":
    """Concepto mas especifico que c (c ES base): conserva los hechos acompañantes."""
    n = C(key, disp, c.propio if propio is None else propio, c.idx, base=c.base)
    n.extra = list(c.extra)
    return n


class ExtractorUD:
    def __init__(self):
        self.principal: Optional[C] = None          # sujeto de la oracion principal anterior (sujeto omitido, «él», «Su X»)
        self.clases: Dict[str, Set[str]] = {}       # clave -> claves de sus clases (para «este animal» = el tema)
        self.motivo = ""

    # ---------- conceptos ----------
    def _nombre(self, A: Arbol, i: int) -> Tuple[List[int], bool]:
        partes = [i] + [j for j in A.hijos(i, "flat", "compound") if A.u(j) in ("PROPN", "NOUN", "X", "NUM", "ADJ")]
        propio = A.u(i) == "PROPN" or any(A.u(j) == "PROPN" for j in partes)
        return sorted(partes), propio

    def concepto(self, A: Arbol, i: int, califica=True, prof=0) -> Optional[C]:
        u = A.u(i)
        if u == "PRON":
            return self.pronombre(A, i)
        if u not in ("NOUN", "PROPN", "X"):
            return None
        partes, propio = self._nombre(A, i)
        if propio:
            texto = " ".join(A.f(j) for j in partes)
        else:
            texto = " ".join((A.l(j) if j == i else A.f(j).lower()) for j in partes)
        if not re.search(r"[a-záéíóúüñ]", texto.lower()):
            return None
        base = C(clave(texto), texto, propio, i)
        c = C(base.key, texto, propio, i, base=base)
        # demostrativo -> tema (si es de su clase): «este fenómeno», «este animal»
        dets = [A.l(j) for j in A.hijos(i, "det")]
        if self.principal and any(x in DEMOSTRATIVOS for x in dets) and not propio and base.key in self.clases.get(self.principal.key, set()):
            return self.principal
        # posesivo: «su cola» = cola_DE_tema
        if self.principal and any(x in POSESIVOS for x in dets) and not propio:
            k = base.key + "_DE_" + self.principal.key
            c = _sub(c, k, texto + " de " + self.principal.disp, False)
            c.extra.append(_ud(k, "ES", base.key, c.disp, texto))
        # cantidad: «25 cantones», «cinco especies»
        for j in A.hijos(i, "nummod"):
            if A.u(j) == "NUM" and A.l(j) not in ("un", "uno", "una"):
                num = clave(A.f(j))
                if num:
                    k2 = num + "_" + c.key
                    c.extra.append(_ud(k2, "ES", c.key, A.f(j) + " " + c.disp, c.disp))
                    c = _sub(c, k2, A.f(j) + " " + c.disp)
                break
        # adjetivos que subclasifican: «león asiático» ES «león»
        if califica and not propio and prof == 0:
            adjs = [j for j in A.hijos(i, "amod") if A.u(j) == "ADJ" and j > i and not self._grado(A, j)][:2]
            if adjs:
                k3 = c.key + "".join("_" + clave(A.l(j)) for j in adjs)
                c.extra.append(_ud(k3, "ES", c.key, c.disp + " " + " ".join(A.l(j) for j in adjs), c.disp))
                c = _sub(c, k3, c.disp + " " + " ".join(A.l(j) for j in adjs), False)
        # complemento con «de»: «cola de castor», «Museo del Prado»
        if prof < 1:
            for j in A.hijos(i, "nmod"):
                if self._prep(A, j) == "de" and A.u(j) in ("NOUN", "PROPN", "X"):
                    s = self.concepto(A, j, califica=False, prof=prof + 1)
                    if s is not None and s is not self.principal:
                        det = ""
                        if propio and s.propio:
                            det = {"el": "del", "la": "de la", "los": "de los", "las": "de las"}.get(next((A.l(x) for x in A.hijos(j, "det")), ""), "de")
                        k4 = c.key + "_" + clave(det or "de") + "_" + s.key
                        d4 = c.disp + " " + (det or "de") + " " + s.disp
                        c.extra.append(_ud(k4, "ES", c.key, d4, c.disp))
                        c.extra += s.extra
                        c = _sub(c, k4, d4, propio)
                    break
        # aposicion: «el capitan John Hunter», «Gatis, ciclista»
        for j in A.hijos(i, "appos"):
            a = self.concepto(A, j, califica=False, prof=prof + 1)
            if a is None:
                continue
            if A.u(j) == "NOUN" and (propio or A.u(i) == "NOUN"):
                c.extra.append(_ud(c.key, "ES", a.key, c.disp, a.disp))
            elif A.u(j) == "PROPN" and A.u(i) == "NOUN" and not propio:
                a.extra.append(_ud(a.key, "ES", c.key, a.disp, c.disp))          # «su padre, Domingo Álvarez»: la entidad es el nombre propio
                a.extra += c.extra
                return a
        return c

    def pronombre(self, A: Arbol, i: int) -> Optional[C]:
        l = A.l(i)
        if l in PRON_ANAF:
            return self.principal
        return None

    @staticmethod
    def _grado(A: Arbol, j: int) -> bool:
        return any(A.l(x) in COMPARATIVO for x in A.hijos(j, "advmod"))

    @staticmethod
    def _prep(A: Arbol, j: int) -> str:
        cs = A.hijos(j, "case")
        return A.l(cs[0]) if cs else ""

    def expandir(self, A: Arbol, i: int) -> List[int]:
        """cabeza + sus coordinados nominales"""
        out, st = [i], [i]
        while st:
            x = st.pop()
            for j in A.hijos(x, "conj"):
                if A.u(j) in ("NOUN", "PROPN", "X", "ADJ") and j not in out:
                    out.append(j)
                    st.append(j)
        return sorted(out)

    # ---------- fechas ----------
    @staticmethod
    def _año(A: Arbol, i: int) -> str:
        for j in A.sub(i):
            m = re.fullmatch(r"(1\d{3}|20\d{2})", A.f(j))
            if m:
                return m.group(1)
        return ""

    # ---------- sujeto ----------
    def sujeto(self, A: Arbol, p: int, memo: Dict[int, Optional[List[C]]], visit=None) -> Optional[List[C]]:
        """Sujetos del predicado p. None = hay sujeto pero no se puede resolver; [] = no hay sujeto propio y no hay de quien heredarlo."""
        if p in memo:
            return memo[p]
        memo[p] = None
        ns = A.hijos(p, "nsubj", "csubj")
        res: Optional[List[C]]
        if ns:
            cs: List[C] = []
            for n_ in ns:
                if A.d(n_) == "csubj" or A.u(n_) == "VERB":
                    continue
                if A.u(n_) == "PRON" and A.l(n_) in PRON_REL:
                    ant = self.antecedente(A, p)
                    if ant:
                        cs += ant
                    continue
                for e in self.expandir(A, n_):
                    c = self.concepto(A, e)
                    if c is not None:
                        cs.append(c)
            res = cs or None
        else:
            res = self._heredado(A, p, memo)
        memo[p] = res
        return res

    def _heredado(self, A: Arbol, p: int, memo) -> Optional[List[C]]:
        d, h = A.d(p), A.h[p]
        if h >= 0 and d in ("conj", "xcomp", "advcl", "parataxis") and (A.u(h) in ("VERB", "AUX") or A.hijos(h, "cop")):
            s = self.sujeto(A, h, memo)
            if s and d in ("conj", "xcomp", "advcl"):
                return s
        if d == "acl":
            return self.antecedente(A, p)
        if A.hijos(p, "expl") and not A.hijos(p, "nsubj"):
            return None                                       # «se observan leones»: impersonal / pasiva refleja
        if self.principal is not None:
            return [self.principal]
        return None

    def antecedente(self, A: Arbol, p: int) -> Optional[List[C]]:
        """Relativa/participio: el nombre al que modifica (si es un predicado nominal, el sujeto de la copula)."""
        h = A.h[p]
        if h < 0:
            return None
        if A.hijos(h, "cop") and A.u(h) in ("NOUN", "PROPN"):
            ns = A.hijos(h, "nsubj")
            if ns:
                c = self.concepto(A, ns[0])
                return [c] if c is not None else None
        c = self.concepto(A, h, califica=False)
        return [c] if c is not None else None

    # ---------- una oracion ----------
    def oracion(self, rows: List[Row], inicio=False) -> List[dict]:
        if not rows:
            return []
        A = Arbol(rows)
        self.motivo = ""
        memo: Dict[int, Optional[List[C]]] = {}
        out: List[dict] = []
        omitir: Set[int] = set()
        raiz = next((i for i in range(A.n) if A.h[i] < 0), 0)
        # predicados: verbos y predicados nominales/adjetivales con cópula
        preds = [i for i in range(A.n) if (A.u(i) in ("VERB", "AUX") and A.d(i) not in ("aux", "cop")) or A.hijos(i, "cop")]
        for p in preds:
            if self._hipotetico(A, p):
                omitir.add(p)
                omitir.update(j for j in A.sub(p) if j in preds)
                h_ = A.h[p]
                if A.d(p) == "advcl" and h_ >= 0 and any(A.l(m) in CONDICIONALES for m in A.hijos(p, "mark")):
                    omitir.add(h_)                                 # «si X, Y»: Y depende de X
        principal_nuevo = None
        for p in preds:
            if p in omitir:
                continue
            antes = len(out)
            try:
                sujs = self.sujeto(A, p, memo)
                if not sujs:
                    self.motivo = self.motivo or "no he podido determinar el sujeto"
                    continue
                neg = any(A.l(x) in NEGACION for x in A.hijos(p, "advmod")) or any(A.l(x) in NEGACION for x in A.hijos(p, "cc")) and False
                if A.hijos(p, "cop"):
                    out += self._copula(A, p, sujs, neg)
                else:
                    out += self._verbal(A, p, sujs, neg)
            except Exception:                                    # noqa
                continue
            if principal_nuevo is None and p == raiz and A.hijos(p, "nsubj") and len(out) > antes and not (self.principal is not None and sujs[0].key.endswith("_DE_" + self.principal.key)):
                principal_nuevo = sujs[0]
        if principal_nuevo is not None:
            self.principal = principal_nuevo
        elif self.principal is None and out:
            self.principal = _desde_hecho(out[0])
        for h in out:
            if h["p"] == "ES" and self.principal is not None and h["s"] == self.principal.key:
                self.clases.setdefault(h["s"], set()).add(h["o"])
        return _limpiar(out)

    def _hipotetico(self, A: Arbol, p: int) -> bool:
        """Oraciones que no afirman: condicionales, concesivas, creencias (ccomp), epistémicos."""
        if A.d(p) in ("ccomp", "csubj", "parataxis"):
            return True
        for m in A.hijos(p, "mark"):
            if A.l(m) == "que" and not any(A.d(x) == "fixed" for x in A.k[m]) and A.h[p] >= 0 and A.d(p) != "conj" and (A.u(A.h[p]) in ("VERB", "AUX") or A.hijos(A.h[p], "cop")):
                return True                                       # «dijo que…», «se demostró que…»: contenido citado o creído, no afirmado
        for j in A.hijos(p, "mark", "advmod", "cc", "case"):
            l = A.l(j)
            if A.d(j) == "mark" and (l in SUBORD_HIPOTETICA or (l == "que" and any(A.l(x) in ("aun", "pese", "a pesar") for x in A.hijos(p, "mark", "advmod", "case")))):
                return True
            if A.d(j) == "advmod" and (l in EPISTEMICOS):
                return True
        # «aun cuando…» / «pese a que…» suelen colgar como advcl con mark compuesto
        return False

    # ---- predicado nominal / adjetival ----
    def _copula(self, A: Arbol, p: int, sujs: List[C], neg: bool) -> List[dict]:
        out: List[dict] = []
        cop = A.l(A.hijos(p, "cop")[0])
        pred_cop = "ESTAR" if cop == "estar" else "SER"
        when = self._año(A, p) if A.hijos(p, "case") else ""
        u = A.u(p)
        prep = self._prep(A, p)
        for S in sujs:
            out += _extra(S)
            if self._grado(A, p) and u in ("ADJ", "VERB"):
                continue                                          # «es más grande que…»: comparación, no cualidad
            if prep and u in ("NOUN", "PROPN", "X"):
                O = self.concepto(A, p)
                if O is not None and not when:
                    out += _extra(O)
                    out.append(_ud(S.key, pred_cop + "_" + prep.upper(), O.key, S.disp, O.disp, neg=neg, tpl="{s} " + ("está" if cop == "estar" else "es") + " " + prep + " {o}"))
                continue
            if u in ("ADJ", "VERB", "AUX"):
                for e in [p] + [j for j in A.hijos(p, "conj") if A.u(j) in ("ADJ", "VERB")]:
                    if self._grado(A, e):
                        continue
                    if A.u(e) == "ADJ" and A.l(e)[-2:] in ("ar", "er", "ir") and len(A.l(e)) > 4:
                        ad = clave(_participio_masc(A.f(e))) if _es_participio(A.f(e), A.l(e)) else ""      # lema verbal: «vencido», no «vencer»
                    else:
                        ad = clave(A.l(e)) if A.u(e) == "ADJ" else clave(_participio_masc(A.f(e)))
                    if not ad:
                        continue
                    out.append(_ud(S.key, pred_cop, ad, S.disp, A.l(e), neg=neg))
                    for o in A.hijos(e, "obl", "nmod"):
                        pr = self._prep(A, o)
                        if pr and A.u(o) in ("NOUN", "PROPN", "X") and not self._año(A, o):
                            O = self.concepto(A, o)
                            if O is not None:
                                out += _extra(O)
                                out.append(_ud(S.key, ad + "_" + pr.upper(), O.key, S.disp, O.disp, neg=neg, tpl="{s} es " + A.l(e) + " " + pr + " {o}"))
                continue
            if u in ("NOUN", "PROPN", "X"):
                for e in self.expandir(A, p):
                    if A.u(e) not in ("NOUN", "PROPN", "X"):
                        continue
                    core = self.concepto(A, e, califica=False)
                    if core is None or core.key == S.key:
                        continue
                    nuc = C(clave(core.base.disp if core.base else core.disp), (core.base.disp if core.base else core.disp), core.propio, e) if not core.propio else core
                    # clase (sin complementos): «un mamífero» ; con «de»: cola_de_castor ES cola
                    out.append(_ud(S.key, "ES", nuc.key, S.disp, nuc.disp, neg=neg, when=when))
                    for a in A.hijos(e, "amod"):
                        if A.u(a) == "ADJ" and not self._grado(A, a):
                            out.append(_ud(S.key, "SER", clave(A.l(a)), S.disp, A.l(a), neg=neg))
                    for j in A.hijos(e, "nmod"):
                        if self._prep(A, j) == "de" and A.u(j) in ("NOUN", "PROPN", "X") and not core.propio:
                            O = self.concepto(A, j, califica=False, prof=1)
                            if O is not None:
                                out += _extra(O)
                                out.append(_ud(S.key, nuc.key + "_DE", O.key, S.disp, O.disp, neg=neg, tpl="{s} es " + nuc.disp + " de {o}"))
                    for j in A.hijos(e, "nmod"):
                        if self._prep(A, j) in ("con", "sin") and A.u(j) in ("NOUN", "PROPN", "X"):
                            O = self.concepto(A, j, califica=False, prof=1)
                            if O is not None:
                                out += _extra(O)
                                out.append(_ud(S.key, "TENER", O.key, S.disp, O.disp, neg=neg or self._prep(A, j) == "sin", tpl="{s} tiene {o}"))
                    out += [x for x in _extra(core) if x["o"] != nuc.key or x["s"] != S.key]
        return out

    # ---- predicado verbal ----
    def _verbal(self, A: Arbol, p: int, sujs: List[C], neg: bool) -> List[dict]:
        out: List[dict] = []
        lema = A.l(p)
        if A.u(p) == "AUX" and lema in ("haber", "ser", "estar") and not A.hijos(p, "obj", "obl"):
            return out
        if lema == "haber":
            return out
        form = A.f(p)
        auxs = [A.l(j) for j in A.hijos(p, "aux")]
        pasiva = any(a in ("ser", "estar") for a in auxs) and _es_participio(form, lema) and not A.hijos(p, "obj")
        se = bool(A.hijos(p, "expl"))
        parti = _es_participio(form, lema) and not auxs and A.d(p) in ("acl", "amod", "advcl")
        when = ""
        # complementos
        comp: List[Tuple[str, int, str]] = []
        for j in A.k[p]:
            d = A.d(j)
            if d == "obj":
                comp.append(("", j, "obj"))
            elif d == "iobj":
                comp.append(("a", j, "iobj"))
            elif d == "obl":
                pr = self._prep(A, j)
                y = self._año(A, j)
                if y and pr in ("en", "durante", "desde", "hasta", "a", ""):
                    when = when or y
                    continue
                if pr and not A.hijos(A.hijos(j, "case")[0], "fixed") and A.u(j) in ("NOUN", "PROPN", "X"):
                    comp.append((pr, j, "obl"))
            elif d == "xcomp" and A.u(j) in ("NOUN", "ADJ") and lema in ATRIBUTIVOS:
                comp.append(("@attr", j, "xcomp"))
            elif d == "xcomp" and A.u(j) in ("NOUN", "ADJ") and A.hijos(j, "case") and lema in COPULAS | LOCATIVOS:
                comp.append((self._prep(A, j), j, "obl"))
        pred = "TENER" if lema == "tener" else clave(lema)
        for S in sujs:
            out += _extra(S)
            if pasiva:
                ag = [(pr, j) for pr, j, d in comp if pr == "por"]
                if ag:
                    for _, j in ag:
                        for e in self.expandir(A, j):
                            O = self.concepto(A, e)
                            if O is not None:
                                out += _extra(O)
                                out.append(_ud(O.key, pred, S.key, O.disp, S.disp, neg=neg, when=when, tpl="{s} " + _tpl_activa(form, lema) + " {o}"))
                else:
                    out.append(_ud(S.key, "SER", clave(_participio_masc(form)), S.disp, _participio_masc(form), neg=neg, when=when))
                for pr, j, d in comp:
                    if pr in ("en", "de", "con", "para", "como", "sobre") and d == "obl":
                        out += self._rel(A, S, clave(_participio_masc(form)) + "_" + pr.upper(), j, neg, when, "{s} es " + _participio_masc(form) + " " + pr + " {o}")
                    if lema in LOCATIVOS and pr == "en" and d == "obl":
                        out += self._rel(A, S, "ESTAR_EN", j, neg, when, "{s} está en {o}")
                continue
            for pr, j, d in comp:
                if pr == "@attr":
                    if A.u(j) == "ADJ":
                        out.append(_ud(S.key, "SER", clave(A.l(j)), S.disp, A.l(j), neg=neg, when=when))
                    else:
                        O = self.concepto(A, j, califica=False)
                        if O is not None:
                            out += _extra(O)
                            out.append(_ud(S.key, "ES", O.key, S.disp, O.disp, neg=neg, when=when))
                    continue
                if lema in LOCATIVOS and (se or pasiva or parti) and pr:
                    out += self._rel(A, S, "ESTAR_" + pr.upper(), j, neg, when, "{s} está " + pr + " {o}")
                    continue
                if d == "obj":
                    tpl = "{s} " + _tpl_verbo(form, lema) + " {o}"
                    out += self._rel(A, S, pred, j, neg, when, tpl)
                else:
                    tpl = "{s} " + _tpl_verbo(form, lema) + " " + pr + " {o}"
                    out += self._rel(A, S, pred + "_" + pr.upper(), j, neg, when, tpl)
        if not out_rel(out) and A.d(p) not in ("xcomp", "advcl", "acl", "ccomp") and not pasiva and not se and not A.hijos(p, "xcomp", "ccomp", "obj", "iobj") and not any(A.d(j) == "obl" for j in A.k[p]) and lema not in COPULAS | {"haber", "hacer", "poder", "deber", "soler", "tender", "ir"}:
            for S in sujs:
                out.append(_ud(S.key, pred, "_", S.disp, "", neg=neg, when=when, tpl="{s} " + _tpl_verbo(form, lema)))
        elif not out_rel(out) and when and not pasiva and not se and lema not in COPULAS | {"haber"}:
            for S in sujs:
                out.append(_ud(S.key, pred, "_", S.disp, "", neg=neg, when=when, tpl="{s} " + _tpl_verbo(form, lema)))
        return out

    def _rel(self, A: Arbol, S: C, pred: str, j: int, neg: bool, when: str, tpl: str) -> List[dict]:
        out: List[dict] = []
        for e in self.expandir(A, j):
            if A.u(e) == "PRON" and A.l(e) in PRON_REL:
                continue
            O = self.concepto(A, e)
            if O is None or O.key == S.key:
                continue
            out += _extra(O)
            out.append(_ud(S.key, pred, O.key, S.disp, O.disp, neg=neg, when=when, tpl=tpl))
        return out


def out_rel(out):
    return [h for h in out if h["o"] != "_" and h["p"] not in ("ES",) or h["p"] == "ES" and False]


def _es_participio(form: str, lema: str) -> bool:
    return bool(re.search(r"(ad|id)[oa]s?$|(to|cho|so)s?$", nrm(form))) and nrm(form) != nrm(lema)


def _tpl_activa(form: str, lema: str) -> str:
    return lema


def _ud(s, p, o, s_disp, o_disp, neg=False, when="", tpl=""):
    h = _h(s, p, o, s_disp, o_disp, tpl=tpl, neg=neg, when=when, when_disp=("en " + when) if when else "")
    h["_extra"] = False
    return h


def _extra(c: C) -> List[dict]:
    return list(c.extra) if c is not None else []


def _desde_hecho(h: dict) -> C:
    return C(h["s"], h.get("s_disp") or h["s"].title(), False)


def _limpiar(hs: List[dict]) -> List[dict]:
    vistos, out = set(), []
    for h in hs:
        if not h["s"] or not h["o"] or h["s"] == h["o"] or len(h["p"]) < 2:
            continue
        k = (h["s"], h["p"], h["o"], bool(h.get("neg")))
        if k in vistos:
            continue
        vistos.add(k)
        out.append(h)
    return out


# ====================================================================================================================================
class LectorUD(Lector):
    """Lee textos de cualquier longitud con la escuela. Misma interfaz que Lector (leer -> informe)."""
    MAX_FORMAS = 38

    def __init__(self, mem, parser, lex=None):
        super().__init__(mem, None, lex)
        self.parser = parser
        self.ud = ExtractorUD()
        self.traza: List[dict] = []

    def leer(self, texto: str, progreso=None) -> dict:
        self.traza = []
        rep = super().leer(texto, progreso)
        rep["traza"] = self.traza
        return rep

    # trocea una frase larga en tramos que la escuela pueda analizar (max 40 formas)
    def _tramos(self, f: str) -> List[str]:
        if len(re.findall(r"\w+|[^\w\s]", f)) <= self.MAX_FORMAS:
            return [f]
        partes = re.split(r"(?<=[;:])\s+|(?<=,)\s+(?=(?:pero|aunque|mientras|ya que|puesto que|sin embargo|por lo que|lo que|y)\b)", f)
        tramos, cur = [], ""
        for p in partes:
            if cur and len(re.findall(r"\w+|[^\w\s]", cur + " " + p)) > self.MAX_FORMAS:
                tramos.append(cur)
                cur = p
            else:
                cur = (cur + " " + p).strip()
        if cur:
            tramos.append(cur)
        return tramos

    def frase(self, f: str, rep: dict, inicio_parrafo=False):
        orig = f
        g = re.sub(r"\([^)]{0,80}\)", "", f)                                      # incisos entre paréntesis: ruido para la sintaxis
        g = re.sub(r"\s+—[^—]{0,200}—", ",", g)
        g = re.sub(r"\s+", " ", g).strip()
        n0 = len(rep["hechos"])
        motivo = ""
        for tr in self._tramos(g):
            try:
                rows = self.parser.tree(tr)
            except Exception:                                                     # noqa
                rows = []
            if not rows:
                continue
            try:
                hs = self.ud.oracion(rows, inicio=inicio_parrafo)
            except RecursionError:                                                # noqa  (árbol raro: se salta ese tramo, no se cuelga)
                hs = []
            motivo = motivo or self.ud.motivo
            if len(self.traza) < 600:
                self.traza.append({"tramo": tr, "arbol": rows, "hechos": [(h["s"], h["p"], h["o"], bool(h.get("neg"))) for h in hs]})
            for h in hs:
                self._guardar_ud(h, orig, rep)
        if len(rep["hechos"]) == n0:
            rep["sin_entender"].append({"frase": orig, "motivo": motivo or "no encuentro una relación clara entre conceptos"})

    def _guardar_ud(self, h: dict, frase: str, rep: dict):
        tr = (h["s"], h["p"], h["o"])
        if not all(tr) or tr[0] == tr[2]:
            return
        if self.mem.contradicts(tr, bool(h.get("neg"))):                           # lo que ya sé manda: se avisa, no se pisa
            rep.setdefault("conflictos", []).append({"hecho": f"{tr[0]} {'NO ' if h.get('neg') else ''}{tr[1]} {tr[2]}", "frase": frase})
            return
        nuevo = self.mem.add_fact(tr, source=frase[:300], neg=bool(h.get("neg")), when=h.get("when", ""), when_disp=h.get("when_disp", ""))
        self.mem.note_surface(tr, h.get("template") or None, h.get("s_disp"), h.get("o_disp"))
        rep["hechos"].append({"s": tr[0], "p": tr[1], "o": tr[2], "neg": bool(h.get("neg")), "frase": frase, "via": "escuela", "nuevo": bool(nuevo),
                              "sd": h.get("s_disp") or tr[0].title(), "od": h.get("o_disp") or tr[2].title()})


def lector_para(mem, parser=None):
    """El lector que corresponde: con escuela (comprensión por gramática) o, si no hay, el de patrones."""
    if parser is not None and hasattr(parser, "tree"):
        return LectorUD(mem, parser)
    return Lector(mem, None)


def escribir_traza(rep: dict, ruta) -> None:
    """Deja en un fichero, para cada frase leida: su arbol de dependencias (el de la escuela) y los hechos que salieron. Sirve para auditar la lectura."""
    L = [f"LECTURA: {rep.get('frases', 0)} frases, {len(rep.get('hechos', []))} hechos, {len(rep.get('sin_entender', []))} sin aprovechar", ""]
    for t in rep.get("traza", []):
        L.append(t["tramo"])
        L.append("   " + " ".join(f"{i + 1}:{r[0]}/{r[1]}->{r[2]}:{r[3]}[{r[4]}]" for i, r in enumerate(t["arbol"])))
        for s_, p_, o_, n_ in t["hechos"]:
            L.append(f"   => {s_} {'NO ' if n_ else ''}{p_} {o_}")
        L.append("")
    for x in rep.get("sin_entender", [])[:100]:
        L.append("SIN ENTENDER: " + x["frase"][:200] + "  (" + x["motivo"] + ")")
    try:
        import os
        os.makedirs(os.path.dirname(str(ruta)), exist_ok=True)
        open(ruta, "w", encoding="utf-8").write("\n".join(L))
    except OSError:
        pass


def guardar_traza(rep: dict) -> None:
    """Deja reports/ultima_lectura.txt (arbol + hechos de cada frase) para auditar lo que se leyo."""
    try:
        import os
        if rep.get("traza"):
            raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            escribir_traza(rep, os.path.join(raiz, "reports", "ultima_lectura.txt"))
    except Exception:                                                                  # noqa
        pass
