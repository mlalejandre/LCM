"""LCM 2.13 · ENRUTADOR DE CÁLCULO.

El LCM no hace cuentas de memoria. Aquí solo se ENTIENDE qué se pide:
  · qué operación (según el léxico que declara cada aplicación del registro `src.apps`)
  · con qué datos (cifras, numerales dichos con palabras, el resultado anterior, datos de un problema)
y se construye un árbol de llamadas a aplicaciones. Cada nodo se ejecuta con `registro.ejecuta`, que devuelve el valor y su traza.
El LCM recoge el resultado y lo dice; si se le pregunta «¿cómo lo has calculado?», enseña la traza.

El reconocimiento se construye A PARTIR DEL REGISTRO (y se rehace si cambia su huella): una aplicación nueva con su léxico
queda entendida sin tocar este archivo.
"""
from __future__ import annotations

import re
from fractions import Fraction as Fr

from src.apps import registro as R
from src.apps import mates as M
from src.apps.registro import ErrorApp
from .morfo import sa
from .numerales import a_cifras


class _NoVale(Exception):
    pass


# ------------------------------------------------------------------ léxico, construido desde el registro
_LEX = {"huella": None}


def lexico():
    h = R.manifiesto()["huella"]
    if _LEX["huella"] == h:
        return _LEX
    ops, pref, suf, verbos, sust, prob_mas, prob_menos, preg = [], [], [], {}, [], [], [], []
    for a in R.de_familia("aritmetica"):
        L = a.lexico
        for o in L.get("operador", []):
            ops.append((tuple(_toks(o)), a.nombre))
        for p in L.get("prefijo", []):
            pref.append((tuple(_toks(p)), a.nombre))
        for s_, e in (L.get("sufijo") or {}).items():
            suf.append((tuple(_toks(s_)), a.nombre, e))
        for v in L.get("verbo", []):
            verbos[sa(v.lower())] = a.nombre
        for n in L.get("sustantivo", []):
            sust.append((tuple(_toks(n)), a.nombre))
        for q in L.get("pregunta", []):
            preg.append((sa(q.lower()), a.nombre))
        prob_mas += [sa(x.lower()) for x in L.get("problema_mas", [])]
        prob_menos += [sa(x.lower()) for x in L.get("problema_menos", [])]
    por_largo = lambda xs: sorted(xs, key=lambda x: -len(x[0]))
    _LEX.update(huella=h, ops=por_largo(ops), pref=por_largo(pref), suf=por_largo(suf), verbos=verbos, sust=por_largo(sust),
                mas=sorted(set(prob_mas), key=lambda x: -len(x)), menos=sorted(set(prob_menos), key=lambda x: -len(x)), preg=preg)
    return _LEX


_TOK = re.compile(r"\d{1,3}(?:\.\d{3})+(?![\d,])|\d+(?:[.,]\d+)?|\*\*|[()+\-*/×÷^%:=−√,]|[a-zñ]+")


def _toks(t):
    t = sa(t.lower()).replace("por ciento", "%")
    return _TOK.findall(t)


def _num(tok):
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", tok):
        return Fr(tok.replace(".", ""))
    if re.fullmatch(r"\d+(?:[.,]\d+)?", tok):
        return Fr(tok.replace(",", "."))
    return None


