function CapitalTable({ data }) {
  if (!data || data.length === 0) return null;

  return (
    <div style={{ marginTop: "30px" }}>
      <h2>Authorised Share Capital Change</h2>

      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Date of Shareholder’s Meeting</th>
            <th style={styles.th}>From</th>
            <th style={styles.th}>To</th>
            <th style={styles.th}>AGM / EGM</th>
            <th style={styles.th}>Source Document</th>
          </tr>
        </thead>

        <tbody>
          {data.map((row, index) => (
            <tr key={index}>
              <td style={styles.td}>{row.date}</td>
              <td style={styles.td}>{row.from}</td>
              <td style={styles.td}>{row.to}</td>
              <td style={styles.td}>{row.agm_egm}</td>
              <td style={styles.td}>{row.source_doc}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const styles = {
  table: {
    width: "100%",
    borderCollapse: "collapse",
    marginTop: "15px",
    background: "#1e1e1e",
    color: "white",
  },
  th: {
    border: "1px solid #555",
    padding: "10px",
    background: "#333",
    fontWeight: "bold",
  },
  td: {
    border: "1px solid #555",
    padding: "10px",
    verticalAlign: "top",
  },
};

export default CapitalTable;