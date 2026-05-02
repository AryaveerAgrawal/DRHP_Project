function FileCard({ item, onRemove }) {
  const fileType = item.file.type;
  const c = item.aiData?.result1_classification;
  const t = item.aiData?.result2_capital_table;

  const thStyle = {
    border: "1px solid #999",
    padding: "8px 12px",
    textAlign: "left",
    fontWeight: "bold",
    backgroundColor: "#333",
    color: "#fff"
  };

  const tdStyle = {
    border: "1px solid #555",
    padding: "8px 12px",
    verticalAlign: "top",
    color: "#eee"
  };

  return (
    <div className="file-card">

      {item.loading ? (
        <div style={{ color: "gray", marginBottom: "10px" }}>
          Processing...
        </div>
      ) : item.error ? (
        <div style={{ color: "red", marginBottom: "10px" }}>
          ❌ Error: {item.error}
        </div>
      ) : item.aiData ? (
        <div style={{ marginBottom: "10px", color: "white" }}>

          {/* ── RESULT 1: Classification ── */}
          {c && (
            <div style={{ marginBottom: "1.5rem", border: "1px solid #444", borderRadius: "8px", padding: "1rem" }}>
              <h3 style={{ borderBottom: "1px solid #555", paddingBottom: "0.5rem", marginTop: 0 }}>
                Result 1: Document Classification
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <tbody>
                  {[
                    ["Document Type", c.doc_type, `${c.doc_type_confidence}% confidence`],
                    ["Filing Status", c.filing_status, ""],
                    ["Corporate Event", c.corporate_event, `${c.event_confidence}% confidence`],
                  ].map(([label, value, note]) => (
                    <tr key={label} style={{ borderBottom: "1px solid #333" }}>
                      <td style={{ ...tdStyle, color: "#aaa", fontWeight: "bold", width: "180px" }}>{label}</td>
                      <td style={tdStyle}>{value}</td>
                      <td style={{ ...tdStyle, color: "#777", fontSize: "0.82rem" }}>{note}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* ── RESULT 2: DRHP Capital Table ── */}
          {t && (
            <div style={{ border: "1px solid #444", borderRadius: "8px", padding: "1rem" }}>
              <h3 style={{ borderBottom: "1px solid #555", paddingBottom: "0.5rem", marginTop: 0 }}>
                Result 2: Draft Capital Structure Table (DRHP Format)
              </h3>
              <p style={{ color: "#aaa", fontSize: "0.9rem" }}>
                Company: <strong style={{ color: "#eee" }}>{t.company_name}</strong>
              </p>

              {t.capital_table?.length > 0 ? (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                    <thead>
                      <tr>
                        <th style={thStyle} rowSpan={2}>Date of Shareholder's Meeting</th>
                        <th style={{ ...thStyle, textAlign: "center" }} colSpan={2}>Particulars of Change</th>
                        <th style={thStyle} rowSpan={2}>AGM/EGM</th>
                        <th style={thStyle} rowSpan={2}>Source Doc</th>
                        <th style={thStyle} rowSpan={2}>Shares</th>
                        <th style={thStyle} rowSpan={2}>Face Value</th>
                      </tr>
                      <tr>
                        <th style={thStyle}>From</th>
                        <th style={thStyle}>To</th>
                      </tr>
                    </thead>
                    <tbody>
                      {t.capital_table.map((row, i) => (
                        <tr key={i} style={{ borderBottom: "1px solid #333" }}>
                          <td style={tdStyle}>{row.date}</td>
                          <td style={tdStyle}>{row.from}</td>
                          <td style={tdStyle}>{row.to}</td>
                          <td style={{ ...tdStyle, textAlign: "center" }}>{row.meeting_type}</td>
                          <td style={{
                            ...tdStyle,
                            color: row.source_doc?.includes("UNCONFIRMED") ? "#ff6b6b" : "#90ee90"
                          }}>
                            {row.source_doc}
                          </td>
                          <td style={tdStyle}>{row.num_shares}</td>
                          <td style={tdStyle}>{row.face_value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p style={{ color: "#888" }}>No capital change events found in document.</p>
              )}

              <p style={{ marginTop: "1rem", fontSize: "0.8rem", color: "#666", fontStyle: "italic" }}>
                * Fields marked [UNCONFIRMED] in red could not be verified from the document.
              </p>
            </div>
          )}

        </div>
      ) : null}

      {/* ── FILE PREVIEW BOX ── */}
      <div className="preview-box">
        {fileType.startsWith("image/") && (
          <img src={item.preview} alt="preview" />
        )}
        {fileType === "application/pdf" && (
          <iframe
            src={URL.createObjectURL(item.file)}
            title="PDF"
          />
        )}
        {!fileType.startsWith("image/") && fileType !== "application/pdf" && (
          <div className="file-info">
            📄 {item.file.name}
          </div>
        )}
      </div>

      {/* ── REMOVE BUTTON ── */}
      <button className="remove-btn" onClick={onRemove}>
        Remove
      </button>

    </div>
  );
}

export default FileCard;