# ------------------------------------------------------------------ análisis de la expresión
class _P:
    """Analizador descendente con la precedencia que declara cada aplicación."""

    def __init__(self, toks, ultimo=None):
        self.t, self.i, self.L, self.ult = toks, 0, lexico(), ultimo

    def ve(self, *ws):
        return tuple(self.t[self.i:self.i + len(ws)]) == ws

    def toma(self, *ws):
        if self.ve(*ws):
            self.i += len(ws)
            return True
        return False

    def fin(self):
        return self.i >= len(self.t)

    def _frase(self, tabla):
        for ws, *resto in tabla:
            if self.ve(*ws):
                self.i += len(ws)
                return resto
        return None

    def _op(self, prec):
        j = self.i
        r = self._frase(self.L["ops"])
        if r is not None and R.app(r[0]).precedencia == prec:
            return r[0]
        self.i = j
        return None

    def expr(self):
        izq = self.termino()
        while True:
            j = self.i
            op = self._op(1)
            if op is None:
                return izq
            try:
                der = self.termino()
            except _NoVale:
                self.i = j
                return izq
            if op == "suma" and izq[0] == "app" and izq[1] == "suma" and not izq[3]:
                izq = ("app", "suma", izq[2] + [der], False)
            else:
                izq = ("app", op, [izq, der], False)

    def termino(self):
        izq = self.potencia()
        while True:
            j = self.i
            op = self._op(2)
            if op is None:
                return izq
            try:
                der = self.potencia()
            except _NoVale:
                self.i = j
                return izq
            if op == "multiplicacion" and izq[0] == "app" and izq[1] == "multiplicacion" and not izq[3]:
                izq = ("app", op, izq[2] + [der], False)
            else:
                izq = ("app", op, [izq, der], False)

    def potencia(self):
        base = self.unario()
        r = self._frase(self.L["suf"])
        if r is not None:
            return ("app", r[0], [base, ("num", Fr(r[1]))], False)
        j = self.i
        op = self._op(3)
        if op is not None:
            try:
                return ("app", op, [base, self.potencia()], False)
            except _NoVale:
                self.i = j
        return base

    def lista(self):
        xs = [self.expr()]
        while self.toma(",") or self.toma("y") or self.toma("e"):
            xs.append(self.expr())
        return xs

    def _con_lista(self, nombre, xs):
        a = R.app(nombre)
        if len(xs) == 1 and xs[0][0] == "app" and xs[0][1] == nombre:
            return xs[0]
        mn, mx = a.aridad
        if len(xs) < mn or (mx is not None and len(xs) > mx):
            raise _NoVale
        return ("app", nombre, xs, True)

    def unario(self):
        if self.fin():
            raise _NoVale
        tok = self.t[self.i]
        if tok in ("-", "−", "menos"):
            self.i += 1
            return ("neg", self.unario())
        if tok == "(":
            self.i += 1
            e = self.expr()
            if not self.toma(")"):
                raise _NoVale
            return ("par", e)
        if tok in ("eso", "esto") or self.ve("ese", "resultado") or self.ve("ese", "numero") or self.ve("el", "resultado", "anterior"):
            if self.ult is None:
                raise _NoVale
            self.i += 1 if tok in ("eso", "esto") else (3 if tok == "el" else 2)
            return ("num", self.ult)
        # el N % de X
        j = self.i
        self.toma("el")
        n = _num(self.t[self.i]) if not self.fin() else None
        if n is not None and self.i + 1 < len(self.t) and self.t[self.i + 1] == "%":
            self.i += 2
            if self.toma("de") or self.toma("del"):
                return ("app", "porcentaje", [("num", n), self.potencia()], True)
            self.i = j
            raise _NoVale
        self.i = j
        # «el resultado de», «el total de»: relleno
        if self.toma("el", "resultado", "de") or self.toma("el", "resultado", "del") or self.toma("resultado", "de"):
            return self.unario()
        # prefijo de aplicación: «el doble de», «la raíz cuadrada de», «la media de»
        r = self._frase(self.L["pref"])
        if r is not None:
            a = R.app(r[0])
            if a.aridad == (1, 1) or a.nombre == "raiz":
                return ("app", a.nombre, [self.potencia()], True)
            return self._con_lista(a.nombre, self.lista())
        # sustantivo: «la suma de/entre A y B», «el producto de A por B»
        j = self.i
        self.toma("la") or self.toma("el")
        r = self._frase(self.L["sust"])
        if r is not None and (self.toma("de") or self.toma("entre") or self.toma("del")):
            nombre = r[0]
            if nombre == "suma" and self.ve("total"):
                raise _NoVale
            return self._verbal(nombre, sustantivo=True)
        self.i = j
        # verbo: «suma A y B», «sumar A y B», «multiplica A por B», «resta A a B»
        if tok in self.L["verbos"] and not tok.startswith("le"):
            self.i += 1
            self.toma("de")
            return self._verbal(self.L["verbos"][tok])
        n = _num(tok)
        if n is not None:
            self.i += 1
            return ("num", n)
        raise _NoVale

    def _verbal(self, nombre, sustantivo=False):
        if nombre == "resta":
            a = self.expr()
            if self.toma("a") or self.toma("de") or self.toma("al") or self.toma("del"):
                b = self.expr()
                return ("app", "resta", [b, a], True)          # «resta 18 a 50» = 50 − 18
            if a[0] == "app" and a[1] == "resta":
                return a
            if self.toma("y") or self.toma(",") or self.toma("menos") or self.toma("e"):
                return ("app", "resta", [a, self.expr()], True)
            raise _NoVale
        if nombre in ("division", "multiplicacion", "potencia"):
            a = self.expr() if nombre != "potencia" else self.unario()
            if a[0] == "app" and a[1] == nombre:
                return a
            sep = {"division": ("entre", "por", "y"), "multiplicacion": ("por", "y", "x"), "potencia": ("a", "y")}[nombre]
            if any(self.toma(s) for s in sep):
                b = self.expr()
                if nombre == "multiplicacion" and (self.toma("y") or self.toma(",")):
                    return ("app", nombre, [a, b, self.expr()], True)
                return ("app", nombre, [a, b], True)
            raise _NoVale
        return self._con_lista(nombre, self.lista())


