import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useApp } from "../state";
import { AddressForm, CardForm } from "../components/Forms";
import { COUNTRIES, Empty, ErrorBox, Loading, Modal, money, useLoad } from "../components/ui";

export default function Checkout() {
  const { currency, notify, refreshCart } = useApp();
  const nav = useNavigate();
  const cart = useLoad(() => api("/cart", { params: { currency } }), [currency]);
  const addrs = useLoad(() => api("/users/me/addresses"), []);
  const cards = useLoad(() => api("/payments/tokens"), []);
  const [addrId, setAddrId] = useState(null);
  const [token, setToken] = useState("");
  const [modal, setModal] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (addrs.data && addrId == null) {
      const d = addrs.data.find((a) => a.is_default) || addrs.data[0];
      if (d) setAddrId(d.id);
    }
  }, [addrs.data, addrId]);

  useEffect(() => {
    if (cards.data?.length && !token) setToken(cards.data[0].token);
  }, [cards.data, token]);

  async function place() {
    setBusy(true);
    let order;
    try {
      order = await api("/orders/checkout", { method: "POST", body: { address_id: addrId, currency } });
    } catch (e) {
      notify(e.message, "err");
      setBusy(false);
      return;
    }
    refreshCart();
    if (order.on_hold) {
      notify("Order placed — pending compliance review");
      nav(`/orders/${order.id}`);
      return;
    }
    try {
      const pay = await api(`/payments/orders/${order.id}/pay`, { method: "POST", body: { token } });
      notify(pay.status === "pending_review" ? "Payment is under review" : "Payment successful 🎉");
    } catch (e) {
      notify(e.message, "err");
    }
    nav(`/orders/${order.id}`);
  }

  if ((cart.loading && !cart.data) || (addrs.loading && !addrs.data) || (cards.loading && !cards.data))
    return <div className="container"><Loading /></div>;
  const loadErr = cart.error || addrs.error || cards.error;
  if (loadErr)
    return (
      <div className="container page">
        <ErrorBox error={loadErr} onRetry={() => { cart.reload(); addrs.reload(); cards.reload(); }} />
      </div>
    );
  const c = cart.data;
  if (!c?.items.length)
    return (
      <div className="container">
        <Empty icon="🛒" title="Nothing to check out"><Link className="btn" to="/">Browse products</Link></Empty>
      </div>
    );
  const ready = addrId && token && !c.items.some((i) => !i.available);

  return (
    <div className="container page">
      <h2>Checkout</h2>
      <div className="two">
        <div>
          <section className="card">
            <div className="card-h"><h3>1 · Shipping address</h3><button className="btn ghost sm" onClick={() => setModal("addr")}>+ New address</button></div>
            {!addrs.data?.length && <p className="muted">Add a shipping address to continue.</p>}
            {addrs.data?.map((a) => (
              <label key={a.id} className={"opt" + (addrId === a.id ? " on" : "")}>
                <input type="radio" checked={addrId === a.id} onChange={() => setAddrId(a.id)} />
                <div>
                  <b>{a.full_name}</b>
                  <div className="muted sm">{a.line1}{a.line2 ? `, ${a.line2}` : ""}, {a.city}, {a.postal_code}, {COUNTRIES[a.country] || a.country}</div>
                </div>
              </label>
            ))}
          </section>
          <section className="card">
            <div className="card-h"><h3>2 · Payment method</h3><button className="btn ghost sm" onClick={() => setModal("card")}>+ New card</button></div>
            {!cards.data?.length && <p className="muted">Add a card to continue.</p>}
            {cards.data?.map((k) => (
              <label key={k.token} className={"opt" + (token === k.token ? " on" : "")}>
                <input type="radio" checked={token === k.token} onChange={() => setToken(k.token)} />
                <div>
                  <b style={{ textTransform: "capitalize" }}>{k.brand}</b> •••• {k.last4}
                  <div className="muted sm">Expires {String(k.exp_month).padStart(2, "0")}/{k.exp_year}</div>
                </div>
              </label>
            ))}
          </section>
        </div>
        <aside className="card sticky">
          <h3 style={{ marginBottom: 12 }}>Order summary</h3>
          {c.items.map((i) => (
            <div className="kv" key={i.product_id}><span>{i.quantity}× {i.name}</span><b>{money(i.line_total, c.currency)}</b></div>
          ))}
          <div className="kv total"><span>Subtotal</span><b>{money(c.subtotal, c.currency)}</b></div>
          <p className="muted sm">Shipping (domestic or cross-border) is added when the order is placed.</p>
          <button className="btn block mt" disabled={!ready || busy} onClick={place}>{busy ? "Placing order..." : "Place order & pay"}</button>
        </aside>
      </div>
      {modal === "addr" && (
        <Modal title="New address" onClose={() => setModal(null)}>
          <AddressForm onSaved={(a) => { setAddrId(a.id); addrs.reload(); setModal(null); }} />
        </Modal>
      )}
      {modal === "card" && (
        <Modal title="Add a card" onClose={() => setModal(null)}>
          <CardForm onSaved={(t) => { setToken(t.token); cards.reload(); setModal(null); }} />
        </Modal>
      )}
    </div>
  );
}