// src/App.jsx
import { useState } from "react";
import { usePredictor } from "./hooks/usePredictor";
import { ResultCard }   from "./components/ResultCard";
import styles from "./App.module.css";

const SUPPORTED_SITES = [
  "vnexpress.net", "tuoitre.vn", "thanhnien.vn",
  "dantri.com.vn", "zingnews.vn", "baomoi.com",
];

function Spinner({ step }) {
  const msg = step === "scraping"
    ? "Đang đọc bài báo từ URL…"
    : "Đang phân tích với PhoBERT…";
  return (
    <div className={styles.spinnerContainer}>
      <div className={styles.spinnerCircle} />
      <div className={styles.spinnerMsg}>{msg}</div>
    </div>
  );
}

// ── URL Tab ──────────────────────────────────────────────────────────────
function UrlTab() {
  const [url, setUrl] = useState("");
  const [threshold, setThreshold] = useState(0.5);
  const { loading, result, error, step, predictUrl, reset } = usePredictor();

  const valid = (() => {
    try { new URL(url); return url.startsWith("http"); }
    catch { return false; }
  })();

  function handleSubmit() {
    if (!valid) return;
    predictUrl(url, threshold);
  }

  return (
    <div>
      <label className={styles.label}>URL BÀI BÁO</label>
      <input
        value={url}
        onChange={e => { setUrl(e.target.value); reset(); }}
        onKeyDown={e => e.key === "Enter" && handleSubmit()}
        placeholder="https://vnexpress.net/…"
        className={styles.input}
      />

      {/* Quick-fill examples */}
      <div className={styles.quickFillList}>
        <span className={styles.quickFillLabel}>Hỗ trợ:</span>
        {SUPPORTED_SITES.map(site => (
          <span key={site} className={styles.quickFillBadge}>{site}</span>
        ))}
      </div>

      {/* Threshold slider */}
      <div className={styles.sliderContainer}>
        <div className={styles.sliderHeader}>
          <span className={styles.sliderLabel}>NGƯỠNG PHÂN LOẠI</span>
          <span className={styles.sliderVal}>{threshold.toFixed(2)}</span>
        </div>
        <input
          type="range" min="0.2" max="0.8" step="0.05"
          value={threshold}
          onChange={e => setThreshold(parseFloat(e.target.value))}
          className={styles.slider}
        />
        <div className={styles.flexRow}>
          <span className={styles.charCount}>Bắt nhiều Fake hơn</span>
          <span className={styles.charCount}>Chính xác hơn</span>
        </div>
      </div>

      {error && (
        <div className={styles.errorAlert}>{error}</div>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading || !valid}
        className={`${styles.button} ${(loading || !valid) ? styles.buttonDisabled : ""}`}
      >
        {loading ? "Đang xử lý…" : "Kiểm tra bài báo"}
      </button>

      <div style={{ marginTop: 24 }}>
        {loading && <Spinner step={step} />}
        {result && !loading && <ResultCard result={result} />}
      </div>
    </div>
  );
}

// ── Text Tab ─────────────────────────────────────────────────────────────
function TextTab() {
  const [text, setText] = useState("");
  const [threshold, setThreshold] = useState(0.5);
  const { loading, result, error, step, predictText, reset } = usePredictor();

  return (
    <div>
      <label className={styles.label}>NỘI DUNG BÀI BÁO</label>
      <textarea
        value={text}
        onChange={e => { setText(e.target.value); reset(); }}
        placeholder="Dán tiêu đề và nội dung bài báo vào đây…"
        className={`${styles.input} ${styles.textarea}`}
      />
      <div className={styles.flexRow} style={{ marginTop: 4 }}>
        <span className={styles.charCount}>{text.length} ký tự</span>
        {text.length < 20 && text.length > 0 && (
          <span className={styles.charWarning}>Cần ít nhất 20 ký tự</span>
        )}
      </div>

      <div className={styles.sliderContainer}>
        <div className={styles.sliderHeader}>
          <span className={styles.sliderLabel}>NGƯỠNG</span>
          <span className={styles.sliderVal}>{threshold.toFixed(2)}</span>
        </div>
        <input
          type="range" min="0.2" max="0.8" step="0.05"
          value={threshold}
          onChange={e => setThreshold(parseFloat(e.target.value))}
          className={styles.slider}
        />
      </div>

      {error && (
        <div className={styles.errorAlert}>{error}</div>
      )}

      <button
        onClick={() => text.length >= 20 && predictText(text, threshold)}
        disabled={loading || text.length < 20}
        className={`${styles.button} ${(loading || text.length < 20) ? styles.buttonDisabled : ""}`}
      >
        {loading ? "Đang phân tích…" : "Phân tích văn bản"}
      </button>

      <div style={{ marginTop: 24 }}>
        {loading && <Spinner step={step} />}
        {result && !loading && <ResultCard result={result} />}
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────
const TABS = [
  { id: "url",  label: "Paste URL" },
  { id: "text", label: "Paste Text" },
];

export default function App() {
  const [tab, setTab] = useState("url");

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@700;800&family=Inter:wght@400;500;600&display=swap');
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
        :root{
          --bg:#0b0b12;--bg2:#111119;--fg:#f0eff8;
          --muted:#7e7d92;--accent:#c8f547;--border:rgba(255,255,255,0.07);
        }
        body{background:var(--bg);color:var(--fg);font-family:'DM Sans',sans-serif;min-height:100vh;-webkit-font-smoothing:antialiased}
        @keyframes slideUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
        @keyframes spin{to{transform:rotate(360deg)}}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
        input[type=range]{height:4px;border-radius:2px}
        textarea::-webkit-scrollbar{width:4px}
        textarea::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.1);border-radius:2px}
      `}</style>

      {/* Ambient glow */}
      <div className={styles.ambientGlow} />

      <div className={styles.container}>

        {/* Header */}
        <header className={styles.header}>
          <div className={styles.badge}>
            <span className={styles.badgeDot} />
            PHOBERT AI · FAKE NEWS DETECTOR
          </div>

          <h1 className={styles.title}>
            Kiểm tra tin giả<br />tiếng Việt
          </h1>

          <p className={styles.description}>
            Paste URL bài báo hoặc nội dung trực tiếp —<br />
            AI sẽ phân tích và cho kết quả trong vài giây.
          </p>
        </header>

        {/* Card */}
        <div className={styles.card}>
          {/* Tabs */}
          <div className={styles.tabs}>
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`${styles.tabBtn} ${tab === t.id ? styles.activeTabBtn : ""}`}
              >{t.label}</button>
            ))}
          </div>

          {/* Tab content */}
          <div className={styles.cardBody}>
            {tab === "url"  && <UrlTab />}
            {tab === "text" && <TextTab />}
          </div>
        </div>

        {/* Footer */}
        <footer className={styles.footer}>
          <div>
            Powered by{" "}
            <strong className={styles.footerStrong}>PhoBERT</strong>
            {" "}·{" "}
            <span className={styles.footerSpan}>vinai/phobert-base-v2</span>
          </div>
          <div className={styles.footerDisclaimer}>
            Kết quả chỉ mang tính tham khảo · Luôn kiểm chứng từ nguồn gốc
          </div>
        </footer>
      </div>
    </>
  );
}

