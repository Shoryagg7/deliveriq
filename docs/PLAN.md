# DeliverIQ — 45-Day Master Plan (v3 — Ubuntu Edition)
### Built for Ubuntu Linux · From Zero Dev Experience → Production-Grade Backend

**For:** Shorya Gupta — final-year CSE, Codeforces Specialist · LeetCode Knight · 1500+ problems. Strong C++/DSA, zero backend experience.
**System:** Ubuntu Linux (every command in this doc is Ubuntu-specific).
**Now with:** Day 0 setup · daily YouTube + docs · C++→Python bridges · "Break It On Purpose" exercises · interview answer templates filled in as you build.

---

## How This Plan Is Structured

Each day has:
- 🎯 **Goal** — what you'll achieve
- 📚 **Resources** — official docs + ONE best YouTube video (max 30 min)
- 💻 **Tasks** — exact things to code
- ✅ **End of Day** — proof you completed it

Some days also have:
- 💡 **C++ → Python** — maps new Python to the C++/CP you already know
- 🔥 **Break It On Purpose** — deliberately sabotage your code to understand WHY each piece exists
- 📝 **Interview Answer Template** — fill-in-the-blank answers, written the same day you build the feature
- 🐧 **Ubuntu Note** — Linux-specific tips that aren't obvious
- 🐛 **Stuck Protocol** — your debugging checklist (defined on Day 1)

**Rule:** Spend max 30 min watching, then START CODING. Don't binge tutorials.

---

## Why This Project Wins

**One-line pitch:**
> A production-grade REST API that dispatches food delivery orders to riders using priority queues, geohashing, rate limiting, and event streaming — built with FastAPI, Redis, Kafka, PostgreSQL, and Docker.

**The differentiator (your answer to "how is this different from Swiggy?"):**
> Dispatch is **fairness-aware**. Among riders within a bounded distance band Δ of the nearest, it assigns to the one with the fewest orders today — balancing rider earnings without breaching delivery SLA. This reframes naive greedy-nearest as a **bounded constrained-assignment problem**, and gives an honest social-impact answer: fairer earnings distribution for gig riders.

**Why interviewers will love it:**
- Uber/Zomato/Swiggy literally have teams building exactly this
- **Not a clone — the fairness-banded dispatch is a defensible design choice that's yours**
- Razorpay/PhonePe care about rate limiting, idempotency, webhooks (all included)
- Demonstrates 5+ system design concepts in ONE codebase
- Pure backend = no frontend complexity wasting your time
- Every line is defensible — no "I copied a tutorial" smell

---

## Tech Stack Explained (For Beginners)

You're a beginner. Here's what each tool does in PLAIN English:

| Tool | What it is | Why we use it |
|---|---|---|
| **Python** | Programming language | Easy syntax, huge ecosystem, industry standard |
| **FastAPI** | Web framework | Builds REST APIs fast, auto-generates docs |
| **PostgreSQL** | Database | Stores orders, riders, logs permanently |
| **SQLAlchemy** | ORM | Lets you write Python instead of raw SQL |
| **Alembic** | Migration tool | Tracks database schema changes |
| **Redis** | In-memory cache | Super-fast (microseconds) temporary storage |
| **Kafka** | Event streaming | Sends events between services reliably |
| **Docker** | Containerization | Packages your app so it runs anywhere |
| **Docker Compose** | Multi-container tool | Starts FastAPI + Postgres + Redis + Kafka together |
| **pytest** | Testing framework | Writes automated tests for your code |
| **Postman** | API testing tool | Manually tests your endpoints |
| **Git + GitHub** | Version control | Tracks code changes, hosts your repo |
| **Railway/Render** | Cloud hosting | Deploys your app to a live public URL |

**Don't panic.** You don't learn these in isolation — you learn them by USING them daily in this project.

