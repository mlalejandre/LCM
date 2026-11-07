"""Esquemas: de varias lecciones parecidas a UNA regla general (parche-14).

Una leccion  ANA PADRE_DE LUIS => LUIS HIJO_DE ANA  se generaliza a
    ?0 PADRE_DE ?1 => ?1 HIJO_DE ?0
donde ?0 y ?1 son variables (entidades) y los predicados/valores fijos son
constantes. Con el esquema se pueden "sonar" (instanciar) ejemplos nuevos con
otras entidades: la base del repaso generativo durante el sueno.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Sequence, Tuple

Triple = Tuple[str, str, str]


def is_entity(space, name: str) -> bool:
    return space.metadata.get(name, {}).get("kind") == "entity"


def family(space, name: str) -> FrozenSet[str]:
    feats = space.metadata.get(name, {}).get("features", {})
    return frozenset(f for f in feats if not f.startswith("identity:"))


@dataclass
class Schema:
    premises: List[Tuple[str, str, str]]
    conclusion: Tuple[str, str, str]
    var_family: Dict[str, FrozenSet[str]] = field(default_factory=dict)

    @property
    def signature(self) -> str:
        return json.dumps([self.premises, self.conclusion], sort_keys=True)

    @property
    def n_vars(self) -> int:
        return len(self.var_family)


def induce(space, premises: Sequence[Triple], conclusion: Triple) -> Schema:
    mapping: Dict[str, str] = {}
    fams: Dict[str, FrozenSet[str]] = {}

    def conv(name: str, slot: int, learn: bool) -> str:
        if slot != 1 and is_entity(space, name):
            if name in mapping:
                return mapping[name]
            if learn:
                var = f"?{len(mapping)}"
                mapping[name] = var
                fams[var] = family(space, name)
                return var
        return name

    prem = [tuple(conv(x, i, True) for i, x in enumerate(p)) for p in premises]
    concl = tuple(conv(x, i, False) for i, x in enumerate(conclusion))
    return Schema(prem, concl, fams)


def instantiate(space, schema: Schema, rng: random.Random, entities: Sequence[str]) -> Tuple[List[Triple], Triple]:
    """Rellena las variables con entidades distintas de la misma familia."""
    chosen: Dict[str, str] = {}
    used = set()
    for var, fam in schema.var_family.items():
        same = [e for e in entities if family(space, e) == fam and e not in used]
        pool = same or [e for e in entities if (family(space, e) & fam) and e not in used] or [e for e in entities if e not in used]
        pick = rng.choice(pool)
        chosen[var] = pick
        used.add(pick)
    fill = lambda t: tuple(chosen.get(x, x) for x in t)
    return [fill(p) for p in schema.premises], fill(schema.conclusion)
