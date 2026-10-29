const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const tokenStore = {
  get: () => localStorage.getItem("ts_token"),
  set: (t) => (t ? localStorage.setItem("ts_token", t) : localStorage.removeItem("ts_token")),
};

export async function api(path, { method = "GET", body, form, params } = {}) {
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
  const res = await fetch(url, { method, headers, body: payload });
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
}