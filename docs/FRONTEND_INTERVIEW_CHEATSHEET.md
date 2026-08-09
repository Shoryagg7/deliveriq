# DeliverIQ Frontend — Rapid Revision Cheat Sheet

> Read this in 15 minutes before an interview. Everything here is verified
> against the repo. Full explanations: `FRONTEND_REACT_INTERVIEW_GUIDE.md`.

---

## 1. My frontend stack (say exactly this)

> "React 19 with Vite, plain JavaScript — no TypeScript. Two runtime
> dependencies: React and React-DOM. Styling is hand-written CSS with custom
> properties, Flexbox and Grid. HTTP is the browser's native `fetch` behind a
> thin wrapper I wrote in `api.js`. No router, no state library, no UI kit — the
> console is a single view with four components, so those would have been
> weight without benefit."

| Thing | Answer |
|---|---|
| Framework | React **19.2.8** + react-dom 19.2.8 |
| Build tool | **Vite 8.2.0**, `@vitejs/plugin-react` 6.0.5 (Oxc-based) |
| Language | **JavaScript (JSX)** — not TypeScript |
| Linter | **oxlint 1.76.0**, `react/rules-of-hooks: error` |
| Styling | One hand-written `App.css` (204 lines) |
| HTTP | Native `fetch` in `src/api.js` — **no Axios** |
| Router | **None** — single view |
| State library | **None** — `useState` + lifting |
| Source size | 721 lines across 4 files |
| Components | 4 — `App`, `Auth`, `Health`, `Stats` |
| Hooks used | `useState` (10), `useEffect` (4), `useCallback` (2) |

---

## 2. React in 10 lines

1. React is a **JavaScript library for building user interfaces** — not a framework.
2. The UI is built from **components**: functions that return JSX.
3. **JSX** looks like HTML but compiles to `React.createElement(...)` calls.
4. React keeps a **virtual DOM** — a lightweight in-memory tree.
5. **State** is data that, when it changes, must redraw the UI.
6. You change state with a **setter** (`setOrders`), never by assignment.
7. Setting state schedules a **re-render**: React calls the function again.
8. React **diffs** old tree vs new tree and patches only what changed.
9. This is **declarative**: I describe the UI *for* a state, not the steps to mutate the DOM.
10. **Hooks** (`useState`, `useEffect`) let function components hold state and run side effects.

---

## 3. JavaScript I actually use

| Concept | Where in my code |
|---|---|
| `const` / `let` | `const` everywhere; `let token` in `api.js:7` (only real reassignment) |
| Arrow functions | 49 occurrences — every handler, every `.map` callback |
| Template literals | `` `Bearer ${token}` ``, `` `order ${id} → ${status}` ``, dynamic classNames |
| Destructuring | `const { data } = await api.login(...)`, `({ user, onUser, say })`, `([dep, state])` |
| Spread `...` | `[...orders].reverse()`, `[newEntry, ...l]`, `{...a}` in reduce |
| `.map()` | 8× — orders, log, health pills, role chips, status buttons |
| `.filter()` | 1× — `riders.filter(r => r.status === "AVAILABLE").length` |
| `.reduce()` | 1× — order status counts |
| `.slice()` | 1× — `.slice(0, 14)` caps the activity log |
| Optional chaining `?.` | `user?.role`, `e.data?.checks`, `data?.message` |
| Nullish coalescing `??` | `e.data?.checks ?? { api: "unreachable" }` |
| Ternary | conditional classNames, `Auth` login-vs-identity branch |
| `&&` short-circuit | `{user?.role === "ops" && <Stats/>}` |
| `async` / `await` | every handler + `request()` |
| `try/catch/finally` | 8 blocks; `finally { setBusy(false) }` |
| `Promise.all` | `refresh()` — orders + riders in parallel |
| `JSON.parse` / `stringify` | `api.js` — response parsing and request bodies |
| Modules | `import`/`export` in all three JS files |
| `Object.entries()` | 2× — health checks, riders-by-status |

**Interview line:** *"Nothing exotic — array methods to turn data into JSX,
async/await for the network, destructuring and optional chaining to read
responses safely."*

---

## 4. Hooks I use

### `useState` — memory that triggers re-render
```jsx
const [orders, setOrders] = useState([]);
```
Array destructuring: current value, setter function, initial value. A plain
`let` would change but **would not redraw** — React only re-renders when a
setter is called.

