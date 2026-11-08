"""Memoria persistente del LCM (parche-13).

Guarda lo que el modelo aprende DIALOGANDO:
  - conceptos nuevos (se re-registran de forma determinista en el catalogo base),
  - hechos sueltos (memoria semantica: "A MAYOR_QUE B"),
  - lecciones (premisas => conclusion) que sirven para aprender y para REPASAR.
Es la base del futuro ciclo de sueno: lo que se consolida sale de aqui.
"""
from __future__ import annotations

import json
import os
import time
from collections import deque
from datetime import date
from typing import Dict, List, Optional, Tuple

Triple = Tuple[str, str, str]


class MemoryStore:
    def __init__(self, path: str = "memory/lcm_memory.json"):
        self.path = path
        self.concepts: List[dict] = []
        self.facts: List[dict] = []
        self.alias: Dict[str, str] = {}         # sinonimos (parche-58): AUTO -> COCHE
        self.opposites: List[list] = []         # pares de contrarios ensenados: ["ruidoso", "silencioso"]
        self.verb_isa: Dict[str, str] = {}      # "cocinar" -> "preparar"
        self.defs: Dict[str, str] = {}          # definiciones tal como se dijeron
        self.past: List[dict] = []              # hechos que dejaron de valer (parche-57): "Ana vivia en Madrid"
        self.lessons: List[dict] = []
        self.surface: Dict[str, str] = {}   # predicado -> plantilla "{s} vive en {o}" (como lo dijo la persona)
        self.display: Dict[str, str] = {}   # entidad -> como se escribia ("el perro", "Marta")
        self.tick = 0  # reloj de mantenimiento: sube una unidad por cada ciclo de sueno
        self.textos: List[dict] = []            # parche-127: frases leidas (texto + arbol de la escuela) para contestar preguntas sobre lo leido
        self._textos_vistos: set = set()
        if os.path.exists(path):
            self.load()

    # ---- persistencia -------------------------------------------------
    def _personal(self) -> dict:
        """Lo que se guarda en la memoria PERSONAL: sin lo que viene de cartuchos montados (parche-91), que se recompone al arrancar."""
        from src.memory.cartuchos import duenos
        own_pairs = [p for d in getattr(self, "cart_own", {}).values() for p in d.get("opposites", [])]
        data = {"concepts": self.concepts, "facts": [f for f in self.facts if not f.get("cart")], "past": self.past, "alias": self.alias,
                "opposites": [p for p in self.opposites if list(p) not in own_pairs], "verb_isa": self.verb_isa, "defs": self.defs, "lessons": self.lessons,
                "tick": self.tick, "surface": self.surface, "display": self.display, "textos": self.textos}
        for sec in ("alias", "verb_isa", "defs", "surface", "display"):
            own = duenos(self, sec)
            if own:
                data[sec] = {k: v for k, v in data[sec].items() if k not in own}
        return data

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(self._personal(),
                      handle, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)

    def load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.concepts = data.get("concepts", [])
        self.facts = data.get("facts", [])
        self.past = data.get("past", [])
        self.alias = data.get("alias", {})
        self.opposites = data.get("opposites", [])
        self.verb_isa = data.get("verb_isa", {})
        self.defs = data.get("defs", {})
        self.lessons = data.get("lessons", [])
        self.tick = int(data.get("tick", 0))
        self.surface = data.get("surface", {})
        self.display = data.get("display", {})
        self.textos = data.get("textos", [])
        self._textos_vistos = {t.get("t") for t in self.textos}

    def add_texto(self, txt: str, arboles: List[str], sec: str = "", doc: int = 0, k: int = 0, par: int = 0) -> bool:
        """parche-127: guarda una frase leida con su arbol (una cadena por tramo: cada token «forma TAB upos TAB cabeza TAB relacion TAB lema», uno por linea)."""
        if not txt or txt in self._textos_vistos:
            return False
        self._textos_vistos.add(txt)
        self.textos.append({"t": txt, "r": list(arboles), "sec": sec, "d": doc, "k": k, "p": par})
        return True

    # ---- conceptos ----------------------------------------------------
    def add_concept(self, name: str, features: Optional[dict] = None, kind: str = "entity") -> None:
        name = name.upper()
        if any(c["name"] == name for c in self.concepts):
            return
        self.concepts.append({"name": name, "features": features, "kind": kind, "t": time.time()})

    def apply_concepts(self, space) -> int:
        """Re-registra los conceptos guardados en un espacio base (vectores deterministas)."""
        added = 0
        for c in self.concepts:
            if c["name"] not in space.concept_to_id:
                space.add_concept(c["name"], features=c.get("features"), kind=c.get("kind", "entity"))
                added += 1
        return added

    # ---- hechos -------------------------------------------------------
    def add_fact(self, fact: Triple, source: str = "usuario", neg: bool = False, when: str = "", when_disp: str = "", quant: str = "") -> bool:
        """neg=True guarda un hecho NEGADO ("Ana no es madre de Luis"): no se usa para razonar, pero se recuerda."""
        fact = tuple(x.upper() for x in fact)
        from src.language.fechas import resolve
        when_abs = resolve(when, getattr(self, "today", None) or date.today()) if when else None
        for f in self.facts:
            if (f["s"], f["p"], f["o"]) == fact and bool(f.get("neg", False)) == neg and f.get("when", "") == when \
                    and f.get("when_abs") == when_abs and f.get("q", "") == quant:
                f["n"] += 1
                return False
        self.facts.append({"s": fact[0], "p": fact[1], "o": fact[2], "t": time.time(), "n": 1, "source": source,
                           "imp": 1.0, "tick": self.tick, "archived": False, "neg": neg, "when": when, "when_disp": when_disp, "when_abs": when_abs, "q": quant})
        return True

    def note_surface(self, fact: Triple, template: Optional[str] = None, s_disp: Optional[str] = None,
                     o_disp: Optional[str] = None) -> None:
        """Recuerda como se dijo una proposicion para poder contestar con las mismas palabras."""
        s, p, o = (x.upper() for x in fact)
        if template and p not in self.surface:
            self.surface[p] = template
        if s_disp and s not in self.display:
            self.display[s] = s_disp
        if o_disp and o not in self.display:
            self.display[o] = o_disp

    def contradicts(self, fact: Triple, neg: bool) -> bool:
        """Hay guardado el hecho contrario (afirmado vs negado)?"""
        fact = tuple(x.upper() for x in fact)
        return any((f["s"], f["p"], f["o"]) == fact and bool(f.get("neg", False)) != neg for f in self.facts)

    def forget_fact(self, fact: Triple) -> bool:
        fact = tuple(x.upper() for x in fact)
        before = len(self.facts)
        self.facts = [f for f in self.facts if (f["s"], f["p"], f["o"]) != fact]
        return len(self.facts) < before

    def find_path(self, start: str, goal: str, max_len: int = 4) -> List[Triple]:
        """Cadena de hechos (<= max_len) que enlaza start con goal, por conceptos compartidos."""
        start, goal = start.upper(), goal.upper()
        edges: Dict[str, List[Triple]] = {}
        for f in self.facts:  # los archivados tambien cuentan: si sirven, se restauran (olvido reversible)
            if f.get("neg"):
                continue
            edges.setdefault(f["s"], []).append((f["s"], f["p"], f["o"]))
        queue = deque([(start, [])])
        seen = {start}
        while queue:
            node, route = queue.popleft()
            if node == goal and route:
                return route
            if len(route) >= max_len:
                continue
            for fact in edges.get(node, []):
                if fact[2] not in seen or fact[2] == goal:
                    seen.add(fact[2])
                    queue.append((fact[2], route + [fact]))
        return []

    # ---- lecciones ----------------------------------------------------
    def add_lesson(self, premises: List[Triple], conclusion: Triple) -> bool:
        prem = [list(x.upper() for x in p) for p in premises]
        concl = [x.upper() for x in conclusion]
        for l in self.lessons:
            if l["premises"] == prem and l["conclusion"] == concl:
                l["n"] += 1
                return False
        self.lessons.append({"premises": prem, "conclusion": concl, "t": time.time(), "n": 1, "archived": False})
        return True

    def active_lessons(self) -> List[dict]:
        return [l for l in self.lessons if not l.get("archived")]

    # ---- olvido reversible (curva de olvido, inspirada en memoria-unificada) --------
    def effective_importance(self, fact: dict, tau: float = 20.0) -> float:
        """I * exp(-edad / (tau * I^3)): lo importante o muy usado dura mucho mas."""
        import math
        imp = max(float(fact.get("imp", 1.0)), 0.05)
        age = max(self.tick - int(fact.get("tick", 0)), 0)
        return imp * math.exp(-age / (tau * imp ** 3))

    def touch(self, fact_triple: Triple) -> None:
        """Recordar un hecho lo refuerza y lo restaura si estaba archivado."""
        fact_triple = tuple(x.upper() for x in fact_triple)
        for f in self.facts:
            if (f["s"], f["p"], f["o"]) == fact_triple:
                f["imp"] = float(f.get("imp", 1.0)) + 0.5
                f["tick"] = self.tick
                f["archived"] = False

    def decay(self, tau: float = 20.0, below: float = 0.15, min_age: int = 3) -> int:
        archived = 0
        for f in self.facts:
            if f.get("archived"):
                continue
            if self.tick - int(f.get("tick", 0)) >= min_age and self.effective_importance(f, tau) < below:
                f["archived"] = True
                archived += 1
        return archived

    def summary(self) -> str:
        arch_f = sum(1 for f in self.facts if f.get("archived"))
        arch_l = sum(1 for l in self.lessons if l.get("archived"))
        extra = f" (archivados: {arch_f} hechos, {arch_l} lecciones)" if arch_f or arch_l else ""
        return f"{len(self.concepts)} conceptos, {len(self.facts)} hechos, {len(self.lessons)} lecciones{extra}"
