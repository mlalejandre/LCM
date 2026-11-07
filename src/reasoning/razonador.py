"""parche-112: RAZONADOR GENERAL del LCM. Un motor de inferencia que no sabe nada de ningun area: el conocimiento (hechos, reglas y propiedades de las relaciones)
llega como DATOS (memoria, lecciones, cartuchos `razon_*`), asi que el mismo motor sirve para parentesco, geografia, biologia, organizaciones, tiempo, fisica...

Que hace
  - preguntar(s, p, o)  -> SI / NO / DESCONOCIDO / CONFLICTO, siempre con una PRUEBA (arbol de pasos) o con el motivo de no poder decidir.
  - consultar(s, p, o)  -> todas las soluciones cuando falta un termino ("quien es abuelo de Pedro", "cuantos hermanos tiene Ana").
  - extremo(atributo, clase) -> "cual es el mas alto" (con los valores comparados); ruta(a, b, relacion) -> camino minimo.
  - explicar(prueba)    -> la prueba en castellano, paso a paso.
  - Verificador         -> comprueba una prueba con codigo INDEPENDIENTE del motor (la validez de la prueba es una metrica, no un acto de fe).

Como razona
  - Hechos (s, p, o) en mayusculas y hechos negados. Reglas de Horn: si [premisas] entonces conclusion, con variables ?X. Premisas especiales: "@DISTINTO", "@MAYOR",
    "@MENOR", "@IGUAL" (numericas) y "!P" (negacion por fallo: no se puede probar).
  - Propiedades de relacion (datos): transitiva, simetrica, inversa, subprop (A es un caso de B), funcional / funcional_inv (solo uno), heredable (de la clase al miembro,
    con EXCEPCIONES: lo mas especifico gana), compara (A p B si atributo(A) op atributo(B)), mundo_cerrado (lo no sabido es falso), disjunta (clases incompatibles).
  - Busqueda hacia atras con presupuesto, control de ciclos y memoria de lo ya resuelto; las relaciones transitivas se resuelven como camino en un grafo (lineal, no exponencial).
  - Mundo ABIERTO por defecto: solo dice NO si hay evidencia (negado explicito, unicidad, clases incompatibles, excepcion, mundo cerrado); si no, DESCONOCIDO. Nunca inventa certezas."""
from __future__ import annotations

import itertools
import re
import time
from collections import defaultdict, deque
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

Atomo = Tuple[str, str, str]
PRESUPUESTO = 40000
PROFUNDIDAD = 14


def N(x) -> str:
    return str(x).strip().upper()


def es_var(t) -> bool:
    return isinstance(t, str) and t.startswith("?")


def _num(x):
    try:
        return float(str(x).replace(",", "."))
    except ValueError:
        return None


class Agotado(Exception):
    """Se acabo el presupuesto de pasos: el motor se rinde (DESCONOCIDO) en vez de colgarse."""


class Prueba:
    """Nodo de una prueba: `atomo` se sigue de `hijos` por la razon `regla` (hecho, inversa, simetrica, subprop, transitiva, regla:ID, herencia, neg, funcional, ...)."""
    __slots__ = ("atomo", "regla", "hijos", "nota")

    def __init__(self, atomo, regla, hijos=(), nota=""):
        self.atomo, self.regla, self.hijos, self.nota = tuple(atomo), regla, list(hijos), nota

    def tam(self) -> int:
        return 1 + sum(h.tam() for h in self.hijos)

    def prof(self) -> int:
        return 1 + max((h.prof() for h in self.hijos), default=0)

    def hojas(self) -> List[Atomo]:
        if not self.hijos:
            return [self.atomo] if self.regla == "hecho" else []
        return [x for h in self.hijos for x in h.hojas()]

    def a_dict(self) -> dict:
        return {"atomo": list(self.atomo), "regla": self.regla, "nota": self.nota, "hijos": [h.a_dict() for h in self.hijos]}

    @staticmethod
    def de_dict(d) -> "Prueba":
        return Prueba(d["atomo"], d["regla"], [Prueba.de_dict(h) for h in d.get("hijos", [])], d.get("nota", ""))


class Resultado:
    __slots__ = ("valor", "prueba", "motivo", "pasos", "ms", "contra")

    def __init__(self, valor, prueba=None, motivo="", pasos=0, ms=0.0, contra=None):
        self.valor, self.prueba, self.motivo, self.pasos, self.ms, self.contra = valor, prueba, motivo, pasos, ms, contra

    def __repr__(self):
        return f"Resultado({self.valor}, pasos={self.pasos})"


class Regla:
    __slots__ = ("id", "premisas", "conclusion", "origen")

    def __init__(self, id_, premisas, conclusion, origen=""):
        self.id = str(id_)
        self.premisas = [tuple(N(x) if i != 1 else N(x) for i, x in enumerate(p)) for p in premisas]
        self.conclusion = tuple(N(x) for x in conclusion)
        self.origen = origen

    @staticmethod
    def de_dict(d, id_=None) -> "Regla":
        prem = d.get("si", d.get("premises", d.get("premisas", [])))
        concl = d.get("entonces", d.get("conclusion"))
        return Regla(d.get("id", id_), prem, concl, d.get("cart", d.get("origen", "")))

    @staticmethod
    def de_leccion(l, id_) -> "Regla":
        """Leccion ensenada (premisas/conclusion ya con variables ?X): igual que el motor antiguo, variables distintas = entidades distintas."""
        from src.reasoning.lessons import generalize
        prem, concl = generalize(l)
        vs = []
        for p in prem:
            for t in (p[0], p[2]):
                if es_var(t) and t not in vs:
                    vs.append(t)
        prem = list(prem) + [(a, "@DISTINTO", b) for a, b in itertools.combinations(vs, 2)]
        return Regla(id_, prem, concl, "leccion")

    def a_dict(self) -> dict:
        return {"id": self.id, "si": [list(p) for p in self.premisas], "entonces": list(self.conclusion)}

    def renombrar(self, k) -> "Regla":
        def r(t):
            return f"{t}#{k}" if es_var(t) else t
        return Regla(self.id, [(r(a), p, r(o)) for a, p, o in self.premisas], (r(self.conclusion[0]), self.conclusion[1], r(self.conclusion[2])), self.origen)


