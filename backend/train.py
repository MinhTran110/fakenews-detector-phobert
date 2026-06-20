"""
train.py — Entry point huấn luyện model

Chạy:
    python train.py
    python train.py training.num_epochs=10
    python train.py model.freeze_layers=0
    python train.py inference.threshold=0.4
"""
import logging, os, sys
import torch
from omegaconf import OmegaConf
from transformers import AutoTokenizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.preprocessing import run_preprocessing
from src.data.dataset       import build_dataloaders
from src.models.phobert_sigmoid import PhoBertSigmoid
from src.training.trainer   import Trainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def evaluate_test(cfg, model, test_loader):
    """Đánh giá trên test set và vẽ biểu đồ."""
    import torch
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.metrics import (
        classification_report, confusion_matrix, roc_curve, auc
    )
    from torch.cuda.amp import autocast

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device).eval()

    all_logits, all_labels = [], []
    with torch.no_grad():
        for batch in test_loader:
            ids  = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            with autocast(enabled=cfg.training.fp16):
                logits = model(ids, mask)
            all_logits.append(logits.cpu())
            all_labels.append(batch["label"])

    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels)
    probs  = torch.sigmoid(logits).numpy()
    preds  = (probs >= cfg.inference.threshold).astype(int)
    y      = labels.numpy().astype(int)

    # Report
    report = classification_report(y, preds, target_names=["Real", "Fake"])
    logger.info(f"\nTest Classification Report:\n{report}")

    # Confusion matrix
    os.makedirs("logs/evaluation", exist_ok=True)
    cm = confusion_matrix(y, preds)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Real","Fake"],
                yticklabels=["Real","Fake"], ax=axes[0])
    axes[0].set_title("Confusion Matrix")
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("Actual")

    # ROC curve
    fpr, tpr, _ = roc_curve(y, probs)
    roc_auc = auc(fpr, tpr)
    axes[1].plot(fpr, tpr, label=f"AUC = {roc_auc:.4f}", linewidth=2)
    axes[1].plot([0,1], [0,1], "k--", linewidth=1)
    axes[1].set_xlabel("FPR")
    axes[1].set_ylabel("TPR")
    axes[1].set_title("ROC Curve")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig("logs/evaluation/test_results.png", dpi=150)
    plt.close()
    logger.info("Saved logs/evaluation/test_results.png")

    # Prob distribution
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(probs[y==0], bins=40, alpha=0.6, label="Real", color="#22c55e")
    ax.hist(probs[y==1], bins=40, alpha=0.6, label="Fake", color="#ef4444")
    ax.axvline(cfg.inference.threshold, color="gray",
               linestyle="--", label=f"threshold={cfg.inference.threshold}")
    ax.set_xlabel("P(fake)")
    ax.set_ylabel("Count")
    ax.set_title("Probability Distribution")
    ax.legend()
    plt.tight_layout()
    plt.savefig("logs/evaluation/prob_distribution.png", dpi=150)
    plt.close()
    logger.info("Saved logs/evaluation/prob_distribution.png")


def main():
    cfg = OmegaConf.merge(
        OmegaConf.load("configs/config.yaml"),
        OmegaConf.from_cli(),
    )
    logger.info("\n" + OmegaConf.to_yaml(cfg))

    torch.manual_seed(cfg.data.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(cfg.data.seed)
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")

    # Preprocessing (bỏ qua nếu đã split rồi)
    import os
    if not os.path.exists(cfg.data.train_path):
        logger.info("Processed data not found, running preprocessing...")
        run_preprocessing(
            cfg,
            raw_path="data/raw/dataset.csv",   # đường dẫn file raw của bạn
            title_col="title",
            content_col="content",
        )

    tokenizer = AutoTokenizer.from_pretrained(cfg.model.pretrained)
    train_loader, val_loader, test_loader, pos_weight = build_dataloaders(
        cfg, tokenizer
    )

    model    = PhoBertSigmoid(cfg)
    trainer  = Trainer(cfg, model, train_loader, val_loader, pos_weight)
    best_dir = trainer.train()

    logger.info("\nEvaluating on test set...")
    evaluate_test(cfg, model, test_loader)


if __name__ == "__main__":
    main()
