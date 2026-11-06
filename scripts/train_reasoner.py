import os
import pickle
import torch
from torch.utils.data import DataLoader
from configs.config import LCMConfig, TrainConfig
from src.model.reasoner import LatentReasoner
from src.training.trainer import ConceptTrainer


def main():
    torch.manual_seed(int(os.environ.get("LCM_SEED", "0")))  # reproducibilidad
    required = ["data/concept_space.pkl", "data/concept_train_dataset.pkl"]
    missing = [path for path in required if not os.path.exists(path)]
    if missing:
        raise FileNotFoundError(
            "Faltan datos. Ejecuta primero `python -m scripts.prepare_concepts`. "
            + ", ".join(missing)
        )
    with open("data/concept_space.pkl", "rb") as handle:
        space = pickle.load(handle)
    with open("data/concept_train_dataset.pkl", "rb") as handle:
        train_dataset = pickle.load(handle)

    val_dataset = None
    if os.path.exists("data/concept_val_dataset.pkl"):
        with open("data/concept_val_dataset.pkl", "rb") as handle:
            val_dataset = pickle.load(handle)

    lcm_config = LCMConfig(
        d_concept=space.d_concept,
        max_concept_seq=4,
    )
    train_config = TrainConfig(
        batch_size=64,
        learning_rate=1e-3,
        epochs=80,
        patience=8,
    )
    train_loader = DataLoader(
        train_dataset, batch_size=train_config.batch_size, shuffle=True,
        pin_memory=(train_config.device == "cuda"),
    )
    val_loader = DataLoader(
        val_dataset, batch_size=128, shuffle=False,
        pin_memory=(train_config.device == "cuda"),
    ) if val_dataset is not None else None

    model = LatentReasoner(lcm_config)
    model.set_space(space)  # lector de ranuras: catalogo y matrices de rol
    trainer = ConceptTrainer(model, train_config, train_loader, val_loader)
    history = trainer.train()
    print(f"[+] Entrenamiento terminado. Epocas ejecutadas: {len(history)}")
    print("[+] Ejecuta `python -m scripts.evaluate_reasoner` para medir generalizacion.")


if __name__ == "__main__":
    main()

