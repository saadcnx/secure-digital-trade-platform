import { useState } from "react";
import { api } from "../api";
import { useApp } from "../state";
import { AddressForm, CardForm } from "../components/Forms";
import { COUNTRIES, Empty, Field, Modal, useLoad } from "../components/ui";

export default function Account() {
  const { user, setUser, notify } = useApp();
  const addrs = useLoad(() => api("/users/me/addresses"), []);
  const cards = useLoad(() => api("/payments/tokens"), []);
  const [f, setF] = useState({
    full_name: user.full_name,
    region: user.region,
    consent_marketing: user.consent_marketing,
    consent_analytics: user.consent_analytics,
  });
  const [modal, setModal] = useState(null);

  async function save(e) {
    e.preventDefault();
    try {
      setUser(await api("/users/me", { method: "PATCH", body: f }));
      notify("Profile updated");
    } catch (err) {
      notify(err.message, "err");
    }
  }

  async function remove(path, reload) {
    try {
      await api(path, { method: "DELETE" });
      reload();
    } catch (err) {
      notify(err.message, "err");
    }
  }

  return (
    <div className="container page">
      <h2>My account</h2>
      <div className="two" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <section className="card">
          <div className="card-h"><h3>Profile & privacy</h3><span className="muted sm">{user.email}</span></div>
          <form className="form" onSubmit={save}>
            <Field label="Full name"><input required value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} /></Field>
            <Field label="Data region" hint="Used for data residency and privacy rules">
              <select value={f.region} onChange={(e) => setF({ ...f, region: e.target.value })}>
                {["EU", "US", "UK", "PK", "OTHER"].map((r) => <option key={r}>{r}</option>)}
              </select>
            </Field>
            <label className="check"><input type="checkbox" checked={f.consent_marketing} onChange={(e) => setF({ ...f, consent_marketing: e.target.checked })} /> I agree to marketing emails</label>
            <label className="check"><input type="checkbox" checked={f.consent_analytics} onChange={(e) => setF({ ...f, consent_analytics: e.target.checked })} /> I agree to analytics & personalization</label>
            <div><button className="btn">Save changes</button></div>
          </form>
        </section>

        <div>
          <section className="card">
            <div className="card-h"><h3>Addresses</h3><button className="btn ghost sm" onClick={() => setModal("addr")}>+ Add</button></div>
            {!addrs.data?.length && <Empty icon="📍" title="No addresses" />}
            {addrs.data?.map((a) => (
              <div className="kv" key={a.id}>
                <span>
                  <b style={{ color: "var(--ink)" }}>{a.full_name}</b> {a.is_default && <span className="badge green">default</span>}
                  <br /><span className="sm">{a.line1}, {a.city}, {COUNTRIES[a.country] || a.country}</span>
                </span>
                <button className="btn danger sm" onClick={() => remove(`/users/me/addresses/${a.id}`, addrs.reload)}>Delete</button>
              </div>
            ))}
          </section>
          <section className="card">
            <div className="card-h"><h3>Saved cards</h3><button className="btn ghost sm" onClick={() => setModal("card")}>+ Add</button></div>
            {!cards.data?.length && <Empty icon="💳" title="No cards" />}
            {cards.data?.map((k) => (
              <div className="kv" key={k.token}>
                <span><b style={{ color: "var(--ink)", textTransform: "capitalize" }}>{k.brand}</b> •••• {k.last4} · {String(k.exp_month).padStart(2, "0")}/{k.exp_year}</span>
                <button className="btn danger sm" onClick={() => remove(`/payments/tokens/${k.token}`, cards.reload)}>Delete</button>
              </div>
            ))}
          </section>
        </div>
      </div>
      {modal === "addr" && (
        <Modal title="New address" onClose={() => setModal(null)}>
          <AddressForm onSaved={() => { addrs.reload(); setModal(null); }} />
        </Modal>
      )}
      {modal === "card" && (
        <Modal title="Add a card" onClose={() => setModal(null)}>
          <CardForm onSaved={() => { cards.reload(); setModal(null); }} />
        </Modal>
      )}
    </div>
  );
}