### `useEffect` — run code outside rendering
```jsx
useEffect(() => {
  refresh();
  const id = setInterval(refresh, 4000);
  return () => clearInterval(id);   // cleanup
}, [refresh]);
```
- Runs **after** the render commits.
- Dep array `[]` → once on mount. `[refresh]` → whenever `refresh` changes.
- The returned function is **cleanup** — here it stops the timer so unmounting
  doesn't leak an interval.

### `useCallback` — a stable function identity
```jsx
const refresh = useCallback(async () => { ... }, []);
```
Without it, `refresh` would be a **new function on every render**, so the
effect that depends on `[refresh]` would tear down and restart its interval
every single render — an infinite poll loop. `say` is memoised for the same
reason (`Stats` depends on `[say]`).

**Not used anywhere:** `useRef`, `useMemo`, `useContext`, `useReducer`, custom hooks.

---

## 5. API flow

```
onClick → handler → setBusy(true) → api.X() → request() → fetch()
   → Authorization: Bearer <jwt>  →  FastAPI  →  JSON
   → setState(...)  →  React re-renders  →  DOM updated
   → finally setBusy(false)
```

**One function does all HTTP** — `request()` in `src/api.js:18-48`:
- builds headers (`Content-Type`, `Authorization`, optional `Idempotency-Key`)
- `await fetch(...)`
- reads text, tries `JSON.parse`, tolerates non-JSON
- on `!res.ok`: builds an `Error` carrying `.status` and `.data`, throws it
- returns `{ data, replayed }`

**Error normalisation** — the backend has three error shapes, flattened to one:
```js
data?.message || data?.detail || data?.error || `HTTP ${res.status}`
```

| `api.*` | Method | Endpoint |
|---|---|---|
| `ready()` | GET | `/ready` |
| `register` / `login` | POST | `/auth/register`, `/auth/login` |
| `me()` | GET | `/auth/me` |
| `listOrders()` | GET | `/orders` |
| `createOrder()` | POST | `/orders` |
| `dispatch()` | POST | `/orders/dispatch` |
| `setStatus()` | PATCH | `/orders/{id}/status` |
| `listRiders()` / `createRider()` | GET / POST | `/riders` |
| `stats()` | GET | `/admin/stats` |

Verbs used: **GET, POST, PATCH**. No PUT, no DELETE.
Codes I can speak to: **200, 201, 400, 401, 403, 404, 409, 429, 503**.

---

## 6. Project architecture

```
index.html  (#root)
   ↓
main.jsx    createRoot(...).render(<StrictMode><App/></StrictMode>)
   ↓
App.jsx     App()  — owns user, orders, riders, log, busy
   ├─ Health   (own state, 5 s poll of /ready)
   ├─ Auth     (props: user, onUser, say)
   ├─ Stats    (prop: say, 6 s poll, ops only)
   └─ lists    orders + activity, rendered with .map()
   ↓
api.js      request() → fetch()
   ↓
FastAPI (same origin) → Postgres · Redis · Kafka
```

**Same-origin, no CORS.** `const BASE = ""` in `api.js`. In dev, `vite.config.js`
proxies API paths to `:8000`; in production FastAPI serves the built bundle from
`frontend/dist`. One deploy artifact, no environment variable pointing at a
backend URL, no CORS config.

**State lives locally and is lifted only when shared.** `App` owns anything two
children need; `Health` and `Stats` own their own polling state because nobody
else reads it.

---

## 7. Five flows I must be able to explain

**1. Login.** Type email/password (controlled inputs → `setEmail`/`setPassword`)
→ click Sign in → `go("login")` → `setBusy(true)` → `POST /auth/login` →
`setToken(data.access_token)` writes module variable + `localStorage` →
`GET /auth/me` → `onUser(me.data)` calls parent's `setUser` → `App` re-renders →
`isOps` becomes true → ops buttons enable and `<Stats/>` mounts → `finally setBusy(false)`.

**2. Session restore on reload.** `App` mounts → effect with `[]` → `getToken()`
reads the module variable seeded from `localStorage` → if present, `GET /auth/me`
→ `setUser(r.data)`. On failure, `setToken(null)` clears the stale token.

**3. Create order + idempotency demo.** Click "+ Order (fixed Idempotency-Key)"
→ `addOrder(true)` → `POST /orders` with `Idempotency-Key: demo-fixed-key` →
middleware caches the first response in Redis → **second click returns the cached
response with header `Idempotent-Replay: true`** → `request()` surfaces
`replayed: true` → log prints `REPLAYED — no second order created` in amber. No
duplicate order is created.

