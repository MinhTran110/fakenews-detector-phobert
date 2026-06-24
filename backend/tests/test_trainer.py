# tests/test_trainer.py
"""
Unit tests cho src/training/trainer.py

Phủ:
- compute_metrics (accuracy, f1, auc)
- EarlyStopping (improve / no-improve / should_stop)
- Trainer._train_epoch (mock model + dataloader)
- Trainer._evaluate  (mock model + dataloader)
- Trainer.train      (end-to-end với dữ liệu giả)
"""
import os
import pytest
import torch
import torch.nn as nn
from unittest.mock import MagicMock, patch, call
from omegaconf import OmegaConf

from src.training.trainer import compute_metrics, EarlyStopping, Trainer


# ── compute_metrics ───────────────────────────────────────────────────────────

class TestComputeMetrics:
    def _make(self, probs, labels, threshold=0.5):
        logits = torch.log(torch.tensor(probs) / (1 - torch.tensor(probs) + 1e-9))
        return compute_metrics(logits, torch.tensor(labels, dtype=torch.float), threshold)

    def test_perfect_prediction(self):
        probs  = [0.9, 0.1, 0.9, 0.1]
        labels = [1,   0,   1,   0  ]
        m = self._make(probs, labels)
        assert m["accuracy"] == 1.0
        assert m["f1_macro"] == 1.0
        assert m["auc"]      == 1.0

    def test_all_wrong_prediction(self):
        probs  = [0.1, 0.9, 0.1, 0.9]
        labels = [1,   0,   1,   0  ]
        m = self._make(probs, labels)
        assert m["accuracy"] == 0.0

    def test_returns_all_keys(self):
        probs  = [0.7, 0.3, 0.6, 0.4]
        labels = [1,   0,   1,   0  ]
        m = self._make(probs, labels)
        assert all(k in m for k in ["accuracy", "f1_macro", "f1_fake", "auc"])

    def test_auc_zero_when_single_class(self):
        """AUC trả về 0.0 khi chỉ có 1 class trong labels."""
        probs  = [0.7, 0.6, 0.8]
        labels = [1,   1,   1  ]   # tất cả là fake
        m = self._make(probs, labels)
        assert m["auc"] == 0.0

    def test_custom_threshold(self):
        # threshold=0.3 → dễ predict FAKE hơn
        probs  = [0.4, 0.2]
        labels = [1,   0  ]
        m = self._make(probs, labels, threshold=0.3)
        # 0.4 >= 0.3 → FAKE ✓ ; 0.2 < 0.3 → REAL ✓
        assert m["accuracy"] == 1.0


# ── EarlyStopping ─────────────────────────────────────────────────────────────

class TestEarlyStopping:
    def test_improves_resets_counter(self):
        es = EarlyStopping(patience=3)
        assert es.step(0.5) is True   # first call → always improves
        assert es.counter   == 0

    def test_no_improve_increments_counter(self):
        es = EarlyStopping(patience=3)
        es.step(0.8)          # best = 0.8
        es.step(0.7)          # no improve
        assert es.counter == 1
        assert es.should_stop is False

    def test_stops_after_patience(self):
        es = EarlyStopping(patience=2)
        es.step(0.9)    # best
        es.step(0.5)    # counter=1
        es.step(0.5)    # counter=2 → should_stop=True
        assert es.should_stop is True

    def test_reset_on_new_best(self):
        es = EarlyStopping(patience=3)
        es.step(0.5)
        es.step(0.3)  # counter=1
        es.step(0.8)  # new best → counter reset
        assert es.counter    == 0
        assert es.should_stop is False

    def test_returns_true_only_on_best(self):
        es = EarlyStopping(patience=5)
        assert es.step(0.5) is True
        assert es.step(0.3) is False
        assert es.step(0.9) is True


# ── Trainer helpers ───────────────────────────────────────────────────────────

def make_fake_batch(batch_size=2, seq_len=16):
    return {
        "input_ids":      torch.zeros(batch_size, seq_len, dtype=torch.long),
        "attention_mask": torch.ones(batch_size,  seq_len, dtype=torch.long),
        "label":          torch.tensor([0.0, 1.0][:batch_size]),
    }


