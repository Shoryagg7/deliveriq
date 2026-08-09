# DeliverIQ — Frontend Project Map

> Code-oriented reference. Every row below was read out of the repository, not
> assumed. Companion to `FRONTEND_REACT_INTERVIEW_GUIDE.md` (the teaching doc)
> and `FRONTEND_INTERVIEW_CHEATSHEET.md` (the revision doc).

---

## 1. Directory tree (actual)

```
frontend/
├── index.html              ← the ONLY HTML page. Contains <div id="root">
├── package.json            ← dependencies + npm scripts
├── package-lock.json
├── vite.config.js          ← React plugin, build outDir, dev API proxy
├── .oxlintrc.json          ← linter rules (react/rules-of-hooks)
├── .gitignore              ← ignores dist/ and node_modules
├── README.md               ← untouched Vite template boilerplate
├── public/
│   ├── favicon.svg
│   └── icons.svg           ← present but NOT imported by any source file
├── src/
│   ├── main.jsx     (9 lines)    ← entry point: mounts React onto #root
│   ├── App.jsx      (439 lines)  ← ALL 4 components live here
│   ├── api.js       (69 lines)   ← the entire HTTP layer + token storage
│   ├── App.css      (204 lines)  ← all styling, hand-written CSS
│   └── assets/
│       ├── hero.png            ← NOT imported by any source file
│       ├── react.svg           ← NOT imported by any source file
│       └── vite.svg            ← NOT imported by any source file
└── dist/                   ← build output, gitignored, served by FastAPI
```

**Total hand-written source: 721 lines** (`main.jsx` + `App.jsx` + `api.js` + `App.css`).

There is **no** `components/`, `pages/`, `hooks/`, `context/`, `services/`, or
`routes/` folder. Say this plainly in an interview — it is a deliberate scale
choice for a 4-component console, not an oversight.

---

## 2. Dependencies (exact installed versions from `package-lock.json`)

| Package | Version | Type | What it does here |
|---|---|---|---|
| `react` | 19.2.8 | dependency | The UI library itself |
| `react-dom` | 19.2.8 | dependency | Renders React to the browser DOM (`createRoot`) |
| `vite` | 8.2.0 | devDependency | Dev server (HMR) + production bundler |
| `@vitejs/plugin-react` | 6.0.5 | devDependency | Compiles JSX → JS. Uses **Oxc** under the hood |
| `oxlint` | 1.76.0 | devDependency | Linter. Enforces `react/rules-of-hooks` |
| `@types/react` | 19.2.17 | devDependency | Type hints for editors only — **project is not TypeScript** |
| `@types/react-dom` | 19.2.3 | devDependency | Same |

**Runtime dependencies: exactly two.** React and React-DOM. Nothing else ships
to the browser.

**Explicitly NOT present** (do not claim any of these): React Router, Redux,
Zustand, Recoil, MobX, Context API, Axios, TanStack/React Query, SWR, Tailwind,
Bootstrap, Material UI, Ant Design, shadcn/ui, styled-components, Emotion,
Sass/Less, Chart.js, Recharts, D3, react-icons, Lucide, Formik, React Hook Form,
Yup, Zod, TypeScript, Jest, Vitest, React Testing Library, Playwright, Cypress.

---

## 3. Files table

| File | Responsibility | Important concepts | APIs touched |
|---|---|---|---|
| [index.html](../frontend/index.html) | The single HTML document the browser loads. Holds `<div id="root">` and the `<script type="module" src="/src/main.jsx">` tag | DOM, script module, viewport meta | — |
| [src/main.jsx](../frontend/src/main.jsx) | Entry point. `createRoot(...).render(<StrictMode><App /></StrictMode>)` | React root, StrictMode, JSX, import | — |
| [src/App.jsx](../frontend/src/App.jsx) | The entire UI: 4 components, all state, all event handlers | useState, useEffect, useCallback, props, conditional rendering, list rendering, keys, controlled inputs, polling | all 10 (via `api.js`) |
| [src/api.js](../frontend/src/api.js) | HTTP wrapper around `fetch`, JWT storage, error normalisation, idempotency header | async/await, fetch, localStorage, try/catch, custom Error, template literals, named exports | all 10 |
| [src/App.css](../frontend/src/App.css) | All styling. CSS custom properties, Flexbox, Grid, one media query | `:root` variables, Flexbox, Grid, pseudo-classes, `@media` | — |
| [vite.config.js](../frontend/vite.config.js) | Dev proxy to `:8000`, build output to `dist/` | Build tooling, same-origin strategy | proxies 8 path prefixes |
| [.oxlintrc.json](../frontend/.oxlintrc.json) | Lint rules — `react/rules-of-hooks: error` | Rules of Hooks | — |

