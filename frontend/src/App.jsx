import { Link, NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { useApp } from "./state";
import { CURRENCIES, Loading } from "./components/ui";
import Home from "./pages/Home";
import Product from "./pages/Product";
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";
import Orders from "./pages/Orders";
import OrderDetail from "./pages/OrderDetail";
import Account from "./pages/Account";
import { Login, Register } from "./pages/Auth";
import Seller from "./pages/Seller";
import Admin from "./pages/Admin";

function Nav() {
  const { user, logout, currency, setCurrency, cartCount } = useApp();
  const nav = useNavigate();
  return (
    <header className="nav">
      <div className="container nav-in">
        <Link to="/" className="brand">
          <span className="logo">T</span>TradeShield
        </Link>
        <nav className="links">
          <NavLink to="/" end>Shop</NavLink>
          {user && <NavLink to="/orders">My orders</NavLink>}
          {user && (user.role === "seller" || user.role === "admin") && <NavLink to="/seller">Seller</NavLink>}
          {user?.role === "admin" && <NavLink to="/admin">Admin</NavLink>}
        </nav>
        <div className="nav-right">
          <select className="cur" value={currency} onChange={(e) => setCurrency(e.target.value)}>
            {CURRENCIES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
          <Link to="/cart" className="cart-btn">
            🛒{cartCount > 0 && <b>{cartCount}</b>}
          </Link>
          {user ? (
            <>
              <Link to="/account" className="who">{user.full_name.split(" ")[0]}</Link>
              <button className="btn ghost sm" onClick={() => { logout(); nav("/"); }}>Logout</button>
            </>
          ) : (
            <>
              <Link className="btn ghost sm" to="/login">Login</Link>
              <Link className="btn sm" to="/register">Sign up</Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

function Guard({ roles, children }) {
  const { user, ready } = useApp();
  if (!ready) return <div className="container"><Loading /></div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  const { toast } = useApp();
  return (
    <>
      <Nav />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/product/:id" element={<Product />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/cart" element={<Guard><Cart /></Guard>} />
          <Route path="/checkout" element={<Guard><Checkout /></Guard>} />
          <Route path="/orders" element={<Guard><Orders /></Guard>} />
          <Route path="/orders/:id" element={<Guard><OrderDetail /></Guard>} />
          <Route path="/account" element={<Guard><Account /></Guard>} />
          <Route path="/seller" element={<Guard roles={["seller", "admin"]}><Seller /></Guard>} />
          <Route path="/admin" element={<Guard roles={["admin"]}><Admin /></Guard>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="footer">
        <div className="container">TradeShield Marketplace · Secure cross-border commerce · Demo platform</div>
      </footer>
      {toast && <div key={toast.id} className={"toast " + toast.kind}>{toast.msg}</div>}
    </>
  );
}