**4. Dispatch (403 path).** As `customer`, the Dispatch button is `disabled`
because `isOps` is false, with a `title` explaining why. If the call *is* made,
`require_ops` returns **403** → `request()` throws with `.status = 403` →
`catch` → `say(e.message, "err")` → red line in the activity log. **The UI
disables; the server enforces.**

**5. Advance order status.** Order row renders buttons from `STATUS_FLOW[o.status]`
→ click `PICKED_UP` → `advance(id, "PICKED_UP")` → `PATCH /orders/{id}/status` →
server checks **legal transition** *and* **permitted actor** → success → `say(...)`
→ `refresh()` → new `orders` array → badge and available buttons change.

---

## 8. Thirty most likely questions — short answers

| # | Question | Answer |
|---|---|---|
| 1 | What is React? | A JS library for building UIs from components; I describe the UI for a given state and React updates the DOM. |
| 2 | Why React here? | The console re-renders continuously from polled data. Declarative state-driven rendering meant I never hand-wrote DOM updates. |
| 3 | Could you have used vanilla JS? | Yes — it's ~700 lines. I'd hand-write DOM updates for every poll and risk stale-UI bugs. React removed that class of bug; the cost was a build step. |
| 4 | What is JSX? | HTML-like syntax that compiles to `React.createElement` calls. Not HTML — `class` becomes `className`, and `{}` embeds JS expressions. |
| 5 | What is a component? | A function returning JSX. I have four: `App`, `Auth`, `Health`, `Stats`. |
| 6 | Props vs state? | Props come *from the parent* and are read-only; state is owned *by the component* and changing it re-renders. `Auth` receives `user` as a prop but owns `email` as state. |
| 7 | Give a props example. | `App` passes `user`, `onUser`, `say` to `Auth`. `onUser` is `setUser` — the child pushes the signed-in user back up. |
| 8 | What does `useState` return? | `[value, setter]`. I destructure: `const [busy, setBusy] = useState(false)`. |
| 9 | Why not a normal variable? | Reassigning a local variable doesn't tell React anything, and it resets each render. Calling the setter schedules a re-render. |
| 10 | Does `setState` update immediately? | No — it schedules. Reading the variable on the next line still gives the old value. |
| 11 | Why the functional updater? | `setLog(l => [...])` uses the latest value rather than the one captured in that render's closure. |
| 12 | Why not mutate state directly? | React compares references. Mutating in place keeps the same reference, so React may skip the re-render. That's why `refresh` assigns a **new** array. |
| 13 | What is `useEffect` for? | Side effects outside rendering — my API polls and session restore. It runs after the render is committed. |
| 14 | What does `[]` mean? | Run once on mount. `[refresh]` re-runs when `refresh` changes; **no array** re-runs every render. |
| 15 | What's the cleanup function? | The function returned from the effect. Mine calls `clearInterval` so unmounting stops the poll. |
| 16 | Why `useCallback` on `refresh`? | The polling effect depends on `[refresh]`. Without memoisation, `refresh` is a new function every render, so the interval would restart endlessly. |
| 17 | What is `StrictMode`? | A dev-only wrapper that intentionally mounts, unmounts and remounts effects to surface missing cleanup. My `clearInterval` is why that's harmless here. |
| 18 | Why `key` in lists? | It identifies items across renders so React reuses the right DOM node. I use `o.id` for orders. |
| 19 | Any bad keys? | Yes — the activity log uses the array index while prepending, so indexes shift. It's cosmetic-only there, but `l.at + msg` would be correct. |
| 20 | Controlled inputs? | `value` comes from state and `onChange` writes back: `value={email} onChange={e => setEmail(e.target.value)}`. State is the single source of truth. |
| 21 | Do you use a `<form>`? | No — inputs plus button `onClick`. The honest cost: Enter doesn't submit. A `<form onSubmit>` with `preventDefault()` would be the fix. |
| 22 | fetch or Axios? | `fetch`. Axios' conveniences (JSON parsing, error-on-4xx) are ~15 lines I wrote once in `request()`. Not worth a dependency for 10 endpoints. |
| 23 | Why async/await? | Network calls are asynchronous. `await` pauses *that function* without blocking the browser, and lets me use ordinary `try/catch`. |
| 24 | How do you store the token? | JWT in `localStorage` under `diq_token`, mirrored to a module variable so `request()` reads it without hitting storage each call. |
| 25 | Is `localStorage` safe? | It's readable by any JS on the page, so an XSS steals the token. An httpOnly cookie is the safer default; that needs CSRF protection in return. I chose it for demo simplicity and I'd change it for production. |
| 26 | 401 vs 403? | 401 = I don't know who you are. 403 = I know, you're not allowed. `require_ops` returns 403 to a signed-in customer. |
| 27 | Why disable rather than hide ops buttons? | A disabled button with a reason teaches the permission model; hidden looks like a missing feature. Either way **the server enforces it** — the UI is UX, not security. |
| 28 | How do you handle loading? | A `busy` state disables action buttons during a request, cleared in `finally`. Honest gap: no skeleton for the lists, and `advance()` has no busy flag. |
| 29 | How do you handle errors? | `request()` throws an `Error` carrying `.status` and `.data`; handlers `catch` and call `say(e.message, "err")`, which renders a red line in the activity panel. |
| 30 | How does the frontend reach the backend? | Same origin. `BASE = ""`. Vite proxies to `:8000` in dev; FastAPI serves the built bundle in production. No CORS anywhere. |

