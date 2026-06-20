"""src/utils/inference.py"""
import torch
from transformers import AutoTokenizer
from omegaconf import OmegaConf
import logging

from src.data.preprocessing import clean_text, merge_title_content
from src.models.phobert_sigmoid import PhoBertSigmoid

logger = logging.getLogger(__name__)


class FakeNewsPredictor:
    def __init__(self, model_dir: str, device: str | None = None):
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.cfg       = OmegaConf.load(f"{model_dir}/config.yaml")
        self.threshold = self.cfg.inference.threshold
        self.tokenizer = AutoTokenizer.from_pretrained(self.cfg.model.pretrained)
        self.model     = PhoBertSigmoid(self.cfg)

        state = torch.load(
            f"{model_dir}/trainer_state.pt",
            map_location=self.device,
            weights_only=False,
        )
        self.model.load_state_dict(state["model_state"])
        self.model.to(self.device).eval()
        logger.info(f"Loaded model from {model_dir} | device={self.device}")

    @torch.no_grad()
    def predict_text(self, text: str,
                     threshold: float | None = None) -> dict:
        thr  = threshold if threshold is not None else self.threshold
        text = clean_text(text)

        enc = self.tokenizer(
            text,
            max_length=self.cfg.data.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        logit     = self.model(
            enc["input_ids"].to(self.device),
            enc["attention_mask"].to(self.device),
        )
        prob_fake = torch.sigmoid(logit).item()
        prob_real = 1.0 - prob_fake
        label     = "FAKE" if prob_fake >= thr else "REAL"

        return {
            "label":      label,
            "prob_fake":  round(prob_fake, 4),
            "prob_real":  round(prob_real, 4),
            "confidence": round(max(prob_fake, prob_real), 4),
            "threshold":  thr,
        }

    def predict_from_article(self, title: str, content: str,
                              threshold: float | None = None) -> dict:
        text = merge_title_content(title, content)
        return self.predict_text(text, threshold)
