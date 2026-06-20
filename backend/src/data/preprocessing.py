"""src/data/preprocessing.py"""
import re
import unicodedata
import logging
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from omegaconf import DictConfig

logger = logging.getLogger(__name__)


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def remove_noise(text: str) -> str:
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"\b\d{9,11}\b", " ", text)
    text = re.sub(r"[^\w\s\.,!?;:\-\(\)]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def clean_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    return remove_noise(normalize_unicode(text))

def merge_title_content(title: str, content: str) -> str:
    t = clean_text(title)
    c = clean_text(content)
    if t and c:
        return t + " [SEP] " + c
    return t or c


def run_preprocessing(cfg: DictConfig, raw_path: str,
                      title_col: str = "title",
                      content_col: str = "content"):
    df = pd.read_csv(raw_path)
    logger.info(f"Loaded {len(df)} rows from {raw_path}")

    label_col = cfg.data.label_col
    df[label_col] = df[label_col].astype(int)

    if cfg.data.text_col not in df.columns:
        df[cfg.data.text_col] = df.apply(
            lambda r: merge_title_content(
                str(r.get(title_col, "")),
                str(r.get(content_col, ""))
            ), axis=1
        )
    else:
        df[cfg.data.text_col] = df[cfg.data.text_col].apply(clean_text)

    before = len(df)
    df = df[df[cfg.data.text_col].str.len() > 10].reset_index(drop=True)
    logger.info(f"Removed {before - len(df)} empty rows")
    logger.info(f"Label distribution:\n{df[label_col].value_counts()}")

    test_r = cfg.data.test_size
    val_r  = cfg.data.val_size / (1 - test_r)

    train_val, test = train_test_split(
        df[[cfg.data.text_col, label_col]],
        test_size=test_r, stratify=df[label_col],
        random_state=cfg.data.seed,
    )
    train, val = train_test_split(
        train_val, test_size=val_r,
        stratify=train_val[label_col],
        random_state=cfg.data.seed,
    )

    out = Path(cfg.data.train_path).parent
    out.mkdir(parents=True, exist_ok=True)
    train.reset_index(drop=True).to_csv(cfg.data.train_path, index=False)
    val.reset_index(drop=True).to_csv(cfg.data.val_path,   index=False)
    test.reset_index(drop=True).to_csv(cfg.data.test_path,  index=False)

    logger.info(f"Saved → train:{len(train)} val:{len(val)} test:{len(test)}")
    return train, val, test
