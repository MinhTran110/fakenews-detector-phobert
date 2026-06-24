// src/App.jsx
import { useState, useEffect } from "react";
import { usePredictor } from "./hooks/usePredictor";
import { ResultCard }   from "./components/ResultCard";
import styles from "./App.module.css";
import hStyles from "./History.module.css";

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
function UrlTab({ onAddHistory, forcedResult, onResetForce }) {
  const [url, setUrl] = useState("");
  const [threshold, setThreshold] = useState(0.5);
  const { loading, result, error, step, predictUrl, reset, setResult } = usePredictor();

  useEffect(() => {
    if (forcedResult && forcedResult.type === "url") {
      setUrl(forcedResult.url);
      setThreshold(forcedResult.threshold || 0.5);
      setResult(forcedResult.result);
      onResetForce();
    }
  }, [forcedResult]);

  const valid = (() => {
    try { new URL(url); return url.startsWith("http"); }
    catch { return false; }
  })();

  async function handleSubmit() {
    if (!valid) return;
    const data = await predictUrl(url, threshold);
    if (data) {
      onAddHistory({
        id: "url-" + Date.now(),
        type: "url",
        label: url,
        url: url,
        threshold: threshold,
        result: data,
        timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      });
    }
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
function TextTab({ onAddHistory, forcedResult, onResetForce }) {
  const [text, setText] = useState("");
  const [threshold, setThreshold] = useState(0.5);
  const { loading, result, error, step, predictText, reset, setResult } = usePredictor();

  useEffect(() => {
    if (forcedResult && forcedResult.type === "text") {
      setText(forcedResult.text);
      setThreshold(forcedResult.threshold || 0.5);
      setResult(forcedResult.result);
      onResetForce();
    }
  }, [forcedResult]);

  async function handleSubmit() {
    if (text.length < 20) return;
    const data = await predictText(text, threshold);
    if (data) {
      onAddHistory({
        id: "text-" + Date.now(),
        type: "text",
        label: text.substring(0, 36) + "...",
        text: text,
        threshold: threshold,
        result: data,
        timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      });
    }
  }

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
        onClick={handleSubmit}
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
  const [history, setHistory] = useState([]);
  const [forcedResult, setForcedResult] = useState(null);

  // Load history from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("fakenews_history");
    if (saved) {
      try { setHistory(JSON.parse(saved)); } catch (e) {}
    }
  }, []);

  const addHistoryItem = (item) => {
    const newHistory = [item, ...history.filter(h => h.label !== item.label)].slice(0, 5);
    setHistory(newHistory);
    localStorage.setItem("fakenews_history", JSON.stringify(newHistory));
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem("fakenews_history");
  };

  const deleteHistoryItem = (id, e) => {
    e.stopPropagation(); // Ngăn sự kiện click vào item kích hoạt xem lại kết quả
    const newHistory = history.filter(h => h.id !== id);
    setHistory(newHistory);
    localStorage.setItem("fakenews_history", JSON.stringify(newHistory));
  };

  const handleHistoryClick = (item) => {
    setTab(item.type);
    setForcedResult(item);
  };

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
            {tab === "url"  && (
              <UrlTab
                onAddHistory={addHistoryItem}
                forcedResult={forcedResult}
                onResetForce={() => setForcedResult(null)}
              />
            )}
            {tab === "text" && (
              <TextTab
                onAddHistory={addHistoryItem}
                forcedResult={forcedResult}
                onResetForce={() => setForcedResult(null)}
              />
            )}
          </div>
        </div>

        {/* History Section */}
        {history.length > 0 && (
          <div className={hStyles.historySection}>
            <div className={hStyles.historyHeader}>
              <span className={hStyles.historyTitle}>Lịch sử kiểm tra gần đây</span>
              <button className={hStyles.clearBtn} onClick={clearHistory}>Xóa tất cả</button>
            </div>
            <div className={hStyles.historyList}>
              {history.map(item => {
                const fakePct = Math.round(item.result.prob_fake * 100);
                let badgeClass = hStyles.badgeNeutral;
                let badgeText = `Nghi vấn ${fakePct}%`;

                if (fakePct > 65) {
                  badgeClass = hStyles.badgeFake;
                  badgeText = `Giả ${fakePct}%`;
                } else if (fakePct < 35) {
                  badgeClass = hStyles.badgeReal;
                  badgeText = `Thật ${100 - fakePct}%`;
                }

                return (
                  <div
                    key={item.id}
                    className={hStyles.historyItem}
                    onClick={() => handleHistoryClick(item)}
                  >
                    <div className={hStyles.itemMain}>
                      <span className={hStyles.itemLabel}>{item.label}</span>
                      <span className={hStyles.itemMeta}>Loại: {item.type === "url" ? "URL" : "Đoạn văn"} · lúc {item.timestamp}</span>
                    </div>
                    <span className={badgeClass} style={{ marginRight: 24 }}>{badgeText}</span>
                    <button
                      className={hStyles.deleteItemBtn}
                      onClick={(e) => deleteHistoryItem(item.id, e)}
                      title="Xóa dòng này"
                    >
                      &times;
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

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


