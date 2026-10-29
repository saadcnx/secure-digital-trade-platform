import { useState } from "react";
import { api } from "../api";
import { useApp } from "../state";
import Tracking from "./Tracking";
import { Badge, Empty, ErrorBox, Field, Loading, Modal, fdate, money, useLoad } from "./ui";

const NEXT = {
  created: ["cancelled"],
  paid: ["packed", "cancelled", "refunded"],
  packed: ["shipped", "cancelled", "refunded"],
  shipped: ["delivered", "refunded"],
  delivered: ["refunded"],
  cancelled: [],
  refunded: [],
};

const EVENT_STATUS = [
  "picked_up", "in_transit", "customs_clearance", "out_for_delivery",
  "delivered", "delayed", "exception", "temperature_alert", "returned",
];

export function OrdersTable({ admin }) {
  const [status, setStatus] = useState("");
  const [open, setOpen] = useState(null);
  const list = useLoad(() => api("/orders", { params: { status, limit: 100 } }), [status]);
  return (
    <div className="card">
      <div className="card-h">
        <h3>Orders</h3>
        <select className="sel" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {Object.keys(NEXT).map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>
      {list.loading && !list.data ? (
        <Loading />
      ) : list.error ? (
        <ErrorBox error={list.error} onRetry={list.reload} />
      ) : !list.data?.length ? (
        <Empty icon="🧾" title="No orders yet">Orders will appear here.</Empty>
      ) : (
        <div className="scroll">
          <table className="tbl">
            <thead>
              <tr><th>#</th><th>Date</th><th>Items</th><th>Total</th><th>Status</th><th /></tr>
            </thead>
            <tbody>
              {list.data.map((o) => (
                <tr key={o.id}>
                  <td><b>#{o.id}</b></td>
                  <td>{fdate(o.created_at)}</td>
                  <td>{o.items.map((i) => `${i.quantity}× ${i.name}`).join(", ")}</td>
                  <td>{money(o.total, o.currency)}</td>
                  <td>
                    <Badge s={o.status} />
                    {o.on_hold && <Badge s="review">on hold</Badge>}
                  </td>
                  <td><button className="btn ghost sm" onClick={() => setOpen(o.id)}>Manage</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && <OrderManager id={open} admin={admin} onClose={() => setOpen(null)} onChanged={list.reload} />}
    </div>
  );
}

export function OrderManager({ id, admin, onClose, onChanged }) {
  const { notify } = useApp();
  const o = useLoad(() => api(`/orders/${id}`), [id]);
  const [reason, setReason] = useState("");

  async function act(fn, ok) {
    try {
      await fn();
      notify(ok);
      o.reload();
      onChanged();
    } catch (e) {
      notify(e.message, "err");
    }
  }

  const setStatus = (st) =>
    act(() => api(`/orders/${id}/status`, { method: "PATCH", body: { status: st } }), `Order marked ${st}`);
  const hold = () =>
    act(() => api(`/orders/${id}/hold`, { method: "POST", body: { reason: reason.trim() } }), "Order put on hold");
  const release = () => act(() => api(`/orders/${id}/release`, { method: "POST" }), "Order released");

  const order = o.data;
  return (
    <Modal title={`Order #${id}`} onClose={onClose} wide>
      {o.error && !order ? (
        <ErrorBox error={o.error} onRetry={o.reload} />
      ) : !order ? (
        <Loading />
      ) : (
        <>
          <div className="spread" style={{ marginBottom: 14 }}>
            <div className="gap">
              <Badge s={order.status} />
              {order.on_hold && <Badge s="review">on hold: {order.hold_reason}</Badge>}
              {order.fraud_decision && <Badge s={order.fraud_decision === "allow" ? "green" : "review"}>fraud: {order.fraud_decision}</Badge>}
              {order.compliance_decision && <Badge s="gray">compliance: {order.compliance_decision}</Badge>}
            </div>
            <b>{money(order.total, order.currency)}</b>
          </div>

          <div className="scroll">
            <table className="tbl">
              <thead><tr><th>Item</th><th>Origin</th><th>HS code</th><th>Qty</th><th>Line</th></tr></thead>
              <tbody>
                {order.items.map((i, k) => (
                  <tr key={k}>
                    <td>{i.name}</td>
                    <td>{i.origin_country}</td>
                    <td>{i.hs_code || "—"}</td>
                    <td>{i.quantity}</td>
                    <td>{money(i.line_total, order.currency)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="muted sm mt">
            📍 Ship to: {order.shipping_address.full_name}, {order.shipping_address.line1}, {order.shipping_address.city},{" "}
            {order.shipping_address.postal_code}, {order.shipping_address.country}
          </p>

          <div className="card mt" style={{ boxShadow: "none", border: "1px solid var(--line)" }}>
            <div className="card-h"><h3>Order actions</h3></div>
            <div className="gap">
              {NEXT[order.status].filter((t) => admin || t === "packed").map((t) => (
                <button key={t} className={"btn sm " + (t === "cancelled" || t === "refunded" ? "danger" : "ghost")} onClick={() => setStatus(t)}>
                  Mark {t}
                </button>
              ))}
              {!admin && <span className="muted sm">Shipping and delivery are updated through the shipment below.</span>}
            </div>
            {admin && (
              <div className="gap mt">
                {order.on_hold ? (
                  <button className="btn sm" onClick={release}>Release hold</button>
                ) : (
                  <>
                    <input className="sel" style={{ minWidth: 240 }} placeholder="Hold reason..." value={reason} onChange={(e) => setReason(e.target.value)} />
                    <button className="btn sm danger" disabled={!reason.trim()} onClick={hold}>Hold order</button>
                  </>
                )}
              </div>
            )}
          </div>

          <ShipmentManager order={order} onChanged={() => { o.reload(); onChanged(); }} />
        </>
      )}
    </Modal>
  );
}

function ShipmentManager({ order, onChanged }) {
  const { notify } = useApp();
  const s = useLoad(() => api(`/shipments/orders/${order.id}`).catch(() => null), [order.id]);
  const [c, setC] = useState({ carrier: "DHL Express", tracking_number: "", origin: "" });
  const [e, setE] = useState({ status: "in_transit", location: "", temperature: "", note: "" });

  async function create(ev) {
    ev.preventDefault();
    try {
      await api(`/shipments/orders/${order.id}`, {
        method: "POST",
        body: { carrier: c.carrier, tracking_number: c.tracking_number || null, origin: c.origin || null },
      });
      notify("Shipment created");
      s.reload();
      onChanged();
    } catch (err) {
      notify(err.message, "err");
    }
  }

  async function addEvent(ev) {
    ev.preventDefault();
    try {
      await api(`/shipments/${s.data.id}/events`, {
        method: "POST",
        body: {
          status: e.status,
          location: e.location,
          temperature: e.temperature === "" ? null : Number(e.temperature),
          note: e.note || null,
        },
      });
      notify("Tracking updated");
      setE({ ...e, location: "", temperature: "", note: "" });
      s.reload();
      onChanged();
    } catch (err) {
      notify(err.message, "err");
    }
  }

  const canCreate = ["paid", "packed", "shipped"].includes(order.status) && !order.on_hold;
  if (s.loading && !s.data) return <Loading />;

  if (!s.data) {
    return (
      <div className="card mt" style={{ boxShadow: "none", border: "1px solid var(--line)" }}>
        <div className="card-h"><h3>📦 Shipment</h3></div>
        {canCreate ? (
          <form className="form" onSubmit={create}>
            <div className="row">
              <Field label="Carrier"><input required value={c.carrier} onChange={(x) => setC({ ...c, carrier: x.target.value })} /></Field>
              <Field label="Tracking number" hint="Leave empty to auto-generate"><input value={c.tracking_number} onChange={(x) => setC({ ...c, tracking_number: x.target.value })} /></Field>
            </div>
            <Field label="Origin location"><input placeholder="Karachi Warehouse, PK" value={c.origin} onChange={(x) => setC({ ...c, origin: x.target.value })} /></Field>
            <button className="btn">Create shipment & mark shipped</button>
          </form>
        ) : (
          <p className="muted sm">A shipment can be created once the order is paid and not on hold.</p>
        )}
      </div>
    );
  }

  return (
    <div className="mt">
      <Tracking shipment={s.data} />
      {!["cancelled", "refunded"].includes(order.status) && (
        <form className="card form" onSubmit={addEvent}>
          <h3>Add tracking update</h3>
          <div className="row">
            <Field label="Status">
              <select value={e.status} onChange={(x) => setE({ ...e, status: x.target.value })}>
                {EVENT_STATUS.map((st) => <option key={st} value={st}>{st.replaceAll("_", " ")}</option>)}
              </select>
            </Field>
            <Field label="Temperature (°C)"><input type="number" step="0.1" value={e.temperature} onChange={(x) => setE({ ...e, temperature: x.target.value })} /></Field>
          </div>
          <Field label="Location"><input required placeholder="Dubai Hub, AE" value={e.location} onChange={(x) => setE({ ...e, location: x.target.value })} /></Field>
          <Field label="Note"><input value={e.note} onChange={(x) => setE({ ...e, note: x.target.value })} /></Field>
          <button className="btn">Add update</button>
        </form>
      )}
    </div>
  );
}