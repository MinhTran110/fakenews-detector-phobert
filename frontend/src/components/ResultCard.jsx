// src/components/ResultCard.jsx
export function ResultCard({ result }) {
  if (!result) return null;

  const fakePct   = Math.round(result.prob_fake * 100);
  const realPct   = 100 - fakePct;

  // Xác định 3 cấp độ cảnh báo dựa trên xác suất Fake (fakePct)
  let status = "neutral"; // "real" | "neutral" | "fake"
  if (fakePct > 65) {
    status = "fake";
  } else if (fakePct < 35) {
    status = "real";
  }

  // Tùy biến UI theo cấp độ cảnh báo
  let accent = "#fbbf24"; // Màu vàng mặc định cho nghi vấn/trung lập
  let bgColor = "rgba(251,191,36,0.08)";
  let border = "rgba(251,191,36,0.25)";
  let icon = "⚠";
  let headline = "Chưa rõ ràng / Cần lưu ý";
  let descriptionText = "Hệ thống phát hiện một số dấu hiệu đáng ngờ nhưng chưa đủ cơ sở để kết luận. Bạn nên kiểm chứng thêm thông tin.";

  if (status === "fake") {
    accent = "#ef4444"; // Đỏ cho tin giả
    bgColor = "rgba(239,68,68,0.08)";
    border = "rgba(239,68,68,0.25)";
    icon = "🚨";
    headline = "Nguy cơ tin giả cao";
    descriptionText = "Hệ thống phát hiện tỷ lệ thông tin không chính xác hoặc giật gân rất lớn. Hãy hết sức cân nhắc trước khi chia sẻ.";
  } else if (status === "real") {
    accent = "#22c55e"; // Xanh cho tin cậy
    bgColor = "rgba(34,197,94,0.08)";
    border = "rgba(34,197,94,0.25)";
    icon = "✓";
    headline = "Tin cậy cao";
    descriptionText = "Nội dung bài viết có cấu trúc hành văn chuẩn mực và các chỉ số đều an toàn. Tuy nhiên, vẫn nên đọc nguồn uy tín.";
  }

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
          width: 56,
          height: 56,
          borderRadius: "50%",
          background: accent,
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 26,
          color: status === "neutral" ? "#000" : "#fff",
          fontWeight: 900,
        }}>{icon}</div>
        <div>
          <div style={{
            fontSize: 24, fontWeight: 800, color: accent, lineHeight: 1.1,
            fontFamily: "'Syne', sans-serif",
          }}>{headline}</div>
          <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4 }}>
            Chỉ số tin giả:{" "}
            <strong style={{ color: accent }}>
              {fakePct}%
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
            Mức độ giả {fakePct}%
          </span>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2, color: "#22c55e" }}>
            Mức độ thật {realPct}%
          </span>
        </div>
        <div style={{
          height: 8, borderRadius: 99, overflow: "hidden",
          background: "rgba(255,255,255,0.08)",
        }}>
          <div style={{
            height: "100%", borderRadius: 99,
            width: `${fakePct}%`,
            background: "linear-gradient(90deg, #ef4444, #f97316, #22c55e)",
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

      {/* Tóm tắt kết luận thân thiện người dùng */}
      <div style={{
        marginTop: 14, padding: "12px 16px",
        background: "rgba(255,255,255,0.02)",
        borderRadius: 10, fontSize: 12,
        color: "var(--muted)", lineHeight: 1.6,
      }}>
        <strong style={{ color: accent }}>Đánh giá hệ thống:</strong>{" "}
        {descriptionText}
      </div>
    </div>
  );
}

