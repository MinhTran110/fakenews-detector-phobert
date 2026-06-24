# tests/test_api.py
"""
Integration tests cho api/app.py (FastAPI)

Dùng httpx.AsyncClient + ASGITransport để test in-process (không cần server thật).

Phủ:
- GET  /health
- GET  /info
- POST /predict/text  (demo mode + production mode)
- POST /predict/url   (mock scraper + mock predictor)
- POST /predict/batch
- Validation errors (400 / 422)
- Cache hit (/predict/url gọi lần 2)
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

# Import app (model sẽ là None vì chưa có checkpoints → demo mode)
from api.app import app


# ── Helpers ───────────────────────────────────────────────────────────────────

FAKE_PREDICT_RESULT = {
    "label":      "FAKE",
    "prob_fake":  0.85,
    "prob_real":  0.15,
    "confidence": 0.85,
    "threshold":  0.5,
}

FAKE_ARTICLE = {
    "title":   "Bài báo giả mạo mẫu",
    "content": "Nội dung bài báo mẫu " * 20,
    "excerpt": "Nội dung bài báo mẫu " * 5 + "…",
    "url":     "https://vnexpress.net/test",
    "source":  "newspaper3k",
    "warning": None,
}


@pytest.fixture
def client():
    """Đồng bộ wrapper để tạo AsyncClient trong test sync."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── /health ───────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_ok(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "model_loaded" in data
        assert "mode" in data

    @pytest.mark.asyncio
    async def test_demo_mode_when_no_model(self):
        """Khi predictor=None → mode='demo'."""
        import api.app as app_module
        original = app_module.predictor
        app_module.predictor = None

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/health")

        app_module.predictor = original
        assert resp.json()["mode"] == "demo"


# ── /info ─────────────────────────────────────────────────────────────────────

class TestInfoEndpoint:
    @pytest.mark.asyncio
    async def test_info_returns_model_details(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/info")

        assert resp.status_code == 200
        data = resp.json()
        assert "model"           in data
        assert "phobert"         in data["model"].lower()
        assert "supported_sites" in data
        assert len(data["supported_sites"]) > 0


# ── /predict/text ─────────────────────────────────────────────────────────────

class TestPredictTextEndpoint:
    @pytest.mark.asyncio
    async def test_demo_mode_returns_result(self):
        """Khi không có model → demo fallback vẫn trả về kết quả."""
        import api.app as app_module
        app_module.predictor = None  # đảm bảo demo mode

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/predict/text", json={
                "text": "Đây là nội dung bài báo cần kiểm tra xem có phải tin giả không."
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "label"      in data
        assert "prob_fake"  in data
        assert "prob_real"  in data
        assert "confidence" in data
        assert data["label"] in ("FAKE", "REAL")
        assert 0.0 <= data["prob_fake"] <= 1.0
        assert 0.0 <= data["prob_real"] <= 1.0

    @pytest.mark.asyncio
    async def test_production_mode_calls_predictor(self):
        """Khi có predictor → gọi predict_text."""
        import api.app as app_module
        mock_pred = MagicMock()
        mock_pred.predict_text.return_value = FAKE_PREDICT_RESULT
        original          = app_module.predictor
        app_module.predictor = mock_pred

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/predict/text", json={
                "text":      "Bài báo test production mode đủ dài hơn 20 ký tự.",
                "threshold": 0.5,
            })

        app_module.predictor = original
        assert resp.status_code == 200
        mock_pred.predict_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_text_too_short_returns_422(self):
        """Text < 20 ký tự → Pydantic validation error 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/predict/text", json={"text": "Ngắn"})

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_custom_threshold_passed(self):
        """threshold tùy chỉnh được truyền vào predict."""
        import api.app as app_module
        mock_pred = MagicMock()
        mock_pred.predict_text.return_value = {**FAKE_PREDICT_RESULT, "threshold": 0.3}
        original          = app_module.predictor
        app_module.predictor = mock_pred

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            await ac.post("/predict/text", json={
                "text":      "Văn bản đủ dài để kiểm tra threshold tuỳ chỉnh nhé.",
                "threshold": 0.3,
            })

        app_module.predictor = original
        _, kwargs = mock_pred.predict_text.call_args
        # threshold=0.3 phải được truyền vào
        args = mock_pred.predict_text.call_args[0]
        assert 0.3 in args or mock_pred.predict_text.call_args[1].get("threshold") == 0.3

    @pytest.mark.asyncio
    async def test_threshold_out_of_range_returns_422(self):
        """threshold > 1.0 → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/predict/text", json={
                "text":      "Văn bản hợp lệ đủ dài hơn 20 ký tự nhé bạn.",
                "threshold": 1.5,
            })
        assert resp.status_code == 422


