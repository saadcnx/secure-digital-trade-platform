import { useCallback, useEffect, useState } from "react";

export const CURRENCIES = ["USD", "EUR", "GBP", "PKR"];
export const COUNTRIES = {
  US: "United States", GB: "United Kingdom", DE: "Germany", FR: "France", PK: "Pakistan", AE: "UAE",
  CA: "Canada", AU: "Australia", IN: "India", CN: "China", SA: "Saudi Arabia", TR: "Turkey",
  NL: "Netherlands", IT: "Italy", ES: "Spain", JP: "Japan",
};

export const flag = (cc) =>
  cc && cc.length === 2 ? String.fromCodePoint(...[...cc.toUpperCase()].map((c) => 127397 + c.charCodeAt(0))) : "🏳";

export const money = (v, cur = "USD") =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: cur,
    maximumFractionDigits: cur === "PKR" ? 0 : 2,
  }).format(Number(v));

export const fdate = (d) => new Date(d).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });

const TONE = {
  created: "gray", paid: "blue", packed: "indigo", shipped: "cyan", delivered: "green", cancelled: "red",
  refunded: "amber", succeeded: "green", failed: "red", pending: "gray", pending_review: "amber",
  in_transit: "cyan", label_created: "gray", picked_up: "indigo", customs_clearance: "amber",
  out_for_delivery: "blue", delayed: "amber", exception: "red", temperature_alert: "red", returned: "amber",
  buyer: "gray", seller: "indigo", admin: "red", review: "amber", active: "green", inactive: "red",
};

export const Badge = ({ s, children }) => (
  <span className={"badge " + (TONE[s] || "gray")}>{children || String(s).replaceAll("_", " ")}</span>
);

export const Stars = ({ value = 0, size = 16 }) => (
  <span className="stars" style={{ fontSize: size }}>
    {[1, 2, 3, 4, 5].map((i) => (
      <i key={i} className={i <= Math.round(value) ? "on" : ""}>★</i>
    ))}
  </span>
);

export const StarInput = ({ value, onChange }) => (
  <span className="stars input">
    {[1, 2, 3, 4, 5].map((i) => (
      <i key={i} className={i <= value ? "on" : ""} onClick={() => onChange(i)}>★</i>
    ))}
  </span>
);

export const Loading = () => (
  <div className="empty"><div className="spin" /></div>
);

export const Empty = ({ icon = "📭", title, children }) => (
  <div className="empty">
    <div className="big">{icon}</div>
    <h3>{title}</h3>
    {children && <p>{children}</p>}
  </div>
);

export const Field = ({ label, hint, children }) => (
  <label className="field">
    <span>{label}</span>
    {children}
    {hint && <small>{hint}</small>}
  </label>
);

export function Modal({ title, onClose, children, wide }) {
  useEffect(() => {
    const h = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  return (
    <div className="overlay" onMouseDown={onClose}>
      <div className={"modal" + (wide ? " wide" : "")} onMouseDown={(e) => e.stopPropagation()}>
        <div className="modal-h">
          <h3>{title}</h3>
          <button className="x" onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Panel({ title, tabs, tab, setTab, children }) {
  return (
    <div className="container page">
      <div className="panel">
        <aside className="side">
          <h4>{title}</h4>
          {tabs.map(([k, l]) => (
            <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>
          ))}
        </aside>
        <section className="main">{children}</section>
      </div>
    </div>
  );
}

export function useLoad(fn, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fn());
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => {
    run();
  }, [run]);
  return { data, loading, error, reload: run, setData };
}