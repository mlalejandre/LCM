"""Construye una ontologia explicita y datos composicionales con holdouts.

Los conjuntos train/val/test separan pares de salida en transitividad y
entidades completas en reglas fisicas/cardinalidad. En transitividad, las
premisas de todos los splits proceden exclusivamente de pares train para
impedir que objetivos val/test aparezcan como entradas de entrenamiento.
El test no se utiliza para seleccionar checkpoints.
"""
import json
import os
import pickle
import random
import torch
from torch.utils.data import TensorDataset
from src.ontology.concept_space import ConceptSpace

D_CONCEPT = 128
MAX_PREMISES = 4


def _register(space, name, es, en, features, kind="concept"):
    space.register_concept(name, es, en, features=features, kind=kind)


def build_ontology():
    space = ConceptSpace(d_concept=D_CONCEPT)

    base = [
        ("MANZANA", "una manzana", "an apple", {"physical_object": 1, "fruit": 1, "edible": 0.5}),
        ("SOLTAR", "accion de soltar", "release action", {"event": 1, "release_event": 1}),
        ("GRAVEDAD", "fuerza gravitatoria", "gravitational force", {"physical_force": 1, "attraction": 1}),
        ("CAER", "movimiento descendente", "downward motion", {"motion": 1, "downward_motion": 1}),
        ("CONJUNTO_FINITO", "conjunto finito", "finite set", {"set": 1, "finite": 1}),
        ("CONJUNTO_INFINITO", "conjunto infinito", "infinite set", {"set": 1, "infinite": 1}),
        ("CONTAR", "proceso de enumeracion", "counting process", {"enumeration_process": 1}),
        ("CARDINALIDAD", "tamano de un conjunto", "set cardinality", {"mathematical_property": 1, "size": 1}),
        ("ENUMERABLE", "conjunto enumerable", "countable set", {"set_property": 1, "enumerable": 1}),
        ("INFINITO_NUMERABLE", "infinito numerable", "countably infinite", {"set_property": 1, "infinite": 1, "enumerable": 1}),
        ("INNUMERABLE", "conjunto no numerable", "uncountable set", {"set_property": 1, "infinite": 1, "not_enumerable": 1}),
        ("NO_CONTAR", "no finalizar una enumeracion", "not finishing an enumeration", {"process_property": 1, "inconclusive": 1}),
        ("HIELO", "agua en estado solido", "water in solid state", {"substance": 1, "solid": 1, "water": 1, "meltable": 1}),
        ("CALOR", "energia termica", "thermal energy", {"energy": 1, "thermal": 1}),
        ("DERRETIR", "cambio de solido a liquido", "solid-to-liquid phase change", {"phase_transition": 1, "melting": 1}),
        ("AIRE", "aire", "air", {"environment": 1, "gas": 1}),
        ("SUELO", "suelo", "ground", {"environment": 1, "solid_surface": 1}),
        ("LIQUIDO", "estado liquido", "liquid state", {"phase": 1, "liquid": 1}),
        ("FUNDIBLE", "sustancia capaz de fundirse", "meltable substance", {"material_property": 1, "meltable": 1}),
        ("NATURALES", "numeros naturales", "natural numbers", {"mathematical_set": 1, "natural_numbers": 1}),
        ("TRUE", "verdadero", "true", {"truth_value": 1}),
        ("NINGUNA", "ninguna conclusion", "no conclusion", {"truth_value": 0.3, "absence": 1}),
    ]
    for item in base:
        _register(space, *item)

    predicates = [
        "MAYOR_QUE", "LIBERADO_EN", "SOMETIDO_A", "CAE_HACIA", "EXPUESTO_A",
        "CAMBIA_A", "ES", "ES_FINITO", "ES_INFINITO", "TIENE_BIYECCION_CON",
        "NO_TIENE_BIYECCION_CON", "ES_ENUMERABLE", "TIENE_CARDINALIDAD_FINITA",
        "SIN_CONCLUSION",
        "MENOR_QUE", "SUPERIOR_A",          # predicados de orden usados tambien en entrenamiento
        "ANTERIOR_A", "POSTERIOR_A",        # predicados de orden NUNCA vistos (solo test)
        "HEREDA", "IMPLICA", "POSEE", "CAUSA", "ADQUIERE", "DERIVA_EN",
        "MUESTRA", "ORIGINA", "EXHIBE", "PROVOCA",  # herencia (train)
        "TIENE_RASGO", "PRODUCE",           # herencia de propiedades (SOLO test)
        "REGLA_HEREDA",                     # enunciado de la regla (premisa)
        "CONTRADICE",                       # conclusion ante premisas incompatibles
    ]
    ordering = {"MAYOR_QUE", "MENOR_QUE", "SUPERIOR_A", "ANTERIOR_A", "POSTERIOR_A"}
    for predicate in predicates:
        _register(
            space, predicate, predicate.lower().replace("_", " "),
            predicate.lower().replace("_", " "),
            {"predicate": 1, f"predicate_family:{predicate}": 1,
             **({"ordering_relation": 1} if predicate in ordering else {})}, kind="predicate"
        )

    # Entidades abstractas para probar composicion transitiva.
    order_entities = [f"ORDEN_{i:02d}" for i in range(18)]
    for i, name in enumerate(order_entities):
        _register(space, name, f"elemento abstracto {i}", f"abstract element {i}",
                  {"abstract_entity": 1, "ordered_domain": 0.4, f"identity:{name}": 0.5}, "entity")

    # Objetos fisicos: las instancias de test no aparecen en entrenamiento.
    object_entities = []
    categories = ["FRUTA", "PELOTA", "PIEDRA", "MONEDA", "BLOQUE", "HERRAMIENTA"]
    for category in categories:
        for j in range(16):
            name = f"OBJ_{category}_{j:02d}"
            object_entities.append((category, j, name))
            _register(space, name, f"objeto {category.lower()} {j}", f"{category.lower()} object {j}",
                      {"physical_object": 1, f"category:{category}": 0.8,
                       "movable": 0.5, f"identity:{name}": 0.5}, "entity")

    # Sustancias fundibles, con instancias no vistas en el test.
    meltables = []
    for category in ("HIELO", "CERA", "MANTEQUILLA"):
        for j in range(12):
            name = f"SUST_{category}_{j:02d}"
            meltables.append((category, j, name))
            _register(space, name, f"muestra de {category.lower()} {j}", f"{category.lower()} sample {j}",
                      {"substance": 1, "solid": 1, "meltable": 1,
                       f"substance_family:{category}": 0.8, f"identity:{name}": 0.5}, "entity")

    # Conjuntos usados para distinguir finitud, numerabilidad y no numerabilidad.
    finite_sets, countable_sets, uncountable_sets = [], [], []
    for j in range(36):
        for prefix, collection, features in (
            ("FINITO", finite_sets, {"set": 1, "finite": 1}),
            ("NUMERABLE", countable_sets, {"set": 1, "infinite": 1, "enumerable": 1}),
            ("NO_NUMERABLE", uncountable_sets, {"set": 1, "infinite": 1, "not_enumerable": 1}),
        ):
            name = f"SET_{prefix}_{j:02d}"
            collection.append((j, name))
            _register(space, name, f"conjunto {prefix.lower()} {j}", f"{prefix.lower()} set {j}",
                      {**features, f"identity:{name}": 0.5}, "entity")

    # Individuos y propiedades (parche-10). Los *_N_* solo se usan en test.
    for prefix, kind in (("IND", "individual"), ("PROP", "property")):
        for i in range(80):
            nm = f"{prefix}_{i:02d}"
            _register(space, nm, f"{kind} {i}", f"{kind} {i}", {kind: 1, f"identity:{nm}": 0.5}, "entity")
        for i in range(10):
            nm = f"{prefix}_N_{i:02d}"
            _register(space, nm, f"{kind} nuevo {i}", f"new {kind} {i}", {kind: 1, f"identity:{nm}": 0.5}, "entity")

    space.build_space(seed=42)
    return space, order_entities, object_entities, meltables, finite_sets, countable_sets, uncountable_sets


