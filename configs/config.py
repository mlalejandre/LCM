from dataclasses import dataclass
import torch


def default_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


@dataclass
class LCMConfig:
    d_concept: int = 128
    n_layers: int = 4
    n_heads: int = 4
    max_concept_seq: int = 4
    dropout: float = 0.05
    device: str = default_device()


@dataclass
class TrainConfig:
    batch_size: int = 64
    learning_rate: float = 3e-4
    epochs: int = 40
    checkpoint_dir: str = "checkpoints"
    device: str = default_device()
    patience: int = 8
    grad_clip: float = 1.0