---

## 9. Things I must NOT claim

❌ Redux / Zustand / MobX — **no state library at all**
❌ Context API — `createContext` appears nowhere
❌ React Router / routing / protected routes — **single view, no router**
❌ Axios, React Query, SWR — native `fetch` only
❌ Tailwind / Bootstrap / MUI / shadcn — hand-written CSS
❌ TypeScript — `@types/*` are editor hints; source is `.jsx`/`.js`
❌ Charts, icon libraries, animation libraries
❌ Frontend tests — **there is no test file in `frontend/`**
❌ Custom hooks, `useRef`, `useMemo`, `useContext`, `useReducer`
❌ Form library or schema validation (Formik / RHF / Zod / Yup)
❌ Code-splitting, lazy loading, SSR, PWA, accessibility audit
❌ WebSockets / real-time — it is **polling** on 4 s / 5 s / 6 s timers
❌ Responsive design *system* — there is exactly **one** media query
❌ "Complex state management" — it is `useState` plus lifting, and that's fine

✅ **Safe to claim:** React 19 function components; hooks (`useState`,
`useEffect`, `useCallback`); props including a child→parent callback; lifting
state up; conditional and list rendering with keys; controlled inputs; a
hand-written `fetch` wrapper with unified error handling; JWT bearer auth with
localStorage persistence and session restore; role-driven UI (ops/rider/customer);
an idempotency-key demo surfaced through a response header; polling with
`setInterval` and correct `clearInterval` cleanup; CSS custom properties,
Flexbox and Grid; Vite build served same-origin by FastAPI.

---

## 10. The four defects to volunteer before you're asked

1. **Dead code:** `{o.rider_id && ...}` at `App.jsx:387` never renders — the
   backend's `OrderResponse` schema doesn't include `rider_id`. *Fix: add the
   field to the Pydantic response model.* **Verified.**
2. **Index keys on a prepended list** (`key={i}`, `App.jsx:408`).
3. **No `<form>`** — Enter doesn't submit the login.
4. **All 439 lines in one file** — fine at four components, but `Auth`,
   `Health`, `Stats` and the `api` layer are the natural split points the day a
   second view appears.

Volunteering these reads as judgement. Having them extracted reads as not knowing.

---

## 11. The 60-second pitch

> "DeliverIQ's frontend is a single-page ops console in React 19, built with
> Vite. It's deliberately small — four components in about 700 lines, with no
> router and no state library, because it's one screen.
>
> `App` owns the shared state: the signed-in user, orders, riders and an
> activity log. Three `setInterval` polls keep it live — orders and riders every
> four seconds, a dependency health check every five, ops-only stats every six —
> each with `clearInterval` cleanup in the effect.
>
> Every network call goes through one `request()` function in `api.js` that
> wraps `fetch`: it attaches the JWT bearer token, optionally an idempotency
> key, and normalises three different backend error shapes into one `Error`
> carrying the HTTP status. Handlers catch that and write a line into the
> activity log, so failures are visible instead of silent.
>
> The interesting part is the role model. Signing in as ops, rider or customer
> changes which controls are enabled — but that's only UX. The server enforces
> it, and the console is built to *show* that: a customer clicking a restricted
> action gets a real 403 rendered in the log. The other demo is idempotency —
> clicking 'add order' twice with a fixed key returns the cached response with
> an `Idempotent-Replay` header, and the UI says 'REPLAYED', so retry-safety is
> demonstrable rather than just claimed."
