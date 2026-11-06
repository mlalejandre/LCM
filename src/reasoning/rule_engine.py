"""Motor simbolico minimo para contrastar las predicciones neuronales.

No sustituye al modelo neuronal: define reglas auditables y un oraculo de
referencia para comprobar que las pruebas realmente contienen inferencias.
"""
from dataclasses import dataclass
from typing import Iterable, Set


@dataclass(frozen=True, order=True)
class Fact:
    subject: str
    predicate: str
    obj: str

    def __post_init__(self):
        object.__setattr__(self, "subject", self.subject.upper())
        object.__setattr__(self, "predicate", self.predicate.upper())
        object.__setattr__(self, "obj", self.obj.upper())


class RuleEngine:
    def __init__(self, max_iterations: int = 32):
        self.max_iterations = max_iterations

    @staticmethod
    def _coerce(facts: Iterable) -> Set[Fact]:
        result = set()
        for fact in facts:
            if isinstance(fact, Fact):
                result.add(fact)
            elif isinstance(fact, (tuple, list)) and len(fact) == 3:
                result.add(Fact(*fact))
            else:
                raise TypeError(f"Formato de hecho no reconocido: {fact!r}")
        return result

    def infer(self, facts: Iterable[Fact]):
        known = self._coerce(facts)
        iterations = 0
        for iteration in range(self.max_iterations):
            additions = set()
            by_subject_predicate = {}
            by_predicate = {}
            for fact in known:
                by_subject_predicate.setdefault((fact.subject, fact.predicate), set()).add(fact.obj)
                by_predicate.setdefault(fact.predicate, []).append(fact)

            # 1) Transitividad: A > B y B > C => A > C.
            greater = by_predicate.get("MAYOR_QUE", [])
            outgoing = {}
            for fact in greater:
                outgoing.setdefault(fact.subject, set()).add(fact.obj)
            for first in greater:
                for end in outgoing.get(first.obj, ()):
                    if first.subject != end:
                        additions.add(Fact(first.subject, "MAYOR_QUE", end))

            # 2) Caida: liberado en aire + sometido a gravedad.
            released = by_predicate.get("LIBERADO_EN", [])
            gravity = by_predicate.get("SOMETIDO_A", [])
            gravity_subjects = {f.subject for f in gravity if f.obj == "GRAVEDAD"}
            for fact in released:
                if fact.obj == "AIRE" and fact.subject in gravity_subjects:
                    additions.add(Fact(fact.subject, "CAE_HACIA", "SUELO"))

            # 3) Fusion: requiere evidencia de que la sustancia es fundible.
            exposed = by_predicate.get("EXPUESTO_A", [])
            meltable = {f.subject for f in by_predicate.get("ES", []) if f.obj == "FUNDIBLE"}
            for fact in exposed:
                if fact.obj == "CALOR" and fact.subject in meltable:
                    additions.add(Fact(fact.subject, "CAMBIA_A", "LIQUIDO"))

            # 4) Cardinalidad: finito implica enumerable.
            finite = by_predicate.get("ES_FINITO", [])
            for fact in finite:
                if fact.obj == "TRUE":
                    additions.add(Fact(fact.subject, "ES", "ENUMERABLE"))
                    additions.add(Fact(fact.subject, "TIENE_CARDINALIDAD_FINITA", "TRUE"))

            # 5) Infinito numerable/no numerable: exige evidencia de biyeccion
            # (o de su inexistencia), no basta con afirmar que es infinito.
            infinite = {f.subject for f in by_predicate.get("ES_INFINITO", []) if f.obj == "TRUE"}
            bijective = {f.subject for f in by_predicate.get("TIENE_BIYECCION_CON", []) if f.obj == "NATURALES"}
            non_bijective = {f.subject for f in by_predicate.get("NO_TIENE_BIYECCION_CON", []) if f.obj == "NATURALES"}
            for subject in infinite & bijective:
                additions.add(Fact(subject, "ES", "INFINITO_NUMERABLE"))
                additions.add(Fact(subject, "ES", "ENUMERABLE"))
            for subject in infinite & non_bijective:
                additions.add(Fact(subject, "ES", "INNUMERABLE"))

            # 7) Contradicciones en MAYOR_QUE: A>B y B>A, o ciclos A>B>C>A.
            reach = {}
            for fact in greater:
                reach.setdefault(fact.subject, set()).add(fact.obj)
            for a_node, nexts in reach.items():
                for b_node in nexts:
                    if a_node in reach.get(b_node, ()):
                        additions.add(Fact(a_node, "CONTRADICE", b_node))
                    for c_node in reach.get(b_node, ()):
                        if a_node in reach.get(c_node, ()):
                            additions.add(Fact(a_node, "CONTRADICE", a_node))

            # 6) Herencia con la regla enunciada como hecho:
            #    (HP REGLA_HEREDA HA), (X HP P), (P HA Q)  =>  (X HP Q)
            for rule in by_predicate.get("REGLA_HEREDA", []):
                hp, ha = rule.subject, rule.obj
                for first in by_predicate.get(hp, []):
                    for q in by_subject_predicate.get((first.obj, ha), ()):
                        additions.add(Fact(first.subject, hp, q))

            additions -= known
            if not additions:
                break
            known.update(additions)
            iterations = iteration + 1
        return {"facts": known, "iterations": iterations}