def _subs(t, b):
    return b.get(t, t) if es_var(t) else t


# ====================================================================================================================================================================
class Razonador:
    def __init__(self, hechos: Iterable[Sequence[str]] = (), reglas: Iterable = (), props: Optional[dict] = None, negados: Iterable[Sequence[str]] = (),
                 presupuesto: int = PRESUPUESTO, profundidad: int = PROFUNDIDAD, norm=None):
        self.norm = norm or N
        self.presupuesto, self.profundidad = presupuesto, profundidad
        self.hechos = set()
        self.neg = set()
        self.por_p = defaultdict(set)                  # p -> {(s, o)}
        self.por_ps = defaultdict(set)                 # (p, s) -> {o}
        self.por_po = defaultdict(set)                 # (p, o) -> {s}
        for f in hechos:
            self.agregar(f)
        for f in negados:
            self.neg.add(tuple(N(x) for x in f))
        self.props: Dict[str, dict] = {N(k): dict(v) for k, v in (props or {}).items()}
        self.reglas: List[Regla] = []
        for i, r in enumerate(reglas):
            self.reglas.append(r if isinstance(r, Regla) else Regla.de_dict(r, f"R{i}"))
        self._compilar()
        self._n = 0
        self._llamadas = 0
        self._cortes = 0
        self._cache: Dict[tuple, list] = {}

    # ---- datos ---------------------------------------------------------------------------------------------------------------------------------------------
    def agregar(self, f):
        s, p, o = (N(x) for x in f)
        if (s, p, o) not in self.hechos:
            self.hechos.add((s, p, o))
            self.por_p[p].add((s, o))
            self.por_ps[(p, s)].add(o)
            self.por_po[(p, o)].add(s)

    def _compilar(self):
        self.inv: Dict[str, str] = {}
        self.hijos_de: Dict[str, List[str]] = defaultdict(list)
        self.disj: Dict[str, set] = defaultdict(set)
        for p, d in self.props.items():
            if d.get("inversa"):
                q = N(d["inversa"])
                self.inv[p] = q
                self.inv.setdefault(q, p)
            for sup in ([d["subprop"]] if isinstance(d.get("subprop"), str) else d.get("subprop", [])):
                self.hijos_de[N(sup)].append(p)
        for s, o in self.por_p.get("DISJUNTA_CON", ()):
            self.disj[s].add(o)
            self.disj[o].add(s)
        self.reglas_por = defaultdict(list)
        for r in self.reglas:
            self.reglas_por[r.conclusion[1]].append(r)
        self._cache = {}

    def prop(self, p, clave):
        return self.props.get(p, {}).get(clave)

    def _herencia_de(self, p) -> bool:
        d = self.props.get(p, {})
        if "heredable" in d:
            return bool(d["heredable"])
        return bool(self.props.get("*", {}).get("heredable")) and p != "ES" and not p.startswith(("@", "!")) and p != "DISJUNTA_CON"

    # ---- aristas de una relacion (hechos + inversa + simetrica + subpropiedades) ----------------------------------------------------------------------------
    def _aristas(self, p, nodo, adelante=True, visto=None) -> Iterator[Tuple[str, Prueba]]:
        visto = visto or frozenset()
        if p in visto:
            return
        visto = visto | {p}
        if adelante:
            for o in sorted(self.por_ps.get((p, nodo), ())):
                yield o, Prueba((nodo, p, o), "hecho")
        else:
            for s in sorted(self.por_po.get((p, nodo), ())):
                yield s, Prueba((s, p, nodo), "hecho")
        if self.prop(p, "simetrica"):
            if adelante:
                for s in sorted(self.por_po.get((p, nodo), ())):
                    yield s, Prueba((nodo, p, s), "simetrica", [Prueba((s, p, nodo), "hecho")])
            else:
                for o in sorted(self.por_ps.get((p, nodo), ())):
                    yield o, Prueba((o, p, nodo), "simetrica", [Prueba((nodo, p, o), "hecho")])
        q = self.inv.get(p)
        if q and q != p:
            if adelante:
                for s in sorted(self.por_po.get((q, nodo), ())):
                    yield s, Prueba((nodo, p, s), "inversa", [Prueba((s, q, nodo), "hecho")])
            else:
                for o in sorted(self.por_ps.get((q, nodo), ())):
                    yield o, Prueba((o, p, nodo), "inversa", [Prueba((nodo, q, o), "hecho")])
        for h in self.hijos_de.get(p, ()):
            for otro, pr in self._aristas(h, nodo, adelante, visto):
                a = (nodo, p, otro) if adelante else (otro, p, nodo)
                yield otro, Prueba(a, "subprop", [pr])

    def _aristas_todas(self, p, nodo, adelante, prof, camino):
        """aristas directas + las que fabrican las reglas de p (para cerrar transitivamente sobre relaciones derivadas)."""
        yield from self._aristas(p, nodo, adelante)
        if self.reglas_por.get(p) and prof > 1:
            for s1, o1, pr in self._por_reglas(p, nodo if adelante else None, None if adelante else nodo, prof - 1, camino):
                yield (o1 if adelante else s1), pr

    # ---- camino en grafo (relaciones transitivas y ruta minima) --------------------------------------------------------------------------------------------
    def _alcance(self, p, origen, destino, adelante, prof, camino, maximo=4000):
        """BFS: {nodo: (previo, paso_prueba)}; si destino esta, se detiene en cuanto lo alcanza (camino minimo)."""
        padre = {origen: None}
        cola = deque([origen])
        while cola and len(padre) < maximo:
            n = cola.popleft()
            for m, pr in self._aristas_todas(p, n, adelante, prof, camino):
                if m not in padre:
                    padre[m] = (n, pr)
                    if m == destino:
                        return padre
                    cola.append(m)
        return padre

    def _cadena(self, padre, origen, fin, adelante, p):
        pasos, x = [], fin
        while padre[x] is not None:
            prev, pr = padre[x]
            pasos.append(pr)
            x = prev
        pasos.reverse() if adelante else None
        a = (origen, p, fin) if adelante else (fin, p, origen)
        if len(pasos) == 1:
            return pasos[0]
        return Prueba(a, "transitiva", pasos)

    # ---- resolucion hacia atras -----------------------------------------------------------------------------------------------------------------------------
    def _sol(self, p, s, o, prof, camino) -> List[Tuple[str, str, Prueba]]:
        """Todas las (s, o, prueba) con p(s, o); s/o None = hueco. Resultado sin duplicados."""
        clave = (p, s, o)
        if clave in self._cache:
            return self._cache[clave]
        if clave in camino or prof <= 0:
            self._cortes += 1
            return []
        self._llamadas += 1
        if self._llamadas > self.presupuesto:
            raise Agotado()
        c0 = self._cortes
        camino = camino | {clave}
        vistos: Dict[Tuple[str, str], Prueba] = {}

        def poner(a, b, pr):
            if (a, b) not in vistos:
                vistos[(a, b)] = pr

        if p.startswith("@"):
            return self._builtin(p, s, o)
        if p.startswith("!"):
            return []
        # 1. hechos y relaciones derivadas de forma directa
        if s is not None:
            for m, pr in self._aristas(p, s, True):
                if o is None or m == o:
                    poner(s, m, pr)
        elif o is not None:
            for m, pr in self._aristas(p, o, False):
                poner(m, o, pr)
        else:
            for a, b in sorted(self.por_p.get(p, ())):
                poner(a, b, Prueba((a, p, b), "hecho"))
            for h in self.hijos_de.get(p, ()):
                for a, b, pr in self._sol(h, None, None, prof - 1, camino):
                    poner(a, b, Prueba((a, p, b), "subprop", [pr]))
            if self.prop(p, "simetrica"):
                for a, b in sorted(self.por_p.get(p, ())):
                    poner(b, a, Prueba((b, p, a), "simetrica", [Prueba((a, p, b), "hecho")]))
            q = self.inv.get(p)
            if q and q != p:
                for a, b in sorted(self.por_p.get(q, ())):
                    poner(b, a, Prueba((b, p, a), "inversa", [Prueba((a, q, b), "hecho")]))
        # 2. transitividad (camino en el grafo)
        if self.prop(p, "transitiva"):
            if s is not None:
                padre = self._alcance(p, s, o, True, prof, camino)
                for m in padre:
                    if m != s and (o is None or m == o):
                        poner(s, m, self._cadena(padre, s, m, True, p))
            elif o is not None:
                padre = self._alcance(p, o, None, False, prof, camino)
                for m in padre:
                    if m != o:
                        poner(m, o, self._cadena(padre, o, m, False, p))
            else:
                nodos = sorted({a for a, _ in self.por_p.get(p, ())} | {b for _, b in self.por_p.get(p, ())})
                for n0 in nodos[:400]:
                    padre = self._alcance(p, n0, None, True, prof, camino, 600)
                    for m in padre:
                        if m != n0:
                            poner(n0, m, self._cadena(padre, n0, m, True, p))
        # 3. comparacion por atributo
        cmp_ = self.prop(p, "compara")
        if cmp_:
            for a, b, pr in self._comparar(p, cmp_, s, o):
                poner(a, b, pr)
        # 4. herencia con excepciones
        if self._herencia_de(p):
            for a, b, pr in self._heredar(p, s, o, prof, camino):
                poner(a, b, pr)
        # 5. reglas
        if self.reglas_por.get(p):
            for a, b, pr in self._por_reglas(p, s, o, prof, camino):
                poner(a, b, pr)
        res = [(a, b, pr) for (a, b), pr in vistos.items()]
        if self._cortes == c0:
            self._cache[clave] = res
        return res

    def _por_reglas(self, p, s, o, prof, camino):
        for regla in self.reglas_por.get(p, ()):
            self._n += 1
            r = regla.renombrar(self._n)
            b: Dict[str, str] = {}
            ok = True
            for term, val in ((r.conclusion[0], s), (r.conclusion[2], o)):
                if val is None:
                    continue
                if es_var(term):
                    if b.get(term, val) != val:
                        ok = False
                    b[term] = val
                elif term != val:
                    ok = False
            if not ok:
                continue
            for b2, pruebas in self._premisas(r.premisas, b, prof - 1, camino):
                a, c = _subs(r.conclusion[0], b2), _subs(r.conclusion[2], b2)
                if es_var(a) or es_var(c):
                    continue
                yield a, c, Prueba((a, p, c), "regla:" + r.id, pruebas)

    def _premisas(self, prem, bind, prof, camino):
        n = len(prem)
        orden = list(range(n))

        def rec(pend, bd, acc):
            if not pend:
                yield bd, [acc[i] for i in range(n)]
                return
            # elegir la premisa mas acotada (mas terminos conocidos), dejando para el final las especiales sin cerrar
            mejor, mejor_k = None, -1
            for i in pend:
                a, p, o = prem[i]
                sa, so = _subs(a, bd), _subs(o, bd)
                esp = p.startswith(("@", "!"))
                cerrado = not es_var(sa) and not es_var(so)
                if esp and not cerrado:
                    continue
                k = (not es_var(sa)) + (not es_var(so)) + (3 if cerrado else 0) + (1 if esp else 0)
                if k > mejor_k:
                    mejor, mejor_k = i, k
            if mejor is None:
                return
            a, p, o = prem[mejor]
            sa, so = _subs(a, bd), _subs(o, bd)
            resto = [i for i in pend if i != mejor]
            if p.startswith("!"):
                if not self._sol(p[1:], sa, so, prof, camino) and not self._refutable(p[1:], sa, so):
                    yield from rec(resto, bd, {**acc, mejor: Prueba((sa, p, so), "naf", [], "no se puede probar")})
                return
            for x, y, pr in self._sol(p, None if es_var(sa) else sa, None if es_var(so) else so, prof, camino):
                b2 = dict(bd)
                if es_var(sa):
                    b2[sa] = x
                if es_var(so):
                    if b2.get(so, y) != y:
                        continue
                    b2[so] = y
                if es_var(sa) and es_var(so) and sa == so and x != y:
                    continue
                yield from rec(resto, b2, {**acc, mejor: pr})

        yield from rec(orden, dict(bind), {})

    def _refutable(self, p, s, o) -> bool:
        return (s, p, o) in self.neg

    def _builtin(self, p, s, o):
        if s is None or o is None:
            return []
        a, b = _num(s), _num(o)
        ok = False
        if p == "@DISTINTO":
            ok = s != o
        elif a is not None and b is not None:
            ok = {"@MAYOR": a > b, "@MENOR": a < b, "@IGUAL": a == b, "@MAYOR_IGUAL": a >= b, "@MENOR_IGUAL": a <= b}.get(p, False)
        elif p == "@IGUAL":
            ok = s == o
        return [(s, o, Prueba((s, p, o), "calculo"))] if ok else []

    # ---- comparaciones por atributo ---------------------------------------------------------------------------------------------------------------------------
    def _valor(self, e, atributo):
        for v in sorted(self.por_ps.get((atributo, e), ())):
            x = _num(v)
            if x is not None:
                return x, Prueba((e, atributo, v), "hecho")
        return None, None

    def _comparar(self, p, cfg, s, o):
        attr, op = N(cfg["atributo"]), cfg.get("op", ">")
        cands_s = [s] if s else sorted({a for a, _ in self.por_p.get(attr, ())})
        cands_o = [o] if o else sorted({a for a, _ in self.por_p.get(attr, ())})
        if (s is None and o is None):
            return []
        for a in cands_s:
            va, pa = self._valor(a, attr)
            if va is None:
                continue
            for b in cands_o:
                if a == b:
                    continue
                vb, pb = self._valor(b, attr)
                if vb is None:
                    continue
                if (va > vb) if op == ">" else (va < vb):
                    yield a, b, Prueba((a, p, b), "comparacion", [pa, pb], f"{attr.lower()}: {va:g} {op} {vb:g}")

    # ---- herencia con excepciones -----------------------------------------------------------------------------------------------------------------------------
    def _antecesores(self, s):
        """[(clase, distancia, prueba de 's ES clase')] por BFS sobre ES (incluye las subpropiedades e inversas declaradas)."""
        padre = self._alcance("ES", s, None, True, 8, frozenset(), 600)
        niv = {s: 0}
        out = []
        for n in padre:
            if n == s:
                continue
            d, x = 0, n
            while padre[x] is not None:
                d += 1
                x = padre[x][0]
            out.append((n, d, self._cadena(padre, s, n, True, "ES")))
        out.sort(key=lambda t: (t[1], t[0]))
        return out

    def _heredar(self, p, s, o, prof, camino):
        if s is None:
            return
        ants = self._antecesores(s)
        niveles = [(s, 0, None)] + ants
        resueltos: Dict[str, int] = {}                 # objeto -> distancia a la que hay decision (para que lo mas cercano gane)
        decisiones = {}
        for cls, d, pr in niveles:
            objetos = {x for x in self.por_ps.get((p, cls), ())} | {x for (a, pp, x) in self.neg if a == cls and pp == p}
            for x in sorted(objetos):
                if o is not None and x != o:
                    continue
                if x in resueltos and resueltos[x] < d:
                    continue
                pos = x in self.por_ps.get((p, cls), ())
                neg = (cls, p, x) in self.neg
                if x in resueltos and resueltos[x] == d:
                    continue
                resueltos[x] = d
                if pos and neg:
                    decisiones[x] = ("CONFLICTO", cls, d, pr)
                elif pos:
                    decisiones[x] = ("SI", cls, d, pr)
                elif neg:
                    decisiones[x] = ("NO", cls, d, pr)
        for x, (v, cls, d, pr) in decisiones.items():
            if v == "SI" and d > 0:
                base = Prueba((cls, p, x), "hecho")
                yield s, x, Prueba((s, p, x), "herencia", [base, pr], f"{s.lower()} hereda de {cls.lower()}")

    def _herencia_no(self, s, p, o):
        """Prueba de NO si el rasgo esta negado en la clase mas cercana que decide (excepcion o negacion heredada)."""
        ants = self._antecesores(s)
        for cls, d, pr in [(s, 0, None)] + ants:
            pos = o in self.por_ps.get((p, cls), ())
            neg = (cls, p, o) in self.neg
            if pos and neg:
                return None
            if pos:
                return None
            if neg:
                base = Prueba((cls, p, o), "neg")
                if d == 0:
                    return base
                return Prueba((s, p, o), "herencia_neg", [base, pr], f"{cls.lower()} lo niega y es la clase mas cercana")
        return None

    # ---- API: preguntar ---------------------------------------------------------------------------------------------------------------------------------------
    def preguntar(self, s, p, o) -> Resultado:
        t0 = time.perf_counter()
        s, p, o = self.norm(s), N(p), self.norm(o)
        self._llamadas, self._cortes, self._cache = 0, 0, {}
        try:
            pos = self._sol(p, s, o, self.profundidad, frozenset())
            neg = self._refutar(p, s, o)
            if pos and neg:
                return Resultado("CONFLICTO", pos[0][2], "se puede probar y refutar a la vez", self._llamadas, (time.perf_counter() - t0) * 1000, neg)
            if pos:
                return Resultado("SI", pos[0][2], "", self._llamadas, (time.perf_counter() - t0) * 1000)
            if neg:
                return Resultado("NO", neg, "", self._llamadas, (time.perf_counter() - t0) * 1000)
            if self.prop(p, "mundo_cerrado"):
                return Resultado("NO", Prueba((s, p, o), "mundo_cerrado", [], f"no consta y {p.lower()} es de mundo cerrado"), "", self._llamadas, (time.perf_counter() - t0) * 1000)
            return Resultado("DESCONOCIDO", None, "no puedo demostrarlo ni refutarlo con lo que sé", self._llamadas, (time.perf_counter() - t0) * 1000)
        except Agotado:
            return Resultado("DESCONOCIDO", None, "agoté el presupuesto de pasos", self._llamadas, (time.perf_counter() - t0) * 1000)

    def _refutar(self, p, s, o) -> Optional[Prueba]:
        if (s, p, o) in self.neg:
            return Prueba((s, p, o), "neg", [], "me dijeron que no")
        q = self.inv.get(p)
        if q and (o, q, s) in self.neg:
            return Prueba((s, p, o), "inversa", [Prueba((o, q, s), "neg")])
        if self.prop(p, "simetrica") and (o, p, s) in self.neg:
            return Prueba((s, p, o), "simetrica", [Prueba((o, p, s), "neg")])
        if self._herencia_de(p):
            h = self._herencia_no(s, p, o)
            if h is not None:
                return h
        if self.prop(p, "asimetrica") and s != o:
            rev = self._sol(p, o, s, self.profundidad, frozenset())
            if rev:
                return Prueba((s, p, o), "asimetrica", [rev[0][2]], f"ya se cumple al revés, y {p.lower()} no puede darse en los dos sentidos")
        cfg = self.prop(p, "compara")
        if cfg and s != o:
            attr = N(cfg["atributo"])
            va, pa = self._valor(s, attr)
            vb, pb = self._valor(o, attr)
            if va is not None and vb is not None and not ((va > vb) if cfg.get("op", ">") == ">" else (va < vb)):
                return Prueba((s, p, o), "comparacion_no", [pa, pb], f"{attr.lower()}: {va:g} frente a {vb:g}")
        if self.prop(p, "funcional"):
            for x, _, pr in self._sol(p, s, None, self.profundidad, frozenset()):
                if x != o:
                    return Prueba((s, p, o), "funcional", [pr], f"{p.lower()} solo puede ser uno y ya es {x.lower()}")
        if self.prop(p, "funcional_inv"):
            for x, _, pr in self._sol(p, None, o, self.profundidad, frozenset()):
                if x != s:
                    return Prueba((s, p, o), "funcional_inv", [pr], f"solo uno puede serlo y ya es {x.lower()}")
        if p == "ES" and self.disj:
            ants_s = [(s, 0, None)] + self._antecesores(s)
            ants_o = [(o, 0, None)] + self._antecesores(o)
            for a, _, pa in ants_s:
                for b, _, pb in ants_o:
                    if b in self.disj.get(a, ()):
                        hijos = [Prueba((a, "DISJUNTA_CON", b), "hecho")] if (a, b) in self.por_p.get("DISJUNTA_CON", set()) else \
                                [Prueba((b, "DISJUNTA_CON", a), "hecho")]
                        sa = [pa] if pa else []
                        sb = [pb] if pb else []
                        return Prueba((s, p, o), "disjunta", sa + sb + hijos, f"{a.lower()} y {b.lower()} son incompatibles")
        return None

    # ---- API: consultar / contar / extremo / ruta -------------------------------------------------------------------------------------------------------------------
    def consultar(self, s, p, o, maximo=200) -> List[dict]:
        """Soluciones para los huecos (None). -> [{"s", "o", "prueba"}] ordenadas."""
        s = self.norm(s) if s is not None else None
        o = self.norm(o) if o is not None else None
        p = N(p)
        self._llamadas, self._cortes, self._cache = 0, 0, {}
        try:
            res = self._sol(p, s, o, self.profundidad, frozenset())
        except Agotado:
            res = []
        res.sort(key=lambda t: (t[0], t[1]))
        return [{"s": a, "o": b, "prueba": pr} for a, b, pr in res[:maximo]]

    def contar(self, s, p, o) -> int:
        return len(self.consultar(s, p, o, 10 ** 6))

    def extremo(self, atributo, clase=None, modo="max") -> Optional[dict]:
        attr = N(atributo)
        cands = []
        for e in sorted({a for a, _ in self.por_p.get(attr, ())}):
            v, pr = self._valor(e, attr)
            if v is None:
                continue
            if clase:
                r = self.preguntar(e, "ES", clase)
                if r.valor != "SI":
                    continue
                cands.append((e, v, pr, r.prueba))
            else:
                cands.append((e, v, pr, None))
        if not cands:
            return None
        mejor = max(cands, key=lambda c: c[1]) if modo == "max" else min(cands, key=lambda c: c[1])
        if len([c for c in cands if c[1] == mejor[1]]) > 1:
            return {"empate": [c[0] for c in cands if c[1] == mejor[1]], "valor": mejor[1], "prueba": None}
        hijos = []
        for e, v, pr, pm in cands:
            hijos.append(pr)
        raiz = Prueba((mejor[0], "EXTREMO_" + modo.upper(), attr), "extremo", hijos + [c[3] for c in cands if c[3]], f"{modo}:{clase or '*'}")
        return {"entidad": mejor[0], "valor": mejor[1], "candidatos": [(c[0], c[1]) for c in cands], "prueba": raiz}

    def ruta(self, a, b, p) -> Optional[Prueba]:
        """Camino de longitud minima de a a b siguiendo la relacion p (con sus inversas/simetrias/subpropiedades)."""
        a, b, p = self.norm(a), self.norm(b), N(p)
        self._llamadas, self._cortes, self._cache = 0, 0, {}
        padre = self._alcance(p, a, b, True, self.profundidad, frozenset(), 20000)
        if b not in padre or a == b:
            return None
        pr = self._cadena(padre, a, b, True, p)
        if pr.regla == "transitiva":
            pr.nota = "ruta"
        return pr

    # ---- explicar -------------------------------------------------------------------------------------------------------------------------------------------------
    def explicar(self, r, nom=None, plantillas=None) -> str:
        return explicar(r.prueba if isinstance(r, Resultado) else r, nom, plantillas)


