"""Evalua generalizacion neuronal (con baselines) y reglas simbolicas.

Importante: la similitud coseno media NO sirve sola. Los vectores objetivo
comparten componentes (mismos predicados/roles) y un predictor trivial ya
supera 0.95. La metrica fiable es la recuperacion exacta de la proposicion
correcta entre TODAS las proposiciones candidatas (sujeto+predicado+objeto).
"""
import json
import os
import pickle
from collections import defaultdict
import torch
import torch.nn.functional as F
from configs.config import LCMConfig
from src.model.reasoner import LatentReasoner
from src.reasoning.rule_engine import run_reference_tests


def _load_checkpoint(path, device):
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)


def _bank(space):
    labels = sorted(space.proposition_vectors)
    matrix = torch.stack([space.proposition_vectors[k] for k in labels])
    return labels, F.normalize(matrix, dim=-1)


def evaluate_neural(space, dataset, device, train_dataset=None):
    path = "checkpoints/lcm_reasoner.pt"
    if not os.path.exists(path):
        raise FileNotFoundError("No existe el checkpoint. Ejecuta primero scripts.train_reasoner.")
    ckpt = _load_checkpoint(path, device)
    saved = ckpt.get("config", {})
    config = LCMConfig(
        d_concept=space.d_concept,
        n_layers=int(saved.get("n_layers", 4)),
        n_heads=int(saved.get("n_heads", 4)),
        max_concept_seq=int(saved.get("max_concept_seq", 4)),
        dropout=float(saved.get("dropout", 0.05)),
        device=device,
    )
    model = LatentReasoner(config).to(device)
    model.set_space(space)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    seq, mask, target = dataset.tensors
    target = F.normalize(target, dim=-1)
    with torch.no_grad():
        pred, _ = model(seq.to(device), attention_mask=mask.to(device))
    pred = pred.cpu()

    labels, bank = _bank(space)
    true_idx = (target @ bank.T).argmax(dim=-1)
    pred_idx = (pred @ bank.T).argmax(dim=-1)
    true_parts = [space.proposition_parts[labels[i]] for i in true_idx.tolist()]
    pred_parts = [space.proposition_parts[labels[i]] for i in pred_idx.tolist()]

    n = len(true_parts)
    exact = sum(a == b for a, b in zip(true_parts, pred_parts)) / n
    role_acc = {
        name: sum(a[i] == b[i] for a, b in zip(true_parts, pred_parts)) / n
        for i, name in enumerate(("subject", "predicate", "object"))
    }
    per_rule = defaultdict(lambda: [0, 0])
    for a, b in zip(true_parts, pred_parts):
        per_rule[a[1]][0] += int(a == b)
        per_rule[a[1]][1] += 1

    tags = getattr(dataset, "tags", None)
    per_variant = defaultdict(lambda: [0, 0])
    if tags:
        for (rule, variant), a, b in zip(tags, true_parts, pred_parts):
            per_variant[variant][0] += int(a == b)
            per_variant[variant][1] += 1

    # Baselines que explican por que el coseno medio engana.
    baselines = {}
    if train_dataset is not None:
        mean_t = F.normalize(F.normalize(train_dataset.tensors[2], dim=-1).mean(0), dim=0)
        baselines["cos_mean_train_target"] = float((target @ mean_t).mean())
    last = torch.stack([seq[i, int(mask[i].sum()) - 1] for i in range(n)])
    baselines["cos_copy_last_premise"] = float(F.cosine_similarity(last, target, dim=-1).mean())
    baselines["exact_chance"] = 1.0 / len(labels)

    cos = F.cosine_similarity(pred, target, dim=-1)
    return {
        "n_test": n,
        "n_candidates": len(labels),
        "exact_match_top1": exact,
        "role_accuracy": role_acc,
        "per_variant": {k: {"exact": v[0] / v[1], "n": v[1]} for k, v in per_variant.items()},
        "per_predicate": {k: {"exact": v[0] / v[1], "n": v[1]} for k, v in per_rule.items()},
        "mean_cosine_similarity": float(cos.mean()),
        "p10_cosine_similarity": float(torch.quantile(cos, 0.10)),
        "baselines": baselines,
        "checkpoint_epoch": int(ckpt.get("epoch", -1)),
        "checkpoint_val_loss": ckpt.get("val_loss"),
        "interpretation": "Usa exact_match_top1 y per_predicate; el coseno solo es una metrica auxiliar.",
    }


def main():
    needed = ("data/concept_space.pkl", "data/concept_test_dataset.pkl")
    if not all(os.path.exists(p) for p in needed):
        raise FileNotFoundError("Ejecuta primero `python -m scripts.prepare_concepts`.")
    with open(needed[0], "rb") as h:
        space = pickle.load(h)
    with open(needed[1], "rb") as h:
        test_dataset = pickle.load(h)
    train_dataset = None
    if os.path.exists("data/concept_train_dataset.pkl"):
        with open("data/concept_train_dataset.pkl", "rb") as h:
            train_dataset = pickle.load(h)

    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    neural = evaluate_neural(space, test_dataset, device, train_dataset)
    symbolic = run_reference_tests()
    report = {"device": device, "neural_generalization": neural, "symbolic_reference_tests": symbolic}
    os.makedirs("reports", exist_ok=True)
    with open("reports/lcm_evaluation.json", "w", encoding="utf-8") as h:
        json.dump(report, h, ensure_ascii=False, indent=2)

    b = neural["baselines"]
    print("\n=== EVALUACION DE GENERALIZACION LCM ===")
    print(f"Dispositivo: {device} | muestras test: {neural['n_test']} | candidatos: {neural['n_candidates']}")
    print(f"EXACT MATCH top-1 (s,p,o):  {neural['exact_match_top1']:.2%}   (azar: {b['exact_chance']:.2%})")
    print("Acierto por rol: " + " | ".join(f"{k}={v:.1%}" for k, v in neural["role_accuracy"].items()))
    print("Por predicado:")
    for k, v in sorted(neural["per_predicate"].items()):
        print(f"  {k:<12} {v['exact']:.1%}  (n={v['n']})")
    if neural["per_variant"]:
        print("Por variante (base / swapped=orden alterado / distractor=premisa irrelevante / insufficient=sin evidencia / chain3=3 aristas / chain4=4 aristas NUNCA vistas / unseen_predicate=relacion nueva / NUEVA_*=regla y palabras nuevas (la regla viaja en las premisas) / norule=sin enunciar la regla / nojoin=premisas que no encajan):")
        for k, v in sorted(neural["per_variant"].items()):
            print(f"  {k:<13} {v['exact']:.1%}  (n={v['n']})")
    print(f"Coseno medio: {neural['mean_cosine_similarity']:.4f} | P10: {neural['p10_cosine_similarity']:.4f}")
    print(f"  baselines de coseno -> media-de-objetivos: {b.get('cos_mean_train_target', float('nan')):.4f}"
          f" | copiar-ultima-premisa: {b['cos_copy_last_premise']:.4f}")
    print(f"Pruebas simbolicas (verifican el RuleEngine, NO la red): {symbolic['passed']}/{symbolic['total']}")
    print("[+] Informe: reports/lcm_evaluation.json")
    if symbolic["passed"] != symbolic["total"]:
        raise SystemExit("Fallaron pruebas del motor simbolico de referencia.")


if __name__ == "__main__":
    main()
