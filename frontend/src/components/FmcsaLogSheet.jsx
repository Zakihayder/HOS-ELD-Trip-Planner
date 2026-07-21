const STATUSES = [
  { key: "Off Duty", label: "Off Duty" },
  { key: "Sleeper Berth", label: "Sleeper Berth" },
  { key: "Driving", label: "Driving" },
  { key: "On Duty (Not Driving)", label: "On Duty (Not Driving)" },
];

function yForStatus(status) {
  const index = STATUSES.findIndex((item) => item.key === status);
  return index < 0 ? 0 : index;
}

function buildPolylinePoints(segments, width, rowHeight) {
  if (!segments?.length) {
    return "";
  }

  const sorted = [...segments].sort((a, b) => a.start_hour - b.start_hour);
  const points = [];

  let first = sorted[0];
  points.push([first.start_hour / 24 * width, yForStatus(first.status) * rowHeight + rowHeight / 2]);

  for (let i = 0; i < sorted.length; i += 1) {
    const segment = sorted[i];
    const rowY = yForStatus(segment.status) * rowHeight + rowHeight / 2;
    points.push([segment.end_hour / 24 * width, rowY]);

    const next = sorted[i + 1];
    if (next) {
      const nextY = yForStatus(next.status) * rowHeight + rowHeight / 2;
      points.push([segment.end_hour / 24 * width, nextY]);
    }
  }

  return points.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(" ");
}

export default function FmcsaLogSheet({ log }) {
  const width = 960;
  const rowHeight = 54;
  const height = rowHeight * 4;
  const polyline = buildPolylinePoints(log.graph_segments, width, rowHeight);

  return (
    <article className="log-sheet">
      <div className="log-meta-grid">
        <p>Date: {log.date}</p>
        <p>Total miles driving today: {log.total_miles_driving_today}</p>
        <p>Total truck miles today: {log.total_truck_miles_today}</p>
        <p>Driver number: {log.driver_number}</p>
        <p>Driver initials: {log.driver_initials}</p>
        <p>Vehicle numbers: {log.vehicle_numbers}</p>
        <p>Name of carrier: {log.carrier_name}</p>
        <p>Main office address: {log.main_office_address}</p>
        <p>Home terminal: {log.home_terminal}</p>
        <p>Tractor number: {log.tractor_number}</p>
        <p>Trailer numbers: {log.trailer_numbers}</p>
        <p>Driver signature: {log.driver_signature}</p>
        <p>Co-driver: {log.co_driver_name}</p>
        <p>Shipper: {log.shipper_name}</p>
        <p>Commodity: {log.commodity}</p>
        <p>Load ID: {log.load_id}</p>
        <p>Shipping document: {log.shipping_document}</p>
      </div>

      <div className="graph-wrap">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="24-hour FMCSA duty status graph">
          <rect x="0" y="0" width={width} height={height} fill="#fff" stroke="#372f25" strokeWidth="1.2" />

          {Array.from({ length: 97 }).map((_, tick) => (
            <line
              key={`v-${tick}`}
              x1={(tick / 96) * width}
              y1="0"
              x2={(tick / 96) * width}
              y2={height}
              stroke={tick % 4 === 0 ? "#8f7f66" : "#d7ccb8"}
              strokeWidth={tick % 4 === 0 ? "1.1" : "0.4"}
            />
          ))}

          {STATUSES.map((_, row) => (
            <line
              key={`h-${row}`}
              x1="0"
              y1={row * rowHeight}
              x2={width}
              y2={row * rowHeight}
              stroke="#b7a993"
              strokeWidth="0.9"
            />
          ))}

          {polyline ? (
            <polyline points={polyline} fill="none" stroke="#0f766e" strokeWidth="3" strokeLinejoin="miter" />
          ) : null}
        </svg>

        <div className="graph-labels">
          {STATUSES.map((status) => (
            <p key={status.key}>{status.label}</p>
          ))}
        </div>
      </div>

      <div className="log-remarks">
        <h4>Remarks</h4>
        <ul>
          {log.remarks.length ? log.remarks.map((remark) => <li key={remark}>{remark}</li>) : <li>No remarks.</li>}
        </ul>
      </div>

      <div className="totals-row">
        <p>Off Duty: {log.totals.off_duty_hhmm}</p>
        <p>Sleeper Berth: {log.totals.sleeper_hhmm}</p>
        <p>Driving: {log.totals.driving_hhmm}</p>
        <p>On Duty (Not Driving): {log.totals.on_duty_hhmm}</p>
        <p>Total: {log.totals.all_status_total}h</p>
        <p>Driving + On-duty (decimal): {log.totals.on_duty_plus_driving_hours_decimal}</p>
        <p>Driving + On-duty (hh:mm): {log.totals.on_duty_plus_driving_hhmm}</p>
      </div>
    </article>
  );
}
