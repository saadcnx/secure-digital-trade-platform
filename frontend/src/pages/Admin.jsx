import { useState } from "react";
import { api } from "../api";
import { useApp } from "../state";
import { OrdersTable } from "../components/OrderManager";
import { Badge, Empty, ErrorBox, Loading, Panel, Stars, fdate, money, useLoad } from "../components/ui";

function Overview() {
  const s = useLoad(() => api("/admin/stats"), []);
  if (s.error) return <ErrorBox error={s.error} onRetry={s.reload} />;
  if (!s.data) return <Loading />;
  const d = s.data;
  const cards = [
    ["Users", d.users], ["Products", d.products], ["Reviews", d.reviews],
    ["Orders", d.orders], ["On hold", d.on_hold], ["Revenue (USD)", money(d.revenue_usd, "USD")],
  ];
  return (
    <>
      <div className="stats">
        {cards.map(([l, v]) => <div className="stat" key={l}><small>{l}</small><b>{v}</b></div>)}
      </div>
      <div className="card">
        <div className="card-h"><h3>Orders by status</h3></div>
        {Object.keys(d.orders_by_status).length === 0 && <p className="muted">No orders yet.</p>}
        {Object.entries(d.orders_by_status).map(([k, v]) => (
          <div className="kv" key={k}><span><Badge s={k} /></span><b>{v}</b></div>
        ))}
      </div>
    </>
  );
}

