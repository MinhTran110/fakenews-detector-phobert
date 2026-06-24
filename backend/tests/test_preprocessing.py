# tests/test_preprocessing.py
"""
Unit tests cho src/data/preprocessing.py

Phủ:
- normalize_unicode
- remove_noise
- clean_text
- merge_title_content
- run_preprocessing (integration)
"""
import pytest
import pandas as pd
from unittest.mock import patch

from src.data.preprocessing import (
    normalize_unicode,
    remove_noise,
    clean_text,
    merge_title_content,
    run_preprocessing,
)


# ── normalize_unicode ─────────────────────────────────────────────────────────

class TestNormalizeUnicode:
    def test_nfc_normalization(self):
        # "ắ" có thể được encode theo NFC hoặc NFD
        text_nfd = "a\u0301"          # a + combining acute accent (NFD)
        result   = normalize_unicode(text_nfd)
        assert result == "\u00e1"     # á precomposed (NFC)

    def test_already_nfc(self):
        text = "Xin chào Việt Nam"
        assert normalize_unicode(text) == text

    def test_empty_string(self):
        assert normalize_unicode("") == ""


# ── remove_noise ──────────────────────────────────────────────────────────────

class TestRemoveNoise:
    def test_remove_url_http(self):
        result = remove_noise("Xem thêm tại http://example.com/bai-viet")
        assert "http" not in result

    def test_remove_url_www(self):
        result = remove_noise("Truy cập www.vnexpress.net ngay")
        assert "www" not in result

    def test_remove_email(self):
        result = remove_noise("Liên hệ: admin@example.com để biết thêm")
        assert "@" not in result

    def test_remove_phone_10_digits(self):
        result = remove_noise("Gọi ngay 0987654321 để tư vấn")
        assert "0987654321" not in result

    def test_keep_short_numbers(self):
        # Số ngắn hơn 9 chữ số KHÔNG bị xóa
        result = remove_noise("Có 3 người trong nhóm")
        assert "3" in result

    def test_collapse_whitespace(self):
        result = remove_noise("Xin   chào    bạn")
        assert "  " not in result
        assert result.strip() == result

    def test_remove_special_chars(self):
        # Ký tự đặc biệt ngoài whitelist bị thay bằng space
        result = remove_noise("Giá: 100$ và £50")
        assert "$" not in result
        assert "£" not in result


# ── clean_text ────────────────────────────────────────────────────────────────

class TestCleanText:
    def test_none_input_returns_empty(self):
        # clean_text chỉ nhận str, test với chuỗi rỗng
        assert clean_text("") == ""

    def test_whitespace_only_returns_empty(self):
        assert clean_text("   \t\n  ") == ""

    def test_normal_text(self):
        result = clean_text("  Tin tức hôm nay rất hay!  ")
        assert result == "Tin tức hôm nay rất hay!"

    def test_combined_cleaning(self):
        text   = "Đọc ngay tại http://abc.vn — liên hệ: test@mail.com"
        result = clean_text(text)
        assert "http" not in result
        assert "@"    not in result

    def test_non_string_returns_empty(self):
        # Hàm kiểm tra isinstance(text, str)
        assert clean_text(None) == ""  # type: ignore
        assert clean_text(123)  == ""  # type: ignore


# ── merge_title_content ───────────────────────────────────────────────────────

class TestMergeTitleContent:
    def test_both_present(self):
        result = merge_title_content("Tiêu đề", "Nội dung bài viết")
        assert "[SEP]" in result
        assert result.startswith("Tiêu đề")
        assert "Nội dung bài viết" in result

    def test_only_title(self):
        result = merge_title_content("Tiêu đề", "")
        assert result == "Tiêu đề"
        assert "[SEP]" not in result

    def test_only_content(self):
        result = merge_title_content("", "Nội dung dài")
        assert result == "Nội dung dài"
        assert "[SEP]" not in result

    def test_both_empty(self):
        result = merge_title_content("", "")
        assert result == ""

    def test_cleans_inputs(self):
        result = merge_title_content(
            "Tiêu đề http://abc.com",
            "Nội dung email@test.com"
        )
        assert "http" not in result
        assert "@"    not in result


# ── run_preprocessing (integration) ──────────────────────────────────────────

class TestRunPreprocessing:
    def test_creates_splits(self, tmp_path, base_cfg, sample_raw_df):
        """Kiểm tra hàm tạo đúng 3 file split."""
        raw_file = tmp_path / "dataset.csv"
        sample_raw_df.to_csv(raw_file, index=False)

        # Cần nhiều dữ liệu hơn để split hợp lệ (ít nhất ~20 rows)
        big_df = pd.concat([sample_raw_df] * 15, ignore_index=True)
        big_df.to_csv(raw_file, index=False)

        # Ghi đè path trong config
        cfg = base_cfg.copy()
        cfg.data.train_path = str(tmp_path / "train.csv")
        cfg.data.val_path   = str(tmp_path / "val.csv")
        cfg.data.test_path  = str(tmp_path / "test.csv")

        train, val, test = run_preprocessing(
            cfg,
            raw_path=str(raw_file),
            title_col="title",
            content_col="content",
        )

        # Kiểm tra shape cơ bản
        assert len(train) > 0
        assert len(val)   > 0
        assert len(test)  > 0
        assert len(train) + len(val) + len(test) == len(big_df)

    def test_label_column_present(self, tmp_path, base_cfg):
        """Label column phải tồn tại sau preprocessing."""
        big_df = pd.DataFrame({
            "title":   ["T"] * 30,
            "content": ["C dài " * 5] * 30,
            "label":   [0, 1] * 15,
        })
        raw_file = str(tmp_path / "data.csv")
        big_df.to_csv(raw_file, index=False)

        cfg = base_cfg.copy()
        cfg.data.train_path = str(tmp_path / "train.csv")
        cfg.data.val_path   = str(tmp_path / "val.csv")
        cfg.data.test_path  = str(tmp_path / "test.csv")

        train, val, test = run_preprocessing(cfg, raw_path=raw_file)

        assert "label" in train.columns
        assert "text"  in train.columns

    def test_empty_rows_removed(self, tmp_path, base_cfg):
        """Hàng text rỗng bị loại bỏ."""
        df = pd.DataFrame({
            "text":  [""] * 5 + ["Nội dung bài viết dài đủ để giữ lại"] * 25,
            "label": [0] * 30,
        })
        raw_file = str(tmp_path / "data.csv")
        df.to_csv(raw_file, index=False)

        cfg = base_cfg.copy()
        cfg.data.train_path = str(tmp_path / "train.csv")
        cfg.data.val_path   = str(tmp_path / "val.csv")
        cfg.data.test_path  = str(tmp_path / "test.csv")

        train, val, test = run_preprocessing(cfg, raw_path=raw_file)
        total = len(train) + len(val) + len(test)
        assert total == 25  # 5 hàng rỗng bị bỏ
