import { useState } from "react";
import CapitalTable from "./CapitalTable";

function FileUpload() {
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [finalTable, setFinalTable] = useState([]);
  const [summary, setSummary]     = useState(null);
  const [debug, setDebug]         = useState(null);
  const [fileCount, setFileCount] = useState(0);

  const handleChange = async (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (!selectedFiles.length) return;

    setFileCount(selectedFiles.length);
    setLoading(true);
    setError(null);
    setFinalTable([]);
    setSummary(null);
    setDebug(null);

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      // Send with relative path so backend knows folder structure
      formData.append("files", file, file.webkitRelativePath || file.name);
    });

    try {
      const response = await fetch("http://127.0.0.1:8000/upload-folder", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText);
      }

      const data = await response.json();
      console.log("API RESPONSE:", data);

      setFinalTable(data.final_capital_table || []);
      setSummary({
        message:      data.message,
        company:      data.company_name,
        groups:       data.groups_found || [],
      });
      setDebug(data.debug_classifications || {});

    } catch (err) {
      console.error("Upload failed:", err);
      setError("Upload failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h2>Upload SH-7 Folder</h2>

      {/* ── Folder picker ── */}
      <input
        type="file"
        multiple
        webkitdirectory="true"
        onChange={handleChange}
        style={{ marginBottom: "12px" }}
      />

      {/* ── Status ── */}
      {fileCount > 0 && !loading && (
        <p style={{ color: "#aaa", fontSize: "0.85rem" }}>
          {fileCount} file(s) uploaded
        </p>
      )}
      {loading && <p style={{ color: "#aaa" }}>⏳ Processing {fileCount} documents...</p>}
      {error   && <p style={{ color: "red" }}>❌ {error}</p>}

      {/* ── Summary banner ── */}
      {summary && (
        <div style={{
          background: "#0d3349", border: "1px solid #2E75B6",
          borderRadius: "6px", padding: "0.8rem 1.2rem",
          margin: "1rem 0", display: "flex", gap: "2rem", flexWrap: "wrap",
          fontSize: "0.88rem"
        }}>
          <span><span style={{ color: "#aaa" }}>Company:</span>{" "}
            <strong style={{ color: "#fff" }}>{summary.company}</strong></span>
          <span><span style={{ color: "#aaa" }}>Groups:</span>{" "}
            <strong style={{ color: "#90ee90" }}>{summary.groups.join(", ")}</strong></span>
          <span><span style={{ color: "#aaa" }}>Capital Events:</span>{" "}
            <strong style={{ color: "#90ee90" }}>{finalTable.length}</strong></span>
        </div>
      )}

      {/* ── Main DRHP table ── */}
      {!loading && finalTable.length > 0 && (
        <CapitalTable data={finalTable} />
      )}

      {/* ── Empty state ── */}
      {!loading && summary && finalTable.length === 0 && (
        <div style={{ color: "#aaa", padding: "1.5rem", textAlign: "center" }}>
          ⚠️ No capital events extracted. Make sure your SH-7 files contain capital
          amounts like "Rs. 5,00,000 divided into 50,000 Equity Shares of Rs. 10 each".
        </div>
      )}

      {/* ── Debug: per-group classification ── */}
      {debug && Object.keys(debug).length > 0 && (
        <details style={{ marginTop: "1.5rem" }}>
          <summary style={{ cursor: "pointer", color: "#2E75B6", fontWeight: "bold", fontSize: "0.9rem" }}>
            🔍 Debug: Per-group classification
          </summary>
          <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "0.5rem", fontSize: "0.82rem" }}>
            <thead>
              <tr>
                {["Group","Doc Type","Filing Status","Corporate Event","Doc Conf","Event Conf"].map(h => (
                  <th key={h} style={{ border:"1px solid #555", padding:"8px", background:"#333", color:"#fff" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(debug).map(([gid, cls], i) => (
                <tr key={i}>
                  <td style={{ border:"1px solid #444", padding:"8px", color:"#eee" }}>{gid}</td>
                  <td style={{ border:"1px solid #444", padding:"8px", color:"#eee" }}>{cls.doc_type}</td>
                  <td style={{ border:"1px solid #444", padding:"8px", color:"#eee" }}>{cls.filing_status}</td>
                  <td style={{ border:"1px solid #444", padding:"8px", color:"#eee" }}>{cls.corporate_event}</td>
                  <td style={{ border:"1px solid #444", padding:"8px",
                    color: cls.doc_type_confidence >= 65 ? "#90ee90" : "#ffd700" }}>
                    {cls.doc_type_confidence}%
                  </td>
                  <td style={{ border:"1px solid #444", padding:"8px",
                    color: cls.event_confidence >= 65 ? "#90ee90" : "#ffd700" }}>
                    {cls.event_confidence}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </div>
  );
}

export default FileUpload;