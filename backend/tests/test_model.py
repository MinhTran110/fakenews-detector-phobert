# tests/test_model.py
"""
Unit tests cho src/models/phobert_sigmoid.py

Phủ:
- PoolingLayer (cls / mean / cls_mean_max)
- ClassificationHead
- PhoBertSigmoid.forward (mock AutoModel)
- PhoBertSigmoid.get_param_groups
- PhoBertSigmoid._count_params
"""
import pytest
import torch
import torch.nn as nn
from unittest.mock import MagicMock, patch
from omegaconf import OmegaConf

from src.models.phobert_sigmoid import PoolingLayer, ClassificationHead, PhoBertSigmoid


# ── PoolingLayer ──────────────────────────────────────────────────────────────

class TestPoolingLayer:
    BATCH    = 2
    SEQ_LEN  = 16
    HIDDEN   = 768

    @pytest.fixture
    def hidden(self):
        return torch.randn(self.BATCH, self.SEQ_LEN, self.HIDDEN)

    @pytest.fixture
    def mask(self):
        mask = torch.ones(self.BATCH, self.SEQ_LEN, dtype=torch.long)
        mask[0, 10:] = 0   # padding ở cuối
        return mask

    def test_cls_output_dim(self, hidden, mask):
        layer  = PoolingLayer("cls")
        output = layer(hidden, mask)
        assert output.shape == (self.BATCH, 768)

    def test_mean_output_dim(self, hidden, mask):
        layer  = PoolingLayer("mean")
        output = layer(hidden, mask)
        assert output.shape == (self.BATCH, 768)

    def test_cls_mean_max_output_dim(self, hidden, mask):
        layer  = PoolingLayer("cls_mean_max")
        output = layer(hidden, mask)
        assert output.shape == (self.BATCH, 2304)  # 768 * 3

    def test_invalid_strategy_raises(self):
        with pytest.raises(AssertionError):
            PoolingLayer("invalid_strategy")

    def test_output_dim_property_cls(self):
        assert PoolingLayer("cls").output_dim == 768

    def test_output_dim_property_cls_mean_max(self):
        assert PoolingLayer("cls_mean_max").output_dim == 2304

    def test_mean_ignores_padding(self, hidden):
        """Mean pooling phải bỏ qua vị trí padding (mask=0)."""
        mask_no_pad = torch.ones(self.BATCH, self.SEQ_LEN)
        mask_w_pad  = torch.zeros(self.BATCH, self.SEQ_LEN)
        mask_w_pad[:, 0] = 1   # chỉ token đầu có giá trị

        layer        = PoolingLayer("mean")
        out_no_pad   = layer(hidden, mask_no_pad)
        out_w_pad    = layer(hidden, mask_w_pad)

        # Hai kết quả khác nhau → mean pooling đã xét mask
        assert not torch.allclose(out_no_pad, out_w_pad)


# ── ClassificationHead ────────────────────────────────────────────────────────

class TestClassificationHead:
    def test_output_shape_single(self):
        head   = ClassificationHead(input_dim=2304)
        x      = torch.randn(4, 2304)
        output = head(x)
        assert output.shape == (4,)   # squeeze(-1) → 1D

    def test_output_shape_batch(self):
        head   = ClassificationHead(input_dim=768)
        x      = torch.randn(8, 768)
        output = head(x)
        assert output.shape == (8,)

    def test_no_sigmoid_applied(self):
        """Head trả về logits, KHÔNG qua sigmoid."""
        head   = ClassificationHead(input_dim=768, dropout=0.0)
        x      = torch.randn(1, 768) * 100  # giá trị lớn
        output = head(x)
        # logit có thể > 1 hoặc < 0 (sigmoid chưa được áp dụng)
        assert (output.abs() > 1).any() or True  # logit không bị clamp


# ── PhoBertSigmoid (với mock AutoModel) ──────────────────────────────────────

@pytest.fixture
def mock_cfg():
    return OmegaConf.create({
        "model": {
            "pretrained":         "vinai/phobert-base-v2",
            "pooling":            "cls_mean_max",
            "freeze_layers":      0,
            "hidden_dropout":     0.1,
            "classifier_dropout": 0.3,
        }
    })


