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
# unidades de medida (clase cerrada: sistema internacional y usuales): un numero + unidad es una CANTIDAD, no un concepto (parche-126)
UNIDADES = set("""km kilometro kilometros m metro metros cm centimetro centimetros mm milimetro milimetros kg kilogramo kilogramos g gramo gramos tonelada toneladas
litro litros hora horas minuto minutos segundo segundos dia dias semana semanas mes meses ano anos siglo siglos decada decadas milenio milenios euro euros dolar dolares
grado grados hectarea hectareas milla millas pie pies hab habitante habitantes km2 m2 m3 hm hm3 kw hz mhz ghz kelvin pascal newton julio julios vatio vatios
bit bits byte bytes mb gb ua pc h""".split())
NUM_ES = set("""trece catorce quince dieciseis diecisiete dieciocho diecinueve veintiun veintiuno veintiuna veintidos veintitres veinticuatro veinticinco veintiseis veintisiete veintiocho veintinueve
sesenta setenta ochenta noventa doscientos doscientas trescientos trescientas cuatrocientos cuatrocientas quinientos quinientas seiscientos seiscientas setecientos setecientas
ochocientos ochocientas novecientos novecientas""".split())
ESCALAS = {"millon", "millones", "mil", "miles", "billon", "billones", "docena", "docenas", "decena", "decenas", "centenar", "centenares"}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
# locuciones (expresiones fijas que no nombran cosas del mundo): «al principio», «en realidad», «de cara a», «con el objetivo de»…  (preposicion, nucleo)
LOCUCIONES = {("a", "principio"), ("en", "realidad"), ("de", "nuevo"), ("en", "lugar"), ("en", "instancia"), ("en", "general"), ("en", "particular"), ("en", "definitiva"),
              ("a", "menudo"), ("de", "manera"), ("de", "forma"), ("de", "modo"), ("en", "resumen"), ("en", "total"), ("a", "veces"), ("en", "ocasiones"), ("en", "cambio"),
              ("de", "hecho"), ("en", "efecto"), ("por", "cierto"), ("por", "fin"), ("de", "cara"), ("en", "vez"), ("a", "cabo"), ("con", "proposito"), ("con", "objetivo"),
              ("con", "fin"), ("con", "intencion"), ("con", "finalidad"), ("a", "partir"), ("en", "torno"), ("por", "tanto"), ("por", "ello"), ("a", "pesar"), ("a", "causa"),
              ("en", "base"), ("en", "funcion"), ("con", "respecto"), ("con", "relacion"), ("en", "relacion"), ("a", "traves"), ("en", "medio"), ("por", "ejemplo"),
              ("a", "raiz"), ("por", "vez"), ("a", "vez"), ("con", "tiempo"), ("de", "vez"), ("por", "primero"), ("en", "primer"), ("en", "segundo"), ("en", "ultimo"), ("por", "lo"), ("a", "lo"), ("en", "caso"), ("por", "parte"), ("en", "parte"), ("a", "tiempo"),
              ("de", "inmediato"), ("a", "continuacion"), ("al", "principio"), ("al", "respecto"), ("de", "momento"), ("en", "adelante"), ("por", "completo")}
FINALES = {"objetivo", "proposito", "fin", "finalidad", "intencion", "meta", "idea"}      # «con el objetivo de ayudar»: el que ayuda es el sujeto de la oracion principal
ASPECTUALES = {"llegar", "empezar", "comenzar", "seguir", "continuar", "volver", "dejar", "terminar", "acabar", "ir", "soler", "poder", "deber", "tratar", "intentar", "pretender",
               "querer", "lograr", "conseguir", "necesitar", "tender", "proceder", "pasar"}                                 # verbo + infinitivo: lo afirmado es del infinitivo
MODAL_COND = {"podria", "podrian", "podriamos", "pudiera", "pudieran", "pudiese", "pudiesen", "deberia", "deberian", "debiera", "debieran"}     # «podria dar»: posibilidad, no hecho
ORDINALES = {"PRIMERO", "SEGUNDO", "TERCERO", "CUARTO", "QUINTO", "ULTIMO", "PENULTIMO", "ANTERIOR", "SIGUIENTE", "MISMO", "OTRO", "UNO"}         # «los primeros de cada grupo»: no es un concepto
REL_BASURA = re.compile(r"(^|_)(CUAL|CUALES|QUE|QUIEN|QUIENES|CUYO|CUYA|CUYOS|CUYAS|DONDE)(_|$)")
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
        lm = (lm if lm and lm != "_" else self.r[i][0]).lower()
        if self.r[i][1] in ("VERB", "AUX"):                                          # «insuflarle», «llevarla», «disponerse» -> insuflar, llevar, disponer
            m = re.fullmatch(r"(\w{3,}?(?:ar|er|ir|ír))(?:me|te|se|nos|os|le|les|lo|los|la|las)(?:lo|la|los|las)?", self.r[i][0].lower())
            if m:
                return m.group(1).replace("ír", "ir")
        return lm

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
    __slots__ = ("key", "disp", "propio", "idx", "extra", "base", "cant", "refleja")

    def __init__(self, key, disp, propio=False, idx=-1, base=None):
        self.key, self.disp, self.propio, self.idx, self.base = key, disp, propio, idx, base
        self.extra: List[dict] = []
        self.cant = ""            # «el 90 % de X»: cantidad con la que se afirma algo de X
        self.refleja = False      # sujeto de una pasiva refleja («se celebra el día…»)


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
    n.cant = c.cant
    return n


