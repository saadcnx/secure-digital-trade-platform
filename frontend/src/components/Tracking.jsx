import { Badge, fdate } from "./ui";

function Spark({ values }) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pts = values
    .map((v, i) => `${(i / (values.length - 1)) * 120},${30 - ((v - min) / span) * 26 - 2}`)
    .join(" ");
  return (
    <svg width="120" height="30">
      <polyline points={pts} fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

export default function Tracking({ shipment }) {
  const events = [...shipment.events].reverse();
  const temps = shipment.events.filter((e) => e.temperature != null).map((e) => e.temperature);
  return (
    <div className="card">
      <div className="card-h">
        <div>
          <h3>Shipment tracking</h3>
          <p className="muted sm">{shipment.carrier} · <code>{shipment.tracking_number}</code></p>
        </div>
        <Badge s={shipment.status} />
      </div>
      {temps.length > 0 && (
        <div className="cold">
          ❄ Cold chain: {temps[temps.length - 1]}°C now
          <Spark values={temps} />
        </div>
      )}
      <ol className="timeline">
        {events.map((e, i) => (
          <li key={e.id} className={i === 0 ? "now" : ""}>
            <span className="dot" />
            <div className="tl-top">
              <b>{e.location}</b>
              <Badge s={e.status} />
            </div>
            <div className="muted sm">
              {fdate(e.created_at)}
              {e.temperature != null && <> · 🌡 {e.temperature}°C</>}
              {e.source === "service" && <> · 📡 IoT</>}
            </div>
            {e.note && <div className="sm">{e.note}</div>}
          </li>
        ))}
      </ol>
    </div>
  );
}