def build_datasets(space, order_entities, object_entities, meltables,
                   finite_sets, countable_sets, uncountable_sets):
    splits = {"train": [], "val": [], "test": []}
    rule_of = {}  # id(ejemplo) -> regla (para equilibrar el entrenamiento)
    current_rule = ["transitivity"]

    rng = random.Random(7)
    pools = {
        "obj": [o for _, _, o in object_entities],
        "sub": [m for _, _, m in meltables],
        "set": [n for grp in (finite_sets, countable_sets, uncountable_sets) for _, n in grp],
    }

    def distractor(subject, kind):
        """Hecho irrelevante sobre OTRA entidad (nunca encadena con la regla)."""
        entity = rng.choice([e for e in pools[kind] if e != subject])
        pred, obj = {"obj": ("LIBERADO_EN", "AIRE"), "sub": ("EXPUESTO_A", "CALOR"),
                     "set": ("ES_INFINITO", "TRUE")}[kind]
        return space.encode_proposition(entity, pred, obj)

    def emit(split, props, target, subject, kind, partials=(), sample=1.0):
        """Variante base + premisas permutadas + distractor + premisas insuficientes.

        Las insuficientes entrenan/evaluan que la red NO concluya sin evidencia
        (objetivo: SUJETO SIN_CONCLUSION NINGUNA)."""
        add(split, props, target, "base")
        if rng.random() > sample:
            return
        if len(props) == 2:
            add(split, props[::-1], target, "swapped")
        noisy = list(props)
        noisy.insert(rng.randint(0, len(noisy)), distractor(subject, kind))
        add(split, noisy, target, "distractor")
        none = space.encode_proposition(subject, "SIN_CONCLUSION", "NINGUNA")
        for partial in partials:
            add(split, [partial], none, "insufficient")

    def add(split, premises, target, variant="base"):
        premise_vectors = [torch.as_tensor(v, dtype=torch.float32) for v in premises]
        if not 1 <= len(premise_vectors) <= MAX_PREMISES:
            raise ValueError("Numero de premisas fuera de rango.")
        seq = torch.zeros(MAX_PREMISES, D_CONCEPT)
        mask = torch.zeros(MAX_PREMISES, dtype=torch.bool)
        seq[:len(premise_vectors)] = torch.stack(premise_vectors)
        mask[:len(premise_vectors)] = True
        example = (seq, mask, torch.as_tensor(target, dtype=torch.float32))
        splits[split].append(example)
        rule_of[id(example)] = (current_rule[0], variant)

    # Regla 1: transitividad. Cada arista ordenada (X,Y) pertenece a un
    # unico bucket. Las dos premisas de TODOS los splits se toman solo de
    # aristas train; la arista conclusion determina el split. De este modo,
    # una conclusion de validacion/test no se filtra como premisa en train.
    def pair_split(source_idx, target_idx):
        bucket = (source_idx * 31 + target_idx * 17) % 10
        return "test" if bucket == 0 else ("val" if bucket == 1 else "train")

    for i, a in enumerate(order_entities):
        for j, b in enumerate(order_entities):
            if i == j or pair_split(i, j) != "train":
                continue
            for k, c in enumerate(order_entities):
                if k == i or k == j:
                    continue
                if pair_split(j, k) != "train":
                    continue
                split = pair_split(i, k)
                p1 = space.encode_proposition(a, "MAYOR_QUE", b)
                p2 = space.encode_proposition(b, "MAYOR_QUE", c)
                target = space.encode_proposition(a, "MAYOR_QUE", c)
                emit(split, [p1, p2], target, a, "obj", partials=[p1], sample=0.12)
                # Mismas cadenas con otros predicados de orden (solo ~30%): ensenan que
                # la regla es "encadenar y CONSERVAR la relacion", no la palabra MAYOR_QUE.
                if rng.random() < 0.3:
                    other = rng.choice(["MENOR_QUE", "SUPERIOR_A"])
                    add(split, [space.encode_proposition(a, other, b), space.encode_proposition(b, other, c)],
                        space.encode_proposition(a, other, c), "order_variants")

    # Regla 1b (parche-7): cadenas de varios pasos. Tres aristas train A>B, B>C,
    # C>D => A>D (entrenamiento/val/test, el par A>D decide el split). Cadenas de
    # CUATRO aristas (A>E) aparecen SOLO en test: miden si la red extrapola a una
    # longitud que nunca vio.
    n = len(order_entities)
    chains3, chains4 = [], []
    for a in range(n):
        for b in range(n):
            if b == a or pair_split(a, b) != "train":
                continue
            for c in range(n):
                if c in (a, b) or pair_split(b, c) != "train":
                    continue
                for d in range(n):
                    if d in (a, b, c) or pair_split(c, d) != "train":
                        continue
                    chains3.append((a, b, c, d))
                    for e in range(n):
                        if e in (a, b, c, d) or pair_split(d, e) != "train":
                            continue
                        if pair_split(a, e) == "test":
                            chains4.append((a, b, c, d, e))
    rng.shuffle(chains3)
    rng.shuffle(chains4)
    quota = {"train": 1500, "val": 120, "test": 200}
    taken = {"train": 0, "val": 0, "test": 0}
    current_rule[0] = "chain3"
    for a, b, c, d in chains3:
        split = pair_split(a, d)
        if taken[split] >= quota[split]:
            continue
        taken[split] += 1
        names = [order_entities[x] for x in (a, b, c, d)]
        props = [space.encode_proposition(names[i], "MAYOR_QUE", names[i + 1]) for i in range(3)]
        add(split, props, space.encode_proposition(names[0], "MAYOR_QUE", names[3]), "chain3")
        # Con una premisa irrelevante la secuencia llega a 4 posiciones: asi la 4a
        # posicion se entrena SIN ensenar cadenas de 4 (chain4 sigue siendo inedita).
        if rng.random() < 0.5:
            noisy = list(props)
            noisy.insert(rng.randint(0, 3), distractor(names[0], "obj"))
            add(split, noisy, space.encode_proposition(names[0], "MAYOR_QUE", names[3]), "chain3_distractor")
    current_rule[0] = "chain4"
    for chain in chains4[:150]:
        names = [order_entities[x] for x in chain]
        props = [space.encode_proposition(names[i], "MAYOR_QUE", names[i + 1]) for i in range(4)]
        add("test", props, space.encode_proposition(names[0], "MAYOR_QUE", names[4]), "chain4")

    # Regla 1c (parche-8): predicado nunca visto. Misma estructura que la
    # transitividad pero con ANTERIOR_A / POSTERIOR_A, que NO aparecen en ningun
    # ejemplo de train/val. Solo test. Mide si la red aplico la estructura
    # ("encadenar y conservar la relacion") o memorizo la palabra MAYOR_QUE.
    current_rule[0] = "unseen_predicate"
    novel = [(a, b, c) for a in range(n) for b in range(n) for c in range(n)
             if len({a, b, c}) == 3 and pair_split(a, b) == "train" and pair_split(b, c) == "train"
             and pair_split(a, c) == "test"]
    rng.shuffle(novel)
    for k, (a, b, c) in enumerate(novel[:120]):
        pred = "POSTERIOR_A" if k % 2 == 0 else "ANTERIOR_A"
        names = [order_entities[x] for x in (a, b, c)]
        props = [space.encode_proposition(names[0], pred, names[1]),
                 space.encode_proposition(names[1], pred, names[2])]
        add("test", props, space.encode_proposition(names[0], pred, names[2]), "unseen_predicate")

    # Regla 1d (parche-10): herencia de propiedades con DOS predicados distintos.
    #   x HEREDA p, p IMPLICA q  =>  x HEREDA q      (train/val)
    # El predicado de la conclusion viene de la 1a premisa y no de la 2a, y si el
    # termino medio NO coincide ("nojoin") no hay conclusion.
    # En TEST se usa la misma estructura con predicados (TIENE_RASGO, PRODUCE) y
    # entidades (IND_N_*, PROP_N_*) que no existen en train/val.
    names = space.concept_to_id
    inds = sorted(k for k in names if k.startswith("IND_") and "_N_" not in k)
    props_old = sorted(k for k in names if k.startswith("PROP_") and "_N_" not in k)
    inds_new = sorted(k for k in names if k.startswith("IND_N_"))
    props_new = sorted(k for k in names if k.startswith("PROP_N_"))

    def inherit(split, x, p, q, hp, ha, tag, other=None):
        """La REGLA viaja como premisa: (hp REGLA_HEREDA ha) declara que, si
        x hp p  y  p ha q, entonces x hp q. Sin esa premisa no hay conclusion."""
        enc = space.encode_proposition
        first, second, rule = enc(x, hp, p), enc(p, ha, q), enc(hp, "REGLA_HEREDA", ha)
        none = enc(x, "SIN_CONCLUSION", "NINGUNA")
        label = "inherit_" + tag
        if tag == "base":
            add(split, [first, second, rule], enc(x, hp, q), label)
        elif tag == "swapped":
            props_ = [first, second, rule]
            rng.shuffle(props_)
            add(split, props_, enc(x, hp, q), label)
        elif tag == "nojoin":
            add(split, [first, enc(other, ha, q), rule], none, label)
        elif tag == "norule":
            add(split, [first, second], none, label)
        elif tag == "insufficient":
            add(split, [first, rule], none, label)

    current_rule[0] = "inherit"
    made = 0
    pair_choices = [("HEREDA", "IMPLICA"), ("POSEE", "CAUSA"), ("ADQUIERE", "DERIVA_EN"),
                    ("MUESTRA", "ORIGINA"), ("EXHIBE", "PROVOCA")]
    while made < 4500:
        x = rng.choice(inds)
        p, q, r = rng.sample(props_old, 3)
        split = "val" if (inds.index(x) * 7 + props_old.index(q) * 13) % 10 == 0 else "train"
        if split == "val" and made > 100 and rng.random() < 0.8:
            continue
        roll = rng.random()
        tag = ("base" if roll < 0.35 else "swapped" if roll < 0.5 else "nojoin" if roll < 0.75
               else "norule" if roll < 0.9 else "insufficient")
        hp, ha = rng.choice(pair_choices)
        inherit(split, x, p, q, hp, ha, tag, other=r)
        made += 1

    # nojoin tambien en transitividad (aristas train; el par a>d decide el split)
    current_rule[0] = "transitivity_nojoin"
    done, tries = 0, 0
    while done < 900 and tries < 60000:
        tries += 1
        a, b, c, d = rng.sample(range(n), 4)
        if pair_split(a, b) != "train" or pair_split(c, d) != "train":
            continue
        split = pair_split(a, d)
        add(split, [space.encode_proposition(order_entities[a], "MAYOR_QUE", order_entities[b]),
                    space.encode_proposition(order_entities[c], "MAYOR_QUE", order_entities[d])],
            space.encode_proposition(order_entities[a], "SIN_CONCLUSION", "NINGUNA"), "nojoin")
        done += 1

    current_rule[0] = "unseen_structure"
    for k in range(150):
        x = rng.choice(inds_new)
        p, q, r = rng.sample(props_new, 3)
        tag = "base" if k < 60 else "swapped" if k < 80 else "nojoin" if k < 115 else "norule"
        inherit("test", x, p, q, "TIENE_RASGO", "PRODUCE", tag, other=r)
        # etiqueta de test propia para no mezclarla con la de entrenamiento
        ex = splits["test"][-1]
        rule_of[id(ex)] = ("unseen_structure", "NUEVA_" + tag)

    # Regla 1e (parche-12): contradicciones.
    #   A>B, B>A        => A CONTRADICE B
    #   A>B, B>C, C>A   => A CONTRADICE A   (ciclo)
    # En train solo con aristas train; en val/test el par (a,b) decide el split.
    current_rule[0] = "contradiction"
    quotas = {"train": 700, "val": 70, "test": 100}
    got2 = {"train": 0, "val": 0, "test": 0}
    got3 = {"train": 0, "val": 0, "test": 0}
    enc_ = space.encode_proposition
    for _ in range(40000):
        a, b, c = rng.sample(range(n), 3)
        split = pair_split(a, b)
        if split == "train" and (pair_split(b, a) != "train"):
            continue
        A, B, C = order_entities[a], order_entities[b], order_entities[c]
        if got2[split] < quotas[split]:
            got2[split] += 1
            add(split, [enc_(A, "MAYOR_QUE", B), enc_(B, "MAYOR_QUE", A)], enc_(A, "CONTRADICE", B), "contradiction")
        if split == "train" and (pair_split(b, c) != "train" or pair_split(c, a) != "train"):
            continue
        if got3[split] < quotas[split]:
            got3[split] += 1
            add(split, [enc_(A, "MAYOR_QUE", B), enc_(B, "MAYOR_QUE", C), enc_(C, "MAYOR_QUE", A)],
                enc_(A, "CONTRADICE", A), "cycle")
        if all(got2[k] >= quotas[k] and got3[k] >= quotas[k] for k in quotas):
            break

    current_rule[0] = "fall"
    # Regla 2: objeto liberado en el aire y sometido a gravedad -> cae.
    for category, j, obj in object_entities:
        split = "test" if j % 8 == 0 else ("val" if j % 8 == 1 else "train")
        p1 = space.encode_proposition(obj, "LIBERADO_EN", "AIRE")
        p2 = space.encode_proposition(obj, "SOMETIDO_A", "GRAVEDAD")
        target = space.encode_proposition(obj, "CAE_HACIA", "SUELO")
        emit(split, [p1, p2], target, obj, "obj", partials=[p1, p2])

    current_rule[0] = "melting"
    # Regla 3: exposicion termica de una sustancia fundible -> estado liquido.
    for category, j, substance in meltables:
        split = "test" if j % 8 == 0 else ("val" if j % 8 == 1 else "train")
        p1 = space.encode_proposition(substance, "EXPUESTO_A", "CALOR")
        p2 = space.encode_proposition(substance, "ES", "FUNDIBLE")
        target = space.encode_proposition(substance, "CAMBIA_A", "LIQUIDO")
        emit(split, [p1, p2], target, substance, "sub", partials=[p1, p2])

    # Reglas de cardinalidad con evidencia explicita. No se infiere que un
    # conjunto sea no numerable por el mero hecho de ser infinito.
    current_rule[0] = "finite"
    for j, set_name in finite_sets:
        split = "test" if j % 6 == 0 else ("val" if j % 6 == 1 else "train")
        premise = space.encode_proposition(set_name, "ES_FINITO", "TRUE")
        target = space.encode_proposition(set_name, "ES", "ENUMERABLE")
        emit(split, [premise], target, set_name, "set")

    current_rule[0] = "countable"
    for j, set_name in countable_sets:
        split = "test" if j % 6 == 0 else ("val" if j % 6 == 1 else "train")
        p1 = space.encode_proposition(set_name, "ES_INFINITO", "TRUE")
        p2 = space.encode_proposition(set_name, "TIENE_BIYECCION_CON", "NATURALES")
        target = space.encode_proposition(set_name, "ES", "INFINITO_NUMERABLE")
        emit(split, [p1, p2], target, set_name, "set", partials=[p1])

    current_rule[0] = "uncountable"
    for j, set_name in uncountable_sets:
        split = "test" if j % 6 == 0 else ("val" if j % 6 == 1 else "train")
        p1 = space.encode_proposition(set_name, "ES_INFINITO", "TRUE")
        p2 = space.encode_proposition(set_name, "NO_TIENE_BIYECCION_CON", "NATURALES")
        target = space.encode_proposition(set_name, "ES", "INNUMERABLE")
        emit(split, [p1, p2], target, set_name, "set", partials=[p1])

    # Equilibrado SOLO del entrenamiento: la transitividad aporta ~2000 muestras
    # y las demas reglas decenas; se repiten las minoritarias (sin tocar val/test).
    by_rule = {}
    for ex in splits["train"]:
        by_rule.setdefault(rule_of[id(ex)][0], []).append(ex)
    target_size = max(len(v) for v in by_rule.values()) // 3
    balanced = []
    for rule, exs in by_rule.items():
        reps = 1 if rule in ("transitivity", "chain3", "inherit", "transitivity_nojoin", "contradiction") else max(1, round(target_size / len(exs)))
        balanced.extend(exs * reps)
    splits["train"] = balanced

    datasets = {}
    for split, examples in splits.items():
        if not examples:
            raise RuntimeError(f"El split {split} ha quedado vacio.")
        seqs = torch.stack([item[0] for item in examples])
        masks = torch.stack([item[1] for item in examples])
        targets = torch.stack([item[2] for item in examples])
        datasets[split] = TensorDataset(seqs, masks, targets)
        datasets[split].tags = [rule_of[id(item)] for item in examples]  # (regla, variante)
    return datasets


