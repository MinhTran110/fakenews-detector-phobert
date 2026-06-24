# tests/conftest.py
"""
Shared pytest fixtures cho toàn bộ test suite.
"""
import os
import sys
import pytest
import pandas as pd
import torch
from unittest.mock import MagicMock, patch
from omegaconf import OmegaConf

# Đảm bảo import từ thư mục backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Config fixture ────────────────────────────────────────────────────────────

@pytest.fixture
def base_cfg():
    """OmegaConf config tối thiểu dùng trong test (không cần file YAML thật)."""
    return OmegaConf.create({
        "data": {
            "train_path": "data/processed/train.csv",
            "val_path":   "data/processed/val.csv",
            "test_path":  "data/processed/test.csv",
            "text_col":   "text",
            "label_col":  "label",
            "max_length": 64,   # nhỏ để test nhanh
            "val_size":   0.15,
            "test_size":  0.15,
            "seed":       42,
        },
        "model": {
            "pretrained":         "vinai/phobert-base-v2",
            "pooling":            "cls_mean_max",
            "freeze_layers":      0,
            "hidden_dropout":     0.1,
            "classifier_dropout": 0.3,
        },
        "training": {
            "output_dir":                  "checkpoints",
            "num_epochs":                  2,
            "train_batch_size":            2,
            "eval_batch_size":             2,
            "learning_rate_bert":          2e-5,
            "learning_rate_head":          1e-4,
            "warmup_ratio":                0.1,
            "weight_decay":                0.01,
            "max_grad_norm":               1.0,
            "fp16":                        False,
            "gradient_accumulation_steps": 1,
            "early_stopping_patience":     2,
            "pos_weight":                  None,
        },
        "inference": {
            "threshold": 0.5,
        },
        "logging": {
            "log_dir":   "logs/test",
            "log_steps": 10,
        },
    })


# ── Data fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    """DataFrame mẫu với 10 hàng để test."""
    return pd.DataFrame({
        "text":  [
            "Chính phủ thông báo chính sách mới về giáo dục",
            "Tin giả: thuốc chữa ung thư bằng lá cây",
            "Bộ Y tế khuyến cáo người dân tiêm vaccine",
            "Khoa học gia tìm ra phương pháp chữa mọi bệnh",
            "Thủ tướng ký quyết định tăng lương cơ sở",
            "Uống nước lá chữa COVID trong 3 ngày",
            "VN đứng đầu ASEAN về tăng trưởng kinh tế",
            "Người ngoài hành tinh đến Hà Nội gặp lãnh đạo",
            "Ngân hàng Nhà nước điều chỉnh lãi suất",
            "Bill Gates tiêm chip vào vaccine COVID",
        ],
        "label": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    })


@pytest.fixture
def sample_raw_df():
    """DataFrame với cột title + content riêng (chưa merge)."""
    return pd.DataFrame({
        "title":   ["Tiêu đề bài báo thật", "Tiêu đề tin giả"],
        "content": ["Nội dung bài báo thật rất dài", "Nội dung tin giả rất ngắn"],
        "label":   [0, 1],
    })


# ── Mock tokenizer fixture ────────────────────────────────────────────────────

@pytest.fixture
def mock_tokenizer():
    """Mock tokenizer trả về tensor giả mà không cần download model."""
    tok = MagicMock()

    def _tokenize(text, max_length=64, padding=None,
                  truncation=None, return_tensors=None):
        """Trả về tensor giả có shape chuẩn."""
        result = MagicMock()
        result.__getitem__ = lambda self, key: torch.zeros(1, max_length, dtype=torch.long)
        return result

    tok.side_effect = _tokenize
    tok.__call__ = _tokenize
    return tok


# ── Mock model fixture ────────────────────────────────────────────────────────

@pytest.fixture
def mock_phobert_model():
    """Mock AutoModel trả về hidden state giả."""
    model = MagicMock()
    # last_hidden_state shape: (batch, seq_len, 768)
    model.return_value.last_hidden_state = torch.randn(2, 64, 768)
    return model
