"""src/data/dataset.py"""
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from omegaconf import DictConfig
import logging

logger = logging.getLogger(__name__)


class FakeNewsDataset(Dataset):
    def __init__(self, df: pd.DataFrame, tokenizer, text_col: str,
                 label_col: str, max_length: int = 256):
        self.texts      = df[text_col].tolist()
        self.labels     = df[label_col].astype(float).tolist()
        self.tokenizer  = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids":      enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "label":          torch.tensor(self.labels[idx], dtype=torch.float),
        }


def build_dataloaders(cfg: DictConfig, tokenizer):
    train_df = pd.read_csv(cfg.data.train_path)
    val_df   = pd.read_csv(cfg.data.val_path)
    test_df  = pd.read_csv(cfg.data.test_path)

    kw = dict(
        tokenizer=tokenizer,
        text_col=cfg.data.text_col,
        label_col=cfg.data.label_col,
        max_length=cfg.data.max_length,
    )
    train_loader = DataLoader(
        FakeNewsDataset(train_df, **kw),
        batch_size=cfg.training.train_batch_size,
        shuffle=True, num_workers=2, pin_memory=True,
    )
    val_loader = DataLoader(
        FakeNewsDataset(val_df, **kw),
        batch_size=cfg.training.eval_batch_size,
        shuffle=False, num_workers=2, pin_memory=True,
    )
    test_loader = DataLoader(
        FakeNewsDataset(test_df, **kw),
        batch_size=cfg.training.eval_batch_size,
        shuffle=False, num_workers=2, pin_memory=True,
    )

    # pos_weight cho BCEWithLogitsLoss
    pos_weight = None
    if cfg.training.pos_weight is None:
        labels = train_df[cfg.data.label_col].values.astype(float)
        n_neg, n_pos = (labels == 0).sum(), (labels == 1).sum()
        pw = n_neg / max(n_pos, 1)
        pos_weight = torch.tensor([pw], dtype=torch.float)
        logger.info(f"pos_weight={pw:.3f} (n_neg={n_neg}, n_pos={n_pos})")

    logger.info(
        f"Dataset → train:{len(train_df)} val:{len(val_df)} test:{len(test_df)}"
    )
    return train_loader, val_loader, test_loader, pos_weight
