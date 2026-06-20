"""src/training/trainer.py"""
import os, time, logging
import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.utils.tensorboard import SummaryWriter
from transformers import get_linear_schedule_with_warmup
from omegaconf import DictConfig, OmegaConf

logger = logging.getLogger(__name__)


def compute_metrics(logits: torch.Tensor, labels: torch.Tensor,
                    threshold: float = 0.5) -> dict:
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    import numpy as np

    probs = torch.sigmoid(logits).numpy()
    preds = (probs >= threshold).astype(int)
    y     = labels.numpy().astype(int)

    return {
        "accuracy":  accuracy_score(y, preds),
        "f1_macro":  f1_score(y, preds, average="macro", zero_division=0),
        "f1_fake":   f1_score(y, preds, pos_label=1, average="binary", zero_division=0),
        "auc":       roc_auc_score(y, probs) if len(np.unique(y)) == 2 else 0.0,
    }


class EarlyStopping:
    def __init__(self, patience: int = 3):
        self.patience = patience
        self.best     = -float("inf")
        self.counter  = 0
        self.should_stop = False

    def step(self, value: float) -> bool:
        if value > self.best:
            self.best    = value
            self.counter = 0
            return True
        self.counter += 1
        if self.counter >= self.patience:
            self.should_stop = True
        return False


class Trainer:
    def __init__(self, cfg: DictConfig, model: nn.Module,
                 train_loader, val_loader,
                 pos_weight: torch.Tensor | None = None):
        self.cfg   = cfg
        self.model = model
        self.train_loader = train_loader
        self.val_loader   = val_loader

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Device: {self.device}")
        self.model.to(self.device)

        if pos_weight is not None:
            pos_weight = pos_weight.to(self.device)
        self.criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

        self.optimizer = AdamW(
            model.get_param_groups(
                cfg.training.learning_rate_bert,
                cfg.training.learning_rate_head,
            ),
            weight_decay=cfg.training.weight_decay,
        )

        total_steps  = len(train_loader) * cfg.training.num_epochs
        warmup_steps = int(total_steps * cfg.training.warmup_ratio)
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer, warmup_steps, total_steps
        )

        self.scaler      = GradScaler(enabled=cfg.training.fp16)
        self.early_stop  = EarlyStopping(cfg.training.early_stopping_patience)
        self.global_step = 0
        self.best_ckpt   = None

        os.makedirs(cfg.logging.log_dir, exist_ok=True)
        self.writer = SummaryWriter(cfg.logging.log_dir)

    def _train_epoch(self, epoch: int) -> float:
        self.model.train()
        total_loss = 0.0
        accum      = self.cfg.training.gradient_accumulation_steps
        self.optimizer.zero_grad()

        for step, batch in enumerate(self.train_loader):
            ids    = batch["input_ids"].to(self.device)
            mask   = batch["attention_mask"].to(self.device)
            labels = batch["label"].to(self.device)

            with autocast(enabled=self.cfg.training.fp16):
                logits = self.model(ids, mask)
                loss   = self.criterion(logits, labels) / accum

            self.scaler.scale(loss).backward()

            if (step + 1) % accum == 0:
                self.scaler.unscale_(self.optimizer)
                nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.cfg.training.max_grad_norm,
                )
                self.scaler.step(self.optimizer)
                self.scaler.update()
                self.scheduler.step()
                self.optimizer.zero_grad()
                self.global_step += 1

            total_loss += loss.item() * accum

            if (step + 1) % self.cfg.logging.log_steps == 0:
                avg = total_loss / (step + 1)
                lr  = self.scheduler.get_last_lr()[0]
                logger.info(
                    f"Epoch {epoch} | step {step+1}/{len(self.train_loader)} "
                    f"| loss={avg:.4f} | lr={lr:.2e}"
                )
                self.writer.add_scalar("train/loss", avg, self.global_step)
                self.writer.add_scalar("train/lr",   lr,  self.global_step)

        return total_loss / len(self.train_loader)

    @torch.no_grad()
    def _evaluate(self) -> dict:
        self.model.eval()
        all_logits, all_labels = [], []

        for batch in self.val_loader:
            ids    = batch["input_ids"].to(self.device)
            mask   = batch["attention_mask"].to(self.device)
            with autocast(enabled=self.cfg.training.fp16):
                logits = self.model(ids, mask)
            all_logits.append(logits.cpu())
            all_labels.append(batch["label"])

        logits  = torch.cat(all_logits)
        labels  = torch.cat(all_labels)
        loss    = self.criterion(logits, labels.to(self.device)).item()
        metrics = compute_metrics(logits, labels, self.cfg.inference.threshold)
        metrics["loss"] = loss
        return metrics

    def train(self) -> str | None:
        os.makedirs(self.cfg.training.output_dir, exist_ok=True)
        logger.info("=" * 55)
        logger.info("Training: PhoBERT + Dense + Sigmoid")
        logger.info("=" * 55)

        for epoch in range(1, self.cfg.training.num_epochs + 1):
            t0          = time.time()
            train_loss  = self._train_epoch(epoch)
            val_metrics = self._evaluate()
            elapsed     = time.time() - t0
            f1          = val_metrics["f1_macro"]

            logger.info(
                f"Epoch {epoch}/{self.cfg.training.num_epochs} "
                f"| train_loss={train_loss:.4f} "
                f"| val_loss={val_metrics['loss']:.4f} "
                f"| val_f1={f1:.4f} "
                f"| val_auc={val_metrics['auc']:.4f} "
                f"| {elapsed:.0f}s"
            )
            for k, v in val_metrics.items():
                self.writer.add_scalar(f"val/{k}", v, epoch)

            if self.early_stop.step(f1):
                ckpt = os.path.join(self.cfg.training.output_dir, "best_model")
                os.makedirs(ckpt, exist_ok=True)
                self.model.bert.save_pretrained(ckpt)
                torch.save({
                    "epoch":       epoch,
                    "model_state": self.model.state_dict(),
                    "val_metrics": val_metrics,
                }, os.path.join(ckpt, "trainer_state.pt"))
                OmegaConf.save(self.cfg, os.path.join(ckpt, "config.yaml"))
                self.best_ckpt = ckpt
                logger.info(f"  Saved best model (f1={f1:.4f})")

            if self.early_stop.should_stop:
                logger.info(f"Early stopping at epoch {epoch}")
                break

        self.writer.close()
        return self.best_ckpt