# ====================================================================================================================================================================
def _frase(a, nom, plantillas):
    s, p, o = a
    n = nom or (lambda x: x.replace("_", " ").lower())
    if plantillas and p in plantillas:
        return plantillas[p].format(s=n(s), o=n(o))
    if p.startswith("@"):
        return f"{n(s)} {p[1:].lower().replace('_', ' ')} {n(o)}"
    return f"{n(s)} {p.lower().replace('_', ' ')} {n(o)}"


def explicar(pr: Optional[Prueba], nom=None, plantillas=None) -> str:
    """Prueba -> pasos numerados en castellano (de las hojas a la conclusion)."""
    if pr is None:
        return ""
    lineas: List[str] = []
    num: Dict[tuple, int] = {}

    def rec(x: Prueba) -> int:
        clave = (x.atomo, x.regla)
        if clave in num:
            return num[clave]
        refs = [rec(h) for h in x.hijos]
        f = _frase(x.atomo, nom, plantillas)
        r = x.regla
        if r == "hecho":
            txt = f"{f} (lo sé)"
        elif r == "neg":
            txt = f"NO se cumple que {f} (me lo dijeron)" if x.atomo else f
        elif r == "inversa":
            txt = f"{f}, porque es la relación inversa del paso {refs[0]}"
        elif r == "simetrica":
            txt = f"{f}, porque la relación es simétrica (paso {refs[0]})"
        elif r == "subprop":
            txt = f"{f}, porque es un caso particular (paso {refs[0]})"
        elif r == "transitiva":
            txt = f"{f}, encadenando los pasos " + ", ".join(str(i) for i in refs)
        elif r.startswith("regla:"):
            txt = f"{f}, por la regla {r[6:]} con los pasos " + ", ".join(str(i) for i in refs) if refs else f"{f} (regla {r[6:]})"
        elif r == "herencia":
            txt = f"{f}, porque lo hereda de su clase ({x.nota}); pasos {', '.join(str(i) for i in refs)}"
        elif r == "herencia_neg":
            txt = f"NO se cumple que {f}: {x.nota}; pasos {', '.join(str(i) for i in refs)}"
        elif r in ("funcional", "funcional_inv", "disjunta"):
            txt = f"NO se cumple que {f}: {x.nota}"
        elif r == "mundo_cerrado":
            txt = f"NO se cumple que {f}: {x.nota}"
        elif r == "comparacion":
            txt = f"{f} ({x.nota})"
        elif r == "comparacion_no":
            txt = f"NO se cumple que {f}: {x.nota}"
        elif r == "asimetrica":
            txt = f"NO se cumple que {f}: {x.nota} (paso {refs[0]})"
        elif r == "calculo":
            txt = f"{f} (cálculo)"
        elif r == "naf":
            txt = f"no consta que {f[1:] if f.startswith('!') else f}"
        elif r == "extremo":
            txt = f"{x.atomo[0].lower()} tiene el valor {'más alto' if 'MAX' in x.atomo[1] else 'más bajo'} entre los {len(x.hijos)} datos comparados"
        else:
            txt = f
        lineas.append(f"{len(lineas) + 1}. {txt[:1].upper() + txt[1:]}.")
        num[clave] = len(lineas)
        return len(lineas)

    rec(pr)
    return "\n".join(lineas)