🐧 **Ubuntu Note:** On Ubuntu, modern Docker uses `docker compose` (a space — it's a built-in plugin), NOT the old `docker-compose` (hyphen). This whole doc uses `docker compose`.

---

## Project Folder Structure (Explained Like You're 5)

You won't build all of this on Day 6. We'll **grow it organically** as you learn. Here's what each piece means so you have context:

```
deliveriq/                  ← your project (a folder)
│
├── app/                    ← all your Python code lives here
│   ├── __init__.py         ← empty file, tells Python "this is a package"
│   ├── main.py             ← the file that starts your FastAPI app
│   │
│   ├── core/               ← shared infrastructure stuff
│   │   ├── config.py       ← reads passwords/URLs from .env file
│   │   ├── database.py     ← code to connect to PostgreSQL
│   │   └── redis_client.py ← code to connect to Redis (added Week 3)
│   │
│   ├── models/             ← database table definitions
│   │   ├── order.py        ← defines what an "Order" row looks like in DB
│   │   └── rider.py        ← same for "Rider"
│   │
│   ├── schemas/            ← request/response shapes for API
│   │   └── order.py        ← "POST /orders needs these fields, returns these"
│   │
│   ├── routers/            ← your API endpoints grouped by topic
│   │   ├── orders.py       ← all /orders/* endpoints
│   │   └── riders.py       ← all /riders/* endpoints
│   │
│   ├── services/           ← your business logic (algorithms)
│   │   ├── dispatch.py     ← priority queue logic
│   │   └── geohash.py      ← rider matching logic
│   │
│   ├── middleware/         ← code that runs on EVERY request (rate limiter)
│   ├── workers/            ← background scripts (Pub/Sub & Kafka consumers)
│   └── utils/              ← helper functions used across the app
│
├── tests/                  ← pytest test files
│   └── test_orders.py
│
├── .env                    ← SECRETS (passwords, API keys) — NEVER commit
├── .env.example            ← template showing what .env should contain
├── .gitignore              ← tells Git which files to ignore (.env, venv, etc.)
├── requirements.txt        ← list of Python packages your project needs
├── README.md               ← project description (the front page on GitHub)
├── Dockerfile              ← recipe to package your app (Week 4)
└── docker-compose.yml      ← recipe to run app + DB + Redis together (Week 4)
```

### Why This Structure?

**The principle:** *Separation of concerns.*
- **Routers** answer "WHAT endpoints exist?" — just routing
- **Schemas** answer "WHAT shape does data have?" — just validation
- **Services** answer "HOW does business logic work?" — the smart stuff
- **Models** answer "WHAT does the database store?" — just persistence
- **Core** is glue (config, connections)

If you mix these (everything in one file), the code becomes unmaintainable. Real companies use this pattern. Interviewers will notice and respect it.

**You'll create folders ONE AT A TIME** as you need them. Don't create empty folders just because the structure says so.

### Folder Unlock Schedule

You create each folder ONLY when you first need it — never before.

| Folder | Created on | Reason |
|---|---|---|
| `app/` | Day 6 | Entry point |
| `app/schemas/` | Day 9 | First Pydantic model |
| `app/core/` | Day 11 | DB connection |
| `app/models/` | Day 11 | First ORM model |
| `app/routers/` | Day 12 | First router split |
| `app/middleware/` | Day 16 | Rate limiter |
| `app/services/` | Day 17 | First algorithm |
| `app/workers/` | Day 20 | Pub/Sub listener |

---

## What is `__init__.py`?

A file named `__init__.py` (often empty) tells Python: *"this folder is a package — you can import code from it."*

Example:
- Folder `app/models/` with `__init__.py` and `order.py`
- In `main.py`, you can write: `from app.models.order import Order`
- Without `__init__.py`, Python might say "module not found"

You'll create one in every folder. They stay empty 99% of the time.

💡 **C++ → Python:** `__init__.py` is loosely like a header that makes a directory "includable." Importing in Python (`from app.models.order import Order`) is the rough equivalent of `#include "order.h"` plus a namespace.

---

## Day 0 — Ubuntu System Check (30 minutes, do this before Day 1)

### 🎯 Goal
Verify your Ubuntu system is ready. Fix anything missing. On a fresh Ubuntu install, none of these tools may exist yet — that's fine.

### 💻 Run this system check
Open a terminal (**Ctrl+Alt+T**) and run each line:

```bash
# 1. Check Ubuntu version
lsb_release -a
# ✅ Should show Ubuntu 20.04 or 22.04 (24.04 also fine)

# 2. Confirm you're on Linux
uname -a
# ✅ Should mention "Linux"

# 3. Check Python
python3 --version
# ✅ Should show 3.8+. We'll install 3.11 on Day 1 if needed.

# 4. Check if pip3 exists
pip3 --version
# If "command not found": sudo apt install python3-pip -y

# 5. Check git
git --version
# If "command not found": sudo apt install git -y

# 6. Check curl (needed for downloads)
curl --version
# If "command not found": sudo apt install curl -y

# 7. Check available disk space
df -h ~
# ✅ Should have at least 10GB free (Docker images are large)

# 8. Check internet
ping -c 3 google.com
# ✅ Should show 3 responses

# 9. Update system packages (do this once — may take 5–10 min)
sudo apt update && sudo apt upgrade -y
```

### What if something fails?
- **Python3 not found:** `sudo apt install python3 python3-pip python3-venv -y`
- **Git not found:** `sudo apt install git -y`
- **curl not found:** `sudo apt install curl -y`
- **No internet:** check WiFi/ethernet — not a code problem
- **Less than 10GB disk:** free up space before continuing

🐧 **Ubuntu Note:** Terminal paste is **Ctrl+Shift+V**, not Ctrl+V. Other handy shortcuts: Ctrl+C kills a running process, Ctrl+L clears the screen, Tab autocompletes, Up arrow recalls the last command.

### ✅ End of Day 0
All checks pass. You're ready for Day 1.

---

# PHASE 1: Python + Git Fundamentals (Days 1–7)

## Day 1 — Install Everything (Ubuntu) + Hello World

### 🎯 Goal
Install your tools the Ubuntu way, write your first Python program, push to GitHub. Learn the Stuck Protocol (you'll use it all 45 days).

### 📚 Resources
- **Watch:** [Python in 1 Hour — Programming with Mosh](https://www.youtube.com/watch?v=kqtD5dpn9C8) *(watch only first 30 min — variables, loops, functions)*
- **Setup video:** [Python + VS Code Setup — Corey Schafer](https://www.youtube.com/watch?v=-nh9rCzPJ20) *(15 min)*
- **Create GitHub account:** [github.com](https://github.com)

### 💻 Tasks

**Step 1 — Install Python 3.11 (Ubuntu):**
```bash
# Check current version
python3 --version

# If not 3.11+, install it (Ubuntu supports multiple Python versions side by side)
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Verify
python3.11 --version
```
🐧 **Ubuntu Note:** If your system `python3` is 3.8 or 3.9, that's fine — just use `python3.11` explicitly when creating your venv on Day 5. There is no "Add to PATH" checkbox on Ubuntu; apt handles it.

**Step 2 — Install Git (Ubuntu):**
```bash
sudo apt update
sudo apt install git -y
git --version
```

**Step 3 — Install VS Code (Ubuntu):**
```bash
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code -y
```

**Step 4 — Set up your workspace:**
```bash
cd ~
mkdir -p projects/deliveriq
cd projects/deliveriq
code .          # opens this folder in VS Code
```
In VS Code: install the extension **"Python"** by Microsoft.

🐧 **Ubuntu Note:** Build everything inside your Linux home directory (`~/projects/deliveriq`). If you ever use WSL, never build under `/mnt/c/...` — file I/O there is up to 10× slower.

**Step 5 — Write `hello.py`:**
```python
name = "DeliverIQ"
print(f"Welcome to {name}!")

# Try this: list, dict, loop
foods = ["pizza", "burger", "biryani"]
for f in foods:
    print(f"Delivering: {f}")
```

**Step 6 — Run it:**
```bash
python3 hello.py
```
🐧 **Ubuntu Note:** At the system level (outside a venv), always use `python3` and `pip3` — plain `python`/`pip` may not exist on Ubuntu.

### 🐛 STUCK PROTOCOL — read this now, use it for the next 45 days
Follow in order, max 15 min per step.

```
Step 1 (5 min): Read the error message carefully.
  On Ubuntu, errors print to the terminal. Look for:
  - The LAST line (this is usually the actual error)
  - Any line mentioning a file inside your project folder (not venv/)
  - "Did you mean...?" suggestions (Python often tells you the fix)

Step 2 (5 min): Google the exact last line of the error in quotes.
  Example: "sqlalchemy.exc.OperationalError: could not connect to server"
  Add "Ubuntu" or "FastAPI" to narrow results. Filter to the last 2 years.

Step 3 (5 min): Check common Ubuntu-specific causes first:
  ModuleNotFoundError       → venv not activated (run: source venv/bin/activate)
  ConnectionRefusedError    → service not running (run: docker ps  or  systemctl status postgresql)
  Permission denied         → Docker group issue (run: newgrp docker)
  python: command not found → use python3 on Ubuntu
  pip: command not found    → use pip3, or activate venv first
  Port already in use       → run: sudo lsof -i :PORT   then   sudo kill -9 PID
  422 Unprocessable Entity  → Pydantic schema mismatch — check your request body JSON

Step 4 (15 min): Ask for help with this exact format:
  "I'm on Ubuntu, building DeliverIQ with FastAPI, on Day [X].
   I'm trying to: [one sentence]
   Full error: [paste entire terminal output]
   Relevant file: [paste the file]
   Already tried: [steps 1-3 results]"
```

### ✅ End of Day
- You see `Welcome to DeliverIQ!` in your terminal
- You know where to look when something breaks (→ See Stuck Protocol)

---

## Day 2 — Python Basics: Variables, Functions, Classes

### 🎯 Goal
Understand Python core syntax to write basic logic.

### 📚 Resources
- **Watch:** [Python OOP in 30 min — Tech With Tim](https://www.youtube.com/watch?v=JeznW_7DlB0) *(classes specifically)*
- **Docs:** [Python Official Tutorial — Sections 3, 4, 9](https://docs.python.org/3/tutorial/)

### 💻 Tasks
Create `practice.py`:
```python
# 1. Functions
def calculate_priority(order_value: float, wait_minutes: int) -> float:
    """Higher score = more urgent."""
    return order_value * 0.4 + wait_minutes * 0.6

print(calculate_priority(500, 15))  # 209.0

# 2. Classes (your first Rider)
class Rider:
    def __init__(self, rider_id: int, name: str):
        self.rider_id = rider_id
        self.name = name
        self.is_available = True

    def assign_order(self, order_id: int):
        if not self.is_available:
            return False
        self.is_available = False
        print(f"Rider {self.name} assigned to order {order_id}")
        return True

# Try it
r = Rider(1, "Suresh")
r.assign_order(101)
r.assign_order(102)  # Should fail — already busy
```
Run with `python3 practice.py`. → See Stuck Protocol if anything breaks.

### ✅ End of Day
- You understand functions, type hints, classes, `self`, `__init__`

---

## Day 3 — Python Data Structures + List Comprehensions

### 🎯 Goal
Master Python's "magic" syntax that you'll use everywhere.

### 📚 Resources
- **Watch:** [Python List Comprehensions — Corey Schafer](https://www.youtube.com/watch?v=3dt4OGnU5sM) *(20 min)*
- **Docs:** [Python Data Structures](https://docs.python.org/3/tutorial/datastructures.html)

### 💡 C++ → Python (for competitive programmers)
```
vector<int>              →  list:          [1, 2, 3]
unordered_map<str,int>   →  dict:          {"key": 1}
unordered_set<int>       →  set:           {1, 2, 3}
pair<int,int>            →  tuple:         (1, 2)
auto x = 5               →  x = 5          (no type needed)
cout << x << endl        →  print(x)
nullptr                  →  None
true / false             →  True / False
```

### 💻 Tasks
```python
# Lists, dicts, sets
orders = [
    {"id": 1, "value": 250, "status": "PENDING"},
    {"id": 2, "value": 800, "status": "DELIVERED"},
    {"id": 3, "value": 450, "status": "PENDING"},
]

# List comprehension — get all pending order IDs
pending_ids = [o["id"] for o in orders if o["status"] == "PENDING"]
print(pending_ids)  # [1, 3]

# Dict comprehension — order_id → value
order_values = {o["id"]: o["value"] for o in orders}
print(order_values)  # {1: 250, 2: 800, 3: 450}

# Sum of pending order values
total = sum(o["value"] for o in orders if o["status"] == "PENDING")
print(total)  # 700
```

### ✅ End of Day
- You can write list/dict comprehensions without looking it up

---

## Day 4 — Git + GitHub

### 🎯 Goal
Understand version control, push your code to GitHub.

### 📚 Resources
- **Watch:** [Git Tutorial for Beginners — Mosh](https://www.youtube.com/watch?v=8JJ101D3knE) *(first 30 min only)*
- **Docs:** [Git Handbook by GitHub](https://docs.github.com/en/get-started/using-git)
- **Cheatsheet:** [GitHub Git Cheat Sheet PDF](https://education.github.com/git-cheat-sheet-education.pdf)

### 💻 Tasks
1. **In terminal, configure Git:**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your-email@example.com"
   ```
2. **Inside `deliveriq` folder:**
   ```bash
   git init
   git branch -M main
   ```
3. **Create `.gitignore`:**
   ```
   __pycache__/
   *.pyc
   venv/
   .env
   .vscode/
   .idea/
   ```
4. **First commit:**
   ```bash
   git add .
   git commit -m "chore: initial commit with practice files"
   ```
5. **Create empty repo on GitHub** named `deliveriq`
6. **Push:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/deliveriq.git
   git push -u origin main
   ```

### ✅ End of Day
- Your code is on GitHub at `github.com/your-username/deliveriq`
- Your first green square appears on your profile

---

## Day 5 — Virtual Environments + pip

### 🎯 Goal
Isolate your project's Python packages from the rest of your system.

### 📚 Resources
- **Watch:** [Python venv Explained — Corey Schafer](https://www.youtube.com/watch?v=Kg1Yvry_Ydk) *(15 min)*
- **Docs:** [venv official](https://docs.python.org/3/library/venv.html)

### 💻 Tasks
```bash
# Inside deliveriq/ folder:

# Create virtual env (use python3.11 if your system python3 is older)
python3 -m venv venv

# Activate it
source venv/bin/activate

# You should now see (venv) at the start of your terminal prompt

# Install FastAPI (inside venv, plain pip works)
pip install fastapi uvicorn[standard]

# Freeze versions
pip freeze > requirements.txt

# Commit
git add requirements.txt
git commit -m "chore: add FastAPI dependencies"
git push
```

🐧 **Ubuntu Note:** The activation command is **`source venv/bin/activate`** — that's the only one you'll ever use. You may see `venv\Scripts\activate` in tutorials; that's **Windows only — ignore it**. To leave the venv later, type `deactivate`.

💡 **C++ → Python:** A venv is like having a per-project set of linked libraries instead of polluting your global system. Each project gets its own clean dependency tree.

### ✅ End of Day
- `(venv)` appears in your terminal
- `requirements.txt` lists `fastapi`, `uvicorn`, etc.
- You understand: venv = "private box of libraries for THIS project only"

---

## Day 6 — Build the App Structure (Hands-On)

### 🎯 Goal
Create ONLY the entry point. You'll add every other folder later, exactly when you need it.

### 📚 Resources
- **Watch:** [FastAPI Tutorial — first 20 min by ArjanCodes](https://www.youtube.com/watch?v=SORiTsvnU28)
- **Docs:** [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)

### 💻 Tasks

> **We will create each folder ONLY when we first need it — not before.** Today you create just `app/` and `app/main.py`. See the Folder Unlock Schedule above.

**Step 1: Create `app/` folder and `__init__.py`**
```bash
mkdir app
touch app/__init__.py
```
*Why?* `app/` will hold all your code. `__init__.py` makes Python treat it as a package.

🐧 **Ubuntu Note:** `touch filename` creates an empty file on Ubuntu. (`type nul > filename` is a Windows command — ignore it if you see it anywhere.) Install `tree` once with `sudo apt install tree -y`, then run `tree app/` anytime to view your folder layout.

**Step 2: Create `app/main.py`**
```python
from fastapi import FastAPI

app = FastAPI(title="DeliverIQ", version="0.1.0")

@app.get("/")
def root():
    return {"status": "alive", "service": "DeliverIQ"}

@app.get("/health")
def health():
    return {"status": "ok"}
```
*Why a separate `main.py`?* It's the **entry point** — the first file Python runs when starting your API.

**Step 3: Run it**
```bash
uvicorn app.main:app --reload
```
*Translation:* "Run the `app` object from the file `app/main.py`, and restart when files change."

**Step 4: Visit in browser**
- `http://localhost:8000/` → JSON response
- `http://localhost:8000/docs` → **Swagger UI** (auto-generated, free!)

**Step 5: Commit**
```bash
git add app/
git commit -m "feat: bootstrap FastAPI app with health endpoint"
git push
```

### Folder right now:
```
deliveriq/
├── app/
│   ├── __init__.py     ← empty
│   └── main.py         ← your FastAPI app
├── venv/               ← (ignored by git)
├── .gitignore
├── requirements.txt
└── hello.py            ← from Day 1 (can delete now)
```

That's it. **No models/, schemas/, routers/ folders yet** — we'll add them when we need them.

### ✅ End of Day
- Visiting `http://localhost:8000/docs` shows Swagger UI with 2 endpoints
- You can explain `app/main.py` line by line

---

## Day 7 — Catch-up + DSA in Python

### 🎯 Goal
Solidify Python by solving DSA problems in Python (not C++).

### 📚 Resources
- **Watch:** [Python for C++ Programmers — NeetCode](https://www.youtube.com/watch?v=0K_eZGS5NsU) *(quick reference)*
- **Practice:** [LeetCode — Easy Array Problems](https://leetcode.com/problemset/all/?difficulty=EASY&topicSlugs=array)

### 💡 C++ → Python
You already know these cold in C++. Re-solving in Python builds fluency fast:
```
sort(v.begin(), v.end())        →  v.sort()   or   sorted(v)
v.push_back(x)                  →  v.append(x)
v.size()                        →  len(v)
m.count(k)                      →  k in m
s.find(x) != string::npos       →  x in s
```

### 💻 Tasks
Solve these 3 in Python (you already know them in C++):
1. **Two Sum** — return indices of two numbers summing to target
2. **Reverse a String** — in-place
3. **Valid Parentheses** — use a stack

This kills two birds: DSA practice + Python fluency.

### ✅ End of Week 1
You now know:
- ✅ Python syntax (variables, loops, functions, classes)
- ✅ Git basics (commit, push, branch)
- ✅ Virtual environments (Ubuntu)
- ✅ FastAPI runs locally
- ✅ Project has a clean entry point — folders grow from here

---

# PHASE 2: FastAPI + PostgreSQL (Days 8–14)

## Day 8 — FastAPI: Path Params & Query Params

### 🎯 Goal
Build dynamic endpoints that take inputs.

### 📚 Resources
- **Docs:** [Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- **Docs:** [Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- **Watch:** [FastAPI Path & Query — BugBytes](https://www.youtube.com/watch?v=PnWcLhdJN0Q) *(15 min)*

### 💻 Tasks
Update `app/main.py`:
```python
from fastapi import FastAPI, HTTPException

app = FastAPI(title="DeliverIQ")

# Fake in-memory database for now
orders_db = {
    1: {"id": 1, "value": 250, "status": "PENDING"},
    2: {"id": 2, "value": 800, "status": "DELIVERED"},
}


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]
@app.get("/orders")
def list_orders(status: str | None = None):
    if status:
        return [o for o in orders_db.values() if o["status"] == status]
    return list(orders_db.values())

```

Test in Swagger:
- `GET /orders/1` → returns order 1
- `GET /orders?status=PENDING` → returns only pending

### ✅ End of Day
- You understand path params (`/orders/{id}`) vs query params (`?status=X`)

---

## Day 9 — Pydantic Models (Request/Response Validation)

### 🎯 Goal
Validate incoming data automatically.

### 📚 Resources
- **Docs:** [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- **Watch:** [Pydantic Tutorial — ArjanCodes](https://www.youtube.com/watch?v=Vj-iU-8_xLs) *(20 min)*

### 💡 C++ → Python
Pydantic `BaseModel` is exactly like a C++ `struct` — but it validates types automatically.
```
struct OrderCreate { int customer_id; float value; };
        ↓
class OrderCreate(BaseModel):
    customer_id: int
    value: float
```
The difference: if you pass a string where a float is expected, Pydantic raises an error automatically and returns HTTP 422. A C++ struct would silently accept garbage or crash.

### 💻 Tasks

**Step 1:** Create `app/schemas/` folder (we need it now!)
```bash
mkdir app/schemas
touch app/schemas/__init__.py
```

**Step 2:** Create `app/schemas/order.py`:
```python
from pydantic import BaseModel, Field
from datetime import datetime

class OrderCreate(BaseModel):
    customer_id: int
    restaurant_id: int
    value: float = Field(gt=0, description="Order value in INR, must be positive")
    pickup_lat: float
    pickup_lon: float
    drop_lat: float
    drop_lon: float

class OrderResponse(BaseModel):
    id: int
    customer_id: int
    value: float
    status: str
    created_at: datetime
```

**Step 3:** Update `app/main.py`:
```python
from fastapi import FastAPI
from datetime import datetime
from app.schemas.order import OrderCreate, OrderResponse

app = FastAPI(title="DeliverIQ")
orders_db = {}
next_id = 1

@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(order: OrderCreate):
    global next_id
    new_order = {
        "id": next_id,
        "customer_id": order.customer_id,
        "value": order.value,
        "status": "PENDING",
        "created_at": datetime.utcnow(),
    }
    orders_db[next_id] = new_order
    next_id += 1
    return new_order
```

Test in Swagger UI — try sending invalid data (negative value), see auto-rejection (422). → See Stuck Protocol if you get unexpected errors.

### ✅ End of Day
- You understand: Pydantic = automatic validation + auto-docs in Swagger

---

## Day 10 — PostgreSQL Setup (Ubuntu)

### 🎯 Goal
Install PostgreSQL on Ubuntu, create your database, connect with a GUI.

### 📚 Resources
- **Watch:** [PostgreSQL Setup — Programming with Mosh](https://www.youtube.com/watch?v=qw--VYLpxG4) *(first 20 min)*
- **Docs:** [PostgreSQL on Ubuntu](https://www.postgresql.org/download/linux/ubuntu/)

### 💻 Tasks

**Option A — Install PostgreSQL natively (recommended on Ubuntu):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create user and database
sudo -u postgres psql -c "CREATE USER deliveriq_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "CREATE DATABASE deliveriq_db OWNER deliveriq_user;"

# Test connection
psql -U deliveriq_user -d deliveriq_db -h localhost
# (type \q to exit)
```

**Option B — Run via Docker instead:**
```bash
docker run -d --name deliveriq-pg -e POSTGRES_USER=deliveriq_user \
  -e POSTGRES_PASSWORD=password -e POSTGRES_DB=deliveriq_db \
  -p 5432:5432 postgres:15
```

**Install DBeaver GUI (Ubuntu):**
```bash
wget https://dbeaver.io/files/dbeaver-ce_latest_amd64.deb
sudo dpkg -i dbeaver-ce_latest_amd64.deb
sudo apt install -f   # fix any dependency issues
dbeaver &             # launch
```
In DBeaver: connect with host `localhost`, user `deliveriq_user`, password `password`, database `deliveriq_db`.

🐧 **Ubuntu Note:** If you ever get `address already in use` on port 5432, something is already running there. Find it with `sudo lsof -i :5432` and stop it (or stop the native service with `sudo systemctl stop postgresql` if you decide to use the Docker one instead). Don't run both on the same port.

### ✅ End of Day
- DBeaver shows you connected to `deliveriq_db`
- You can open a SQL Editor and run `SELECT 1;` successfully

---

## Day 11 — SQLAlchemy + First DB Model

### 🎯 Goal
Connect FastAPI to PostgreSQL, define your Order table.

### 📚 Resources
- **Watch:** [SQLAlchemy + FastAPI — pixegami](https://www.youtube.com/watch?v=0zb2kohYZIM) *(30 min — most important video this week)*
- **Docs:** [SQLAlchemy 2.0 ORM Quickstart](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- **Docs:** [FastAPI + SQL](https://fastapi.tiangolo.com/tutorial/sql-databases/)

### 💻 Tasks

**Step 1:** Install packages
```bash
pip install sqlalchemy psycopg2-binary
pip freeze > requirements.txt
```

**Step 2:** Create `app/core/` folder
```bash
mkdir app/core
touch app/core/__init__.py
```

**Step 3:** Create `app/core/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://deliveriq_user:password@localhost:5432/deliveriq_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency: gives each request its own DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 4:** Create `app/models/` folder + `order.py`:
```bash
mkdir app/models
touch app/models/__init__.py
```

```python
# app/models/order.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    restaurant_id = Column(Integer, nullable=False)
    value = Column(Float, nullable=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lon = Column(Float, nullable=False)
    drop_lat = Column(Float, nullable=False)
    drop_lon = Column(Float, nullable=False)
    status = Column(String, default="PENDING", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Step 5:** In `app/main.py`, create tables:
```python
from app.core.database import Base, engine
from app.models.order import Order  # important: import so SQLAlchemy sees it

Base.metadata.create_all(bind=engine)
```

Restart `uvicorn`. Check DBeaver — `orders` table appears!

### ✅ End of Day
- `orders` table exists in PostgreSQL
- You understand ORM = "Python class ↔ DB table"

---

## Day 12 — Real CRUD with Database

### 🎯 Goal
Make endpoints actually save and read from PostgreSQL.

### 📚 Resources
- **Docs:** [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- **Reference:** [SQLAlchemy ORM Querying Guide](https://docs.sqlalchemy.org/en/20/orm/queryguide/)

### 💻 Tasks

**Create `app/routers/` folder:**
```bash
mkdir app/routers
touch app/routers/__init__.py
```

`app/routers/orders.py`:
```python
# app/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("", response_model=OrderResponse, status_code=201)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    new_order = Order(**order.model_dump())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    return order

@router.get("", response_model=list[OrderResponse])
def list_orders(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    return query.all()
```

**Update `app/main.py`:**
```python
from fastapi import FastAPI
from app.core.database import Base, engine
from app.models.order import Order
from app.routers import orders

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DeliverIQ")
app.include_router(orders.router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

Test in Swagger — create order, fetch it, see it in DBeaver.

### ✅ End of Day
- Orders persist in PostgreSQL
- Folder structure now has `core/`, `models/`, `routers/`, `schemas/`

---

## Day 13 — Add Rider Model + Endpoints

### 🎯 Goal
Repeat what you learned. Build it without looking back.

### 📚 Resources
- Same as Day 11–12 (reference back if stuck → See Stuck Protocol)

### 💻 Tasks
- Create `app/models/rider.py` — fields: id, name, current_lat, current_lon, is_available, created_at
- Create `app/schemas/rider.py` — `RiderCreate`, `RiderResponse`
- Create `app/routers/riders.py` — POST, GET, list
- Register router in `main.py` with `app.include_router(riders.router)`

### ✅ End of Day
- You can create/list riders via API
- You did it independently — proves Day 11–12 stuck

---

## Day 14 — Alembic Migrations + Buffer

### 🎯 Goal
Stop using `create_all`. Use real database migrations.

### 📚 Resources
- **Watch:** [Alembic Migrations — pixegami](https://www.youtube.com/watch?v=zTSmvUVbk8M) *(15 min)*
- **Docs:** [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

### 💻 Tasks
```bash
pip install alembic
alembic init alembic
```

Edit `alembic.ini` → set `sqlalchemy.url` to your DB URL.
Edit `alembic/env.py` → import your `Base` and set `target_metadata = Base.metadata`.

```bash
alembic revision --autogenerate -m "create orders and riders tables"
alembic upgrade head
```

Remove `Base.metadata.create_all()` from `main.py` — Alembic handles it now.

**Why this matters:** Production NEVER uses `create_all`. Migrations let you safely change schema later. **Interviewers ask about this.**

### ✅ End of Week 2
- ✅ Two tables in Postgres (orders, riders)
- ✅ Full CRUD via API
- ✅ Proper migrations
- ✅ Clean folder structure

---

# PHASE 3: Redis + Core Dispatch Logic (Days 15–21)

## Day 15 — Redis Setup + Basics (Ubuntu)

### 🎯 Goal
Install Redis on Ubuntu, learn the 10 commands you'll use 90% of the time.

### 📚 Resources
- **Watch:** [Redis in 20 minutes — Fireship](https://www.youtube.com/watch?v=G1rOthIU-uo)
- **Watch:** [Redis Crash Course — Hussein Nasser](https://www.youtube.com/watch?v=jgpVdJB2sKQ) *(deeper)*
- **Docs:** [Redis Data Types](https://redis.io/docs/data-types/)

### 💻 Tasks

**Option A — Install Redis natively (Ubuntu):**
```bash
sudo apt update
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test
redis-cli ping
# Should return: PONG
```

**Option B — Run via Docker:**
```bash
docker run -d --name deliveriq-redis -p 6379:6379 redis:7
```

**RedisInsight GUI (easiest on Ubuntu via Docker):**
```bash
docker run -d --name redisinsight -p 5540:5540 redis/redisinsight:latest
# Open: http://localhost:5540
```

**Install the Python client:**
```bash
pip install redis
```

Create `app/core/redis_client.py`:
```python
import redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
```

Practice commands in Python:
```python
from app.core.redis_client import redis_client

# Strings
redis_client.set("hello", "world", ex=60)  # expires in 60s
redis_client.get("hello")

# Counters
redis_client.incr("page_views")

# Sets (for geohash later)
redis_client.sadd("riders_in_zone_A", "rider_1", "rider_2")
redis_client.smembers("riders_in_zone_A")

# Sorted sets (for priority queue)
redis_client.zadd("pending_orders", {"order_1": 100, "order_2": 250})
redis_client.zrevrange("pending_orders", 0, 0)  # highest score
```

### ✅ End of Day
- You ran 10+ Redis commands and saw them in RedisInsight

---

## Day 16 — Token Bucket Rate Limiter ⭐ (Most Important Day)

### Before we code: what is middleware?

Every HTTP request your API receives goes through a pipeline. Middleware sits in that pipeline and runs on every request — before your endpoint code executes.

```
Incoming request
      │
      ▼
┌─────────────────────┐
│  Rate Limit Check   │  ← middleware (runs first, always)
└──────────┬──────────┘
           │ (if allowed)
           ▼
┌─────────────────────┐
│  Your Endpoint Code │  ← only runs if middleware allows it
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Add Response Header │  ← middleware again (runs on the way out)
└─────────────────────┘
           │
           ▼
    Response to client
```

You write middleware ONCE. It protects ALL your endpoints automatically — you never have to add rate limiting code inside each endpoint function. This is the same principle as a `#pragma` or a decorator in C++ — applied globally.

### 🎯 Goal
Build the rate limiter — your #1 interview talking point.

### 📚 Resources
- **Watch:** [Token Bucket Algorithm — ByteByteGo](https://www.youtube.com/watch?v=mhUQe4BKZXs) *(7 min, gold)*
- **Read:** [Cloudflare's Rate Limiting Explanation](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/)
- **Docs:** [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)

### 💡 C++ → Python
Token bucket is the sliding-window rate problem from LeetCode (e.g. LC 239, 480) — but instead of running once on an array, it runs on EVERY incoming HTTP request. The Redis hash is your "window state" that persists between requests.

### 💻 Tasks

Create `app/middleware/` folder:
```bash
mkdir app/middleware
touch app/middleware/__init__.py
```

`app/middleware/rate_limiter.py`:
```python
# app/middleware/rate_limiter.py
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.redis_client import redis_client

BUCKET_SIZE = 100        # max tokens
REFILL_RATE = 100 / 60   # 100 tokens per 60 seconds

async def rate_limit_middleware(request: Request, call_next):
    client_key = request.headers.get("X-API-Key") or request.client.host
    bucket_key = f"rate_limit:{client_key}"

    now = time.time()
    data = redis_client.hgetall(bucket_key)

    if not data:
        tokens = float(BUCKET_SIZE)
        last_refill = now
    else:
        tokens = float(data['tokens'])
        last_refill = float(data['last_refill'])
        elapsed = now - last_refill
        tokens = min(BUCKET_SIZE, tokens + elapsed * REFILL_RATE)

    if tokens < 1:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Try again later."}
        )

    tokens -= 1
    redis_client.hset(bucket_key, mapping={"tokens": tokens, "last_refill": now})
    redis_client.expire(bucket_key, 120)

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(int(tokens))
    return response
```

Register in `main.py`:
```python
from app.middleware.rate_limiter import rate_limit_middleware
app.middleware("http")(rate_limit_middleware)
```

**Test it:** Open a terminal and fire 110 requests fast:
```bash
for i in {1..110}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/health; done
```
You'll see `200` for the first ~100, then `429` after the bucket empties. **MAGIC. You just built rate limiting.**

🐧 **Ubuntu Note:** The `for i in {1..110}; do ...; done` loop is native bash and works in your Ubuntu terminal as-is. No PowerShell needed.

### 🔥 Break It On Purpose
Delete the `redis_client.expire(bucket_key, 120)` line. Restart the server. Make 110 requests (you'll get 429 after 100 — good). Now wait 3 minutes and make 10 more requests. They should succeed IF the TTL was working. But they fail — the bucket is permanently empty. The expire line is what allows recovery. Now restore it.

### 📝 Interview Answer Template — fill this in now, save to `INTERVIEW_NOTES.md`
```
"I implemented a ________ rate limiter backed by ________.
Each API client gets ________ tokens, replenished at ________ per minute.
Every request costs ________ token. If the bucket is empty, I return HTTP ________.
I chose this algorithm over ________ because it allows ________ (hint: think bursts).
The check costs ________ Redis operations, so overhead per request is under ________."
```

### ✅ End of Day
- Rate limiter blocks requests after quota
- You can explain Token Bucket on a whiteboard

---

## Day 17 — Priority Queue Dispatch

### 🎯 Goal
Implement order dispatch using Redis sorted sets.

### 📚 Resources
- **Watch:** [Priority Queues Explained — NeetCode](https://www.youtube.com/watch?v=wptevk0bshY)
- **Docs:** [Redis Sorted Sets](https://redis.io/docs/data-types/sorted-sets/)

### 💡 C++ → Python
```
priority_queue<pair<float,int>, vector<...>, greater<...>>  →  heapq module
```
`heapq` is a MIN-heap by default (smallest score out first). To simulate a MAX-heap (largest priority first), push NEGATIVE scores:
```python
heapq.heappush(pq, (-priority, order_id))
heapq.heappop(pq)  # returns most negative = originally highest priority
```
In DeliverIQ we use Redis **sorted sets** instead (ZADD/ZREVRANGE), which is cleaner for distributed state shared across multiple API instances.

### 💻 Tasks

Create `app/services/` folder:
```bash
mkdir app/services
touch app/services/__init__.py
```

`app/services/dispatch.py`:
```python
# app/services/dispatch.py
import time
from app.core.redis_client import redis_client

PENDING_ORDERS_KEY = "orders:pending"

def calculate_priority(value: float, wait_minutes: float) -> float:
    return value * 0.4 + wait_minutes * 0.6

def add_to_dispatch_queue(order_id: int, value: float):
    score = calculate_priority(value, 0)
    redis_client.zadd(PENDING_ORDERS_KEY, {str(order_id): score})

def pop_highest_priority() -> int | None:
    result = redis_client.zrevrange(PENDING_ORDERS_KEY, 0, 0, withscores=True)
    if not result:
        return None
    order_id, score = result[0]
    removed = redis_client.zrem(PENDING_ORDERS_KEY, order_id)
    if removed == 0:
        return None  # someone else dispatched it
    return int(order_id)
```

In `app/routers/orders.py`, after creating an order, call `add_to_dispatch_queue()`.
Create a new endpoint `POST /dispatch` that calls `pop_highest_priority()`.

### 🔥 Break It On Purpose
Change `zrevrange` to `zrange` (drop the 'rev'). Create 3 orders with values 100, 500, 200. Call `POST /dispatch` 3 times. You'll get them in order: 100, 200, 500 — cheapest first. A regular delivery customer gets dispatched before the premium order. That's the bug. Restore `zrevrange`.

### 📝 Interview Answer Template — fill this in now
```
"I dispatch orders using a ________ data structure stored in Redis ________ (data type).
Each order gets a priority score: ________ × 0.4 + ________ × 0.6.
Higher value + longer wait time = higher priority.
The dispatch operation is O(________) for insert and O(________) for extract.
If two orders tie on score, I break ties by ________."
```

### ✅ End of Day
- Create 3 orders with different values → dispatch endpoint returns highest-priority first
- You can sketch the algorithm on paper

---

## Day 18 — Geohash Rider Matching

### 🎯 Goal
Find nearby riders without scanning all riders.

### 📚 Resources
- **Watch:** [Geohashing Explained — System Design Interview](https://www.youtube.com/watch?v=UaYAYrXlBS8) *(10 min)*
- **Interactive:** [Geohash Explorer](https://geohash.softeng.co/)
- **Library docs:** [python-geohash](https://github.com/hkwi/python-geohash)

### 💡 C++ → Python
Geohash is just a spatial hash function — it maps (lat, lon) → string key. It's like `unordered_map` but the keys have a spatial property: nearby locations share a common prefix. `"tdr1yz"` and `"tdr1yx"` are adjacent cells; `"xyz123"` is far away. You're doing O(1) Redis SET lookup by key — same idea as `unordered_map::find()`.

### 💻 Tasks
```bash
pip install python-geohash
```

Create `app/services/geohash_service.py`:
```python
import geohash
from app.core.redis_client import redis_client

PRECISION = 6  # ~1.2 km cells

def add_rider(rider_id: int, lat: float, lon: float):
    cell = geohash.encode(lat, lon, PRECISION)
    redis_client.sadd(f"geohash:{cell}", rider_id)
    redis_client.hset(f"rider:{rider_id}:loc", mapping={"lat": lat, "lon": lon, "cell": cell})

def find_nearby_riders(lat: float, lon: float) -> list[int]:
    cell = geohash.encode(lat, lon, PRECISION)
    neighbors = geohash.neighbors(cell)
    cells_to_check = [cell] + neighbors

    riders = set()
    for c in cells_to_check:
        riders.update(redis_client.smembers(f"geohash:{c}"))
    return [int(r) for r in riders]
```

**Why check neighbors?** Orders at cell edges might have closer riders in adjacent cells. **Gold interview talking point.**

### 💻 Tasks (continued) — Fairness-Banded Rider Selection

`find_nearby_riders` gives you the *candidate set*. Now pick ONE — but not just the nearest. Naive nearest-rider starves some riders and overloads others. Instead: among riders within a band Δ of the closest, assign to whoever has the **fewest orders today**. Fairness is a tiebreaker *inside* a distance band — never an override (or you'd send a far rider and deliver cold food).

Add to `app/services/geohash_service.py`:
```python
import math, time

def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6_371_000  # metres
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def select_rider(order_lat: float, order_lon: float, band_m: float = 500) -> int | None:
    candidates = find_nearby_riders(order_lat, order_lon)
    if not candidates:
        return None
    scored = []
    for rid in candidates:
        loc = redis_client.hgetall(f"rider:{rid}:loc")
        if not loc:
            continue
        dist = _haversine(order_lat, order_lon, float(loc["lat"]), float(loc["lon"]))
        orders_today = int(redis_client.hget(f"rider:{rid}", "orders_today") or 0)
        scored.append((rid, dist, orders_today))
    if not scored:
        return None
    d_min = min(s[1] for s in scored)
    feasible = [s for s in scored if s[1] <= d_min + band_m]
    feasible.sort(key=lambda s: (s[2], s[1]))   # fewest orders, then nearest
    chosen = feasible[0][0]
    redis_client.hincrby(f"rider:{chosen}", "orders_today", 1)
    redis_client.hset(f"rider:{chosen}", "last_assigned_at", int(time.time()))
    return chosen
```
> **Heap framing for the interview:** the selection is a min-heap on the composite key `(orders_today, distance)` over the feasible band — greedy on a composite key, O(k log k) on the small candidate set k, not O(n) over all riders.

> **Reset note:** `orders_today` needs a daily reset — a midnight job, or store it as `rider:{id}:orders:{YYYY-MM-DD}` with a 48h TTL. Mention this if asked; it shows you thought about state lifecycle.

### 🔥 Break It On Purpose
**(a) Boundary bug:** In `find_nearby_riders`, delete `neighbors = geohash.neighbors(cell)` and change `cells_to_check = [cell] + neighbors` to `cells_to_check = [cell]`. Add a rider at exactly lat=28.6139, lon=77.2090. Place an order at lat=28.6140, lon=77.2091 (literally 10 metres away but just across a cell boundary). The dispatch returns no riders. Restore the neighbors line.

**(b) Fairness vs SLA:** Set `band_m = 50000` in `select_rider`. Add two riders — one 50 m away with 10 orders today, one 4 km away with 0 orders. Dispatch. The far, idle rider wins → cold food. This is the exact failure an interviewer probes. Drop `band_m` back to 500 and watch the near rider win. **You just proved you understood the tradeoff — that's the whole point of the feature.**

### 📝 Interview Answer Template — fill this in now
```
"For rider matching, I use ________ instead of computing haversine distance to every rider.
This encodes (lat, lon) into a ________ string where nearby locations share a ________.
Lookup is O(________) — I query the home cell plus ________ neighbors to handle boundary cases.
Without this, matching would be O(________).
To pick the final rider I don't just take the nearest — among riders within a ________ m band of the closest, I assign the one with the fewest ________, which balances rider ________ without hurting delivery ________.
This reframes greedy-nearest as a ________ problem."
```

### ✅ End of Day
- Adding 5 riders → finding orders correctly returns nearby ones

---

## Day 19 — Order State Machine

### 🎯 Goal
Enforce valid state transitions (no DELIVERED → PENDING).

### 📚 Resources
- **Read:** [State Machine Pattern](https://refactoring.guru/design-patterns/state)
- **Watch:** [State Machines Explained](https://www.youtube.com/watch?v=Y_uqQpzNFM4)

### 💻 Tasks

Create `app/services/order_state.py`:
```python
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

VALID_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.ASSIGNED, OrderStatus.CANCELLED},
    OrderStatus.ASSIGNED: {OrderStatus.PICKED_UP, OrderStatus.CANCELLED},
    OrderStatus.PICKED_UP: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}

class InvalidTransition(Exception): pass

def transition(current: OrderStatus, target: OrderStatus):
    if target not in VALID_TRANSITIONS[current]:
        raise InvalidTransition(f"Cannot go from {current} to {target}")
```

Add a `PATCH /orders/{id}/status` endpoint that uses this.

### 🔥 Break It On Purpose
Comment out the `if target not in VALID_TRANSITIONS[current]` block entirely. Now PATCH an order directly from PENDING to DELIVERED. It works — an order is "delivered" before any rider was assigned. This is a data-integrity nightmare. Restore the validation.

### ✅ End of Day
- Trying to mark DELIVERED → PENDING returns a 400 error

---

## Day 20 — Redis Pub/Sub (Pre-Kafka Practice)

### 🎯 Goal
Build event publishing — we'll upgrade to Kafka in Week 5.

### 📚 Resources
- **Watch:** [Redis Pub/Sub — Hussein Nasser](https://www.youtube.com/watch?v=KIFA_fFzSbo)
- **Docs:** [Redis Pub/Sub](https://redis.io/docs/manual/pubsub/)

### 💻 Tasks
Publish an event when an order is dispatched:
```python
import json, time
redis_client.publish("order.dispatched", json.dumps({
    "order_id": order_id,
    "rider_id": rider_id,
    "timestamp": time.time()
}))
```

Create `app/workers/` folder and a listener script:
```bash
mkdir app/workers
touch app/workers/__init__.py
```

`app/workers/notification_worker.py`:
```python
import json
from app.core.redis_client import redis_client

pubsub = redis_client.pubsub()
pubsub.subscribe("order.dispatched")

print("Listening...")
for msg in pubsub.listen():
    if msg["type"] == "message":
        data = json.loads(msg["data"])
        print(f"📲 Notify customer: Order {data['order_id']} dispatched to rider {data['rider_id']}")
```

Run in a separate terminal: `python -m app.workers.notification_worker`.
Now dispatch an order — see the notification log.

🐧 **Ubuntu Note:** Open a second terminal tab with **Ctrl+Shift+T** so you can keep `uvicorn` running in one tab and the worker in another.

### ✅ End of Day
- Pub/Sub works
- You feel the limitation: if the worker is off, the message is lost (this is why we move to Kafka)

---

## Day 21 — Integration Testing

### 🎯 Goal
Write automated tests so future changes don't silently break things.

### 📚 Resources
- **Watch:** [pytest Tutorial — ArjanCodes](https://www.youtube.com/watch?v=DhUpxWjOhME) *(20 min)*
- **Docs:** [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

### 💻 Tasks
```bash
pip install pytest pytest-cov httpx
```

Create `tests/test_orders.py`:
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_order():
    response = client.post("/orders", json={
        "customer_id": 1,
        "restaurant_id": 1,
        "value": 500,
        "pickup_lat": 28.6,
        "pickup_lon": 77.2,
        "drop_lat": 28.7,
        "drop_lon": 77.3,
    })
    assert response.status_code == 201
    assert response.json()["value"] == 500

def test_invalid_value():
    response = client.post("/orders", json={"value": -10})
    assert response.status_code == 422  # validation error
```

Run: `pytest -v --cov=app`

### ✅ End of Week 3
- ✅ Rate limiter live
- ✅ Priority queue dispatch live
- ✅ Geohash matching live
- ✅ State machine enforced
- ✅ Events via Pub/Sub
- ✅ Tests passing

---

# PHASE 4: Production Quality + Docker (Days 22–28)

## Day 22 — Structured Logging

### 🎯 Goal
Replace `print()` with proper JSON logs.

### 📚 Resources
- **Watch:** [Python Logging Best Practices — ArjanCodes](https://www.youtube.com/watch?v=urrfJgHwIJA) *(15 min)*
- **Docs:** [Python logging](https://docs.python.org/3/howto/logging.html)

### 💻 Tasks
Create `app/core/logging_config.py`:
```python
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])
```

Call `setup_logging()` in `main.py`. Replace ALL `print()` with `logger.info()`.

### ✅ End of Day
- Logs come out as JSON, easy to ship to log aggregators

---

## Day 23 — Custom Exceptions

### 🎯 Goal
Clean error responses, no Python tracebacks leaking.

### 📚 Resources
- **Docs:** [FastAPI Exception Handlers](https://fastapi.tiangolo.com/tutorial/handling-errors/)

### 💻 Tasks
Create `app/core/exceptions.py`:
```python
class DeliverIQException(Exception): pass
class OrderNotFound(DeliverIQException): pass
class RiderUnavailable(DeliverIQException): pass
class InvalidStateTransition(DeliverIQException): pass
```

In `main.py`:
```python
from fastapi.responses import JSONResponse
from app.core.exceptions import OrderNotFound

@app.exception_handler(OrderNotFound)
async def order_not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "ORDER_NOT_FOUND", "message": str(exc)})
```

### ✅ End of Day
- API returns clean JSON errors with codes

---

## Day 24 — Environment Config with .env

### 🎯 Goal
No more hardcoded passwords.

### 📚 Resources
- **Watch:** [Pydantic Settings — ArjanCodes](https://www.youtube.com/watch?v=NJtY6J0KME0)
- **Docs:** [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

### 💻 Tasks
```bash
pip install pydantic-settings python-dotenv
```

Create `app/core/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    rate_limit_per_minute: int = 100

    class Config:
        env_file = ".env"

settings = Settings()
```

Create `.env`:
```
DATABASE_URL=postgresql://deliveriq_user:password@localhost:5432/deliveriq_db
REDIS_URL=redis://localhost:6379
```

Create `.env.example` (commit this, NOT `.env`):
```
DATABASE_URL=
REDIS_URL=
```

Use `settings.database_url` everywhere instead of hardcoded strings.

🐧 **Ubuntu Note:** To check an env var in your terminal, run `echo $DATABASE_URL`. To set one temporarily for the current shell, run `export DATABASE_URL="postgresql://..."`. `python-dotenv` reads the `.env` file the same way on Ubuntu as anywhere else.

### ✅ End of Day
- Zero hardcoded secrets in code

---

## Day 25 — Dockerize Your App

### 🎯 Goal
Package your app into a portable container.

### 📚 Resources
- **Watch:** [Docker for Python Apps — TechWorld with Nana](https://www.youtube.com/watch?v=bi0cKgmRuiA) *(20 min)*
- **Docs:** [Docker Get Started](https://docs.docker.com/get-started/)

### 💻 Tasks

**First, install Docker on Ubuntu (if you haven't already):**
```bash
# Remove old versions if any
sudo apt remove docker docker-engine docker.io containerd runc

# Install Docker
sudo apt update
sudo apt install ca-certificates curl gnupg lsb-release -y
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y

# Run Docker without sudo (IMPORTANT)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

🐧 **Ubuntu Note:** If you get `permission denied` on Docker, you need to refresh your group membership. Either run `newgrp docker` in the current terminal, or fully log out and back in. Verify with `groups $USER` — you should see `docker` in the list.

**Create `Dockerfile` in project root:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build & run:
```bash
docker build -t deliveriq .
docker run -p 8000:8000 --env-file .env deliveriq
```

### ✅ End of Day
- Your app runs in a Docker container

---

## Day 26 — Docker Compose for Full Stack

### 🎯 Goal
One command starts FastAPI + Postgres + Redis.

### 📚 Resources
- **Watch:** [docker compose Tutorial — TechWorld with Nana](https://www.youtube.com/watch?v=DM65_JyGxCo) *(15 min)*
- **Docs:** [Compose reference](https://docs.docker.com/compose/)

### 💻 Tasks
Create `docker-compose.yml` (the file is still named with a hyphen; only the *command* changed to `docker compose`):
```yaml
version: '3.8'
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://deliveriq_user:password@db:5432/deliveriq_db
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: deliveriq_db
      POSTGRES_USER: deliveriq_user
      POSTGRES_PASSWORD: password
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  pg_data:
```

Run: `docker compose up --build`. Visit `localhost:8000/docs`.

🐧 **Ubuntu Note:** If port 5432 or 6379 says "address already in use", you probably still have the native Postgres/Redis running from Days 10/15. Stop them with `sudo systemctl stop postgresql redis-server` so Compose can use those ports, or find the process with `sudo lsof -i :5432`.

### 🔥 Break It On Purpose
Remove `depends_on: [db, redis]` from the `api` service. Run `docker compose up`. The API starts before Postgres is ready and crashes with `connection refused`. The `depends_on` is startup ordering. Restore it.

### ✅ End of Day
- One command brings up your entire stack

---

## Day 27 — Admin Analytics Endpoint

### 🎯 Goal
Show off SQL aggregation skills.

### 📚 Resources
- **Docs:** [SQLAlchemy func module](https://docs.sqlalchemy.org/en/20/core/functions.html)

### 💻 Tasks
Add `GET /admin/stats`:
```python
from sqlalchemy import func
from app.models.order import Order

@router.get("/admin/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Order.id)).scalar()
    by_status = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    avg_value = db.query(func.avg(Order.value)).scalar()
    return {
        "total_orders": total,
        "by_status": dict(by_status),
        "avg_order_value": float(avg_value or 0),
    }
```

### ✅ End of Day
- Beautiful analytics endpoint working

---

## Day 28 — Load Testing

### 🎯 Goal
Get concrete numbers for your resume.

### 📚 Resources
- **Watch:** [Locust Tutorial — Sam Meech-Ward](https://www.youtube.com/watch?v=2x8d_-MAQUo) *(15 min)*
- **Docs:** [Locust](https://docs.locust.io/en/stable/quickstart.html)

### 💻 Tasks
```bash
pip install locust
```

Create `load_test.py`:
```python
from locust import HttpUser, task, between

class DeliverIQUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def create_order(self):
        self.client.post("/orders", json={
            "customer_id": 1, "restaurant_id": 1, "value": 500,
            "pickup_lat": 28.6, "pickup_lon": 77.2,
            "drop_lat": 28.7, "drop_lon": 77.3,
        })
```

Run: `locust -f load_test.py --host http://localhost:8000`
Visit `http://localhost:8089` → start 500 users.
**Screenshot the results** for your README.

### ✅ End of Week 4
- ✅ Dockerized, dotenv'd, logged, tested
- ✅ Real load test numbers (e.g., "p99 = 43ms at 500 RPS")

---

# Before Phase 5: Redis vs Kafka — Read This First

This confuses every beginner. Here's the truth, before you touch Kafka.

### Redis = Fast Memory Storage
Use Redis for things that need to be **read/written in microseconds**:
- **Rate limit buckets** — count "how many requests has this user made in the last minute?"
- **Rider location cache** — store rider GPS coordinates for instant lookup
- **Geohash → rider sets** — map "which riders are in grid cell xyz?" using Redis Sets
- **Session data** — temporary user info

Redis stores data in RAM. Lightning fast, but data can be lost if Redis crashes (unless you configure persistence).

### Kafka = Reliable Event Pipeline
Use Kafka for **events that must NEVER be lost** and may be processed later:
- **Order created event** — multiple services need to know: notification service, analytics, inventory
- **Order dispatched event** — trigger driver app push, customer SMS, restaurant alert
- **Audit logs** — every action stored permanently

Kafka stores events on disk in a log. Slightly slower (milliseconds) but **durable, replayable, scalable**.

### Simple Rule
- **Need it NOW, can lose it** → Redis
- **Need it RELIABLY, may process later** → Kafka

### In DeliverIQ:
| Feature | Tool | Reason |
|---|---|---|
| Rate limit counters | Redis | Microsecond reads on every request |
| Cache rider locations | Redis | Hot data, refreshed every minute |
| Geohash → rider sets | Redis | Set operations are O(1) |
| Order dispatched event | **Kafka** | Multiple services consume, can't lose it |
| Customer notifications | **Kafka** | Async, durable |
| Analytics events | **Kafka** | Replay history if analytics service crashes |

### Beginner Path
- **Week 1–4:** Use only Redis (Pub/Sub for events)
- **Week 5:** Replace Redis Pub/Sub with Kafka
- This way you UNDERSTAND why Kafka exists before using it

---

# PHASE 5: Kafka + Advanced Features (Days 29–35)

## Day 29 — Kafka Theory + First Touch

### 🎯 Goal
Understand Kafka, then immediately use it once (no Python yet) so the theory sticks.

### 📚 Resources
- **Watch:** [Kafka in 100 Seconds — Fireship](https://www.youtube.com/watch?v=uvb00oaa3k8) *(2 min)*
- **Watch:** [Apache Kafka Explained — Confluent](https://www.youtube.com/watch?v=06iRM1Ghr1k) *(7 min, official)*
- **Watch:** [Kafka Deep Dive — Hussein Nasser](https://www.youtube.com/watch?v=Ch5VhJzaoaI) *(30 min)*
- **Course (free):** [Confluent Kafka 101](https://developer.confluent.io/learn-kafka/apache-kafka/events/)

### 💻 Tasks
Learn the vocabulary and write a 1-page note in your own words:
- Topic, Partition, Offset, Producer, Consumer, Consumer Group
- Why Kafka > Redis Pub/Sub: persistence, replay, scaling

### Hands-on Kafka preview (15 min)
*(You'll add the Kafka services to docker-compose.yml properly on Day 30. If they're not there yet, do this preview after Day 30's compose edit.)*
```bash
# Bring up Kafka and its UI
docker compose up zookeeper kafka kafka-ui -d

# Wait 30 seconds for startup, then open:
# http://localhost:8080

# In Kafka UI:
# 1. Click "Topics" → "Add a Topic" → name it "test.topic", 1 partition
# 2. Click into the topic → "Produce Message" → type any text → Send
# 3. Click "Messages" tab — see your message appear with offset=0

# Congratulations — you just used Kafka without writing a line of code.
# Tomorrow: do the exact same thing from Python.
```

### ✅ End of Day
- You can explain Kafka in 2 minutes to a beginner
- You produced and saw one Kafka message in the UI

---

## Day 30 — Kafka in docker-compose

### 🎯 Goal
Get Kafka running locally as part of your stack.

### 📚 Resources
- **Watch:** [Kafka with Docker — Stéphane Maarek](https://www.youtube.com/watch?v=YA1JosJW1XQ)
- **Docs:** [Confluent Docker Quickstart](https://docs.confluent.io/platform/current/installation/docker/installation.html)

### 💻 Tasks
Add to `docker-compose.yml`:
```yaml
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on: [zookeeper]
    ports: ["9092:9092"]
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  kafka-ui:
    image: provectuslabs/kafka-ui
    ports: ["8080:8080"]
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
```

Run `docker compose up`. Visit `localhost:8080` → Kafka UI.

### ✅ End of Day
- Kafka running, GUI accessible

---

## Day 31 — Kafka Producer

### 🎯 Goal
Publish events from FastAPI to Kafka.

### 📚 Resources
- **Docs:** [confluent-kafka-python](https://docs.confluent.io/kafka-clients/python/current/overview.html)
- **Example:** [Producer Examples](https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/producer.py)

### 💻 Tasks
```bash
pip install confluent-kafka
```

Create `app/core/kafka_producer.py`:
```python
import json
from confluent_kafka import Producer

producer = Producer({'bootstrap.servers': 'localhost:9092'})

def publish_event(topic: str, event: dict):
    producer.produce(topic, json.dumps(event).encode('utf-8'))
    producer.flush()
```

Replace Redis `publish` calls with `publish_event("order.dispatched", {...})`.

### ✅ End of Day
- Events appear in Kafka UI under the `order.dispatched` topic

---

## Day 32 — Kafka Consumer

### 🎯 Goal
Read events asynchronously.

### 📚 Resources
- **Example:** [Consumer Examples](https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/consumer.py)

### 💻 Tasks
Create `app/workers/notification_consumer.py`:
```python
import json
from confluent_kafka import Consumer

consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'notifications',
    'auto.offset.reset': 'earliest',
})
consumer.subscribe(['order.dispatched'])

print("Listening to Kafka...")
while True:
    msg = consumer.poll(1.0)
    if msg is None or msg.error():
        continue
    event = json.loads(msg.value())
    print(f"📲 [Kafka] Notify: order {event['order_id']} → rider {event['rider_id']}")
```

Run: `python -m app.workers.notification_consumer`.

### ✅ End of Day
- Kafka producer + consumer fully working

---

## Day 33 — Multiple Consumers (Real Power Move)

### 🎯 Goal
Show event-driven architecture with 3 independent consumers.

### 💻 Tasks
Create 3 workers, each in its own file:
- `notification_consumer.py` — group `notifications`
- `analytics_consumer.py` — group `analytics` (writes to DB)
- `audit_consumer.py` — group `audit-log` (writes to file)

All consume the same `order.dispatched` topic. Each gets its own copy.

**This is gold.** In an interview, you say:
> "I have 3 independent consumers — notifications, analytics, audit — each consuming the same Kafka topic via different consumer groups. They scale and fail independently. That's event-driven architecture."

### 📝 Interview Answer Template — fill this in now
```
"I replaced Redis Pub/Sub with Kafka because Pub/Sub is ________ — if the consumer is down, messages are ________.
Kafka persists events to ________ and allows ________ from any point.
I have ________ independent consumer groups on the order.dispatched topic:
________, ________, and ________.
Each group processes events ________ and can fail without affecting the others."
```

### ✅ End of Day
- 3 separate worker scripts, all reading the same topic, doing different things

---

## Day 34 — Idempotency Keys ⭐ (Razorpay Gold)

### 🎯 Goal
Handle duplicate requests safely.

### 📚 Resources
- **Read:** [Stripe's Idempotency Guide](https://stripe.com/docs/api/idempotent_requests)
- **Watch:** [Idempotency Explained — Hussein Nasser](https://www.youtube.com/watch?v=Vn5tgkPj1lQ)

### 💻 Tasks
Add middleware:
```python
import json
async def idempotency_middleware(request: Request, call_next):
    if request.method != "POST":
        return await call_next(request)

    key = request.headers.get("Idempotency-Key")
    if not key:
        return await call_next(request)

    cached = redis_client.get(f"idempotency:{key}")
    if cached:
        return JSONResponse(content=json.loads(cached), status_code=200)

    response = await call_next(request)
    # Cache successful responses for 24h
    redis_client.setex(f"idempotency:{key}", 86400, response.body.decode())
    return response
```

**Pitch this in every Razorpay/PhonePe interview.**

### 📝 Interview Answer Template — fill this in now
```
"Idempotency keys solve the problem of ________ due to network retries.
The client sends a ________ header with a UUID. The server caches the response in Redis for ________.
On a duplicate request, we return the ________ response instead of processing again.
This is critical for ________ APIs where charging a customer twice is unacceptable."
```

### ✅ End of Day
- Same `Idempotency-Key` returns the same response on retry

---

## Day 35 — JWT Authentication

### 🎯 Goal
Secure your API.

### 📚 Resources
- **Watch:** [JWT in FastAPI — pixegami](https://www.youtube.com/watch?v=5GxQ1rLTwaU) *(25 min)*
- **Docs:** [FastAPI Security with JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

### 💻 Tasks
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

Add `/auth/register`, `/auth/login` endpoints. Protect `/admin/stats` with a JWT bearer dependency.

### ✅ End of Week 5
- ✅ Kafka producer + 3 consumers
- ✅ Idempotency
- ✅ JWT auth
- You're now genuinely strong

---

# PHASE 6: Deployment + Observability (Days 36–42)

## Day 36 — Prometheus Metrics

### 🎯 Goal
Expose metrics for monitoring.

### 📚 Resources
- **Watch:** [Prometheus + FastAPI — Sam Meech-Ward](https://www.youtube.com/watch?v=h4Sl21AKiDg)
- **Library:** [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)

### 💻 Tasks
```bash
pip install prometheus-fastapi-instrumentator
```

In `main.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

Visit `/metrics` — beautiful metrics page.

### ✅ End of Day
- `/metrics` endpoint working

---

## Day 37 — Grafana Dashboard

### 🎯 Goal
Visual dashboard for a showpiece screenshot.

### 📚 Resources
- **Watch:** [Grafana + Prometheus Setup — TechWorld with Nana](https://www.youtube.com/watch?v=h4Sl21AKiDg)

### 💻 Tasks
Add to `docker-compose.yml`:
```yaml
  prometheus:
    image: prom/prometheus
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports: ["3000:3000"]
```

Create `prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'deliveriq'
    static_configs:
      - targets: ['api:8000']
```

Run `docker compose up`. Login to Grafana (`admin`/`admin`), add Prometheus as a data source, and build a dashboard with:
- Request rate
- p95/p99 latency
- Error rate
- Active orders

**Take SCREENSHOTS.** These go in the README.

### ✅ End of Day
- You have a Grafana dashboard screenshot — interview gold

---

## Day 38 — Health Checks

### 🎯 Goal
Production-ready health endpoint.

### 💻 Tasks
```python
from fastapi.responses import JSONResponse

@app.get("/health")
def health(db: Session = Depends(get_db)):
    checks = {}
    try:
        db.execute("SELECT 1")
        checks["db"] = "up"
    except Exception:
        checks["db"] = "down"

    try:
        redis_client.ping()
        checks["redis"] = "up"
    except Exception:
        checks["redis"] = "down"

    all_up = all(v == "up" for v in checks.values())
    status_code = 200 if all_up else 503
    return JSONResponse(
        content={"status": "ok" if all_up else "degraded", **checks},
        status_code=status_code,
    )
```

### ✅ End of Day
- Health check covers DB + Redis (extend to Kafka if you wish)

---

## Day 39 — Deploy to Railway

### 🎯 Goal
Get a public URL.

### 📚 Resources
- **Watch:** [Deploy FastAPI to Railway — pixegami](https://www.youtube.com/watch?v=zEY9KCDp5gA)
- **Docs:** [Railway Docs](https://docs.railway.app/)

### 💻 Tasks
1. Push everything to GitHub `main` branch
2. railway.app → New Project → Deploy from GitHub
3. Add Postgres plugin (auto-injects DATABASE_URL)
4. Add Redis plugin (auto-injects REDIS_URL)
5. For Kafka: sign up at [Upstash Kafka](https://upstash.com) (free tier), get broker URL
6. Set env vars in Railway dashboard
7. **Get URL** like `deliveriq-production.up.railway.app/docs`

### ✅ End of Day
- Live public URL working

---

## Day 40 — GitHub Actions CI/CD

### 🎯 Goal
Tests run automatically on every push.

### 📚 Resources
- **Watch:** [GitHub Actions for Python — Real Python](https://www.youtube.com/watch?v=mFFXuXjVgkU)
- **Docs:** [GitHub Actions Quickstart](https://docs.github.com/en/actions/quickstart)

### 💻 Tasks
Create `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env: { POSTGRES_PASSWORD: password }
        ports: ["5432:5432"]
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: pytest --cov=app
```

Push → see green CI badge.

🐧 **Ubuntu Note:** The CI runner uses `ubuntu-latest` — the same OS you develop on. So "works on my machine" actually means something here. Nice.

### ✅ End of Day
- CI badge in README, tests run on every PR

---

## Day 41 — README + Architecture Diagram

### 🎯 Goal
Showpiece front page.

### 📚 Resources
- **Tool:** [Excalidraw](https://excalidraw.com) — draw architecture, export as PNG
- **Example READMEs:** browse [Awesome FastAPI](https://github.com/mjhea0/awesome-fastapi)
- **Markdown guide:** [GitHub Markdown](https://docs.github.com/en/get-started/writing-on-github)

### 💻 Tasks
- Draw architecture in Excalidraw, save `architecture.png` in repo
- Write README with: description, badges, live URL, architecture diagram, quickstart, design decisions, load test results, Grafana screenshot

**README quickstart snippet to include:**
```bash
git clone https://github.com/you/deliveriq
cp .env.example .env
docker compose up --build
# API at http://localhost:8000/docs
```

### ✅ End of Day
- README looks like a real product page

---

## Day 42 — Demo Video

### 🎯 Goal
3-min Loom video showing it all works.

### 📚 Resources
- **Tool:** [Loom](https://loom.com) (free, 5 min videos)

### 💻 Tasks
Record 3 minutes:
1. Show Swagger UI (15s)
2. Create order via API (30s)
3. Show DB row in DBeaver (15s)
4. Show Kafka event in Kafka UI (30s)
5. Show Grafana dashboard updating (45s)
6. Trigger rate limiter (30s)

Link video in README and LinkedIn.

### ✅ End of Day
- Demo video live, ready to share

---

# PHASE 7: Polish + Interview Prep (Days 43–45)

## Day 43 — Code Quality Sweep

### 📚 Resources
- **black** formatter: `pip install black` → `black app/`
- **flake8** linter: `pip install flake8` → `flake8 app/`
- **mypy** type checker: `pip install mypy` → `mypy app/`

### 💻 Tasks
- Run all 3, fix all warnings
- Delete dead code
- Add docstrings to every function:
  ```python
  def dispatch_order(order_id: int) -> Rider:
      """Assign the highest-priority pending order to the nearest available rider.

      Args:
          order_id: Database ID of the order to dispatch.

      Returns:
          The Rider object assigned to this order.

      Raises:
          RiderUnavailableException: If no riders are within the geohash neighborhood.
      """
  ```
- Squash messy commits with `git rebase -i`

### ✅ End of Day
- Codebase is clean, formatted, type-checked, documented

---

## Day 44 — Interview Drills

### 🎯 Goal
Lock in every answer. You've been filling templates since Day 16 — now consolidate and rehearse.

### 📚 Resources
- **Watch:** [System Design Mock Interviews — Hello Interview](https://www.youtube.com/@hello_interview)

### 💻 Tasks
- Open your `INTERVIEW_NOTES.md` (all those filled-in templates from Days 16, 17, 18, 33, 34)
- Answer the full question bank below out loud, timed
- Record yourself doing the 2-minute pitch
- Sketch the architecture from memory on paper in 2 minutes

### The Full 20-Question Bank

**System Design**
1. **Why FastAPI over Flask/Django?**
   *Async by default, Pydantic validation, auto-OpenAPI, near-Go performance for I/O-bound work.*

2. **How does your rate limiter work? Why Token Bucket?**
   *Token Bucket allows burst traffic (good UX) while capping average rate. Implemented as a Redis hash storing tokens + last_refill_time, with lazy refill on each request. O(1) per check.*

3. **Why Redis for the priority queue, not PostgreSQL?**
   *Sub-ms reads, sorted sets are purpose-built (ZADD/ZREVRANGE). PostgreSQL would need an index scan.*

4. **What happens if Redis dies?**
   *Fallback: dispatch from PostgreSQL with a latency penalty. Rate limiter fails open with logging.*

5. **How does geohashing work?**
   *Encodes lat/lon into a base-32 string. Adjacent cells share a prefix. We check the home cell + 8 neighbors for boundary cases.*

6. **Why Kafka over Redis Pub/Sub?**
   *Pub/Sub is fire-and-forget — if the consumer is down, the message is lost. Kafka persists to disk, allows replay, supports consumer groups for parallel processing, and scales horizontally.*

**DSA**
7. **Why min-heap for dispatch?**
   *O(log n) insert/extract vs O(n) scan. Priority is a composite score (value × 0.4 + wait × 0.6).*

8. **Time complexity of your dispatch endpoint end-to-end?**
   *Rate-limit check: O(1). Pop from sorted set: O(log n). Geohash lookup: O(1). Total: O(log n).*

9. **Two orders with the same priority — what happens?**
   *Tiebreak by created_at (FIFO). Encode the score as `priority * 1e6 + (max_timestamp - created_at)`.*

10. **At 10M concurrent orders, what breaks first?**
    *The single-node Redis sorted set. Fix: Redis Cluster sharded by zone_id. Kafka partitions by region.*

**Database**
11. **Schema design?**
    *Orders(id, customer_id, restaurant_id, value, status, created_at, ...). Indexes on status, created_at. Audit-log table for state transitions.*

12. **Why PostgreSQL over MongoDB?**
    *Relational integrity matters here — orders FK to riders, zones. PostgreSQL gives ACID transactions. MongoDB shines for unstructured data.*

13. **How do you handle concurrent dispatch (two requests for the same order)?**
    *`SELECT ... FOR UPDATE` to lock the row, or atomic Redis ZREM (returns 1 if removed, 0 if already gone). Use the latter — faster.*

**Production**
14. **How does your CI/CD work?**
    *GitHub Actions runs pytest + black + flake8 on every PR. Merge to main triggers a Railway deploy. Health check confirms before serving traffic.*

15. **What if your API gets DDoSed?**
    *Token Bucket blocks per-key. Add Cloudflare in front for L7 protection. Rate-limit by IP at the gateway level too.*

16. **How do you debug a slow endpoint in production?**
    *Check Grafana p99 latency. Check structured logs by request_id. Profile with Python's cProfile if needed. Add explicit timing logs around the suspect code.*

17. **Idempotency — why and how?**
    *Network retries cause duplicate POSTs. Client sends an `Idempotency-Key` UUID. Server caches the response in Redis (24h TTL). A repeat key returns the cached response. Critical for payment APIs.*

**Behavioral**
18. **Hardest part to build?**
    *Geohash boundary conditions — an order at the edge of a cell needs to check 8 neighbors. Initially I only checked the home cell, and riders 100m away in the next cell weren't matching.*

19. **What would you do differently with more time?**
    *Add a circuit breaker (Hystrix pattern), distributed tracing with OpenTelemetry, a proper saga pattern for payment integration, and chaos testing with toxiproxy.*

20. **What did you learn?**
    *Event-driven architecture deeply — Kafka's offset model, consumer groups, partitioning trade-offs. Also production hygiene: structured logs, metrics, health checks.*

**Design / Differentiation**
21. **How is this different from a real Swiggy/Zomato dispatch?**
    *Theirs optimizes pure ETA. Mine adds a bounded fairness constraint: within a distance band Δ of the nearest rider, I assign to whoever has the fewest orders today. Greedy-nearest reframed as a constrained assignment problem.*

22. **What real problem does the fairness band solve?**
    *Naive nearest-rider starves some riders and overloads others — a real gig-economy issue. Banding spreads earnings more evenly while Δ guarantees I never trade away delivery SLA. Honest social-impact angle, no fabrication.*

23. **Why a band instead of a single weighted score (α·dist + β·fairness)?**
    *A blended score can silently send a far rider when β is high — cold food. The band makes the SLA guarantee explicit and tunable: fairness only operates inside Δ. Easier to reason about and defend.*

### ✅ End of Day
- You can answer all 20 cold, and deliver the 2-minute pitch from memory

---

## Day 45 — Final Buffer

### 💻 Tasks
- Fix any last bugs
- Tag release: `git tag v1.0.0 && git push --tags`
- Pin the repo on your GitHub profile
- Update LinkedIn projects section
- Update resume with the project bullets (see Resume Tips below)
- **Rest. You did it.**

---

# GitHub Workflow

### Daily Loop
```bash
git checkout dev
git pull
git checkout -b feature/kafka-consumer

# ... write code, write tests ...

git add -p                    # stage hunks, review what you're committing
git commit -m "feat: add Kafka consumer for order.dispatched events"
git push origin feature/kafka-consumer

# Open PR on GitHub → review → merge to dev
# Every Sunday: merge dev → main
```

### Commit Message Convention
| Prefix | When to use |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `test:` | Tests |
| `refactor:` | Code restructuring |
| `chore:` | Build/tooling |
| `perf:` | Performance improvement |

### Branch Structure
- `main` — always deployable, protected, requires PR
- `dev` — integration branch
- `feature/*` — feature work
- `fix/*` — bug fixes

### Pro Tip
**Make at least 50+ commits over 45 days.** Recruiters check your GitHub contribution graph. Green squares matter.

---

# Deployment Guide

### Railway (Recommended for Beginners)
1. **Sign up** at railway.app
2. **New Project** → **Deploy from GitHub repo**
3. Railway auto-detects `Dockerfile`
4. **Add plugins:**
   - PostgreSQL → auto-sets `DATABASE_URL`
   - Redis → auto-sets `REDIS_URL`
5. **For Kafka:** Use [Upstash Kafka](https://upstash.com) free tier
6. **Set env vars** in Railway dashboard
7. **Get URL** — share it with everyone

### Render (Alternative)
- Free Postgres and Redis
- Slower cold starts than Railway
- Better for static sites

### Production URL Looks Like
`https://deliveriq.up.railway.app/docs`

---

# Resume Tips

### Format (place under "Projects" section)
```
DeliverIQ — Order Dispatch API   [GitHub] [Live Demo]
Python · FastAPI · PostgreSQL · Redis · Kafka · Docker
• Designed a food delivery dispatch system with min-heap priority queue
  (O(log n)) and geohash-based rider matching (O(1) zone lookup), handling
  500 concurrent requests at p99 < 50ms.
• Built a fairness-aware rider assignment that balances rider earnings within
  a bounded distance band — reframing greedy-nearest as a constrained
  assignment problem without breaching delivery SLA.
• Built a Token Bucket rate limiter in Redis with <1ms overhead per request;
  reduced abusive traffic by 99% in load tests.
• Implemented an event-driven architecture with Kafka topics for order
  lifecycle events, enabling async notifications and decoupled analytics.
• Added idempotency keys for safe retries; deployed full stack
  (API + PostgreSQL + Redis + Kafka) via Docker Compose and GitHub
  Actions CI/CD to Railway.
```

### Rules
- ✅ **Quantify everything:** ms, RPS, complexity, %
- ✅ **Use industry vocabulary:** dispatch, idempotency, event-driven, geohash
- ✅ **Link GitHub AND live URL**
- ✅ **Put it under "Projects" not "Experience"**
- ❌ Don't say "learned" or "explored" — say "built", "designed", "implemented"

---

# How to Present Confidently

### The 2-Minute Pitch (Memorize)
> "I built DeliverIQ — a backend system that solves the order dispatch problem at companies like Zomato and Uber Eats.
>
> The core challenge: given hundreds of incoming orders and available riders, how do you assign them optimally in real time?
>
> I implemented a min-heap priority queue where each order gets a score based on value and wait time. For rider matching, I used geohashing — instead of computing distance to every rider, I look up the local grid cell in O(1).
>
> One thing that's mine: dispatch is fairness-aware — among riders within a distance band of the nearest, I assign to whoever has the fewest orders today, so earnings stay balanced without delivering cold food.
>
> The API has a Token Bucket rate limiter in Redis with sub-millisecond overhead, and an event-driven pipeline using Kafka — when an order is dispatched, downstream services (notifications, analytics, audit) consume the event independently.
>
> The whole stack runs in Docker Compose, has Prometheus + Grafana for observability, and is deployed on Railway with GitHub Actions CI/CD.
>
> What I'm proudest of is that every design decision has a clear reason — I can tell you exactly why I chose Token Bucket over Leaky Bucket, and Kafka over Redis Pub/Sub."

### Do's
- ✅ **Draw the architecture** on the whiteboard FIRST, then walk through it
- ✅ **Lead with the problem**, not the tech
- ✅ **Quote concrete numbers:** "500 RPS, p99 of 43ms"
- ✅ **Proactively mention trade-offs:** "I chose X, but Y would be better at scale because..."
- ✅ **Have one war story:** the bug that taught you something (your geohash boundary bug is perfect)

### Don'ts
- ❌ Don't say "I followed a tutorial"
- ❌ Don't apologize for missing features
- ❌ Don't list tech alphabetically — connect them: "FastAPI handles requests, Redis caches hot data, Kafka handles events"
- ❌ Don't go over 2 minutes without a question — pause and ask "should I go deeper on any part?"

### Body Language
- Stand if possible (energy + confidence)
- Smile when you mention something you're proud of
- Use your hands to draw boxes in the air when explaining architecture

---

# Final Polishing Checklist

### Code Quality
- [ ] No hardcoded secrets (check with `git log -p | grep -i password`)
- [ ] All functions have docstrings
- [ ] No dead code or commented-out blocks
- [ ] `black` and `flake8` pass with zero warnings
- [ ] `mypy` passes
- [ ] `pip freeze > requirements.txt` (pinned versions)
- [ ] Test coverage ≥ 60%

### GitHub
- [ ] README has: description, badges, live URL, architecture diagram, quickstart, design decisions
- [ ] At least 50 meaningful commits
- [ ] CI badge showing passing tests
- [ ] `.env.example` present, `.env` in `.gitignore`
- [ ] Tagged release `v1.0.0`
- [ ] Loom demo video linked
- [ ] Repo pinned on profile

### Deployment
- [ ] Live URL works at `/docs` (Swagger UI)
- [ ] `GET /health` returns DB + Redis + Kafka status
- [ ] App auto-restarts on crash
- [ ] HTTPS enabled (Railway gives this free)
- [ ] Grafana dashboard screenshot in README

### Interview Readiness
- [ ] Can explain every file in the codebase
- [ ] Know the Big-O of every algorithm
- [ ] Have an answer for "what breaks at 10x scale"
- [ ] Have an answer for "what's next"
- [ ] Can sketch the architecture from memory in 2 mins
- [ ] 2-minute pitch memorized
- [ ] 5 war stories ready (bugs, design choices, trade-offs)

---

# Common Pitfalls to Avoid

1. **Tutorial Hell** — Don't watch 10 hours of Kafka videos. Read docs, build immediately.
2. **Refactoring too early** — Make it work first. Refactor in Week 7 (Day 43).
3. **Skipping tests** — Without tests, your "done" features will silently break.
4. **Hardcoding secrets** — Never. Use `.env` from Day 24 (and `.gitignore` from Day 4).
5. **Big commits** — Commit small and often. One commit = one logical change.
6. **Ignoring errors** — Read every error message. Search the exact text. (→ See Stuck Protocol)
7. **Not asking for help** — Stuck >45 min? Ask Claude, ChatGPT, Stack Overflow.
8. **Comparing to others** — Your only competition is yesterday-you.

---

# Master Resource Library

## YouTube Channels to Follow
| Channel | Why |
|---|---|
| **Corey Schafer** | Best Python tutorials |
| **ArjanCodes** | Python best practices, design |
| **pixegami** | FastAPI focused |
| **Hussein Nasser** | Backend deep dives |
| **TechWorld with Nana** | Docker, K8s, DevOps |
| **Fireship** | Quick concept explainers (100 seconds series) |
| **ByteByteGo** | System design |
| **Confluent Developer** | Kafka official |

## Official Docs (Bookmark These)
| Tool | URL |
|---|---|
| FastAPI | https://fastapi.tiangolo.com |
| SQLAlchemy | https://docs.sqlalchemy.org/en/20/ |
| Redis | https://redis.io/docs/ |
| Kafka (Confluent) | https://developer.confluent.io |
| Docker | https://docs.docker.com |
| Pydantic | https://docs.pydantic.dev |
| Pytest | https://docs.pytest.org |

## Books (Optional, if time)
- "Designing Data-Intensive Applications" — Martin Kleppmann (reference, not cover-to-cover)
- "Fluent Python" — Luciano Ramalho (Python deep dive)

## When Stuck
1. **Read the exact error message** (90% of the time it tells you the fix)
2. **Google the exact error**
3. **Ask Claude/ChatGPT** with: error + relevant code + what you tried (use the Stuck Protocol format)
4. **Stack Overflow** for tricky ones
5. **Discord:** [FastAPI Discord](https://discord.gg/VQjSZaeJmf), [Python Discord](https://pythondiscord.com)

---

# Final Sanity Check

Before you start Day 1, ensure:
- [ ] You're on Ubuntu with ~10GB free disk space (Day 0 confirms this)
- [ ] You can dedicate 3–4 hours daily (no exceptions for 45 days)
- [ ] You have a GitHub account
- [ ] You're emotionally ready to be confused — that's the LEARNING part

**Don't read this whole doc again.** Open Day 0, then Day 1. Start.

---

# Closing Words

This roadmap is comprehensive because **your goal is comprehensive** — beating 90% of candidates at top product companies. Three things to remember:

1. **Discipline > Motivation.** Show up daily. Even 1 hour beats 8 hours once a week.
2. **Build > Watch.** Every concept you learn, immediately use it in DeliverIQ.
3. **Depth > Breadth.** Knowing Kafka deeply beats knowing 10 frameworks superficially.

You're a Codeforces Specialist and LeetCode Knight — the algorithmic muscle is already there. This project simply wraps that muscle in the production skin interviewers want to see: APIs, databases, caching, queues, events, deployment.

On Day 45, you'll have something rare: a project you can defend in any technical interview because every line came from your fingers.

**Now stop reading. Open the terminal (Ctrl+Alt+T). Start Day 0.**

🚀 *See you on Day 45.*
