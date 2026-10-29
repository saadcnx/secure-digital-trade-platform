const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const tokenStore = {
  get: () => {
    try {
      return localStorage.getItem("ts_token");
    } catch {
      return null;
    }
  },
  set: (t) => {
    try {
      if (t) localStorage.setItem("ts_token", t);
      else localStorage.removeItem("ts_token");
    } catch {
      return;
    }
  },
};

export async function api(
  path,
  { method = "GET", body, form, params, signal, retries = 1, timeoutMs = 15000 } = {}
) {
  const url = new URL(BASE + path);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    });
  }
  const headers = {};
  const t = tokenStore.get();
  if (t) headers.Authorization = "Bearer " + t;
  let payload;
  if (form) {
    payload = new URLSearchParams(form);
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const ctrl = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    ctrl.abort();
  }, timeoutMs);
  const onAbort = () => ctrl.abort();
  if (signal) {
    if (signal.aborted) ctrl.abort();
    else signal.addEventListener("abort", onAbort);
  }

  try {
    const res = await fetch(url, { method, headers, body: payload, signal: ctrl.signal });
    if (res.status === 401 && t && path !== "/auth/login") {
      window.dispatchEvent(new CustomEvent("auth:expired"));
    }
    if (res.status === 204) return null;
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      const d = data?.detail;
      let msg =
        typeof d === "string"
          ? d
          : d?.message || (Array.isArray(d) ? d.map((e) => e.msg).join(", ") : "Request failed");
      if (d?.reasons?.length) msg += ": " + d.reasons.join(", ");
      const err = new Error(msg);
      err.status = res.status;
      throw err;
    }
    return data;
  } catch (e) {
    if (e.name === "AbortError" && timedOut) throw new Error("Request timed out");
    if (retries > 0 && (method === "GET" || method === "HEAD") && e.name !== "AbortError" && !e.status) {
      return api(path, { method, body, form, params, signal, retries: retries - 1, timeoutMs });
    }
    throw e;
  } finally {
    clearTimeout(timer);
    if (signal) signal.removeEventListener("abort", onAbort);
  }
}