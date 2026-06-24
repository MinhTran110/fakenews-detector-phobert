# Fake News Detector — PhoBERT + URL Scraper

Paste URL bài báo → AI tự đọc nội dung → phân loại FAKE / REAL.

## Cấu trúc project

```
fakenews_url/
├── backend/
│   ├── configs/config.yaml         ← toàn bộ tham số
│   ├── src/
│   │   ├── data/
│   │   │   ├── preprocessing.py    ← clean text, split data
│   │   │   └── dataset.py          ← PyTorch Dataset, DataLoader
│   │   ├── models/
│   │   │   └── phobert_sigmoid.py  ← PhoBERT + Pooling + Dense + Sigmoid
│   │   ├── training/
│   │   │   └── trainer.py          ← BCEWithLogitsLoss, AdamW, warmup, fp16
│   │   └── utils/
│   │       ├── scraper.py          ← scrape URL báo VN (newspaper3k + BS4)
│   │       └── inference.py        ← load model, predict text/article
│   ├── api/app.py                  ← FastAPI: /predict/url, /predict/text
│   ├── train.py                    ← entry point training
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx                 ← UI chính: URL tab + Text tab
    │   ├── components/
    │   │   └── ResultCard.jsx      ← hiển thị kết quả
    │   └── hooks/
    │       └── usePredictor.js     ← gọi API, quản lý state
    ├── index.html
    ├── vite.config.js
    └── package.json
```

---

## Chạy nhanh trên Windows (Khuyên dùng)

### Bước 0: Tải mã nguồn về máy
Mở Git Bash hoặc CMD và chạy lệnh sau để clone project:
```bash
git clone https://github.com/MinhTran110/fakenews-detector-phobert.git
cd fakenews-detector-phobert
```

Sau đó, tiến hành cài đặt và kích hoạt tự động bằng các file script `.bat`:

1. **Cài đặt lần đầu:** Click đúp vào file [setup.bat](file:///c:/Users/Administrator/Downloads/fakenews_url/fakenews_url/setup.bat) (hoặc chạy trong CMD: `setup.bat`). Script sẽ tự động tạo môi trường ảo Python (`venv`), cài đặt toàn bộ dependencies backend và frontend.
2. **Khởi động ứng dụng:** Click đúp vào file [start.bat](file:///c:/Users/Administrator/Downloads/fakenews_url/fakenews_url/start.bat). Script sẽ kích hoạt cùng lúc Backend (cổng 8000), Frontend (cổng 5173) và tự động mở trình duyệt web.
3. **Dừng ứng dụng:** Click đúp vào file [stop.bat](file:///c:/Users/Administrator/Downloads/fakenews_url/fakenews_url/stop.bat) để tắt nhanh các server đang chạy ngầm.
4. **Chạy kiểm thử:** Click đúp vào file [test.bat](file:///c:/Users/Administrator/Downloads/fakenews_url/fakenews_url/test.bat) để chạy bộ kiểm thử tự động (Pytest).

---

## Chạy thủ công (Từng phần)

### Backend

```bash
cd backend
pip install -r requirements.txt

# Train model (cần có data/raw/dataset.csv)
python train.py

# Khởi động API
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev       # → http://localhost:5173
```

---

## Train model

### Chuẩn bị data

File `data/raw/dataset.csv` cần có:

| Cột | Mô tả |
|---|---|
| `title` | Tiêu đề bài báo |
| `content` | Nội dung bài báo |
| `label` | 0 = real, 1 = fake |

Nếu đã có cột `text` (đã ghép sẵn), cập nhật `text_col` trong `config.yaml`.

### Chạy training

```bash
# Mặc định
python train.py

# Override config
python train.py training.num_epochs=10
python train.py model.freeze_layers=0      # fine-tune toàn bộ
python train.py inference.threshold=0.4   # tune threshold
python train.py training.train_batch_size=8  # GPU ít VRAM
```

### Theo dõi training

```bash
tensorboard --logdir logs
```

---

## API Endpoints

```bash
# Phân tích URL bài báo
curl -X POST http://localhost:8000/predict/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://vnexpress.net/bai-viet-mau", "threshold": 0.5}'

# Phân tích text trực tiếp
curl -X POST http://localhost:8000/predict/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Nội dung bài báo cần kiểm tra...", "threshold": 0.5}'

# Health check
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs
```

### Response mẫu (URL)

```json
{
  "label":      "FAKE",
  "prob_fake":  0.8923,
  "prob_real":  0.1077,
  "confidence": 0.8923,
  "threshold":  0.5,
  "article": {
    "title":   "Tiêu đề bài báo",
    "excerpt": "200 ký tự đầu của nội dung...",
    "url":     "https://...",
    "source":  "newspaper3k"
  },
  "warning":            null,
  "processing_time_ms": 412.3,
  "cached":             false
}
```

---

## Scraper hỗ trợ

| Site | Hỗ trợ |
|---|---|
| vnexpress.net | ✅ |
| tuoitre.vn | ✅ |
| thanhnien.vn | ✅ |
| dantri.com.vn | ✅ |
| zingnews.vn | ✅ |
| baomoi.com | ✅ |
| nhandan.vn | ✅ |
| laodong.vn | ✅ |
| Site lạ/không rõ | ⚠ Generic fallback |
| Facebook/TikTok | ❌ Không hỗ trợ |
| Trang có paywall | ⚠ Chỉ đọc phần free |

---

## Deploy

### Backend → Railway

```bash
npm install -g @railway/cli
railway login && railway init && railway up
```

### Backend → Hugging Face Spaces

Tạo `Dockerfile` trong thư mục backend:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "7860"]
```

### Frontend → Vercel

```bash
cd frontend
npm run build
npx vercel --prod
# Thêm env var: VITE_API_URL=https://your-backend-url
```