def _analiza(toks, ultimo=None):
    p = _P(toks, ultimo)
    try:
        nodo = p.expr()
    except _NoVale:
        return None
    if not p.fin():
        return None
    return nodo


# ------------------------------------------------------------------ ejecución (solo las aplicaciones calculan)
def ejecuta(nodo, traza):
    k = nodo[0]
    if k == "num":
        return nodo[1]
    if k == "par":
        return ejecuta(nodo[1], traza)
    if k == "neg":
        v, t = R.ejecuta("resta", Fr(0), ejecuta(nodo[1], traza))
        traza.append(t)
        return v
    args = [ejecuta(x, traza) for x in nodo[2]]
    v, t = R.ejecuta(nodo[1], *args)
    traza.append(t)
    return v


def _tiene_app(nodo):
    return nodo[0] in ("app", "neg") or (nodo[0] == "par" and _tiene_app(nodo[1]))


F = M.formato


def escribe(nodo, padre=0):
    """Árbol -> «3 + 4 × 5» con los símbolos que declara cada aplicación."""
    k = nodo[0]
    if k == "num":
        s = F(nodo[1])
        return f"({s})" if nodo[1] < 0 and padre else s
    if k == "par":
        return "(" + escribe(nodo[1]) + ")"
    if k == "neg":
        return "−" + escribe(nodo[1], 9)
    a = R.app(nodo[1])
    xs = nodo[2]
    if a.nombre == "porcentaje":
        return f"{escribe(xs[0], 9)} % de {escribe(xs[1], 9)}"
    if a.nombre == "raiz":
        return f"√{escribe(xs[0], 9)}"
    if a.nombre == "potencia":
        return f"{escribe(xs[0], 9)}^{escribe(xs[1], 9)}"
    if a.precedencia in (1, 2) and a.simbolo and a.nombre != "diferencia":
        s = f" {a.simbolo} ".join(escribe(x, a.precedencia + (1 if i else 0)) for i, x in enumerate(xs))
        return f"({s})" if padre > a.precedencia else s
    return f"{a.nombre_humano or a.nombre}({', '.join(escribe(x) for x in xs)})"


def _lista_es(xs):
    xs = [escribe(x) for x in xs]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def frase_resultado(nodo, v):
    igual = "=" if M.es_exacto(v) else "≈"
    if nodo[0] == "app":
        a = R.app(nodo[1])
        es = "es" if M.es_exacto(v) else "es aproximadamente"
        if a.nombre == "porcentaje":
            return f"El {escribe(nodo[2][0])} % de {escribe(nodo[2][1])} {es} {F(v)}."
        if a.nombre == "raiz":
            return f"La raíz cuadrada de {escribe(nodo[2][0])} {es} {F(v)}."
        if a.nombre == "diferencia":
            return f"La diferencia entre {_lista_es(nodo[2])} {es} {F(v)}."
        if a.precedencia == 4 or a.nombre in ("media",):
            h = a.nombre_humano or a.nombre
            return f"{h[0].upper() + h[1:]} de {_lista_es(nodo[2])} {es} {F(v)}."
    return f"{escribe(nodo)} {igual} {F(v)}."