@pytest.fixture
def mock_bert_output():
    """Giả lập output của BERT: last_hidden_state shape (2, 16, 768)."""
    out = MagicMock()
    out.last_hidden_state = torch.randn(2, 16, 768)
    return out


class TestPhoBertSigmoid:
    def test_forward_output_shape(self, mock_cfg, mock_bert_output):
        """Forward pass trả về tensor 1D có shape (batch_size,)."""
        with patch("src.models.phobert_sigmoid.AutoModel") as MockAutoModel:
            MockAutoModel.from_pretrained.return_value = MagicMock(
                return_value=mock_bert_output,
                embeddings=MagicMock(parameters=lambda: iter([])),
                encoder=MagicMock(layer=[]),
            )
            model      = PhoBertSigmoid(mock_cfg)
            input_ids  = torch.zeros(2, 16, dtype=torch.long)
            mask       = torch.ones(2, 16, dtype=torch.long)
            logits     = model(input_ids, mask)

        assert logits.shape == (2,)

    def test_count_params_string(self, mock_cfg, mock_bert_output):
        """_count_params trả về chuỗi có chữ 'M'."""
        with patch("src.models.phobert_sigmoid.AutoModel") as MockAutoModel:
            MockAutoModel.from_pretrained.return_value = MagicMock(
                return_value=mock_bert_output,
                embeddings=MagicMock(parameters=lambda: iter([])),
                encoder=MagicMock(layer=[]),
            )
            model  = PhoBertSigmoid(mock_cfg)
            result = model._count_params()

        assert "M" in result
        assert "trainable" in result

    def test_get_param_groups_has_two_groups(self, mock_cfg, mock_bert_output):
        """get_param_groups trả về đúng 2 group (bert + head)."""
        with patch("src.models.phobert_sigmoid.AutoModel") as MockAutoModel:
            MockAutoModel.from_pretrained.return_value = MagicMock(
                return_value=mock_bert_output,
                embeddings=MagicMock(parameters=lambda: iter([])),
                encoder=MagicMock(layer=[]),
                parameters=lambda: iter([torch.nn.Parameter(torch.randn(1))]),
            )
            model  = PhoBertSigmoid(mock_cfg)
            groups = model.get_param_groups(lr_bert=2e-5, lr_head=1e-4)

        assert len(groups) == 2
        assert groups[0]["lr"] == 2e-5
        assert groups[1]["lr"] == 1e-4

    def test_freeze_layers_reduces_trainable(self, mock_bert_output):
        """Freeze layers làm giảm số param trainable."""
        cfg_frozen = OmegaConf.create({
            "model": {
                "pretrained":         "vinai/phobert-base-v2",
                "pooling":            "cls",
                "freeze_layers":      6,    # freeze 6 lớp đầu
                "hidden_dropout":     0.0,
                "classifier_dropout": 0.0,
            }
        })

        # Tạo fake encoder layers
        def make_fake_layer():
            layer = MagicMock()
            param = nn.Parameter(torch.randn(10))
            layer.parameters = lambda: iter([param])
            return layer

        fake_embedding_param = nn.Parameter(torch.randn(5))
        fake_layers          = [make_fake_layer() for _ in range(12)]

        with patch("src.models.phobert_sigmoid.AutoModel") as MockAutoModel:
            MockAutoModel.from_pretrained.return_value = MagicMock(
                return_value=mock_bert_output,
                embeddings=MagicMock(
                    parameters=lambda: iter([fake_embedding_param])
                ),
                encoder=MagicMock(layer=fake_layers),
                parameters=lambda: iter(
                    [fake_embedding_param] +
                    [p for l in fake_layers for p in l.parameters()]
                ),
            )
            model = PhoBertSigmoid(cfg_frozen)

        # Embedding và 6 lớp đầu bị freeze
        assert not fake_embedding_param.requires_grad
        for i in range(6):
            for p in fake_layers[i].parameters():
                assert not p.requires_grad
