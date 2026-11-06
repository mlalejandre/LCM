"""Prueba de estres: catalogo ABIERTO (conceptos anadidos DESPUES de entrenar).

Se registran conceptos que el modelo nunca vio ni siquiera como palabra en el
catalogo (algunos con solo rasgo de identidad) y se comprueban reglas con ellos,
sin reentrenar. La salida se decodifica con el lector de ranuras.
"""
import copy
import json
import os
import pickle
import random
import torch
from configs.config import LCMConfig
from src.model.reasoner import LatentReasoner


def load_model(base_space, space, device):
    path = "checkpoints/lcm_reasoner.pt"
    if not os.path.exists(path):
        raise FileNotFoundError("Falta el checkpoint. Ejecuta scripts.train_reasoner.")
    try:
        ckpt = torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        ckpt = torch.load(path, map_location=device)
    saved = ckpt.get("config", {})
    config = LCMConfig(d_concept=space.d_concept, n_layers=int(saved.get("n_layers", 4)),
                       n_heads=int(saved.get("n_heads", 4)), max_concept_seq=int(saved.get("max_concept_seq", 4)),
                       dropout=float(saved.get("dropout", 0.05)), device=device)
    model = LatentReasoner(config).to(device)
    model.set_space(base_space)  # catalogo del entrenamiento: encaja con el checkpoint
    model.load_state_dict(ckpt["model_state_dict"])
    model.set_space(space)       # ahora, el catalogo ampliado
    model.eval()
    return model


def infer(model, space, premises, device):
    vectors = [space.encode_proposition(*p) for p in premises]
    seq = torch.stack(vectors).unsqueeze(0).to(device)
    mask = torch.ones(1, seq.shape[1], dtype=torch.bool, device=device)
    with torch.no_grad():
        out, _ = model(seq, attention_mask=mask)
        s, p, o = model.read_slots(out.view(1, 1, -1))[0, 0].tolist()
    return tuple(space.id_to_concept[i] for i in (s, p, o))


def main():
    with open("data/concept_space.pkl", "rb") as handle:
        base_space = pickle.load(handle)
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    space = copy.deepcopy(base_space)
    n_before = len(space.concept_to_id)
    rng = random.Random(123)

    # Conceptos nuevos: la mitad con rasgos de familia, la mitad solo con identidad.
    order, objs, inds, props = [], [], [], []
    for i in range(8):
        nm = f"NUEVO_ORDEN_{i}"
        feats = ({"abstract_entity": 1, "ordered_domain": 0.4, f"identity:{nm}": 0.5} if i % 2 == 0 else None)
        space.add_concept(nm, features=feats, kind="entity"); order.append(nm)
        nm = f"NUEVO_OBJ_{i}"
        feats = ({"physical_object": 1, "category:FRUTA": 0.8, "movable": 0.5, f"identity:{nm}": 0.5} if i % 2 == 0 else None)
        space.add_concept(nm, features=feats, kind="entity"); objs.append(nm)
        nm = f"NUEVO_IND_{i}"
        space.add_concept(nm, features=({"individual": 1, f"identity:{nm}": 0.5} if i % 2 == 0 else None), kind="entity"); inds.append(nm)
        nm = f"NUEVO_PROP_{i}"
        space.add_concept(nm, features=({"property": 1, f"identity:{nm}": 0.5} if i % 2 == 0 else None), kind="entity"); props.append(nm)

    model = load_model(base_space, space, device)
    results = {}

    def run(name, cases):
        ok = sum(infer(model, space, prem, device) == exp for prem, exp in cases)
        results[name] = {"ok": ok, "total": len(cases)}

    cases = []
    for _ in range(40):
        a, b, c = rng.sample(order, 3)
        cases.append(([(a, "MAYOR_QUE", b), (b, "MAYOR_QUE", c)], (a, "MAYOR_QUE", c)))
    run("transitividad con conceptos nuevos", cases)

    cases = []
    for _ in range(40):
        a, b, c, d = rng.sample(order, 4)
        cases.append(([(a, "MAYOR_QUE", b), (b, "MAYOR_QUE", c), (c, "MAYOR_QUE", d)], (a, "MAYOR_QUE", d)))
    run("cadena de 3 aristas con conceptos nuevos", cases)

    cases = [([(o, "LIBERADO_EN", "AIRE"), (o, "SOMETIDO_A", "GRAVEDAD")], (o, "CAE_HACIA", "SUELO")) for o in objs]
    run("caida con objetos nuevos", cases)

    cases = []
    for _ in range(40):
        x = rng.choice(inds); p, q = rng.sample(props, 2)
        cases.append(([(x, "HEREDA", p), (p, "IMPLICA", q), ("HEREDA", "REGLA_HEREDA", "IMPLICA")], (x, "HEREDA", q)))
    run("herencia con individuos y propiedades nuevos", cases)

    cases = []
    for _ in range(40):
        x = rng.choice(inds); p, q, r = rng.sample(props, 3)
        cases.append(([(x, "HEREDA", p), (r, "IMPLICA", q), ("HEREDA", "REGLA_HEREDA", "IMPLICA")], (x, "SIN_CONCLUSION", "NINGUNA")))
    run("premisas que no encajan (conceptos nuevos)", cases)

    cases = []
    for _ in range(30):
        a, b = rng.sample(order, 2)
        cases.append(([(a, "MAYOR_QUE", b), (b, "MAYOR_QUE", a)], (a, "CONTRADICE", b)))
    run("contradiccion A>B, B>A (conceptos nuevos)", cases)

    cases = []
    for _ in range(30):
        a, b, c = rng.sample(order, 3)
        cases.append(([(a, "MAYOR_QUE", b), (b, "MAYOR_QUE", c), (c, "MAYOR_QUE", a)], (a, "CONTRADICE", a)))
    run("ciclo A>B>C>A (conceptos nuevos)", cases)

    print("\n=== PRUEBA DE ESTRES: CATALOGO ABIERTO ===")
    print(f"Conceptos al entrenar: {n_before} | anadidos despues: {len(space.concept_to_id) - n_before}")
    for name, r in results.items():
        print(f"  {r['ok'] / r['total']:7.1%}  ({r['ok']}/{r['total']})  {name}")
    os.makedirs("reports", exist_ok=True)
    with open("reports/lcm_stress.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
    print("[+] Informe: reports/lcm_stress.json")


if __name__ == "__main__":
    main()