def justificacion(traza, breve=False):
    if not traza:
        return None
    usadas = list(dict.fromkeys(t["app"] for t in traza))
    nombres = [R.app(u).nombre_humano or u for u in usadas]
    nom = nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]
    pasos = "; ".join(_paso(t) for t in traza[:6])
    if breve:
        return f"La cuenta la ha hecho la aplicación de {nom.replace('la ', '').replace('el ', '')}: {pasos}."
    return (f"No lo saco de memoria: lo ha calculado la aplicación de {nom.replace('la ', '').replace('el ', '')} "
            f"({'v' + R.app(usadas[0]).version}). Pasos: {pasos}.")


def _paso(t):
    a = R.app(t["app"])
    xs = [F(x) if not isinstance(x, (list, dict, str)) else str(x) for x in t["args"]]
    if a.familia == "calendario":
        return f"{a.nombre_humano}: {', '.join(xs)} → {t['valor'] if not isinstance(t['valor'], tuple) else '%d:%02d' % t['valor']}"
    if a.precedencia in (1, 2, 3) and a.simbolo and len(xs) >= 2 and a.nombre != "diferencia":
        return f" {a.simbolo} ".join(xs) + f" = {F(t['valor'])}"
    return f"{a.nombre_humano or a.nombre} de {', '.join(xs)} = {F(t['valor'])}"


# ------------------------------------------------------------------ frases de cálculo directo
_ENTRADA = re.compile(
    r"^(?:(?:y|oye|lcm|vale|bueno|pues|entonces|a ver|venga|ahora)\s*,?\s+)*"
    r"(?:(?:me\s+)?(?:puedes|podrias|sabes|sabrias)\s+(?:decirme|decir|calcular|calcularme|hacer|hacerme)\s+(?:cuanto\s+(?:es|son|da|dan|sale|salen|suman|hace|hacen)\s+)?|"
    r"dime\s+(?:cuanto\s+(?:es|son|da|dan|sale|salen)\s+)?|calcula(?:me)?\s+|haz(?:me)?\s+(?:la\s+(?:cuenta|operacion)\s+(?:de\s+)?)?|resuelve\s+|opera\s+|"
    r"cuanto\s+(?:es|son|da|dan|sale|salen|vale|valen|hace|hacen|seria|serian|resulta|resultan|te\s+da)\s+|cuanto\s+(?=suman|sumado|restado|multiplicado|dividido)|"
    r"cual\s+es\s+|cual\s+seria\s+|que\s+(?:es|da|sale|resulta)\s+)?")
_COLA = re.compile(r"\s*(?:,?\s*(?:por favor|porfa|gracias))?\s*(?:=|igual a|es igual a)?\s*$")


def _limpia(texto):
    t = sa((texto or "").lower()).strip()
    t = re.sub(r"[¿?¡!]", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" .")
    t = re.sub(r"\bpor\s+ciento\b", "%", t)
    return a_cifras(t)


def calculo_directo(texto, ultimo=None):
    """Frase -> (nodo, valor, traza) si TODA la frase pide un cálculo; None si no."""
    t = _limpia(texto)
    m_mm = re.match(r"^(?:y )?(?:cual|que numero|que) (?:es|sera) (?:el )?(?:numero )?(mayor|menor|mas grande|mas pequeno|mas pequeño|mas alto|mas bajo),? ?(?:entre |de )?(\d+(?:,\d+)?)(?:,| o| y) (\d+(?:,\d+)?)(?:(?:,| o| y) (\d+(?:,\d+)?))?$", t)
    if m_mm:                                             # 2.16: «¿cuál es mayor, 0,5 o 0,25?» -> aplicación máximo/mínimo
        nums = [("num", Fr(x.replace(",", "."))) for x in m_mm.groups()[1:] if x]
        return ("app", "maximo" if m_mm.group(1) in ("mayor", "mas grande", "mas alto") else "minimo", nums, True)
    if not re.search(r"\d", t) and not (ultimo is not None and re.search(r"\b(?:eso|esto|resultado|numero)\b", t)):
        return None
    cuerpo = _COLA.sub("", _ENTRADA.sub("", t, count=1)).strip()
    if not cuerpo:
        return None
    nodo = _analiza(_toks(cuerpo), ultimo)
    if nodo is None or not _tiene_app(nodo):
        return None
    return nodo


