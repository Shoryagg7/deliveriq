# DeliverIQ — Frontend & React Interview Guide

> **Written for someone who can program, but has almost no frontend experience.**
>
> Everything in this guide was read out of your actual repository. No generic
> React course material, no invented endpoints, no features you don't have.
> Where your code has a flaw, this guide says so and prepares you to discuss it.
>
> Companion documents:
> - `FRONTEND_PROJECT_MAP.md` — tables, file-by-file, code-oriented
> - `FRONTEND_INTERVIEW_CHEATSHEET.md` — 15-minute pre-interview revision

---

## How to read this

Each topic answers five questions in the same order:

**WHAT IS IT?** → **WHY DO WE NEED IT?** → **WHERE IS IT IN MY PROJECT?** →
**THE ACTUAL CODE** → **HOW TO EXPLAIN IT IN AN INTERVIEW**

Every concept is tagged:

| Tag | Meaning |
|---|---|
| 🔴 **MUST KNOW** | An interviewer will almost certainly ask. Do not skip. |
| 🟡 **SHOULD KNOW** | Likely as a follow-up. Learn after the reds. |
| ⚪ **OPTIONAL** | Only if you have spare time. You can say "I haven't needed that here." |

---

## The 30-second orientation

Your frontend is **721 lines of hand-written source across four files**:

```
frontend/src/main.jsx   9 lines    starts React
frontend/src/App.jsx  439 lines    the entire UI — 4 components
frontend/src/api.js    69 lines    all HTTP + token storage
frontend/src/App.css  204 lines    all styling
```

It is a **single-screen operations console** for your delivery dispatch backend.
It shows live counts of orders and riders, lets an operator create orders,
onboard riders and dispatch work, and demonstrates two backend features
visually: **role-based permissions** (403s) and **idempotent retries**.

It has **exactly two runtime dependencies**: `react` and `react-dom`.

That smallness is a strength if you frame it correctly. It is *not* a weakness
to have skipped Redux on a four-component app — it is a weakness to not know
*why* you skipped it. This guide makes sure you know why.

---

# Part 1 — Frontend Fundamentals I Need Before React

## 1.1 What actually happens when someone opens your app 🔴 MUST KNOW

Before any React: the browser needs an HTML document. Yours is
[frontend/index.html](../frontend/index.html) — the **only** HTML file in the
whole project:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DeliverIQ — Dispatch Console</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

Line by line:

| Line | What it does |
|---|---|
| `<!doctype html>` | Tells the browser "this is modern HTML" |
| `<html lang="en">` | Root element. `lang` helps screen readers and search engines |
| `<head>` | Information *about* the page — never displayed |
| `<meta charset="UTF-8">` | Text encoding, so `₹` and `→` render correctly (you use both) |
| `<meta name="viewport" ...>` | Makes the page scale correctly on phones |
| `<title>` | The browser tab text — "DeliverIQ — Dispatch Console" |
| `<body>` | The visible content |
| `<div id="root"></div>` | **Empty.** React fills this at runtime |
| `<script type="module" src="/src/main.jsx">` | Loads your JavaScript |

**The key insight:** your HTML file is essentially *empty*. There is no header,
no button, no table written in HTML. Everything a user sees is created by
JavaScript at runtime. That is what "**single-page application**" means.

> **Interview answer:** *"The HTML is a shell — one empty `div` with `id="root"`
> and a script tag. React mounts the whole interface into that div at runtime.
> Nothing the user sees exists in the HTML source."*

---

## 1.2 HTML elements, tags and attributes 🔴 MUST KNOW

**WHAT IS IT?** HTML describes the *structure* of a page using **tags**. A tag
is a keyword in angle brackets. Most come in pairs: an opening tag, content, and
a closing tag. Together that is an **element**.

```html
<button>Sign in</button>
   ↑        ↑        ↑
 opening  content  closing
```

**Attributes** are extra settings written inside the opening tag as
`name="value"`:

```html
<input type="password" placeholder="password" />
```

Here `type` and `placeholder` are attributes. `<input>` has no content, so it is
self-closing.

### The elements your project actually uses

Read from `App.jsx` — this is the complete list:

