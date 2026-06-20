// src/App.jsx
import { useState } from "react";
import { usePredictor } from "./hooks/usePredictor";
import { ResultCard }   from "./components/ResultCard";

const SUPPORTED_SITES = [
  "vnexpress.net", "tuoitre.vn", "thanhnien.vn",
  "dantri.com.vn", "zingnews.vn", "baomoi.com",
];

function Spinner({ step }) {
  const msg = step === "scraping"
    ? "Đang đọc bài báo từ URL…"
    : "Đang phân tích với PhoBERT…";
  return (
    <div style={{
      display: "flex", flexDirection: "column",
      alignItems: "center", gap: 16, padding: "36px 0",
    }}>
      <div style={{
        width: 44, height: 44,
        border: "3px solid rgba(255,255,255,0.08)",
        borderTop: "3px solid var(--accent)",
        borderRadius: "50%",
        animation: "spin .7s linear infinite",
      }} />
      <div style={{ fontSize: 14, color: "var(--muted)", fontStyle: "italic" }}>
        {msg}
      </div>
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
      <label style={labelStyle}>URL BÀI BÁO</label>
      <input
        value={url}
        onChange={e => { setUrl(e.target.value); reset(); }}
        onKeyDown={e => e.key === "Enter" && handleSubmit()}
        placeholder="https://vnexpress.net/…"
        style={inputStyle}
        onFocus={e => e.target.style.borderColor = "var(--accent)"}
        onBlur={e  => e.target.style.borderColor = "rgba(255,255,255,0.08)"}
      />

      {/* Quick-fill examples */}
      <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <span style={{ fontSize: 11, color: "var(--muted)" }}>Hỗ trợ:</span>
        {SUPPORTED_SITES.map(site => (
          <span key={site} style={{
            fontSize: 11, padding: "2px 8px", borderRadius: 99,
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.08)",
            color: "var(--muted)",
          }}>{site}</span>
        ))}
      </div>

      {/* Threshold slider */}
      <div style={{ marginTop: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ fontSize: 11, color: "var(--muted)", letterSpacing: 1 }}>NGƯỠNG PHÂN LOẠI</span>
          <span style={{ fontSize: 12, color: "var(--accent)", fontWeight: 700 }}>{threshold.toFixed(2)}</span>
        </div>
        <input
          type="range" min="0.2" max="0.8" step="0.05"
          value={threshold}
          onChange={e => setThreshold(parseFloat(e.target.value))}
          style={{ width: "100%", accentColor: "var(--accent)" }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 2 }}>
          <span style={{ fontSize: 10, color: "var(--muted)" }}>Bắt nhiều Fake hơn</span>
          <span style={{ fontSize: 10, color: "var(--muted)" }}>Chính xác hơn</span>
        </div>
      </div>

      {error && (
        <div style={{
          marginTop: 12, padding: "10px 14px",
          background: "rgba(239,68,68,0.1)",
          border: "1px solid rgba(239,68,68,0.25)",
          borderRadius: 10, fontSize: 13, color: "#ef4444",
        }}>{error}</div>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading || !valid}
        style={btnStyle(loading || !valid)}
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
      <label style={labelStyle}>NỘI DUNG BÀI BÁO</label>
      <textarea
        value={text}
        onChange={e => { setText(e.target.value); reset(); }}
        placeholder="Dán tiêu đề và nội dung bài báo vào đây…"
        style={{
          ...inputStyle,
          minHeight: 180,
          resize: "vertical",
          fontFamily: "'DM Sans', sans-serif",
          lineHeight: 1.7,
        }}
        onFocus={e => e.target.style.borderColor = "var(--accent)"}
        onBlur={e  => e.target.style.borderColor = "rgba(255,255,255,0.08)"}
      />
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
        <span style={{ fontSize: 11, color: "var(--muted)" }}>{text.length} ký tự</span>
        {text.length < 20 && text.length > 0 && (
          <span style={{ fontSize: 11, color: "#f97316" }}>Cần ít nhất 20 ký tự</span>
        )}
      </div>

      <div style={{ marginTop: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ fontSize: 11, color: "var(--muted)", letterSpacing: 1 }}>NGƯỠNG</span>
          <span style={{ fontSize: 12, color: "var(--accent)", fontWeight: 700 }}>{threshold.toFixed(2)}</span>
        </div>
        <input
          type="range" min="0.2" max="0.8" step="0.05"
          value={threshold}
          onChange={e => setThreshold(parseFloat(e.target.value))}
          style={{ width: "100%", accentColor: "var(--accent)" }}
        />
      </div>

      {error && (
        <div style={{
          marginTop: 12, padding: "10px 14px",
          background: "rgba(239,68,68,0.1)",
          border: "1px solid rgba(239,68,68,0.25)",
          borderRadius: 10, fontSize: 13, color: "#ef4444",
        }}>{error}</div>
      )}

      <button
        onClick={() => text.length >= 20 && predictText(text, threshold)}
        disabled={loading || text.length < 20}
        style={btnStyle(loading || text.length < 20)}
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

// ── Styles ────────────────────────────────────────────────────────────────
const labelStyle = {
  display: "block",
  fontSize: 11, fontWeight: 700,
  letterSpacing: 2, color: "var(--muted)",
  marginBottom: 10,
};

const inputStyle = {
  width: "100%", padding: "14px 16px",
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 12, color: "var(--fg)",
  fontSize: 15, outline: "none",
  transition: "border-color .2s",
  boxSizing: "border-box",
};

const btnStyle = (disabled) => ({
  marginTop: 16, width: "100%",
  padding: "14px 0",
  background: disabled ? "rgba(255,255,255,0.06)" : "var(--accent)",
  color: disabled ? "var(--muted)" : "#000",
  border: "none", borderRadius: 12,
  fontSize: 15, fontWeight: 700,
  cursor: disabled ? "not-allowed" : "pointer",
  letterSpacing: 0.5,
  transition: "all .2s",
  fontFamily: "'Syne', sans-serif",
});

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
      <div style={{
        position: "fixed", top: -200, left: "50%",
        transform: "translateX(-50%)",
        width: 600, height: 600, borderRadius: "50%",
        background: "radial-gradient(circle,rgba(124,92,252,0.1) 0%,transparent 70%)",
        pointerEvents: "none", zIndex: 0,
      }} />

      <div style={{
        position: "relative", zIndex: 1,
        maxWidth: 660, margin: "0 auto", padding: "0 20px 60px",
      }}>

        {/* Header */}
        <header style={{ padding: "52px 0 36px", textAlign: "center" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            padding: "5px 14px", borderRadius: 99,
            background: "rgba(200,245,71,0.08)",
            border: "1px solid rgba(200,245,71,0.18)",
            fontSize: 11, fontWeight: 700, letterSpacing: 2,
            color: "var(--accent)", marginBottom: 20,
          }}>
            <span style={{
              width: 6, height: 6, borderRadius: "50%",
              background: "var(--accent)",
              animation: "pulse 2s infinite",
            }} />
            PHOBERT AI · FAKE NEWS DETECTOR
          </div>

          <h1 style={{
            fontSize: "clamp(30px,5.5vw,48px)", fontWeight: 800,
            fontFamily: "'Be Vietnam Pro', sans-serif", lineHeight: 1.1,
            background: "linear-gradient(135deg,#f0eff8 30%,#6b6a7e)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            marginBottom: 14,
          }}>
            Kiểm tra tin giả<br />tiếng Việt
          </h1>

          <p style={{ fontSize: 15, color: "var(--muted)", lineHeight: 1.65 }}>
            Paste URL bài báo hoặc nội dung trực tiếp —<br />
            AI sẽ phân tích và cho kết quả trong vài giây.
          </p>
        </header>

        {/* Card */}
        <div style={{
          background: "var(--bg2)",
          border: "1px solid var(--border)",
          borderRadius: 24,
          overflow: "hidden",
          boxShadow: "0 24px 64px rgba(0,0,0,0.5)",
        }}>
          {/* Tabs */}
          <div style={{
            display: "flex",
            borderBottom: "1px solid var(--border)",
            background: "rgba(255,255,255,0.015)",
          }}>
            {TABS.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)} style={{
                flex: 1, padding: "16px 8px",
                background: "transparent", border: "none",
                borderBottom: tab === t.id
                  ? "2px solid var(--accent)"
                  : "2px solid transparent",
                color: tab === t.id ? "var(--fg)" : "var(--muted)",
                fontSize: 14,
                fontWeight: tab === t.id ? 600 : 400,
                cursor: "pointer", transition: "all .2s",
                fontFamily: "'Inter', sans-serif",
              }}>{t.label}</button>
            ))}
          </div>

          {/* Tab content */}
          <div style={{ padding: "28px" }}>
            {tab === "url"  && <UrlTab />}
            {tab === "text" && <TextTab />}
          </div>
        </div>

        {/* Footer */}
        <footer style={{
          marginTop: 36, textAlign: "center",
          fontSize: 12, color: "var(--muted)", lineHeight: 1.8,
        }}>
          <div>
            Powered by{" "}
            <strong style={{ color: "var(--fg)" }}>PhoBERT</strong>
            {" "}·{" "}
            <span style={{ opacity: 0.6 }}>vinai/phobert-base-v2</span>
          </div>
          <div style={{ marginTop: 4, opacity: 0.5, fontSize: 11 }}>
            Kết quả chỉ mang tính tham khảo · Luôn kiểm chứng từ nguồn gốc
          </div>
        </footer>
      </div>
    </>
  );
}