_SEGUIR = re.compile(r"^(?:y\s+)?(?:ahora\s+)?(?:si\s+)?(?:le\s+|lo\s+|la\s+)?"
                     r"(suma|sumo|sumas|sumamos|sumale|sumale|anade|anado|anades|anadele|resta|resto|restas|restamos|restale|quita|quito|quitas|quitale|"
                     r"multiplica|multiplico|multiplicas|multiplicalo|divide|divido|divides|dividelo|eleva|elevo|elevas|elevalo)"
                     r"\s+(?:le\s+|lo\s+)?(?:por\s+|entre\s+|a\s+|al\s+|con\s+)?(.+)$")
_SEGUIR_PREF = re.compile(r"^(?:y\s+)?(?:ahora\s+)?(?:cual\s+es\s+|cuanto\s+es\s+)?(el doble|el triple|la mitad|la raiz cuadrada|la raiz|el cuadrado|el cubo)"
                          r"(?:\s+de\s+(?:eso|esto|ese numero|ese resultado|lo anterior))?$")
_RAIZ_V = {"sum": "suma", "ana": "suma", "res": "resta", "qui": "resta", "mul": "multiplicacion", "div": "division", "ele": "potencia"}


def calculo_seguido(texto, ultimo):
    """«¿y si le resto 50?», «¿y la mitad?» -> opera sobre el resultado anterior."""
    if ultimo is None:
        return None
    t = _limpia(texto)
    m = _SEGUIR.match(t)
    if m:
        op = _RAIZ_V[m.group(1)[:3]]
        resto = _analiza(_toks(m.group(2)), ultimo)
        if resto is None:
            return None
        return ("app", op, [("num", ultimo), resto], False)
    m = _SEGUIR_PREF.match(t)
    if m:
        k = m.group(1)
        if k in ("el cuadrado", "el cubo"):
            return ("app", "potencia", [("num", ultimo), ("num", Fr(2 if k == "el cuadrado" else 3))], False)
        nombre = {"el doble": "doble", "el triple": "triple", "la mitad": "mitad", "la raiz cuadrada": "raiz", "la raiz": "raiz"}[k]
        return ("app", nombre, [("num", ultimo)], True)
    return None


# ------------------------------------------------------------------ problemas de enunciado
_NO_UNIDAD = {"me", "te", "le", "nos", "os", "les", "se", "hay", "quedan", "queda", "tengo", "tiene", "tienes", "tenemos", "tienen", "son", "es",
              "cuestan", "cuesta", "pago", "pagas", "paga", "pagamos", "valen", "vale", "lleva", "llevan", "llevamos", "tocan", "toca", "damos", "dan",
              "da", "faltan", "falta", "sobran", "sobra", "suman", "en", "a", "de", "al", "le", "lo", "la", "los", "las", "mas", "menos", "hace", "habra",
              "habia", "tendre", "tendra", "tenia", "tenias", "ahora", "total", "juntos", "juntas"}
_MONEDA = {"euros", "euro", "dolares", "dolar", "centimos", "pesos", "libras"}
_JUNTOS = re.compile(r"\b(?:juntos|juntas|en total|entre (?:los|las) (?:2|dos)|ambos|ambas|todo junto|todos juntos|en conjunto|entre todos)\b")
_REPARTO = re.compile(r"\b(?:repart\w*|a cada uno|a cada una|cada uno|cada una|por cabeza|por persona|a cada)\b")


def _partes(t):
    """Enunciado y pregunta: «tengo 12 caramelos y me dan 5 más, ¿cuántos tengo?»."""
    i = t.find("¿")
    if i > 0:
        return t[:i].strip(" ,"), t[i:]
    m = re.search(r",\s*(?=(?:y\s+)?(?:cuant|a que hora|que dia|quien))", t)
    if m:
        return t[:m.start()].strip(" ,"), t[m.end():]
    return None, None


