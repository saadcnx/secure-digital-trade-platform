import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { useApp } from "../state";
import { Badge, COUNTRIES, Empty, Field, Loading, StarInput, Stars, fdate, flag, money, useLoad } from "../components/ui";

function ReviewForm({ productId, onDone }) {
  const { notify } = useApp();
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api(`/products/${productId}/reviews`, { method: "POST", body: { rating, title, body } });
      notify("Thanks for your review!");
      setTitle("");
      setBody("");
      onDone();
    } catch (err) {
      notify(err.message, "err");
    }
    setBusy(false);
  }

  return (
    <form className="form" onSubmit={submit} style={{ marginBottom: 20 }}>
      <h4>Write a review</h4>
      <StarInput value={rating} onChange={setRating} />
      <Field label="Title"><input required maxLength={120} value={title} onChange={(e) => setTitle(e.target.value)} /></Field>
      <Field label="Your review"><textarea rows={3} value={body} onChange={(e) => setBody(e.target.value)} /></Field>
      <div><button className="btn" disabled={busy}>{busy ? "Posting..." : "Post review"}</button></div>
    </form>
  );
}

export default function Product() {
  const { id } = useParams();
  const { currency, user, notify, refreshCart } = useApp();
  const nav = useNavigate();
  const p = useLoad(() => api(`/products/${id}`, { params: { currency } }), [id, currency]);
  const rv = useLoad(() => api(`/products/${id}/reviews`), [id]);
  const [qty, setQty] = useState(1);

  async function add() {
    if (!user) return nav("/login");
    try {
      await api("/cart/items", { method: "POST", body: { product_id: Number(id), quantity: qty } });
      notify("Added to cart 🛒");
      refreshCart();
    } catch (e) {
      notify(e.message, "err");
    }
  }

  async function del(rid) {
    try {
      await api(`/reviews/${rid}`, { method: "DELETE" });
      notify("Review removed");
      rv.reload();
    } catch (e) {
      notify(e.message, "err");
    }
  }

  if (p.loading && !p.data) return <div className="container"><Loading /></div>;
  if (p.error) return <div className="container"><Empty icon="😕" title="Product not found">{p.error}</Empty></div>;
  const x = p.data;
  const reviews = rv.data;
  const alreadyReviewed = reviews?.items.some((r) => r.user_id === user?.id);

  return (
    <div className="container page">
      <Link to="/" className="muted sm">← Back to shop</Link>
      <div className="pd">
        <div className="pd-img"><img src={x.image_url} alt={x.name} /></div>
        <div>
          <div className="muted">{flag(x.origin_country)} Ships from {COUNTRIES[x.origin_country] || x.origin_country} · sold by <b>{x.seller_name}</b></div>
          <h1 className="pd-title">{x.name}</h1>
          <div className="rate">
            <Stars value={reviews?.average || 0} size={20} />
            <span className="muted sm">{reviews ? `${reviews.average} · ${reviews.count} review${reviews.count === 1 ? "" : "s"}` : ""}</span>
          </div>
          <div className="pd-price">{money(x.display_price, x.display_currency)}</div>
          {x.display_currency !== x.currency && <div className="muted sm">Listed at {money(x.price, x.currency)}</div>}
          <p className="desc">{x.description}</p>
          <div className="facts">
            <div><small>Origin</small><b>{flag(x.origin_country)} {x.origin_country}</b></div>
            <div><small>HS code</small><b>{x.hs_code || "Pending"}</b></div>
            <div><small>Stock</small><b>{x.stock > 0 ? `${x.stock} available` : "Sold out"}</b></div>
          </div>
          <div className="buy">
            <div className="qty">
              <button onClick={() => setQty(Math.max(1, qty - 1))}>−</button>
              <span>{qty}</span>
              <button onClick={() => setQty(Math.min(x.stock || 1, qty + 1))}>+</button>
            </div>
            <button className="btn" disabled={x.stock === 0} onClick={add}>Add to cart</button>
          </div>
        </div>
      </div>

      <section className="card">
        <div className="card-h"><h3>Customer reviews</h3></div>
        {user && user.id !== x.seller_id && !alreadyReviewed && <ReviewForm productId={id} onDone={rv.reload} />}
        {!reviews?.items.length ? (
          <p className="muted">No reviews yet. Be the first to share your experience.</p>
        ) : (
          reviews.items.map((r) => (
            <div key={r.id} className="rv">
              <div className="spread">
                <div className="gap"><Stars value={r.rating} /><b>{r.reviewer_name}</b>{r.verified_purchase && <Badge s="green">Verified purchase</Badge>}</div>
                <span className="muted sm">{fdate(r.created_at)}</span>
              </div>
              <h4>{r.title}</h4>
              <p className="muted">{r.body}</p>
              {(user?.id === r.user_id || user?.role === "admin") && (
                <button className="btn danger sm" style={{ marginTop: 8 }} onClick={() => del(r.id)}>Delete</button>
              )}
            </div>
          ))
        )}
      </section>
    </div>
  );
}