---

## 4. Routes

**There is no client-side router.** The console is a single view at `/`.

| URL | Served by | Renders |
|---|---|---|
| `/` | FastAPI `StaticFiles(..., html=True)` — [app/main.py:136](../app/main.py#L136) | `index.html` → `main.jsx` → `<App />` |
| `/docs` | FastAPI (Swagger UI) | Not React — a plain `<a href>` in the footer |
| anything else | FastAPI | **404.** `html=True` serves index.html at the mount root only; it does not rewrite unknown paths |

The "views" a user perceives are **conditional renders driven by state**, not routes:

| Perceived view | Condition | Source |
|---|---|---|
| Signed-out login strip | `user === null` | [App.jsx:159-181](../frontend/src/App.jsx#L159-L181) |
| Signed-in identity strip | `user !== null` | [App.jsx:129-158](../frontend/src/App.jsx#L129-L158) |
| Ops stats bar | `user?.role === "ops"` | [App.jsx:327](../frontend/src/App.jsx#L327) |
| Permission warning note | `!isOps` | [App.jsx:367-372](../frontend/src/App.jsx#L367-L372) |
| Empty orders panel | `orders.length === 0` | [App.jsx:381](../frontend/src/App.jsx#L381) |
| Empty activity panel | `log.length === 0` | [App.jsx:406](../frontend/src/App.jsx#L406) |

---

## 5. Components

All four are defined in `App.jsx`. Only `App` is exported.

| Component | Lines | Props | State (useState) | Events | Effects | Renders |
|---|---|---|---|---|---|---|
| `App` | [187-439](../frontend/src/App.jsx#L187-L439) | none (root) | `user`, `orders`, `riders`, `log`, `busy` | `onClick` ×6 | 2 (session restore, 4s poll) | `<Health/>`, `<Auth/>`, `<Stats/>`, counters, orders list, activity log, footer |
| `Auth` | [89-185](../frontend/src/App.jsx#L89-L185) | `user`, `onUser`, `say` | `email`, `password`, `busy` | `onChange` ×2, `onClick` ×4+ | none | login inputs OR identity chip + role switcher |
| `Health` | [16-43](../frontend/src/App.jsx#L16-L43) | none | `checks` | none | 1 (5s poll of `/ready`) | dependency pills (postgres / redis / kafka) |
| `Stats` | [53-87](../frontend/src/App.jsx#L53-L87) | `say` | `stats` | none | 1 (6s poll of `/admin/stats`) | ops-only metrics strip; returns `null` if no data |

### Props detail

| Parent | Child | Prop | Type | Purpose |
|---|---|---|---|---|
| `App` | `Auth` | `user` | object \| null | Lets `Auth` choose login form vs identity strip |
| `App` | `Auth` | `onUser` | function (`setUser`) | Child pushes the signed-in user **up** to the parent |
| `App` | `Auth` | `say` | function (`useCallback`) | Child writes into the parent's activity log |
| `App` | `Stats` | `say` | function (`useCallback`) | Same — report errors to the shared log |

`Health` receives no props. This is the complete props inventory — three props, one child-to-parent callback pattern (`onUser`), and one shared logger (`say`).

---

## 6. State ownership

| State | Owner | Initial | Written by | Read by / UI it drives |
|---|---|---|---|---|
| `user` | `App` [188](../frontend/src/App.jsx#L188) | `null` | session-restore effect, `Auth` via `onUser` | `isOps`, `<Stats/>` mount, button `disabled`, permission note, `Auth` branch |
| `orders` | `App` [189](../frontend/src/App.jsx#L189) | `[]` | `refresh()` every 4s | orders panel, `counts`, order count badge |
| `riders` | `App` [190](../frontend/src/App.jsx#L190) | `[]` | `refresh()` every 4s | `free` counter, `RIDERS FREE` tile |
| `log` | `App` [191](../frontend/src/App.jsx#L191) | `[]` | `say()` — capped at 14 entries | activity panel |
| `busy` | `App` [192](../frontend/src/App.jsx#L192) | `false` | all four action handlers | `disabled` on action buttons |
| `email` | `Auth` [90](../frontend/src/App.jsx#L90) | `"ops@deliveriq.io"` | `onChange`, `switchTo()` | email input `value` |
| `password` | `Auth` [91](../frontend/src/App.jsx#L91) | `"opspassword123"` | `onChange`, `switchTo()` | password input `value` |
| `busy` | `Auth` [92](../frontend/src/App.jsx#L92) | `false` | `go()`, `switchTo()` | `disabled` on auth buttons |
| `checks` | `Health` [17](../frontend/src/App.jsx#L17) | `null` | 5s `/ready` poll | health pills, `checking…` placeholder |
| `stats` | `Stats` [54](../frontend/src/App.jsx#L54) | `null` | 6s `/admin/stats` poll | ops strip; `null` → render nothing |

**Architecture in one line:** state is **local `useState`, lifted to `App` when
two components need it**. No global store, no Context. The one piece of state
that lives outside React is the JWT — a module-level `let token` in
[api.js:7](../frontend/src/api.js#L7) mirrored into `localStorage`.

---

## 7. Hooks inventory

| Hook | Call sites | Where |
|---|---|---|
| `useState` | **10** | `Health` ×1, `Stats` ×1, `Auth` ×3, `App` ×5 |
| `useEffect` | **4** | `Health` ×1, `Stats` ×1, `App` ×2 |
| `useCallback` | **2** | `App` — `say` and `refresh` |

Not used anywhere: `useRef`, `useMemo`, `useContext`, `useReducer`,
`useLayoutEffect`, `useId`, `use`, custom hooks.

### Effects detail

| Component | Deps | Interval | Cleanup | Purpose |
|---|---|---|---|---|
| `Health` [19-28](../frontend/src/App.jsx#L19-L28) | `[]` | 5000 ms | `clearInterval` | poll `/ready`, show dependency pills |
| `Stats` [56-68](../frontend/src/App.jsx#L56-L68) | `[say]` | 6000 ms | `clearInterval` | poll `/admin/stats` (ops only) |
| `App` [210-217](../frontend/src/App.jsx#L210-L217) | `[]` | — | none | restore session from stored JWT on load |
| `App` [219-223](../frontend/src/App.jsx#L219-L223) | `[refresh]` | 4000 ms | `clearInterval` | poll `/orders` + `/riders` in parallel |

Three independent timers run concurrently: **4 s, 5 s, 6 s**.

---

## 8. API layer — `src/api.js`

Every network call in the app goes through one function, `request()`
([api.js:18-48](../frontend/src/api.js#L18-L48)). There is no Axios, no React
Query — just the browser's built-in `fetch`.

### The 10 methods

| `api.*` method | HTTP | Path | Auth required (server) | Called from |
|---|---|---|---|---|
| `ready()` | GET | `/ready` | no | `Health` effect |
| `register(email, password)` | POST | `/auth/register` | no | `Auth.go("register")` |
| `login(email, password)` | POST | `/auth/login` | no | `Auth.go()`, `Auth.switchTo()` |
| `me()` | GET | `/auth/me` | **yes** (bearer) | `Auth.go`, `Auth.switchTo`, `App` restore effect |
| `listOrders()` | GET | `/orders` | no | `App.refresh()` |
| `createOrder(body, idempotencyKey)` | POST | `/orders` | no | `App.addOrder()` |
| `dispatch()` | POST | `/orders/dispatch` | **ops** → 403 | `App.dispatch()` |
| `setStatus(id, status)` | PATCH | `/orders/{id}/status` | **yes** + actor guard | `App.advance()` |
| `listRiders()` | GET | `/riders` | no | `App.refresh()` |
| `createRider(body)` | POST | `/riders` | **ops** → 403 | `App.addRider()` |
| `stats()` | GET | `/admin/stats` | **ops** → 403 | `Stats` effect |

HTTP verbs actually used: **GET, POST, PATCH**. No PUT, no DELETE anywhere.

### Headers `request()` sets

| Header | When | Source |
|---|---|---|
| `Content-Type: application/json` | only when a body exists | [api.js:20](../frontend/src/api.js#L20) |
| `Authorization: Bearer <jwt>` | only when a token exists | [api.js:21](../frontend/src/api.js#L21) |
| `Idempotency-Key: <key>` | only when caller passes one | [api.js:23](../frontend/src/api.js#L23) |

### Return shape

```js
return { data, replayed: res.headers.get("Idempotent-Replay") === "true" };
```

`replayed` is read only by `addOrder()` ([App.jsx:261-268](../frontend/src/App.jsx#L261-L268))
to print `REPLAYED — no second order created`.

### Error normalisation

The backend emits **three different error shapes**. `request()` flattens all of them:

| Source | Shape | Example |
|---|---|---|
| `DeliverIQError` handler ([app/main.py:142](../app/main.py#L142)) | `{error, message}` | `{"error":"NO_PENDING_ORDERS","message":"..."}` |
| FastAPI `HTTPException` | `{detail}` | `{"detail":"Ops privileges required"}` |
| Rate limiter ([rate_limiter.py:86](../app/middleware/rate_limiter.py#L86)) | `{error}` | `{"error":"Rate limit exceeded..."}` |

```js
const msg = data?.message || data?.detail || data?.error || `HTTP ${res.status}`;
const err = new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
err.status = res.status;
err.data = data;
throw err;
```

The `typeof msg === "string"` guard exists because FastAPI's **422 validation**
errors put an *array* in `detail`, not a string.

---

## 9. Backend endpoint guards (what produces 401 vs 403)

| Endpoint | Guard | Failure code |
|---|---|---|
| `GET /orders` | none | — |
| `POST /orders` | **none** | — |
| `POST /orders/dispatch` | `require_ops` | 401 no token / **403** wrong role |
| `PATCH /orders/{id}/status` | `get_current_user` + `assert_may_change_status` | 401 / **403** / 400 illegal transition / 404 |
| `GET /riders` | none | — |
| `POST /riders` | `require_ops` | 401 / **403** |
| `GET /admin/stats` | router-level `require_admin` | 401 / **403** |
| `POST /auth/register` | none | 409 duplicate email |
| `POST /auth/login` | none | **401** bad credentials |
| `GET /auth/me` | `get_current_user` | **401** |

Source: [app/core/dependencies.py](../app/core/dependencies.py),
[app/routers/](../app/routers/).

---

## 10. Build & run

| Command | What it does |
|---|---|
| `npm run dev` | Vite dev server + HMR. Proxies `/orders /riders /auth /admin /ready /health /metrics /docs` → `http://localhost:8000` |
| `npm run build` | Bundles to `frontend/dist/` |
| `npm run preview` | Serves the built bundle locally |
| `npm run lint` | Runs `oxlint` |

**Environment variables: none.** No `.env`, no `import.meta.env` usage. The API
base URL is the empty string ([api.js:5](../frontend/src/api.js#L5)) because the
frontend is always same-origin — proxied in dev, served by FastAPI in production
([app/main.py:130-136](../app/main.py#L130-L136)). That is why there is no CORS
configuration anywhere in the codebase.

---

## 11. CSS map

| Concept | Used? | Where |
|---|---|---|
| CSS custom properties (`:root` variables) | ✅ | [App.css:5-21](../frontend/src/App.css#L5-L21) — 16 tokens |
| Flexbox | ✅ heavily | `header`, `.auth-bar`, `.row`, `.actions`, `.health`, `footer` |
| CSS Grid | ✅ | `.stats` (`auto-fit, minmax(150px, 1fr)`), `.cols` (`1.45fr 1fr`) |
| Media query | ✅ ×1 | [App.css:138](../frontend/src/App.css#L138) — `max-width: 900px` collapses `.cols` to one column |
| Pseudo-classes | ✅ | `:hover`, `:focus`, `:disabled`, `:not()`, `:last-child` |
| Pseudo-elements | ✅ | `h1::after` injects the "ops console" badge; `::-webkit-scrollbar` |
| Class selectors | ✅ | the dominant selector type |
| ID selectors | ❌ | `#root` exists in HTML but is never styled |
| `position` | ❌ | not used |
| CSS Modules / preprocessors | ❌ | one plain global stylesheet |

**Dynamic class pattern** — template literals build class names from state:

```jsx
className={`pill ${state === "ok" ? "up" : "down"}`}   // Health
className={`badge s-${o.status}`}                       // order badge → .s-PENDING etc.
className={`chip ${user.role === d.label ? "on" : ""}`} // active role chip
className={`role role-${user.role}`}                    // .role-ops / .role-rider
```

Note `.role-customer` is **not defined** in the CSS — a customer's role chip
falls back to the base `.role` styling.

---

## 12. Known defects & rough edges (verified)

| # | Issue | Location | Evidence |
|---|---|---|---|
| 1 | **Dead code**: rider badge never renders — `OrderResponse` has no `rider_id` field | [App.jsx:387](../frontend/src/App.jsx#L387) | [app/schemas/order.py](../app/schemas/order.py) declares only `id, customer_id, value, status, created_at` |
| 2 | Array index used as `key` on a **prepended** list | [App.jsx:408](../frontend/src/App.jsx#L408) | `say()` unshifts, so every index shifts on each new entry |
| 3 | No `<form>` element → **Enter key does not submit** login | [App.jsx:160-173](../frontend/src/App.jsx#L160-L173) | zero occurrences of `<form`, `onSubmit`, `preventDefault` |
| 4 | JWT in `localStorage` → readable by any XSS | [api.js:7-13](../frontend/src/api.js#L7-L13) | `localStorage.getItem("diq_token")` |
| 5 | `refresh()` swallows every error silently | [App.jsx:205-207](../frontend/src/App.jsx#L205-L207) | empty `catch {}` |
| 6 | `advance()` sets no `busy` flag → double-click can double-fire | [App.jsx:293-301](../frontend/src/App.jsx#L293-L301) | no `setBusy` in that handler |
| 7 | Polling has no backoff and never pauses on a hidden tab | 3 × `setInterval` | 4 s / 5 s / 6 s, unconditional |
| 8 | `counts` rebuilds the accumulator object per item (`{...a}`) | [App.jsx:308-311](../frontend/src/App.jsx#L308-L311) | O(n²) allocation; irrelevant at demo scale |
| 9 | No Error Boundary — a render crash blanks the page | — | zero occurrences of `componentDidCatch` / `ErrorBoundary` |
| 10 | Demo credentials hard-coded in shipped source | [App.jsx:47-51](../frontend/src/App.jsx#L47-L51) | `DEMO_LOGINS` array |
| 11 | Single `busy` flag disables **all** action buttons during any one action | [App.jsx:192](../frontend/src/App.jsx#L192) | shared across `addRider`/`addOrder`/`dispatch` |
| 12 | No `AbortController` — in-flight requests are not cancelled on unmount | [api.js:25](../frontend/src/api.js#L25) | `fetch` called without `signal` |
| 13 | Unused assets shipped in the repo | `src/assets/*`, `public/icons.svg` | no `import` references them |
| 14 | Root `frontend/README.md` is untouched Vite boilerplate | [frontend/README.md](../frontend/README.md) | describes a template, not this app |

Each of these has a prepared answer in **Part 6 → "Areas Where An Interviewer
Could Catch Me"** of the main guide.

---

## 13. One-screen architecture

```
Browser
  │  GET /
  ▼
index.html  ──  <div id="root">
  │            <script type="module" src="/src/main.jsx">
  ▼
main.jsx    ──  createRoot(#root).render(<StrictMode><App/></StrictMode>)
  │
  ▼
App.jsx  ── App()                        state: user, orders, riders, log, busy
  ├── <Health/>   ── 5 s poll ─────────────────────┐
  ├── <Auth/>     ── props: user, onUser, say      │
  ├── <Stats/>    ── 6 s poll (ops only) ──────────┤
  ├── counters    ── derived from orders/riders    │
  ├── actions     ── onClick handlers ─────────────┤
  ├── orders list ── [...orders].reverse().map()   │
  └── activity    ── log.map()                     │
                                                   ▼
                                        api.js → request() → fetch()
                                                   │  Authorization: Bearer <jwt>
                                                   ▼
                                        FastAPI (same origin, :8000)
                                        /auth /orders /riders /admin /ready
                                                   │
                                        Postgres · Redis · Kafka
```
