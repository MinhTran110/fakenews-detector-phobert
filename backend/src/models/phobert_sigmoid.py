"""
src/models/phobert_sigmoid.py
PhoBERT + Multi-Pooling + Dense + Sigmoid cho binary fake-news detection.
"""
import torch
import torch.nn as nn
from transformers import AutoModel
from omegaconf import DictConfig
import logging

logger = logging.getLogger(__name__)


class PoolingLayer(nn.Module):
    DIMS = {"cls": 768, "mean": 768, "cls_mean_max": 2304}

    def __init__(self, strategy: str = "cls_mean_max"):
        super().__init__()
        assert strategy in self.DIMS
        self.strategy = strategy

    @property
    def output_dim(self) -> int:
        return self.DIMS[self.strategy]

    def forward(self, hidden: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        cls = hidden[:, 0, :]
        if self.strategy == "cls":
            return cls

        expanded = mask.unsqueeze(-1).float()
        mean = (hidden * expanded).sum(1) / expanded.sum(1).clamp(min=1e-9)
        if self.strategy == "mean":
            return mean

        mx = hidden.masked_fill(mask.unsqueeze(-1) == 0, float("-inf")).max(1).values
        return torch.cat([cls, mean, mx], dim=-1)


class ClassificationHead(nn.Module):
    def __init__(self, input_dim: int, dropout: float = 0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, 512),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(512, 128),
            nn.GELU(),
            nn.Dropout(dropout * 0.67),
            nn.Linear(128, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


class PhoBertSigmoid(nn.Module):
    def __init__(self, cfg: DictConfig):
        super().__init__()
        self.bert = AutoModel.from_pretrained(
            cfg.model.pretrained,
            hidden_dropout_prob=cfg.model.hidden_dropout,
            attention_probs_dropout_prob=cfg.model.hidden_dropout,
        )
        self._freeze_layers(cfg.model.freeze_layers)
        self.pooling    = PoolingLayer(cfg.model.pooling)
        self.classifier = ClassificationHead(
            self.pooling.output_dim,
            cfg.model.classifier_dropout,
        )
        logger.info(
            f"PhoBertSigmoid | pooling={cfg.model.pooling} "
            f"| frozen={cfg.model.freeze_layers} | {self._count_params()}"
        )

    def _freeze_layers(self, n: int):
        if n <= 0:
            return
        for p in self.bert.embeddings.parameters():
            p.requires_grad = False
        for layer in self.bert.encoder.layer[:n]:
            for p in layer.parameters():
                p.requires_grad = False

    def _count_params(self) -> str:
        total     = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return f"{trainable/1e6:.1f}M trainable / {total/1e6:.1f}M total"

    def forward(self, input_ids: torch.Tensor,
                attention_mask: torch.Tensor) -> torch.Tensor:
        out    = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = self.pooling(out.last_hidden_state, attention_mask)
        return self.classifier(pooled)

    def get_param_groups(self, lr_bert: float, lr_head: float) -> list:
        bert_params = [p for p in self.bert.parameters() if p.requires_grad]
        head_params = (
            list(self.pooling.parameters()) +
            list(self.classifier.parameters())
        )
        return [
            {"params": bert_params, "lr": lr_bert},
            {"params": head_params, "lr": lr_head},
        ]
