import os
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from configs.config import TrainConfig
from src.model.reasoner import LatentReasoner


class ConceptTrainer:
    def __init__(
        self,
        model: LatentReasoner,
        config: TrainConfig,
        loader: DataLoader,
        val_loader: DataLoader = None,
    ):
        self.config = config
        self.model = model.to(config.device)
        self.loader = loader
        self.val_loader = val_loader
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(), lr=config.learning_rate, weight_decay=1e-4
        )
        # Tasa de aprendizaje decreciente: evita los picos de perdida a mitad de entrenamiento.
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=config.epochs, eta_min=config.learning_rate * 0.02
        )
        os.makedirs(config.checkpoint_dir, exist_ok=True)
        self.best_val_loss = float("inf")

    @staticmethod
    def _unpack(batch):
        if len(batch) == 3:
            seq, mask, target = batch
        elif len(batch) == 2:  # Compatibilidad con datasets antiguos.
            seq, target = batch
            mask = torch.ones(seq.shape[:2], dtype=torch.bool)
        else:
            raise ValueError("Cada lote debe contener (secuencia, mascara, objetivo).")
        return seq, mask, target

    def _run_epoch(self, loader, training: bool) -> float:
        self.model.train(training)
        total_loss = 0.0
        total_items = 0
        context = torch.enable_grad() if training else torch.no_grad()
        with context:
            iterator = tqdm(loader, desc="Entrenando" if training else "Validando", leave=False)
            for batch in iterator:
                seq, mask, target = self._unpack(batch)
                seq = seq.to(self.config.device)
                mask = mask.to(self.config.device)
                target = target.to(self.config.device)
                _, loss = self.model(seq, target=target, attention_mask=mask)
                if loss is None or not torch.isfinite(loss):
                    raise RuntimeError("Loss no finita; revisa los datos y las mascaras.")
                if training:
                    self.optimizer.zero_grad(set_to_none=True)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.grad_clip)
                    self.optimizer.step()
                size = int(seq.shape[0])
                total_loss += float(loss.detach().item()) * size
                total_items += size
                iterator.set_postfix(loss=f"{loss.item():.4f}")
        return total_loss / max(total_items, 1)

    def save_checkpoint(self, epoch: int, train_loss: float, val_loss: float):
        path = os.path.join(self.config.checkpoint_dir, "lcm_reasoner.pt")
        tmp_path = path + ".tmp"
        torch.save({
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "train_loss": train_loss,
            "val_loss": val_loss,
            "config": {
                "d_concept": self.model.config.d_concept,
                "n_layers": self.model.config.n_layers,
                "n_heads": self.model.config.n_heads,
                "max_concept_seq": self.model.config.max_concept_seq,
                "dropout": self.model.config.dropout,
            },
        }, tmp_path)
        os.replace(tmp_path, path)

    def train(self):
        print(f"[*] Entrenamiento conceptual en [{self.config.device.upper()}]")
        history = []
        patience_left = self.config.patience
        for epoch in range(1, self.config.epochs + 1):
            train_loss = self._run_epoch(self.loader, training=True)
            val_loss = self._run_epoch(self.val_loader, training=False) if self.val_loader else train_loss
            self.scheduler.step()
            history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
            print(
                f"[E{epoch:03d}] train_loss={train_loss:.5f} | "
                f"val_loss={val_loss:.5f}"
            )
            improved = val_loss < (self.best_val_loss - 1e-6)
            if improved:
                self.best_val_loss = val_loss
                self.save_checkpoint(epoch, train_loss, val_loss)
                patience_left = self.config.patience
            else:
                patience_left -= 1
            if self.val_loader and patience_left <= 0:
                print("[*] Early stopping: la validacion no mejora.")
                break
        if not os.path.exists(os.path.join(self.config.checkpoint_dir, "lcm_reasoner.pt")):
            self.save_checkpoint(len(history), history[-1]["train_loss"], history[-1]["val_loss"])
        return history