function Users() {
  const { notify, user: me } = useApp();
  const [q, setQ] = useState("");
  const u = useLoad(() => api("/admin/users", { params: { q, limit: 200 } }), [q]);

  async function patch(id, body) {
    try {
      await api(`/admin/users/${id}`, { method: "PATCH", body });
      notify("User updated");
      u.reload();
    } catch (e) {
      notify(e.message, "err");
    }
  }

  return (
    <div className="card">
      <div className="card-h">
        <h3>Users</h3>
        <input className="sel" placeholder="Search name or email..." value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {u.error ? <ErrorBox error={u.error} onRetry={u.reload} /> : !u.data ? <Loading /> : (
        <div className="scroll">
          <table className="tbl">
            <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Role</th><th>Region</th><th>Joined</th><th>Status</th><th /></tr></thead>
            <tbody>
              {u.data.map((x) => (
                <tr key={x.id}>
                  <td>{x.id}</td>
                  <td><b>{x.full_name}</b></td>
                  <td>{x.email}</td>
                  <td>
                    <select className="sel" value={x.role} disabled={x.id === me.id} onChange={(e) => patch(x.id, { role: e.target.value })}>
                      {["buyer", "seller", "admin"].map((r) => <option key={r}>{r}</option>)}
                    </select>
                  </td>
                  <td>{x.region}</td>
                  <td>{fdate(x.created_at)}</td>
                  <td><Badge s={x.is_active ? "active" : "inactive"} /></td>
                  <td>
                    {x.id !== me.id && (
                      <button className={"btn sm " + (x.is_active ? "danger" : "ghost")} onClick={() => patch(x.id, { is_active: !x.is_active })}>
                        {x.is_active ? "Deactivate" : "Activate"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Products() {
  const { notify } = useApp();
  const [q, setQ] = useState("");
  const p = useLoad(() => api("/admin/products", { params: { q } }), [q]);

  async function toggle(x) {
    try {
      await api(`/products/${x.id}`, { method: "PATCH", body: { is_active: !x.is_active } });
      notify("Product updated");
      p.reload();
    } catch (e) {
      notify(e.message, "err");
    }
  }

  return (
    <div className="card">
      <div className="card-h">
        <h3>Products</h3>
        <input className="sel" placeholder="Search products..." value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {p.error ? <ErrorBox error={p.error} onRetry={p.reload} /> : !p.data ? <Loading /> : (
        <div className="scroll">
          <table className="tbl">
            <thead><tr><th /><th>Name</th><th>Seller</th><th>Price</th><th>Stock</th><th>Origin</th><th>HS</th><th>Status</th><th /></tr></thead>
            <tbody>
              {p.data.map((x) => (
                <tr key={x.id}>
                  <td><img className="thumb" src={x.image_url} alt="" /></td>
                  <td><b>{x.name}</b></td>
                  <td>{x.seller_name}</td>
                  <td>{money(x.price, x.currency)}</td>
                  <td>{x.stock}</td>
                  <td>{x.origin_country}</td>
                  <td>{x.hs_code || "—"}</td>
                  <td><Badge s={x.is_active ? "active" : "inactive"} /></td>
                  <td><button className={"btn sm " + (x.is_active ? "danger" : "ghost")} onClick={() => toggle(x)}>{x.is_active ? "Hide" : "Show"}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Reviews() {
  const { notify } = useApp();
  const r = useLoad(() => api("/admin/reviews"), []);

  async function del(id) {
    try {
      await api(`/reviews/${id}`, { method: "DELETE" });
      notify("Review deleted");
      r.reload();
    } catch (e) {
      notify(e.message, "err");
    }
  }

  return (
    <div className="card">
      <div className="card-h"><h3>Reviews</h3></div>
      {r.error ? <ErrorBox error={r.error} onRetry={r.reload} /> : !r.data ? <Loading /> : !r.data.length ? <Empty icon="⭐" title="No reviews yet" /> : (
        <div className="scroll">
          <table className="tbl">
            <thead><tr><th>Product</th><th>Reviewer</th><th>Rating</th><th>Review</th><th>Verified</th><th>IP</th><th>Date</th><th /></tr></thead>
            <tbody>
              {r.data.map((x) => (
                <tr key={x.id}>
                  <td>{x.product_name}</td>
                  <td>{x.reviewer_name}</td>
                  <td><Stars value={x.rating} /></td>
                  <td><b>{x.title}</b><span className="detail">{x.body}</span></td>
                  <td><Badge s={x.verified_purchase ? "green" : "gray"}>{x.verified_purchase ? "yes" : "no"}</Badge></td>
                  <td>{x.ip || "—"}</td>
                  <td>{fdate(x.created_at)}</td>
                  <td><button className="btn danger sm" onClick={() => del(x.id)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Audit() {
  const [prefix, setPrefix] = useState("");
  const a = useLoad(() => api("/admin/audit", { params: { action: prefix, limit: 200 } }), [prefix]);
  return (
    <div className="card">
      <div className="card-h">
        <h3>Audit log</h3>
        <div className="chips">
          {["", "auth", "order", "payment", "review", "shipment", "admin"].map((p) => (
            <button key={p} className={"chip" + (prefix === p ? " on" : "")} onClick={() => setPrefix(p)}>{p || "all"}</button>
          ))}
        </div>
      </div>
      {a.error ? <ErrorBox error={a.error} onRetry={a.reload} /> : !a.data ? <Loading /> : !a.data.length ? <Empty icon="🗂" title="No log entries" /> : (
        <div className="scroll">
          <table className="tbl">
            <thead><tr><th>Time</th><th>Action</th><th>User</th><th>IP</th><th>Details</th></tr></thead>
            <tbody>
              {a.data.map((x) => (
                <tr key={x.id}>
                  <td style={{ whiteSpace: "nowrap" }}>{fdate(x.created_at)}</td>
                  <td><code>{x.action}</code></td>
                  <td>{x.user_id ?? "—"}</td>
                  <td>{x.ip || "—"}</td>
                  <td><span className="detail" title={JSON.stringify(x.detail)}>{x.detail ? JSON.stringify(x.detail) : ""}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function Admin() {
  const [tab, setTab] = useState("overview");
  const tabs = [
    ["overview", "📊 Overview"], ["users", "👥 Users"], ["orders", "🧾 Orders"],
    ["products", "📦 Products"], ["reviews", "⭐ Reviews"], ["audit", "🗂 Audit log"],
  ];
  return (
    <Panel title="Admin console" tabs={tabs} tab={tab} setTab={setTab}>
      {tab === "overview" && <Overview />}
      {tab === "users" && <Users />}
      {tab === "orders" && <OrdersTable admin />}
      {tab === "products" && <Products />}
      {tab === "reviews" && <Reviews />}
      {tab === "audit" && <Audit />}
    </Panel>
  );
}