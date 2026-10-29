import { useState } from "react";
import { api } from "../api";
import { useApp } from "../state";
import { COUNTRIES, Field } from "./ui";

export function AddressForm({ onSaved }) {
  const { notify, user } = useApp();
  const [f, setF] = useState({
    full_name: user?.full_name || "", line1: "", line2: "", city: "", state: "",
    postal_code: "", country: "US", is_default: false,
  });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const a = await api("/users/me/addresses", {
        method: "POST",
        body: { ...f, line2: f.line2 || null, state: f.state || null },
      });
      notify("Address saved");
      onSaved(a);
    } catch (err) {
      notify(err.message, "err");
    }
    setBusy(false);
  }

  return (
    <form className="form" onSubmit={submit}>
      <Field label="Full name"><input required value={f.full_name} onChange={set("full_name")} /></Field>
      <Field label="Address line 1"><input required value={f.line1} onChange={set("line1")} /></Field>
      <Field label="Address line 2"><input value={f.line2} onChange={set("line2")} /></Field>
      <div className="row">
        <Field label="City"><input required value={f.city} onChange={set("city")} /></Field>
        <Field label="State / Province"><input value={f.state} onChange={set("state")} /></Field>
      </div>
      <div className="row">
        <Field label="Postal code"><input required value={f.postal_code} onChange={set("postal_code")} /></Field>
        <Field label="Country">
          <select value={f.country} onChange={set("country")}>
            {Object.entries(COUNTRIES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </Field>
      </div>
      <label className="check"><input type="checkbox" checked={f.is_default} onChange={set("is_default")} /> Make default address</label>
      <button className="btn" disabled={busy}>{busy ? "Saving..." : "Save address"}</button>
    </form>
  );
}

export function CardForm({ onSaved }) {
  const { notify, user } = useApp();
  const [f, setF] = useState({ card_number: "", holder_name: user?.full_name || "", exp_month: "", exp_year: "", cvv: "" });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const t = await api("/payments/tokens", {
        method: "POST",
        body: { ...f, exp_month: Number(f.exp_month), exp_year: Number(f.exp_year) },
      });
      notify(`Card •••• ${t.last4} saved`);
      onSaved(t);
    } catch (err) {
      notify(err.message, "err");
    }
    setBusy(false);
  }

  return (
    <form className="form" onSubmit={submit}>
      <div className="banner ok">🔒 Your card number is tokenized. Only brand, last 4 digits and expiry are stored.</div>
      <Field label="Card number" hint="Test: 4242 4242 4242 4242 (ok) · 4000 0000 0000 0002 (declined)">
        <input required inputMode="numeric" placeholder="4242 4242 4242 4242" value={f.card_number} onChange={set("card_number")} />
      </Field>
      <Field label="Name on card"><input required value={f.holder_name} onChange={set("holder_name")} /></Field>
      <div className="row">
        <Field label="Expiry month"><input required type="number" min="1" max="12" placeholder="MM" value={f.exp_month} onChange={set("exp_month")} /></Field>
        <Field label="Expiry year"><input required type="number" placeholder="YYYY" value={f.exp_year} onChange={set("exp_year")} /></Field>
      </div>
      <Field label="CVV"><input required inputMode="numeric" maxLength={4} placeholder="123" value={f.cvv} onChange={set("cvv")} /></Field>
      <button className="btn" disabled={busy}>{busy ? "Saving..." : "Save card"}</button>
    </form>
  );
}