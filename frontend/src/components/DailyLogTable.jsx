import FmcsaLogSheet from "./FmcsaLogSheet";

export default function DailyLogTable({ logs = [] }) {
  if (!logs.length) {
    return <p className="muted">Daily logs will appear here after plan generation.</p>;
  }

  return (
    <div className="logs-wrap">
      <div className="logs-actions">
        <button type="button" className="secondary-btn" onClick={() => window.print()}>
          Print / Save PDF
        </button>
        <button
          type="button"
          className="secondary-btn"
          onClick={() => {
            const blob = new Blob([JSON.stringify(logs, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = "daily_logs.json";
            link.click();
            URL.revokeObjectURL(url);
          }}
        >
          Download JSON
        </button>
      </div>
      {logs.map((log) => (
        <FmcsaLogSheet key={log.date} log={log} />
      ))}
    </div>
  );
}
