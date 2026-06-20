// src/components/ResultCard.jsx
export function ResultCard({ result }) {
  if (!result) return null;

  const isFake    = result.label === "FAKE";
  const accent    = isFake ? "#ef4444" : "#22c55e";
  const bgColor   = isFake ? "rgba(239,68,68,0.08)" : "rgba(34,197,94,0.08)";
  const border    = isFake ? "rgba(239,68,68,0.25)" : "rgba(34,197,94,0.25)";
  const icon      = isFake ? "⚠" : "✓";
  const headline  = isFake ? "Có khả năng là tin giả" : "Có vẻ đáng tin cậy";
  const fakePct   = Math.round(result.prob_fake * 100);
  const realPct   = 100 - fakePct;

  return (
    <div style={{
      background: bgColor,
      border: `1px solid ${border}`,
      borderRadius: 16,
      padding: "24px 28px",
      animation: "slideUp .4s cubic-bezier(.16,1,.3,1)",
    }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{
          width: 56, height: 56, borderRadius: "50%",
          background: accent, flexShrink: 0,
          display: "flex", alignItems: "center",
          justifyContent: "center",
          fontSize: 26, color: "#fff", fontWeight: 900,
        }}>{icon}</div>
        <div>
          <div style={{
            fontSize: 24, fontWeight: 800, color: accent, lineHeight: 1.1,
            fontFamily: "'Syne', sans-serif",
          }}>{headline}</div>
          <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4 }}>
            Độ tin cậy:{" "}
            <strong style={{ color: accent }}>
              {Math.round(result.confidence * 100)}%
            </strong>
            {result.processing_time_ms && (
              <span style={{ marginLeft: 10, opacity: 0.6 }}>
                · {result.processing_time_ms}ms
              </span>
            )}
            {result.cached && (
              <span style={{ marginLeft: 10, opacity: 0.6 }}>· cached</span>
            )}
          </div>
        </div>
      </div>

      {/* Probability bar */}
      <div style={{ marginTop: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2, color: "#ef4444" }}>
            FAKE {fakePct}%
          </span>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2, color: "#22c55e" }}>
            REAL {realPct}%
          </span>
        </div>
        <div style={{
          height: 8, borderRadius: 99, overflow: "hidden",
          background: "rgba(255,255,255,0.08)",
        }}>
          <div style={{
            height: "100%", borderRadius: 99,
            width: `${fakePct}%`,
            background: "linear-gradient(90deg, #ef4444, #f97316)",
            transition: "width 0.9s cubic-bezier(.16,1,.3,1)",
          }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
          <span style={{ fontSize: 10, color: "var(--muted)" }}>← Tin giả</span>
          <span style={{ fontSize: 10, color: "var(--muted)" }}>Đáng tin →</span>
        </div>
      </div>

      {/* Article info (nếu từ URL) */}
      {result.article && (
        <div style={{
          marginTop: 18, padding: "14px 16px",
          background: "rgba(255,255,255,0.04)",
          borderRadius: 10,
        }}>
          {result.article.title && (
            <div style={{
              fontSize: 14, fontWeight: 600,
              color: "var(--fg)", marginBottom: 6, lineHeight: 1.4,
            }}>
              {result.article.title}
            </div>
          )}
          {result.article.excerpt && (
            <div style={{
              fontSize: 12, color: "var(--muted)", lineHeight: 1.6,
            }}>
              {result.article.excerpt}
            </div>
          )}
          <a
            href={result.article.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-block", marginTop: 8,
              fontSize: 11, color: "var(--accent)",
              textDecoration: "none", letterSpacing: 0.5,
            }}
          >
            Xem bài gốc ↗
          </a>
        </div>
      )}

      {/* Warning */}
      {result.warning && (
        <div style={{
          marginTop: 14, padding: "10px 14px",
          background: "rgba(251,191,36,0.1)",
          border: "1px solid rgba(251,191,36,0.3)",
          borderRadius: 8, fontSize: 12, color: "#fbbf24",
        }}>
          ⚠ {result.warning}
        </div>
      )}

      {/* Disclaimer nếu FAKE */}
      {isFake && (
        <div style={{
          marginTop: 14, padding: "12px 16px",
          background: "rgba(239,68,68,0.06)",
          borderRadius: 10, fontSize: 12,
          color: "var(--muted)", lineHeight: 1.6,
        }}>
          <strong style={{ color: "#ef4444" }}>Lưu ý:</strong>{" "}
          Kết quả do AI phân tích, có thể không chính xác 100%.
          Hãy kiểm tra từ nhiều nguồn uy tín trước khi chia sẻ.
        </div>
      )}
    </div>
  );
}
