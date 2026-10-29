import { useState } from "react";
import { api } from "../api";
import { useApp } from "../state";
import { OrdersTable } from "../components/OrderManager";
import { CURRENCIES, COUNTRIES, Badge, Empty, ErrorBox, Field, Loading, Modal, Panel, money, useLoad } from "../components/ui";

function ProductForm({ initial, cats, onSaved }) {
  const { notify } = useApp();
  const [f, setF] = useState(
    initial
      ? { ...initial, price: String(initial.price), hs_code: initial.hs_code || "", image_url: initial.image_url || "", category_id: initial.category_id || "" }
      : { name: "", description: "", image_url: "", price: "", currency: "USD", stock: 10, origin_country: "PK", hs_code: "", category_id: "" }
  );
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    const body = {
      name: f.name,
      description: f.description,
      image_url: f.image_url || null,
      price: String(f.price),
      currency: f.currency,
      stock: Number(f.stock),
      origin_country: f.origin_country,
      hs_code: f.hs_code || null,
      category_id: f.category_id ? Number(f.category_id) : null,
    };
    try {
      if (initial) await api(`/products/${initial.id}`, { method: "PATCH", body: { ...body, is_active: f.is_active } });
      else await api("/products", { method: "POST", body });
      notify("Product saved");
      onSaved();
    } catch (err) {
      notify(err.message, "err");
    }
  }

  return (
    <form className="form" onSubmit={submit}>
      <Field label="Product name"><input required value={f.name} onChange={set("name")} /></Field>
      <Field label="Description"><textarea rows={3} value={f.description} onChange={set("description")} /></Field>
      <Field label="Image URL"><input placeholder="https://..." value={f.image_url} onChange={set("image_url")} /></Field>
      <div className="row">
        <Field label="Price"><input required type="number" step="0.01" min="0.01" value={f.price} onChange={set("price")} /></Field>
        <Field label="Currency">
          <select value={f.currency} onChange={set("currency")}>{CURRENCIES.map((c) => <option key={c}>{c}</option>)}</select>
        </Field>
      </div>
      <div className="row">
        <Field label="Stock"><input required type="number" min="0" value={f.stock} onChange={set("stock")} /></Field>
        <Field label="Origin country">
          <select value={f.origin_country} onChange={set("origin_country")}>
            {Object.entries(COUNTRIES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </Field>
      </div>
      <div className="row">
        <Field label="Category">
          <select value={f.category_id} onChange={set("category_id")}>
            <option value="">— none —</option>
            {cats?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="HS code" hint="Optional — classification can be filled later"><input maxLength={12} value={f.hs_code} onChange={set("hs_code")} /></Field>
      </div>
      {initial && (
        <label className="check"><input type="checkbox" checked={f.is_active} onChange={(e) => setF({ ...f, is_active: e.target.checked })} /> Visible in the shop</label>
      )}
      <button className="btn">{initial ? "Save changes" : "Add product"}</button>
    </form>
  );
}

function Products() {
  const { notify } = useApp();
  const list = useLoad(() => api("/products/mine"), []);
  const cats = useLoad(() => api("/categories"), []);
  const [edit, setEdit] = useState(null);

  async function hide(id) {
    try {
      await api(`/products/${id}`, { method: "DELETE" });
      notify("Product hidden");
      list.reload();
    } catch (e) {
      notify(e.message, "err");
    }
  }

  return (
    <div className="card">
      <div className="card-h">
        <h3>My products</h3>
        <button className="btn sm" onClick={() => setEdit({})}>+ Add product</button>
      </div>
      {list.loading && !list.data ? (
        <Loading />
      ) : list.error ? (
        <ErrorBox error={list.error} onRetry={list.reload} />
      ) : !list.data?.length ? (
        <Empty icon="🏷" title="No products yet">Add your first product to start selling.</Empty>
      ) : (
        <div className="scroll">
          <table className="tbl">
            <thead><tr><th /><th>Name</th><th>Price</th><th>Stock</th><th>Origin</th><th>HS code</th><th>Status</th><th /></tr></thead>
            <tbody>
              {list.data.map((p) => (
                <tr key={p.id}>
                  <td><img className="thumb" src={p.image_url} alt="" /></td>
                  <td><b>{p.name}</b></td>
                  <td>{money(p.price, p.currency)}</td>
                  <td>{p.stock}</td>
                  <td>{p.origin_country}</td>
                  <td>{p.hs_code || "—"}</td>
                  <td><Badge s={p.is_active ? "active" : "inactive"} /></td>
                  <td>
                    <div className="gap">
                      <button className="btn ghost sm" onClick={() => setEdit(p)}>Edit</button>
                      {p.is_active && <button className="btn danger sm" onClick={() => hide(p.id)}>Hide</button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {edit && (
        <Modal title={edit.id ? "Edit product" : "Add product"} onClose={() => setEdit(null)}>
          <ProductForm initial={edit.id ? edit : null} cats={cats.data} onSaved={() => { setEdit(null); list.reload(); }} />
        </Modal>
      )}
    </div>
  );
}

export default function Seller() {
  const [tab, setTab] = useState("products");
  return (
    <Panel title="Seller center" tabs={[["products", "📦 Products"], ["orders", "🧾 Orders & shipments"]]} tab={tab} setTab={setTab}>
      {tab === "products" ? <Products /> : <OrdersTable />}
    </Panel>
  );
}