| Element | Meaning | Where in your code |
|---|---|---|
| `<div>` | Generic box, no meaning. A container | `.app`, `.health`, `.row`, `.stat` |
| `<span>` | Generic *inline* box (sits in a line of text) | badges, pills, counters |
| `<header>` | **Semantic**: page header | [App.jsx:316](../frontend/src/App.jsx#L316) |
| `<section>` | **Semantic**: a distinct part of the page | counters, actions, the two panels |
| `<footer>` | **Semantic**: page footer | [App.jsx:423](../frontend/src/App.jsx#L423) |
| `<h1>`, `<h2>` | Headings, level 1 and 2 | "DeliverIQ", "Orders", "Activity" |
| `<p>` | Paragraph | `.sub`, `.empty`, `.hint` |
| `<button>` | A clickable control | every action in the app |
| `<input>` | A text entry box | email and password |
| `<a>` | A link ("anchor") | footer links to API docs, Grafana |
| `<b>` | Bold text | inside the stats strip and hint text |
| `<small>` | Smaller text | `/{riders.length}` in the riders tile |
| `<i>` | Inline element — here used as a **dot** | the coloured status dot in health pills |

**Semantic elements** (`<header>`, `<section>`, `<footer>`) are elements whose
*name describes their purpose*. `<div>` says nothing; `<header>` says "this is
the page header". Screen readers and search engines use that meaning. Your
project uses them for page-level layout and `<div>`/`<span>` for everything
inside — a reasonable, common approach.

### Two elements you should notice are MISSING

🔴 **You have no `<form>` element and no `<table>` element.**

- Your login is two `<input>`s and two `<button>`s — *not* a form. This has a
  real consequence covered in §5.3: **pressing Enter does not sign you in.**
- Your "Orders" panel *looks* like a table but is built from `<div>`s styled with
  Flexbox ([App.jsx:383-398](../frontend/src/App.jsx#L383-L398)).

If asked "does your project use tables/forms?", the honest answer is *no*, plus
the reason. Never claim either.

### `id` vs `class` 🔴 MUST KNOW

Both label elements so CSS and JavaScript can find them.

- **`id`** — must be unique on the page. You have exactly one: `id="root"` in
  `index.html`. JavaScript finds it with `document.getElementById("root")` in
  [main.jsx:5](../frontend/src/main.jsx#L5).
- **`class`** — reusable, many elements can share it. This is what your CSS
  targets. Every visual style in `App.css` hangs off a class.

> **Interview answer:** *"`id` is unique — I have one, `root`, which is the
> element React mounts into. Classes are reusable and are what all my CSS
> selectors target. In JSX the attribute is spelled `className` because `class`
> is a reserved word in JavaScript."*

---

## 1.3 JSX → HTML: what your React code actually becomes 🔴 MUST KNOW

This is the single most important bridge for you. Your JSX **is not HTML** — it
is JavaScript that *produces* HTML elements in the browser.

Take a real snippet, [App.jsx:336-342](../frontend/src/App.jsx#L336-L342):

```jsx
<div className="stat">
  <span className="n">
    {free}
    <small>/{riders.length}</small>
  </span>
  <span className="l">RIDERS FREE</span>
</div>
```

If `free` is `3` and `riders.length` is `7`, the browser ends up with this real
HTML in the DOM:

```html
<div class="stat">
  <span class="n">3<small>/7</small></span>
  <span class="l">RIDERS FREE</span>
</div>
```

Three translations happened:

1. **`className` → `class`.** In JSX you must write `className`, because JSX is
   JavaScript and `class` is a reserved keyword there.
2. **`{free}` was evaluated.** Curly braces mean "run this JavaScript and insert
   the result". `{free}` became `3`.
3. **`{riders.length}`** — any JavaScript *expression* works, not just variables.

Another real one, [App.jsx:390-396](../frontend/src/App.jsx#L390-L396):

```jsx
<button className="tiny" onClick={() => advance(o.id, next)}>
  {next}
</button>
```

becomes, in the DOM:

```html
<button class="tiny">PICKED_UP</button>
```

...with a click listener attached by React. Note the `onClick` attribute does
**not** appear in the HTML — React registers the handler in JavaScript instead.

> **Interview answer:** *"JSX looks like HTML but it's compiled — Vite's React
> plugin turns every tag into a `React.createElement` call. The differences that
> bite you are `className` instead of `class`, camelCase event props like
> `onClick`, and curly braces for embedding JavaScript expressions. What lands in
> the browser is ordinary HTML elements."*

---

## 1.4 The DOM 🔴 MUST KNOW — high-probability question

**WHAT IS IT?** DOM = **Document Object Model**. When the browser reads HTML, it
builds a **tree of objects in memory**, one object per element. That tree is the
DOM. JavaScript can read and change it, and the screen updates to match.

**The pipeline:**

```
HTML text  →  browser parses it  →  DOM tree (objects in memory)  →  pixels
                                          ↑
                                   JavaScript can change this
```

For your `index.html`, the initial DOM tree is:

```
document
└── html
    ├── head
    │   └── title  "DeliverIQ — Dispatch Console"
    └── body
        ├── div#root          ← EMPTY at this moment
        └── script
```

Then [main.jsx](../frontend/src/main.jsx) runs:

```jsx
createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

`document.getElementById("root")` is a **direct DOM API call** — the one and only
place your project touches the DOM by hand. Everything after that, React does.

### The React relationship — the part interviewers probe 🔴

**Traditional JavaScript** — you find elements and mutate them yourself:

```js
// NOT in your project — this is what you would otherwise have to write
const el = document.querySelector(".count");
el.textContent = orders.length;
el.classList.add("updated");
```

You are giving **instructions**: find this, change that. This is **imperative**.

**React** — you change *state*, and React updates the DOM for you:

```jsx
// Your actual code, App.jsx:203
setOrders(o.data);
```

That is the whole update. You never wrote `document.querySelector`. You never
set `textContent`. You changed a value and **described** what the UI should look
like for that value:

```jsx
<h2>Orders <span className="count">{orders.length}</span></h2>
```

This is **declarative**: you describe the destination, not the route.

**How React does it:** React keeps a lightweight copy of the DOM tree in memory
(the **virtual DOM**). When state changes, it re-runs your component function to
build a fresh tree, **diffs** it against the previous one, and applies only the
minimal real DOM changes. If `orders.length` went from 6 to 7, React updates one
text node — it does not rebuild the panel.

### Walk through one real example

Your 4-second poll fires ([App.jsx:200-208](../frontend/src/App.jsx#L200-L208)):

1. `refresh()` calls `GET /orders`, gets back an array of 7 orders.
2. `setOrders(o.data)` — state changes from a 6-item array to a 7-item array.
3. React notices the state changed, so it **re-runs the `App()` function**.
4. `App()` returns a new description: `orders.length` is now `7`, and
   `[...orders].reverse().map(...)` produces 7 row elements instead of 6.
5. React diffs new vs old: the count text changed, and there is one extra row.
6. React touches exactly those two spots in the real DOM. The other six rows are
   untouched — because their `key` (`o.id`) matched.

> **Interview answer:** *"The DOM is the browser's in-memory object tree of the
> page — JavaScript changes the tree, the screen follows. In plain JavaScript I'd
> query elements and mutate them by hand, which means the UI and my data can
> drift apart. In React I only call a state setter — `setOrders(o.data)` in my
> refresh function — and React re-runs the component, diffs the result against
> the previous render, and patches just the changed nodes. My project touches the
> DOM directly exactly once: `document.getElementById("root")` in `main.jsx`, to
> tell React where to mount."*

---

## 1.5 CSS Fundamentals Used In My Project

**WHAT IS IT?** HTML gives structure, CSS gives appearance. A CSS rule has a
**selector** (what to style) and **declarations** (how):

```css
.pill { display: inline-flex; gap: 7px; }
  ↑              ↑
selector      declarations (property: value)
```

Your entire stylesheet is [frontend/src/App.css](../frontend/src/App.css) — 204
lines, hand-written, no framework. It is imported once, in
[App.jsx:3](../frontend/src/App.jsx#L3):

```jsx
import "./App.css";
```

That import is a **build-tool feature**, not standard JavaScript — Vite sees it
and injects the stylesheet into the page. The CSS is **global**: these are not
CSS Modules, so `.row` applies to every element with `class="row"` anywhere.

### What you actually use — and what you don't 🟡

| Concept | Used? | Where |
|---|---|---|
| Class selectors | ✅ dominant | `.panel`, `.row`, `.badge`, `.pill` |
| CSS custom properties (variables) | ✅ 16 of them | [App.css:5-21](../frontend/src/App.css#L5-L21) |
| Flexbox | ✅ heavily | `header`, `.auth-bar`, `.row`, `.actions`, `footer` |
| CSS Grid | ✅ twice | `.stats`, `.cols` |
| `margin` / `padding` / `border` | ✅ everywhere | — |
| Colours, fonts | ✅ | via variables |
| `:hover`, `:focus`, `:disabled` | ✅ | buttons and inputs |
| Pseudo-elements `::after` | ✅ | `h1::after` injects the "ops console" badge |
| Media query | ✅ **exactly one** | [App.css:138](../frontend/src/App.css#L138) |
| ID selectors | ❌ | `#root` exists but is never styled |
| `position` | ❌ | not used at all |
| Sass / CSS Modules / Tailwind | ❌ | plain global CSS |

### CSS variables 🔴 MUST KNOW (you clearly use them)

```css
:root {
  --bg: #0c0e13;
  --surface: #141821;
  --ink: #eef1f5;
  --accent: #ff7a45;
  --ok: #4ec99a;
  --err: #e86a6a;
  --radius: 10px;
}
```

`:root` means "the whole document". Names starting with `--` are **custom
properties** — variables. You then use them with `var()`:

```css
.panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}
```

**Why this matters:** the orange accent `#ff7a45` appears in ~8 rules. Defined
once, changed once. This is the same reason you use constants in Python.

> **Interview answer:** *"I used CSS custom properties as a small design-token
> layer — background, surface, text, accent and one radius defined once on
> `:root` and referenced with `var()`. It gave me consistency without a CSS
> framework, and re-theming means editing seven lines."*

### Flexbox 🔴 MUST KNOW

**WHAT IS IT?** Flexbox lays out children in **one direction** — a row or a
column — and controls how they share leftover space.

Your order row ([App.css:156-159](../frontend/src/App.css#L156-L159)):

```css
.row {
  display: flex;         /* lay children out in a row */
  align-items: center;   /* vertically centre them */
  gap: 12px;             /* 12px between each child */
  padding: 11px 4px;
  border-bottom: 1px solid var(--line);
}
```

And the trick that makes your layout work — [App.css:73](../frontend/src/App.css#L73):

```css
.grow { flex: 1; }
```

In the JSX ([App.jsx:388](../frontend/src/App.jsx#L388)) there is a bare
`<span className="grow" />` between the order details and the action buttons.
`flex: 1` tells that empty span "take all remaining space", which pushes the
buttons to the right edge. That is a **spacer** — a very common Flexbox idiom.

### CSS Grid 🟡 SHOULD KNOW

**WHAT IS IT?** Grid lays out in **two dimensions** — rows *and* columns.

Your counter tiles ([App.css:97-100](../frontend/src/App.css#L97-L100)):

```css
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}
```

Read that middle line as: *"make as many columns as fit; each is at least 150px
wide and otherwise shares space equally."* On a wide screen you get five tiles
in a row; on a narrow one they wrap automatically — **with no media query**.

### The one media query 🟡

```css
.cols { display: grid; grid-template-columns: 1.45fr 1fr; gap: 20px; }

@media (max-width: 900px) {
  .cols { grid-template-columns: 1fr; }
}
```

**WHAT IS IT?** A media query applies rules only when a condition holds. Here:
below 900px wide, the two panels (Orders and Activity) stack into one column
instead of sitting side by side.

⚠️ **Be precise in an interview.** You have *one* media query. Do not say "the
app is fully responsive". Say:

> *"There's one breakpoint at 900px that stacks the two panels, and the counter
> tiles reflow automatically because they use a Grid `auto-fit` with a `minmax`
> track. It's responsive enough for a desktop ops console, which is the actual
> use case — it isn't a mobile-first design and I wouldn't claim it is."*

### Dynamic class names 🔴 MUST KNOW

This is where CSS meets React in your code. You build class strings from state
using **template literals**:

```jsx
// App.jsx:34 — health pill turns green or red
<span className={`pill ${state === "ok" ? "up" : "down"}`}>

// App.jsx:385 — order badge picks its colour from the status
<span className={`badge s-${o.status}`}>{o.status}</span>

// App.jsx:141 — the currently-active role chip
<button className={`chip ${user.role === d.label ? "on" : ""}`}>
```

The second one is elegant: `s-${o.status}` produces `s-PENDING`, `s-ASSIGNED`,
`s-PICKED_UP`, `s-DELIVERED` or `s-CANCELLED` — and your CSS defines exactly
those five classes ([App.css:170-174](../frontend/src/App.css#L170-L174)). Data
drives styling with no `if` statement at all.

⚠️ **One honest gap to know about:** `.role-ops` and `.role-rider` are defined,
but **`.role-customer` is not**. Signed in as a customer, the role chip falls
back to the plain `.role` style. Harmless, but if an interviewer is reading your
CSS closely, know it before they mention it.

---

# Part 2 — JavaScript I Must Know To Understand My React Project

Every concept below appears in your code. Nothing here is theoretical.

## 2.1 `const` and `let` 🔴 MUST KNOW

**Simple meaning:** both declare variables. `const` cannot be reassigned; `let`
can. Prefer `const` — it signals "this binding never changes".

**Project usage:** almost everything is `const`. There is exactly one meaningful
`let` in the whole codebase, [api.js:7](../frontend/src/api.js#L7):

```js
let token = localStorage.getItem("diq_token") || null;
```

**What it does here:** holds the JWT for the lifetime of the page. It is `let`
because `setToken()` reassigns it on login and logout — the *only* variable in
your frontend that genuinely needs reassignment.

⚠️ **The classic trick question:** *"`const` means immutable, right?"* **No.**
`const` prevents **reassignment of the binding**, not mutation of the contents:

```js
const arr = [1, 2];
arr.push(3);      // ✅ allowed — the array is mutated, the binding is unchanged
arr = [4];        // ❌ TypeError — reassignment
```

This matters in React. In [App.jsx:308](../frontend/src/App.jsx#L308) you write
`const counts = orders.reduce(...)` — and you deliberately build a *new* object
rather than mutating, because React detects changes by comparing references
(§4.5).

> **Interview answer:** *"I default to `const`. The only `let` is the token in
> `api.js`, because it's genuinely reassigned on login and logout. And `const`
> isn't immutability — it stops reassignment, not mutation."*

---

## 2.2 Arrow functions 🔴 MUST KNOW

**Simple meaning:** shorter syntax for writing a function.

```js
function add(a, b) { return a + b; }   // traditional
const add = (a, b) => a + b;           // arrow — implicit return
```

If the body is a single expression, you can drop `{}` and `return`.

**Project usage:** 49 occurrences across 42 lines. Every event handler and every `.map()`
callback. From [api.js:51-56](../frontend/src/api.js#L51-L56):

```js
export const api = {
  ready: () => request("/ready"),
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: { email, password } }),
  me: () => request("/auth/me"),
```

**What it does here:** each is a one-line function returning the result of
`request(...)`. `ready` takes no parameters — hence the empty `()`.

**A pattern to understand** — [App.jsx:143](../frontend/src/App.jsx#L143):

```jsx
onClick={() => switchTo(d)}
```

🔴 Why not `onClick={switchTo(d)}`? Because that would **call** `switchTo(d)`
immediately during render and hand React the return value. Wrapping it in an
arrow gives React a function to call **later**, when the click happens. This is a
very common interview question.

> **Interview answer:** *"Arrow functions are the concise form and I use them for
> every handler and array callback. In JSX I write `onClick={() => advance(o.id,
> next)}` rather than `onClick={advance(o.id, next)}` — the second would run
> during render instead of on click. The arrow defers the call and lets me pass
> arguments."*

---

## 2.3 Objects, arrays and destructuring 🔴 MUST KNOW

**Objects** are key-value collections. Your order request body,
[App.jsx:250-258](../frontend/src/App.jsx#L250-L258):

```js
const body = {
  customer_id: Math.floor(Math.random() * 100) + 1,
  restaurant_id: Math.floor(Math.random() * 20) + 1,
  value: Math.floor(Math.random() * 900) + 100,
  pickup_lat: 28.61,
  pickup_lon: 77.2,
  drop_lat: 28.65,
  drop_lon: 77.25,
};
```

This object is sent as the JSON body of `POST /orders`, and its shape must match
the backend's `OrderCreate` Pydantic schema exactly — it does.

**Destructuring** pulls values out into named variables:

```js
// App.jsx:98 — object destructuring
const { data } = await api.login(email, password);
```

`request()` returns `{ data, replayed }`. This extracts just `data`. Equivalent
to `const data = result.data;` but shorter.

```js
// App.jsx:202 — array destructuring
const [o, r] = await Promise.all([api.listOrders(), api.listRiders()]);
```

`Promise.all` returns an array of two results; this names them `o` and `r` by
**position**.

```jsx
// App.jsx:89 — destructuring in the parameter list
function Auth({ user, onUser, say }) {
```

React passes one `props` object. This unpacks the three fields immediately, so
you write `user` instead of `props.user`. 🔴 This is *the* standard React idiom
and you should recognise it instantly.

```jsx
// App.jsx:33 — destructuring in a map callback
Object.entries(checks).map(([dep, state]) => ( ... ))
```

`Object.entries({postgres: "ok"})` gives `[["postgres", "ok"]]` — an array of
`[key, value]` pairs. `([dep, state])` destructures each pair.

> **Interview answer:** *"Destructuring pulls fields out by name or position. I
> use it in three places: unpacking `{ data }` from my API wrapper, naming the
> two results of a `Promise.all`, and unpacking props in a component signature —
> `function Auth({ user, onUser, say })`."*

---

## 2.4 The spread operator `...` 🔴 MUST KNOW

**Simple meaning:** "unpack everything from this array/object into here". It
**copies**.

Three real uses, all important.

**1. Copy before mutating** — [App.jsx:382](../frontend/src/App.jsx#L382):

```jsx
{[...orders].reverse().map((o) => ( ... ))}
```

🔴 This is a genuinely good piece of code — be ready to explain it.
`.reverse()` **mutates the array it's called on**. Calling `orders.reverse()`
directly would mutate React state in place. `[...orders]` makes a copy first, so
the reverse happens on the copy and your state object is never touched.

**2. Prepend to a list immutably** — [App.jsx:195-197](../frontend/src/App.jsx#L195-L197):

```js
setLog((l) =>
  [{ msg, kind, at: new Date().toLocaleTimeString() }, ...l].slice(0, 14),
);
```

Builds a **brand new array**: the new entry first, then all previous entries
spread after it, then `.slice(0, 14)` keeps only the newest 14. The old array is
never modified.

**3. Object spread in a reducer** — [App.jsx:308-311](../frontend/src/App.jsx#L308-L311):

```js
const counts = orders.reduce(
  (a, o) => ({ ...a, [o.status]: (a[o.status] || 0) + 1 }),
  {},
);
```

Copies the accumulator and adds/increments one key.

⚠️ Honest note: this allocates a new object per order, which is O(n²) overall.
At demo scale it is irrelevant, but a sharp interviewer may spot it. The
straightforward fix is to mutate the accumulator (safe — it is local, not state):
`(a, o) => { a[o.status] = (a[o.status] || 0) + 1; return a; }`.

> **Interview answer:** *"Spread is how I keep state updates immutable. The
> clearest case is `[...orders].reverse()` — `reverse` mutates in place, so
> copying first prevents me from mutating React state. Same idea in my logger:
> I build a new array with the new entry prepended rather than pushing into the
> existing one."*

---

## 2.5 `map()` 🔴 MUST KNOW — the single most important array method in React

**Simple meaning:** transform every item of an array into something else, and
get back a new array of the same length.

```js
[1, 2, 3].map(n => n * 2)   // → [2, 4, 6]
```

**Why React cares:** JSX can render an **array of elements**. So `map()` is how
you turn data into UI. You use it 8 times.

**Project usage — the orders list**, [App.jsx:382-399](../frontend/src/App.jsx#L382-L399):

```jsx
{[...orders].reverse().map((o) => (
  <div key={o.id} className="row">
    <span className="id">#{o.id}</span>
    <span className={`badge s-${o.status}`}>{o.status}</span>
    <span className="val">₹{o.value}</span>
    {o.rider_id && <span className="rid">rider {o.rider_id}</span>}
    <span className="grow" />
    {(STATUS_FLOW[o.status] || []).map((next) => (
      <button key={next} className="tiny" onClick={() => advance(o.id, next)}>
        {next}
      </button>
    ))}
  </div>
))}
```

**What it does here, step by step:**

1. `[...orders]` copies the array (so `.reverse()` doesn't mutate state).
2. `.reverse()` puts newest orders first.
3. `.map((o) => ...)` turns each order **object** into a `<div className="row">`
   **element**.
4. `key={o.id}` gives React a stable identity for each row (§4.7).
5. **A nested `map()`**: `STATUS_FLOW[o.status]` looks up which transitions are
   offered from this order's current status, and maps each into a button.
   `|| []` guards against an unknown status.

So an order in state `ASSIGNED` renders two buttons (`PICKED_UP`, `CANCELLED`)
because of [App.jsx:8-14](../frontend/src/App.jsx#L8-L14):

```js
const STATUS_FLOW = {
  PENDING: [],
  ASSIGNED: ["PICKED_UP", "CANCELLED"],
  PICKED_UP: ["DELIVERED"],
  DELIVERED: [],
  CANCELLED: [],
};
```

A `DELIVERED` order maps an empty array → **zero buttons**. The UI is a direct
projection of a data structure. That is a genuinely good design point to raise.

**Your other `map()` calls:**

| Location | Array | Produces |
|---|---|---|
| [App.jsx:33](../frontend/src/App.jsx#L33) | `Object.entries(checks)` | one health pill per dependency |
| [App.jsx:80](../frontend/src/App.jsx#L80) | `Object.entries(stats.riders_by_status)` | rider counts by status |
| [App.jsx:138](../frontend/src/App.jsx#L138), [176](../frontend/src/App.jsx#L176) | `DEMO_LOGINS` | the ops/rider/customer chips |
| [App.jsx:330](../frontend/src/App.jsx#L330) | a literal status array | the four counter tiles |
| [App.jsx:389](../frontend/src/App.jsx#L389) | `STATUS_FLOW[o.status]` | per-order action buttons |
| [App.jsx:407](../frontend/src/App.jsx#L407) | `log` | activity log lines |

> **Interview answer:** *"`map()` is how data becomes UI in React — JSX renders an
> array of elements, so mapping an array of objects to an array of JSX nodes is
> the standard list-rendering pattern. In my orders panel I map orders to rows,
> and inside each row I map `STATUS_FLOW[order.status]` to action buttons — so the
> available transitions are driven by a lookup table rather than conditionals."*

---

## 2.6 `filter()`, `reduce()` and `slice()` 🟡 SHOULD KNOW

**`filter()`** — keep only items matching a test; returns a shorter array.
[App.jsx:312](../frontend/src/App.jsx#L312):

```js
const free = riders.filter((r) => r.status === "AVAILABLE").length;
```

Keeps available riders, then takes the count. This feeds the "RIDERS FREE" tile.

**`reduce()`** — collapse an array into a single value.
[App.jsx:308-311](../frontend/src/App.jsx#L308-L311):

```js
const counts = orders.reduce(
  (a, o) => ({ ...a, [o.status]: (a[o.status] || 0) + 1 }),
  {},          // ← initial value: an empty object
);
```

`a` is the **accumulator** (the running result), `o` is the current order. For
each order it copies the accumulator and increments that status's counter.
Result: `{ PENDING: 3, ASSIGNED: 2, DELIVERED: 5 }`. Rendered at
[App.jsx:330-335](../frontend/src/App.jsx#L330-L335) as `{counts[s] || 0}` — the
`|| 0` handles statuses with no orders, which would otherwise render `undefined`.

Note `[o.status]` in square brackets — that is a **computed property name**: use
the *value* of `o.status` as the key.

**`slice()`** — take a portion; does **not** mutate.
[App.jsx:196](../frontend/src/App.jsx#L196): `.slice(0, 14)` caps the activity
log at 14 entries so it can't grow forever.

🔴 **Know the distinction:** `slice()` returns a copy; `splice()` mutates. You
correctly use `slice`.

**Not used anywhere in your project:** `find()`, `forEach()`, `some()`, `every()`,
`sort()`. Don't claim them.

> **Interview answer:** *"`filter` narrows an array — I use it to count available
> riders. `reduce` collapses one to a single value — I use it to build a
> status→count object for the header tiles. And `slice(0, 14)` caps the activity
> log, which matters because it's an unbounded append-on-every-action list."*

---

## 2.7 Template literals 🔴 MUST KNOW

**Simple meaning:** strings in backticks that can embed expressions with `${}`.

```js
`Bearer ${token}`                    // api.js:21
`order ${id} → ${status}`            // App.jsx:296
`Rider-${Math.floor(Math.random() * 900 + 100)}`   // App.jsx:234
`${e.message} — run: python -m scripts.seed_users` // App.jsx:121
`/orders/${id}/status`               // api.js:63 — building a URL
`badge s-${o.status}`                // App.jsx:385 — building a CSS class
```

They also span multiple lines without `\n`. The two most *interesting* uses in
your code are building a **URL path** and building a **CSS class name** — both
turn data into a string that something else consumes.

> **Interview answer:** *"Template literals with `${}` interpolation. I use them
> for the `Bearer` auth header, for path parameters like
> `` `/orders/${id}/status` ``, and to compose conditional CSS class names from
> state."*

---

## 2.8 Optional chaining `?.` and nullish coalescing `??` 🔴 MUST KNOW

**The problem they solve:** reading a property of `null` or `undefined` throws
`TypeError: Cannot read properties of null`. In a UI where data arrives
asynchronously, values are *routinely* null before the first response lands.

**`?.` — optional chaining.** "If the left side is null/undefined, stop and give
`undefined` instead of throwing."

```jsx
const isOps = user?.role === "ops";        // App.jsx:306
{user?.role === "ops" && <Stats say={say} />}   // App.jsx:327
```

🔴 This is essential: `user` starts as `null` ([App.jsx:188](../frontend/src/App.jsx#L188))
and stays null until login. `user.role` would crash on the very first render.
`user?.role` yields `undefined`, the comparison is `false`, and nothing renders.

```js
data?.message || data?.detail || data?.error   // api.js:41
```

`data` can be `null` when a response has no body — this reads three possible
error shapes without crashing.

**`??` — nullish coalescing.** "Use the left value unless it is `null` or
`undefined`, in which case use the right."

```js
.catch((e) => setChecks(e.data?.checks ?? { api: "unreachable" }));   // App.jsx:24
```

If the API returns a 503 with a `checks` breakdown, use it. If the API is
completely unreachable there is no response body at all, so fall back to
`{ api: "unreachable" }` — which is why your health pills show a red "api" dot
when the backend is down instead of blanking out.

⚠️ **Trick question:** *"What's the difference between `??` and `||`?"*
`||` treats **any falsy** value as absent — `0`, `""`, `false` all trigger the
fallback. `??` only triggers on `null`/`undefined`. For a count of `0` that
distinction is the difference between showing `0` and showing your fallback.

> **Interview answer:** *"Optional chaining stops null-property crashes, which
> matters because my `user` state starts as `null` and only fills in after login —
> `user?.role === "ops"` is safe on the first render, `user.role` would throw.
> `??` differs from `||` in that it only falls back on null or undefined, not on
> falsy values like `0`."*

---

## 2.9 Conditionals: `if`, ternary, and `&&` 🔴 MUST KNOW

**`if/else`** — used in your regular functions:

```js
// App.jsx:97 — only register when the button was "Register"
if (kind === "register") await api.register(email, password);

// api.js:20-23 — conditionally add headers
if (body) headers["Content-Type"] = "application/json";
if (token) headers["Authorization"] = `Bearer ${token}`;
if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
```

Those three lines are a nice detail: each header is added **only if needed**, so
a GET carries no `Content-Type` and an anonymous request carries no
`Authorization`.

**Ternary** `condition ? a : b` — a conditional **expression**, so it can go
inside JSX where `if` cannot:

```jsx
{checks ? ( ...pills... ) : ( <span className="pill">checking…</span> )}  // App.jsx:32
className={`pill ${state === "ok" ? "up" : "down"}`}                       // App.jsx:34
title={isOps ? "" : "ops only — dispatch assigns work to a courier"}       // App.jsx:363
say(replayed ? "REPLAYED — ..." : "order created", replayed ? "warn" : "ok"); // App.jsx:265-268
```

**`&&` short-circuit** — `a && b` returns `b` only if `a` is truthy, otherwise
`a`. React renders nothing for `false`, `null` and `undefined`, so this is the
"render only if" idiom:

```jsx
{user?.role === "ops" && <Stats say={say} />}          // App.jsx:327
{orders.length === 0 && <p className="empty">No orders yet.</p>}  // App.jsx:381
{user.rider_id && <span className="rid">rider #{user.rider_id}</span>}  // App.jsx:134
{!isOps && (<span className="perm-note">...</span>)}   // App.jsx:367
```

⚠️ **Classic trap, worth knowing:** `{orders.length && <p>...</p>}` — if the
length is `0`, React renders the literal **`0`** on screen, because `0` is a
value, not `false`. Your code correctly writes `orders.length === 0 &&`, which
yields a real boolean. If asked about `&&` pitfalls, this is the answer.

> **Interview answer:** *"Inside JSX I can only use expressions, so conditionals
> are ternaries or `&&`. `&&` is my 'render only if' — the ops stats bar is
> `{user?.role === "ops" && <Stats/>}`. The trap is short-circuiting on a number:
> `{items.length && ...}` renders a literal `0`. I compare explicitly instead."*

---

## 2.10 `async`, `await`, Promises and `try/catch` 🔴 MUST KNOW

### The problem

A network request takes time — maybe 50 ms, maybe 3 seconds. JavaScript runs on
**one thread**. If it simply waited, the entire page would freeze: no clicking,
no scrolling, no rendering.

### Promise 🔴

**WHAT IS IT?** A **Promise** is an object representing a value that isn't ready
yet. It ends up either **fulfilled** (here's the value) or **rejected** (here's
the error). `fetch()` returns a Promise immediately, before any response arrives.

You use Promises in two styles.

**`.then()` / `.catch()` style** — inside your effects,
[App.jsx:20-24](../frontend/src/App.jsx#L20-L24):

```js
const poll = () =>
  api
    .ready()
    .then((r) => setChecks(r.data.checks))
    .catch((e) => setChecks(e.data?.checks ?? { api: "unreachable" }));
```

Read as: "call `/ready`; **when** it resolves, run this; **if** it rejects, run
that."

**`async`/`await` style** — in your handlers. Same thing, written to *look*
sequential.

### `async` / `await` 🔴

- **`async`** before a function means: this function returns a Promise, and
  `await` may be used inside it.
- **`await`** means: pause *this function* until the Promise settles, then
  continue with its value. Crucially, it **does not block the browser** — the
  rest of the page keeps running, other timers keep firing.

### Line-by-line: your login handler ([App.jsx:94-108](../frontend/src/App.jsx#L94-L108))

```js
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
```

| Line | What happens |
|---|---|
| `async function go(kind)` | Marks the function as asynchronous so `await` is allowed |
| `setBusy(true)` | State change → re-render → auth buttons become `disabled`. **This runs before any waiting**, so the user can't double-submit |
| `try {` | Anything that throws below jumps to `catch` |
| `if (kind === "register") await ...` | Register first only when the Register button was clicked; then fall through and log in |
| `const { data } = await api.login(...)` | **Pauses here** until the server responds. Destructures `data` out of `{ data, replayed }` |
| `setToken(data.access_token)` | Stores the JWT in the module variable **and** `localStorage` |
| `const me = await api.me()` | Second request — **this one carries the token**, because `setToken` already ran |
| `onUser(me.data)` | Calls the parent's `setUser`. This is a **child updating parent state** |
| `say(...)` | Appends a green line to the activity log |
| `catch (e)` | Any failure — bad credentials (401), network down — lands here |
| `say(e.message, "err")` | `e.message` is the readable message `request()` extracted from the response body |
| `finally { setBusy(false) }` | 🔴 **Runs on both success and failure.** Without `finally`, a failed login would leave the buttons permanently disabled |

🔴 **The `finally` block is the single most interview-worthy line here.** You use
this pattern in all four action handlers.

### `Promise.all` — parallel requests 🟡

[App.jsx:202](../frontend/src/App.jsx#L202):

```js
const [o, r] = await Promise.all([api.listOrders(), api.listRiders()]);
```

Both requests are **started immediately**, then awaited together. If each takes
100 ms, this takes ~100 ms total, not 200 ms. Sequential `await`s would be:

```js
const o = await api.listOrders();   // wait 100ms
const r = await api.listRiders();   // wait another 100ms
```

⚠️ **Know the caveat:** `Promise.all` rejects as soon as *any* promise rejects.
So if `/riders` fails, you lose the `/orders` result too. `Promise.allSettled`
would give you both outcomes independently. In your code both come from the same
API, so they usually fail together — but say it as a conscious trade-off, and
note that the whole thing is wrapped in a `catch` that deliberately does nothing:

```js
} catch {
  /* transient poll failure — the health pills already show it */
}
```

That `catch` with no parameter is valid modern JavaScript (**optional catch
binding**) — used when you don't need the error object.

> **Interview answer:** *"`fetch` returns a Promise, and `await` lets me write
> asynchronous code that reads top-to-bottom while the browser stays responsive.
> Every handler follows the same shape: set `busy`, `try` the calls, `catch` and
> log the error, and reset `busy` in `finally` — so a failure can't leave the UI
> stuck disabled. In the polling refresh I use `Promise.all` to fetch orders and
> riders in parallel rather than one after the other."*

---

## 2.11 JSON 🔴 MUST KNOW

**WHAT IS IT?** JSON (JavaScript Object Notation) is a **text format** for
structured data. It is how your browser and your Python backend exchange
information despite being different languages.

A JavaScript object is **not** JSON — JSON is the string representation.

**Converting out** — [api.js:28](../frontend/src/api.js#L28):

```js
body: body ? JSON.stringify(body) : undefined,
```

`JSON.stringify()` turns your object into a string for the wire:

```js
{ email: "ops@deliveriq.io", password: "opspassword123" }
// becomes the text:
'{"email":"ops@deliveriq.io","password":"opspassword123"}'
```

**Converting in** — [api.js:31-37](../frontend/src/api.js#L31-L37):

```js
const text = await res.text();
let data = null;
try {
  data = text ? JSON.parse(text) : null;
} catch {
  data = { raw: text };
}
```

🔴 This is careful code — explain it as such:

1. Read the response as **plain text first**, not `res.json()`.
2. `text ? ... : null` — an empty body (e.g. a 204) parses to `null` rather than
   throwing.
3. `JSON.parse` inside a `try` — if the server returns HTML (a proxy error page,
   a 502 from a load balancer), parsing fails and you store `{ raw: text }`
   instead of crashing the app.

**Why not `res.json()`?** Because `res.json()` throws on non-JSON, and you would
lose the body entirely. Your approach never loses information.

> **Interview answer:** *"JSON is the text format on the wire — `JSON.stringify`
> on the way out, `JSON.parse` on the way in. I deliberately read the response as
> text and parse it inside a try/catch rather than calling `res.json()`, because
> a proxy returning an HTML error page would otherwise throw and I'd lose the
> response body. If parsing fails I keep the raw text so the error is still
> visible."*

---

## 2.12 Modules: `import` and `export` 🔴 MUST KNOW

**WHAT IS IT?** Each file is a **module** with its own scope. Nothing is shared
unless explicitly exported and imported.

**Named exports** — [api.js](../frontend/src/api.js):

```js
export function setToken(t) { ... }
export function getToken() { ... }
export const api = { ... };
```

**Named imports** — [App.jsx:2](../frontend/src/App.jsx#L2):

```jsx
import { api, getToken, setToken } from "./api";
```

The braces `{ }` mean "named imports" and the names must match exactly.

**Default export** — [App.jsx:187](../frontend/src/App.jsx#L187):

```jsx
export default function App() { ... }
```

One per file, imported **without** braces and can be renamed
([main.jsx:3](../frontend/src/main.jsx#L3)):

```jsx
import App from "./App.jsx";
```

**Importing from a package** — [App.jsx:1](../frontend/src/App.jsx#L1):

```jsx
import { useCallback, useEffect, useState } from "react";
```

No `./` means "look in `node_modules`". A leading `./` means a local file.

🔴 **A subtle and important point about `api.js`:** the module-level
`let token` is **module state**. The module is evaluated once, so every file
importing from `api.js` shares that same variable. That is why `setToken()`
called inside `Auth` affects the `request()` calls made by `App` — no props, no
context, no store. It's a module-scoped singleton.

> **Interview answer:** *"ES modules. `api.js` uses named exports for `api`,
> `setToken` and `getToken`; `App.jsx` has a default export. One thing worth
> noting is that the token lives as a module-level variable in `api.js` — modules
> are evaluated once, so it's effectively a singleton shared by every importer,
> which is why `request()` always sees the current token without it being passed
> around."*

---

## 2.13 Quick reference: JavaScript features NOT in your project ⚪

Say "I haven't needed that here" rather than bluffing:

`class` / OOP · `this` · prototypes · generators · `Symbol` · `Proxy` ·
`WeakMap` · regular expressions · `setTimeout` (you use `setInterval` only) ·
`localStorage` events · Web Workers · `structuredClone` · labelled loops ·
`switch` statements · `for` / `while` loops (**you use zero explicit loops —
everything is array methods**) · `sort()` · `find()` · `forEach()` ·
`Array.from()` · getters/setters · `Object.freeze`.

🔴 The "zero explicit loops" point is worth making out loud — it signals you
understand that declarative array transformation is the idiom in React code.

---

# Part 3 — React From Zero Using My Project

## 3.1 What is React? 🔴 MUST KNOW

**WHAT IS IT?** React is a **JavaScript library for building user interfaces**.
Not a framework — it does one thing: turn data into UI and keep them in sync.

Four words define it. Learn all four with your own examples:

**1. Component-based.** The UI is built from independent, reusable functions
that return a description of some UI. You have four: `App`, `Auth`, `Health`,
`Stats`.

**2. Declarative.** You describe *what the UI should look like for a given
state*, not the steps to get there. You never wrote "find the count element and
change its text" — you wrote `{orders.length}` and React handles the rest.

**3. State-driven.** The UI is a function of state. Change the state, the UI
follows. `setUser(...)` runs, and the ops buttons enable themselves.

**4. Virtual DOM.** React builds the new UI tree in memory, compares it against
the previous one, and applies only the minimal real-DOM changes.

> **Interview answer:** *"React is a UI library built on components — functions
> that take data and return a description of the interface. It's declarative and
> state-driven: I don't write DOM instructions, I write what the UI should look
> like for a given state, call a setter when the state changes, and React diffs
> the new tree against the old one and patches only what actually changed."*

---

## 3.2 How my application starts — the actual boot sequence 🔴 MUST KNOW

```
Browser requests  /
        ↓
FastAPI serves  frontend/dist/index.html          (app/main.py:136)
        ↓
index.html has  <div id="root">  and a <script> tag
        ↓
main.jsx runs                                     (frontend/src/main.jsx)
   createRoot(document.getElementById("root"))
        ↓
   .render(<StrictMode><App /></StrictMode>)
        ↓
App() runs                                        (App.jsx:187)
   ├─ 5 useState calls  → user, orders, riders, log, busy
   ├─ 2 useCallback     → say, refresh
   ├─ 2 useEffect       → session restore, 4s polling
   └─ returns JSX describing the whole page
        ↓
React converts that description into real DOM nodes inside #root
        ↓
Effects run AFTER the DOM is painted
   ├─ App effect 1   → GET /auth/me   (only if a token exists)
   ├─ App effect 2   → GET /orders + GET /riders, then every 4s
   ├─ Health effect  → GET /ready,    then every 5s
   └─ Stats effect   → GET /admin/stats, every 6s (only if mounted, i.e. ops)
        ↓
Responses arrive → setState → React re-renders → DOM patched
```

### The entry point, line by line ([main.jsx](../frontend/src/main.jsx))

```jsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

| Piece | Meaning |
|---|---|
| `react` vs `react-dom/client` | 🔴 **Two packages.** `react` is the component/hooks engine and is platform-agnostic. `react-dom` renders to a *browser*. This split is why React Native can exist |
| `createRoot(el)` | The React 18+ API. Creates a root attached to a real DOM element |
| `document.getElementById("root")` | The only direct DOM access in your project |
| `.render(...)` | Renders your tree into that element |
| `<App />` | JSX for "render the App component". Capital `A` is required — see §3.3 |
| `<StrictMode>` | 🔴 See below |

### `StrictMode` 🔴 — very likely follow-up

**WHAT IS IT?** A development-only wrapper. It renders nothing visible. In
development it deliberately **double-invokes** components and **mounts, unmounts,
and remounts** each component once, to surface bugs.

**WHY IT MATTERS TO YOU SPECIFICALLY:** you have three `setInterval` timers. In
StrictMode, each effect runs → cleanup runs → effect runs again. Without a
cleanup function you would end up with **two intervals per component**, polling
at double rate, forever. Your code is correct:

```js
useEffect(() => {
  poll();
  const id = setInterval(poll, 5000);
  return () => clearInterval(id);     // ← this is what makes StrictMode safe
}, []);
```

⚠️ Two things to be precise about: StrictMode is **development-only** (it is a
no-op in the production build), and the double-invocation is intentional, not a
bug.

> **Interview answer:** *"StrictMode is a dev-only check that deliberately mounts
> and remounts components to expose effects that don't clean up after themselves.
> It's directly relevant in my app because I run three polling intervals — without
> the `clearInterval` in the effect cleanup, StrictMode would leave a second timer
> running and I'd poll at double rate. It's a no-op in production builds."*

---

## 3.3 JSX in depth 🔴 MUST KNOW

**WHAT IS IT?** JSX is syntax that lets you write HTML-like markup inside
JavaScript. It is **not** valid JavaScript on its own — a compiler (here,
`@vitejs/plugin-react`, which uses Oxc) converts it.

```jsx
<span className="count">{orders.length}</span>
```
becomes roughly:
```js
React.createElement("span", { className: "count" }, orders.length)
```

That is why `.jsx` files need a build step, and why your project has Vite.

### The rules that will trip you up 🔴

| Rule | Why | Your code |
|---|---|---|
| `className`, not `class` | `class` is a reserved JS keyword | 49 occurrences |
| camelCase events | `onclick` → `onClick` | `onClick`, `onChange` |
| Self-close every tag | `<br>` is invalid JSX; `<br />` is required | `<span className="grow" />`, `<i />`, `<br />` at [App.jsx:415](../frontend/src/App.jsx#L415) |
| One root element | A component returns one node | see Fragments below |
| `{}` embeds expressions | Statements (`if`, `for`) are not allowed | ternaries and `&&` instead |
| Capitalised components | lowercase = HTML tag, Capital = your component | `<Health />` vs `<div>` |

🔴 **The capitalisation rule is a real interview question.** `<health />` would
be compiled as a literal HTML tag named `health` and render nothing useful.
`<Health />` is compiled as a reference to your `Health` function.

### Fragments 🟡

A component must return a single node. When you don't want a wrapper `<div>`,
use an empty tag — a **Fragment**. [App.jsx:130](../frontend/src/App.jsx#L130):

```jsx
{user ? (
  <>
    <span className="who">...</span>
    <span className="grow" />
    <button className="ghost" onClick={signOut}>Sign out</button>
  </>
) : (
  <> ... </>
)}
```

`<>...</>` groups children **without adding a DOM element**. Here it matters:
`.auth-bar` is a Flexbox container, and an extra wrapper `<div>` would become a
single flex child, collapsing the whole layout.

> **Interview answer:** *"A Fragment groups elements without emitting a wrapper
> node. In my auth bar it's structural — the parent is a flex container, so an
> extra div would make everything inside it one flex item and break the layout."*

### Five real JSX examples from your code, explained

**1. Expression embedding + nesting** — [App.jsx:336-342](../frontend/src/App.jsx#L336-L342)
```jsx
<div className="stat">
  <span className="n">{free}<small>/{riders.length}</small></span>
  <span className="l">RIDERS FREE</span>
</div>
```
Two JS expressions inside markup. Renders `3/7`. `<small>` is a real HTML tag
nested inside a `<span>` alongside an expression.

**2. Computed className from data** — [App.jsx:385](../frontend/src/App.jsx#L385)
```jsx
<span className={`badge s-${o.status}`}>{o.status}</span>
```
The attribute value is a template literal in braces. `o.status === "DELIVERED"`
produces `class="badge s-DELIVERED"`, which your CSS colours green. The same
value is also the visible text.

**3. Conditional with a ternary** — [App.jsx:32-40](../frontend/src/App.jsx#L32-L40)
```jsx
{checks ? (
  Object.entries(checks).map(([dep, state]) => (
    <span key={dep} className={`pill ${state === "ok" ? "up" : "down"}`}>
      <i /> {dep}
    </span>
  ))
) : (
  <span className="pill">checking…</span>
)}
```
Two ternaries. The outer picks list-vs-placeholder; the inner picks the pill
colour. `<i />` is a self-closed empty element styled by CSS into a coloured dot.

**4. Conditional rendering with `&&` plus a component** — [App.jsx:327](../frontend/src/App.jsx#L327)
```jsx
{user?.role === "ops" && <Stats say={say} />}
```
If the user isn't ops, this evaluates to `false` and React renders nothing.
🔴 Note the real consequence: `Stats` isn't merely hidden — it is **never
mounted**, so its `useEffect` never runs and it **never polls `/admin/stats`**.
Conditional rendering controls behaviour, not just visibility.

**5. Passing a function down + calling it with arguments** — [App.jsx:390-396](../frontend/src/App.jsx#L390-L396)
```jsx
{(STATUS_FLOW[o.status] || []).map((next) => (
  <button key={next} className="tiny" onClick={() => advance(o.id, next)}>
    {next}
  </button>
))}
```
A nested map inside another map, with `key` on the inner element too, and an
arrow wrapper so `advance` runs on click rather than during render — capturing
`o.id` and `next` from the surrounding closure.

---

## 3.4 React Components 🔴 MUST KNOW

**WHAT IS IT?** A component is a **JavaScript function whose name starts with a
capital letter and which returns JSX**. That's the whole definition.

**WHY DO WE NEED THEM?** Three reasons, all visible in your code:
1. **Reuse** — `DEMO_LOGINS.map(...)` renders the same button three times.
2. **Isolation** — `Health` owns its own polling state; nothing else can touch it.
3. **Readability** — `<Auth user={user} onUser={setUser} say={say} />` reads as
   one line instead of 96 lines inline.

You use **function components** exclusively. There are no class components
anywhere. If asked, that is the modern default — class components are legacy.

### Component 1 — `Health` 🔴

```
COMPONENT:  Health                    App.jsx:16-43
PURPOSE:    Live status pills for postgres / redis / kafka
PARENT:     App
CHILDREN:   none (plain elements only)
PROPS:      none
STATE:      checks — null | { postgres: "ok", redis: "ok", kafka: "ok" }
EVENTS:     none — display only
API CALLS:  GET /ready, every 5 seconds
```

```jsx
function Health() {
  const [checks, setChecks] = useState(null);

  useEffect(() => {
    const poll = () =>
      api.ready()
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
```

🔴 **The detail that makes this component good:** the `.catch` branch. Your
backend's `/ready` returns **HTTP 503 with a body** when a dependency is down
([app/main.py:108-111](../app/main.py#L108-L111)):

```json
{"status": "degraded", "checks": {"postgres": "ok", "redis": "error: ConnectionError", "kafka": "ok"}}
```

`request()` throws on any non-2xx, but it attaches the parsed body as `err.data`
— so the catch can still read `e.data.checks` and **render exactly which
dependency failed**. If the whole API is unreachable there is no body at all, so
`?? { api: "unreachable" }` provides a fallback. Three distinct states — healthy,
degraded-with-detail, and totally down — handled in five lines.

> **How to explain it:** *"`Health` is a self-contained polling widget. It hits
> `/ready` every five seconds and renders one pill per dependency. The interesting
> part is that a degraded backend returns 503 *with* a per-dependency breakdown,
> and my HTTP wrapper attaches the response body to the thrown error — so the
> catch branch still renders which dependency is down rather than just showing a
> generic failure. It owns its own state because nothing else in the app needs it."*

### Component 2 — `Stats` 🔴

```
COMPONENT:  Stats                     App.jsx:53-87
PURPOSE:    Ops-only metrics strip (total orders, avg value, riders by status)
PARENT:     App — conditionally rendered at App.jsx:327
CHILDREN:   none
PROPS:      say (function)
STATE:      stats — null | { total_orders, avg_order_value, riders_by_status, ... }
EVENTS:     none
API CALLS:  GET /admin/stats, every 6 seconds
```

Two things to highlight:

**Early return** — [App.jsx:70](../frontend/src/App.jsx#L70):
```jsx
if (!stats) return null;
```
🔴 Returning `null` from a component is legal and means "render nothing". Note it
comes **after** the hooks — hooks must never be behind a conditional (§3.7).

**Defensive rendering** — [App.jsx:78-84](../frontend/src/App.jsx#L78-L84):
```jsx
avg <b>₹{Math.round(stats.avg_order_value || 0)}</b>
{Object.entries(stats.riders_by_status || {}).map(([k, v]) => ( ... ))}
```
`|| 0` and `|| {}` guard against an empty database. Your backend returns
`avg_order_value: 0` when there are no orders
([app/routers/admin.py:37](../app/routers/admin.py#L37)) — without the guard,
`Math.round(undefined)` renders `NaN`, and `Object.entries(undefined)` throws.

### Component 3 — `Auth` 🔴 the most feature-rich

```
COMPONENT:  Auth                      App.jsx:89-185
PURPOSE:    Sign in / register / switch demo role / sign out
PARENT:     App
CHILDREN:   none
PROPS:      user (object|null), onUser (function), say (function)
STATE:      email, password, busy
EVENTS:     onChange ×2, onClick ×4 (sign in, register, role chips, sign out)
API CALLS:  POST /auth/register, POST /auth/login, GET /auth/me
```

`Auth` renders one of two completely different UIs from a single ternary at
[App.jsx:129](../frontend/src/App.jsx#L129):
- **`user` is null** → email + password inputs, Sign in, Register, demo chips
- **`user` exists** → email, role badge, rider id, role switcher, Sign out

> **How to explain it:** *"`Auth` is a controlled-input component that owns the
> form fields locally but pushes the resulting user up to `App` through an
> `onUser` callback prop. It renders two different UIs from one ternary on
> whether `user` is null. The role chips are a demo affordance — they log in as
> seeded ops/rider/customer accounts so the permission differences can be
> demonstrated side by side without three browsers."*

### Component 4 — `App` 🔴 the root

```
COMPONENT:  App                       App.jsx:187-439
PURPOSE:    Root. Owns shared state, all action handlers, and page layout
PARENT:     none (mounted by main.jsx)
CHILDREN:   Health, Auth, Stats
PROPS:      none
STATE:      user, orders, riders, log, busy
EVENTS:     onClick ×4 direct (+ per-order status buttons)
API CALLS:  GET /auth/me, GET /orders, GET /riders, POST /orders,
            POST /riders, POST /orders/dispatch, PATCH /orders/{id}/status
```

⚠️ **Be ready for "isn't `App` doing too much?"** — yes, and you should say so
first. It holds layout, state, four handlers and two derived values in one
439-line file with three other components. At four components that is a
defensible trade-off; the honest answer is in Part 6.

---

## 3.5 Props 🔴 MUST KNOW

**WHAT IS IT?** Props are the **inputs to a component** — data passed from parent
to child. In the parent they look like HTML attributes; in the child they arrive
as a single object.

**Key rule:** props are **read-only**. A child must never modify them. Data flows
**down**. This is "one-way data flow".

```
    App  (owns user, say)
     │  passes down as props
     ▼
    Auth  (receives user, onUser, say — read-only)
     │  calls onUser(newUser)
     ▼
    App's setUser runs → App re-renders → new user flows back down
```

### Example 1 — `user`: data flowing down 🔴

**Parent** ([App.jsx:326](../frontend/src/App.jsx#L326)):
```jsx
<Auth user={user} onUser={setUser} say={say} />
```
**Child** ([App.jsx:89](../frontend/src/App.jsx#L89)):
```jsx
function Auth({ user, onUser, say }) {
```
**Why it's passed:** `Auth` must decide between the login form and the identity
strip. It cannot own `user` itself, because `App` also needs it — for `isOps`, for
mounting `<Stats/>`, and for disabling buttons. So `App` owns it and passes it
down.

### Example 2 — `onUser`: a function flowing down, data flowing up 🔴🔴

This is the most important props concept in your project.

**Parent passes its own state setter:**
```jsx
<Auth user={user} onUser={setUser} say={say} />
```
**Child calls it** ([App.jsx:101](../frontend/src/App.jsx#L101)):
```jsx
const me = await api.me();
onUser(me.data);       // ← this is App's setUser
```

`Auth` cannot assign to `App`'s state — props are read-only. But `App` can hand
down a **function**, and `Auth` can call it. That is how a child "updates the
parent". It's called a **callback prop**, and the `on...` naming convention
signals it.

Note the child never knows it's calling `setUser` — it just knows it received
something called `onUser`. That keeps `Auth` reusable.

> **Interview answer:** *"Props are one-way — parent to child, read-only. To send
> data back up, the parent passes a function down. My `Auth` component receives
> `onUser`, which is `App`'s `setUser`. When the login succeeds, `Auth` calls
> `onUser(user)` and `App`'s state updates, which re-renders the whole tree with
> the new user. That's 'lifting state up': `user` lives in `App` because `App`,
> `Auth` and `Stats` all depend on it."*

### Example 3 — `say`: a shared capability 🟡

**Parent** ([App.jsx:194-198](../frontend/src/App.jsx#L194-L198)):
```jsx
const say = useCallback((msg, kind = "info") => {
  setLog((l) =>
    [{ msg, kind, at: new Date().toLocaleTimeString() }, ...l].slice(0, 14),
  );
}, []);
```
Passed to **both** `Auth` and `Stats`. Any component can write to the shared
activity log without owning it. Note the **default parameter** `kind = "info"`,
so `say("signed out")` works without a second argument.

🔴 It is wrapped in `useCallback` for a specific reason covered in §3.8 — the
`Stats` effect lists `[say]` as a dependency, so `say` must keep a stable
identity or the polling interval would restart on every render.

### Props vs State 🔴 MUST KNOW — near-guaranteed question

| | Props | State |
|---|---|---|
| Comes from | The parent | The component itself |
| Who can change it | Only the parent (by re-rendering) | Only the component, via its setter |
| Mutable by owner? | ❌ read-only | ✅ via `setX` |
| Purpose | Configure/feed a child | Remember something that changes |
| Your example | `user`, `onUser`, `say` | `email`, `password`, `busy`, `checks` |

**The clean illustration from your own code:** in `Auth`, `user` is a **prop**
(owned by `App`, because three places need it) while `email` is **state** (owned
by `Auth`, because nothing else cares what's typed until submit).

> **Interview answer:** *"Props are inputs from the parent and are read-only;
> state is data a component owns and can change. `Auth` shows both — `user` is a
> prop because `App` and `Stats` also depend on it, but the email and password
> fields are local state because nothing outside `Auth` needs them until the
> login succeeds. The rule I applied is: keep state as low as possible, lift it
> only when a second component needs it."*

---

## 3.6 State 🔴 MUST KNOW — the highest-value topic in this guide

### Normal variable vs React state

Imagine writing this instead of `useState`:

```jsx
function App() {
  let orders = [];                 // ❌ broken in two separate ways
  // ... later
  orders = response.data;
  return <span>{orders.length}</span>;
}
```

**Problem 1: React doesn't know.** Assigning to a local variable is invisible to
React. Nothing tells it to re-run the component, so the screen never updates.

**Problem 2: it resets.** A component function runs again on *every* render.
`let orders = []` would re-execute and wipe the value each time.

`useState` fixes both: React **stores the value outside the function** (so it
survives re-renders) and the **setter notifies React** (so the UI updates).

```jsx
const [orders, setOrders] = useState([]);
```

### Every part of that line 🔴

```jsx
const [loading, setLoading] = useState(false);
  │      │          │            │        │
  │      │          │            │        └── initial value, used on first render only
  │      │          │            └── the hook
  │      │          └── setter — calling it schedules a re-render
  │      └── current value for THIS render
  └── array destructuring; the names are yours to choose
```

`useState` returns an array of exactly two items, so `[a, b]` names them by
position. The convention is `x` / `setX`.

🔴 **"Used on first render only"** is a real interview point: `useState(false)`
does not reset to `false` on later renders. React ignores the argument after the
initial mount.

### Every state variable in your project

| Component | State | Initial | Changed by | UI that depends on it |
|---|---|---|---|---|
| `App` | `user` | `null` | session-restore effect; `Auth` via `onUser` | `isOps`, `<Stats/>` mounting, button `disabled`, permission note, `Auth` branch |
| `App` | `orders` | `[]` | `refresh()` every 4 s | orders panel, `counts` tiles, count badge |
| `App` | `riders` | `[]` | `refresh()` every 4 s | "RIDERS FREE" tile |
| `App` | `log` | `[]` | `say()` | activity panel |
| `App` | `busy` | `false` | 3 action handlers | `disabled` on action buttons |
| `Auth` | `email` | `"ops@deliveriq.io"` | `onChange`, `switchTo()` | email input `value` |
| `Auth` | `password` | `"opspassword123"` | `onChange`, `switchTo()` | password input `value` |
| `Auth` | `busy` | `false` | `go()`, `switchTo()` | `disabled` on auth buttons |
| `Health` | `checks` | `null` | 5 s poll | health pills / "checking…" |
| `Stats` | `stats` | `null` | 6 s poll | ops strip; `null` → renders nothing |

### Worked example: `busy` 🔴

```
FILE:            frontend/src/App.jsx
COMPONENT:       App (line 192)
STATE VARIABLE:  busy
INITIAL VALUE:   false
WHAT CHANGES IT: addRider(), addOrder(), dispatch() — set true at entry,
                 false in finally
WHAT DEPENDS:    disabled={busy || !isOps} on + Rider and Dispatch;
                 disabled={busy} on both + Order buttons
```

The full lifecycle:
1. User clicks **Dispatch** → `dispatch()` runs.
2. `setBusy(true)` → re-render → all action buttons get `disabled` → CSS
   `button:disabled { opacity: .4; cursor: not-allowed; }` greys them out.
3. `await api.dispatch()` — the user physically cannot double-dispatch.
4. Success or failure, `finally { setBusy(false) }` → re-render → buttons live again.

⚠️ **Two honest gaps to volunteer** (both in Part 6):
`advance()` has **no** `busy` guard, so order status buttons *can* be
double-clicked; and `busy` is a single flag, so any one action disables all of
them rather than just its own button.

### Three rules of state 🔴

**Rule 1 — never assign directly.**
```js
orders.push(newOrder);   // ❌ React never notices
setOrders([...orders, newOrder]);   // ✅ new array, new reference
```
React decides whether to re-render by comparing the **reference** (`Object.is`).
Mutating in place leaves the reference identical, so React can skip the render.
This is exactly why your logger builds a new array with spread rather than
pushing, and why `[...orders].reverse()` copies first.

**Rule 2 — updates are asynchronous.**
```js
setBusy(true);
console.log(busy);   // still false!
```
`busy` is a `const` **for this render**. The new value appears in the *next*
render. React batches multiple setter calls in one event into a single re-render.

**Rule 3 — use the functional form when the new value depends on the old.**
[App.jsx:195](../frontend/src/App.jsx#L195):
```js
setLog((l) => [{ msg, kind, at: ... }, ...l].slice(0, 14));
```
`l` is guaranteed to be the **latest** value, not the one captured in this
render's closure. If two actions log within the same tick, `setLog(l => ...)`
keeps both; `setLog([entry, ...log])` could drop one.

🔴 This is a *very* common interview question and your code has the correct
answer already written in it.

> **Interview answer:** *"State is data that, when it changes, should redraw the
> UI. A normal variable fails twice — React isn't notified, and it resets on every
> render, because the component function runs again each time. `useState` keeps
> the value outside the function and gives me a setter that schedules a re-render.
> Three rules I actually apply: never mutate, because React compares references;
> setters are asynchronous, so reading the variable straight after gives the old
> value; and when the next value depends on the previous one, use the functional
> form — my activity logger uses `setLog(l => [entry, ...l])` for exactly that."*

---

## 3.7 Hooks 🔴 MUST KNOW

**WHAT IS IT?** Hooks are functions starting with `use` that let a function
component do things only class components could historically do — hold state,
run side effects, access React features.

Your project uses **exactly three**:

| Hook | Calls | Purpose here |
|---|---|---|
| `useState` | 10 | Remember values that drive the UI |
| `useEffect` | 4 | Run side effects — the API polls and session restore |
| `useCallback` | 2 | Keep function identities stable across renders |

**Not used:** `useRef`, `useMemo`, `useContext`, `useReducer`, custom hooks. Say
this plainly — it's a small app and they weren't needed.

### The Rules of Hooks 🔴 — likely question

1. **Only call hooks at the top level.** Never inside `if`, loops, or nested
   functions.
2. **Only call hooks from React components or other hooks.**

**Why?** React tracks hooks **by call order**, not by name. First `useState` call
= slot 0, second = slot 1. If a conditional skipped one call, every later hook
would read the wrong slot and your state would silently swap.

**Your code obeys this**, and `Stats` shows the correct pattern:
```jsx
function Stats({ say }) {
  const [stats, setStats] = useState(null);   // hook first
  useEffect(() => { ... }, [say]);            // hook second
  if (!stats) return null;                    // early return AFTER all hooks
```
The early return comes *after* both hooks. Putting `if (!stats) return null`
first would conditionally skip `useEffect` and break the rule.

🔴 Your linter enforces this — [.oxlintrc.json](../frontend/.oxlintrc.json):
```json
"rules": { "react/rules-of-hooks": "error" }
```
Mentioning that you have this lint rule configured is a strong signal.

---

## 3.8 `useCallback` 🟡 SHOULD KNOW — but be able to justify it

**WHAT IS IT?** `useCallback(fn, deps)` returns the **same function object**
across renders, as long as `deps` haven't changed.

**WHY DO WE NEED IT?** Functions defined inside a component are **recreated on
every render**. A new function is a new object — `fn1 !== fn2` even if the code is
identical. Anything comparing function identity therefore sees a change.

**Where it matters in your project** — this is a genuine bug prevention, not
premature optimisation:

```jsx
const refresh = useCallback(async () => {
  try {
    const [o, r] = await Promise.all([api.listOrders(), api.listRiders()]);
    setOrders(o.data);
    setRiders(r.data);
  } catch { /* transient poll failure */ }
}, []);

useEffect(() => {
  refresh();
  const id = setInterval(refresh, 4000);
  return () => clearInterval(id);
}, [refresh]);          // ← depends on refresh
```

🔴 **Trace what happens without `useCallback`:**

1. `App` renders → `refresh` is created as a new function object.
2. The effect's dependency `[refresh]` differs from last render → React runs
   cleanup (`clearInterval`) and re-runs the effect.
3. The effect calls `refresh()` → response → `setOrders(...)` → **re-render**.
4. Re-render creates *another* new `refresh` → back to step 2.

That is an **infinite render/fetch loop**. `useCallback(..., [])` gives `refresh`
one stable identity for the component's lifetime, so `[refresh]` never changes and
the interval is created exactly once.

The same reasoning applies to `say`: `Stats` lists `[say]` in its effect
dependencies, so an unstable `say` would restart the `/admin/stats` poll on every
render of `App`.

> **Interview answer:** *"Functions are recreated on every render, so they're new
> objects each time. My polling effect depends on `refresh`, so if `refresh` had a
> new identity every render the effect would tear down and restart its interval
> continuously — and since the effect sets state, that's an infinite loop. Wrapping
> `refresh` in `useCallback` with an empty dependency array pins the identity. Same
> for `say`, because the `Stats` effect depends on it. It's not micro-optimisation
> here — it's what makes the dependency array correct."*

⚠️ **Follow-up you should expect:** *"Why not just remove `refresh` from the
dependency array?"* Answer: because that hides the dependency rather than fixing
it — the linter flags it, and if `refresh` ever captured a prop or state value,
the effect would silently use a stale copy. `useCallback` keeps the dependency
honest.

---

## 3.9 `useEffect` in detail 🔴 MUST KNOW — highest-probability deep-dive

**WHAT IS IT?** `useEffect` runs code that is **not** part of rendering — network
requests, timers, subscriptions. Rendering must be pure (same inputs → same JSX,
no side effects), so anything that touches the outside world goes in an effect.

**WHEN DOES IT RUN?** **After** React has rendered and committed changes to the
DOM. Not during.

### The dependency array — the whole API 🔴

```jsx
useEffect(() => { ... });              // no array   → after EVERY render
useEffect(() => { ... }, []);          // empty      → once, on mount
useEffect(() => { ... }, [refresh]);   // with deps  → on mount + when deps change
return () => { ... };                  // cleanup    → before re-run, and on unmount
```

Your project uses `[]` twice and `[dep]` twice. It never omits the array — good,
because that is the classic infinite-loop mistake when the effect sets state.

### Your four effects

| # | Component | Deps | Cleanup | Purpose |
|---|---|---|---|---|
| 1 | `Health` [19-28](../frontend/src/App.jsx#L19-L28) | `[]` | `clearInterval` | poll `/ready` every 5 s |
| 2 | `Stats` [56-68](../frontend/src/App.jsx#L56-L68) | `[say]` | `clearInterval` | poll `/admin/stats` every 6 s |
| 3 | `App` [210-217](../frontend/src/App.jsx#L210-L217) | `[]` | none | restore session from stored JWT |
| 4 | `App` [219-223](../frontend/src/App.jsx#L219-L223) | `[refresh]` | `clearInterval` | poll `/orders` + `/riders` every 4 s |

### Effect 3, line by line — session restore 🔴

```jsx
useEffect(() => {
  if (getToken()) {
    api.me()
      .then((r) => setUser(r.data))
      .catch(() => setToken(null));
  }
}, []);
```

| Step | What happens |
|---|---|
| `[]` | Runs **once**, right after the first render |
| `if (getToken())` | Reads the module variable in `api.js`, which was seeded from `localStorage` at import time. No token → do nothing, stay signed out |
| `api.me()` | `GET /auth/me` with the `Authorization: Bearer` header |
| `.then(setUser)` | Token valid → `user` state fills → re-render → ops controls appear |
| `.catch(() => setToken(null))` | 🔴 Token expired/tampered → server returns **401** → clear the stale token from both the variable and `localStorage` |

**This is why a page refresh keeps you signed in.** It is also the correct
handling of an expired JWT — an interviewer may ask "what happens when the token
expires?", and the answer is "on the next load this effect gets a 401 and clears
it". Be honest about the limit too: this only runs on mount, so a token expiring
*while* the tab is open is not detected until reload.

### The complete flow you must be able to recite 🔴

```
component mounts
   ↓
React renders → returns JSX (orders = [] → "No orders yet.")
   ↓
React commits to the DOM → user sees the empty state
   ↓
useEffect runs
   ↓
refresh() called → Promise.all([GET /orders, GET /riders])
   ↓
   ... browser stays responsive; other timers keep firing ...
   ↓
responses arrive
   ↓
setOrders(o.data) + setRiders(r.data)
   ↓
React schedules a re-render
   ↓
App() runs again — orders.length is now 7
   ↓
React diffs the new tree against the old one
   ↓
DOM patched: count badge + 7 new rows
   ↓
setInterval fires 4 s later → the whole cycle repeats
```

🔴 **The key sentence:** *the first render always shows the empty state, because
effects run after render, not before.* That's why `orders` starts as `[]` and
`checks` starts as `null` — those initial values are what the user sees for the
first few hundred milliseconds.

### Cleanup 🔴

```jsx
const id = setInterval(poll, 5000);
return () => clearInterval(id);
```

**WHAT IS IT?** The function you return from an effect. React calls it **before
re-running the effect** and **when the component unmounts**.

**WHY IT MATTERS HERE:** without it, when `Stats` unmounts — which happens every
time you switch from ops to customer, since `{user?.role === "ops" && <Stats/>}`
stops rendering it — the interval would keep firing forever, calling
`/admin/stats` and `setStats` on a dead component. Switch roles ten times and
you'd have ten orphaned timers. And in StrictMode you'd get doubles from the
start.

> **Interview answer:** *"`useEffect` runs after render for things that aren't
> rendering — in my case three polling intervals and a session restore. The
> dependency array controls re-runs: empty means once on mount, and my polling
> effect lists `[refresh]`, which is why `refresh` is memoised with `useCallback`.
> The returned cleanup function is essential here — it calls `clearInterval`, so
> when `Stats` unmounts on a role switch its timer stops instead of polling a
> component that no longer exists."*

---

## 3.10 Events 🔴 MUST KNOW

**WHAT IS IT?** An event is something that happens in the browser — a click, a
keystroke. An **event handler** is the function you register to respond.

In React you attach handlers as **camelCase props** whose value is a function.
React uses **synthetic events** — a cross-browser wrapper over native events, and
listeners are attached at the root rather than per element.

### Events actually used in your project

Only two. Say exactly this — no `onSubmit`, no `onKeyDown`, no `onFocus`.

| Event | Count | Where |
|---|---|---|
| `onClick` | 10 | every button |
| `onChange` | 2 | email and password inputs |

### `onChange` — [App.jsx:161](../frontend/src/App.jsx#L161)

```jsx
<input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
```

- `e` is the synthetic event object.
- `e.target` is the DOM element that fired it — the `<input>`.
- `e.target.value` is its current text.
- `setEmail(...)` stores it → re-render → `value={email}` shows the new text.

🔴 Note it fires on **every keystroke**, not on blur. Typing "ops" = three
renders. That's normal and cheap.

### `onClick` — three shapes in your code

```jsx
onClick={addRider}                          // App.jsx:347 — no arguments needed
onClick={() => addOrder(false)}             // App.jsx:353 — needs an argument
onClick={() => advance(o.id, next)}         // App.jsx:393 — arguments from the closure
```

🔴 **Why the arrow in the second and third?** `onClick={addOrder(false)}` would
**call** `addOrder(false)` during render and pass its return value to React. The
arrow gives React a function to invoke on click instead.

**The named async handler** — `signOut` in [App.jsx](../frontend/src/App.jsx),
passed as `onClick={signOut}` with no arrow, because it already *is* a function
and takes no arguments:

```jsx
async function signOut() {
  setBusy(true);
  try {
    await api.logout();          // POST /auth/logout → jti onto the denylist
    try {
      await api.me();            // replay the SAME token — should now fail
      say("logged out, but the token still works — is Redis up?", "warn");
    } catch (e) {
      say(e.status === 401 ? "signed out — token revoked, reuse returned 401" : ..., "ok");
    }
  } catch (e) {
    say(`server logout failed (${e.message}) — clearing locally`, "warn");
  } finally {
    setToken(null);              // runs on EVERY path, including failure
    onUser(null);
    setBusy(false);
  }
}
```

🔴 **Three React points live in this one function**, and they are all askable:

1. **`finally` is the whole safety argument.** Whatever happens to the network
   call, the local token is cleared. A user who clicks Sign out must end up
   signed out even if the server is unreachable — so the local clear cannot sit
   in the `try`.
2. **Nested try/catch, deliberately.** The inner one expects to fail: a 401 is
   the *success* signal for the probe. The outer one handles the logout call
   itself failing. Collapsing them would make "revocation worked" and "the
   server is down" indistinguishable.
3. **`onClick={signOut}` vs `onClick={() => signOut()}`.** Both work; the bare
   reference is right here because there are no arguments to close over. The
   arrow is only needed when you must pass something in — `() => advance(o.id,
   next)` a few lines up.

### `preventDefault` ⚠️ — you do NOT use it

**What it is:** browsers have default behaviours — submitting a form reloads the
page, clicking a link navigates. `e.preventDefault()` cancels that.

**Why it isn't in your code:** you have no `<form>` and no in-app links, so
there's no default behaviour to cancel.

🔴 **Answer it like this:** *"I don't use `preventDefault` because I don't have a
`<form>` element — my login is inputs plus button `onClick` handlers, so there's
no native submit to cancel. If I added a `<form onSubmit>` — which I should, so
that Enter submits — the first line of that handler would need to be
`e.preventDefault()` to stop the browser doing a full page reload."*

That answer proves you understand the concept *and* the gap. Much stronger than
"we didn't need it".

### Full event trace: clicking "Dispatch next →"

```
1  User clicks the button
2  React's synthetic event system fires the onClick handler
3  dispatch() runs  (App.jsx:277)
4  setBusy(true)                       → re-render → all action buttons disabled
5  await api.dispatch()                → POST /orders/dispatch, Bearer token attached
6  Backend: require_ops guard          → ops? proceed. otherwise 403
7  Backend: pick_next_order(db)        → SQL priority claim + geohash matching
8  Response 200 { dispatched: { order_id, rider_id } }
9  say(`dispatched order 12 → rider 4`, "ok")   → setLog → green line in Activity
10 refresh()                           → GET /orders + /riders in parallel
11 setOrders / setRiders               → re-render
12 Order 12's badge flips PENDING → ASSIGNED, PENDING count drops, ASSIGNED rises
13 finally setBusy(false)              → buttons re-enabled
```

If step 6 returns 403 instead: `request()` throws → step 9 becomes
`say("Ops privileges required", "err")` → a red line — and no refresh happens.

---

## 3.11 Forms and controlled inputs 🔴 MUST KNOW

⚠️ **Accuracy first:** your project has **no `<form>` element**. It has two
controlled `<input>`s and buttons with `onClick`. Never say "I built a form with
validation" — you didn't. What you *do* have is the controlled-input pattern,
which is the concept interviewers are actually testing.

### Controlled inputs 🔴

**WHAT IS IT?** An input whose displayed value comes from React state, and whose
every change writes back to that state. React state is the **single source of
truth**; the DOM input never holds independent data.

```jsx
const [email, setEmail] = useState("ops@deliveriq.io");
const [password, setPassword] = useState("opspassword123");

<input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" />
```

**The loop:**
```
user types "x"
  → onChange fires with e.target.value = "opsx"
  → setEmail("opsx")
  → re-render
  → <input value="opsx">
  → the DOM input shows "opsx"
```

🔴 **The proof this is genuinely controlled** is your role switcher
([App.jsx:111-112](../frontend/src/App.jsx#L111-L112)):

```js
async function switchTo(demo) {
  setEmail(demo.email);
  setPassword(demo.password);
```

Clicking the "rider" chip **changes what's displayed in the input boxes**,
without touching the DOM. That's only possible because the input renders from
state. With an uncontrolled input you'd need a ref and manual DOM assignment.
This is an excellent concrete example — use it.

### Controlled vs uncontrolled 🔴 — classic question

| | Controlled | Uncontrolled |
|---|---|---|
| Value lives in | React state | The DOM node |
| Read it via | the state variable | a `ref` |
| Needs `onChange`? | yes | no |
| Validate as you type? | easy | awkward |
| Your project | ✅ both inputs | ❌ never used |

> **Interview answer:** *"Both my inputs are controlled — `value` comes from
> state and `onChange` writes back, so state is the single source of truth. The
> clearest benefit in my app is the demo role switcher: clicking a chip calls
> `setEmail` and `setPassword`, and the input boxes update automatically. With
> uncontrolled inputs I'd need refs and manual DOM writes to do the same."*

### The complete login trace 🔴

```
1  Page loads. useState initialises email/password to the seeded ops credentials
2  <input value={email}>          → the box shows "ops@deliveriq.io"
3  User edits it → onChange → setEmail → re-render → box shows the new text
4  User clicks "Sign in" → onClick={() => go("login")}
5  go("login") runs:
     setBusy(true)                → re-render → both auth buttons disabled
     kind !== "register", so registration is skipped
     await api.login(email, password)
        → request("/auth/login", { method: "POST", body: { email, password } })
        → headers: Content-Type: application/json   (no token yet)
        → fetch POST, body: {"email":"...","password":"..."}
6  Backend app/routers/auth.py:57
     looks up the user, bcrypt-verifies the password
     ❌ wrong → 401 {"detail":"Incorrect email or password"}   (one generic
        message for both "no such user" and "wrong password" — deliberately,
        so the endpoint isn't an account-enumeration oracle)
     ✅ right → 200 {"access_token":"eyJ...","token_type":"bearer"}
7  const { data } = await api.login(...)      → destructure
8  setToken(data.access_token)
     → module variable in api.js updated
     → localStorage.setItem("diq_token", ...)
9  const me = await api.me()                  → GET /auth/me, NOW with the Bearer header
10 Backend get_current_user: decodes+verifies the JWT, then LOADS THE USER FROM
   THE DB rather than trusting the token's claims — so a demoted user loses
   access immediately instead of at token expiry
11 Response: { id, email, role, rider_id }
12 onUser(me.data)                            → App's setUser → App re-renders
13 say("signed in as ops@deliveriq.io (ops)", "ok")  → green line in Activity
14 App re-renders with the new user:
     isOps = true                    → "+ Rider" and "Dispatch" enabled
     {user?.role === "ops" && <Stats/>}  → Stats MOUNTS → its effect starts the 6 s poll
     Auth's ternary flips            → identity strip replaces the login inputs
     the permission note disappears
15 finally setBusy(false)                     → buttons re-enabled
```

⚠️ **The honest gap — volunteer it:** because there is no `<form>`, pressing
**Enter** in the password box does nothing. Users expect Enter to submit. The fix
is small:

```jsx
<form onSubmit={(e) => { e.preventDefault(); go("login"); }}>
  ...
  <button type="submit">Sign in</button>
</form>
```

Saying this unprompted demonstrates you know what a form *is* and made a
conscious (if imperfect) call.

### Validation 🔴 — know exactly where it lives

**Frontend validation in your project: essentially none.** No length check, no
email-format check, no required-field check. Clicking Sign in with empty boxes
sends an empty request.

**Backend validation: thorough.** [app/routers/auth.py:18-22](../app/routers/auth.py#L18-L22):
```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=MAX_PASSWORD_BYTES)
```
Pydantic rejects a malformed email or a short password with **422**, and your
`request()` surfaces it — note the guard at [api.js:42](../frontend/src/api.js#L42),
`typeof msg === "string" ? msg : JSON.stringify(msg)`, which exists precisely
because FastAPI's 422 puts an **array** in `detail`, not a string.

> **Interview answer:** *"Validation is on the server — Pydantic enforces email
> format and a minimum password length, and returns 422. I don't duplicate it on
> the client, which costs a round trip for bad input; the upside is one source of
> truth. What matters is the direction: client-side validation is a UX
> convenience, never a security control, because anyone can call the API directly
> with curl. So the server must validate regardless — and it does."*

---

## 3.12 Conditional rendering 🔴 MUST KNOW

**WHAT IS IT?** Showing different UI depending on state. React renders nothing
for `false`, `null` and `undefined`, which makes the patterns short.

### Every conditional in your project

**1. Ternary — two alternatives** ([App.jsx:32-40](../frontend/src/App.jsx#L32-L40)):
```jsx
{checks ? ( ...map pills... ) : ( <span className="pill">checking…</span> )}
```
Loading state. Before the first `/ready` response, `checks` is `null` → shows
"checking…".

**2. Ternary swapping an entire UI** ([App.jsx:129-182](../frontend/src/App.jsx#L129-L182)):
```jsx
{user ? ( <>identity strip</> ) : ( <>login inputs</> )}
```
54 lines of JSX on each branch. This is what replaces routing in your app —
"signed in" and "signed out" are *states*, not URLs.

**3. `&&` — render only if** ([App.jsx:327](../frontend/src/App.jsx#L327)):
```jsx
{user?.role === "ops" && <Stats say={say} />}
```
🔴 Not just visibility — an unmounted `Stats` never runs its effect, so no
`/admin/stats` polling happens for non-ops users. Conditional rendering controls
*behaviour*.

**4. `&&` for empty states** ([App.jsx:381](../frontend/src/App.jsx#L381), [406](../frontend/src/App.jsx#L406)):
```jsx
{orders.length === 0 && <p className="empty">No orders yet.</p>}
{log.length === 0 && <p className="empty">Actions appear here.</p>}
```
Note `=== 0` rather than `!orders.length` — and definitely not
`{orders.length && ...}`, which would render a literal `0`.

**5. Early return** ([App.jsx:70](../frontend/src/App.jsx#L70)):
```jsx
if (!stats) return null;
```
The whole component renders nothing. Placed **after** the hooks.

**6. Conditional attributes** ([App.jsx:348-349](../frontend/src/App.jsx#L348-L349)):
```jsx
disabled={busy || !isOps}
title={isOps ? "" : "ops only — onboarding a courier is an operator action"}
```
Not conditional *rendering* — conditional **props**. The button always renders;
its `disabled` and tooltip depend on state.

🔴 **This is a deliberate design choice worth explaining:**
[App.jsx:303-305](../frontend/src/App.jsx#L303-L305) documents it —
*"Ops-only actions are disabled rather than hidden: a greyed control with a
reason teaches the permission model, whereas a missing button just looks like a
feature that isn't there."*

> **Interview answer:** *"Ternaries when there are two alternatives, `&&` when
> it's show-or-nothing, and an early `return null` when a whole component has
> nothing to show. One thing I'd point out: I disable restricted controls instead
> of hiding them, with a `title` explaining why, so the permission model is
> visible. That's a UX decision — the enforcement is entirely server-side."*

---

## 3.13 List rendering and keys 🔴 MUST KNOW

### The pattern

```
array of data  →  .map()  →  array of JSX elements  →  React renders them
```

### `key` — what it is and why it exists 🔴

**WHAT IS IT?** A special prop giving each element in a list a **stable
identity** across renders.

**WHY DO WE NEED IT?** When your orders array goes from 6 items to 7, React must
work out what changed. Without keys it compares **by position**, so inserting at
the front makes React think every single row changed. With keys it matches by
identity: "these six already exist, one is new" — and only the new row is created.

Consequences of getting it wrong: unnecessary DOM work, and **lost internal
state** — an input's text or scroll position attaching to the wrong row.

### Your keys, audited honestly

| Location | Key | Verdict |
|---|---|---|
| [App.jsx:383](../frontend/src/App.jsx#L383) `orders` | `key={o.id}` | ✅ database primary key — ideal |
| [App.jsx:34](../frontend/src/App.jsx#L34) health pills | `key={dep}` | ✅ unique dependency name |
| [App.jsx:81](../frontend/src/App.jsx#L81) rider stats | `key={k}` | ✅ unique status string |
| [App.jsx:139](../frontend/src/App.jsx#L139),[177](../frontend/src/App.jsx#L177) role chips | `key={d.label}` | ✅ unique label |
| [App.jsx:331](../frontend/src/App.jsx#L331) counter tiles | `key={s}` | ✅ unique status |
| [App.jsx:391](../frontend/src/App.jsx#L391) status buttons | `key={next}` | ✅ unique within the row |
| [App.jsx:408](../frontend/src/App.jsx#L408) activity log | `key={i}` | ⚠️ **index — and the list is prepended** |

🔴 **Own the last one before it's found.** `say()` puts the new entry at the
**front**:

```js
setLog((l) => [{ msg, kind, at }, ...l].slice(0, 14));
```

So every existing entry's index shifts by one. Entry at index 0 becomes index 1,
and React thinks the *content* of every row changed rather than that one row was
inserted. It re-renders all 14 lines instead of 1.

**Why it's not causing a visible bug:** the log rows are pure text with no
internal state, no inputs and no animation — so the worst outcome is a little
wasted DOM work on a 14-item list.

**The fix**, if asked: `key={`${l.at}-${l.msg}`}` (timestamp + message), or
attach an incrementing id when creating the entry.

⚠️ **Also note:** 🔴 keys must be unique **among siblings**, not globally. And a
key is *not* accessible inside the component as a prop — `props.key` is undefined.
Both are common trick questions.

> **Interview answer:** *"Keys give list items a stable identity so React can
> match them across renders instead of comparing by position. My orders list uses
> the database id, which is the right choice. My activity log uses the array
> index, which is the anti-pattern — and it's worse than usual because I prepend,
> so every index shifts on each new entry. It's harmless there because the rows
> are stateless text, but the correct key would be a timestamp-plus-message
> composite, and I'd change it if the rows gained interactive state."*

---

## 3.14 State management architecture 🔴 MUST KNOW

**The whole answer:** local `useState`, lifted to `App` when more than one
component needs it. **No Redux, no Zustand, no Context API, no store of any kind.**

### Where data lives → who updates it → who reads it

| Data | Lives in | Updated by | Read by |
|---|---|---|---|
| `user` | `App` | session effect; `Auth` via `onUser` | `App` (`isOps`, `Stats` mount, buttons), `Auth` |
| `orders` | `App` | `refresh()` 4 s poll | orders panel, `counts` |
| `riders` | `App` | `refresh()` 4 s poll | "RIDERS FREE" tile |
| `log` | `App` | `say()` — from `App`, `Auth`, `Stats` | activity panel |
| `busy` | `App` | 3 handlers | action buttons |
| `email`/`password`/`busy` | `Auth` | `onChange`, `switchTo` | inputs and auth buttons |
| `checks` | `Health` | 5 s poll | health pills |
| `stats` | `Stats` | 6 s poll | ops strip |
| **JWT** | **`api.js` module scope + `localStorage`** | `setToken()` | `request()` on every call |

### The principle you applied 🔴

**Keep state as low as possible; lift it only when a second component needs it.**

- `checks` stays in `Health` — nothing else uses it.
- `email` stays in `Auth` — `App` doesn't care what's being typed.
- `user` is lifted to `App` — because `App` *and* `Auth` *and* the `Stats`
  mounting decision all depend on it.

This is called **lifting state up**, and it is React's built-in answer before
you reach for a library.

### "Why no Redux / Context?" 🔴 — expect this

> *"The tree is two levels deep — `App` and three direct children. Context solves
> prop-drilling, and with three props passed one level down there's nothing to
> drill. Redux adds a store, actions and reducers to coordinate state across
> distant parts of an app; my entire shared state is five `useState` calls in the
> root component. Adding either would be more code, more indirection and more to
> explain, with no problem solved. The point at which I'd reconsider is concrete:
> a second view, or a component that needs `user` three-plus levels down — then
> Context for the auth object first, and a store only if I had genuinely complex
> cross-cutting state."*

That answer is much stronger than "the project was small". It names the trigger
for changing your mind.

### The one piece of state outside React 🟡

```js
let token = localStorage.getItem("diq_token") || null;   // api.js:7
```

The JWT is deliberately **not** React state. `request()` needs it on every call,
and it's read at call time rather than render time — so making it state would
mean threading it into the API layer for no benefit. Modules evaluate once, so
it's effectively a singleton.

⚠️ **The trade-off to acknowledge:** because it's outside React, changing the
token doesn't trigger a re-render. Your code handles this by always pairing
`setToken(...)` with `onUser(...)` / `setUser(...)` — see
[App.jsx:99-101](../frontend/src/App.jsx#L99-L101) and
[150-152](../frontend/src/App.jsx#L150-L152). If someone updated the token
without updating `user`, the UI would show stale identity. Naming that coupling
is a strong answer.

---

# Part 4 — How My React Frontend Talks To The Backend

This is the highest-value section for interviews. Your frontend is essentially a
UI over an HTTP API.

## 4.1 The architecture 🔴 MUST KNOW

**One file, one function, every call.** There is no Axios, no React Query, no
service-per-resource layer — just
[`request()` in api.js](../frontend/src/api.js#L18-L48) plus an `api` object of
thin wrappers.

```
Component handler
   ↓ calls
api.createOrder(body, key)          ← named wrapper, api.js:59
   ↓ calls
request(path, { method, body, idempotencyKey })   ← the one HTTP function
   ↓ calls
fetch()                             ← the browser's built-in HTTP client
   ↓
FastAPI, same origin
   ↓
JSON response
   ↓ back through request(): parse, check status, throw or return
setState(...)
   ↓
React re-renders → DOM updated
```

**Why a wrapper at all?** Without it, every call site would repeat: build
headers, attach the token, stringify the body, parse the response, check
`res.ok`, extract an error message. That's ~15 lines × 10 endpoints. Centralising
it means the token is attached in **one** place — so no endpoint can forget it.

## 4.2 `request()` line by line 🔴

```js
async function request(path, { method = "GET", body, idempotencyKey } = {}) {
```
**Destructured parameters with defaults**, and `= {}` at the end so
`request("/ready")` works with no second argument at all. Without that trailing
default, destructuring `undefined` would throw.

```js
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
```
Each header added only when relevant. 🔴 The `Authorization` line is your entire
auth mechanism on the client — every authenticated request in the app is
authenticated by *this one line*.

```js
  const res = await fetch(BASE + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
```
`BASE` is `""`, so `BASE + path` is just `/orders` — a **relative URL**, i.e.
same origin. `body: undefined` omits the body entirely for GETs (a GET with a
body is invalid).

```js
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; }
  catch { data = { raw: text }; }
```
Defensive parsing — handles empty bodies and non-JSON responses (§2.11).

```js
  if (!res.ok) {
    const msg = data?.message || data?.detail || data?.error || `HTTP ${res.status}`;
    const err = new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return { data, replayed: res.headers.get("Idempotent-Replay") === "true" };
}
```

🔴 **Four things to say about this block:**

1. **`fetch` does not throw on 4xx/5xx.** It only rejects on network failure. A
   404 is a *successful* fetch with `ok === false`. So you must check `res.ok`
   yourself. **This is a classic interview question** and your code answers it.
2. **Three error shapes unified.** Your backend emits `{error, message}` from the
   `DeliverIQError` handler, `{detail}` from FastAPI's `HTTPException`, and
   `{error}` from the rate limiter. The `||` chain flattens all three into one
   readable string.
3. **The error carries `.status` and `.data`.** That's why `Health` can render a
   503's dependency breakdown and `Stats` can silently ignore a 403
   (`if (e.status !== 403)`).
4. **`replayed`** reads a *response header*, not the body — surfacing the
   backend's idempotency behaviour to the UI.

## 4.3 Five real API workflows 🔴

### Workflow 1 — Sign in

```
FEATURE:        Authenticate and load identity
FRONTEND FILE:  src/App.jsx (Auth) → src/api.js
FUNCTION:       go(kind) → api.login() → api.me()
HTTP METHOD:    POST, then GET
ENDPOINT:       /auth/login, then /auth/me
REQUEST DATA:   { email, password }  → then no body, Authorization: Bearer <jwt>
RESPONSE:       { access_token, token_type } → { id, email, role, rider_id }
STATE UPDATED:  token (module + localStorage), App.user (via onUser), App.log
UI RESULT:      Login inputs → identity strip; ops controls enable; Stats mounts
BACKEND:        app/routers/auth.py:57 (bcrypt verify, JWT issue), :73 (/me)
FAILURE:        401 "Incorrect email or password" → red line in Activity
```

### Workflow 2 — Poll orders and riders (runs forever, every 4 s)

```
FEATURE:        Keep the console live
FRONTEND FILE:  src/App.jsx
FUNCTION:       refresh() — useCallback, driven by useEffect + setInterval
HTTP METHOD:    GET × 2, in parallel via Promise.all
ENDPOINT:       /orders and /riders
REQUEST DATA:   none (Bearer attached if signed in, but neither endpoint requires it)
RESPONSE:       [ {id, customer_id, value, status, created_at}, ... ]
                [ {id, name, current_lat, current_lon, status, created_at}, ... ]
STATE UPDATED:  orders, riders
UI RESULT:      Counter tiles recompute (counts/free), order rows re-render
BACKEND:        app/routers/orders.py:42, app/routers/riders.py:41
FAILURE:        swallowed by an empty catch — the Health pills show the outage
```

⚠️ Note: **both endpoints are unauthenticated** on your backend. The console
shows orders and riders even signed out. That's a deliberate demo choice but you
should know it — see Part 6.

### Workflow 3 — Create an order with an idempotency key 🔴 your best story

```
FEATURE:        Demonstrate retry-safety
FRONTEND FILE:  src/App.jsx → src/api.js
FUNCTION:       addOrder(true) → api.createOrder(body, "demo-fixed-key")
HTTP METHOD:    POST
ENDPOINT:       /orders
HEADERS:        Content-Type: application/json, Idempotency-Key: demo-fixed-key
REQUEST DATA:   { customer_id, restaurant_id, value, pickup_lat/lon, drop_lat/lon }
RESPONSE:       201 { id, customer_id, value, status: "PENDING", created_at }
                on the SECOND click: the cached first response + header
                Idempotent-Replay: true
STATE UPDATED:  log (amber "REPLAYED — no second order created"), then orders via refresh()
UI RESULT:      First click adds an order. Second click adds NOTHING — order count
                is unchanged — and logs REPLAYED
BACKEND:        app/middleware/idempotency.py — Redis SET NX claims the key,
                caches the response for 24h, replays it on repeat
```

The key is deliberately fixed ([App.jsx:259-264](../frontend/src/App.jsx#L259-L264))
so the feature is clickable rather than theoretical. This is the single most
impressive thing in your frontend — it makes a backend guarantee **visible**.

### Workflow 4 — Dispatch (ops only)

```
FEATURE:        Assign the next pending order to a rider
FRONTEND FILE:  src/App.jsx
FUNCTION:       dispatch() → api.dispatch()
HTTP METHOD:    POST
ENDPOINT:       /orders/dispatch
REQUEST DATA:   no body; Authorization: Bearer <jwt>
RESPONSE:       200 { dispatched: { order_id, rider_id } }
STATE UPDATED:  log, then orders/riders via refresh()
UI RESULT:      Green log line "dispatched order 12 → rider 4"; the order's badge
                turns from PENDING to ASSIGNED; the free-riders count drops
BACKEND:        app/routers/orders.py:50, guarded by require_ops
FAILURES:       403 "Ops privileges required"   (signed in as rider/customer)
                404 NO_PENDING_ORDERS           (nothing to dispatch)
                409 RIDER_UNAVAILABLE           (no rider in range)
```

🔴 Those last two are worth mentioning: your backend distinguishes a **demand**
problem from a **supply** problem, and each surfaces as a distinct message in the
activity log.

### Workflow 5 — Advance order status

```
FEATURE:        Move an order through its state machine
FRONTEND FILE:  src/App.jsx
FUNCTION:       advance(id, status) → api.setStatus(id, status)
HTTP METHOD:    PATCH
ENDPOINT:       /orders/{id}/status
REQUEST DATA:   { status: "PICKED_UP" }
RESPONSE:       200 { order_id, status }
STATE UPDATED:  log, then orders via refresh()
UI RESULT:      Badge colour changes; the available buttons change, because they
                are rendered from STATUS_FLOW[o.status]
BACKEND:        app/routers/orders.py:79 — TWO orthogonal guards:
                  assert_may_change_status(user, order, new)  → permitted actor?
                  transition(current, new)                    → legal move?
FAILURES:       401 no token / 403 wrong actor / 400 INVALID_TRANSITION / 404
```

🔴 **The two-guard design is a great thing to explain**, and the frontend mirrors
only the first half: `STATUS_FLOW` prevents offering illegal transitions, but it
knows nothing about actors. Your own code comment says it
([App.jsx:5-7](../frontend/src/App.jsx#L5-L7)) — *"The server enforces the real
rules (legal transition AND permitted actor) — this only avoids showing buttons
that are guaranteed to 400."*

## 4.4 HTTP fundamentals 🔴 MUST KNOW

### Request and response

A **request** has: a method, a URL, headers, and optionally a body.
A **response** has: a status code, headers, and usually a body.

Your `POST /orders` request looks like this on the wire:
```
POST /orders HTTP/1.1
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Idempotency-Key: demo-fixed-key

{"customer_id":42,"restaurant_id":7,"value":530,"pickup_lat":28.61,...}
```
Response:
```
HTTP/1.1 201 Created
Content-Type: application/json
X-RateLimit-Remaining: 97

{"id":12,"customer_id":42,"value":530.0,"status":"PENDING","created_at":"..."}
```

### Methods 🔴 — mark clearly which you use

| Method | Meaning | Used here? |
|---|---|---|
| **GET** | Read. No body. Safe and idempotent | ✅ `/ready`, `/auth/me`, `/orders`, `/riders`, `/admin/stats` |
| **POST** | Create / trigger an action. Not idempotent | ✅ `/auth/register`, `/auth/login`, `/orders`, `/riders`, `/orders/dispatch` |
| **PATCH** | Partial update | ✅ `/orders/{id}/status` |
| PUT | Full replacement | ❌ not used |
| DELETE | Remove | ❌ not used |

🔴 **Why PATCH and not PUT for the status change?** You send only
`{ status: "PICKED_UP" }`, not the entire order. PUT means "replace the resource
with this representation"; PATCH means "apply this partial change". PATCH is
correct here — a good, specific answer.

🔴 **Why is POST /orders/dispatch a POST when it doesn't create anything?**
Because it *changes server state* — it assigns a rider. GET must be **safe**
(no side effects), so a dispatch that mutated data behind a GET would be wrong,
and would be re-triggered by any retry or prefetch.

### Status codes 🔴 — the ones your app actually produces

| Code | Meaning | Where it comes from in your system |
|---|---|---|
| **200 OK** | Success | login, `/auth/me`, list endpoints, dispatch, status update |
| **201 Created** | Resource created | `POST /orders`, `POST /riders`, `POST /auth/register` |
| **400 Bad Request** | Malformed / illegal | `INVALID_TRANSITION` — e.g. PENDING → DELIVERED |
| **401 Unauthorized** | *Not authenticated* — no/invalid token | wrong password; missing or expired JWT |
| **403 Forbidden** | *Authenticated but not allowed* | customer clicking dispatch; rider cancelling |
| **404 Not Found** | Doesn't exist | `ORDER_NOT_FOUND`, `NO_PENDING_ORDERS` |
| **409 Conflict** | Conflicts with current state | duplicate email on register; `RIDER_UNAVAILABLE`; idempotency in-progress |
| **422 Unprocessable** | Validation failed | Pydantic — bad email, password < 8 chars |
| **429 Too Many Requests** | Rate limited | token-bucket middleware |
| **500** | Server error | unhandled exception |
| **503 Service Unavailable** | Degraded | `/ready` when a dependency is down |

🔴 **401 vs 403 — near-certain question.**
- **401** = "I don't know who you are." Missing, malformed, or expired token.
- **403** = "I know exactly who you are, and you may not do this."

Your app demonstrates both cleanly: signed out, dispatch gives 401; signed in as
`customer`, it gives 403 from `require_ops`
([app/core/dependencies.py:43-49](../app/core/dependencies.py#L43-L49)).

### Headers your code sets or reads

| Header | Direction | Purpose |
|---|---|---|
| `Content-Type: application/json` | sent | tells the server the body is JSON |
| `Authorization: Bearer <jwt>` | sent | identifies the caller |
| `Idempotency-Key` | sent | makes a retry safe |
| `Idempotent-Replay: true` | **received** | tells the client the response was replayed |
| `X-RateLimit-Remaining` | received | set by your rate limiter (not read by the UI) |

## 4.5 Same-origin: why there is no CORS 🟡 SHOULD KNOW — a strong point

```js
const BASE = "";     // api.js:5
```

Every request goes to a **relative path**: `/orders`, `/auth/login`. Relative
means "the same origin that served this page".

**In development** — [vite.config.js](../frontend/vite.config.js) proxies:
```js
server: {
  proxy: {
    "/orders": "http://localhost:8000",
    "/riders": "http://localhost:8000",
    "/auth":   "http://localhost:8000",
    "/admin":  "http://localhost:8000",
    "/ready":  "http://localhost:8000",
    ...
  },
}
```
The browser talks to Vite on :5173; Vite forwards those paths to FastAPI on
:8000. The browser only ever sees one origin.

**In production** — FastAPI serves the built bundle
([app/main.py:130-136](../app/main.py#L130-L136)):
```python
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
```
HTML and API come from the same server, so again: one origin.

**What is CORS?** Browsers block a page on origin A from reading responses from
origin B unless B explicitly opts in with `Access-Control-Allow-Origin`. It's a
browser-enforced security boundary.

🔴 **Your answer:** *"There is no CORS configuration anywhere in the project,
because there is no cross-origin request. `BASE` is an empty string, so every
call is a relative path. In dev, Vite proxies those paths to the API; in
production, FastAPI serves the built bundle itself. One origin, one deploy
artifact, and no environment variable pointing the frontend at a per-environment
backend URL. The trade-off is that the frontend can't be deployed to a CDN
independently — which for an internal ops console is the right call, but I'd
change it if the frontend needed independent scaling or global edge caching."*

That last sentence — naming the cost — is what separates a good answer from a
recited one.

## 4.6 `fetch` vs Axios 🔴 — expect this question

| | `fetch` (yours) | Axios |
|---|---|---|
| Built into browsers | ✅ | ❌ ~13 KB dependency |
| Rejects on 4xx/5xx | ❌ must check `res.ok` | ✅ automatic |
| Auto JSON parsing | ❌ manual | ✅ |
| Interceptors | ❌ | ✅ |
| Request timeout | ❌ needs `AbortController` | ✅ built in |

> **Interview answer:** *"I used `fetch` because it's built into the browser and
> what Axios adds — automatic JSON parsing, throwing on non-2xx, and interceptors
> — is about fifteen lines that I wrote once in my `request()` wrapper. For ten
> endpoints that wasn't worth a dependency. The two things I genuinely gave up are
> request timeouts and cancellation: `fetch` needs an `AbortController` for those
> and I don't use one, so a hung request stays pending. Axios gives you a timeout
> option out of the box. If the API were slower or less reliable, that would
> change the calculation."*

---

## 4.7 Routing 🔴 MUST KNOW — because the answer is "none"

⚠️ **Your project has no client-side router.** No React Router, no
`BrowserRouter`, no `Routes`, no `Link`, no `useNavigate`, no URL parameters.
**Never claim otherwise** — it is trivially disproved by `package.json`.

**What you have instead:** one URL (`/`) and conditional rendering. What a user
perceives as different "screens" are different *states*:

| Perceived view | Actually |
|---|---|
| Signed-out login | `user === null` → ternary branch in `Auth` |
| Signed-in console | `user !== null` → the other branch |
| Ops view with stats | `{user?.role === "ops" && <Stats/>}` |
| Empty state | `{orders.length === 0 && <p>No orders yet.</p>}` |

**One consequence worth knowing** — your backend comments on it explicitly
([app/main.py:132-135](../app/main.py#L132-L135)): `StaticFiles(html=True)`
serves `index.html` at the mount root but does **not** rewrite unknown paths to
it. So `/nope` returns a real 404. If you added React Router, you would *also*
need a server-side catch-all that returns `index.html` for unknown paths —
otherwise deep links and page refreshes on a sub-route would 404.

🔴 That is the single best thing you can say about routing: you understand what
adding it would require on the server, not just the client.

> **Interview answer:** *"There's no router — it's a single-view console, so
> routing would be indirection with nothing to route to. The 'views' are
> conditional renders driven by state: whether a user is signed in, and whether
> their role is ops. If I added React Router I'd wrap the app in `BrowserRouter`,
> declare `Route`s, and navigate with `Link`/`useNavigate` — but the part people
> forget is the server side. FastAPI currently serves `index.html` only at the
> mount root, so a refresh on `/orders/12` would 404. I'd need a catch-all that
> returns `index.html` for unknown paths, without shadowing the API routes."*

---

## 4.8 Authentication 🔴 MUST KNOW — and know the security trade-offs

### The mechanism: JWT bearer tokens

**What is a JWT?** A JSON Web Token: three base64 sections — header, payload,
signature — joined by dots. The payload holds **claims**; yours are `sub` (the
email), `is_admin`, `iat` (issued at), and `exp` (expiry)
([app/core/security.py:46-54](../app/core/security.py#L46-L54)).

🔴 **The single most important fact:** a JWT payload is **base64-encoded, not
encrypted**. Anyone holding the token can read its contents. What they cannot do
is *change* it, because the server verifies an HMAC-SHA256 signature. So: never
put secrets in a JWT.

### The complete flow

```
1  LOGIN          POST /auth/login  { email, password }
2  SERVER         bcrypt-verifies the password (constant-time compare)
                  issues a signed JWT with sub + exp
3  RESPONSE       { access_token: "eyJ...", token_type: "bearer" }
4  FRONTEND       setToken(data.access_token)      api.js:9-13
                    → let token = t                (module variable, fast)
                    → localStorage.setItem("diq_token", t)   (survives refresh)
5  EVERY CALL     if (token) headers["Authorization"] = `Bearer ${token}`
6  SERVER         get_current_user: verify signature + exp,
                  then LOAD THE USER FROM THE DATABASE
7  RELOAD         useEffect on mount → getToken() → GET /auth/me → setUser
8  EXPIRED        /auth/me returns 401 → .catch(() => setToken(null))
9  LOGOUT         POST /auth/logout → server adds the token's jti to a Redis
                  denylist (TTL = the token's remaining life)
10 PROOF          replay the same token at /auth/me → 401
11 LOCAL          setToken(null) → removeItem → onUser(null), in `finally`
```

### Two details worth raising unprompted 🔴

**1. The server re-loads the user rather than trusting token claims**
([app/core/dependencies.py:34-40](../app/core/dependencies.py#L34-L40)):
```python
# Load the user rather than trusting the token's claims wholesale: a token
# stays valid until it expires, so a user deleted or demoted a minute ago
# would otherwise keep full access for the rest of the token's life.
user = db.query(User).filter(User.email == claims["sub"]).first()
```
This means a role change takes effect on the **next request**, not at token
expiry. That is a genuinely good design point and it's in *your* backend.

**2. Logout is a server-side event, and the UI proves it.** This is the classic
JWT trap: a signature check can never express "this one was logged out", so
clearing `localStorage` leaves a copied token valid until `exp`. The fix is a
denylist — every token carries a `jti`, `POST /auth/logout` writes that `jti` to
Redis with **TTL = the token's remaining lifetime**, and `get_current_user`
checks it.

Two things to say about it unprompted:

- **It does not undo statelessness.** The denylist is bounded and self-cleaning
  — an entry outlives the token by zero seconds — so it is not a session store
  that grows forever. Signature verification is still local; only the "was this
  revoked" lookup is shared.
- **The console demonstrates it rather than claiming it.** After logging out it
  replays the same token against `/auth/me` and reports the 401. Without that
  step, a real revocation and a purely local clear look *identical* on screen.

The remaining honest gap is that this revokes **one token, not the user** —
signing out on a phone deliberately leaves the laptop signed in. Revoking every
session would need a second denylist keyed on `sub` plus an issued-after
timestamp. Refresh tokens are also still absent.

### Storage: `localStorage` vs the alternatives 🔴 — near-certain question

```js
let token = localStorage.getItem("diq_token") || null;   // api.js:7
```

| Option | Survives refresh? | Survives tab close? | Readable by JS? |
|---|---|---|---|
| **`localStorage`** ← yours | ✅ | ✅ | ⚠️ **yes** |
| `sessionStorage` | ✅ | ❌ per-tab | ⚠️ yes |
| In-memory only | ❌ | ❌ | yes |
| **httpOnly cookie** | ✅ | ✅ | ✅ **no** |

🔴 **The security answer, stated properly:**

> *"The token is in `localStorage`, which means any JavaScript running on the
> page can read it — so a single XSS vulnerability, including one from a
> compromised npm dependency, is a token theft. The stronger default is an
> httpOnly cookie, which JavaScript cannot read at all. That isn't free: cookies
> are sent automatically on every request to the origin, which opens CSRF, so
> you'd need `SameSite=Strict` and/or a CSRF token. I chose `localStorage` for a
> demo console because it's simple and works with a pure bearer-token API, but
> for anything handling real user data I'd move to httpOnly cookies with CSRF
> protection, and shorten token lifetime with a refresh flow."*

That answer shows you know the attack, the alternative, **and** the cost of the
alternative. That is the senior-sounding version.

### Authorization: how roles reach the UI 🔴

Your three roles are `ops`, `rider`, `customer`
([app/core/enums.py:12-15](../app/core/enums.py#L12-L15)).

**Frontend** ([App.jsx:306](../frontend/src/App.jsx#L306)):
```jsx
const isOps = user?.role === "ops";
```
Used for `disabled={busy || !isOps}`, the `title` tooltip, the permission note,
and whether `<Stats/>` mounts at all.

**Backend** — the real enforcement:
| Rule | Where |
|---|---|
| `require_ops` on dispatch and rider creation | [dependencies.py:43](../app/core/dependencies.py#L43) |
| Router-level guard on all `/admin/*` | [admin.py:13-17](../app/routers/admin.py#L13-L17) |
| Actor guard on status changes: ops → anything; rider → only their own order, never cancel; customer → nothing | [dependencies.py:57-96](../app/core/dependencies.py#L57-L96) |

🔴 **Authentication vs authorization** — say it in one line: *"Authentication is
who you are; authorization is what you're allowed to do. My login endpoint does
authentication and issues a JWT; `require_ops` and `assert_may_change_status` do
authorization."*

🔴 **"Can I bypass your frontend permission checks?"** — the answer that wins:

> *"Yes, trivially — open devtools and remove the `disabled` attribute, or just
> call the endpoint with curl. That's exactly why the check exists in both
> places. The frontend check is UX: it explains why a control is unavailable
> instead of letting you click and fail. The server check is the security
> boundary — `require_ops` runs regardless of what the browser did. The console
> is actually built to demonstrate this: switch to the customer role, and a
> restricted action returns a real 403 that shows up in the activity log."*

---

## 4.9 Loading, error and empty states 🔴 MUST KNOW

**WHY THEY MATTER:** a network call can be slow, fail, or return nothing. A UI
that only handles the happy path looks broken in the other three cases.

### Loading

| Mechanism | Where | What the user sees |
|---|---|---|
| `busy` flag | `App` and `Auth` | action buttons `disabled`, greyed at 40% opacity, `cursor: not-allowed` |
| `checks === null` | `Health` | the text "checking…" |
| `stats === null` | `Stats` | nothing — the strip simply isn't there yet |

```jsx
setBusy(true);
try { ... } catch (e) { ... } finally { setBusy(false); }
```
🔴 `finally` is what guarantees the UI never gets stuck disabled after a failure.

⚠️ **Honest gaps:** there is **no loading indicator for the orders/riders lists**
— on first load they show "No orders yet." which is indistinguishable from a
genuinely empty database. And `advance()` sets no `busy` flag at all, so status
buttons can be double-clicked.

### Errors

Every handler follows one pattern:
```js
catch (e) {
  say(e.message, "err");
}
```
`say` prepends `{ msg, kind: "err", at: <time> }` to `log` → the activity panel
renders it with `className="row log err"` → CSS colours it red
([App.css:179](../frontend/src/App.css#L179)).

**Three refinements worth pointing out:**

```js
// App.jsx:63 — Stats: don't shout about an expected 403
if (e.status !== 403) say(e.message, "err");
```
```js
// App.jsx:121 — Auth: turn a failure into an actionable instruction
say(`${e.message} — run: python -m scripts.seed_users`, "err");
```
```js
// App.jsx:299 — advance: prefix which order failed
say(`order ${id}: ${e.message}`, "err");
```

⚠️ **And one gap** ([App.jsx:205-207](../frontend/src/App.jsx#L205-L207)):
```js
} catch {
  /* transient poll failure — the health pills already show it */
}
```
The 4-second poll silently swallows every error. The rationale is sound — a
failing poll every 4 seconds would flood a 14-line log and drown real messages —
but the effect is that a persistent failure is invisible except through the
health pills. A better design would be a single sticky "connection lost" banner
driven by a consecutive-failure count.

### Empty states

```jsx
{orders.length === 0 && <p className="empty">No orders yet.</p>}
{log.length === 0 && <p className="empty">Actions appear here.</p>}
{counts[s] || 0}                          // renders 0, never "undefined"
{Math.round(stats.avg_order_value || 0)}  // renders 0, never "NaN"
{Object.entries(stats.riders_by_status || {})}  // never throws
```

> **Interview answer:** *"Every action follows set-busy / try / catch / finally,
> so buttons disable during the request and always re-enable — including on
> failure, because the reset is in `finally`. Errors surface as a red line in the
> activity panel with the message the server actually sent, since my HTTP wrapper
> normalises three different error shapes into one. Empty states are explicit
> rather than blank. The gap I'd fix first is that the background poll swallows
> errors silently — I'd add a consecutive-failure counter and a single connection
> banner rather than spamming the log."*

---

## 4.10 CSS and UI libraries 🔴 — the answer is "none, deliberately"

⚠️ **You use zero UI libraries.** No Tailwind, Bootstrap, Material UI, Ant
Design, shadcn/ui, Chakra, styled-components, Emotion, Sass. No icon library. No
chart library. Two runtime dependencies total: `react` and `react-dom`.

**What you have instead:** 204 lines of hand-written CSS in one global
stylesheet, using custom properties as design tokens, Flexbox and Grid for
layout, and dynamic class names composed from state.

### The libraries in your `package.json`, and what each is for

| Package | What it is | Why it's here | What you must know |
|---|---|---|---|
| **react** 19.2.8 | The UI library | It's the whole app | components, JSX, hooks, state |
| **react-dom** 19.2.8 | Renders React to the browser DOM | `createRoot` in `main.jsx` | why it's a separate package from `react` |
| **vite** 8.2.0 | Dev server + bundler | `npm run dev` (HMR), `npm run build` → `dist/` | it compiles JSX and bundles; the dev proxy config |
| **@vitejs/plugin-react** 6.0.5 | JSX transform for Vite | Turns JSX into `createElement` calls; uses **Oxc** | JSX needs a build step; this is what does it |
| **oxlint** 1.76.0 | Linter | `npm run lint`; enforces `react/rules-of-hooks` | why the Rules of Hooks need a linter |
| **@types/react**, **@types/react-dom** | TypeScript type definitions | Editor autocomplete only | 🔴 **their presence does NOT make this a TypeScript project** |

🔴 **Be careful with that last row.** If an interviewer sees `@types/react` in
`package.json` and asks "so this is TypeScript?", the answer is: *"No — the
source is `.jsx` and `.js`. Those type packages come with the Vite template and
only give editors autocomplete and hover docs. There's no `tsconfig.json` and no
type checking in the build."*

### Vite 🟡 SHOULD KNOW

**WHAT IS IT?** A build tool. Two jobs:
1. **Dev server** — serves your source with **HMR** (Hot Module Replacement): save
   a file and the browser updates that module without a full reload, preserving
   state.
2. **Bundler** — `npm run build` compiles JSX, bundles, minifies and hashes into
   `frontend/dist/`, which FastAPI then serves.

**Why a build step at all?** Browsers don't understand JSX. Something must
convert `<div className="x">` into `React.createElement("div", {className:"x"})`.
That's `@vitejs/plugin-react`.

> **Interview answer:** *"I didn't use a UI library. The console is four
> components and about 200 lines of CSS, so Tailwind or MUI would have been a
> dependency and a class-name vocabulary to learn for no real gain. I used CSS
> custom properties as a small token layer — colours, surfaces, one radius — plus
> Flexbox and Grid. The build is Vite: HMR in development, and a bundle in
> `dist/` that FastAPI serves in production. If this grew into a multi-page
> product with a design system and a team, I'd reach for a component library then
> — the trigger would be needing accessible, consistent primitives like modals,
> dropdowns and date pickers, which are genuinely hard to hand-roll correctly."*

---

# Part 5 — My Actual Frontend Architecture

## 5.1 The directory tree, and what each part is responsible for

```
frontend/
├── index.html          the single HTML document — holds <div id="root">
├── package.json        dependencies and the four npm scripts
├── vite.config.js      dev API proxy → :8000, build output → dist/
├── .oxlintrc.json      lint rules — react/rules-of-hooks: error
├── public/             static files copied to the build as-is
│   ├── favicon.svg     ← referenced by index.html
│   └── icons.svg       ← NOT referenced by anything
├── src/
│   ├── main.jsx        ENTRY POINT — mounts React onto #root
│   ├── App.jsx         ALL UI — App, Auth, Health, Stats; all state; all handlers
│   ├── api.js          ALL HTTP — request(), the api object, token storage
│   ├── App.css         ALL styling — tokens, layout, components, one breakpoint
│   └── assets/         hero.png, react.svg, vite.svg  ← none are imported
└── dist/               build output (gitignored) — served by FastAPI
```

⚠️ **Note the four unused files** (`public/icons.svg`, `src/assets/*`). They are
leftovers from the Vite template. Deleting them would be a two-second cleanup;
if an interviewer notices, say exactly that — don't invent a purpose for them.
The same applies to `frontend/README.md`, which is still the **untouched Vite
template text** and describes a boilerplate, not your app.

## 5.2 Why there is no `components/` or `pages/` folder 🔴

Expect: *"Why is everything in one file?"*

> *"At four components and 439 lines, splitting into folders would have meant
> more files to navigate than code in them. The whole UI fits on two screens, and
> the components are genuinely coupled — `Auth`, `Stats` and the layout all read
> the same `user` state. What I'd say honestly is that the split points are
> already obvious: `Health`, `Stats` and `Auth` are self-contained and would move
> to `components/` unchanged, and `api.js` is already the service layer. The
> trigger for doing it is a second view or a second developer — at that point the
> merge-conflict surface of one 439-line file starts to cost more than the
> indirection saves."*

Naming the trigger is what makes this a judgement call rather than an excuse.

## 5.3 Startup → routing → page → components → state → API → backend

```
   Browser
      │  GET /
      ▼
   FastAPI  StaticFiles → frontend/dist/index.html          app/main.py:136
      │
      ▼
   index.html            <div id="root"> + <script src=main.jsx>
      │
      ▼
   main.jsx              createRoot(#root).render(<StrictMode><App/></StrictMode>)
      │
      ▼
   App.jsx  App()        [no router — a single view]
      │  state: user, orders, riders, log, busy
      │  derived: isOps, counts, free
      │
      ├──▶ <Health/>     own state · GET /ready every 5 s
      ├──▶ <Auth/>       props: user, onUser, say · POST /auth/login · GET /auth/me
      ├──▶ <Stats/>      prop: say · GET /admin/stats every 6 s · ops only
      ├──▶ counters      derived from orders + riders
      ├──▶ actions       onClick → addRider / addOrder / dispatch
      ├──▶ orders panel  [...orders].reverse().map() → rows + STATUS_FLOW buttons
      └──▶ activity      log.map() → timestamped lines
      │
      ▼
   api.js   request() → fetch()
      │     headers: Content-Type · Authorization: Bearer · Idempotency-Key
      ▼
   FastAPI  /auth /orders /riders /admin /ready       (same origin — no CORS)
      │     middleware: request_id → rate_limit → idempotency → route
      ▼
   Postgres · Redis · Kafka
```

---

## 5.4 The 10 Files I Must Understand Before My Interview

Ranked by how much of the application each one teaches you.

### 1. `frontend/src/App.jsx` — lines 187-330 (the `App` component) 🔴
**WHY IT MATTERS:** the root component. Contains every piece of shared state,
all four action handlers, both effects, and the composition of the whole page.
Roughly 60% of everything an interviewer can ask about lives here.
**WHAT TO UNDERSTAND:** the five `useState` calls and what UI each drives; `say`
and `refresh` and why both are `useCallback`; the two effects and their
dependency arrays; the `busy` / `try` / `catch` / `finally` pattern; the derived
values `isOps`, `counts`, `free`.
**IMPORTANT FUNCTIONS:** `say`, `refresh`, `addRider`, `addOrder`, `dispatch`, `advance`.
**REACT CONCEPTS:** useState, useEffect, useCallback, lifting state up, props,
conditional rendering, derived state.
**LIKELY QUESTIONS:** Why is `refresh` wrapped in `useCallback`? What happens if
you remove it? Why does `busy` reset in `finally`? Why is `user` in `App` rather
than in `Auth`?

### 2. `frontend/src/api.js` (all 69 lines) 🔴
**WHY IT MATTERS:** the entire frontend/backend boundary. Small enough to
memorise, and it answers questions about HTTP, auth, error handling and JSON.
**WHAT TO UNDERSTAND:** `request()` end to end; why `fetch` needs an explicit
`res.ok` check; the three-shape error normalisation; why the token is a module
variable mirrored into `localStorage`; why `BASE` is `""`.
**IMPORTANT FUNCTIONS:** `request`, `setToken`, `getToken`, the `api` object.
**CONCEPTS:** async/await, Promises, try/catch, custom Error properties, JSON,
headers, HTTP methods and status codes, modules.
**LIKELY QUESTIONS:** Why not Axios? Does `fetch` throw on a 404? Where is the
token stored and what's the risk? What is `replayed`?

### 3. `frontend/src/App.jsx` — lines 89-185 (`Auth`) 🔴
**WHY IT MATTERS:** the only place with controlled inputs, the clearest
parent↔child props example, and the whole login flow.
**WHAT TO UNDERSTAND:** `value` + `onChange` as a controlled input; `onUser` as a
child-to-parent callback; the `go()` handler line by line; the ternary that swaps
the entire UI.
**CONCEPTS:** props, controlled components, callback props, async handlers,
conditional rendering, Fragments.
**LIKELY QUESTIONS:** Controlled vs uncontrolled? How does the child update the
parent? Why is there no `<form>`? What happens on a wrong password?

### 4. `frontend/src/App.jsx` — lines 16-43 (`Health`) 🔴
**WHY IT MATTERS:** the smallest complete component — state, effect, cleanup,
polling, error handling and list rendering in 28 lines. The best one to walk
through out loud.
**WHAT TO UNDERSTAND:** why the cleanup exists; the three states (loading,
healthy, degraded); how a 503 body is still rendered from the `.catch`.
**CONCEPTS:** useState, useEffect with `[]`, cleanup, `setInterval`,
`Object.entries().map()`, keys, `??`.
**LIKELY QUESTIONS:** What does the returned function do? What breaks without it?
What does the empty dependency array mean?

### 5. `frontend/src/App.jsx` — lines 375-421 (the two panels) 🔴
**WHY IT MATTERS:** list rendering, keys, nested `map`, empty states — and it
contains both your best key (`o.id`) and your worst (`i`).
**WHAT TO UNDERSTAND:** why `[...orders]` is copied before `.reverse()`; how
`STATUS_FLOW` drives which buttons exist; why `key={i}` on a prepended list is
wrong.
**LIKELY QUESTIONS:** Why do lists need keys? Is an index ever acceptable? What
does `[...orders].reverse()` protect against?

### 6. `frontend/src/main.jsx` (9 lines) 🔴
**WHY IT MATTERS:** it's nine lines and it answers "how does your app start?"
**WHAT TO UNDERSTAND:** `createRoot`; why `react` and `react-dom` are separate;
what StrictMode does and why it matters to your intervals.
**LIKELY QUESTIONS:** What is StrictMode? Why do effects run twice in dev?

### 7. `frontend/vite.config.js` 🟡
**WHY IT MATTERS:** explains dev vs production, the proxy, and why there's no CORS.
**LIKELY QUESTIONS:** How does the frontend find the backend? Why no CORS config?
What changes between dev and production?

### 8. `frontend/src/App.css` — lines 1-30 and 96-138 🟡
**WHY IT MATTERS:** covers custom properties, Grid, Flexbox and the single media
query — enough to answer any CSS question about this project.
**LIKELY QUESTIONS:** How did you handle theming? Is it responsive? Flexbox vs Grid?

### 9. `app/core/dependencies.py` (backend) 🔴
**WHY IT MATTERS:** the frontend's `isOps` is cosmetic; **this** is the real
permission model. Any question about your role UI ends here.
**WHAT TO UNDERSTAND:** `get_current_user` re-loading the user from the DB;
`require_ops` returning 403 not 401; the actor guard vs the transition guard.
**LIKELY QUESTIONS:** 401 vs 403? Can I bypass the frontend check? How do you
stop a rider cancelling an order?

### 10. `app/middleware/idempotency.py` (backend) 🟡
**WHY IT MATTERS:** it's the mechanism behind your most interesting UI feature —
the `REPLAYED` message.
**WHAT TO UNDERSTAND:** the Redis `SET NX` claim; the 24-hour cache; the
`Idempotent-Replay` response header that `request()` reads.
**LIKELY QUESTIONS:** What does the idempotency key do? What happens if you click
twice? Why does the client need to know it was a replay?

---

## 5.5 Five Project Flows I Must Be Able To Explain

Learn these five and you can hold a 20-minute conversation about this frontend.

### Flow 1 — User login 🔴

1. **User opens the app.** FastAPI serves `index.html`; `main.jsx` calls
   `createRoot(...).render(<App/>)`.
2. **React renders `App`.** `user` is `null`, `orders` is `[]`, `busy` is `false`.
3. **`App` renders `<Auth user={null} onUser={setUser} say={say} />`.** Because
   `user` is null, `Auth`'s ternary at [App.jsx:129](../frontend/src/App.jsx#L129)
   takes the else-branch: two inputs and four buttons.
4. **The inputs are pre-filled** — `useState("ops@deliveriq.io")` and
   `useState("opspassword123")` are the initial values, and `value={email}`
   displays them.
5. **User types.** Each keystroke fires `onChange={(e) => setEmail(e.target.value)}`
   → state updates → re-render → the input shows the new text. Controlled input.
6. **User clicks "Sign in"** → `onClick={() => go("login")}`.
7. **`go("login")` runs** ([App.jsx:94](../frontend/src/App.jsx#L94)):
   `setBusy(true)` → re-render → both auth buttons `disabled`.
8. **`await api.login(email, password)`** → `request("/auth/login", {method:"POST",
   body:{email,password}})` → `fetch` with `Content-Type: application/json`.
9. **Backend** ([auth.py:57](../app/routers/auth.py#L57)) finds the user,
   bcrypt-verifies the password in constant time, and returns
   `{access_token, token_type}`. On failure it returns **401** with one generic
   message for both "no such user" and "wrong password" — deliberately, to avoid
   account enumeration.
10. **`setToken(data.access_token)`** → module variable set **and**
    `localStorage.setItem("diq_token", ...)`.
11. **`await api.me()`** → `GET /auth/me`, now carrying
    `Authorization: Bearer <jwt>`. The backend verifies the signature and expiry,
    then loads the user from the database rather than trusting the claims.
12. **`onUser(me.data)`** → this is `App`'s `setUser` → `App` re-renders.
13. **The UI changes in four places at once:** `isOps` becomes `true` so "+ Rider"
    and "Dispatch" enable; `{user?.role === "ops" && <Stats/>}` **mounts `Stats`**,
    whose effect starts the 6-second `/admin/stats` poll; `Auth`'s ternary flips to
    the identity strip; the permission note disappears.
14. **`say("signed in as ops@deliveriq.io (ops)", "ok")`** → green line in Activity.
15. **`finally { setBusy(false) }`** → buttons re-enable — on success *and* on failure.

### Flow 2 — Page refresh keeps me signed in 🔴

1. User presses F5. **All React state is destroyed** — `user` is `null` again.
2. The browser reloads `index.html` and re-runs the bundle.
3. **`api.js` is evaluated**, and its very first statement runs:
   `let token = localStorage.getItem("diq_token") || null`. The token is back in
   memory before any component renders.
4. `App` renders with `user === null` — for a moment the login inputs are visible.
5. **After that first render commits, the mount effect runs**
   ([App.jsx:210](../frontend/src/App.jsx#L210)): `if (getToken())` is true.
6. `api.me()` → `GET /auth/me` with the Bearer header.
7. **Success** → `setUser(r.data)` → re-render → the identity strip and ops
   controls appear.
8. **Failure (expired or tampered token)** → the backend returns **401** →
   `.catch(() => setToken(null))` clears it from both memory and `localStorage`,
   leaving a clean signed-out state.

🔴 The honest limit: this only runs on mount. A token that expires *while* the
tab is open isn't noticed until the next reload — the polls keep working because
`/orders` and `/riders` don't require auth.

### Flow 3 — Create an order, and prove retries are safe 🔴 (your best story)

1. User clicks **"+ Order [fixed Idempotency-Key]"** →
   `onClick={() => addOrder(true)}`.
2. `setBusy(true)` → all action buttons grey out.
3. A body is built with randomised customer/restaurant/value and fixed Delhi
   coordinates ([App.jsx:250-258](../frontend/src/App.jsx#L250-L258)).
4. `api.createOrder(body, "demo-fixed-key")` → `request()` adds three headers:
   `Content-Type`, `Authorization` (if signed in), and
   `Idempotency-Key: demo-fixed-key`.
5. **Backend middleware** ([idempotency.py:28](../app/middleware/idempotency.py#L28))
   sees the key, looks it up in Redis, finds nothing, and claims it with
   `SET NX` so two concurrent retries can't both proceed.
6. The route creates the order and returns **201**. The middleware caches that
   response body for 24 hours.
7. `request()` returns `{ data, replayed: false }`.
8. `say("order created", "ok")` → green line. `refresh()` → the new order appears.
9. **User clicks the same button again.**
10. The middleware finds the cached record and returns the **original response**
    with the header `Idempotent-Replay: true`. **The route never runs. No second
    order is created.**
11. `request()` reads that header → `replayed: true`.
12. `say("REPLAYED — no second order created", "warn")` → **amber** line.
13. `refresh()` runs; the order count is unchanged — visible proof.

🔴 Contrast with the plain "+ Order" button, which sends **no** key: every click
creates a new order. Clicking the two buttons alternately demonstrates the
difference in about five seconds.

### Flow 4 — A customer is refused (the 403 demo) 🔴

1. Signed in as ops, the user clicks the **"customer"** chip →
   `onClick={() => switchTo(d)}`.
2. `switchTo` sets the email/password state (visibly changing the inputs — proof
   the inputs are controlled), logs in as the seeded customer, and calls
   `onUser(me.data)`.
3. `App` re-renders with `user.role === "customer"`:
   - `isOps` is `false` → "+ Rider" and "Dispatch" become `disabled`, each with a
     `title` explaining why.
   - `{user?.role === "ops" && <Stats/>}` is false → **`Stats` unmounts**, its
     cleanup runs `clearInterval`, and the `/admin/stats` polling stops.
   - The `.perm-note` appears: *"signed in as customer — rider onboarding and
     dispatch are ops only"*.
4. **The buttons are disabled, so the click can't happen through the UI** — that's
   the point of the design. But the interviewer's question is "what if it did?"
5. If the request is made — via devtools, or curl — `POST /orders/dispatch` hits
   `require_ops` ([dependencies.py:43](../app/core/dependencies.py#L43)), which
   raises **403 "Ops privileges required"**.
6. `request()` sees `!res.ok`, extracts `detail`, creates an `Error` with
   `.status = 403`, and throws.
7. The handler's `catch` calls `say("Ops privileges required", "err")` → a **red**
   line in Activity.
8. `refresh()` is skipped, because the throw jumped past it. `finally` still
   resets `busy`.

🔴 **The sentence to land:** *"The UI disables the control for clarity; the server
refuses it for security. Those are two different jobs, and only the second one is
a boundary."*

### Flow 5 — Advance an order through its state machine 🔴

1. `refresh()` has populated `orders`. An order has `status: "ASSIGNED"`.
2. The row renders from `STATUS_FLOW["ASSIGNED"]`, which is
   `["PICKED_UP", "CANCELLED"]` → the inner `map` produces exactly two buttons.
   A `DELIVERED` order maps `[]` → zero buttons. The UI is a projection of a
   lookup table.
3. User clicks **PICKED_UP** → `onClick={() => advance(o.id, "PICKED_UP")}` — the
   arrow captures `o.id` and `next` from the closure.
4. `advance()` runs. ⚠️ Note it sets **no** `busy` flag — a known gap.
5. `api.setStatus(id, "PICKED_UP")` → **PATCH** `/orders/12/status` with body
   `{ "status": "PICKED_UP" }`. PATCH because it's a partial update, not a
   replacement.
6. **Backend** ([orders.py:79](../app/routers/orders.py#L79)) applies **two
   orthogonal guards**:
   - `assert_may_change_status(user, order, new)` — *may this actor?* ops can do
     anything; a rider only on their own assigned order and never CANCELLED; a
     customer never.
   - `transition(current, new)` — *is this move legal?* PENDING → DELIVERED
     raises `InvalidTransition` (**400**).
7. On success the order is updated. If the new status is terminal, the rider is
   freed and re-indexed into Redis geohash.
8. Response `200 { order_id, status }`.
9. `say("order 12 → PICKED_UP", "ok")` → green line.
10. `refresh()` → new `orders` array → re-render.
11. **The badge changes colour** (`s-ASSIGNED` blue → `s-PICKED_UP` amber) **and
    the buttons change**, because `STATUS_FLOW["PICKED_UP"]` is `["DELIVERED"]` —
    one button now.
12. On failure — say a rider tries to advance someone else's order — **403** →
    `say("order 12: You may only update orders assigned to you", "err")`.

🔴 **The point to make:** the frontend's `STATUS_FLOW` mirrors only the
*transition* half of the rules, never the *actor* half. Your own code comment
says so at [App.jsx:5-7](../frontend/src/App.jsx#L5-L7). That's a deliberate,
defensible split: the client avoids offering buttons guaranteed to 400, and the
server owns correctness.

---

# Part 6 — Interview Questions Based On My Actual Project

80 questions, grouped. Each has a simple answer, a stronger answer, the project
example, and a likely follow-up.

## Frontend Basics

**Q1. What is your frontend built with?**
**SIMPLE:** React 19 with Vite, in plain JavaScript.
**BETTER:** *"React 19.2 with Vite 8 as the build tool, written in JSX — not
TypeScript. It's deliberately minimal: two runtime dependencies, React and
React-DOM. No router, no state library, no UI kit, hand-written CSS. It's a
single-view ops console of about 700 lines, so those would have added weight
without solving a problem I had."*
**PROJECT:** `frontend/package.json`.
**FOLLOW-UP:** *Why no UI library?* → 204 lines of CSS with custom properties as
tokens was less work than learning and shipping a framework's class vocabulary.

**Q2. What does your frontend actually do?**
**BETTER:** *"It's an operations console for a delivery dispatch backend. It shows
live counts of orders by status and how many riders are free, lets an operator
create orders, onboard riders and dispatch work, and advance orders through their
state machine. Two backend behaviours are made visible on purpose: role-based
permissions — you can switch between ops, rider and customer and see real 403s —
and idempotent retries, where clicking 'add order' twice with a fixed key
produces one order and a 'REPLAYED' message."*

**Q3. Is it a single-page application?**
**BETTER:** *"Yes. `index.html` contains one empty `div` and a script tag —
nothing the user sees exists in the HTML source. React builds the entire
interface at runtime and updates it in place; the browser never does a full page
load after the first one."*

**Q4. What's the difference between frontend and backend here?**
**BETTER:** *"The frontend is React running in the user's browser — it renders
the UI and holds transient state like what's typed in a box. The backend is
FastAPI with Postgres, Redis and Kafka; it owns the data, the business rules and
all enforcement. They talk over HTTP with JSON. The dividing line I'd emphasise is
that nothing in the browser can be trusted — my role checks in the UI are
usability, and every one of them is duplicated as a real guard on the server."*

## HTML

**Q5. What's in your `index.html`?**
**BETTER:** *"Almost nothing — a `<head>` with charset, viewport and title, and a
body with `<div id="root">` and a module script tag. That empty div is React's
mount point; `main.jsx` calls `document.getElementById("root")` and renders into
it."*
**FOLLOW-UP:** *Why is the div empty?* → Everything is created by JavaScript at
runtime. The trade-off is that with JS disabled or still loading, the page is
blank — server-side rendering exists to solve that, and I don't need it for an
internal tool.

**Q6. Do you use semantic HTML?**
**BETTER:** *"At the page level, yes — `<header>`, `<section>` and `<footer>`, so
the structure is meaningful rather than a wall of divs. Inside those I use divs
and spans. If I were being rigorous about accessibility I'd go further: the
orders panel is a list of divs styled with Flexbox, and a real `<table>` or an
ARIA list would be better for screen readers."*

**Q7. What's the difference between an id and a class?**
**BETTER:** *"An id is unique per page; a class is reusable. I have exactly one
id — `root` — and it exists so JavaScript can find the mount point. Every style
in my CSS targets classes. In JSX it's spelled `className`, because `class` is a
reserved JavaScript keyword."*

**Q8. Does your project use forms or tables?**
**BETTER:** *"Neither, and that's worth being precise about. The login is two
inputs and buttons with `onClick` — there's no `<form>` element, which has a real
cost: pressing Enter doesn't sign you in. And the orders panel looks tabular but
is divs laid out with Flexbox. Both are things I'd change: a `<form onSubmit>`
with `preventDefault()` for the login, and a semantic table for the orders."*

## CSS

**Q9. How did you style the app?**
**BETTER:** *"One hand-written global stylesheet, `App.css`, imported once in
`App.jsx`. Sixteen CSS custom properties on `:root` act as design tokens —
background, surface, text, accent, status colours, radius — referenced with
`var()`. Layout is Flexbox for rows and Grid for the counter tiles and the
two-panel split."*

**Q10. Flexbox or Grid — when do you use which?**
**BETTER:** *"Flexbox for one dimension, Grid for two. My order rows are Flexbox
— items in a line with a `gap`, plus an empty spacer span with `flex: 1` that
pushes the action buttons to the right edge. My counter strip is Grid with
`repeat(auto-fit, minmax(150px, 1fr))`, so the tiles reflow to as many columns as
fit without any media query."*

**Q11. Is the app responsive?**
**BETTER:** *"Partly, and I'd be careful how I phrase it. There's exactly one
media query, at 900px, which stacks the two panels into a single column. The
counter tiles reflow on their own because of the Grid `auto-fit`. It's a desktop
ops console and it's built for that; it isn't mobile-first and I wouldn't claim it
is."*

**Q12. How do you style based on state?**
**BETTER:** *"Template literals that build a class name from data. The cleanest
example is the order badge: `` className={`badge s-${o.status}`} `` produces
`s-PENDING`, `s-ASSIGNED`, `s-DELIVERED` and so on, and my CSS defines a colour
for each. So the badge colour follows the data with no conditional in the JSX at
all."*
**FOLLOW-UP:** *Any gap there?* → Yes — `.role-ops` and `.role-rider` are defined
but `.role-customer` isn't, so a customer's chip falls back to the base style.

**Q13. What are CSS variables and why did you use them?**
**BETTER:** *"Custom properties declared on `:root` with a `--` prefix and read
with `var()`. My accent orange appears in about eight rules; defining it once
means changing it once. It's the same reasoning as a constant in code, and it's
the lightweight version of what a theming system gives you."*

## JavaScript

**Q14. What's the difference between `const` and `let`?**
**BETTER:** *"`const` can't be reassigned; `let` can. I default to `const` — the
only meaningful `let` in the whole frontend is the auth token in `api.js`, because
it genuinely changes on login and logout. And `const` isn't immutability: it
stops reassignment, not mutation. `const arr = []; arr.push(1)` is fine."*

**Q15. Why do you write `onClick={() => addOrder(false)}` instead of `onClick={addOrder(false)}`?**
**BETTER:** *"The second version calls the function during render and hands React
the return value, so it would fire on every render and never on click. The arrow
gives React a function to invoke later, and lets me bake in arguments — that's how
`onClick={() => advance(o.id, next)}` captures which order and which status from
the surrounding closure."*

**Q16. Explain `map()` and why React uses it so much.**
**BETTER:** *"`map` transforms every element of an array into something else. React
can render an array of elements, so mapping data to JSX is *the* list-rendering
pattern. I use it eight times — orders to rows, the log to lines, health checks to
pills. There's a nested one in the orders panel: each row maps
`STATUS_FLOW[order.status]` into action buttons, so the available transitions come
from a lookup table rather than a chain of conditionals."*

**Q17. What does the spread operator do in your code?**
**BETTER:** *"It's how I keep updates immutable. `[...orders].reverse()` is the
important one — `reverse` mutates the array it's called on, so copying first stops
me mutating React state directly. My logger does the same thing with
`[newEntry, ...oldLog]` rather than pushing."*

**Q18. What's optional chaining, and why is it all over your code?**
**BETTER:** *"`?.` returns `undefined` instead of throwing when the left side is
null. It matters because my `user` state starts as `null` and only fills in after
login — `user.role` would crash on the first render, `user?.role` is safe. Same
for API responses, where a body might be absent entirely."*
**FOLLOW-UP:** *`??` vs `||`?* → `||` falls back on any falsy value including `0`
and `""`; `??` only on null or undefined. For a count of zero that's the
difference between showing `0` and showing your fallback.

**Q19. Where do you use `reduce()`?**
**BETTER:** *"To build the status counts for the header tiles — I reduce the
orders array into an object like `{PENDING: 3, ASSIGNED: 2}`. Honestly, my
implementation spreads the accumulator on every iteration, which allocates a new
object per order. It's irrelevant at demo scale but it's O(n²); mutating the local
accumulator would be the cleaner fix, and it's safe because it's not state."*

**Q20. Do you use loops anywhere?**
**BETTER:** *"Not a single `for` or `while`. Everything is array methods — `map`,
`filter`, `reduce`, `slice`. That's the idiom in React code, because `map` returns
a value you can render whereas a loop is a statement and can't go inside JSX."*

**Q21. What is destructuring?**
**BETTER:** *"Pulling values out by name or position. Three places in my code:
`const { data } = await api.login(...)` unpacks my wrapper's return;
`const [o, r] = await Promise.all([...])` names two results positionally; and
`function Auth({ user, onUser, say })` unpacks props in the signature, which is
the standard React idiom."*

**Q22. What is JSON and where does it appear?**
**BETTER:** *"It's the text format on the wire. `JSON.stringify` turns my request
object into a string; `JSON.parse` turns the response text back into an object. I
deliberately read responses as text and parse inside a try/catch instead of calling
`res.json()` — if a proxy returns an HTML error page, `res.json()` throws and I
lose the body, whereas my version keeps the raw text so the error is still
visible."*

## React Basics

**Q23. What is React and why did you use it?**
**BETTER:** *"React is a library for building UIs out of components, and it's
declarative — I describe what the interface should look like for a given state
rather than writing DOM instructions. That mattered here because the console
re-renders continuously: three polls, every four to six seconds, each replacing
lists and counters. In plain JavaScript I'd be hand-writing DOM updates for every
one of those, and the classic bug is updating your data but forgetting one place
in the DOM. With React I call `setOrders(...)` and everything derived from orders
— the rows, the four status tiles, the count badge — updates together, because
they're all computed from the same state."*

**Q24. What is the virtual DOM?**
**BETTER:** *"React keeps a lightweight copy of the UI tree in memory. When state
changes it builds a new tree, diffs it against the old one, and applies only the
minimal real-DOM changes. Real DOM operations are expensive; the in-memory
comparison isn't. In my orders panel, when the poll returns one extra order,
React updates the count text and inserts one row — the other rows are untouched
because their `key` matched."*

**Q25. What does "declarative" mean?**
**BETTER:** *"I describe the destination, not the route. My orders count is
`{orders.length}` — I never wrote code to *change* that number. Imperative would
be `document.querySelector('.count').textContent = orders.length`, where I'm
responsible for remembering every place that needs updating."*

**Q26. How does your app start up?**
**BETTER:** *"FastAPI serves `index.html`, which loads `main.jsx`. That calls
`createRoot(document.getElementById('root'))` and renders `<App/>` inside
`StrictMode`. `App` runs its hooks, returns JSX, React converts it to real DOM
nodes, and then the effects fire — a session restore and three polling
intervals."*

**Q27. Why are `react` and `react-dom` separate packages?**
**BETTER:** *"`react` is the component model and hooks — it doesn't know what it's
rendering to. `react-dom` is the renderer for browsers. That split is why React
Native can exist with a different renderer over the same component model. In my
code `main.jsx` imports `createRoot` from `react-dom/client` and the hooks from
`react`."*

**Q28. What is StrictMode?**
**BETTER:** *"A development-only wrapper that deliberately mounts, unmounts and
remounts components to expose effects that don't clean up. It's directly relevant
to me because I run three `setInterval` polls — without `clearInterval` in the
cleanup, StrictMode would leave orphaned timers and I'd poll at double rate. It's
a no-op in the production build."*

## JSX

**Q29. What is JSX and is it HTML?**
**BETTER:** *"It's HTML-like syntax inside JavaScript that gets compiled — Vite's
React plugin turns every tag into a `createElement` call. It isn't HTML: `class`
becomes `className`, events are camelCase props, every tag must self-close, and
curly braces embed JavaScript expressions. What ends up in the browser is ordinary
DOM elements."*

**Q30. Why `className` instead of `class`?**
**BETTER:** *"Because JSX is JavaScript, and `class` is a reserved keyword there."*

**Q31. Can you use an `if` statement inside JSX?**
**BETTER:** *"No — braces take an expression, and `if` is a statement. So it's
ternaries for two branches and `&&` for show-or-nothing. If the logic is bigger, I
compute it above the return or return early — `Stats` does `if (!stats) return
null` before its JSX."*

**Q32. What's a Fragment and why do you use one?**
**BETTER:** *"`<>...</>` groups children without emitting a wrapper element. In my
auth bar it's structural, not cosmetic — the parent is a Flexbox container, so an
extra wrapper div would collapse everything inside it into a single flex item and
break the layout."*

**Q33. Why must component names be capitalised?**
**BETTER:** *"JSX uses the case to decide what to compile to. Lowercase becomes a
literal HTML tag string; capitalised becomes a reference to your function. So
`<health />` would emit a meaningless `<health>` element, while `<Health />` calls
my component."*

## Components

**Q34. What is a component?**
**BETTER:** *"A function whose name starts with a capital and which returns JSX. I
have four: `App` is the root and owns shared state; `Auth` handles sign-in;
`Health` polls readiness; `Stats` shows ops-only metrics. All function components
— there are no class components, which is the modern default."*

**Q35. Walk me through one component.**
**BETTER:** Use `Health` — it's 28 lines and covers state, effects, cleanup,
polling, error handling and list rendering. *"It holds one piece of state,
`checks`, starting as null. An effect with an empty dependency array polls
`/ready` immediately and then every five seconds, and returns a cleanup that
clears the interval. The render is a ternary: null shows 'checking…', otherwise
`Object.entries(checks).map(...)` makes one pill per dependency, green or red. The
nice bit is the catch — a degraded backend returns 503 *with* a per-dependency
breakdown, and because my HTTP wrapper attaches the response body to the thrown
error, the catch can still render exactly which dependency is down."*

**Q36. Why is everything in one file?**
**BETTER:** See §5.2 — defend it with the trigger for changing your mind.

**Q37. How would you split `App.jsx` if it grew?**
**BETTER:** *"`Health`, `Stats` and `Auth` are already self-contained and would
move to `components/` unchanged — they don't reach into `App` for anything except
the props they're given. `api.js` is already the service layer. What's left in
`App` is state plus four handlers, and if that grew I'd pull the polling into a
custom `useOrders` hook. The trigger would be a second view or a second developer,
because that's when a single 439-line file starts costing more in merge conflicts
than the indirection saves."*

## Props

**Q38. What are props?**
**BETTER:** *"Inputs to a component, passed from parent to child, and read-only.
`App` passes three to `Auth`: `user`, `onUser` and `say`. Data flows one way —
down — which makes it easy to reason about where a value came from."*

**Q39. How does a child update the parent?**
**BETTER:** *"The parent passes a function down. `App` passes `onUser={setUser}`
to `Auth`; when login succeeds, `Auth` calls `onUser(user)` and `App`'s state
updates. The child doesn't know it's calling `setUser` — it just knows it got
something called `onUser`, which keeps it reusable. That's the callback-prop
pattern, and the `on...` naming signals it."*

**Q40. Props vs state?**
**BETTER:** *"Props come from the parent and are read-only; state is owned by the
component and changing it re-renders. `Auth` demonstrates both — `user` is a prop
because `App` and the `Stats` mounting decision also depend on it, while `email`
and `password` are local state because nothing outside `Auth` cares until submit.
My rule was: keep state as low as possible, lift it only when a second component
needs it."*

**Q41. What is "lifting state up"?**
**BETTER:** *"Moving state to the closest common ancestor when more than one
component needs it. `user` started conceptually inside `Auth`, but `App` needs it
for `isOps` and for deciding whether to mount `Stats` — so it lives in `App` and
comes back down as a prop, with `onUser` as the way up."*

**Q42. Can a child modify a prop?**
**BETTER:** *"No. Props are read-only — mutating one breaks the one-way data flow
and React won't re-render from it anyway. To change something the parent owns, you
call a function the parent gave you."*

## State

**Q43. What is state and why not a normal variable?**
**BETTER:** *"State is data that should redraw the UI when it changes. A plain
variable fails twice: React isn't notified, so nothing re-renders, and the
variable resets on every render because the component function runs again from
the top. `useState` stores the value outside the function and gives me a setter
that schedules a re-render."*

**Q44. Explain `const [busy, setBusy] = useState(false)`.**
**BETTER:** *"`useState` returns a two-element array, so that's array
destructuring — `busy` is the value for this render, `setBusy` schedules an update
and a re-render, and `false` is the initial value, used only on the first render.
React ignores that argument afterwards. In my app `busy` drives the `disabled`
attribute on the action buttons."*

**Q45. Does `setState` update the variable immediately?**
**BETTER:** *"No. It schedules an update. If I call `setBusy(true)` and read
`busy` on the next line, it's still false — `busy` is a const bound to this
render. The new value shows up in the next render. React also batches multiple
setter calls in one event handler into a single re-render."*

**Q46. Why shouldn't you mutate state directly?**
**BETTER:** *"React decides whether to re-render by comparing references. If I
push into the existing array, the reference is unchanged, so React can conclude
nothing happened. That's why my logger builds a new array with spread, and why I
write `[...orders].reverse()` — `reverse` mutates in place, so without the copy
I'd be mutating state."*

**Q47. When do you use the functional form of a setter?**
**BETTER:** *"When the next value depends on the previous one. My logger is
`setLog(l => [entry, ...l].slice(0, 14))`. The callback receives the latest value
rather than the one captured in this render's closure, so if two actions log in
the same tick both survive. Writing `setLog([entry, ...log])` could drop one."*

**Q48. What state does your app hold?**
**BETTER:** *"Five pieces in `App` — the signed-in user, orders, riders, an
activity log and a busy flag. `Auth` owns email, password and its own busy;
`Health` owns its checks; `Stats` owns its stats. Plus one thing deliberately
outside React: the JWT, as a module variable in `api.js` mirrored to
localStorage."*

**Q49. What is derived state, and do you have any?**
**BETTER:** *"Values computed from state during render rather than stored
separately. I have three: `isOps` from `user`, `counts` reduced from `orders`, and
`free` filtered from `riders`. Keeping them derived means they can never go stale
— if I stored `counts` in its own state I'd have to remember to update it every
time orders changed, and that's exactly the class of bug React is designed to
remove."*

## Hooks

**Q50. What are hooks?**
**BETTER:** *"Functions starting with `use` that let function components hold
state and run side effects. I use three: `useState` ten times, `useEffect` four
times, and `useCallback` twice. No refs, no memo, no context, no custom hooks —
nothing else was needed."*

**Q51. What are the Rules of Hooks and why do they exist?**
**BETTER:** *"Only call hooks at the top level of a component, never inside a
condition or loop. React tracks hooks by call order, not by name — first
`useState` is slot zero, second is slot one. A conditional call would shift every
later hook to the wrong slot and your state would silently swap. My `Stats`
component shows the correct shape: both hooks first, then `if (!stats) return
null`. And I have `react/rules-of-hooks` set to error in my oxlint config."*

**Q52. What is `useCallback` and why do you need it?**
**BETTER:** See §3.8 — the infinite-loop trace. This is the strongest hooks answer
you have; learn it properly.
**FOLLOW-UP:** *Why not just drop `refresh` from the deps array?* → That hides the
dependency instead of fixing it. If `refresh` ever captured a prop or state value,
the effect would silently use a stale copy. `useCallback` keeps the dependency
honest.

**Q53. Do you use `useMemo`? Why not?**
**BETTER:** *"No. `useMemo` caches an expensive computed value between renders. My
derived values are a reduce and a filter over arrays of maybe a few dozen items —
memoising those would cost more in complexity than it saves, and memoisation isn't
free either. I'd reach for it if a computation were genuinely expensive or if a
derived object were being passed as a prop to a memoised child."*

**Q54. Do you use `useRef` or `useContext`?**
**BETTER:** *"Neither. `useRef` is for holding a mutable value that shouldn't
trigger re-renders, or for direct DOM access — I have no direct DOM access outside
the mount point. `useContext` solves prop-drilling, and my tree is one level deep
with three props, so there's nothing to drill."*

**Q55. Have you written a custom hook?**
**BETTER:** *"No, and I'd be straight about that. The natural candidate is
`usePolling(fn, interval)` — I repeat the same effect-plus-setInterval-plus-
clearInterval shape three times, in `Health`, `Stats` and `App`. Extracting it
would remove genuine duplication. I didn't because three copies of five lines
didn't feel worth an abstraction yet, but it's the first refactor I'd do."*

## useEffect

**Q56. What is `useEffect` and when does it run?**
**BETTER:** *"It runs side effects — anything that isn't rendering. It fires after
React has rendered and committed to the DOM, not during. Rendering has to be pure,
so network calls and timers go in effects. I have four: three polls and a session
restore."*

**Q57. Explain the dependency array.**
**BETTER:** *"It controls when the effect re-runs. Empty means once on mount — my
health poll and session restore. With dependencies it re-runs when they change —
my orders poll depends on `[refresh]`. Omitting the array entirely means every
render, which is the classic infinite loop when the effect also sets state. I never
omit it."*

**Q58. What is the cleanup function?**
**BETTER:** *"The function returned from the effect. React calls it before
re-running the effect and when the component unmounts. Mine call `clearInterval`.
It's load-bearing in my app: `Stats` unmounts every time you switch away from the
ops role, and without cleanup its six-second poll would keep firing forever against
a component that no longer exists — switch roles ten times and you'd have ten
orphaned timers."*

**Q59. Trace what happens between mount and the first data appearing.**
**BETTER:** *"First render happens with `orders` as an empty array, so the user
briefly sees 'No orders yet.' React commits that to the DOM. Then the effect runs
and fires `Promise.all` for orders and riders. The responses come back, I call
`setOrders` and `setRiders`, React re-renders, diffs, and patches in the rows and
counts. That empty first render isn't a bug — it's a direct consequence of effects
running after render, which is why initial state values are what the user sees
first."*

**Q60. Why does your effect run twice in development?**
**BETTER:** *"StrictMode. React deliberately mounts, unmounts and remounts once in
development to surface effects that don't clean up. Mine survive it because they
clear their intervals. It doesn't happen in production."*

**Q61. Why is your polling in `useEffect` rather than just called at the top of the component?**
**BETTER:** *"Because the component function runs on every render. A fetch at the
top level would fire on every render, and since the response sets state, that's an
infinite loop. Effects run after the commit and only when their dependencies
change, which is exactly the control I need."*

## Events

**Q62. What events does your app handle?**
**BETTER:** *"Just two: `onClick` on every button, and `onChange` on the two login
inputs. React wraps native events in a synthetic event system for consistency
across browsers."*

**Q63. What is `e.target.value`?**
**BETTER:** *"`e` is the synthetic event, `e.target` is the element that fired it —
the input — and `.value` is its current text. `onChange={(e) => setEmail(e.target.value)}`
fires on every keystroke and stores the text in state."*

**Q64. Do you use `preventDefault`?**
**BETTER:** See §3.10 — the answer that turns the gap into a strength.

**Q65. Trace a click end to end.**
**BETTER:** Use the Dispatch trace from §3.10, all thirteen steps.

## Forms

**Q66. What's a controlled component?**
**BETTER:** *"An input whose value comes from React state and whose `onChange`
writes back, so state is the single source of truth. Both my login inputs are
controlled. The proof it's genuinely controlled is the demo role switcher —
clicking the 'rider' chip calls `setEmail` and `setPassword`, and the input boxes
visibly update, without touching the DOM. With an uncontrolled input I'd need a ref
and a manual DOM write."*

**Q67. Controlled vs uncontrolled — which is better?**
**BETTER:** *"Controlled is the default because it makes validation, conditional
disabling and programmatic updates straightforward. Uncontrolled is lighter and can
be better for very large forms, where re-rendering on every keystroke costs
something — that's what React Hook Form leans on. My forms are two fields, so
controlled is obviously right."*

**Q68. How do you validate input?**
**BETTER:** *"I don't, on the client — and that's a real gap I'd own. The server
does it properly: Pydantic enforces email format and a minimum eight-character
password, returning 422. The direction matters more than the gap though: client
validation is a UX convenience and can never be a security control, because anyone
can hit the API with curl. So the server has to validate regardless. What I'm
missing is the fast feedback loop, and I'd add a simple required-field check."*

## API Calls

**Q69. How does your frontend talk to the backend?**
**BETTER:** *"Every call goes through one function — `request()` in `api.js` —
wrapping the browser's native `fetch`. It builds headers, attaches the bearer
token, stringifies the body, parses the response, checks the status and either
returns data or throws. On top of that there's an `api` object of ten thin named
wrappers like `api.listOrders()` and `api.setStatus(id, status)`, so components
never see a URL."*
**FOLLOW-UP:** *Why centralise?* → The token is attached in exactly one place, so
no endpoint can forget it, and error handling is uniform.

**Q70. Does `fetch` throw on a 404?**
**BETTER:** *"No — that's the gotcha. `fetch` only rejects on a network failure. A
404 or a 500 is a successfully completed fetch with `ok` set to false, so you have
to check `res.ok` yourself. My wrapper does, and throws an Error carrying both the
status code and the parsed body, so callers can branch on `e.status` — `Stats` uses
that to silently ignore an expected 403."*

**Q71. How do you handle errors from the API?**
**BETTER:** *"My backend emits three different error shapes — `{error, message}`
from the custom exception handler, `{detail}` from FastAPI's HTTPException, and
`{error}` from the rate limiter. `request()` flattens all three with a fallback
chain into one readable message, wraps it in an Error with `.status` and `.data`
attached, and throws. Every handler catches and calls `say(e.message, "err")`,
which renders a red line in the activity panel."*

**Q72. What's `Promise.all` doing in your refresh?**
**BETTER:** *"Firing the orders and riders requests in parallel rather than
sequentially — one round trip instead of two. The caveat is that `Promise.all`
rejects as soon as either does, so a failing riders call loses the orders result
too. `Promise.allSettled` would give me both independently. They come from the same
API so they generally fail together, but it's a conscious trade-off."*

**Q73. What is the Idempotency-Key header doing?**
**BETTER:** Use Flow 3 from §5.5. This is your most distinctive answer.
**FOLLOW-UP:** *Why does the client need to know it was a replay?* → So the UI can
tell the truth. Without the `Idempotent-Replay` header the second click would look
identical to the first, and the user would assume a second order was created.

**Q74. Why PATCH and not PUT for the status update?**
**BETTER:** *"I send only `{status: "PICKED_UP"}`, not the whole order. PUT means
replace the resource with this representation; PATCH means apply this partial
change. PATCH is the accurate verb."*

**Q75. What HTTP status codes does your app deal with?**
**BETTER:** *"200 and 201 on success; 400 for an illegal state transition; 401
when there's no valid token; 403 when a role isn't permitted; 404 for a missing
order or nothing pending; 409 for a duplicate email or no available rider; 422 for
Pydantic validation; 429 from the rate limiter; and 503 from `/ready` when a
dependency is down — that last one my health pills render as a per-dependency
breakdown."*

**Q76. Explain 401 vs 403 using your app.**
**BETTER:** *"401 is 'I don't know who you are' — no token, or an expired one. 403
is 'I know exactly who you are and you may not do this.' Signed out, dispatch gives
401. Signed in as a customer, the same call gives 403 from `require_ops`. My
frontend uses that distinction: `Stats` checks `e.status !== 403` so an expected
permission denial doesn't spam the activity log."*

## async/await

**Q77. What is a Promise?**
**BETTER:** *"An object representing a value that isn't ready yet — it either
fulfils with a value or rejects with an error. `fetch` returns one immediately,
before any response arrives. I use both styles: `.then()/.catch()` inside my
polling effects, and `async`/`await` in the click handlers."*

**Q78. What do `async` and `await` actually do?**
**BETTER:** *"`async` marks a function as returning a Promise and allows `await`
inside it. `await` pauses that function until the Promise settles, then continues
with the value — but it doesn't block the browser. The page stays interactive and
my other timers keep firing. It's the same asynchronous behaviour as callbacks,
written so it reads top to bottom."*

**Q79. Why `try/catch/finally` in every handler?**
**BETTER:** *"`try` because an awaited call can throw — a 403, a bad password, the
network dropping. `catch` turns that into a visible red line rather than a silent
failure or an unhandled rejection. And `finally` is the important one:
`setBusy(false)` lives there, so the buttons re-enable whether the call succeeded
or failed. If I reset `busy` at the end of the try block instead, one failed
request would leave the UI permanently disabled."*

**Q80. What happens in your app if the API is slow? Or fails entirely?**
**BETTER:** *"If it's slow: the action buttons stay disabled because `busy` is
true, so the user gets feedback and can't double-submit — but the lists just show
stale data, because I have no per-list loading indicator and no request timeout.
A hung request stays pending forever, since I don't use an `AbortController`. If
it fails entirely: the health pills go red within five seconds — that path is
handled well, because the catch falls back to `{api: "unreachable"}` when there's
no response body at all. But the four-second poll swallows its errors silently, so
the lists just freeze at their last known values. The fix I'd make first is a
consecutive-failure counter driving a single 'connection lost' banner, plus a
timeout via AbortController."*

---

## The Top 30 Questions — Two Versions Each

**Version A** for a casual, in-passing question. **Version B** for a real
discussion. Speak them, don't recite them.

**1. What's your frontend built with?**
**A:** *"React 19 with Vite, plain JavaScript — deliberately minimal, just React
and React-DOM as dependencies."*
**B:** *"React 19 with Vite as the build tool, written in JSX rather than
TypeScript. It's about 700 lines across four files — four components, one CSS
file, one API module. What's notable is what isn't there: no router, no state
library, no UI framework. It's a single-view ops console, so a router would have
had nothing to route to, and my entire shared state is five `useState` calls in
the root component. I'd rather explain those choices than carry dependencies I
can't justify."*

**2. What does the app do?**
**A:** *"It's an ops console for a delivery dispatch system — live order and rider
counts, and controls to create, dispatch and advance orders."*
**B:** *"It's the operator's view onto a delivery dispatch backend. It polls for
orders and riders every few seconds and shows counts by status plus how many
riders are free. An operator can create orders, onboard riders, dispatch the next
pending order to a nearby rider, and move orders through their state machine. Two
things are deliberately made visible: the permission model — you can switch between
ops, rider and customer accounts and see real 403s come back — and idempotency,
where clicking 'add order' twice with a fixed key gives you one order and a
'REPLAYED' message."*

**3. Why React and not plain JavaScript?**
**A:** *"The UI re-renders constantly from polled data — React means I update state
and everything derived from it follows, instead of me hand-writing DOM updates."*
**B:** *"The console is driven by three polls on four-, five- and six-second
timers. Every cycle can change the orders list, four status counters, the free-rider
count and the per-row action buttons. In vanilla JS I'd write DOM update code for
each of those, and the classic bug is updating your data and forgetting one of the
places that displays it. In React those are all computed from the same `orders`
state, so `setOrders(...)` updates them together and they can't drift. Could I have
built this without React? Honestly, yes — it's 700 lines. But I'd have hand-rolled
a rendering layer, and that's just a worse React."*

**4. What is state?**
**A:** *"Data that redraws the UI when it changes — I call a setter, React
re-renders."*
**B:** *"Data a component owns that should update the screen when it changes. The
reason it can't be a normal variable is twofold: React has no idea a plain variable
changed, and the variable resets every render because the component function runs
again from the top. `useState` keeps the value outside the function and gives me a
setter that schedules a re-render. In my app that's the user, orders, riders, the
activity log and a busy flag."*

**5. Props vs state?**
**A:** *"Props come from the parent and are read-only; state is owned locally and
can change."*
**B:** *"Props are inputs passed down from a parent — read-only. State is owned by
the component and changing it triggers a re-render. `Auth` shows both: `user` is a
prop, because `App` also needs it for the ops checks and for deciding whether to
mount `Stats`; but the email and password fields are local state, because nothing
outside `Auth` cares until the login succeeds. The rule I applied is keep state as
low as possible and lift it only when a second component needs it."*

**6. How does a child update its parent?**
**A:** *"The parent passes a function down, and the child calls it."*
**B:** *"Props are one-way, so a child can't reach up. Instead the parent hands
down a function. `App` passes `onUser={setUser}` to `Auth`, and when the login
succeeds `Auth` calls `onUser(user)`. `App`'s state updates and the whole tree
re-renders with the new user. The child never knows it's calling `setUser` — it
just received something called `onUser` — which keeps it decoupled."*

**7. What is `useEffect` for?**
**A:** *"Side effects — anything that isn't rendering. Mine are three API polls and
a session restore."*
**B:** *"Rendering has to be pure, so anything that touches the outside world goes
in an effect, and effects run after React has committed to the DOM. I have four:
one restores the session from a stored token on mount, and three set up polling
intervals. The dependency array controls re-runs, and each polling effect returns a
cleanup that clears its interval — which matters because `Stats` unmounts whenever
you leave the ops role, and without cleanup its timer would keep firing forever."*

**8. What does the dependency array do?**
**A:** *"Controls when the effect re-runs — empty means once on mount."*
**B:** *"It tells React which values the effect depends on. Empty means run once
after mount. With values listed, it re-runs whenever any of them change. Omitting
the array entirely means it runs after every render, which is the classic infinite
loop if the effect sets state. Mine are either empty or list a memoised function —
and that memoisation is exactly why `useCallback` is in the code."*

**9. Why did you use `useCallback`?**
**A:** *"So my polling effect's dependency stays stable — otherwise it would tear
down and restart the interval on every render."*
**B:** *"Functions are recreated on every render, so they're new objects each time.
My polling effect lists `refresh` as a dependency. Without memoisation, every render
gives `refresh` a new identity, so React tears down and re-runs the effect — and
since the effect fetches and sets state, that triggers another render, and it never
stops. Wrapping `refresh` in `useCallback` with an empty dependency array pins its
identity so the interval is created once. Same reason for `say`, because the `Stats`
effect depends on it. It isn't micro-optimisation — it's what makes the dependency
array correct."*

**10. Does `setState` update immediately?**
**A:** *"No — it schedules an update; the new value appears in the next render."*
**B:** *"No. It schedules a re-render. If I call `setBusy(true)` and read `busy` on
the very next line, it's still false — `busy` is a const bound to the current
render. React also batches multiple setter calls in one event into a single
re-render. And when the new value depends on the old one, you need the functional
form — my activity logger uses `setLog(l => [entry, ...l])` so concurrent updates
can't clobber each other."*

**11. Why not mutate state directly?**
**A:** *"React compares references — mutating in place leaves the reference
unchanged, so it may skip the re-render."*
**B:** *"React decides whether to re-render by comparing references, not by deep
equality. If I push into an existing array the reference is identical, so React can
correctly conclude nothing changed and skip the update. That's why my logger builds
a new array with spread instead of pushing. The subtler case is
`[...orders].reverse()` in my orders panel — `reverse` mutates the array it's called
on, so without copying first I'd be mutating React state in place during render."*

**12. Why do lists need a `key`?**
**A:** *"It gives each item a stable identity so React can match items across
renders instead of comparing by position."*
**B:** *"Without keys React compares by position, so inserting at the front makes it
think every row changed. With keys it matches by identity and only touches what
actually moved. My orders list uses the database id, which is ideal. My activity log
uses the array index, which is the anti-pattern — and worse than usual because I
prepend, so every index shifts on each new entry. It's harmless there because the
rows are stateless text, but the correct key would be a timestamp-plus-message
composite, and I'd fix it the moment those rows had any internal state."*

**13. What's a controlled component?**
**A:** *"An input whose value comes from state and whose onChange writes back —
state is the source of truth."*
**B:** *"The input renders from React state and every change writes back, so the
DOM never holds independent data. Both my login inputs work that way. The clearest
proof is my demo role switcher: clicking the 'rider' chip calls `setEmail` and
`setPassword`, and the input boxes update on screen without any DOM manipulation.
With uncontrolled inputs I'd need refs and manual writes to achieve the same
thing."*

**14. `fetch` or Axios?**
**A:** *"`fetch` — Axios' conveniences were about fifteen lines I wrote once."*
**B:** *"`fetch`, because it's built into the browser. What Axios adds is automatic
JSON parsing, throwing on non-2xx, and interceptors — and that's roughly fifteen
lines that I wrote once in my `request()` wrapper. For ten endpoints it wasn't
worth a dependency. The two things I genuinely gave up are timeouts and
cancellation, which `fetch` needs an `AbortController` for and I don't use one. If
the API were slower or flakier, that would change the maths."*

**15. Does `fetch` throw on a 404?**
**A:** *"No — only on a network failure. You have to check `res.ok` yourself."*
**B:** *"No, and it catches people out. A 404 or 500 is a successfully completed
HTTP exchange, so the promise fulfils with `ok` set to false. `fetch` only rejects
when the request never completed — DNS failure, connection refused. My wrapper
checks `res.ok` explicitly and throws an Error with the status and parsed body
attached, so callers can branch on `e.status`. `Stats` uses that to swallow an
expected 403 rather than logging it."*

**16. How do you store the auth token?**
**A:** *"JWT in localStorage, mirrored to a module variable so every request can
attach it."*
**B:** *"It's a JWT in localStorage under `diq_token`, and `api.js` also keeps it in
a module-level variable so `request()` doesn't hit storage on every call. The
localStorage copy is what makes a page refresh keep you signed in — on mount, an
effect reads the token and calls `/auth/me` to rehydrate the user. If that returns
401 because the token expired, the catch clears it. Modules evaluate once, so that
variable is effectively a singleton shared by every importer."*

**17. Is localStorage safe for a token?**
**A:** *"No — any JavaScript on the page can read it, so an XSS is a token theft.
An httpOnly cookie is safer, at the cost of needing CSRF protection."*
**B:** *"It's the pragmatic choice, not the safe one. Anything in localStorage is
readable by any script on the page, including a compromised npm dependency — so one
XSS and the token is gone. The stronger default is an httpOnly cookie, which
JavaScript can't touch at all. But that isn't free: cookies go out automatically on
every request to the origin, which opens CSRF, so you need SameSite and probably a
CSRF token. I chose localStorage because it's simple and fits a pure bearer-token
API for a demo console. For real user data I'd move to httpOnly cookies with CSRF
protection and add short-lived tokens with a refresh flow."*

**18. 401 vs 403?**
**A:** *"401 means I don't know who you are; 403 means I know and you're not
allowed."*
**B:** *"401 is authentication — no token, or an invalid or expired one. 403 is
authorization — you're authenticated and still not permitted. My app demonstrates
both: signed out, dispatch returns 401; signed in as a customer, the same call
returns 403 from the `require_ops` dependency. The frontend uses the distinction
too — `Stats` checks `e.status !== 403` so an expected permission denial doesn't
spam the activity log."*

**19. Can someone bypass your frontend permission checks?**
**A:** *"Yes, trivially — and that's why the same checks exist on the server, which
is the actual boundary."*
**B:** *"Absolutely — remove the `disabled` attribute in devtools, or skip the
browser and use curl. The frontend check is a UX affordance: it greys out the
control and puts the reason in a tooltip so the user understands why. The security
boundary is entirely server-side — `require_ops` on dispatch and rider creation,
a router-level guard on `/admin`, and an actor guard on status changes that stops a
rider touching an order that isn't theirs. The console is actually built to
demonstrate that: switch to the customer role and you get a real 403 rendered in the
activity log."*

**20. How do you handle loading states?**
**A:** *"A `busy` flag disables the action buttons during a request, and it's reset
in `finally`."*
**B:** *"Every action follows the same shape: set busy, try the call, catch and log
the error, reset busy in `finally`. `finally` is the load-bearing part — if I reset
at the end of the try block, one failed request would leave the buttons permanently
disabled. `Health` has a separate loading state, showing 'checking…' until the first
response. Where I'm weak is the lists: on first load they show 'No orders yet.',
which is indistinguishable from a genuinely empty database. A skeleton or a
distinct loading state would be the fix."*

**21. How do you handle errors?**
**A:** *"My HTTP wrapper throws an Error with the status and body attached, and
handlers log it as a red line in the activity panel."*
**B:** *"It's centralised. `request()` checks `res.ok`, and my backend has three
different error shapes — `{error, message}`, `{detail}`, and `{error}` from the rate
limiter — so it flattens them with a fallback chain into one message, attaches the
status code and parsed body to an Error, and throws. Every handler catches and calls
`say(message, "err")`, which prepends a timestamped red line to the activity panel.
Two refinements: `Stats` suppresses expected 403s, and the auth handler appends
'run: python -m scripts.seed_users' when login fails, because that's usually the
real cause in a fresh environment."*

**22. What happens on a page refresh?**
**A:** *"React state is wiped, but the token in localStorage survives, so an effect
re-fetches the user and you stay signed in."*
**B:** *"All React state is destroyed. But `api.js` reads the token from
localStorage as its very first statement when the module evaluates, so it's back in
memory before anything renders. Then a mount effect in `App` checks for it and calls
`/auth/me` to rehydrate the user object. There's a brief flash of the signed-out UI
because effects run after the first render — that's inherent to the model. And if
the token has expired the server returns 401 and the catch clears it, so you land in
a clean signed-out state rather than a broken half-authenticated one."*

**23. Why is there no router?**
**A:** *"It's a single view — the different 'screens' are conditional renders driven
by state."*
**B:** *"There's one URL and nothing to route to. What looks like different screens
— signed out versus signed in, ops versus customer — are conditional renders on
state. The part I'd add if asked how I'd introduce routing is the server side:
FastAPI currently serves `index.html` only at the mount root, so refreshing on a
sub-route would 404. I'd need a catch-all returning index.html for unknown paths
without shadowing the API routes, which is the bit people forget."*

**24. Why no Redux or Context?**
**A:** *"The tree is one level deep and shared state is five `useState` calls —
there's nothing to drill and nothing to coordinate."*
**B:** *"Context solves prop-drilling, and I pass three props one level down.
Redux coordinates state across distant parts of a large app; my entire shared state
is five `useState` calls in the root. Either would be more code and more indirection
for no problem solved. I can name the trigger for changing my mind though: a second
view, or a component needing `user` three-plus levels down — Context for the auth
object first, and a store only if I had genuinely complex cross-cutting state with
lots of derived data."*

**25. Why is everything in one file?**
**A:** *"Four components and 439 lines — folders would have had more files than
code. The split points are obvious when it grows."*
**B:** See §5.2.

**26. What's the idempotency demo?**
**A:** *"Clicking 'add order' twice with a fixed key creates one order — the second
response is replayed from Redis, and the UI says so."*
**B:** Use Flow 3 from §5.5.

**27. What is the virtual DOM?**
**A:** *"An in-memory copy of the UI tree. React diffs the new one against the old
and patches only what changed."*
**B:** *"React builds a lightweight tree in memory rather than touching the real DOM
directly. On a state change it builds a new tree, diffs, and applies the minimal set
of real changes. Real DOM operations are expensive, in-memory comparison isn't. My
orders poll runs every four seconds and usually returns nearly identical data —
React works out that only the count and one row changed and leaves the rest alone,
which is why the panel doesn't flicker or lose scroll position on every poll."*

**28. How does your frontend find the backend?**
**A:** *"Same origin — every path is relative. Vite proxies in dev, FastAPI serves
the bundle in production."*
**B:** *"My base URL is an empty string, so every request is a relative path like
`/orders`. In development Vite proxies those to port 8000; in production FastAPI
serves the built bundle itself, so the HTML and the API come from the same server.
That means no CORS configuration anywhere and no environment variable pointing at a
per-environment backend URL — one artifact, one deploy. The trade-off is that the
frontend can't be deployed to a CDN independently, which for an internal ops console
is the right call but wouldn't be for a public app."*

**29. What would you improve?**
**A:** *"Split `App.jsx` into components, extract a `usePolling` hook, add a real
`<form>` for login, and fix the index keys on the log."*
**B:** *"Four things, in order. First, there's a genuine bug: the orders list tries
to render a rider badge, but the backend's response schema doesn't include
`rider_id`, so it never shows — a one-line fix on the Pydantic model. Second, the
login should be a real `<form>` with `onSubmit` and `preventDefault`, because right
now Enter doesn't submit. Third, I repeat the same effect-plus-interval-plus-cleanup
pattern three times and it should be a `usePolling` custom hook. Fourth, the
background poll swallows errors silently — I'd add a consecutive-failure counter
driving a single connection banner instead of nothing."*

**30. What was the hardest part?**
**A:** *"Getting the polling effects right — the dependency array and `useCallback`
interaction is subtle, and getting it wrong is an infinite loop."*
**B:** *"The polling. The naive version — define `refresh`, use it in an effect,
list it as a dependency — is an infinite loop, because the function is recreated
every render, which re-runs the effect, which sets state, which re-renders. Working
out that the fix was `useCallback` rather than just deleting the dependency was the
thing that made hooks click for me. The related lesson was cleanup: `Stats` unmounts
every time you leave the ops role, and without `clearInterval` in the effect's
return, each role switch would leak a timer polling a component that no longer
exists."*

---

# How I Should Explain My Frontend In An Interview

Speak these. Don't recite them word for word — learn the shape and the facts.

## 20-second answer

> "The frontend is a single-page ops console in React 19, built with Vite. It's
> deliberately small — four components, about seven hundred lines, no router and
> no state library, because it's one screen. It polls the FastAPI backend every
> few seconds for orders and riders, and lets an operator create orders, onboard
> riders and dispatch work. The interesting part is that it makes two backend
> behaviours visible: role-based permissions, and idempotent retries."

## 1-minute answer

> "It's the operator's view onto the dispatch backend. React 19 with Vite, plain
> JavaScript, and only two runtime dependencies — React and React-DOM. No router,
> no Redux, no UI framework, because it's a single view with four components.
>
> `App` is the root and owns the shared state: the signed-in user, orders, riders
> and an activity log. Three polling intervals keep it live — orders and riders
> every four seconds, a dependency health check every five, and ops-only stats
> every six — each set up in a `useEffect` with a `clearInterval` cleanup.
>
> Every network call goes through one `request()` function that wraps `fetch`. It
> attaches the JWT bearer token, optionally an idempotency key, and normalises
> three different backend error shapes into a single Error carrying the HTTP
> status. Handlers catch that and write a line into the activity panel, so
> failures are visible rather than silent.
>
> What I'd point at is the role model. You can switch between ops, rider and
> customer accounts, and restricted controls grey out with a tooltip explaining
> why — but that's only UX. The server enforces it, and the console is built to
> show that a customer gets a real 403."

## 2-minute answer

> "It's an ops console for a delivery dispatch system — React 19 with Vite,
> written in JSX, roughly seven hundred lines across four files. Two runtime
> dependencies. No router, no state library, no UI kit, and I'm happy to defend
> each of those.
>
> **Structure.** `main.jsx` mounts `<App/>` into an empty div. `App` owns five
> pieces of state — user, orders, riders, an activity log and a busy flag — and
> renders three children: `Health`, which polls the readiness endpoint and shows a
> pill per dependency; `Auth`, which handles sign-in; and `Stats`, an ops-only
> metrics strip that's conditionally rendered, so it isn't just hidden for
> non-ops — it never mounts and never polls.
>
> **State.** All local `useState`, lifted to `App` when more than one component
> needs it. `user` lives in `App` because `Auth`, the ops checks and the `Stats`
> mounting decision all depend on it; `Auth` passes the signed-in user back up
> through an `onUser` callback prop. `email` and `password` stay local to `Auth`
> because nothing else cares until submit.
>
> **Data flow.** Three `setInterval` polls, each in a `useEffect` with cleanup.
> The refresh function is wrapped in `useCallback` — without that, the effect's
> dependency changes every render, which restarts the interval, which sets state,
> which re-renders, and it never stops. That was the subtlest thing to get right.
>
> **API layer.** One `request()` function over `fetch`. It builds headers, checks
> `res.ok` — because `fetch` doesn't throw on a 404 — and throws an Error carrying
> the status and parsed body, so callers can branch on it. The token lives in a
> module variable mirrored to localStorage, which is what makes a page refresh
> keep you signed in.
>
> **The two demos.** Role permissions: switch to customer, and the ops controls
> disable with a reason, and a real 403 comes back if you call the endpoint
> anyway. Idempotency: there are two 'add order' buttons, and the second sends a
> fixed Idempotency-Key. Click it twice and only one order exists — the second
> response is replayed from Redis with an `Idempotent-Replay` header, which my
> wrapper surfaces so the UI can print 'REPLAYED'.
>
> **What I'd change.** The login should be a real `<form>` so Enter submits, the
> activity log uses index keys on a prepended list, and there's a dead conditional
> rendering a rider badge that never shows because the backend's response schema
> doesn't include `rider_id`."

## 5-minute technical walkthrough

Open the files as you talk.

**1. Start with `index.html` (15 s).** *"One empty div with `id="root"` and a
module script. Nothing the user sees is in the HTML — React builds it all at
runtime. That's what makes it a single-page app."*

**2. `main.jsx` (20 s).** *"Nine lines. `createRoot` on that div, render `<App/>`
inside `StrictMode`. Worth noting the two packages: `react` is the component model
and hooks, `react-dom` is the browser renderer — that split is why React Native can
exist. And StrictMode double-mounts effects in development, which matters to me
specifically because I run three intervals; my cleanups are what make that
harmless."*

**3. `App.jsx`, the `App` component (90 s).** *"Five `useState` calls at the top —
user, orders, riders, log, busy. Then two `useCallback`s: `say`, which prepends a
timestamped entry to the activity log capped at fourteen entries, and `refresh`,
which fetches orders and riders in parallel with `Promise.all`.*
*Two effects. The first has an empty dependency array and restores the session — if
there's a stored token, call `/auth/me` and set the user; on 401, clear the token.
That's what survives a page refresh. The second sets up the four-second poll and
returns a cleanup that clears the interval.*
*Then four handlers, all the same shape: set busy, try, catch and log the error,
reset busy in `finally`. `finally` matters — resetting inside the try would leave
the UI stuck disabled after any failure.*
*And three derived values — `isOps` from the user, `counts` reduced from orders,
`free` filtered from riders. They're computed during render rather than stored,
so they can't go stale."*

**4. The JSX (60 s).** *"`Health` and `Auth` always render; `Stats` is behind
`{user?.role === "ops" && ...}`, so for a customer it isn't hidden — it's never
mounted, so it never polls. The counter tiles map over a status array. The orders
panel is the interesting one: `[...orders].reverse()` — copied first, because
`reverse` mutates in place and that's React state. Each row keys on the database
id. Inside each row, a nested map over `STATUS_FLOW[order.status]` produces the
action buttons, so an `ASSIGNED` order gets two buttons and a `DELIVERED` order
gets none. The UI is a projection of a lookup table rather than a chain of
conditionals."*

**5. `api.js` (60 s).** *"One function does all HTTP. Headers built conditionally —
`Content-Type` only with a body, `Authorization` only when there's a token,
`Idempotency-Key` only when the caller passes one. Then `fetch` against a relative
path, because the base URL is an empty string — Vite proxies in dev, FastAPI serves
the bundle in prod, so there's no CORS anywhere.*
*Response handling is deliberately defensive: read as text, parse inside a
try/catch, so a proxy returning an HTML error page doesn't throw and lose the body.
Then check `res.ok`, because `fetch` doesn't reject on a 404. My backend has three
error shapes, so there's a fallback chain flattening them into one message, wrapped
in an Error with the status and body attached. And the return value includes
`replayed`, read from a response header — that's what powers the idempotency
demo."*

**6. Close with the trade-offs (45 s).** *"Things I'd flag honestly: it's all in
one file, which is fine at four components but the split points are already obvious.
The login isn't a real `<form>`, so Enter doesn't submit. The activity log uses index
keys while prepending. The background poll swallows errors silently. And there's a
dead conditional trying to render a rider id that the backend's response schema
doesn't actually include — I found that reading the Pydantic model against the JSX."*

---

# Why Did You Use React?

Do not give a marketing answer. Tie it to your architecture.

> **"Three concrete reasons, all specific to this app.**
>
> **One — the UI is continuously re-rendered from polled data.** Three intervals
> at four, five and six seconds. Every cycle can change the orders list, four
> status counters, the free-rider count and which action buttons each row shows.
> In vanilla JS, each of those is a piece of DOM update code I have to write and
> keep in sync. In React they're all derived from the same `orders` and `riders`
> state, so one `setOrders(...)` updates them together and they cannot drift apart.
> That whole class of bug — data updated, one part of the DOM forgotten — just
> doesn't arise.
>
> **Two — the UI has to change shape based on identity.** Signed out versus signed
> in versus ops versus customer changes which controls are enabled, whether the
> stats strip exists at all, and what the auth bar shows. Expressing that as
> `{user?.role === "ops" && <Stats/>}` is one line, and it does the right thing on
> both sides — mounting the component *and* starting its poll, or neither. Doing
> that imperatively means remembering to tear down the timer when you hide the
> element, and that's exactly the kind of thing people forget.
>
> **Three — components let me isolate the polling.** `Health` is twenty-eight
> lines and completely self-contained: its own state, its own interval, its own
> cleanup. Nothing else in the app can touch it, and I can reason about it without
> holding the rest of the console in my head.
>
> **What React cost me:** a build step, a compile stage for JSX, and about seventy
> kilobytes of runtime. For an internal tool that's a fine trade. For a public
> marketing page it wouldn't be."

---

# React vs Vanilla JavaScript

## The core difference, with your own code

**Vanilla JS — imperative.** You would write something like this (this is *not* in
your project):

```js
async function refresh() {
  const orders = await (await fetch("/orders")).json();

  // now manually update EVERY place that displays order data:
  document.querySelector(".count").textContent = orders.length;

  const counts = {};
  orders.forEach(o => counts[o.status] = (counts[o.status] || 0) + 1);
  document.querySelector("#pending .n").textContent  = counts.PENDING  || 0;
  document.querySelector("#assigned .n").textContent = counts.ASSIGNED || 0;
  // ... two more ...

  const rows = document.querySelector(".rows");
  rows.innerHTML = "";                      // destroys scroll position
  for (const o of orders.slice().reverse()) {
    const div = document.createElement("div");
    div.className = "row";
    // ... build every span by hand ...
    // ... attach a click listener to every status button ...
    rows.appendChild(div);
  }
}
```

**React — declarative.** Your actual code:

```js
setOrders(o.data);
```

Plus a description of what the UI looks like for any `orders` value. That's it.

## What you actually gain

| | Vanilla | React (yours) |
|---|---|---|
| Update the count | manual `textContent` | `{orders.length}` — automatic |
| Update four tiles | four manual writes | derived from `counts` |
| Rebuild rows | `innerHTML = ""` then rebuild | `.map()` with keys — React patches |
| Scroll position | lost on every rebuild | preserved (keys match) |
| Event listeners | re-attach on every rebuild | declared in JSX, handled by React |
| Data/UI drift | very easy | structurally impossible |

🔴 **The `innerHTML = ""` point is the strongest one to make.** Your orders panel
has `max-height: 460px; overflow-y: auto` — it scrolls. A vanilla rebuild every
four seconds would reset that scroll position every four seconds, making the panel
unusable. React's keyed diffing leaves untouched rows alone, so scroll survives.
That's a concrete, user-visible consequence, not a theoretical one.

## "Could this application have been built without React?"

Give a balanced answer — interviewers are testing whether you're a fanatic.

> **"Yes, genuinely. It's seven hundred lines, one screen and ten endpoints —
> that's well within reach of vanilla JavaScript, and the bundle would be smaller
> with no build step.**
>
> **But I'd have ended up writing a worse React.** The moment you have data that
> updates on a timer and four different parts of the page derived from it, you
> either hand-write every DOM update — and eventually miss one — or you build a
> little render-on-state-change layer. That layer is React, just untested and
> undocumented.
>
> **The specific thing that would have bitten me** is the orders panel. It scrolls,
> and it refreshes every four seconds. The naive vanilla approach clears and
> rebuilds it, which resets the scroll position every four seconds. To avoid that
> I'd have to diff the list myself and only touch what changed — which is precisely
> what React's keyed reconciliation does for me.
>
> **Where vanilla would genuinely have won:** a smaller bundle, no build tooling,
> and no framework knowledge required to maintain it. If this were a static status
> page with no interaction, I'd have used plain JS or server-rendered HTML."

---

# Common Trick Questions

**What happens when state changes?**
React schedules a re-render, calls the component function again, builds a new
element tree, diffs it against the previous one, and applies the minimal set of
real DOM changes. It does *not* re-run the whole app or reload the page. Children
re-render too, unless memoised.

**Does `useState` update immediately?**
No. It schedules. Reading the variable on the next line gives the old value,
because it's a `const` bound to the current render. React also batches multiple
setter calls within one event into a single re-render.

**Why shouldn't we directly mutate state?**
React compares references, not deep contents. Mutating in place leaves the
reference identical, so React can correctly conclude nothing changed and skip the
re-render. Hence `[...orders].reverse()` rather than `orders.reverse()`.

**Why does `useEffect` sometimes run again?**
Because a value in its dependency array changed. In development, StrictMode also
mounts, unmounts and remounts once deliberately. If you *omit* the array it runs
after every render.

**Why are keys needed?**
So React can match list items by identity across renders instead of by position.
Without them, inserting at the front makes React think every item changed —
wasted DOM work, and lost internal state on stateful children. Keys must be
unique among siblings, and are **not** readable as a prop inside the component.

**Props vs state?** §3.5.

**Controlled vs uncontrolled?** §3.11.

**Why async/await instead of `.then()`?**
Same behaviour, better readability for sequential steps, and ordinary
`try/catch/finally` works. My login does three dependent steps in a row — register,
login, then `/auth/me` — which reads far better sequentially. I still use `.then()`
in the polling effects, where it's a single call.

**`fetch` vs Axios?** §4.6.

**localStorage vs sessionStorage?**
Both are readable by JavaScript. `localStorage` persists until cleared and is
shared across tabs; `sessionStorage` is per-tab and dies when the tab closes. I use
`localStorage` so a refresh — and a second tab — keeps you signed in.
`sessionStorage` would slightly reduce the window of exposure on a shared machine
but doesn't change the XSS story at all. Only an httpOnly cookie does that.

**Authentication vs authorization?**
Authentication is who you are — my login endpoint, bcrypt verification, JWT
issuance. Authorization is what you may do — `require_ops`, the router-level admin
guard, and the actor guard on status changes.

**401 vs 403?** §4.4.

**Frontend vs backend validation?**
Frontend validation is a UX convenience — fast feedback without a round trip.
Backend validation is the actual control, because anyone can call the API with
curl. Mine is entirely backend, via Pydantic. The gap is UX, not security.

**Why can't frontend security be trusted?**
Everything shipped to the browser is under the user's control — they can edit the
DOM, change variables in the console, or skip the browser entirely. So a
client-side check can only ever be a hint. In my app, disabling the dispatch button
is a hint; `require_ops` returning 403 is the control.

**What happens if the API is slow?**
Buttons stay disabled because `busy` is true, so the user gets feedback and can't
double-submit. But the lists show stale data with no indicator, and there's no
timeout — I don't use an `AbortController`, so a hung request stays pending
indefinitely.

**What happens if the API fails?**
The health pills go red within five seconds, including a fallback to
`{api: "unreachable"}` when there's no response body at all. Action failures show as
red lines in the activity log. But the four-second poll swallows errors silently, so
the lists just freeze — that's the gap I'd fix first.

**What happens if two people use the console at once?**
Both see each other's changes within four seconds, because everything is polled from
the server rather than held client-side. There's no optimistic update — I always
`refresh()` after a mutation rather than patching local state — which is slower to
feel but can't go out of sync.

---

# Things I Should NOT Say In An Interview

Every item below is verifiable from the repository in seconds. Claiming any of
them is a fast way to lose credibility.

## ❌ Never claim

| Don't say | Reality |
|---|---|
| "We use Redux / Zustand / MobX" | **No state library at all.** `package.json` has two runtime deps |
| "I used the Context API" | `createContext` and `useContext` appear **zero** times |
| "I set up React Router" / "protected routes" | **No router.** One view, one URL |
| "I used Axios" | Native `fetch` only |
| "React Query / SWR handles caching" | Neither is installed. Polling with `setInterval` |
| "Styled with Tailwind / MUI / Bootstrap / shadcn" | 204 lines of hand-written CSS |
| "It's written in TypeScript" | `.jsx`/`.js`. `@types/*` are editor hints; there is no `tsconfig.json` |
| "I wrote tests for the frontend" | **There is no test file in `frontend/`.** No Jest, Vitest, RTL, Cypress or Playwright |
| "I built custom hooks" | Zero. Only `useState`, `useEffect`, `useCallback` |
| "I used `useMemo`/`useRef`/`useReducer` for performance" | None appear |
| "Real-time updates / WebSockets / SSE" | **Polling** on 4 s / 5 s / 6 s timers |
| "Fully responsive / mobile-first" | **One** media query at 900px |
| "I implemented complex state management" | Five `useState` calls in the root plus lifting |
| "Form validation on the client" | None. Pydantic does it server-side |
| "I used a charting library" | No chart library. The stats strip is plain numbers |
| "I used an icon library" | No icon library. The status dots are styled `<i>` elements |
| "Code splitting / lazy loading / Suspense" | None |
| "Server-side rendering / Next.js" | Client-rendered SPA served as static files |
| "I made it accessible / did an a11y audit" | No ARIA attributes, no keyboard handling, no audit |
| "Optimistic UI updates" | Always `refresh()` after a mutation — no optimistic patching |
| "I handled auth token refresh" | No refresh tokens. A token expires and you re-login |
| "Error boundaries catch render failures" | No error boundary anywhere |

## ✅ Safe to claim — all verifiable

- React 19 function components and JSX
- Hooks: `useState`, `useEffect` (with dependency arrays **and cleanup**), `useCallback`
- Props, including a **child-to-parent callback** (`onUser`) and **lifting state up**
- Conditional rendering with ternaries, `&&` and early `return null`
- List rendering with `.map()` and keys, including a **nested** map
- **Controlled inputs** with `value` + `onChange`
- A hand-written `fetch` wrapper with centralised headers, status checking and
  error normalisation across three backend error shapes
- **JWT bearer auth** with localStorage persistence and session restore on mount
- **Role-based UI** (ops / rider / customer) mirroring server-side enforcement
- **Polling** with `setInterval` and correct `clearInterval` cleanup
- Surfacing an **idempotency-key replay** through a response header
- Derived state (`isOps`, `counts`, `free`) computed during render
- CSS custom properties as design tokens, Flexbox, Grid, one breakpoint
- Vite build, dev proxy, and a **same-origin deployment served by FastAPI** — and
  the reason that means no CORS

## ⚠️ Say carefully

- **"I built the frontend."** True — but it's a 700-line console, so present it as
  a focused UI over a substantial backend, not as a large frontend project.
- **"I handled errors well."** Mostly true — but volunteer the silently swallowed
  poll errors before someone finds them.
- **"The UI enforces permissions."** ❌ Say: *"the UI reflects permissions; the
  server enforces them."* This distinction matters and interviewers listen for it.

---

# Areas Where An Interviewer Could Catch Me

Fourteen issues, each verified in the code. For each: what they'll ask, how to
answer, and the fix. **Volunteering these reads as judgement; being caught reads
as not knowing.**

### 1. 🔴 Dead code — the rider badge never renders

**The code** ([App.jsx:387](../frontend/src/App.jsx#L387)):
```jsx
{o.rider_id && <span className="rid">rider {o.rider_id}</span>}
```
**The problem:** your backend's `OrderResponse` schema
([app/schemas/order.py](../app/schemas/order.py)) declares only `id`,
`customer_id`, `value`, `status` and `created_at`. Pydantic serialises **only
declared fields**, so `rider_id` is never in the JSON — even though the database
column exists. `o.rider_id` is always `undefined`, so this never renders.
**THEY MAY ASK:** *"Where does an order show its rider?"* or *"What does this line
do?"*
**HOW TO ANSWER:** *"It doesn't do anything — and I'd rather tell you that than have
you find it. The Order model has a `rider_id` column, but the Pydantic response
schema doesn't declare it, so it's filtered out of the JSON. The JSX was written
against the database model rather than the API contract. It's a one-line fix on the
response schema, and it's a good example of why the API contract and the model
should be checked against each other."*
**FIX:** add `rider_id: int | None = None` to `OrderResponse`.

### 2. Index keys on a prepended list
**The code** ([App.jsx:408](../frontend/src/App.jsx#L408)): `key={i}` while `say()`
prepends.
**HOW TO ANSWER:** *"That's the anti-pattern, and worse than usual because I
prepend — every index shifts on each new entry, so React re-renders all fourteen
lines instead of inserting one. It's harmless here because the rows are stateless
text, but I'd use a timestamp-plus-message composite key, and I'd have to fix it the
moment those rows had any internal state."*

### 3. No `<form>` — Enter doesn't submit
**HOW TO ANSWER:** *"A real usability bug. Users expect Enter to submit a login. The
fix is wrapping it in `<form onSubmit={...}>` with `e.preventDefault()` and a
`type="submit"` button — which also gets me browser autofill and password-manager
support for free."*

### 4. JWT in localStorage
**HOW TO ANSWER:** see Q17's Version B. Name the attack, the alternative, and the
alternative's cost.

### 5. The background poll swallows every error
**The code** ([App.jsx:205-207](../frontend/src/App.jsx#L205-L207)): `catch {}` with
a comment.
**HOW TO ANSWER:** *"Deliberate but too blunt. The reasoning was that a failure every
four seconds would flood a fourteen-line log and bury real messages. But the effect
is that a sustained outage is invisible except through the health pills. The right
design is a consecutive-failure counter driving a single sticky 'connection lost'
banner — one signal, not zero and not sixty."*

### 6. `advance()` has no `busy` guard
**HOW TO ANSWER:** *"Inconsistent with my other three handlers, which all set busy.
Double-clicking a status button fires two PATCHes. The second usually fails with a
400 invalid-transition, so the backend saves me — but relying on that is luck, not
design. Per-row disabled state would be the proper fix, which also solves the next
problem."*

### 7. `busy` is a single global flag
**HOW TO ANSWER:** *"Any one action disables all of them. It's coarse — creating an
order shouldn't grey out dispatch. With more actions I'd track which operation is in
flight, something like `useState(null)` holding an action name, rather than a
boolean."*

### 8. Polling: no backoff, no visibility check
**HOW TO ANSWER:** *"Three timers running unconditionally. If the backend is down
they keep hammering it every four seconds with no backoff, and they keep polling
even when the tab is hidden. I'd add exponential backoff on consecutive failures and
pause on `document.hidden` via the Page Visibility API. The real answer at scale is
server-sent events or WebSockets so the server pushes rather than the client
asking."*

### 9. Everything in one 439-line file
**HOW TO ANSWER:** see §5.2 — defend with the trigger.

### 10. No error boundary
**HOW TO ANSWER:** *"If any component throws during render, the whole app unmounts
and the user gets a blank page. An error boundary around the main content would show
a fallback and keep the rest usable. It's a genuine gap — and it's the one thing
that still needs a class component, since there's no hook equivalent."*

### 11. `POST /orders` and the list endpoints are unauthenticated
**HOW TO ANSWER:** *"Worth flagging honestly — it's a backend decision the frontend
exposes. Creating an order and listing orders and riders need no token, so the
console shows data when signed out and anyone can create an order. That's fine for a
demo, and it's why the '+ Order' button isn't gated. In production, order creation
would be authenticated and scoped to the calling customer, and listing would be
filtered by role — a customer should see their own orders, not everyone's."*

🔴 This one is valuable: it shows you can see past your own UI to the API's
security posture.

### 12. Hard-coded demo credentials in shipped source
**HOW TO ANSWER:** *"`DEMO_LOGINS` with three seeded accounts and their passwords is
in the bundle. It's intentional — it makes the permission demo one click instead of
a setup ritual — but it only belongs in a demo. Real deployments would drop that
array, and those seeded accounts must never exist in production."*

### 13. No request timeout or cancellation
**HOW TO ANSWER:** *"I don't pass an `AbortController` signal to `fetch`, so a hung
request stays pending forever and an in-flight request isn't cancelled when a
component unmounts. For polling that's mostly benign, but the correct pattern is an
AbortController in the effect, aborted in the cleanup."*

### 14. Unused files and boilerplate README
**HOW TO ANSWER:** *"`src/assets/` and `public/icons.svg` are unused Vite template
leftovers, and `frontend/README.md` is still the untouched template text. Housekeeping
I should have done — I'd rather say that than pretend they're intentional."*

---

# 7-Day Frontend Interview Study Plan

Roughly 2–3 focused hours a day. Your project is the entire curriculum — you are
not learning React, you are learning *your* React.

## Day 1 — HTML, CSS and how the page exists 🔴

**READ:** Part 1 (§1.1–1.5).
**OPEN:** `frontend/index.html`, `frontend/src/App.css` (lines 1–30 and 96–138).
**MUST UNDERSTAND:**
- Why `index.html` is essentially empty, and what `<div id="root">` is for
- `className` vs `class`, and why
- CSS custom properties on `:root` and `var()`
- Flexbox for rows and the `flex: 1` spacer trick; Grid for the counter tiles
- That there is exactly **one** media query
**PRACTISE:** Q5–Q13.
**PRIORITY:** MUST — HTML/CSS basics, JSX→HTML translation. OPTIONAL — pseudo-element
details, scrollbar styling.

## Day 2 — JavaScript 🔴

**READ:** Part 2 (§2.1–2.13).
**OPEN:** `frontend/src/api.js` in full; `App.jsx` lines 194–312.
**MUST UNDERSTAND:**
- `const` vs `let`, and that `const` isn't immutability
- Arrow functions, and why `onClick={() => fn(x)}` needs the wrapper
- `map`, `filter`, `reduce`, `slice` — and **where each one is in your code**
- Spread, and why `[...orders].reverse()` matters
- Destructuring in all three forms
- `?.` and `??`, and why `user` starting as `null` makes them necessary
- async/await, Promises, try/catch/**finally**, `Promise.all`
**PRACTISE:** Q14–Q22, Q77–Q80.
**PRIORITY:** MUST — map, spread, destructuring, async/await, optional chaining.
SHOULD — reduce, Promise.all. OPTIONAL — the O(n²) reduce nuance.

## Day 3 — React, JSX, components, props 🔴

**READ:** Part 3 (§3.1–3.5).
**OPEN:** `main.jsx`; `App.jsx` lines 16–43 (`Health`) and 89–185 (`Auth`).
**MUST UNDERSTAND:**
- What React is in four words: component-based, declarative, state-driven, virtual DOM
- The exact boot sequence — index.html → main.jsx → App → children
- What StrictMode does and **why it matters to your intervals**
- JSX rules, Fragments, and the capitalisation rule
- Props are read-only; `onUser` is how the child updates the parent
- Props vs state, using `Auth` as the example
**PRACTISE:** Q23–Q42.
**PRIORITY:** MUST — all of it. This is the densest interview day.

## Day 4 — State, hooks, effects, events 🔴 the most important day

**READ:** Part 3 (§3.6–3.11).
**OPEN:** `App.jsx` lines 187–301 with the guide side by side.
**MUST UNDERSTAND:**
- Why a normal variable can't replace state — **both** reasons
- Every part of `const [busy, setBusy] = useState(false)`
- The three rules: never mutate, updates are async, use the functional form
- `useEffect` — when it runs, all four dependency-array cases, cleanup
- The `useCallback` infinite-loop trace (§3.8) — **learn this cold**
- Controlled inputs, and why the role switcher proves they're controlled
- The `busy`/`try`/`catch`/`finally` pattern and why `finally` is load-bearing
**PRACTISE:** Q43–Q68.
**PRIORITY:** MUST — everything. If you only have one day, use this one.

## Day 5 — API, HTTP, auth 🔴

**READ:** Part 4 (§4.1–4.9).
**OPEN:** `api.js`; `app/routers/auth.py`; `app/core/dependencies.py`.
**MUST UNDERSTAND:**
- `request()` line by line
- **`fetch` doesn't throw on 4xx** — you must check `res.ok`
- The three backend error shapes and how you flatten them
- GET/POST/PATCH and which endpoint uses which; PATCH vs PUT
- 200/201/400/401/403/404/409/422/429/503 — with a project example for each
- **401 vs 403**, and where each occurs in your app
- The full JWT flow, and the localStorage trade-off
- Why there's no CORS
**PRACTISE:** Q69–Q76, and Q17/Q18/Q19 from the top-30.
**PRIORITY:** MUST — request(), fetch/res.ok, 401 vs 403, the token story.
SHOULD — idempotency. OPTIONAL — rate limiting details.

## Day 6 — The five flows 🔴

**READ:** §5.5, then §5.1–5.4.
**DO:** Say each of the five flows out loud, from memory, with the files open.
Time yourself — each should take 60–90 seconds. Then do it again with the files
closed.
**MUST UNDERSTAND:** login; session restore on refresh; the idempotency demo; the
403 role demo; the status state machine.
**ALSO:** the 10 files list (§5.4) — be able to say why each matters in one
sentence.
**PRIORITY:** MUST — all five. These carry most of a real conversation.

## Day 7 — Questions, weak spots, revision 🔴

**READ:** the top-30 two-version answers; "Things I Should NOT Say"; "Areas Where
An Interviewer Could Catch Me".
**DO:**
- Say the 20-second, 1-minute and 2-minute pitches out loud until they're natural
- Walk the 5-minute technical tour with the files open
- Read the "never claim" table twice — these are the cheap ways to lose credibility
- Pick your three favourite weak spots and practise volunteering them
**PRACTISE:** all 30 A/B answers, out loud.
**PRIORITY:** MUST — the pitches, the not-to-claim list, and three volunteered
weak spots.

**If you only have two days:** Day 4 and Day 6. State/hooks plus the five flows
covers most of what gets asked.

---

# 15-Minute Interview Revision

The final pass. Everything here is verified against your code.

**React** — a JS library for building UIs from components. Declarative and
state-driven: describe the UI for a state, call a setter, React diffs a virtual
DOM and patches the real one.

**Component** — a function starting with a capital that returns JSX. You have
four: `App` (root, owns shared state), `Auth` (login), `Health` (readiness pills),
`Stats` (ops metrics).

**JSX** — HTML-like syntax compiled to `createElement` calls. `className` not
`class`, camelCase events, self-closing tags, `{}` for expressions, one root
element (or a `<>` Fragment).

**Props** — read-only inputs from parent to child. Yours: `user`, `onUser`, `say`.
`onUser` is a callback prop — that's how `Auth` updates `App`'s state.

**State** — data that redraws the UI. A plain variable fails because React isn't
notified and it resets every render.

**`useState`** — `const [busy, setBusy] = useState(false)`. Value, setter, initial
value used only on the first render. Never mutate; updates are asynchronous; use
`setX(prev => ...)` when the new value depends on the old.

**`useEffect`** — side effects, run after commit. `[]` = once on mount; `[dep]` =
when dep changes; no array = every render. The returned function is cleanup — yours
call `clearInterval`.

**`useCallback`** — stable function identity. `refresh` needs it because the
polling effect depends on it; without it the interval restarts every render →
infinite loop.

**Event handler** — `onClick={() => advance(o.id, next)}`. The arrow defers the
call; without it the function runs during render.

**Form** — you have **no** `<form>`. Two controlled inputs (`value` + `onChange`)
plus button `onClick`. Consequence: Enter doesn't submit.

**`map`** — turns data into JSX. Orders → rows; `STATUS_FLOW[status]` → buttons;
`log` → lines.

**`key`** — stable identity for list items. `o.id` on orders ✅; `i` on the log ⚠️
(prepended, so indexes shift).

**API** — one `request()` over `fetch` in `api.js`. Builds headers, checks
`res.ok` (**fetch doesn't throw on 4xx**), flattens three error shapes, throws an
Error with `.status` and `.data`. Ten methods. GET/POST/PATCH only.

**async/await** — `await` pauses the function, not the browser. Every handler:
set busy → try → catch and log → **`finally` reset busy**.

**JSON** — `stringify` out, `parse` in. You parse inside a try/catch so an HTML
error page doesn't crash the app.

**Routing** — **none**. Single view. "Screens" are conditional renders on state.
If you added a router you'd also need a server catch-all returning `index.html`.

**Frontend↔backend** — same origin. `BASE = ""`. Vite proxies in dev; FastAPI
serves `dist/` in production. **No CORS anywhere.**

**Auth** — JWT bearer. Login → `setToken` → module variable + localStorage →
`Authorization: Bearer` on every request → mount effect calls `/auth/me` to
restore the session → 401 clears the token. Logout is client-side only, because
JWTs are stateless.

**Roles** — ops / rider / customer. `isOps` disables controls in the UI; the
server enforces with `require_ops` and an actor guard. **The UI reflects
permissions; the server enforces them.**

**Architecture** — `index.html` → `main.jsx` (`createRoot`) → `App` → `Health` /
`Auth` / `Stats` → `api.js` → FastAPI → Postgres/Redis/Kafka.

**State management** — local `useState`, lifted to `App` when shared. No Redux, no
Context. Trigger to change: a second view, or three-plus levels of drilling.

**The five flows** — login · session restore on refresh · order creation with the
idempotency replay · the 403 role demo · the status state machine.

**Top-20 rapid fire**
1. React? UI library, component-based, declarative, state-driven.
2. Why React? Continuous re-render from polled data; derived UI can't drift.
3. JSX? Compiled HTML-like syntax; `className`, `{}`, self-closing.
4. Component? Capitalised function returning JSX. You have four.
5. Props vs state? From-parent-readonly vs owned-and-changeable.
6. Child updates parent? Parent passes a function; `onUser`.
7. `useState` returns? `[value, setter]`; initial value used once.
8. `setState` immediate? No — scheduled; next render.
9. Why not mutate? React compares references.
10. `useEffect` when? After commit. `[]` once; `[dep]` on change.
11. Cleanup? Returned function; yours `clearInterval`.
12. `useCallback` why? Stable identity for the effect dependency.
13. Keys why? Identity across renders. `o.id` good, index bad.
14. Controlled input? `value` from state + `onChange` writes back.
15. `fetch` throws on 404? **No** — check `res.ok`.
16. fetch vs Axios? Built in; wrote the 15 lines myself; gave up timeouts.
17. Token storage? localStorage + module variable; XSS-readable.
18. 401 vs 403? Don't know you vs know you and refuse.
19. Router? None — single view, conditional rendering.
20. Improve? Real `<form>`, fix the log keys, `usePolling` hook, fix the dead
    `rider_id` badge.

**Common mistakes to avoid saying**
- ❌ "We use Redux/Context/React Router/Axios/Tailwind/TypeScript" — none are true
- ❌ "It's real-time" — it's polling on 4 s / 5 s / 6 s timers
- ❌ "Fully responsive" — one media query
- ❌ "I wrote frontend tests" — there are none
- ❌ "The UI enforces permissions" — it *reflects* them; the server enforces
- ❌ Claiming `@types/react` makes it TypeScript — it doesn't

**Volunteer these three before you're asked**
1. The dead `rider_id` badge — the response schema doesn't include the field.
2. No `<form>`, so Enter doesn't submit.
3. Index keys on a prepended activity log.