def _unidad_pregunta(q):
    m = re.search(r"\bcuant[oa]s?\s+([a-zñ]+)", q)
    if m and m.group(1) not in _NO_UNIDAD and not m.group(1).endswith(("ra", "re")):
        return m.group(1)
    return None


def _numeros(s):
    return [(Fr(m.group(1).replace(",", ".")), m.start(), m.end(), (m.group(2) or "")) for m in re.finditer(r"(\d+(?:,\d+)?)(?:\s+([a-zñ]+))?", s)]


def _signo(ventana, despues):
    L = lexico()
    w = " " + ventana + " "
    for x in [x for x in L["mas"] if " " in x]:
        if f" {x} " in w:
            return "suma"
    for x in L["menos"]:
        if f" {x} " in w:
            return "resta"
    for x in L["mas"]:
        if f" {x} " in w:
            return "suma"
    if despues in ("mas",):
        return "suma"
    if despues in ("menos",):
        return "resta"
    return None


def problema(texto):
    """Problema de enunciado -> (nodo, unidad) o None. Solo se entienden las situaciones; las cuentas las hacen las aplicaciones."""
    t0 = sa((texto or "").lower())
    if "?" not in t0:
        return None
    t = a_cifras(re.sub(r"\s+", " ", t0.replace("¡", "").replace("!", "")).strip())
    s, q = _partes(t)
    if not s or not q or "cuant" not in q:
        return None
    s = re.sub(r"^si\s+", "", s)
    q = q.strip("¿? .")
    ns = _numeros(s)
    if _JUNTOS.search(q):
        q = re.sub(r"\b(?:los|las|entre)\s+\d+\b", " ", q)
    nq = _numeros(q)
    if not ns:
        return None
    uq = _unidad_pregunta(q)
    # «dentro de N años» / «hace N años»
    m = re.search(r"\b(dentro de|hace)\s+(\d+)\s+(a[nñ]os|dias|meses|semanas|horas)\b", q)
    if m and len(ns) == 1:
        op = "suma" if m.group(1) == "dentro de" else "resta"
        return ("app", op, [("num", ns[0][0]), ("num", Fr(m.group(2)))], False), ns[0][3] or m.group(3)
    # «N X de M Y»: 6 filas de 8 huevos, 3 libros de 12 euros
    m = re.search(r"(\d+)\s+([a-zñ]+)\s+de\s+(\d+)(?:\s+([a-zñ]+))?", s)
    if m and len(ns) == 2:
        return ("app", "multiplicacion", [("num", Fr(m.group(1))), ("num", Fr(m.group(3)))], False), uq or m.group(4) or m.group(2)
    # precio de la unidad: «una camiseta cuesta 15 euros, ¿cuánto cuestan 4 camisetas?»
    m = re.search(r"\b(?:un|una|1|el|la)\s+([a-zñ]+(?:\s+de\s+[a-zñ]+)?)\s+(?:cuesta|vale|pesa|mide|tarda|dura)\s+(\d+(?:,\d+)?)(?:\s+([a-zñ]+))?", s)
    if m and len(ns) == 1 and len(nq) == 1 and not _JUNTOS.search(q):
        return ("app", "multiplicacion", [("num", nq[0][0]), ("num", Fr(m.group(2).replace(",", ".")))], False), m.group(3) or uq
    if nq:
        return None
    if len(ns) < 2:
        return None
    unidad = uq if uq and uq != "dinero" else (next((n[3] for n in ns if n[3] in _MONEDA), None) or ns[0][3] or uq)
    # reparto: «repartimos 45 cromos entre 5 niños», «60 caramelos para 4 niños, ¿cuántos a cada uno?»
    if len(ns) == 2 and (_REPARTO.search(s) or _REPARTO.search(q) or re.search(r"\ba medias\b|\bentre todos\b|\ba partes iguales\b", s + " " + q)):
        a_, b_ = ns[0], ns[1]
        if (a_[0] < b_[0] and (b_[3] in _MONEDA or not a_[3] or re.match(r"^(?:somos|eramos|son)\b", s))):
            a_, b_ = b_, a_                              # 2.16: «somos 4 y pagamos 60 euros a medias»: se reparte lo que se paga, entre los que son
        return ("app", "division", [("num", a_[0]), ("num", b_[0])], False), (a_[3] if not uq or uq in ("paga", "pagamos", "toca") else uq)
    # cadena de sumas y restas según los verbos del enunciado
    nodo = ("num", ns[0][0])
    desconocido = False
    for k in range(1, len(ns)):
        ventana = s[ns[k - 1][2]:ns[k][1]]
        despues = ns[k][3]
        op = _signo(ventana, despues)
        if op is None:
            desconocido = True
            op = "suma"
        nodo = ("app", op, [nodo, ("num", ns[k][0])], False)
    if desconocido:
        # sin verbo que diga si se suma o se resta, solo se suma cuando la pregunta pide el total
        nombres = {n[3] for n in ns}
        total = _JUNTOS.search(q) or (re.search(r"\b(?:hay|somos|son|cuestan|valen|pago|pagas|paga|pagamos)\b", q) and (uq is None or uq not in nombres))
        if not total:
            return None
    return nodo, (unidad if unidad not in _NO_UNIDAD else None)


