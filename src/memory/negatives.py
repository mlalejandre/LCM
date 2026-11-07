"""Ejemplos NEGATIVOS para las lecciones (parche-20): "esta regla NO se aplica aqui".

Fallo que mostro la conversacion real: tras ensenar  X PADRE_DE Y => Y HIJO_DE X,
el modelo respondia  JOSE HIJO_DE PACO  a  "Paco HIJO_DE Jose"  (aplicaba la regla a
cualquier frase de dos personas). Las lecciones solo traian casos donde la regla SI
vale. Aqui se generan casos hermanos donde cambia la relacion de una premisa y la
respuesta correcta es  SUJETO SIN_CONCLUSION NINGUNA.

Solo se usan como negativos relaciones que el motor simbolico confirma que, solas,
no concluyen nada (asi no se contradice el conocimiento de fabrica).
"""
from __future__ import annotations

import random
from typing import List, Sequence, Tuple

from ..reasoning.rule_engine import Fact, RuleEngine
from .schema import induce, instantiate, is_entity

Triple = Tuple[str, str, str]
SKIP = {"SIN_CONCLUSION", "REGLA_HEREDA", "CONTRADICE", "NINGUNA"}


# Relaciones "fantasma" (parche-22): nombres que el modelo nunca ha visto. Sirven para que aprenda la regla
# general "si no tengo una leccion para esta relacion, no concluyo", y no solo "no concluyo con AMIGO_DE".
# Suenan como relaciones que el oido puede sacar de una frase en espanol (jefe de, criado de...).
GHOST_POOL = ["JEFE_DE", "CRIADO_DE", "MAESTRO_DE", "SOCIO_DE", "DUENO_DE", "AMO_DE", "CRIADA_DE", "VIUDO_DE",
              "RIVAL_DE", "SOCIA_DE", "TUTOR_DE", "HEREDERO_DE", "ALUMNO_DE", "PATRON_DE", "CONOCIDO_DE", "ENEMIGO_DE"]
_SYL = ["BA", "KO", "LU", "MI", "NE", "PO", "RA", "SU", "TE", "VI", "ZA", "DO", "FE", "GU", "HO"]


def make_ghosts(space, rng: random.Random, n: int, exclude=()) -> List[str]:
    out = []
    pool = [g for g in GHOST_POOL if g not in exclude and g not in space.concept_to_id]
    for _ in range(n):
        if pool and rng.random() < 0.5:
            name = rng.choice(pool)
        else:
            name = "".join(rng.choice(_SYL) for _ in range(rng.randint(2, 4))) + "_DE"
            if name in exclude or name in space.concept_to_id:
                continue
        register_ghost(space, name)
        out.append(name)
    return out


def register_ghost(space, name: str) -> None:
    """Vector temporal para un nombre que NO esta en el catalogo (no se guarda ni se decodifica)."""
    if name in space.proposition_vectors:
        return
    import torch
    import torch.nn.functional as F
    vec = torch.zeros(space.d_concept)
    for feat, w in (("predicate", 1.0), ("relation", 1.0), (f"identity:{name}", 0.5)):
        vec += w * (space.feature_to_vector[feat] if feat in space.feature_to_vector else space._feature_vector(feat))
    space.proposition_vectors[name] = F.normalize(vec, p=2, dim=-1)
    space.__dict__.setdefault("_ghosts", set()).add(name)


def purge_ghosts(space) -> None:
    ghosts = space.__dict__.get("_ghosts")
    if not ghosts:
        return
    for label in [l for l in list(space.proposition_vectors)
                  if l in ghosts or any(part in ghosts for part in space.proposition_parts.get(l, ()))]:
        space.proposition_vectors.pop(label, None)
        space.proposition_parts.pop(label, None)
    ghosts.clear()


def safe_predicates(space) -> List[str]:
    engine = RuleEngine()
    ents = [n for n in space.concept_to_id if is_entity(space, n)][:2]
    out = []
    if len(ents) < 2:
        return out
    for name, meta in space.metadata.items():
        if meta.get("kind") != "predicate" or name in SKIP:
            continue
        given = {Fact(ents[0], name, ents[1])}
        if not (engine.infer(given)["facts"] - given):
            out.append(name)
    return out


def make_negatives(space, lessons: Sequence[Tuple[Sequence[Triple], Triple]], n: int, rng: random.Random,
                   entities: Sequence[str], safe: Sequence[str] | None = None, ghosts: float = 0.5,
                   ghost_exclude=()):
    if not lessons:
        return []
    safe = list(safe) if safe is not None else safe_predicates(space)
    lesson_preds = {p[1] for prem, _ in lessons for p in prem}
    cands = [q for q in safe if q not in lesson_preds]
    fantasmas = make_ghosts(space, rng, max(8, n // 8), exclude=set(ghost_exclude) | lesson_preds) if ghosts > 0 else []
    if not cands and not fantasmas:
        return []
    schemas = {}
    for prem, concl in lessons:
        s = induce(space, [tuple(p) for p in prem], tuple(concl))
        schemas[s.signature] = s
    schemas = list(schemas.values())
    out = []
    for _ in range(n):
        schema = rng.choice(schemas)
        prem, _ = instantiate(space, schema, rng, entities)
        k = rng.randrange(len(prem))
        use_ghost = fantasmas and (not cands or rng.random() < ghosts)
        prem[k] = (prem[k][0], rng.choice(fantasmas if use_ghost else cands), prem[k][2])
        out.append((prem, (prem[0][0], "SIN_CONCLUSION", "NINGUNA")))
    return out
