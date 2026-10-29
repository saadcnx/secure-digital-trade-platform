import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useApp } from "../state";
import { Field } from "../components/ui";

const home = (u) => (u.role === "admin" ? "/admin" : u.role === "seller" ? "/seller" : "/");

export function Login() {
  const { login, notify } = useApp();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const demo = [
    ["Buyer", "buyer@tradeshield.test", "Buyer@12345"],
    ["Seller", "seller1@tradeshield.test", "Seller@12345"],
    ["Admin", "admin@tradeshield.test", "Admin@12345"],
  ];

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      nav(home(await login(email, password)));
    } catch (err) {
      notify(err.message, "err");
    }
    setBusy(false);
  }

  return (
    <div className="auth">
      <div className="card">
        <h2>Welcome back</h2>
        <p className="muted" style={{ marginBottom: 20 }}>Sign in to your TradeShield account</p>
        <form className="form" onSubmit={submit}>
          <Field label="Email"><input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
          <Field label="Password"><input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
          <button className="btn block" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
        </form>
        <div className="demo">
          <span className="muted sm">Demo accounts:</span>
          {demo.map(([l, e, p]) => (
            <button key={l} className="btn ghost sm" type="button" onClick={() => { setEmail(e); setPassword(p); }}>{l}</button>
          ))}
        </div>
        <p className="muted sm mt">New here? <Link to="/register" style={{ color: "var(--brand)", fontWeight: 600 }}>Create an account</Link></p>
      </div>
    </div>
  );
}

export function Register() {
  const { login, notify } = useApp();
  const nav = useNavigate();
  const [f, setF] = useState({ full_name: "", email: "", password: "", role: "buyer", region: "OTHER" });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api("/auth/register", { method: "POST", body: f });
      nav(home(await login(f.email, f.password)));
    } catch (err) {
      notify(err.message, "err");
    }
    setBusy(false);
  }

  return (
    <div className="auth">
      <div className="card">
        <h2>Create your account</h2>
        <p className="muted" style={{ marginBottom: 20 }}>Buy or sell across borders, securely</p>
        <form className="form" onSubmit={submit}>
          <Field label="Full name"><input required value={f.full_name} onChange={set("full_name")} /></Field>
          <Field label="Email"><input type="email" required value={f.email} onChange={set("email")} /></Field>
          <Field label="Password" hint="At least 8 characters"><input type="password" required minLength={8} value={f.password} onChange={set("password")} /></Field>
          <div className="row">
            <Field label="I want to">
              <select value={f.role} onChange={set("role")}>
                <option value="buyer">Buy products</option>
                <option value="seller">Sell products</option>
              </select>
            </Field>
            <Field label="Region">
              <select value={f.region} onChange={set("region")}>
                {["EU", "US", "UK", "PK", "OTHER"].map((r) => <option key={r}>{r}</option>)}
              </select>
            </Field>
          </div>
          <button className="btn block" disabled={busy}>{busy ? "Creating..." : "Create account"}</button>
        </form>
        <p className="muted sm mt">Already registered? <Link to="/login" style={{ color: "var(--brand)", fontWeight: 600 }}>Sign in</Link></p>
      </div>
    </div>
  );
}