class ExtractorUD:
    def __init__(self):
        self.principal_plural: Optional[bool] = None
        self.recientes: List[C] = []
        self.principal_edad = 0                      # frases desde que se fijó el tema: un tema viejo ya no es «el sujeto de esta frase»
        self.principal: Optional[C] = None          # sujeto de la oracion principal anterior (sujeto omitido, «él», «Su X»)
        self.clases: Dict[str, Set[str]] = {}       # clave -> claves de sus clases (para «este animal» = el tema)
        self.motivo = ""
        self._cants: Dict[str, str] = {}             # clave de concepto -> cantidad con que aparece en esta oracion (parche-126)
        self._en_sujeto = False
        self._clave_cant: Dict[str, str] = {}

    # ---------- conceptos ----------
    def _nombre(self, A: Arbol, i: int) -> Tuple[List[int], bool]:
        partes = [i] + [j for j in A.hijos(i, "flat", "compound") if A.u(j) in ("PROPN", "NOUN", "X", "NUM", "ADJ")]
        propio = A.u(i) == "PROPN" or any(A.u(j) == "PROPN" for j in partes)
        return sorted(partes), propio

    def concepto(self, A: Arbol, i: int, califica=True, prof=0) -> Optional[C]:
        u = A.u(i)
        if u == "PRON":
            return self.pronombre(A, i)
        if u not in ("NOUN", "PROPN", "X") and not (u == "SYM" and nrm(A.f(i)) in UNIDADES):
            return None
        m_ = self._medida(A, i, califica, prof)
        if m_ is not None:
            return m_
        if nrm(A.f(i)) in ESCALAS and i + 2 < A.n and nrm(A.f(i + 1)) == "de" and nrm(A.f(i + 2)) in UNIDADES:
            return None                                              # «715 millones de años»: la cantidad se guarda en «años», no es un concepto «715_MILLON»
        if u == "SYM":
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
            adjs = [j for j in A.hijos(i, "amod") if A.u(j) == "ADJ" and j > i and not self._grado(A, j)
                    and not re.search(r"(ad|id)[oa]s?$", nrm(A.f(j))) and not _es_participio(A.f(j), A.l(j))][:2]       # un participio («encargada», «presentado») es un estado, no una subclase
            if adjs:
                k3 = c.key + "".join("_" + clave(A.l(j)) for j in adjs)
                c.extra.append(_ud(k3, "ES", c.key, c.disp + " " + " ".join(A.l(j) for j in adjs), c.disp))
                c = _sub(c, k3, c.disp + " " + " ".join(A.l(j) for j in adjs), False)
        # complemento con «de»: «cola de castor», «Museo del Prado»
        if prof < 1:
            for j in A.hijos(i, "nmod"):
                if self._prep(A, j) == "de" and A.u(j) in ("NOUN", "PROPN", "X"):
                    s = self.concepto(A, j, califica=False, prof=prof + 1)
                    if s is not None and s.cant and s is not self.principal:
                        if self._en_sujeto:                                # «los menores de 12 años»: la edad califica al sujeto, no es su cantidad
                            k5 = c.key + "_DE_" + self._clave_cant.get(s.key, clave(s.cant))
                            d5 = c.disp + " de " + s.cant
                            c.extra.append(_ud(k5, "ES", c.key, d5, c.disp))
                            c = _sub(c, k5, d5, propio)
                        else:
                            c = _sub(c, c.key, c.disp, propio)             # «una distancia de 39 541 578 kilómetros»: DISTANCIA con su cantidad
                            self._cants[c.key] = s.cant
                        break
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

    # ---------- cantidades con unidad (parche-126) ----------
    @staticmethod
    def _es_cifra(f: str) -> bool:
        return bool(re.fullmatch(r"~?\d[\d.,]*", f)) or nrm(f) in NUM_PAL or nrm(f) in NUM_ES

    def _cantidad_izq(self, A: Arbol, i: int) -> Optional[int]:
        """Posicion donde empieza la cifra que precede a la unidad i: «11,68 km», «39 514 827 kilómetros», «715 millones de años», «cuarenta y dos días»."""
        j = i - 1
        if j >= 1 and nrm(A.f(j)) == "de" and nrm(A.f(j - 1)) in ESCALAS:
            j -= 1
        ini = None
        while j >= 0:
            w = nrm(A.f(j))
            if self._es_cifra(A.f(j)) or w in ESCALAS or (w == "y" and 1 <= j < i - 1 and self._es_cifra(A.f(j - 1)) and self._es_cifra(A.f(j + 1))):
                ini = j
                j -= 1
            else:
                break
        if ini is None or all(nrm(A.f(x)) in ESCALAS | {"de"} for x in range(ini, i)):
            return None
        return ini

    def _medida(self, A: Arbol, i: int, califica: bool, prof: int) -> Optional["C"]:
        """«11,68 km² de superficie», «3 000 km de radio», «715 millones de años», «un valor de 39 514 827 kilómetros»: la cifra con su unidad es una CANTIDAD (q)
        de un concepto limpio (SUPERFICIE, RADIO, ANO); no se crea el concepto «11_68_KM»."""
        f = nrm(A.f(i)).replace("²", "2").replace("³", "3")
        if f not in UNIDADES and nrm(A.l(i)) not in UNIDADES:
            return None
        ini = self._cantidad_izq(A, i)
        if ini is None:
            return None
        fin = i
        while fin + 1 < A.n:
            s = A.f(fin + 1)
            if s in ("²", "³"):
                fin += 1
            elif s == "/" and fin + 2 < A.n and nrm(A.f(fin + 2)) in UNIDADES:
                fin += 2
            else:
                break
        cant = " ".join(A.f(x) for x in range(ini, fin + 1)).replace(" ²", "²").replace(" ³", "³").replace(" / ", "/")
        c: Optional[C] = None
        if prof < 1:
            for j in A.hijos(i, "nmod"):
                if self._prep(A, j) == "de" and A.u(j) in ("NOUN", "PROPN", "X") and nrm(A.f(j)) not in UNIDADES:
                    c = self.concepto(A, j, califica=False, prof=prof + 1)
                    break
        if c is None:
            lem = nrm(A.l(i))
            base = lem if lem in UNIDADES and len(lem) > 2 else nrm(A.f(i))
            c = C(clave(base), base.upper() if len(base) <= 3 else base, False, i)
        else:
            c = _sub(c, c.key, c.disp)
        c.cant = cant
        self._cants[c.key] = cant
        self._clave_cant[c.key] = clave(" ".join(A.f(x) for x in range(ini, i))) + "_" + clave(A.l(i) if nrm(A.l(i)) in UNIDADES else A.f(i))
        return c

    def pronombre(self, A: Arbol, i: int) -> Optional[C]:
        l = A.l(i)
        if l in PRON_ANAF:
            return self.principal
        return None

    @staticmethod
    def _grado(A: Arbol, j: int) -> bool:
        return any(A.l(x) in COMPARATIVO for x in A.hijos(j, "advmod"))

    BARE = {("en", "lugar"), ("en", "parte"), ("en", "caso"), ("en", "medio"), ("en", "vez"), ("a", "tiempo"), ("en", "base"), ("en", "funcion"), ("en", "general"), ("en", "particular")}

    def _locucion(self, A: Arbol, j: int) -> bool:
        """«al principio», «en realidad», «de cara a», «con el objetivo de», «en primer lugar»: expresiones fijas, no cosas del mundo (no se guardan como complemento)."""
        cs = A.hijos(j, "case")
        if not cs:
            return False
        par = (nrm(A.l(cs[0])), nrm(A.l(j)))
        if par not in LOCUCIONES:
            return False
        dets = A.hijos(j, "det")
        if par != ("por", "parte") and any(A.l(x) in DEMOSTRATIVOS or A.l(x) in POSESIVOS for x in dets):      # «por su parte»
            return False
        return not (par in self.BARE and dets)

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
    def _cuando(A: Arbol, i: int) -> str:
        """Fecha de un complemento temporal: «el 16 de diciembre de 1850» -> abs:1850-12-16/1850-12-16, «agosto de 1999» -> el mes entero, «el 17 de mayo» -> 17_mayo,
        «en 1850» -> 1850. Sin fecha reconocible, ''."""
        import calendar
        sub = A.sub(i)
        for m in sub:
            w = nrm(A.f(m))
            if w not in MESES:
                continue
            mes = MESES.index(w) + 1
            dia = None
            d_ = m - 2 - (1 if m >= 3 and A.f(m - 2) in ("º", "ª", "o") else 0)
            if m >= 2 and nrm(A.f(m - 1)) == "de" and d_ >= 0 and re.fullmatch(r"\d{1,2}", A.f(d_)) and 1 <= int(A.f(d_)) <= 31:
                dia = int(A.f(d_))
            elif m >= 2 and nrm(A.f(m - 1)) == "de" and nrm(A.f(m - 2)) == "primero":
                dia = 1
            ano = None
            k_ = m + 2 + (2 if m + 4 < A.n and nrm(A.f(m + 2)) == "el" and nrm(A.f(m + 3)) == "ano" else 0)
            if k_ < A.n and nrm(A.f(m + 1)) == "de" and re.fullmatch(r"\d{3,4}", A.f(k_)):
                ano = int(A.f(k_))
            elif m + 1 < A.n and re.fullmatch(r"(1\d{3}|20\d{2})", A.f(m + 1)):
                ano = int(A.f(m + 1))
            if ano and 100 <= ano <= 2100:
                if dia and dia <= calendar.monthrange(ano, mes)[1]:
                    d_ = f"{ano:04d}-{mes:02d}-{dia:02d}"
                    return f"abs:{d_}/{d_}"
                if not dia:
                    return f"abs:{ano:04d}-{mes:02d}-01/{ano:04d}-{mes:02d}-{calendar.monthrange(ano, mes)[1]:02d}"
            if dia and not ano:
                return f"{dia}_{w}"
        return ExtractorUD._año(A, i)

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
                if A.d(n_) == "csubj" or A.u(n_) == "VERB" or self._comparado(A, n_):
                    continue
                if A.u(n_) == "PRON" and A.l(n_) in PRON_REL:
                    ant = self.antecedente(A, p)
                    if ant:
                        cs += ant
                    continue
                self._en_sujeto = True
                try:
                    for e in self.expandir(A, n_):
                        c = self._cuantificado(A, e) or self.concepto(A, e)
                        if c is not None:
                            cs.append(c)
                finally:
                    self._en_sujeto = False
            res = cs or None
        else:
            res = self._refleja(A, p) or self._heredado(A, p, memo)
        memo[p] = res
        return res

    EDAD_MAX = 1
    VENTANA = 6
    COMPARATIVAS = ("al igual que", "igual que", "a diferencia de", "asi como", "tal como", "como", "tanto como", "lo mismo que", "de igual modo que")

    @staticmethod
    def _comparado(A: Arbol, n: int) -> bool:
        """«Al igual que Mercurio, carece de satélites»: Mercurio es el término de la comparación, no el sujeto."""
        previas = []
        j = n - 1
        while j >= 0 and A.u(j) not in ("PUNCT",) and len(previas) < 4:
            if A.u(j) == "DET" and A.d(j) == "det" and A.h[j] == n:
                j -= 1
                continue
            previas.insert(0, nrm(A.f(j)))
            j -= 1
        txt = re.sub(r"\bde el\b", "del", re.sub(r"\ba el\b", "al", " ".join(previas)))       # la escuela separa «al» y «del»
        return any(txt.endswith(c) and (txt == c or txt[: -len(c)].endswith(" ")) for c in ExtractorUD.COMPARATIVAS)

    PARTITIVOS = {"mayoría", "mayoria", "mitad", "tercio", "parte", "resto", "porcentaje", "minoría", "minoria", "cuarto"}

    def _cuantificado(self, A: Arbol, i: int) -> Optional[C]:
        """«El 90 % de las hemorragias…», «la mayoría de los casos…»: se habla de las hemorragias, pero no de todas: se guarda con su cantidad."""
        if not (A.f(i) == "%" or A.l(i) in self.PARTITIVOS or A.u(i) == "SYM"):
            return None
        for j in A.hijos(i, "nmod"):
            if self._prep(A, j) == "de" and A.u(j) in ("NOUN", "PROPN"):
                c = self.concepto(A, j, califica=False)
                if c is None:
                    return None
                num = next((A.f(x) for x in A.hijos(i, "nummod")), "")
                c = _sub(c, c.key, c.disp)
                c.cant = ((num + " " + A.f(i)) if num else A.l(i)).strip()
                return c
        return None

    def _refleja(self, A: Arbol, p: int) -> Optional[List[C]]:
        """Pasiva refleja con el paciente delante del verbo: «El Día Mundial se celebra el 17 de mayo» (la escuela lo etiqueta como complemento)."""
        if not A.hijos(p, "expl") or A.hijos(p, "nsubj", "csubj") or A.u(p) != "VERB":
            return None
        f = nrm(A.f(p))
        if f.endswith("n") or f.endswith(("ando", "iendo")):
            return None
        for j in A.hijos(p, "obl", "obj"):
            if j < p and A.u(j) in ("NOUN", "PROPN") and not A.hijos(j, "case") and not A.hijos(j, "nummod"):
                c = self.concepto(A, j)
                if c is not None:
                    c = _sub(c, c.key, c.disp)
                    c.refleja = True
                    return [c]
        return None

    def _heredado(self, A: Arbol, p: int, memo) -> Optional[List[C]]:
        d, h = A.d(p), A.h[p]
        if h >= 0 and d in ("conj", "xcomp", "advcl", "parataxis") and (A.u(h) in ("VERB", "AUX") or A.hijos(h, "cop")):
            s = self.sujeto(A, h, memo)
            if s and d in ("conj", "xcomp", "advcl"):
                return s
        if d == "acl" and h >= 0 and nrm(A.l(h)) in FINALES:      # «con el objetivo de ayudar»: ayuda el sujeto de la oracion principal, no el «objetivo»
            g = A.h[h]
            for _ in range(3):
                if g < 0 or A.u(g) in ("VERB", "AUX") or A.hijos(g, "cop"):
                    break
                g = A.h[g]
            if g >= 0 and g != p:
                return self.sujeto(A, g, memo)
            return None
        if d == "acl":
            return self.antecedente(A, p)
        if A.hijos(p, "expl") and not A.hijos(p, "nsubj"):
            return None                                       # «se observan leones»: impersonal / pasiva refleja
        if self.principal is not None and self.principal_edad <= self.EDAD_MAX and self._puede_heredar(A, p):
            return [self.principal]
        return None

    def _puede_heredar(self, A: Arbol, p: int) -> bool:
        """El sujeto omitido (el tema del discurso) solo se hereda en un verbo conjugado y que concuerde en número con él: un infinitivo,
        un gerundio o un participio sin sujeto no son «el tema hace X», y «hicieron» no puede ser un tema singular."""
        cop = A.hijos(p, "cop") or [j for j in A.hijos(p, "aux") if A.l(j) in ("ser", "estar", "haber")]
        v = cop[0] if cop else p
        f, lm = nrm(A.f(v)), nrm(A.l(v))
        if f.endswith(("ando", "iendo", "yendo")) or (f.endswith(("ar", "er", "ir")) and len(f) > 3 and f == lm) or (not cop and _es_participio(A.f(v), A.l(v))):
            return False
        if self.principal_plural is not None and len(f) > 4 and not f.endswith(("ción", "sión")):
            verbo_plural = f.endswith("n") and not f.endswith(("ion", "men", "ten")) or (cop and f in ("son", "eran", "fueron", "estan", "estaban"))
            if verbo_plural != self.principal_plural and (f.endswith("n") or self.principal_plural):
                return False
        return True

    @staticmethod
    def _plural_nombre(A: Arbol, i: int) -> Optional[bool]:
        for d in A.hijos(i, "det"):
            f = A.f(d).lower()
            if f in ("los", "las", "unos", "unas", "estos", "estas", "esos", "esas", "sus", "muchos", "muchas", "varios", "varias"):
                return True
            if f in ("el", "la", "un", "una", "este", "esta", "ese", "esa", "su"):
                return False
        if A.hijos(i, "nummod") and A.f(A.hijos(i, "nummod")[0]).lower() not in ("un", "uno", "una", "1"):
            return True
        if A.u(i) == "PROPN":
            return bool(A.hijos(i, "conj"))                   # un nombre propio es singular (Valdés, Cortés), salvo coordinado: «Ana y Luis»
        f = A.f(i).lower()
        return bool(f.endswith("s") and len(f) > 3 and not f.endswith(("is", "us", "es")) or (f.endswith("es") and len(f) > 5))

    def _concordante(self, A: Arbol, p: int, h: int) -> int:
        """«un niño de once años que practica…»: la escuela cuelga la relativa del nombre más cercano (años). El verbo concuerda en número
        con su antecedente: si no concuerda con h, se sube por la cadena de «de» hasta el nombre que sí concuerde."""
        vf = A.f(p).lower()
        if not A.hijos(p, "nsubj") or A.l(A.hijos(p, "nsubj")[0]) != "que" or len(vf) < 4:
            return h
        plural_v = vf.endswith("n") and not vf.endswith(("ción", "sión"))
        x, vistos = h, 0
        while vistos < 4:
            pl = self._plural_nombre(A, x)
            if pl is None or pl == plural_v:
                return x
            if A.d(x) not in ("nmod", "obl") or A.h[x] < 0 or A.u(A.h[x]) not in ("NOUN", "PROPN"):
                return h
            x, vistos = A.h[x], vistos + 1
        return h

    def antecedente(self, A: Arbol, p: int) -> Optional[List[C]]:
        """Relativa/participio: el nombre al que modifica (si es un predicado nominal, el sujeto de la copula)."""
        h = A.h[p]
        if h < 0:
            return None
        h = self._concordante(A, p, h)
        if A.hijos(h, "cop") and A.u(h) in ("NOUN", "PROPN"):
            ns = A.hijos(h, "nsubj")
            if ns:
                c = self.concepto(A, ns[0])
                return [c] if c is not None else None
        self._en_sujeto = True                                       # el antecedente es el sujeto de la relativa
        try:
            c = self.concepto(A, h, califica=False)
        finally:
            self._en_sujeto = False
        return [c] if c is not None else None

    # ---------- una oracion ----------
    def oracion(self, rows: List[Row], inicio=False) -> List[dict]:
        if not rows:
            return []
        A = Arbol(rows)
        self.motivo = ""
        self._cants = {}
        if self._meta(A):
            self.motivo = "es texto sobre el propio documento (avisos, enlaces), no conocimiento"
            return []
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
                for h in out[antes:]:
                    for S_ in sujs:
                        if S_.cant and h["s"] == S_.key:
                            h["q"] = S_.cant
                    if h["p"] == "ES" and h.get("q"):
                        h["q"] = ""
                    cq = self._cants.get(h["o"])
                    estructura = h["p"] == "ES" and (h["s"].startswith(h["o"] + "_") or h["s"].endswith("_" + h["o"]))      # «NINO_DE_ONCE_ANO ES NINO»: no es un hecho con cantidad
                    if cq and not h.get("q") and not estructura:             # «tiene 11,68 km² de superficie»: SUPERFICIE con su cantidad
                        h["q"] = cq
                        if h["p"] in ("ES", "SER", "SER_DE"):
                            h["p"] = "TENER"
            except Exception:                                    # noqa
                continue
            if principal_nuevo is None and (p == raiz and A.hijos(p, "nsubj") or A.d(p) == "xcomp" and A.h[p] == raiz and A.l(raiz) in ASPECTUALES and A.hijos(raiz, "nsubj")) and len(out) > antes and not (self.principal is not None and sujs[0].key.endswith("_DE_" + self.principal.key)):
                principal_nuevo = sujs[0]
        self.principal_edad += 1
        if principal_nuevo is not None:
            self.principal_edad = 0
            self.recientes.append(principal_nuevo)
            del self.recientes[:-self.VENTANA]
            veces = {}
            for c_ in self.recientes:
                veces[c_.key] = veces.get(c_.key, 0) + 1
            tope = max(veces.values())
            principal_nuevo = next(c_ for c_ in reversed(self.recientes) if veces[c_.key] == tope)      # el tema es el sujeto más constante, no el último
            self.principal = principal_nuevo
            self.principal_plural = self._plural_nombre(A, principal_nuevo.idx) if 0 <= principal_nuevo.idx < A.n else None
        elif self.principal is None and out:
            self.principal = _desde_hecho(out[0])
            self.principal_edad = 0
        for h in out:
            if h["p"] == "ES" and self.principal is not None and h["s"] == self.principal.key:
                self.clases.setdefault(h["s"], set()).add(h["o"])
        return _limpiar(out)

    DOC = {"artículo", "articulo", "sección", "seccion", "página", "pagina", "aviso", "plantilla", "wikipedia", "borrador"}

    def _meta(self, A: Arbol) -> bool:
        """Texto sobre el propio documento y no sobre el mundo: «Este artículo necesita más referencias», «Busca fuentes», «véase X»,
        y las correlativas «cuanto más A, más B» (no afirman un hecho)."""
        for i in range(A.n):
            l, f = A.l(i), nrm(A.f(i))
            if l in self.DOC and any(A.l(j) in ("este", "esta", "dicho", "dicha") for j in A.hijos(i, "det")):
                return True
            if f in ("vease", "consultese", "compárese", "comparese") or (f == "busca" and i + 1 < A.n and nrm(A.f(i + 1)) == "fuentes"):
                return True
            if f == "cuanto" and i + 1 < A.n and nrm(A.f(i + 1)) in ("mas", "menos", "mayor", "menor"):
                return True
        return False

    def _hipotetico(self, A: Arbol, p: int) -> bool:
        """Oraciones que no afirman: condicionales, concesivas, creencias (ccomp), epistémicos."""
        if A.d(p) in ("ccomp", "csubj", "parataxis"):
            return True
        if any(A.l(j) in ("poder", "deber") and nrm(A.f(j)) in MODAL_COND for j in A.hijos(p, "aux")) or \
                (A.d(p) == "xcomp" and A.h[p] >= 0 and A.l(A.h[p]) in ("poder", "deber") and nrm(A.f(A.h[p])) in MODAL_COND):
            return True                                           # «podría dar un paso»: posibilidad, no hecho
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
        when = self._cuando(A, p) if A.hijos(p, "case") else ""
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
                        if pr and A.u(o) in ("NOUN", "PROPN", "X") and not self._cuando(A, o) and not self._locucion(A, o):
                            O = self.concepto(A, o)
                            if O is not None:
                                out += _extra(O)
                                out.append(_ud(S.key, ad + "_" + pr.upper(), O.key, S.disp, O.disp, neg=neg, tpl="{s} es " + A.l(e) + " " + pr + " {o}"))
                continue
            if u in ("NOUN", "PROPN", "X"):
                for e in self.expandir(A, p):
                    if A.u(e) not in ("NOUN", "PROPN", "X") or A.l(e) in DEMOSTRATIVOS or A.l(e) in PRON_ANAF:
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
        if lema in ASPECTUALES and any(A.d(x) == "xcomp" and A.u(x) in ("VERB", "AUX") for x in A.k[p]):
            return out                                       # «llegó a firmar», «intenta aprovechar»: lo afirmado es del infinitivo (parche-126)
        form = A.f(p)
        auxs = [A.l(j) for j in A.hijos(p, "aux")]
        pasiva = any(a in ("ser", "estar") for a in auxs) and _es_participio(form, lema) and not A.hijos(p, "obj")
        se = bool(A.hijos(p, "expl"))
        parti = _es_participio(form, lema) and not auxs and A.d(p) in ("acl", "amod", "advcl")
        when = ""
        # complementos
        comp: List[Tuple[str, int, str]] = []
        src = list(A.k[p])
        hh = A.h[p]
        if A.d(p) == "xcomp" and hh >= 0 and A.l(hh) in ASPECTUALES:                  # «llegó a firmar como X»: la escuela cuelga «como X» del verbo auxiliar
            src += [j for j in A.k[hh] if A.d(j) == "obl" and j > p and j not in src]
        for j in src:
            d = A.d(j)
            if d == "obj":
                comp.append(("", j, "obj"))
            elif d == "iobj":
                comp.append(("a", j, "iobj"))
            elif d == "obl":
                pr = self._prep(A, j)
                y = self._cuando(A, j)
                if y and pr in ("en", "durante", "desde", "hasta", "a", ""):
                    when = when or y
                    continue
                if pr and not A.hijos(A.hijos(j, "case")[0], "fixed") and A.u(j) in ("NOUN", "PROPN", "X") and not self._locucion(A, j):
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
        if se and not out_rel(out) and any(S.refleja for S in sujs):
            for S in sujs:
                out.append(_ud(S.key, "SE_" + pred, "_", S.disp, "", neg=neg, when=when, tpl="{s} se " + _tpl_verbo(form, lema)))
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


