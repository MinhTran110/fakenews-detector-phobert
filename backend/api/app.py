"""
api/app.py — FastAPI server
Endpoints:
  POST /predict/url    → paste URL bài báo → scrape → phân loại
  POST /predict/text   → paste text trực tiếp → phân loại
  POST /predict/batch  → nhiều text cùng lúc
  GET  /health         → kiểm tra server + model
  GET  /info           → thông tin model
"""
import os, time, logging, hashlib
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger    = logging.getLogger(__name__)
predictor = None                       # load khi server khởi động
url_cache = {}                         # đơn giản in-memory cache theo URL hash


# ── Lifespan ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global predictor
    model_path = os.getenv("MODEL_PATH", "checkpoints/best_model")
    try:
        from src.utils.inference import FakeNewsPredictor
        predictor = FakeNewsPredictor(model_path)
        logger.info("Model loaded OK")
        print("MODEL LOADED OK", flush=True)   # ← chuyển vào đây
    except Exception as e:
        import traceback
        logger.error(f"Model not loaded: {e}")
        print(f"LOAD ERROR: {e}", flush=True)
        import traceback; print(traceback.format_exc(), flush=True)
    yield


app = FastAPI(
    title="Fake News Detection API",
    description="Phát hiện tin giả tiếng Việt — PhoBERT + Dense + Sigmoid",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # production: chỉ định domain frontend
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ─────────────────────────────────────────────────────────────────
class UrlRequest(BaseModel):
    url:       str   = Field(..., description="URL bài báo cần kiểm tra")
    threshold: float = Field(0.5, ge=0.0, le=1.0)

class TextRequest(BaseModel):
    text:      str   = Field(..., min_length=20, max_length=10000)
    threshold: float = Field(0.5, ge=0.0, le=1.0)

class BatchRequest(BaseModel):
    texts:     list[str] = Field(..., min_length=1, max_length=16)
    threshold: float     = Field(0.5, ge=0.0, le=1.0)


# ── Demo fallback (khi chưa có model) ───────────────────────────────────────
def _demo_predict(text: str, threshold: float) -> dict:
    import random
    random.seed(int(hashlib.md5(text[:60].encode()).hexdigest(), 16) % 9999)
    p = random.uniform(0.05, 0.95)
    return {
        "label":      "FAKE" if p >= threshold else "REAL",
        "prob_fake":  round(p, 4),
        "prob_real":  round(1 - p, 4),
        "confidence": round(max(p, 1 - p), 4),
        "threshold":  threshold,
    }

def _predict(text: str, threshold: float) -> dict:
    if predictor:
        return predictor.predict_text(text, threshold)
    return _demo_predict(text, threshold)


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status":       "ok",
        "model_loaded": predictor is not None,
        "mode":         "production" if predictor else "demo",
    }


@app.get("/info")
def info():
    return {
        "model":    "vinai/phobert-base-v2",
        "pooling":  "cls_mean_max (2304 dim)",
        "output":   "sigmoid (1 neuron)",
        "loss":     "BCEWithLogitsLoss",
        "labels":   {"0": "REAL", "1": "FAKE"},
        "supported_sites": [
            "vnexpress.net", "tuoitre.vn", "thanhnien.vn",
            "dantri.com.vn", "zingnews.vn", "baomoi.com",
            "nhandan.vn", "laodong.vn",
        ],
    }


@app.post("/predict/url")
async def predict_url(req: UrlRequest):
    """
    Nhận URL bài báo → scrape nội dung → phân loại FAKE/REAL.
    Kết quả được cache theo URL để tránh scrape lại.
    """
    # Validate URL
    try:
        parsed = urlparse(req.url)
        assert parsed.scheme in ("http", "https") and parsed.netloc
    except Exception:
        raise HTTPException(status_code=400, detail="URL không hợp lệ")

    # Check cache
    cache_key = hashlib.md5(req.url.encode()).hexdigest()
    if cache_key in url_cache:
        cached = url_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    # Scrape
    t0 = time.perf_counter()
    try:
        from src.utils.scraper import scrape_article
        article = await scrape_article(
            req.url,
            timeout=15,
            min_content_len=100,
            max_content_len=8000,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tải bài báo: {e}")

    # Predict
    try:
        full_text = f"{article['title']} [SEP] {article['content']}"
        result    = _predict(full_text, req.threshold)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi phân tích: {e}")

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    response = {
        **result,
        "article": {
            "title":   article["title"],
            "excerpt": article["excerpt"],
            "url":     req.url,
            "source":  article["source"],
        },
        "warning":            article.get("warning"),
        "processing_time_ms": elapsed_ms,
        "cached":             False,
    }

    # Lưu cache (tối đa 500 entries)
    if len(url_cache) < 500:
        url_cache[cache_key] = response

    return response


@app.post("/predict/text")
def predict_text(req: TextRequest):
    """Nhận text trực tiếp → phân loại FAKE/REAL."""
    t0 = time.perf_counter()
    try:
        result = _predict(req.text, req.threshold)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        **result,
        "processing_time_ms": round((time.perf_counter() - t0) * 1000, 1),
    }


@app.post("/predict/batch")
def predict_batch(req: BatchRequest):
    """Phân loại nhiều text cùng lúc (tối đa 16)."""
    t0 = time.perf_counter()
    results = []

    for text in req.texts:
        try:
            results.append(_predict(text, req.threshold))
        except Exception as e:
            results.append({"error": str(e)})

    return {
        "results":            results,
        "total":              len(results),
        "processing_time_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