class TinyModel(nn.Module):
    """Mô hình cực nhỏ thay thế PhoBERT để test Trainer nhanh."""
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(16, 1)

    def forward(self, input_ids, attention_mask):
        x = input_ids.float().mean(dim=1)   # (batch, 16)
        return self.linear(x).squeeze(-1)   # (batch,)

    def get_param_groups(self, lr_bert, lr_head):
        return [{"params": self.parameters(), "lr": lr_bert}]


def make_mock_loader(n_batches=3):
    """DataLoader giả trả về n batch."""
    batches = [make_fake_batch() for _ in range(n_batches)]
    loader  = MagicMock()
    loader.__iter__ = MagicMock(return_value=iter(batches))
    loader.__len__  = MagicMock(return_value=n_batches)
    return loader


# ── Trainer unit tests ────────────────────────────────────────────────────────

class TestTrainer:
    @pytest.fixture
    def cfg(self, tmp_path):
        return OmegaConf.create({
            "training": {
                "output_dir":                  str(tmp_path / "ckpt"),
                "num_epochs":                  2,
                "train_batch_size":            2,
                "eval_batch_size":             2,
                "learning_rate_bert":          1e-3,
                "learning_rate_head":          1e-3,
                "warmup_ratio":                0.0,
                "weight_decay":                0.0,
                "max_grad_norm":               1.0,
                "fp16":                        False,
                "gradient_accumulation_steps": 1,
                "early_stopping_patience":     5,
                "pos_weight":                  None,
            },
            "inference": {"threshold": 0.5},
            "logging":   {"log_dir": str(tmp_path / "logs"), "log_steps": 1},
        })

    @pytest.fixture
    def trainer(self, cfg):
        model        = TinyModel()
        train_loader = make_mock_loader(3)
        val_loader   = make_mock_loader(2)
        return Trainer(cfg, model, train_loader, val_loader)

    def test_train_epoch_returns_float(self, trainer):
        loss = trainer._train_epoch(epoch=1)
        assert isinstance(loss, float)
        assert loss >= 0.0

    def test_evaluate_returns_dict_with_metrics(self, trainer):
        metrics = trainer._evaluate()
        assert all(k in metrics for k in ["accuracy", "f1_macro", "f1_fake", "auc", "loss"])

    def test_full_train_saves_checkpoint(self, cfg, tmp_path):
        """train() phải lưu checkpoint khi f1 cải thiện."""
        model        = TinyModel()
        train_loader = make_mock_loader(4)
        val_loader   = make_mock_loader(2)

        # Patch SummaryWriter để không tạo file tensorboard thật
        with patch("src.training.trainer.SummaryWriter"):
            trainer = Trainer(cfg, model, train_loader, val_loader)
            ckpt    = trainer.train()

        # best_ckpt phải được set và thư mục tồn tại
        assert ckpt is not None
        assert os.path.isdir(ckpt)

    def test_early_stopping_triggered(self, tmp_path):
        """Với patience=1, training dừng sớm nếu f1 không cải thiện."""
        cfg = OmegaConf.create({
            "training": {
                "output_dir":                  str(tmp_path / "ckpt"),
                "num_epochs":                  10,  # nhiều epoch nhưng sẽ dừng sớm
                "train_batch_size":            2,
                "eval_batch_size":             2,
                "learning_rate_bert":          1e-3,
                "learning_rate_head":          1e-3,
                "warmup_ratio":                0.0,
                "weight_decay":                0.0,
                "max_grad_norm":               1.0,
                "fp16":                        False,
                "gradient_accumulation_steps": 1,
                "early_stopping_patience":     1,   # dừng ngay sau 1 epoch không cải thiện
                "pos_weight":                  None,
            },
            "inference": {"threshold": 0.5},
            "logging":   {"log_dir": str(tmp_path / "logs"), "log_steps": 99},
        })

        # Tạo model luôn predict 0 → f1 không thay đổi sau epoch 1
        model        = TinyModel()
        train_loader = make_mock_loader(2)
        val_loader   = make_mock_loader(2)

        epoch_count = []
        with patch("src.training.trainer.SummaryWriter"):
            trainer = Trainer(cfg, model, train_loader, val_loader)
            original_train_epoch = trainer._train_epoch

            def track_epoch(epoch):
                epoch_count.append(epoch)
                return original_train_epoch(epoch)

            trainer._train_epoch = track_epoch
            trainer.train()

        # Với patience=1, phải dừng trước epoch 10
        assert len(epoch_count) < 10
