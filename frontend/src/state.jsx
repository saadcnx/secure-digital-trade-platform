import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, tokenStore } from "./api";

const Ctx = createContext(null);
export const useApp = () => useContext(Ctx);

export function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [currency, setCurrencyState] = useState(() => {
    try {
      return localStorage.getItem("ts_cur") || "USD";
    } catch {
      return "USD";
    }
  });
  const [cartCount, setCartCount] = useState(0);
  const [toast, setToast] = useState(null);

  const notify = useCallback((msg, kind = "ok") => setToast({ msg, kind, id: Date.now() }), []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(t);
  }, [toast]);

  const refreshCart = useCallback(async () => {
    if (!tokenStore.get()) return setCartCount(0);
    try {
      const c = await api("/cart");
      setCartCount(c.items.reduce((n, i) => n + i.quantity, 0));
    } catch {
      setCartCount(0);
    }
  }, []);

  useEffect(() => {
    (async () => {
      if (tokenStore.get()) {
        try {
          setUser(await api("/users/me"));
        } catch {
          tokenStore.set(null);
        }
      }
      setReady(true);
    })();
  }, []);

  useEffect(() => {
    refreshCart();
  }, [user, refreshCart]);

  useEffect(() => {
    const h = () => {
      if (!tokenStore.get()) return;
      tokenStore.set(null);
      setUser(null);
      setCartCount(0);
      notify("Session expired, please login again", "err");
    };
    window.addEventListener("auth:expired", h);
    return () => window.removeEventListener("auth:expired", h);
  }, [notify]);

  const login = async (email, password) => {
    const t = await api("/auth/login", { method: "POST", form: { username: email, password } });
    tokenStore.set(t.access_token);
    try {
      const u = await api("/users/me");
      setUser(u);
      return u;
    } catch (e) {
      tokenStore.set(null);
      throw e;
    }
  };

  const logout = () => {
    tokenStore.set(null);
    setUser(null);
    setCartCount(0);
  };

  const setCurrency = (c) => {
    try {
      localStorage.setItem("ts_cur", c);
    } catch {
      return;
    }
    setCurrencyState(c);
  };

  return (
    <Ctx.Provider
      value={{ user, setUser, ready, login, logout, currency, setCurrency, cartCount, refreshCart, notify, toast }}
    >
      {children}
    </Ctx.Provider>
  );
}