# ====================================================================================================================================================================
class Verificador:
    """Comprueba una prueba SIN usar el motor: solo la base de hechos, las reglas y las propiedades. Devuelve (ok, motivo)."""

    def __init__(self, hechos, reglas, props, negados=()):
        self.h = {tuple(N(x) for x in f) for f in hechos}
        self.neg = {tuple(N(x) for x in f) for f in negados}
        self.props = {N(k): v for k, v in (props or {}).items()}
        self.reglas = {}
        for i, r in enumerate(reglas):
            rr = r if isinstance(r, Regla) else Regla.de_dict(r, f"R{i}")
            self.reglas[rr.id] = rr
        self.inv = {}
        self.sub = defaultdict(set)
        for p, d in self.props.items():
            if d.get("inversa"):
                self.inv[p] = N(d["inversa"])
                self.inv.setdefault(N(d["inversa"]), p)
            for s_ in ([d["subprop"]] if isinstance(d.get("subprop"), str) else d.get("subprop", [])):
                self.sub[N(s_)].add(p)

    def ok(self, pr: Prueba) -> Tuple[bool, str]:
        try:
            return self._v(pr)
        except Exception as e:                                                  # noqa
            return False, f"error al verificar: {e!r}"

    def _v(self, x: Prueba):
        s, p, o = x.atomo
        r = x.regla
        for h in x.hijos:
            ok, why = self._v(h)
            if not ok:
                return False, why
        if r == "hecho":
            return ((s, p, o) in self.h, "el hecho no está en la base")
        if r == "neg":
            return ((s, p, o) in self.neg, "el hecho negado no está en la base")
        if r == "calculo":
            a, b = _num(s), _num(o)
            if p == "@DISTINTO":
                return (s != o, "no son distintos")
            return ((a is not None and b is not None and {"@MAYOR": a > b, "@MENOR": a < b, "@IGUAL": a == b, "@MAYOR_IGUAL": a >= b, "@MENOR_IGUAL": a <= b}.get(p, False)) or (p == "@IGUAL" and s == o), "cálculo falso")
        if r == "simetrica":
            h = x.hijos[0].atomo
            return (bool(self.props.get(p, {}).get("simetrica")) and h == (o, p, s), "simetría no válida")
        if r == "inversa":
            h = x.hijos[0].atomo
            return (self.inv.get(p) == h[1] and h[0] == o and h[2] == s, "inversa no válida")
        if r == "subprop":
            h = x.hijos[0].atomo
            return (p in self.sub.get(h[1], set()) or h[1] in self.sub.get(p, set()) and False or p in self._supers(h[1]), "subpropiedad no declarada") if (h[0], h[2]) == (s, o) else (False, "extremos distintos")
        if r == "transitiva":
            if not self.props.get(p, {}).get("transitiva") and not x.nota == "ruta":
                return False, "la relación no es transitiva"
            if len(x.hijos) < 2:
                return False, "cadena demasiado corta"
            if x.hijos[0].atomo[0] != s or x.hijos[-1].atomo[2] != o:
                return False, "extremos de la cadena no coinciden"
            for a, b in zip(x.hijos, x.hijos[1:]):
                if a.atomo[2] != b.atomo[0]:
                    return False, "cadena rota"
            return all(h.atomo[1] == p for h in x.hijos), "paso de otra relación"
        if r.startswith("regla:"):
            rg = self.reglas.get(r[6:])
            if rg is None:
                return False, "regla desconocida"
            return self._regla(rg, x)
        if r == "comparacion":
            cfg = self.props.get(p, {}).get("compara")
            if not cfg or len(x.hijos) != 2:
                return False, "comparación no declarada"
            va, vb = _num(x.hijos[0].atomo[2]), _num(x.hijos[1].atomo[2])
            if x.hijos[0].atomo[0] != s or x.hijos[1].atomo[0] != o or x.hijos[0].atomo[1] != N(cfg["atributo"]) or x.hijos[1].atomo[1] != N(cfg["atributo"]):
                return False, "atributos mal citados"
            return ((va > vb) if cfg.get("op", ">") == ">" else (va < vb), "la comparación es falsa")
        if r == "herencia":
            base, cadena = x.hijos
            return (base.atomo[1] == p and base.atomo[2] == o and cadena.atomo[0] == s and cadena.atomo[1] == "ES" and cadena.atomo[2] == base.atomo[0] and self._mas_cercano(s, p, o, base.atomo[0], True), "herencia no válida")
        if r == "herencia_neg":
            base, cadena = x.hijos
            return (base.atomo == (cadena.atomo[2], p, o) and cadena.atomo[0] == s and self._mas_cercano(s, p, o, base.atomo[0], False), "excepción no válida")
        if r == "asimetrica":
            h = x.hijos[0].atomo
            return (bool(self.props.get(p, {}).get("asimetrica")) and h == (o, p, s) and s != o, "asimetría no válida")
        if r == "comparacion_no":
            cfg = self.props.get(p, {}).get("compara")
            if not cfg or len(x.hijos) != 2:
                return False, "comparación no declarada"
            a1, a2 = x.hijos[0].atomo, x.hijos[1].atomo
            at = N(cfg["atributo"])
            if (a1[0], a1[1], a2[0], a2[1]) != (s, at, o, at):
                return False, "atributos mal citados"
            va, vb = _num(a1[2]), _num(a2[2])
            return (not ((va > vb) if cfg.get("op", ">") == ">" else (va < vb)), "la comparación sí se cumple")
        if r == "funcional":
            h = x.hijos[0].atomo
            return (bool(self.props.get(p, {}).get("funcional")) and h[0] == s and h[1] == p and h[2] != o, "unicidad no válida")
        if r == "funcional_inv":
            h = x.hijos[0].atomo
            return (bool(self.props.get(p, {}).get("funcional_inv")) and h[2] == o and h[1] == p and h[0] != s, "unicidad no válida")
        if r == "disjunta":
            d = [h.atomo for h in x.hijos if h.atomo[1] == "DISJUNTA_CON"]
            return (len(d) == 1 and p == "ES", "incompatibilidad no válida") if d else (False, "falta DISJUNTA_CON")
        if r == "mundo_cerrado":
            return (bool(self.props.get(p, {}).get("mundo_cerrado")) and (s, p, o) not in self.h, "mundo cerrado no válido")
        if r == "extremo":
            return self._extremo(x)
        if r == "naf":
            return (True, "")
        return False, f"razón desconocida: {r}"

    def _supers(self, p):
        out = set()
        for sup, hs in self.sub.items():
            if p in hs:
                out.add(sup)
        return out

    def _regla(self, rg: Regla, x: Prueba):
        b: Dict[str, str] = {}

        def unif(pat, val):
            if es_var(pat):
                if b.get(pat, val) != val:
                    return False
                b[pat] = val
                return True
            return pat == val
        c = rg.conclusion
        if not (unif(c[0], x.atomo[0]) and c[1] == x.atomo[1] and unif(c[2], x.atomo[2])):
            return False, "conclusión distinta a la de la regla"
        hijos = list(x.hijos)
        if len(hijos) != len(rg.premisas):
            return False, "número de premisas distinto"
        for (a, p, o), h in zip(rg.premisas, hijos):
            if p.startswith("!"):
                continue
            if h.atomo[1] != p or not (unif(a, h.atomo[0]) and unif(o, h.atomo[2])):
                return False, f"premisa {a} {p} {o} no encaja con {h.atomo}"
        return True, ""

    def _anc(self, s):
        out, cola, vis = {}, deque([(s, 0)]), {s}
        while cola:
            n, d = cola.popleft()
            for (a, p, b) in self.h:
                pass
            for b in self._es(n):
                if b not in vis:
                    vis.add(b)
                    out[b] = d + 1
                    cola.append((b, d + 1))
        return out

    def _es(self, n):
        res = {o for (a, p, o) in self.h if a == n and p == "ES"}
        for q in self.sub.get("ES", ()):
            res |= {o for (a, p, o) in self.h if a == n and p == q}
        return res

    def _mas_cercano(self, s, p, o, cls, positivo):
        """La clase `cls` decide el rasgo y ninguna clase mas cercana (o la misma distancia con signo opuesto) lo decide."""
        anc = self._anc(s)
        anc[s] = 0
        if cls not in anc:
            return False
        d0 = anc[cls]
        for c, d in anc.items():
            if d < d0 and (((c, p, o) in self.h) or ((c, p, o) in self.neg)):
                return False
            if d == d0 and c != cls and (((c, p, o) in self.h) != positivo or ((c, p, o) in self.neg) == positivo) and (((c, p, o) in self.h) or ((c, p, o) in self.neg)):
                return False
        return ((cls, p, o) in self.h) if positivo else ((cls, p, o) in self.neg)

    def _extremo(self, x: Prueba):
        modo = "max" if "MAX" in x.atomo[1] else "min"
        attr = x.atomo[2]
        datos = [h for h in x.hijos if h.regla == "hecho" and h.atomo[1] == attr]
        val = {}
        for h in datos:
            if h.atomo not in self.h:
                return False, "dato inexistente"
            val[h.atomo[0]] = _num(h.atomo[2])
        e = x.atomo[0]
        if e not in val:
            return False, "el ganador no está entre los datos"
        mejor = max(val.values()) if modo == "max" else min(val.values())
        if val[e] != mejor or sum(1 for v in val.values() if v == mejor) != 1:
            return False, "no es el extremo único"
        todos = {a for (a, p, _) in self.h if p == attr and _num(_) is not None}
        clase = x.nota.split(":", 1)[1]
        if clase == "*":
            return (set(val) == todos, "faltan candidatos")
        miembros = {a for a in todos if clase in self._anc(a)}
        return (set(val) == miembros, "faltan o sobran candidatos de la clase")