def _cuando_disp(w: str) -> str:
    if w.startswith("abs:"):
        a, _, b = w[4:].partition("/")
        b = b or a
        try:
            y, m, d = a.split("-")
            if a == b:
                return f"el {int(d)} de {MESES[int(m) - 1]} de {int(y)}"
            if a[:7] == b[:7] and a.endswith("-01"):
                return f"en {MESES[int(m) - 1]} de {int(y)}"
        except (ValueError, IndexError):
            pass
        return f"entre {a} y {b}"
    m_ = re.fullmatch(r"(\d{1,2})_([a-z]+)", w)
    if m_:
        return f"el {m_.group(1)} de {m_.group(2)}"
    return "en " + w


def _ud(s, p, o, s_disp, o_disp, neg=False, when="", tpl=""):
    h = _h(s, p, o, s_disp, o_disp, tpl=tpl, neg=neg, when=when, when_disp=_cuando_disp(when) if when else "")
    h["_extra"] = False
    return h


def _extra(c: C) -> List[dict]:
    return list(c.extra) if c is not None else []


def _desde_hecho(h: dict) -> C:
    return C(h["s"], h.get("s_disp") or h["s"].title(), False)


def _basura(k: str) -> bool:
    """Concepto que no lo es: pronombre relativo dentro («AGUA_DE_CUAL»), solo cifras («3_C»), o una palabra repetida («ALBEDO_DE_ALBEDO_BOLOMETRICO»)."""
    if not k or k == "_":
        return False
    if k in ORDINALES:
        return True
    if REL_BASURA.search(k) or re.fullmatch(r"\d+(?:_\d+)*(?:_[A-Z])?", k):
        return True
    toks = [x for x in k.split("_") if len(x) > 3]
    return len(toks) != len(set(toks))