def run_reference_tests():
    engine = RuleEngine()
    cases = {}

    result = engine.infer([
        Fact("ALFA_NUEVO", "MAYOR_QUE", "BETA_NUEVO"),
        Fact("BETA_NUEVO", "MAYOR_QUE", "GAMMA_NUEVO"),
    ])
    cases["transitivity_unseen_entities"] = Fact("ALFA_NUEVO", "MAYOR_QUE", "GAMMA_NUEVO") in result["facts"]

    result = engine.infer([
        Fact("DRON_NUEVO", "LIBERADO_EN", "AIRE"),
        Fact("DRON_NUEVO", "SOMETIDO_A", "GRAVEDAD"),
    ])
    cases["gravity_unseen_entity"] = Fact("DRON_NUEVO", "CAE_HACIA", "SUELO") in result["facts"]

    result = engine.infer([Fact("CONJUNTO_F", "ES_FINITO", "TRUE")])
    cases["finite_implies_countable"] = Fact("CONJUNTO_F", "ES", "ENUMERABLE") in result["facts"]

    result = engine.infer([
        Fact("CONJUNTO_C", "ES_INFINITO", "TRUE"),
        Fact("CONJUNTO_C", "TIENE_BIYECCION_CON", "NATURALES"),
    ])
    cases["bijection_implies_countably_infinite"] = Fact("CONJUNTO_C", "ES", "INFINITO_NUMERABLE") in result["facts"]

    result = engine.infer([
        Fact("CONJUNTO_N", "ES_INFINITO", "TRUE"),
        Fact("CONJUNTO_N", "NO_TIENE_BIYECCION_CON", "NATURALES"),
    ])
    cases["explicit_no_bijection_implies_uncountable"] = Fact("CONJUNTO_N", "ES", "INNUMERABLE") in result["facts"]

    result = engine.infer([Fact("INFINITO_SIN_MAS", "ES_INFINITO", "TRUE")])
    cases["infinite_alone_not_uncountable"] = Fact("INFINITO_SIN_MAS", "ES", "INNUMERABLE") not in result["facts"]

    result = engine.infer([
        Fact("CERA_NUEVA", "EXPUESTO_A", "CALOR"),
        Fact("CERA_NUEVA", "ES", "FUNDIBLE"),
    ])
    cases["melting_requires_fusible_evidence"] = Fact("CERA_NUEVA", "CAMBIA_A", "LIQUIDO") in result["facts"]
    result = engine.infer([Fact("MATERIAL_DESCONOCIDO", "EXPUESTO_A", "CALOR")])
    cases["heat_alone_does_not_imply_melting"] = Fact("MATERIAL_DESCONOCIDO", "CAMBIA_A", "LIQUIDO") not in result["facts"]

    return {"passed": sum(bool(v) for v in cases.values()), "total": len(cases), "cases": cases}

