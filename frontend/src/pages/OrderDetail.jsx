import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useApp } from "../state";
import Tracking from "../components/Tracking";
import { Badge, COUNTRIES, Empty, Loading, fdate, money, useLoad } from "../components/ui";

const STEPS = ["created", "paid", "packed", "shipped", "delivered"];

export default function OrderDetail() {
  const { id } = useParams();
  const { user, notify } = useApp();
  const o = useLoad(() => api(`/orders/${id}`), [id]);
  const s = useLoad(() => api(`/shipments/orders/${id}`).catch(() => null), [id]);
  const cards = useLoad(() => api("/payments/tokens"), []);
  const [token, setToken] = useState("");

  useEffect(() => {
    if (cards.data?.length && !token) setToken(cards.data[0].token);
  }, [cards.data, token]);

  async function run(fn, ok) {
    try {
      await fn();
      notify(ok);
    } catch (e) {
      notify(e.message, "err");
    }
    o.reload();
    s.reload();
  }

  if (o.loading && !o.data) return <div className="container"><Loading /></div>;
  if (o.error) return <div className="container"><Empty icon="😕" title="Order not found">{o.error}</Empty></div>;
  const order = o.data;
  const isBuyer = order.buyer_id === user.id;
  const idx = STEPS.indexOf(order.status);
  const closed = order.status === "cancelled" || order.status === "refunded";
  const addr = order.shipping_address;

  return (
    <div className="container page">
      <Link to="/orders" className="muted sm">← All orders</Link>
      <div className="spread" style={{ margin: "10px 0 18px" }}>
        <h2>Order #{order.id}</h2>
        <span className="muted">{fdate(order.created_at)}</span>
      </div>

      {order.on_hold && <div className="banner warn">⏸ This order is on hold ({(order.hold_reason || "review").replaceAll("_", " ")}). We will release it once the review completes.</div>}
      {closed && <div className="banner bad">This order was {order.status}.</div>}

      <div className="card">
        {!closed && (
          <ol className="steps">
            {STEPS.map((st, i) => (
              <li key={st} className={i <= idx ? "done" : ""}><span>{i < idx ? "✓" : i + 1}</span>{st}</li>
            ))}
          </ol>
        )}
        {closed && <Badge s={order.status} />}
      </div>

      <div className="two mt">
        <div>
          <section className="card">
            <div className="card-h"><h3>Items</h3></div>
            {order.items.map((i) => (
              <div className="kv" key={i.product_id}>
                <span>
                  {i.quantity}× <Link to={`/product/${i.product_id}`}><b style={{ color: "var(--ink)" }}>{i.name}</b></Link>
                  {order.status === "delivered" && isBuyer && <Link to={`/product/${i.product_id}`} className="sm" style={{ color: "var(--brand)", marginLeft: 10 }}>Write a review</Link>}
                </span>
                <b>{money(i.line_total, order.currency)}</b>
              </div>
            ))}
            <div className="kv"><span>Shipping</span><b>{money(order.shipping_cost, order.currency)}</b></div>
            <div className="kv total"><span>Total</span><b>{money(order.total, order.currency)}</b></div>
          </section>

          {s.data && <div className="mt"><Tracking shipment={s.data} /></div>}
        </div>

        <aside>
          <section className="card">
            <div className="card-h"><h3>Shipping to</h3></div>
            <b>{addr.full_name}</b>
            <p className="muted sm">{addr.line1}{addr.line2 ? `, ${addr.line2}` : ""}<br />{addr.city}, {addr.postal_code}<br />{COUNTRIES[addr.country] || addr.country}</p>
          </section>

          <section className="card">
            <div className="card-h"><h3>Payments</h3></div>
            {!order.payments.length && <p className="muted sm">No payment attempts yet.</p>}
            {order.payments.map((p) => (
              <div className="kv" key={p.id}>
                <span><Badge s={p.status} /> {p.failure_reason && <span className="sm">{p.failure_reason.replaceAll("_", " ")}</span>}</span>
                <b>{money(p.amount, p.currency)}</b>
              </div>
            ))}
            {isBuyer && order.status === "created" && !order.on_hold && (
              <div className="form mt">
                {cards.data?.length ? (
                  <>
                    <select className="sel" value={token} onChange={(e) => setToken(e.target.value)}>
                      {cards.data.map((k) => <option key={k.token} value={k.token}>{k.brand} •••• {k.last4}</option>)}
                    </select>
                    <button className="btn" onClick={() => run(() => api(`/payments/orders/${id}/pay`, { method: "POST", body: { token } }), "Payment processed")}>Pay {money(order.total, order.currency)}</button>
                  </>
                ) : (
                  <Link className="btn ghost" to="/account">Add a card first</Link>
                )}
              </div>
            )}
            {isBuyer && ["created", "paid"].includes(order.status) && (
              <button className="btn danger block mt" onClick={() => run(() => api(`/orders/${id}/status`, { method: "PATCH", body: { status: "cancelled" } }), "Order cancelled")}>Cancel order</button>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}