def _limpiar(hs: List[dict]) -> List[dict]:
    vistos, out = set(), []
    for h in hs:
        if not h["s"] or not h["o"] or h["s"] == h["o"] or len(h["p"]) < 2:
            continue
        if _basura(h["s"]) or _basura(h["o"]) or h["s"].lower() in UNIDADES:      # «7.12 km² corresponden a tierra firme»: el sujeto no es «KM»
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
        self._fichas: List[Tuple[str, str]] = []
        self.traza: List[dict] = []

    def ficha(self, k: str, v: str, rep: dict) -> bool:
        """«Radio medio: 6051,8 km» -> (tema, TENER, RADIO_MEDIO) con la cantidad «6051,8 km». Hasta saber de que se habla se guardan en espera."""
        if self.ud.principal is None:
            self._fichas.append((k, v))
            return True
        self._volcar_fichas(rep)
        self._guardar_ficha(k, v, rep)
        return True

    def _guardar_ficha(self, k: str, v: str, rep: dict):
        tema, kc = self.ud.principal, clave(k)
        if tema is None or not kc or len(kc) > 40:
            return
        h = _ud(tema.key, "TENER", kc, tema.disp, k.strip().lower())
        h["q"] = v.strip()
        self._guardar_ud(h, f"{k}: {v}", rep)

    def _volcar_fichas(self, rep: dict):
        pend, self._fichas = self._fichas, []
        for k, v in pend:
            self._guardar_ficha(k, v, rep)

    def leer(self, texto: str, progreso=None) -> dict:
        self.traza = []
        self._fichas = []
        self._doc = 1 + max([t.get("d", 0) for t in getattr(self.mem, "textos", [])] or [0])
        self._k = 0
        self._p = 0
        n0 = len(self.mem.facts)
        rep = super().leer(texto, progreso)
        if self._fichas and self.ud.principal is not None:
            self._volcar_fichas(rep)
            rep["nuevos"] = sum(1 for h in rep["hechos"] if h["nuevo"])
        rep["traza"] = self.traza
        try:
            from src.language.anclaje import anclar
            rep["anclaje"] = anclar(self.mem, rep["hechos"], n0)
        except Exception:                                                             # noqa
            pass
        return rep

    # trocea una frase larga en tramos que la escuela pueda analizar (max 40 formas: lo que pasa de ahi se perdia sin avisar, parche-127)
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
        out = []
        for t in tramos:
            out.extend(self._trocear(t))
        return out

    def _trocear(self, t: str) -> List[str]:
        """Un tramo que aun pasa del maximo se corta por una coma, una raya o antes de «y / que / quien / donde...»; si no hay, por palabras."""
        sal = []
        while True:
            toks = [m for m in re.finditer(r"\w+|[^\w\s]", t)]
            if len(toks) <= self.MAX_FORMAS:
                sal.append(t)
                return sal
            tope = toks[self.MAX_FORMAS - 1].end()
            mejor = None
            for m in re.finditer(r"[,;:—–]\s+|\s+(?=(?:y|e|que|quien|quienes|donde|cuando|pero|aunque|mientras)\b)", t[:tope + 1]):
                if m.end() <= tope + 1 and m.start() >= 20:
                    mejor = m
            cut = mejor.end() if mejor is not None else (t.rfind(" ", 0, tope) + 1 or tope)
            sal.append(t[:cut].strip(" ,;:—–"))
            t = t[cut:].strip(" ,;:—–")
            if not t:
                return sal

    FICHA_RX = re.compile(r"^(?P<nom>[A-ZÁÉÍÓÚÑ][^\s(),]*(?:\s+(?:de|del|la|las|los|y|von|van|da|di|[A-ZÁÉÍÓÚÑ][^\s(),]*)){0,5})\s*\((?P<in>[^()]{6,140})\)")
    FECHA_RX = re.compile(r"(?:\d{1,2}\s+de\s+[a-záéíóúñ]+\s+de\s+\d{3,4}|[a-záéíóúñ]+\s+de\s+\d{3,4}|\d{3,4})")

    def _ficha(self, f: str) -> List[str]:
        """«Marie Curie (Varsovia, 7 de noviembre de 1867 - Passy, 4 de julio de 1934) fue ...»: nacimiento y muerte dichos entre parentesis, como frases normales."""
        m = self.FICHA_RX.match(f)
        if not m or not re.search(r"\d{3,4}", m.group("in")):
            return []
        partes = re.split(r"\s+[-–—]\s+|(?<=\d)\s*[-–—]\s*(?=[A-ZÁÉÍÓÚÑ\d])", m.group("in"), maxsplit=1)
        out = []
        for verbo, parte in zip(("nació", "falleció"), partes):
            fm = self.FECHA_RX.search(parte)
            if not fm:
                continue
            lugar = re.sub(r"^(?:n\.|m\.|\*|†|\+)\s*", "", parte[:fm.start()].strip(" ,;"))
            lugar = lugar if (lugar and len(lugar.split()) <= 5 and lugar[:1].isupper() and not re.search(r"\d", lugar)) else ""
            fecha = fm.group(0)
            cuando = ("el " + fecha) if re.match(r"\d{1,2}\s+de", fecha) else ("en " + fecha)
            out.append(f"{m.group('nom')} {verbo}" + (f" en {lugar}" if lugar else "") + f" {cuando}.")
        return out

    @staticmethod
    def _incisos(f: str) -> List[str]:
        out = [m.group(1).strip(" ,;") for m in re.finditer(r"—([^—]{12,220})—", f)]
        saltar = None
        fm = re.match(r"^[^(]{1,60}\((?P<in>[^()]{6,140})\)", f)
        if fm and re.search(r"\d{3,4}\s*[-–—]|\d{3,4}\s+de\s+\w+\s*[-–—]", fm.group("in") + " "):
            saltar = fm.group("in")
        for m in re.finditer(r"\(([^()]{12,160})\)", f):
            c = m.group(1)
            if c == saltar:
                continue
            if len(re.findall(r"[^\W\d_]{3,}", c)) >= 3:
                out.append(c.strip())
        return out[:4]

    def frase(self, f: str, rep: dict, inicio_parrafo=False):
        orig = f
        if inicio_parrafo:
            self._p = getattr(self, "_p", 0) + 1
        g = re.sub(r"\([^)]{0,80}\)", "", f)                                      # incisos entre paréntesis: ruido para la sintaxis
        g = re.sub(r"\s+—[^—]{0,200}—", ",", g)
        g = re.sub(r"\s+", " ", g).strip()
        n0 = len(rep["hechos"])
        motivo = ""
        arboles = []
        for tr in self._tramos(g):
            try:
                rows = self.parser.tree(tr)
            except Exception:                                                     # noqa
                rows = []
            if not rows:
                continue
            arboles.append("\n".join("\t".join(str(x) for x in r[:5]) for r in rows))
            try:
                hs = self.ud.oracion(rows, inicio=inicio_parrafo)
            except RecursionError:                                                # noqa  (árbol raro: se salta ese tramo, no se cuelga)
                hs = []
            motivo = motivo or self.ud.motivo
            nums = sum(1 for r in rows if r[1] == "NUM" or str(r[0]).replace(",", "").replace(".", "").isdigit())
            if rows and nums > 0.4 * len([r for r in rows if r[1] != "PUNCT"]):          # filas de tabla («Infantil A: 1 0 0»): no son afirmaciones
                hs = []
            if len(self.traza) < 600:
                self.traza.append({"tramo": tr, "arbol": rows, "hechos": [(h["s"], h["p"], h["o"], bool(h.get("neg"))) for h in hs]})
            for h in hs:
                self._guardar_ud(h, orig, rep)
        if len(rep["hechos"]) == n0:
            rep["sin_entender"].append({"frase": orig, "motivo": motivo or "no encuentro una relación clara entre conceptos"})
        if not getattr(self, "_en_ficha", False):                                 # nacimiento y muerte del parentesis de una biografia, como frases propias
            self._en_ficha = True
            try:
                for fs_ in self._ficha(orig):
                    self.frase(fs_, rep, False)
            finally:
                self._en_ficha = False
        for inc in self._incisos(orig):                                           # parche-127: lo dicho entre rayas o parentesis tambien se guarda para contestar, aparte de los hechos
            for tr in self._tramos(inc):
                try:
                    rows = self.parser.tree(tr)
                except Exception:                                                 # noqa
                    rows = []
                if rows:
                    arboles.append("@\n" + "\n".join("\t".join(str(x) for x in r[:5]) for r in rows))
        try:                                                                      # parche-127: la frase queda guardada para poder contestar sobre ella
            self._k = getattr(self, "_k", 0) + 1
            if self.mem.add_texto(orig, arboles, (rep.get("titulos") or [""])[-1], getattr(self, "_doc", 1), self._k, getattr(self, "_p", 0)) is not False:
                rep["memorizadas"] = rep.get("memorizadas", 0) + 1
        except Exception:                                                         # noqa
            pass

    @staticmethod
    def _basura(tr) -> bool:
        """Hechos que no dicen nada: siglas sueltas («F»), numeros como sujeto («9_GOL ES GOL») y nombres kilometricos."""
        s_, p_, o_ = tr
        if len(s_) == 1 or len(o_) == 1 or s_[:1].isdigit():
            return True
        if s_.count("_DE_") + s_.count("_DEL_") > 3 or o_.count("_DE_") + o_.count("_DEL_") > 3 or len(s_) > 70 or len(o_) > 70:
            return True
        return False

    def _guardar_ud(self, h: dict, frase: str, rep: dict):
        tr = (h["s"], h["p"], h["o"])
        if not all(tr) or tr[0] == tr[2]:
            return
        if self._basura(tr):
            rep["descartados"] = rep.get("descartados", 0) + 1
            return
        if self.mem.contradicts(tr, bool(h.get("neg"))):                           # lo que ya sé manda: se avisa, no se pisa
            rep.setdefault("conflictos", []).append({"hecho": f"{tr[0]} {'NO ' if h.get('neg') else ''}{tr[1]} {tr[2]}", "frase": frase})
            return
        nuevo = self.mem.add_fact(tr, source=frase[:300], neg=bool(h.get("neg")), when=h.get("when", ""), when_disp=h.get("when_disp", ""), quant=h.get("q", ""))
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
    an = rep.get("anclaje")
    if an:
        L.append("CONCEPTOS: " + ", ".join(f"{k}={v}" for k, v in an["cuenta"].items()))
        for k, e in sorted(an["conceptos"].items()):
            L.append(f"   {e['estado']:9s} {k}" + (("  [" + " > ".join(e["clase"]) + "]") if e["clase"] else "") + (" (provisional)" if e["estado"] == "nuevo" and not e.get("definido") else "") + (f" ajuste={e['ajuste']}" if e.get("ajuste") is not None else ""))
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