# ── /predict/url ──────────────────────────────────────────────────────────────

class TestPredictUrlEndpoint:
    @pytest.mark.asyncio
    async def test_valid_url_returns_result(self):
        """Mock scraper + predictor, kiểm tra response đầy đủ."""
        import api.app as app_module
        mock_pred = MagicMock()
        mock_pred.predict_text.return_value = FAKE_PREDICT_RESULT
        original          = app_module.predictor
        app_module.predictor = mock_pred
        app_module.url_cache = {}   # clear cache

        with patch("api.app.scrape_article", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = FAKE_ARTICLE
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.post("/predict/url", json={
                    "url": "https://vnexpress.net/tin-tuc-mau-p123.html"
                })

        app_module.predictor = original
        assert resp.status_code == 200
        data = resp.json()
        assert "label"              in data
        assert "article"            in data
        assert "processing_time_ms" in data
        assert data["cached"]       is False

    @pytest.mark.asyncio
    async def test_cache_hit_on_second_call(self):
        """Gọi lần 2 cùng URL → cached=True, scrape KHÔNG được gọi lại."""
        import api.app as app_module
        app_module.predictor = None
        app_module.url_cache = {}

        url = "https://tuoitre.vn/bai-viet-cache-test.html"

        with patch("api.app.scrape_article", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = FAKE_ARTICLE
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                await ac.post("/predict/url", json={"url": url})  # lần 1
                resp2 = await ac.post("/predict/url", json={"url": url})  # lần 2

        assert mock_scrape.call_count == 1  # chỉ scrape 1 lần
        assert resp2.json()["cached"] is True

    @pytest.mark.asyncio
    async def test_invalid_url_scheme_returns_400(self):
        """URL không dùng http/https → 400."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/predict/url", json={
                "url": "ftp://invalid.com/bai-viet"
            })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_scrape_error_returns_422(self):
        """Khi scraper raise ValueError → 422."""
        import api.app as app_module
        app_module.url_cache = {}

        with patch("api.app.scrape_article", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = ValueError("Không đọc được nội dung")
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.post("/predict/url", json={
                    "url": "https://example.com/bai-viet-test.html"
                })

        assert resp.status_code == 422


# ── /predict/batch ────────────────────────────────────────────────────────────

class TestPredictBatchEndpoint:
    @pytest.mark.asyncio
    async def test_batch_returns_list(self):
        """Batch với 3 texts → list 3 kết quả."""
        import api.app as app_module
        app_module.predictor = None  # demo mode

        texts = [
            "Văn bản thứ nhất cần kiểm tra trong batch này.",
            "Văn bản thứ hai cũng cần kiểm tra xem sao.",
            "Văn bản thứ ba cuối cùng trong batch request.",
        ]
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/predict/batch", json={"texts": texts})

        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["total"] == 3
        assert len(data["results"]) == 3
        assert "processing_time_ms" in data

    @pytest.mark.asyncio
    async def test_batch_empty_list_returns_422(self):
        """texts rỗng → Pydantic validation 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/predict/batch", json={"texts": []})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_batch_max_16_enforced(self):
        """texts > 16 phần tử → 422."""
        texts = [f"Văn bản số {i} đủ dài." for i in range(17)]
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/predict/batch", json={"texts": texts})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_each_result_has_label(self):
        """Mỗi item trong results phải có 'label'."""
        import api.app as app_module
        app_module.predictor = None

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/predict/batch", json={
                "texts": [
                    "Bài viết đầu tiên đủ dài để test.",
                    "Bài viết thứ hai cũng đủ dài nhé.",
                ]
            })

        results = resp.json()["results"]
        for r in results:
            assert "label" in r
            assert r["label"] in ("FAKE", "REAL")