def main():
    print("[*] Iteracion de ontologia y datos composicionales")
    os.makedirs("data", exist_ok=True)
    (space, order_entities, object_entities, meltables,
     finite_sets, countable_sets, uncountable_sets) = build_ontology()
    datasets = build_datasets(space, order_entities, object_entities, meltables,
                              finite_sets, countable_sets, uncountable_sets)

    with open("data/concept_space.pkl", "wb") as handle:
        pickle.dump(space, handle, protocol=pickle.HIGHEST_PROTOCOL)
    filenames = {
        "train": "concept_train_dataset.pkl",
        "val": "concept_val_dataset.pkl",
        "test": "concept_test_dataset.pkl",
    }
    for split, dataset in datasets.items():
        with open(os.path.join("data", filenames[split]), "wb") as handle:
            pickle.dump(dataset, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # Alias compatible con scripts antiguos que esperaban concept_dataset.pkl.
    with open("data/concept_dataset.pkl", "wb") as handle:
        pickle.dump(datasets["train"], handle, protocol=pickle.HIGHEST_PROTOCOL)

    manifest = {
        "schema_version": 2,
        "d_concept": D_CONCEPT,
        "max_premises": MAX_PREMISES,
        "concepts": len(space.concept_to_id),
        "propositions": len(space.proposition_vectors),
        "samples": {k: len(v) for k, v in datasets.items()},
        "split_policy": "Transitivity: target pair sets the split; both premise pairs must belong to train, preventing val/test target edges from appearing as training inputs. Other rules hold out complete entity instances.",
        "semantic_note": "Explicit feature ontology with role-bound proposition vectors; not pretrained language semantics.",
    }
    with open("data/dataset_manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    print(f"[+] Conceptos: {manifest['concepts']} | proposiciones: {manifest['propositions']}")
    print("[+] Muestras: " + " | ".join(f"{k}={len(v)}" for k, v in datasets.items()))
    print("[+] Ontologia y datasets guardados en data/.")


if __name__ == "__main__":
    main()

