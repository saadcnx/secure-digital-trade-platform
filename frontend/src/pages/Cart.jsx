import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useApp } from "../state";
import { Empty, ErrorBox, Loading, money, useLoad } from "../components/ui";

export default function Cart() {
  const { currency, notify, refreshCart } = useApp();
  const nav = useNavigate();
  const cart = useLoad(() => api("/cart", { params: { currency } }), [currency]);

  async function change(fn) {
    try {
      cart.setData(await fn());
      refreshCart();
    } catch (e) {
      notify(e.message, "err");
    }
  }
  const upd = (pid, quantity) =>
    change(() => api(`/cart/items/${pid}`, { method: "PATCH", body: { quantity }, params: { currency } }));
  const del = (pid) => change(() => api(`/cart/items/${pid}`, { method: "DELETE", params: { currency } }));

  if (cart.loading && !cart.data) return <div className="container"><Loading /></div>;
  if (cart.error) return <div className="container page"><ErrorBox error={cart.error} onRetry={cart.reload} /></div>;
  const c = cart.data;
  if (!c.items.length)
    return (
      <div className="container">
        <Empty icon="🛒" title="Your cart is empty">
          <Link className="btn" to="/">Start shopping</Link>
        </Empty>
      </div>
    );
  const bad = c.items.some((i) => !i.available);

  return (
    <div className="container page">
      <h2>Your cart</h2>
      <div className="two">
        <div className="card">
          {c.items.map((i) => (
            <div className="line" key={i.product_id}>
              <img src={i.image_url} alt="" />
              <div>
                <Link to={`/product/${i.product_id}`}><b>{i.name}</b></Link>
                <div className="muted sm">Sold by {i.seller_name} · {money(i.unit_price, c.currency)}</div>
                {!i.available && <div className="sm" style={{ color: "var(--bad)" }}>Not enough stock — reduce quantity</div>}
                <button className="btn danger sm" style={{ marginTop: 8 }} onClick={() => del(i.product_id)}>Remove</button>
              </div>
              <div className="qty">
                <button onClick={() => upd(i.product_id, i.quantity - 1)}>−</button>
                <span>{i.quantity}</span>
                <button onClick={() => upd(i.product_id, i.quantity + 1)}>+</button>
              </div>
              <b>{money(i.line_total, c.currency)}</b>
            </div>
          ))}
        </div>
        <aside className="card sticky">
          <h3 style={{ marginBottom: 12 }}>Order summary</h3>
          <div className="kv"><span>Subtotal</span><b>{money(c.subtotal, c.currency)}</b></div>
          <div className="kv"><span>Shipping</span><span>Calculated at checkout</span></div>
          <button className="btn block mt" disabled={bad} onClick={() => nav("/checkout")}>Proceed to checkout</button>
        </aside>
      </div>
    </div>
  );
}