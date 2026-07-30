// Same-origin in production (FastAPI serves the built bundle), proxied to :8000
// in dev by vite.config.js. No CORS config anywhere, because there is no cross
// origin — the reason for serving the bundle from the API rather than hosting
// the frontend separately.
const BASE = "";

let token = localStorage.getItem("diq_token") || null;

export function setToken(t) {
  token = t;
  if (t) localStorage.setItem("diq_token", t);
  else localStorage.removeItem("diq_token");
}
export function getToken() {
  return token;
}

async function request(path, { method = "GET", body, idempotencyKey } = {}) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;
  // Surfaced in the UI so the retry-safety story is demonstrable, not just claimed.
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;

  const res = await fetch(BASE + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }

  if (!res.ok) {
    const msg =
      data?.message || data?.detail || data?.error || `HTTP ${res.status}`;
    const err = new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return { data, replayed: res.headers.get("Idempotent-Replay") === "true" };
}

export const api = {
  ready: () => request("/ready"),
  register: (email, password) =>
    request("/auth/register", { method: "POST", body: { email, password } }),
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: { email, password } }),
  me: () => request("/auth/me"),

  listOrders: () => request("/orders"),
  createOrder: (body, idempotencyKey) =>
    request("/orders", { method: "POST", body, idempotencyKey }),
  dispatch: () => request("/orders/dispatch", { method: "POST" }),
  setStatus: (id, status) =>
    request(`/orders/${id}/status`, { method: "PATCH", body: { status } }),

  listRiders: () => request("/riders"),
  createRider: (body) => request("/riders", { method: "POST", body }),

  stats: () => request("/admin/stats"),
};
