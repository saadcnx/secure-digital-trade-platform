import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useApp } from "../state";
import { COUNTRIES, Empty, ErrorBox, Loading, flag, money, useLoad } from "../components/ui";

function ProductCard({ p }) {
  return (
    <Link to={`/product/${p.id}`} className="pcard">
      <div className="pimg">
        <img src={p.image_url} alt={p.name} loading="lazy" onError={(e) => (e.currentTarget.style.visibility = "hidden")} />
        {p.stock > 0 && p.stock <= 5 && <span className="tag">Only {p.stock} left</span>}
        {p.stock === 0 && <span className="tag bad">Sold out</span>}
      </div>
      <div className="pbody">
        <div className="muted sm">{flag(p.origin_country)} {COUNTRIES[p.origin_country] || p.origin_country} · {p.seller_name}</div>
        <h4>{p.name}</h4>
        <div className="price">{money(p.display_price ?? p.price, p.display_currency ?? p.currency)}</div>
      </div>
    </Link>
  );
}

export default function Home() {
  const { currency } = useApp();
  const [input, setInput] = useState("");
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("");
  const [origin, setOrigin] = useState("");
  const cats = useLoad(() => api("/categories"), []);
  const prods = useLoad(
    () => api("/products", { params: { q, category_id: cat, origin_country: origin, currency, limit: 60 } }),
    [q, cat, origin, currency]
  );

  return (
    <>
      <section className="hero">
        <div className="container">
          <span className="pill">🌍 Cross-border marketplace</span>
          <h1>Shop the world.<br />Securely, in your currency.</h1>
          <p>Products from trusted sellers in Pakistan, Europe and beyond, priced in USD, EUR, GBP or PKR.</p>
          <form className="search" onSubmit={(e) => { e.preventDefault(); setQ(input.trim()); }}>
            <input placeholder="Search products..." value={input} onChange={(e) => setInput(e.target.value)} />
            <button className="btn">Search</button>
          </form>
        </div>
      </section>
      <div className="container">
        <div className="filters">
          <div className="chips">
            <button className={"chip" + (cat === "" ? " on" : "")} onClick={() => setCat("")}>All</button>
            {cats.data?.map((c) => (
              <button key={c.id} className={"chip" + (cat === c.id ? " on" : "")} onClick={() => setCat(c.id)}>{c.name}</button>
            ))}
          </div>
          <select className="sel" value={origin} onChange={(e) => setOrigin(e.target.value)}>
            <option value="">Ships from: anywhere</option>
            {Object.entries(COUNTRIES).map(([k, v]) => <option key={k} value={k}>{flag(k)} {v}</option>)}
          </select>
        </div>
        {prods.loading && !prods.data ? (
          <Loading />
        ) : prods.error ? (
          <ErrorBox error={prods.error} onRetry={prods.reload} />
        ) : !prods.data?.length ? (
          <Empty icon="🔍" title="No products found">Try a different search or filter.</Empty>
        ) : (
          <div className="grid">{prods.data.map((p) => <ProductCard key={p.id} p={p} />)}</div>
        )}
      </div>
    </>
  );
}