# ------------------------------------------------------------------ calendario y reloj en suposiciones
_DIAS = "lunes|martes|miercoles|jueves|viernes|sabado|domingo"
_REL = {"manana": 1, "pasado manana": 2, "ayer": -1, "anteayer": -2, "antes de ayer": -2, "hoy": 0}


def calendario(texto):
    t = sa((texto or "").lower()).replace("ñ", "n")
    m = re.search(rf"\b(?:si\s+)?hoy\s+(?:es|fuera|fuese)\s+({_DIAS})\b", t)
    if m and "?" in t:
        q = t[m.end():] + " " + t[:m.start()]            # 2.16: la suposición puede ir detrás («¿qué día será mañana si hoy es sábado?»)
        r = re.search(r"\bque dia\s+(?:sera|es|fue|era|seria|sera)\s+(pasado manana|manana|antes de ayer|anteayer|ayer)\b", q)
        r2 = re.search(r"\bque dia\s+(?:sera|es|seria)\s+dentro de\s+(\d+|[a-z]+)\s+dias?\b", a_cifras(q))
        r3 = re.search(r"\bque dia\s+(?:fue|era)\s+hace\s+(\d+|[a-z]+)\s+dias?\b", a_cifras(q))
        if r:
            n = _REL[r.group(1)]
            pal = r.group(1).replace("manana", "mañana")
        elif r2 and r2.group(1).isdigit():
            n, pal = int(r2.group(1)), f"dentro de {r2.group(1)} días"
        elif r3 and r3.group(1).isdigit():
            n, pal = -int(r3.group(1)), f"hace {r3.group(1)} días"
        else:
            return None
        v, tr = R.ejecuta("dia_semana", m.group(1), n)
        verbo = "será" if n > 0 else ("fue" if n < 0 else "es")
        return f"{pal[0].upper() + pal[1:]} {verbo} {v}.", [tr]
    t2 = a_cifras(t)
    m = re.search(r"\b(?:sale|empieza|comienza|salgo|salimos|empiezo|parte|arranca)\s+a\s+las\s+(\d{1,2})(?:[:.](\d{2})|\s+y\s+(media|cuarto))?\b", t2)
    d = re.search(r"\b(?:tarda|dura|tardo|tardamos|tardara|durara|son)\s+(\d+)\s+horas?(?:\s+y\s+(\d+)\s+minutos?|\s+y\s+media)?", t2)
    if m and d and re.search(r"\ba que hora\b", t2):
        h = int(m.group(1)); mi = int(m.group(2) or 0) + (30 if m.group(3) == "media" else 15 if m.group(3) == "cuarto" else 0)
        dm = int(d.group(2) or 0) + (30 if "y media" in d.group(0) else 0)
        v, tr = R.ejecuta("hora_mas", h, mi, int(d.group(1)), dm)
        verbo = re.search(r"\ba que hora\s+([a-z]+)", t2)
        vb = verbo.group(1) if verbo else "llega"
        return f"{vb.capitalize()} a las {v[0]}:{v[1]:02d}.", [tr]
    return None
