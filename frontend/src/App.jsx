import { useCallback, useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";
import "./App.css";

// Which transitions the UI offers from each state. The server enforces the real
// rules (legal transition AND permitted actor) — this only avoids showing
// buttons that are guaranteed to 400.
const STATUS_FLOW = {
  PENDING: [],
  ASSIGNED: ["PICKED_UP", "CANCELLED"],
  PICKED_UP: ["DELIVERED"],
  DELIVERED: [],
  CANCELLED: [],
};

function Health() {
  const [checks, setChecks] = useState(null);

  useEffect(() => {
    const poll = () =>
      api
        .ready()
        .then((r) => setChecks(r.data.checks))
        .catch((e) => setChecks(e.data?.checks ?? { api: "unreachable" }));
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="health">
      {checks ? (
        Object.entries(checks).map(([dep, state]) => (
          <span key={dep} className={`pill ${state === "ok" ? "up" : "down"}`}>
            <i /> {dep}
          </span>
        ))
      ) : (
        <span className="pill">checking…</span>
      )}
    </div>
  );
}

function Auth({ user, onUser, say }) {
  const [email, setEmail] = useState("ops@deliveriq.io");
  const [password, setPassword] = useState("opspassword123");
  const [busy, setBusy] = useState(false);

  async function go(kind) {
    setBusy(true);
    try {
      if (kind === "register") await api.register(email, password);
      const { data } = await api.login(email, password);
      setToken(data.access_token);
      const me = await api.me();
      onUser(me.data);
      say(`signed in as ${me.data.email} (${me.data.role})`, "ok");
    } catch (e) {
      say(e.message, "err");
    } finally {
      setBusy(false);
    }
  }

  if (user) {
    return (
      <div className="auth-bar">
        <span className="who">
          {user.email}
          <span className={`role role-${user.role}`}>{user.role}</span>
        </span>
        <button
          className="ghost"
          onClick={() => {
            setToken(null);
            onUser(null);
            say("signed out");
          }}
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <div className="auth-bar">
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="password"
      />
      <button disabled={busy} onClick={() => go("login")}>
        Sign in
      </button>
      <button className="ghost" disabled={busy} onClick={() => go("register")}>
        Register
      </button>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [riders, setRiders] = useState([]);
  const [log, setLog] = useState([]);
  const [busy, setBusy] = useState(false);

  const say = useCallback((msg, kind = "info") => {
    setLog((l) =>
      [{ msg, kind, at: new Date().toLocaleTimeString() }, ...l].slice(0, 14),
    );
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [o, r] = await Promise.all([api.listOrders(), api.listRiders()]);
      setOrders(o.data);
      setRiders(r.data);
    } catch {
      /* transient poll failure — the health pills already show it */
    }
  }, []);

  useEffect(() => {
    if (getToken()) {
      api
        .me()
        .then((r) => setUser(r.data))
        .catch(() => setToken(null));
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, [refresh]);

  async function addRider() {
    setBusy(true);
    try {
      await api.createRider({
        name: `Rider-${Math.floor(Math.random() * 900 + 100)}`,
        current_lat: 28.61 + (Math.random() - 0.5) * 0.02,
        current_lon: 77.2 + (Math.random() - 0.5) * 0.02,
      });
      say("rider added", "ok");
      refresh();
    } catch (e) {
      say(e.message, "err");
    } finally {
      setBusy(false);
    }
  }

  async function addOrder(withKey) {
    setBusy(true);
    try {
      const body = {
        customer_id: Math.floor(Math.random() * 100) + 1,
        restaurant_id: Math.floor(Math.random() * 20) + 1,
        value: Math.floor(Math.random() * 900) + 100,
        pickup_lat: 28.61,
        pickup_lon: 77.2,
        drop_lat: 28.65,
        drop_lon: 77.25,
      };
      // A FIXED key on purpose: click it twice and the second call is served
      // from the idempotency cache, which is the feature made visible.
      const { replayed } = await api.createOrder(
        body,
        withKey ? "demo-fixed-key" : undefined,
      );
      say(
        replayed ? "REPLAYED — no second order created" : "order created",
        replayed ? "warn" : "ok",
      );
      refresh();
    } catch (e) {
      say(e.message, "err");
    } finally {
      setBusy(false);
    }
  }

  async function dispatch() {
    setBusy(true);
    try {
      const { data } = await api.dispatch();
      say(
        `dispatched order ${data.dispatched.order_id} → rider ${data.dispatched.rider_id}`,
        "ok",
      );
      refresh();
    } catch (e) {
      say(e.message, "err");
    } finally {
      setBusy(false);
    }
  }

  async function advance(id, status) {
    try {
      await api.setStatus(id, status);
      say(`order ${id} → ${status}`, "ok");
      refresh();
    } catch (e) {
      say(`order ${id}: ${e.message}`, "err");
    }
  }

  const counts = orders.reduce(
    (a, o) => ({ ...a, [o.status]: (a[o.status] || 0) + 1 }),
    {},
  );
  const free = riders.filter((r) => r.status === "AVAILABLE").length;

  return (
    <div className="app">
      <header>
        <div>
          <h1>DeliverIQ</h1>
          <p className="sub">
            Distributed order dispatch · FastAPI · Postgres · Redis · Kafka
          </p>
        </div>
        <Health />
      </header>

      <Auth user={user} onUser={setUser} say={say} />

      <section className="stats">
        {["PENDING", "ASSIGNED", "PICKED_UP", "DELIVERED"].map((s) => (
          <div key={s} className="stat">
            <span className="n">{counts[s] || 0}</span>
            <span className="l">{s.replace("_", " ")}</span>
          </div>
        ))}
        <div className="stat">
          <span className="n">
            {free}
            <small>/{riders.length}</small>
          </span>
          <span className="l">RIDERS FREE</span>
        </div>
      </section>

      <section className="actions">
        <button onClick={addRider} disabled={busy}>
          + Rider
        </button>
        <button onClick={() => addOrder(false)} disabled={busy}>
          + Order
        </button>
        <button className="alt" onClick={() => addOrder(true)} disabled={busy}>
          + Order <span className="tag">fixed Idempotency-Key</span>
        </button>
        <button className="primary" onClick={dispatch} disabled={busy}>
          Dispatch next →
        </button>
      </section>

      <div className="cols">
        <section className="panel">
          <h2>
            Orders <span className="count">{orders.length}</span>
          </h2>
          <div className="rows">
            {orders.length === 0 && <p className="empty">No orders yet.</p>}
            {[...orders].reverse().map((o) => (
              <div key={o.id} className="row">
                <span className="id">#{o.id}</span>
                <span className={`badge s-${o.status}`}>{o.status}</span>
                <span className="val">₹{o.value}</span>
                {o.rider_id && <span className="rid">rider {o.rider_id}</span>}
                <span className="grow" />
                {(STATUS_FLOW[o.status] || []).map((next) => (
                  <button
                    key={next}
                    className="tiny"
                    onClick={() => advance(o.id, next)}
                  >
                    {next}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <h2>Activity</h2>
          <div className="rows">
            {log.length === 0 && <p className="empty">Actions appear here.</p>}
            {log.map((l, i) => (
              <div key={i} className={`row log ${l.kind}`}>
                <span className="ts">{l.at}</span>
                <span>{l.msg}</span>
              </div>
            ))}
          </div>
          <p className="hint">
            Status changes require a signed-in <b>ops</b> user or the{" "}
            <b>assigned rider</b> — anyone else gets 403.
          </p>
        </section>
      </div>

      <footer>
        <a href="/docs" target="_blank" rel="noreferrer">
          API docs
        </a>
        <a href="http://localhost:3000/d/deliveriq-main" target="_blank" rel="noreferrer">
          Grafana
        </a>
        <a href="http://localhost:9090" target="_blank" rel="noreferrer">
          Prometheus
        </a>
        <a href="http://localhost:8080" target="_blank" rel="noreferrer">
          Kafka UI
        </a>
      </footer>
    </div>
  );
}
