# tests/test_dataset.py
"""
Unit tests cho src/data/dataset.py

Phủ:
- FakeNewsDataset.__len__
- FakeNewsDataset.__getitem__ (shape, dtype)
- build_dataloaders (mock CSV files + pos_weight)
"""
import pytest
import pandas as pd
import torch
from unittest.mock import MagicMock, patch
from torch.utils.data import DataLoader

from src.data.dataset import FakeNewsDataset, build_dataloaders


# ── Mock tokenizer helper ─────────────────────────────────────────────────────

def make_tokenizer(max_length: int = 64):
    """Trả về callable giả lập tokenizer (không download model)."""
    def _tok(text, max_length=max_length,
             padding=None, truncation=None, return_tensors=None):
        result = {
            "input_ids":      torch.zeros(1, max_length, dtype=torch.long),
            "attention_mask": torch.ones(1, max_length, dtype=torch.long),
        }
        # Hỗ trợ cả subscript access lẫn dict access
        mock = MagicMock()
        mock.__getitem__ = lambda self, key: result[key]
        return mock
    return _tok


# ── FakeNewsDataset ───────────────────────────────────────────────────────────

class TestFakeNewsDataset:
    @pytest.fixture
    def df(self):
        return pd.DataFrame({
            "text":  [f"Văn bản mẫu số {i}" for i in range(10)],
            "label": [i % 2 for i in range(10)],
        })

    @pytest.fixture
    def tokenizer(self):
        return make_tokenizer(max_length=64)

    @pytest.fixture
    def dataset(self, df, tokenizer):
        return FakeNewsDataset(df, tokenizer, text_col="text",
                               label_col="label", max_length=64)

    def test_length(self, dataset, df):
        assert len(dataset) == len(df)

    def test_getitem_has_required_keys(self, dataset):
        item = dataset[0]
        assert "input_ids"      in item
        assert "attention_mask" in item
        assert "label"          in item

    def test_getitem_input_ids_shape(self, dataset):
        item = dataset[0]
        # Dataset squeeze(0) nên shape là (max_length,)
        assert item["input_ids"].shape == (64,)

    def test_getitem_attention_mask_shape(self, dataset):
        item = dataset[0]
        assert item["attention_mask"].shape == (64,)

    def test_getitem_label_dtype_float(self, dataset):
        item = dataset[0]
        assert item["label"].dtype == torch.float32

    def test_label_values(self, dataset):
        labels = [dataset[i]["label"].item() for i in range(len(dataset))]
        assert set(labels) == {0.0, 1.0}

    def test_all_items_accessible(self, dataset):
        """Không có IndexError khi lặp toàn bộ dataset."""
        for i in range(len(dataset)):
            item = dataset[i]
            assert item is not None


# ── build_dataloaders ─────────────────────────────────────────────────────────

class TestBuildDataloaders:
    @pytest.fixture
    def csv_dfs(self, tmp_path):
        """Tạo file CSV tạm cho train/val/test."""
        for split in ("train", "val", "test"):
            n  = 20 if split == "train" else 10
            df = pd.DataFrame({
                "text":  [f"Bài viết {split} {i}" for i in range(n)],
                "label": [i % 2 for i in range(n)],
            })
            df.to_csv(tmp_path / f"{split}.csv", index=False)
        return tmp_path

    @pytest.fixture
    def cfg_with_paths(self, base_cfg, csv_dfs):
        cfg = base_cfg.copy()
        cfg.data.train_path = str(csv_dfs / "train.csv")
        cfg.data.val_path   = str(csv_dfs / "val.csv")
        cfg.data.test_path  = str(csv_dfs / "test.csv")
        return cfg

    def test_returns_four_values(self, cfg_with_paths):
        tokenizer = make_tokenizer(64)
        result    = build_dataloaders(cfg_with_paths, tokenizer)
        assert len(result) == 4  # train, val, test, pos_weight

    def test_train_loader_is_dataloader(self, cfg_with_paths):
        tokenizer        = make_tokenizer(64)
        train, *_        = build_dataloaders(cfg_with_paths, tokenizer)
        assert isinstance(train, DataLoader)

    def test_pos_weight_computed_when_none(self, cfg_with_paths):
        tokenizer = make_tokenizer(64)
        _, _, _, pw = build_dataloaders(cfg_with_paths, tokenizer)
        # pos_weight=null trong config → tự tính
        assert pw is not None
        assert isinstance(pw, torch.Tensor)
        assert pw.shape == (1,)
        assert pw.item() > 0

    def test_pos_weight_skipped_when_set(self, cfg_with_paths):
        cfg_with_paths.training.pos_weight = 1.0   # set cụ thể → bỏ qua tính
        tokenizer = make_tokenizer(64)
        _, _, _, pw = build_dataloaders(cfg_with_paths, tokenizer)
        assert pw is None

    def test_batch_size_respected(self, cfg_with_paths):
        cfg_with_paths.training.train_batch_size = 4
        tokenizer = make_tokenizer(64)
        train, _, _, _ = build_dataloaders(cfg_with_paths, tokenizer)
        assert train.batch_size == 4
