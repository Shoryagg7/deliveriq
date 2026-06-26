# DeliverIQ — 45-Day Master Plan (v3.2 — Ubuntu Edition, Corrected)
### Zero Backend Experience → Production-Grade Backend API

**For:** Shorya Gupta — final-year CSE (Thapar, grad 2027) · Codeforces **Expert** · CodeChef 3★ · LeetCode Knight · 1500+ problems. Strong C++/DSA, learning backend.
**System:** Ubuntu Linux (every command here is Ubuntu-specific).
**Stack:** Python 3.14 · FastAPI · SQLAlchemy 2.0 · Pydantic · Alembic · PostgreSQL 18 · Redis · Kafka · Docker.

---

## What changed in v3.2 (read this first)

This version fixes real bugs and reconciles the plan with what was actually built on Days 15–18. The corrections:

1. **Day 16 "Break It" was factually wrong** and is rewritten. The old version claimed deleting the `expire` line makes the token bucket "permanently empty" so requests fail after 3 minutes. That is false for a *token bucket* — it recovers from the **elapsed-time refill math**, not from the key's TTL. The `expire` line is **memory housekeeping** (it garbage-collects buckets of clients who vanish), not the recovery mechanism. The old claim confused token-bucket with fixed-window (where the TTL *is* the reset). Corrected exercise is in Day 16.

2. **Day 9 latitude boundary bug.** Old: `Field(gt=-90, le=90)`. Latitude **−90** (south pole) is valid, and `gt` wrongly rejects it. Fixed to `ge=-90` (closed interval), applied symmetrically to **both** pickup and drop coordinates.

3. **Day 17 dispatch reconciled to what was built.** The primary implementation is now a **Python `heapq` over PENDING orders pulled from PostgreSQL** (which is what you built and what showcases your DSA), with the **Redis sorted-set** version reframed as the *distributed scale-up* — a strong interview talking point rather than a contradiction.

4. **`datetime.utcnow()` is deprecated on Python 3.14.** Replaced everywhere with `datetime.now(UTC)` (timezone-aware).

5. **`OrderStatus` enum defined once.** It previously appeared in both `schemas/order.py` (Day 9) and `services/order_state.py` (Day 19) — two definitions of the same thing. Now it lives in `app/core/enums.py` and is imported everywhere.

6. **Day 38 health check** used `db.execute("SELECT 1")`, which errors on SQLAlchemy 2.0. Fixed to `db.execute(text("SELECT 1"))`.

7. **Naming consistency.** Routers and models both use the **singular** filename (`order.py`, `rider.py`). The filename is arbitrary — what matters is that the import path matches.

8. **Rate-limiter hardening notes added** (Day 16): `request.client` None-guard now; `X-Forwarded-For` / trusted-proxy handling is explicitly a **deployment-phase** concern (the header is spoofable without a trusted proxy in front). Sliding-window is parked as an optional **Day-40 stretch** — you understand the fixed-window vs sliding-window tradeoff well enough to *speak* to it without building it.

---

## How This Plan Is Structured

Each day has:
- 🎯 **Goal** — what you'll achieve
- 📚 **Resources** — official docs + ONE best video (≤30 min)
- 💻 **Tasks** — exactly what to code
- ✅ **End of Day** — proof you completed it

Some days also have:
- 💡 **C++ → Python** — maps new Python to the C++/CP you already own
- 🔥 **Break It On Purpose** — sabotage your own code to feel *why* each piece exists
- 📝 **Interview Answer** — filled-in talking points, written the day you build the feature
- 🐧 **Ubuntu Note** — Linux specifics that aren't obvious
- 🐛 **Stuck Protocol** — your debugging checklist (defined Day 1)

**Working rule:** ≤30 min of watching, then START CODING. Don't binge tutorials.

**Pacing rule (yours):** one small step at a time, understand the *why*, run it and watch it behave, confirm before moving on. Verify each step actually took effect — a silent failure (a server that didn't restart, a file that didn't save) is how you end up debugging ghosts.

---

## Why This Project Wins

**One-line pitch:**
> A production-grade REST API that dispatches food-delivery orders to riders using priority queues, geohashing, rate limiting, and event streaming — built with FastAPI, Redis, Kafka, PostgreSQL, and Docker.

**The differentiator (your answer to "how is this different from Swiggy?"):**
> Dispatch is **fairness-aware**. Among riders within a bounded distance band Δ of the nearest, it assigns to the one with the fewest orders today — balancing rider earnings without breaching delivery SLA. This reframes naive greedy-nearest as a **bounded constrained-assignment problem**, and gives an honest social-impact answer: fairer earnings distribution for gig riders.

**Why interviewers will care:**
- Uber/Zomato/Swiggy have teams building exactly this.
- **Not a clone** — the fairness-banded dispatch is a defensible design choice that's *yours*.
- Razorpay/PhonePe care about rate limiting, idempotency, webhooks (all included).
- 5+ system-design concepts in ONE codebase.
- Pure backend — no frontend complexity eating your time.
- Every line is defensible. No "I copied a tutorial" smell.

---

## Tech Stack in Plain English

| Tool | What it is | Why we use it |
|---|---|---|
| **Python** | Language | Easy syntax, huge ecosystem, industry standard |
| **FastAPI** | Web framework | Builds REST APIs fast, auto-generates docs |
| **PostgreSQL** | Database | Stores orders, riders, logs permanently |
| **SQLAlchemy** | ORM | Write Python instead of raw SQL |
| **Alembic** | Migrations | Tracks DB schema changes safely |
| **Redis** | In-memory store | Microsecond reads for counters, caches, queues |
| **Kafka** | Event streaming | Durable, replayable events between services |
| **Docker** | Containers | Packages the app so it runs anywhere |
| **Docker Compose** | Multi-container | Starts API + Postgres + Redis + Kafka together |
| **pytest** | Testing | Automated tests |
| **Git + GitHub** | Version control | Tracks changes, hosts your repo |
| **Railway** | Hosting | Deploys to a live public URL |

🐧 **Ubuntu Note:** Modern Docker uses `docker compose` (a space — built-in plugin), NOT the old `docker-compose` (hyphen). This doc uses `docker compose`.

---

## Project Folder Structure

You grow this **organically** — create each folder only when you first need it.

```
deliveriq/
│
├── app/
│   ├── __init__.py
│   ├── main.py             ← starts the FastAPI app (entry point)
│   │
│   ├── core/               ← shared infrastructure (glue)
│   │   ├── config.py       ← reads secrets from .env
│   │   ├── database.py     ← PostgreSQL connection
│   │   ├── redis_client.py ← Redis connection
│   │   └── enums.py        ← OrderStatus (one definition, imported everywhere)
│   │
│   ├── models/             ← DB table definitions (SQLAlchemy)
│   │   ├── order.py
│   │   └── rider.py
│   │
│   ├── schemas/            ← request/response shapes (Pydantic)
│   │   ├── order.py
│   │   └── rider.py
│   │
│   ├── routers/            ← API endpoints grouped by topic
│   │   ├── order.py
│   │   └── rider.py
│   │
│   ├── services/           ← business logic / algorithms
│   │   ├── dispatch.py     ← priority-queue dispatch
│   │   ├── geohash_service.py ← rider matching + fairness band
│   │   └── order_state.py  ← state-machine transitions
│   │
│   ├── middleware/         ← runs on EVERY request (rate limiter)
│   ├── workers/            ← background consumers (Pub/Sub, Kafka)
│   └── utils/              ← shared helpers
│
├── tests/
├── .env                    ← SECRETS — never commit
├── .env.example            ← template (commit this)
├── .gitignore
├── requirements.txt
├── README.md
├── Dockerfile
└── docker-compose.yml
```

**The principle — separation of concerns:**
- **Routers** = *what endpoints exist* (routing only)
- **Schemas** = *what shape data has* (validation only)
- **Services** = *how the logic works* (the smart stuff)
- **Models** = *what the DB stores* (persistence only)
- **Core** = glue (config, connections, shared enums)

💡 **C++ → Python:** `__init__.py` (usually empty) marks a folder as an importable package — loosely like a header that makes a directory includable. `from app.models.order import Order` is the rough equivalent of `#include "order.h"` plus a namespace.

### Folder Unlock Schedule

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

## Day 0 — Ubuntu System Check (30 min, before Day 1)

### 🎯 Goal
Verify your system is ready. On a fresh Ubuntu install, none of these may exist yet — that's fine.

```bash
lsb_release -a          # Ubuntu 20.04+/22.04/24.04
uname -a                # should mention "Linux"
python3 --version       # 3.8+; we use 3.14 for this project
pip3 --version          # else: sudo apt install python3-pip -y
git --version           # else: sudo apt install git -y
curl --version          # else: sudo apt install curl -y
df -h ~                 # ≥10GB free (Docker images are large)
ping -c 3 google.com    # internet check
sudo apt update && sudo apt upgrade -y   # once; 5–10 min
```

🐧 **Ubuntu Note:** Terminal paste is **Ctrl+Shift+V**. Ctrl+C kills a process, Ctrl+L clears screen, Tab autocompletes, Up arrow recalls last command.

### ✅ End of Day 0
All checks pass.

---

# PHASE 1 — Python + Git Fundamentals (Days 1–7)

## Day 1 — Install Everything + Hello World

### 🎯 Goal
Install tools the Ubuntu way, write your first Python program, push to GitHub, learn the Stuck Protocol.

### 📚 Resources
- [Python in 1 Hour — Mosh](https://www.youtube.com/watch?v=kqtD5dpn9C8) *(first 30 min)*
- [Python + VS Code Setup — Corey Schafer](https://www.youtube.com/watch?v=-nh9rCzPJ20) *(15 min)*

### 💻 Tasks
```bash
# Python (use 3.14 for this project; side-by-side installs are fine on Ubuntu)
sudo apt update
sudo apt install python3 python3-venv python3-dev python3-pip git -y

# VS Code
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update && sudo apt install code -y

# Workspace
cd ~ && mkdir -p projects/deliveriq && cd projects/deliveriq && code .
```
Install the **Python** extension (Microsoft) in VS Code.

`hello.py`:
```python
name = "DeliverIQ"
print(f"Welcome to {name}!")

foods = ["pizza", "burger", "biryani"]
for f in foods:
    print(f"Delivering: {f}")
```
Run: `python3 hello.py`

🐧 **Ubuntu Note:** Outside a venv, always use `python3`/`pip3` — plain `python`/`pip` may not exist.

### 🐛 STUCK PROTOCOL — use this for the next 45 days
```
Step 1 (5 min): Read the error. The LAST line is usually the real error.
                Look for any line mentioning a file in YOUR project (not venv/).
Step 2 (5 min): Google the exact last line in quotes. Add "Ubuntu" or "FastAPI".
Step 3 (5 min): Check common Ubuntu causes:
  ModuleNotFoundError       → venv not activated: source venv/bin/activate
  ConnectionRefusedError    → service down: systemctl status postgresql / redis-server
  Address already in use    → old process on the port: fuser -k 8000/tcp
  python: command not found → use python3
  422 Unprocessable Entity  → Pydantic schema mismatch — check your JSON body
Step 4 (15 min): Ask for help in this format:
  "Ubuntu, DeliverIQ + FastAPI, Day [X].
   Trying to: [one sentence]. Full error: [paste]. File: [paste]. Tried: [steps 1-3]."
```

### ✅ End of Day
`Welcome to DeliverIQ!` prints; you know where to look when things break.

---

## Day 2 — Variables, Functions, Classes

### 🎯 Goal
Core Python syntax.

### 📚 Resources
- [Python OOP in 30 min — Tech With Tim](https://www.youtube.com/watch?v=JeznW_7DlB0)

### 💻 Tasks — `practice.py`
```python
def calculate_priority(order_value: float, wait_minutes: int) -> float:
    """Higher score = more urgent."""
    return order_value * 0.4 + wait_minutes * 0.6

print(calculate_priority(500, 15))  # 209.0

class Rider:
    def __init__(self, rider_id: int, name: str):
        self.rider_id = rider_id
        self.name = name
        self.is_available = True

    def assign_order(self, order_id: int) -> bool:
        if not self.is_available:
            return False
        self.is_available = False
        print(f"Rider {self.name} assigned to order {order_id}")
        return True

r = Rider(1, "Suresh")
r.assign_order(101)
r.assign_order(102)  # fails — already busy
```

### ✅ End of Day
You understand functions, type hints, classes, `self`, `__init__`.

---

## Day 3 — Data Structures + Comprehensions

### 💡 C++ → Python
```
vector<int>            → list   [1, 2, 3]
unordered_map<str,int> → dict   {"k": 1}
unordered_set<int>     → set    {1, 2, 3}
pair<int,int>          → tuple  (1, 2)
cout << x              → print(x)
nullptr                → None
true / false           → True / False
```

### 💻 Tasks
```python
orders = [
    {"id": 1, "value": 250, "status": "PENDING"},
    {"id": 2, "value": 800, "status": "DELIVERED"},
    {"id": 3, "value": 450, "status": "PENDING"},
]
pending_ids = [o["id"] for o in orders if o["status"] == "PENDING"]   # [1, 3]
order_values = {o["id"]: o["value"] for o in orders}                  # {1:250, 2:800, 3:450}
total = sum(o["value"] for o in orders if o["status"] == "PENDING")   # 700
```

### ✅ End of Day
You can write list/dict comprehensions without looking them up.

---

## Day 4 — Git + GitHub

### 📚 Resources
- [Git for Beginners — Mosh](https://www.youtube.com/watch?v=8JJ101D3knE) *(first 30 min)*

### 💻 Tasks
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git init && git branch -M main
```
`.gitignore`:
```
__pycache__/
*.pyc
venv/
.env
.vscode/
.idea/
```
```bash
git add . && git commit -m "chore: initial commit"
# create empty repo "deliveriq" on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/deliveriq.git
git push -u origin main
```

### ✅ End of Day
Code is on GitHub; first green square appears.

---

## Day 5 — Virtual Environments + pip

### 💻 Tasks
```bash
python3 -m venv venv
source venv/bin/activate          # prompt now shows (venv)
pip install fastapi "uvicorn[standard]"
pip freeze > requirements.txt
git add requirements.txt && git commit -m "chore: add FastAPI deps" && git push
```
🐧 **Ubuntu Note:** Activation is always `source venv/bin/activate`. `venv\Scripts\activate` is Windows — ignore it. Leave with `deactivate`.

💡 **C++ → Python:** A venv is a per-project set of linked libraries instead of polluting the global system. Each project gets a clean dependency tree.

### ✅ End of Day
`(venv)` shows; `requirements.txt` lists fastapi, uvicorn.

---

## Day 6 — App Structure (Entry Point Only)

### 🎯 Goal
Create just `app/` and `app/main.py`. Everything else comes later.

### 💻 Tasks
```bash
mkdir app && touch app/__init__.py
```
`app/main.py`:
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
```bash
uvicorn app.main:app --reload
```
Visit `http://localhost:8000/` and `http://localhost:8000/docs` (Swagger UI, free).

🐧 **Ubuntu Note:** `touch file` creates an empty file. Install `tree` (`sudo apt install tree -y`), then `tree app/` shows your layout.

### ✅ End of Day
`/docs` shows 2 endpoints; you can explain `main.py` line by line.

---

## Day 7 — Catch-up + DSA in Python

### 🎯 Goal
Build Python fluency by re-solving problems you already know in C++.

### 💡 C++ → Python
```
sort(v.begin(), v.end())   → v.sort()  /  sorted(v)
v.push_back(x)             → v.append(x)
v.size()                   → len(v)
m.count(k)                 → k in m
```

### 💻 Tasks
Solve in Python: **Two Sum**, **Reverse String** (in-place), **Valid Parentheses** (stack).

### ✅ End of Week 1
Python syntax, Git, venv, FastAPI running, clean entry point.

---

# PHASE 2 — FastAPI + PostgreSQL (Days 8–14)

## Day 8 — Path & Query Params

### 💻 Tasks — update `app/main.py` (in-memory for now)
```python
from enum import Enum
from fastapi import FastAPI, HTTPException

app = FastAPI(title="DeliverIQ")

orders_db = {
    1: {"id": 1, "value": 250, "status": "PENDING"},
    2: {"id": 2, "value": 800, "status": "DELIVERED"},
}

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"

@app.get("/orders")
def list_orders(status: OrderStatus | None = None):
    if status:
        return [o for o in orders_db.values() if o["status"] == status.value]
    return list(orders_db.values())
```

💡 **Why type the query param as an enum (not `str`)?** With `status: str`, FastAPI accepts *any* string — `?status=banana` silently returns `[]`, hiding the caller's mistake. With `status: OrderStatus`, FastAPI auto-rejects bad values with `422`, renders a **dropdown** in `/docs`, and makes the contract self-documenting. Push validation to the boundary so bad data can't get deep into your system.

### ✅ End of Day
You understand path params (`/orders/{id}`) vs query params (`?status=X`).

---

## Day 9 — Pydantic Models (Validation)

### 💡 C++ → Python
Pydantic `BaseModel` is a C++ `struct` that validates types automatically. Pass a string where a float is expected → Pydantic raises `422`. A C++ struct would silently accept garbage.

### 💻 Tasks

**Create the schemas folder + a single shared enum location:**
```bash
mkdir app/schemas && touch app/schemas/__init__.py
mkdir -p app/core && touch app/core/__init__.py   # if not present yet
```

`app/core/enums.py` — **define `OrderStatus` once, here:**
```python
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
```
> **Why a separate file?** Both your schemas *and* your models *and* your state machine need this enum. Defining it once in `core/enums.py` avoids duplicate definitions drifting apart (the old plan defined it twice — in schemas and again in the state machine).

`app/schemas/order.py`:
```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.core.enums import OrderStatus  # imported, not redefined

class OrderCreate(BaseModel):
    customer_id: int
    restaurant_id: int
    value: float = Field(gt=0, description="Order value in INR, must be positive")
    # latitude is the closed interval [-90, 90]; longitude is [-180, 180].
    # Use ge/le (inclusive), NOT gt/lt — -90 (south pole) and -180 are valid.
    # Validate pickup AND drop symmetrically.
    pickup_lat: float = Field(ge=-90, le=90)
    pickup_lon: float = Field(ge=-180, le=180)
    drop_lat: float = Field(ge=-90, le=90)
    drop_lon: float = Field(ge=-180, le=180)

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    value: float
    status: str
    created_at: datetime
```

> 🐛 **Corrected from v3:** old code used `Field(gt=-90, le=90)`, which rejects a valid `-90`, and only validated the drop coordinates. Both fixed above.

### ✅ End of Day
Sending a negative value or `lat=9999` returns `422` automatically.

---

## Day 10 — PostgreSQL Setup (Ubuntu)

### 💻 Tasks
```bash
sudo apt update && sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql && sudo systemctl enable postgresql

sudo -u postgres psql -c "CREATE USER deliveriq_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "CREATE DATABASE deliveriq_db OWNER deliveriq_user;"
psql -U deliveriq_user -d deliveriq_db -h localhost   # \q to exit
```
**DBeaver GUI:**
```bash
wget https://dbeaver.io/files/dbeaver-ce_latest_amd64.deb
sudo apt install ./dbeaver-ce_latest_amd64.deb   # './' upgrades in place, keeps connections
dbeaver &
```
Connect: host `localhost`, user `deliveriq_user`, password `password`, db `deliveriq_db`.

🐧 **Ubuntu Note:** `address already in use` on 5432 → find it with `sudo lsof -i :5432`. DBeaver feeling slow is almost always JVM memory pressure or a stale metadata cache — right-click the connection → **Invalidate/Reconnect** (F5) before ever reinstalling. Reinstalling is a guess, not a diagnosis.

### ✅ End of Day
DBeaver connected; `SELECT 1;` runs.

---

## Day 11 — SQLAlchemy + First DB Model

### 💻 Tasks
```bash
pip install sqlalchemy psycopg2-binary
pip freeze > requirements.txt
```
`app/core/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://deliveriq_user:password@localhost:5432/deliveriq_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency: one DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
`app/models/order.py`:
```python
from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Float, DateTime
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
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
```
> 🐛 **Corrected from v3:** `datetime.utcnow` is deprecated on Python 3.14. Use `datetime.now(UTC)` (timezone-aware). Wrapped in a `lambda` so it's evaluated **per insert**, not once at import.

> 💡 **PostgreSQL id sequences never reset on DELETE.** The id is auto-incremented by a *sequence* — a counter independent of the rows. Delete all rows, insert again → you get the *next* number, not 1. Gaps are intentional and correct: ids must be unique forever so old references (payments, logs) never silently re-point to a different order. Only `TRUNCATE ... RESTART IDENTITY` resets the counter — dev-only.

### ✅ End of Day
You understand ORM = "Python class ↔ DB table". (Table creation happens via Alembic on Day 14, not `create_all`.)

---

## Day 12 — Real CRUD with the Database

### 💻 Tasks
```bash
mkdir app/routers && touch app/routers/__init__.py
```
`app/routers/order.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import OrderStatus
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
def list_orders(status: OrderStatus | None = None, db: Session = Depends(get_db)):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status.value)  # .value → the stored string
    return query.all()
```
`app/main.py`:
```python
from fastapi import FastAPI
from app.routers import order

app = FastAPI(title="DeliverIQ")
app.include_router(order.router)

@app.get("/health")
def health():
    return {"status": "ok"}
```
Test in Swagger: create order, fetch it, see the row in DBeaver.

### ✅ End of Day
Orders persist. Folder now has `core/`, `models/`, `routers/`, `schemas/`.

---

## Day 13 — Rider Model + Endpoints (Independent Rep)

### 💻 Tasks — build without looking back
- `app/models/rider.py` — fields: `id, name, current_lat, current_lon, is_available, created_at` (use `datetime.now(UTC)` default)
- `app/schemas/rider.py` — `RiderCreate`, `RiderResponse`
- `app/routers/rider.py` — POST, GET by id, list
- Register in `main.py`: `app.include_router(rider.router)`

### ✅ End of Day
You can create/list riders via the API — proves Days 11–12 stuck.

---

## Day 14 — Alembic Migrations

### 🎯 Goal
Stop using `create_all`. Use real migrations — production never uses `create_all`, and interviewers ask about this.

### Why migrations exist — the `create_all` flaw (understand this before typing)
`create_all` **only creates tables that don't exist yet — it never alters an existing one.** Add a column to a model and run `create_all`: it does *nothing*, because the table already exists. Now your Python model and your real DB schema have **drifted apart**, and the next query referencing that column crashes. `create_all` is fine for spinning up an empty dev DB once; it's useless for *evolving* a schema, which is what real projects do constantly.

**Migrations** are versioned, incremental, reversible scripts that describe schema *changes* — an `upgrade()` to apply a change and a `downgrade()` to roll it back. Think **git for your database schema**: each migration is a commit, `alembic upgrade head` is checkout-latest, and every environment (your laptop, CI, production) replays the same ordered changes to land in an identical state. **Alembic** is the migration tool that pairs with SQLAlchemy.

> 💡 **C++ → Python:** a migration is like a versioned patch file for your DB. You don't re-describe the whole schema each time (that's `create_all`); you record the *diff* and apply diffs in order — exactly how a series of git commits builds up state.

### 💻 Tasks
```bash
pip install alembic
alembic init alembic
```
- In `alembic.ini`: set `sqlalchemy.url` to your DB URL.
- In `alembic/env.py`: import `Base` **and every model**, then set `target_metadata = Base.metadata`.
```python
# alembic/env.py (near the top)
from app.core.database import Base
from app.models.order import Order   # noqa: F401
from app.models.rider import Rider   # noqa: F401
target_metadata = Base.metadata
```
```bash
alembic revision --autogenerate -m "create orders and riders tables"
# REVIEW the generated upgrade()/downgrade() before applying ↓
alembic upgrade head
```
Remove any `Base.metadata.create_all()` from `main.py` — Alembic owns the schema now. Confirm the `alembic_version` table exists in Postgres.

### The three things that trip everyone up
1. **The import trap.** `env.py` must import the **model classes**, not just `Base`. A model only registers in `Base.metadata` when its file is *imported*. Miss the import → autogenerate thinks your models define *no* tables → it generates `DROP` statements for your real tables. (The `# noqa: F401` silences the "unused import" warning — the import *is* the work, even though the name isn't referenced.)
2. **Autogenerate is a draft, not gospel.** It diffs models vs DB and drafts a migration, but it can miss column renames (it sees a drop + an add) and some type changes. **Always read the generated `upgrade()` before running it.** The interview answer to "how do you handle migrations?" is exactly: *"autogenerate, then review before applying."*
3. **`alembic_version`** is a one-row table holding the current revision id. That single row is how Alembic knows where your DB stands and which migrations still need applying.

> 🐛 **`default=` ≠ `nullable=False` (carry-over from Day 11).** A model `default="PENDING"` fills the value via the ORM at insert time, but the column still allows `NULL` at the DB level. For a DB-*enforced* constraint, you also need `nullable=False`. They solve different problems — one supplies a value, the other forbids its absence.

### 📝 Interview Answer — save to `INTERVIEW_NOTES.md`
```
"Production never uses create_all — it only creates missing tables, it can't alter
existing ones, so schema and code drift apart. I use Alembic migrations: versioned,
reversible schema changes, like git for the DB. env.py imports Base AND every model
(miss a model import and autogenerate drops your real tables). Autogenerate drafts
the migration; I review the upgrade() before running it. alembic_version tracks the
current revision so every environment converges to the same schema."
```

### ✅ End of Week 2
Two tables, full CRUD, proper migrations, clean structure.

---

# PHASE 3 — Redis + Core Dispatch Logic (Days 15–21)

## Day 15 — Redis Setup + Mental Model

### 🎯 Goal
Install Redis, and *understand* what it is by watching keys store, count, and self-destruct.

### 📚 Resources
- [Redis in 20 minutes — Fireship](https://www.youtube.com/watch?v=G1rOthIU-uo)
- [Redis Data Types](https://redis.io/docs/data-types/)

### What Redis is (in CP terms)
PostgreSQL is your durable `std::map` backed by a file. Redis is a `std::unordered_map` living in RAM — O(1) lookups, microseconds, no durability guarantees by default. You use it for data you read thousands of times/sec and don't mind losing on restart: request counters, hot caches, queues.

### 💻 Step 1 — Install + verify
```bash
sudo apt update && sudo apt install redis-server -y
redis-cli ping        # → PONG  (proves the server is up on port 6379)
```
If it doesn't reply: `sudo systemctl start redis-server`.

### 💻 Step 2 — Feel it in the shell (type one at a time)
```bash
redis-cli
```
```
SET rider:42:orders 3        → OK        (store a key; ':' is just a naming convention)
GET rider:42:orders          → "3"       (O(1) RAM read)
INCR rider:42:orders         → (integer) 4   (atomic read-add-write — race-safe)
```
**`INCR` is the heartbeat of a rate limiter.** Atomic means 1000 concurrent requests can't corrupt the count.

### 💻 Step 3 — TTL: keys that delete themselves
```
SET session:99 active        → OK
EXPIRE session:99 10         → (integer) 1   (delete this key in 10s)
TTL session:99               → (integer) 8   (live countdown)
# wait ~10s
GET session:99               → (nil)         (gone — Redis deleted it, no cleanup code)
TTL session:99               → (integer) -2  (key does not exist)
```

### 💻 Step 4 — Hashes (one key, many fields — needed Day 16)
```
HSET bucket:test tokens 100 last_refill 1700000000   → (integer) 2
HGETALL bucket:test          → tokens / 100 / last_refill / 1700000000
HGET bucket:test tokens      → "100"
```
A hash is a tiny dict stored under one key. In Python (with `decode_responses=True`) `hgetall` returns a real dict, and values come back as **strings** (so you cast with `float(...)`).

### 💻 Step 5 — Python client (your app becomes another Redis client)
```bash
pip install redis && pip freeze > requirements.txt
```
`app/core/redis_client.py`:
```python
import redis
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
```
> `decode_responses=True` makes Redis return Python `str` instead of raw bytes (`b'3'`). One shared client, imported everywhere — same pattern as `database.py`.

### ✅ End of Day
You saw store / count / expire / hash behave live, and Python can `ping()` Redis.

---

## Day 16 — Token-Bucket Rate Limiter ⭐ (Most Important Day)

### What is middleware?
Every request flows through a pipeline. **Middleware wraps** that pipeline — it runs *before* your endpoint (can reject the request) and *after* it (can decorate the response). A **dependency**, by contrast, sits only on the *entry* path and never sees the response. That bidirectional position is exactly why the rate limiter is middleware: it both **gates** the request and **adds** a response header.

```
request → [rate-limit check] → (if allowed) → your endpoint → [add header] → response
```

### 🎯 Goal
Build the token-bucket limiter — your #1 interview talking point.

### 📚 Resources
- [Token Bucket — ByteByteGo](https://www.youtube.com/watch?v=mhUQe4BKZXs) *(7 min)*
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)

### The model
A bucket holds up to **100 tokens**, refilling continuously at **100/60 ≈ 1.67 tokens/sec**. Each request spends 1 token; an empty bucket → `429`. Recovery is computed from elapsed time:
```
tokens = min(CAP, tokens + elapsed_seconds * REFILL_RATE)
```
💡 **C++ → Python:** this is the simulation "accumulate a resource over a time delta, capped" pattern you've used in contests — but it runs on every HTTP request, with the Redis hash holding state between requests.

### 💻 Tasks
```bash
mkdir app/middleware && touch app/middleware/__init__.py
```
`app/middleware/rate_limiter.py`:
```python
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.redis_client import redis_client

BUCKET_SIZE = 100        # max tokens
REFILL_RATE = 100 / 60   # tokens per second (~1.67)

async def rate_limit_middleware(request: Request, call_next):
    # request.client can be None in some ASGI/test setups — guard it.
    client = request.client
    client_ip = client.host if client is not None else "unknown"
    client_key = request.headers.get("X-API-Key") or client_ip
    bucket_key = f"rate_limit:{client_key}"

    now = time.time()
    data = redis_client.hgetall(bucket_key)

    if not data:                      # first time we've seen this client
        tokens = float(BUCKET_SIZE)
        last_refill = now
    else:                             # refill by elapsed time
        tokens = float(data["tokens"])
        last_refill = float(data["last_refill"])
        elapsed = now - last_refill
        tokens = min(BUCKET_SIZE, tokens + elapsed * REFILL_RATE)

    if tokens < 1:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Try again later."},
        )

    tokens -= 1
    redis_client.hset(bucket_key, mapping={"tokens": tokens, "last_refill": now})
    redis_client.expire(bucket_key, 120)   # housekeeping: GC abandoned buckets

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(int(tokens))
    return response
```
Register in `main.py` (after `app = FastAPI(...)`):
```python
from app.middleware.rate_limiter import rate_limit_middleware
app.middleware("http")(rate_limit_middleware)
```

> ⚠️ **Deployment-phase note (not now):** keying on `request.client.host` is correct for local dev. **Behind a reverse proxy** (Railway/nginx), every request shows the *proxy's* IP, and the real client IP arrives in `X-Forwarded-For`. But that header is **client-settable and spoofable** — trusting it without verifying the request came from *your* trusted proxy lets anyone bypass the limiter by forging a new IP per request. So: handle XFF only at deployment, with a trusted-proxy check. The `X-API-Key` fallback above is fine because a key is an identifier you issue, not a security decision.

> 🐍 **Confirm the server actually restarted.** `--reload` silently does nothing if the port is still held by an old process — you'll see `ERROR: [Errno 98] Address already in use` and keep testing stale code. Kill the old one with `fuser -k 8000/tcp`, then relaunch and wait for `Application startup complete`.

### Test it — watch burst → throttle
```bash
URL=http://localhost:8000/orders
for i in $(seq 1 105); do curl -s -o /dev/null -w "%{http_code} " "$URL"; done; echo
```
You'll see ~100 × `200`, then `429` once the bucket drains. The first 429 body reads `{"error":"Rate limit exceeded. Try again later."}`.

### 🔥 Break It On Purpose (corrected)
**The point of `expire(bucket_key, 120)` is memory housekeeping, NOT recovery.** Prove it:
1. Keep `expire`. Make one request. In `redis-cli`: `TTL rate_limit:<your-key>` → ~120, counting down. If you stop, the key self-cleans.
2. Comment out the `expire` line, restart, make one request. `TTL rate_limit:<your-key>` → `-1` ("exists, no expiry"). **That key now lives forever** even if the client never returns — a slow memory leak across millions of one-time clients. *That* is the bug `expire` prevents.
3. Restore the line.

> ❌ **Why the old "wait 3 minutes, requests fail" claim was wrong:** after 3 minutes, `elapsed ≈ 180s`, so `tokens = min(100, 180 × 1.67) = 100` — the bucket refills to **full** from the timestamp math regardless of TTL. The follow-up requests would **succeed**. Deleting `expire` does *not* break recovery for a token bucket. (That claim is true for a *fixed-window* limiter, where the key's TTL *is* the reset — a different algorithm.)

### 📝 Interview Answer — save to `INTERVIEW_NOTES.md`
```
"I implemented a token-bucket rate limiter backed by Redis hashes.
Each client gets 100 tokens, refilled continuously at 100/min.
Each request costs 1 token; an empty bucket returns HTTP 429.
I chose token-bucket over fixed-window because it allows controlled bursts
up to bucket size AND avoids fixed-window's boundary-burst flaw (where a
client can fire 2x the limit straddling the reset edge).
The check is ~3 Redis ops (HGETALL/HSET/EXPIRE), sub-millisecond locally.
The expire(key,120) line is memory housekeeping for abandoned buckets, not
recovery — recovery comes from the elapsed-time refill. At scale I'd collapse
the read+write into one atomic Lua/pipeline call to remove the read-write race."
```

> 🧠 **Parked (optional Day-40 stretch): sliding window.** Fixed-window's flaw is the boundary burst. The smoother fix is a sliding-window log/counter (a Redis sorted set, ~20 lines), trading memory for smoothness. You don't need to *build* it — knowing the tradeoff is the interview value. Build only if an interviewer pushes for live coding, or as end-of-project hardening.

### ✅ End of Day
Limiter blocks after quota; you can explain token-bucket on a whiteboard and name what `expire` really does.

---

## Day 17 — Priority-Queue Dispatch

### 🎯 Goal
Decide which PENDING order gets handled next — your CP heap, applied to a real dispatch engine.

### 📚 Resources
- [Priority Queues — NeetCode](https://www.youtube.com/watch?v=wptevk0bshY)

### 💡 C++ → Python: `heapq`
`std::priority_queue` is a **max-heap** (`top()` = largest). Python's `heapq` is a **min-heap** with no max flag — so push the **negated** priority. Push tuples `(-priority, id)`; tuples compare element-by-element, exactly like `pair`.
```python
import heapq
heap = []
heapq.heappush(heap, (-2000, 2))   # value 2000, order 2
heapq.heappush(heap, (-150, 1))
neg, oid = heapq.heappop(heap)     # → (-2000, 2): highest real priority first
```
> ⚠️ `heapq` operates **on a plain Python list** — it's not a class you instantiate (unlike C++'s container adaptor).

### 💻 Build the dispatcher
```bash
mkdir app/services && touch app/services/__init__.py
```
`app/services/dispatch.py` — **heap over PENDING orders from Postgres:**
```python
import heapq
from sqlalchemy.orm import Session
from app.models.order import Order
from app.core.enums import OrderStatus

def pick_next_order(db: Session) -> int | None:
    # 1. only orders still waiting for a rider
    pending = db.query(Order).filter(Order.status == OrderStatus.PENDING.value).all()
    if not pending:
        return None

    # 2. build a max-heap by value via negation
    heap = []
    for o in pending:
        heapq.heappush(heap, (-o.value, o.id))

    # 3. pop the winner
    _, order_id = heapq.heappop(heap)

    # 4. assign it: flip status so it leaves the pending pool (durable in Postgres)
    by_id = {o.id: o for o in pending}      # reuse rows already in memory; no 2nd query, no None
    winner = by_id[order_id]
    winner.status = OrderStatus.ASSIGNED.value
    db.commit()
    return order_id
```
Endpoint in `app/routers/order.py`:
```python
from app.services.dispatch import pick_next_order

@router.post("/dispatch")
def dispatch_order(db: Session = Depends(get_db)):
    order_id = pick_next_order(db)
    if order_id is None:
        raise HTTPException(404, "No pending orders to dispatch")
    return {"dispatched_order_id": order_id}
```
**Use `POST`** — dispatch is an action that changes state, not a passive read.

### Test
Create orders with values 150 / 2000 / 500. Call `POST /orders/dispatch` repeatedly:
- → 2000's id (now ASSIGNED) → 500's id → 150's id → `404` (pool empty).

Verify in DBeaver: `SELECT id, value, status FROM orders;` shows each flipping to ASSIGNED.
🐍 To see the returned id in the terminal (uvicorn access logs only show the status code): `curl -X POST http://localhost:8000/orders/dispatch`.

### 🔥 Break It On Purpose
Negate the negation: push `(o.value, o.id)` instead of `(-o.value, o.id)`. Now `heappop` returns the **cheapest** order first — the ₹150 customer is dispatched before the ₹2000 one. That's the bug. Restore the minus sign.

### Enhancement — anti-starvation aging (add when ready)
Value-only priority can **starve** a cheap order forever behind a stream of expensive ones. Blend in wait time (the OS "aging" technique):
```python
priority = value + wait_minutes * WEIGHT
```
Push `(-priority, id)`. The longer an order waits, the higher it climbs until it beats fresh high-value orders. Naming "aging / starvation" is a senior signal.

### Honest complexity note (good interview material)
This rebuilds the heap from the DB each call and pops one element — O(n) build to extract one max, so for a *single* pick a plain `max()` does equal work. The heap earns its keep when you pop many in sequence or keep it warm across calls. State that openly.

### 📈 The distributed scale-up (Redis sorted set) — ⚠️ scheduled for Phase 4, NOT optional
At scale the queue shouldn't live inside one API process. Move it into a **Redis sorted set**: `ZADD orders:pending {id: priority}` on create, `ZREVRANGE ... 0 0` to peek the max, `ZREM` to claim it atomically. Benefits: O(log n) ops, shared across multiple API instances, and `ZREM` returning `1`-or-`0` is your **concurrent-dispatch guard** (two workers can't claim the same order). This is the natural "what breaks at scale, and how you'd fix it" answer.

> 🔑 **Why "later," not "now":** today you run a single uvicorn process — there's no second instance to share state with, so the sorted set would solve a problem you don't yet have (and you couldn't *demonstrate* the `ZREM` race-guard with only one worker). The heapq version is also the one that actually showcases your DSA; the sorted set *hides* the heap inside Redis. So heapq first, by design.

> 🟥 **Resume dependency — do not skip.** Your resume says **"distributed."** That word is only earned once this is built and you've shown the multi-instance race + `ZREM` fix. **Build it in Phase 4** (Day 26, Docker Compose) by running the API with 2+ replicas and moving the queue here — *then* "distributed" is true and demonstrable, and the race becomes one of your best war stories. If you finish the project without doing it, **soften the resume** ("designed for horizontal scaling" / "stateless API with externalized state") rather than leave an indefensible claim. Don't ship the word "distributed" with a single-instance heap behind it.

### 📝 Interview Answer — save to `INTERVIEW_NOTES.md`
```
"Dispatch selects the highest-priority PENDING order with a max-heap (Python
heapq, negated keys). Priority = value (+ wait-time aging to prevent starvation).
heappush/heappop are O(log n). I assign by flipping status PENDING→ASSIGNED and
committing, so the order leaves the pool. Single-process today; at scale I'd move
the queue to a Redis sorted set (ZADD/ZREVRANGE/ZREM) so it's shared across API
instances and ZREM gives an atomic concurrent-claim guard. Ties break by created_at."
```

### ✅ End of Day
3 orders dispatch highest-value-first, drain to `404`, statuses persist in Postgres.

---
## Day 18 — Geohash Rider Matching + Fairness Band ⭐ (The Differentiator)

### 🎯 Goal
Find nearby riders *without scanning all riders*, then pick one **fairly** — the feature that makes DeliverIQ yours.

### 📚 Resources
- [Geohash Explorer](https://geohash.softeng.co/)

### Two layers (keep them distinct)
1. **Geohash = efficiently find who's nearby.** Encode (lat, lon) into a short string where **nearby points share a prefix**. "Find nearby riders" becomes a cheap prefix/set lookup instead of computing distance to every rider.
2. **Fairness band = among the nearby, choose fairly.** Within a distance band Δ of the closest candidate, assign to whoever has the fewest orders today.

💡 **C++ → Python:** geohash is **grid bucketing / spatial hashing** — exactly the coordinate-bucketing trick you use for nearest-neighbour, so you only check nearby cells instead of all pairs. Prefix length = grid resolution.

> 🗂️ **Where rider data lives:** riders are persisted in **PostgreSQL** (source of truth, Day 13). Day 18 *also* indexes their live location in **Redis** for fast geohash lookup. Redis is a hot cache over the durable Postgres record.

### 💻 Layer 1 + 2 — the service
```bash
pip install python-geohash && pip freeze > requirements.txt
```
`app/services/geohash_service.py`:
```python
import math
import time
from datetime import UTC, datetime

import geohash

from app.core.redis_client import redis_client

PRECISION = 6  # ~1.2 km cells


def _orders_key(rider_id: int) -> str:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"rider:{rider_id}:orders:{today}"


def add_rider(rider_id: int, lat: float, lon: float):
    cell = geohash.encode(lat, lon, PRECISION)
    redis_client.sadd(f"geohash:{cell}", rider_id)
    redis_client.hset(
        f"rider:{rider_id}:loc", mapping={"lat": lat, "lon": lon, "cell": cell}
    )


def find_nearby_riders(lat: float, lon: float) -> list[int]:
    cell = geohash.encode(lat, lon, PRECISION)
    cells_to_check = [cell] + geohash.neighbors(cell)  # home + 8 neighbours
    riders = set()
    for c in cells_to_check:
        riders.update(redis_client.smembers(f"geohash:{c}"))
    return [int(r) for r in riders]


def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6_371_000  # earth radius, metres
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
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
        orders_today = int(redis_client.get(_orders_key(rid)) or 0)
        scored.append((rid, dist, orders_today))
    if not scored:
        return None

    d_min = min(s[1] for s in scored)
    feasible = [s for s in scored if s[1] <= d_min + band_m]  # within band of nearest
    feasible.sort(key=lambda s: (s[2], s[1]))  # fewest orders, then nearest
    chosen = feasible[0][0]

    redis_client.hset(f"rider:{chosen}", "last_assigned_at", int(time.time()))
    key = _orders_key(chosen)
    redis_client.incr(key)
    redis_client.expire(key, 172800)   # 48h TTL — auto-cleans old days
    return chosen
```

> **Heap framing for interviews:** the selection is a min-heap on the composite key `(orders_today, distance)` over the small feasible band — greedy on a composite key, O(k log k) on candidate set k, not O(n) over all riders.

> **State-lifecycle note (built):** `orders_today` resets via the date-stamped key `rider:{id}:orders:{YYYY-MM-DD}` — the date in the key name *is* the reset (tomorrow is a fresh key at 0, no cron). A sliding 48h TTL garbage-collects past days. The count (`incr`) and the TTL (`expire`) are independent on the same key.

### 💻 The endpoint
`app/routers/rider.py`:
```python
from pydantic import BaseModel
from app.services.geohash_service import select_rider

class MatchRequest(BaseModel):
    lat: float
    lon: float

@router.post("/match")
def match_rider(req: MatchRequest, db: Session = Depends(get_db)):
    rider_id = select_rider(req.lat, req.lon)
    if rider_id is None:
        raise HTTPException(404, "No available rider nearby")
    return {"assigned_rider_id": rider_id}
```
> **Use POST, not GET** — matching increments the winner's order count (a side effect). GETs must stay safe/idempotent. Same reasoning as `POST /orders/dispatch`.

### Test
Seed via the service (no HTTP route adds rider locations yet), then hit `/match`:
```python
# python shell
from app.services.geohash_service import add_rider
from app.core.redis_client import redis_client
from datetime import UTC, datetime

redis_client.flushdb()
add_rider(1, 28.6139, 77.2090)   # nearest
add_rider(2, 28.6145, 77.2095)   # ~80 m
add_rider(3, 28.6150, 77.2100)   # ~150 m
# make rider 1 busy so fairness has work to do
redis_client.set(f"rider:1:orders:{datetime.now(UTC).strftime('%Y-%m-%d')}", 5)
```
```bash
# fire the same request repeatedly, watch the winner change
for i in $(seq 1 11); do
  curl -s -X POST http://localhost:8000/riders/match \
    -H "Content-Type: application/json" \
    -d '{"lat": 28.6139, "lon": 77.2090}'; echo
done
```
Expected: riders **2 and 3 alternate** (absorbing orders, climbing together) while rider 1 stays frozen at 5 — then once all three tie at 5, rider **1** wins on the distance tiebreak (it's at the order's exact spot). The system drains the load imbalance first, then reverts to nearest-rider.

### 🔥 Break It On Purpose
**(a) Boundary bug:** in `find_nearby_riders`, change `cells_to_check` to just `[cell]` (drop neighbours). Rider at lat=28.6139, lon=77.2090; order at 28.6140, 77.2091 (≈10 m, just across a cell edge). Match returns no rider. Restore neighbours.

**(b) Band vs SLA — both riders must be *within geohash range*:** the band only filters riders geohash already found, so a rider 4 km away is irrelevant (the neighbour ring ~3.6 km already excluded them — no band size rescues it). To see the tradeoff, place both inside range:
```python
redis_client.flushdb()
add_rider(1, 28.6139, 77.2090)              # nearest
add_rider(2, 28.6150, 77.2100)              # ~150 m away
redis_client.set(f"rider:1:orders:{datetime.now(UTC).strftime('%Y-%m-%d')}", 10)  # near rider slammed

select_rider(28.6139, 77.2090)              # band 500: rider 2 inside band → idle rider 2 wins
select_rider(28.6139, 77.2090, band_m=50)   # band 50:  rider 2 outside band → slammed rider 1 wins
```
Same riders, same loads — only Δ changed, and the winner inverts. **That's the tunable knob:** wide band = more fairness (spread earnings), narrow band = tighter SLA. Fairness only ever operates *inside* the band.

### 📝 Interview Answer
> Full concept→soundbite→gotcha writeup is in [Interview_notes](docs/Interview_prep.md) §14–15. One-line summary: geohash for a coarse O(1)-ish candidate set (home cell + 8 neighbours), haversine to rank it, then a fairness band — among riders within Δ of the nearest, assign the least-loaded. Reframes greedy-nearest as a bounded constrained-assignment problem; the hard band makes the SLA guarantee explicit and tunable (a blended score could silently send a far rider).

### ✅ End of Day
Riders seeded → `POST /riders/match` returns the fairly-chosen nearby rider; fairness convergence and the band/SLA tradeoff both demonstrated live.

### 🔄 Rider Sync — keep Postgres and Redis consistent (added after initial Day 18)

Riders live in **two stores**: PostgreSQL (durable truth, Day 13) and Redis (hot geohash index). Every rider write must update **both**, or `select_rider` reads a stale index. Three pieces close the loop. *(Concept writeup — dual-write consistency, recovery, why orders don't have this problem — is in `Interview_prep.md` §17.)*

#### 1. Create also indexes into Redis
```python
@router.post("", response_model=RiderResponse, status_code=201)
def create_rider(rider: RiderCreate, db: Session = Depends(get_db)):
    new_rider = Rider(**rider.model_dump())
    db.add(new_rider)
    db.commit()
    db.refresh(new_rider)            # need the DB-generated id BEFORE indexing
    add_rider(new_rider.id, new_rider.current_lat, new_rider.current_lon)
    return new_rider
```
> Order is forced: `add_rider` needs the id Postgres generates on insert → `commit` → `refresh` → `add_rider`. Index before refresh and the id is still `None`.

#### 2. The move path — update location, clean the old cell
`add_rider` only ever `sadd`s the new cell, never leaves the old one → phantom membership on move. Remove from the old cell first (`srem`). Add to `geohash_service.py`:
```python
def update_rider_location(rider_id: int, lat: float, lon: float):
    old_cell = redis_client.hget(f"rider:{rider_id}:loc", "cell")
    new_cell = geohash.encode(lat, lon, PRECISION)
    if old_cell and old_cell != new_cell:
        redis_client.srem(f"geohash:{old_cell}", rider_id)   # leave stale cell
    redis_client.sadd(f"geohash:{new_cell}", rider_id)
    redis_client.hset(f"rider:{rider_id}:loc",
                      mapping={"lat": lat, "lon": lon, "cell": new_cell})
```
Endpoint in `rider.py`:
```python
class LocationUpdate(BaseModel):
    lat: float
    lon: float

@router.patch("/{rider_id}/location")
def update_location(rider_id: int, loc: LocationUpdate, db: Session = Depends(get_db)):
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(404, "Rider not found")
    rider.current_lat, rider.current_lon = loc.lat, loc.lon   # Postgres = truth
    db.commit()
    update_rider_location(rider_id, loc.lat, loc.lon)          # Redis index follows
    return {"status": "updated", "rider_id": rider_id}
```
> **PATCH** — partial update of an existing resource. Postgres first (truth), then Redis (derived index).

#### 3. Rider model — `utcnow` fix (missed in v3.2's sweep)
```python
# app/models/rider.py
from datetime import datetime, UTC
created_at = Column(DateTime, default=lambda: datetime.now(UTC))
```
> Deprecated/naive `utcnow` → `datetime.now(UTC)`; `lambda` defers to per-insert. Migration-free (default lives in the ORM, not the DB column).

### 🧪 Sync test (HTTP, no manual seeding)
```bash
redis-cli flushall
# 1. create → auto-index, then match at that spot
curl -X POST :8000/riders -H "Content-Type: application/json" \
  -d '{"name":"Suresh","current_lat":28.6139,"current_lon":77.2090}'
curl -X POST :8000/riders/match -H "Content-Type: application/json" \
  -d '{"lat":28.6139,"lon":77.2090}'                       # → assigned_rider_id: 1
# 2. move to Mumbai, match at OLD spot → must 404 (old cell cleaned)
curl -X PATCH :8000/riders/1/location -H "Content-Type: application/json" \
  -d '{"lat":19.0760,"lon":72.8777}'
curl -X POST :8000/riders/match -H "Content-Type: application/json" \
  -d '{"lat":28.6139,"lon":77.2090}'                       # → 404 No available rider
# 3. match at NEW spot → found
curl -X POST :8000/riders/match -H "Content-Type: application/json" \
  -d '{"lat":19.0760,"lon":72.8777}'                       # → assigned_rider_id: 1
```
Test 2 returning **404** is the critical proof — `srem` removed the rider from the old Delhi cell. *(Note: the `orders_today` counter key is stamped in **UTC**, so on IST it may read e.g. `...:2026-06-26` after midnight UTC — inspect via `redis-cli get rider:1:orders:<UTC-date>`, not DBeaver. DBeaver shows only Postgres.)*
---

## Day 19 — Order State Machine

### 🎯 Goal
Stop order status from being set to anything arbitrary. Enforce a **legal lifecycle** — a directed graph of allowed transitions — and route *every* status change through one gate.

### 💡 C++ → Python
The transition table is an **adjacency list**: `map<State, set<State>>`. "Is this transition legal?" is "is `target` in the neighbour set of `current`?" — an O(1) set lookup. Terminal states (DELIVERED, CANCELLED) have empty neighbour sets — nothing is reachable from them.

### ⚠️ Prerequisite — consolidate `OrderStatus` first
Before Day 19, `OrderStatus` must live in **one** place. If it's still defined in `schemas/order.py` (and `dispatch.py` uses raw `"PENDING"`/`"ASSIGNED"` strings, and `order_state.py` imports from a non-existent `core.enums` behind a `# type: ignore`), fix that first:
1. Create `app/core/enums.py` with the full 5-value enum (PENDING, ASSIGNED, PICKED_UP, DELIVERED, CANCELLED).
2. In `schemas/order.py`: delete the class, replace with `from app.core.enums import OrderStatus`.
3. In `dispatch.py`: import the enum, replace raw strings with `OrderStatus.PENDING.value` / `OrderStatus.ASSIGNED.value`.
4. Remove every `# type: ignore` that was masking the broken import.
5. Verify: `python -c "from app.core.enums import OrderStatus; from app.services.order_state import transition; from app.services.dispatch import pick_next_order; print('all imports OK')"`

> A `# type: ignore` on an import is a smell — it was silencing a real `ModuleNotFoundError`. Comments that suppress errors usually hide the bug you need to see.

### 💻 The state machine — `app/services/order_state.py`
```python
from app.core.enums import OrderStatus   # the one definition

VALID_TRANSITIONS = {
    OrderStatus.PENDING:   {OrderStatus.ASSIGNED, OrderStatus.CANCELLED},
    OrderStatus.ASSIGNED:  {OrderStatus.PICKED_UP, OrderStatus.CANCELLED},
    OrderStatus.PICKED_UP: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),     # terminal
    OrderStatus.CANCELLED: set(),     # terminal
}

class InvalidTransition(Exception):
    pass

def transition(current: OrderStatus, target: OrderStatus) -> None:
    if target not in VALID_TRANSITIONS[current]:
        raise InvalidTransition(f"Cannot go from {current.value} to {target.value}")
```
> Pure logic — no DB, no Redis. It only *validates* (raises or stays silent); it does **not** mutate. The caller persists. That separation is deliberate: the service decides legality, the caller decides what to do about it.

### 🧭 Design decision — no `ASSIGNED → PENDING` (kept strict)
A rider who accepts then abandons an order does **not** send it back to PENDING. Re-dispatching forces the customer through a second matching cycle → cold food, broken SLA. Instead: `ASSIGNED → CANCELLED` + a rider penalty (penalty tracked separately on the rider, *not* as an order transition — order-state and rider-penalty are independent state spaces; coupling them is a mistake). The penalty mechanics come later with the event plumbing; today only the *rule* (ASSIGNED→CANCELLED legal, ASSIGNED→PENDING not) matters.

### 💻 The status endpoint — `app/routers/orders.py`
```python
from pydantic import BaseModel
from app.core.enums import OrderStatus
from app.services.order_state import transition, InvalidTransition

class StatusUpdate(BaseModel):
    status: OrderStatus

@router.patch("/{order_id}/status")
def update_status(order_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    current = OrderStatus(order.status)          # str from DB → enum
    try:
        transition(current, body.status)         # validate; raises if illegal
    except InvalidTransition as e:
        raise HTTPException(400, str(e))         # user asked for illegal → 400

    order.status = body.status.value             # enum → str for the DB
    db.commit()
    return {"order_id": order_id, "status": order.status}
```
> **Validate before mutate.** Status never changes unless the transition was legal.
> **`OrderStatus(order.status)`** casts the stored string back to the enum (`transition` compares enum keys).
> **400, not 422:** the input is well-formed (a valid status) but *illegal given current state* — that's a runtime "doesn't make sense against the data" raise, not a malformed-input 422. ("Type it if you can, raise it if you must.")

### 💻 Refactor — route dispatch's flip through the state machine too
`dispatch.py` was setting `winner.status = "ASSIGNED"` raw, bypassing the gate. Route it through `transition()` so **all** status changes go through one place:
```python
from app.core.enums import OrderStatus
from app.services.order_state import transition   # InvalidTransition NOT caught here — see below

    # ... after popping the winner ...
    current = OrderStatus(winner.status)
    # Always legal here (we filtered for PENDING); routing through the state
    # machine keeps ALL status changes going through one gate. If this ever
    # raises, it's an invariant violation — a real bug — so let it crash.
    transition(current, OrderStatus.ASSIGNED)
    winner.status = OrderStatus.ASSIGNED.value
    db.commit()
    return order_id
```
> **Endpoint catches, dispatch doesn't — deliberate.** In the endpoint the target comes from the *user*, so an illegal transition is expected bad input → catch → 400. In dispatch the transition is derived from your own `status == "PENDING"` filter, so a failure means a server-side bug (a non-PENDING order got pulled) → let it raise into a 500. Error-handling follows *who caused the error*, not the function being called. (The `transition()` call is provably always-legal here given the filter — it's an invariant assertion, not user validation. Cheap insurance + single-gate story; the comment marks it as deliberate, not dead code.)

### ⚠️ Auth deferred to Day 35 — endpoint is open right now
The state machine enforces *which transitions are legal*; it does **not** enforce *who may make them*. A customer shouldn't mark their own order DELIVERED even though it's a legal edge. Transitions are really driven by riders (ASSIGNED→PICKED_UP→DELIVERED) and the dispatch system (PENDING→ASSIGNED), not the customer. **Legal-transition and permitted-actor are orthogonal guards** — the second needs authenticated identities, so it lands on **Day 35 (JWT)**: role + ownership checks (assigned rider advances their own orders, ops can cancel, customer can't touch status). Today the endpoint is an unauthenticated dev/admin tool — fine for this stage, tracked as a deliberate follow-up.

### 🔥 Break It On Purpose
Comment out the `if target not in ...` check in `transition()`. PATCH an order straight PENDING → DELIVERED — "delivered" before any rider was assigned, a data-integrity nightmare. Restore the check.

### Test
Create an order (starts PENDING), use its returned id:
```bash
curl -X PATCH :8000/orders/1/status -H "Content-Type: application/json" -d '{"status":"ASSIGNED"}'    # legal  → 200
curl -X PATCH :8000/orders/1/status -H "Content-Type: application/json" -d '{"status":"DELIVERED"}'   # skips PICKED_UP → 400
curl -X PATCH :8000/orders/1/status -H "Content-Type: application/json" -d '{"status":"PENDING"}'     # backward → 400
```
Then dispatch a fresh PENDING order and confirm PENDING→ASSIGNED still flips (now validated through the state machine).

### ✅ End of Day
Illegal transitions return 400; dispatch's flip routes through the same state machine; `OrderStatus` lives in one file; auth gap tracked for Day 35. *(Concept depth — state machine as a graph, the two-failure-semantics distinction, legal-vs-permitted — is in `Interview_prep.md` §19.)*
---

## Day 20 — Redis Pub/Sub (Pre-Kafka Practice)

### 💻 Tasks
Publish on dispatch:
```python
import json, time
redis_client.publish("order.dispatched", json.dumps({
    "order_id": order_id, "rider_id": rider_id, "timestamp": time.time()
}))
```
```bash
mkdir app/workers && touch app/workers/__init__.py
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
        print(f"Notify customer: order {data['order_id']} → rider {data['rider_id']}")
```
Run in a second terminal: `python -m app.workers.notification_worker`. Dispatch an order, watch it log.

🐧 **Ubuntu Note:** New terminal tab = **Ctrl+Shift+T** (keep uvicorn in one, the worker in another).

### ✅ End of Day
Pub/Sub works — and you feel its limitation: **if the worker is off, the message is lost.** That's exactly why Kafka comes next.

---

## Day 21 — Integration Testing

### 💻 Tasks
```bash
pip install pytest pytest-cov httpx
```
`tests/test_orders.py`:
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_order():
    r = client.post("/orders", json={
        "customer_id": 1, "restaurant_id": 1, "value": 500,
        "pickup_lat": 28.6, "pickup_lon": 77.2,
        "drop_lat": 28.7, "drop_lon": 77.3,
    })
    assert r.status_code == 201
    assert r.json()["value"] == 500

def test_invalid_value():
    r = client.post("/orders", json={"value": -10})
    assert r.status_code == 422
```
Run: `pytest -v --cov=app`

### ✅ End of Week 3
Rate limiter, dispatch, geohash + fairness, state machine, Pub/Sub events, tests — all live.

---

# PHASE 4 — Production Quality + Docker (Days 22–28)

## Day 22 — Structured Logging
Replace `print()` with JSON logs. `app/core/logging_config.py`:
```python
import logging, json
from datetime import datetime, UTC

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])
```
> 🐛 **Corrected:** `datetime.now(UTC)` (not deprecated `utcnow()`).
Call `setup_logging()` in `main.py`; replace every `print()` with `logger.info(...)`.
**✅** Logs come out as JSON.

## Day 23 — Custom Exceptions
`app/core/exceptions.py`:
```python
class DeliverIQException(Exception): ...
class OrderNotFound(DeliverIQException): ...
class RiderUnavailable(DeliverIQException): ...
class InvalidStateTransition(DeliverIQException): ...
```
In `main.py`:
```python
from fastapi.responses import JSONResponse
from app.core.exceptions import OrderNotFound

@app.exception_handler(OrderNotFound)
async def order_not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "ORDER_NOT_FOUND", "message": str(exc)})
```
**✅** Clean JSON errors, no tracebacks leaking.

## Day 24 — Environment Config with .env
```bash
pip install pydantic-settings python-dotenv
```
`app/core/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    database_url: str
    redis_url: str = "redis://localhost:6379"
    rate_limit_per_minute: int = 100

settings = Settings()
```
`.env` (gitignored) and `.env.example` (committed, blank values). Use `settings.database_url` everywhere — no hardcoded secrets.
🐧 `echo $DATABASE_URL` to check; `export VAR="..."` to set for the shell.
**✅** Zero hardcoded secrets.

## Day 25 — Dockerize
Install Docker (Ubuntu):
```bash
sudo apt update && sudo apt install ca-certificates curl gnupg lsb-release -y
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update && sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
sudo usermod -aG docker $USER && newgrp docker
docker --version && docker compose version
```
`Dockerfile`:
```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
```bash
docker build -t deliveriq .
docker run -p 8000:8000 --env-file .env deliveriq
```
🐧 `permission denied` on Docker → `newgrp docker` or log out/in; verify with `groups $USER`.
**✅** App runs in a container.

## Day 26 — Docker Compose (Full Stack)
`docker-compose.yml`:
```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://deliveriq_user:password@db:5432/deliveriq_db
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]
  db:
    image: postgres:18
    environment:
      POSTGRES_DB: deliveriq_db
      POSTGRES_USER: deliveriq_user
      POSTGRES_PASSWORD: password
    volumes: ["pg_data:/var/lib/postgresql/data"]
    ports: ["5432:5432"]
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
volumes:
  pg_data:
```
`docker compose up --build` → `localhost:8000/docs`.
🐧 Port clash on 5432/6379 → stop native services: `sudo systemctl stop postgresql redis-server`.
### 🔥 Break It On Purpose
Remove `depends_on: [db, redis]`. The API starts before Postgres is ready → `connection refused`. Restore it (startup ordering).

### 🟥 Earn the "distributed" claim — multi-instance dispatch (the deferred Day-17 work lands here)
Now that the stack runs in Compose, this is where you make "distributed" *true* on your resume:
1. Scale the API to multiple replicas: `docker compose up --build --scale api=3` (and put nginx or Compose's load balancing in front if needed).
2. Move the dispatch queue from the in-process `heapq` into a **Redis sorted set** (`ZADD` on create, `ZREVRANGE` to peek, `ZREM` to claim) — see Day 17's scale-up note.
3. **Demonstrate the race + fix:** with the old heap, two instances can claim the same order. With `ZREM`, only one instance gets the `1` return → atomic claim guard. Capture this — it's a top-tier war story ("two instances double-dispatched; ZREM's atomic return fixed it").
Once this works and you can show it, "distributed" is earned. If you skip it, soften the resume wording instead.

**✅** One command brings up the whole stack; dispatch survives multiple API instances via Redis-sorted-set claims.

## Day 27 — Admin Analytics Endpoint
```python
from sqlalchemy import func
from app.models.order import Order

@router.get("/admin/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Order.id)).scalar()
    by_status = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    avg_value = db.query(func.avg(Order.value)).scalar()
    return {"total_orders": total, "by_status": dict(by_status), "avg_order_value": float(avg_value or 0)}
```
**✅** Aggregation endpoint working.

## Day 28 — Load Testing
```bash
pip install locust
```
`load_test.py`:
```python
from locust import HttpUser, task, between

class DeliverIQUser(HttpUser):
    wait_time = between(0.1, 0.5)
    @task
    def create_order(self):
        self.client.post("/orders", json={
            "customer_id": 1, "restaurant_id": 1, "value": 500,
            "pickup_lat": 28.6, "pickup_lon": 77.2, "drop_lat": 28.7, "drop_lon": 77.3,
        })
```
`locust -f load_test.py --host http://localhost:8000` → `localhost:8089` → 500 users. **Screenshot p99/RPS** for the README.
### ✅ End of Week 4
Dockerized, dotenv'd, logged, tested, with real load numbers (e.g. "p99 = 43ms at 500 RPS").

---

# Before Phase 5 — Redis vs Kafka (read first)

**Redis = fast memory.** Rate-limit buckets, rider-location cache, geohash→rider sets, sessions. RAM-fast, lossy on crash unless persisted.
**Kafka = durable event log.** Order events that must never be lost and may be processed later by multiple independent services. Disk-backed, replayable, scalable.

**Rule:** *Need it NOW, can lose it →* Redis. *Need it RELIABLY, process later →* Kafka.

| Feature | Tool | Why |
|---|---|---|
| Rate-limit counters | Redis | microsecond reads every request |
| Rider locations / geohash sets | Redis | O(1) set ops |
| Dispatch queue (scale-up) | Redis | sorted set, shared across instances |
| order.dispatched event | **Kafka** | many consumers, can't lose it |
| Notifications / analytics / audit | **Kafka** | async, durable, replayable |

You used Pub/Sub first (Day 20) so you'd *feel* why Kafka exists before adopting it.

---

# PHASE 5 — Kafka + Advanced Features (Days 29–35)

## Day 29 — Kafka Theory + First Touch
Watch [Kafka in 100s — Fireship] + [Confluent: Kafka Explained]. Write a 1-page note in your own words: Topic, Partition, Offset, Producer, Consumer, Consumer Group; why Kafka > Pub/Sub (persistence, replay, scaling). Then produce one message via the Kafka UI (after Day 30's compose edit).
**✅** You can explain Kafka in 2 minutes and saw one message in the UI.

## Day 30 — Kafka in docker-compose
Add to `docker-compose.yml`:
```yaml
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment: { ZOOKEEPER_CLIENT_PORT: 2181 }
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
`docker compose up` → `localhost:8080`.
**✅** Kafka running, GUI accessible.

## Day 31 — Kafka Producer
```bash
pip install confluent-kafka
```
`app/core/kafka_producer.py`:
```python
import json
from confluent_kafka import Producer

producer = Producer({"bootstrap.servers": "localhost:9092"})

def publish_event(topic: str, event: dict):
    producer.produce(topic, json.dumps(event).encode("utf-8"))
    producer.flush()
```
Replace Redis `publish` with `publish_event("order.dispatched", {...})`.
**✅** Events appear in Kafka UI.

## Day 32 — Kafka Consumer
`app/workers/notification_consumer.py`:
```python
import json
from confluent_kafka import Consumer

consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "notifications",
    "auto.offset.reset": "earliest",
})
consumer.subscribe(["order.dispatched"])
print("Listening to Kafka...")
while True:
    msg = consumer.poll(1.0)
    if msg is None or msg.error():
        continue
    event = json.loads(msg.value())
    print(f"[Kafka] order {event['order_id']} → rider {event['rider_id']}")
```
`python -m app.workers.notification_consumer`.
**✅** Producer + consumer working.

## Day 33 — Multiple Consumers (Power Move)
Three workers, same topic, different consumer groups: `notifications`, `analytics` (writes DB), `audit-log` (writes file). Each gets its own copy and fails independently.
### 📝 Interview Answer
```
"I replaced Redis Pub/Sub with Kafka because Pub/Sub is fire-and-forget — if the
consumer is down, the message is lost. Kafka persists events to disk and allows
replay from any offset. I run 3 independent consumer groups on order.dispatched —
notifications, analytics, audit — each processing independently; one can fail
without affecting the others. That's event-driven architecture."
```
**✅** 3 workers reading one topic, doing different things.

## Day 34 — Idempotency Keys ⭐ (Razorpay gold)
```python
import json
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.redis_client import redis_client

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
    redis_client.setex(f"idempotency:{key}", 86400, response.body.decode())
    return response
```
### 📝 Interview Answer
```
"Idempotency keys make retries safe. The client sends an Idempotency-Key UUID; the
server caches the response in Redis for 24h. A duplicate key returns the cached
response instead of reprocessing — critical for payment APIs where double-charging
is unacceptable."
```
**✅** Same key returns the same response on retry.

## Day 35 — JWT Authentication
```bash
pip install "python-jose[cryptography]" "passlib[bcrypt]"
```
Add `/auth/register`, `/auth/login`; protect `/admin/stats` with a JWT bearer dependency.
### ✅ End of Week 5
Kafka producer + 3 consumers, idempotency, JWT auth.

---

# PHASE 6 — Deployment + Observability (Days 36–42)

## Day 36 — Prometheus Metrics
```bash
pip install prometheus-fastapi-instrumentator
```
```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```
Visit `/metrics`.
**✅** Metrics endpoint live.

## Day 37 — Grafana Dashboard
Add to `docker-compose.yml`:
```yaml
  prometheus:
    image: prom/prometheus
    ports: ["9090:9090"]
    volumes: ["./prometheus.yml:/etc/prometheus/prometheus.yml"]
  grafana:
    image: grafana/grafana
    ports: ["3000:3000"]
```
`prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'deliveriq'
    static_configs:
      - targets: ['api:8000']
```
Grafana (`admin`/`admin`) → add Prometheus data source → dashboard: request rate, p95/p99 latency, error rate, active orders. **Screenshot for README.**
**✅** Grafana dashboard screenshot — interview gold.

## Day 38 — Health Checks
```python
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.responses import JSONResponse
from app.core.database import get_db
from app.core.redis_client import redis_client

@app.get("/health")
def health(db: Session = Depends(get_db)):
    checks = {}
    try:
        db.execute(text("SELECT 1"))   # CORRECTED: text() required on SQLAlchemy 2.0
        checks["db"] = "up"
    except Exception:
        checks["db"] = "down"
    try:
        redis_client.ping()
        checks["redis"] = "up"
    except Exception:
        checks["redis"] = "down"
    all_up = all(v == "up" for v in checks.values())
    return JSONResponse(
        content={"status": "ok" if all_up else "degraded", **checks},
        status_code=200 if all_up else 503,
    )
```
> 🐛 **Corrected from v3:** bare `db.execute("SELECT 1")` raises on SQLAlchemy 2.0 — raw SQL must be wrapped in `text(...)`.
**✅** Health check covers DB + Redis.

## Day 39 — Deploy to Railway
1. Push to GitHub `main`. 2. railway.app → New Project → Deploy from GitHub (auto-detects Dockerfile). 3. Add Postgres plugin (auto-sets `DATABASE_URL`). 4. Add Redis plugin (auto-sets `REDIS_URL`). 5. Kafka: [Upstash Kafka](https://upstash.com) free tier. 6. Set env vars. 7. Get URL like `deliveriq-production.up.railway.app/docs`.
> 🔐 **Now is when the rate-limiter `X-Forwarded-For` work lands.** Behind Railway's proxy, `request.client.host` is the proxy IP — read the real client IP from `X-Forwarded-For`, but only after confirming the request came from the trusted proxy (else the header is spoofable).
**✅** Live public URL.

## Day 40 — GitHub Actions CI/CD
`.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:18
        env: { POSTGRES_PASSWORD: password }
        ports: ["5432:5432"]
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.14' }
      - run: pip install -r requirements.txt
      - run: pytest --cov=app
```
> 🧠 **Optional stretch (if time):** the sliding-window rate limiter parked on Day 16. ~20 lines with a Redis sorted set. Build only as hardening or if interviewers ask for live coding.
**✅** Green CI badge; tests run on every PR.

## Day 41 — README + Architecture Diagram
Draw architecture in [Excalidraw](https://excalidraw.com) → `architecture.png`. README: description, badges, live URL, diagram, quickstart, design decisions, load-test results, Grafana screenshot.
```bash
git clone https://github.com/you/deliveriq
cp .env.example .env
docker compose up --build      # API at http://localhost:8000/docs
```
**✅** README looks like a product page.

## Day 42 — Demo Video
3-min Loom: Swagger (15s) → create order (30s) → DB row in DBeaver (15s) → Kafka event in UI (30s) → Grafana updating (45s) → trigger rate limiter (30s). Link in README + LinkedIn.
**✅** Demo video live.

---

# PHASE 7 — Polish + Interview Prep (Days 43–45)

## Day 43 — Code Quality Sweep
```bash
pip install black flake8 mypy
black app/ && flake8 app/ && mypy app/
```
Fix warnings, delete dead code, add docstrings to every function, squash messy commits with `git rebase -i`.
**✅** Clean, formatted, type-checked, documented.

## Day 44 — Interview Drills
Consolidate `INTERVIEW_NOTES.md` (Days 16, 17, 18, 33, 34). Answer the bank below out loud, timed. Record the 2-minute pitch. Sketch the architecture from memory in 2 minutes.

### The Question Bank
**System Design**
1. **FastAPI over Flask/Django?** Async by default, Pydantic validation, auto-OpenAPI, near-Go I/O performance.
2. **Your rate limiter — why token-bucket?** Allows bursts up to bucket size, caps average rate, avoids fixed-window's boundary-burst flaw. Redis hash of tokens + last_refill, lazy refill per request, ~O(1).
3. **Redis for the queue, not Postgres?** Sub-ms reads; sorted sets are purpose-built (ZADD/ZREVRANGE) vs an index scan. (Note: you built the in-process heap first; Redis is the scale-up.)
4. **If Redis dies?** Dispatch falls back to Postgres with a latency penalty; rate limiter fails open with logging.
5. **Geohashing?** Encodes lat/lon to a base-32 string; adjacent cells share a prefix; check home cell + 8 neighbours for boundaries.
6. **Kafka over Pub/Sub?** Pub/Sub is fire-and-forget; Kafka persists to disk, replays from offsets, supports consumer groups, scales horizontally.

**DSA**
7. **Min-heap for dispatch?** O(log n) insert/extract vs O(n) scan. Priority = value (+ wait-time aging).
8. **End-to-end dispatch complexity?** Rate check O(1), heap/sorted-set pop O(log n), geohash O(1) → O(log n).
9. **Tie on priority?** Break by created_at (FIFO) — encode as `priority*1e6 + (MAX_TS - created_at)`.
10. **At 10M concurrent orders, first thing to break?** Single-node Redis sorted set → Redis Cluster sharded by zone; Kafka partitioned by region.

**Database**
11. **Schema?** orders(id, customer_id, restaurant_id, value, status, created_at, coords). Indexes on status, created_at. Audit table for transitions.
12. **Postgres over Mongo?** Relational integrity (orders→riders/zones), ACID transactions.
13. **Concurrent dispatch of the same order?** Atomic Redis `ZREM` (returns 1 if claimed, 0 if gone) or `SELECT ... FOR UPDATE`. Prefer ZREM — faster.

**Production**
14. **CI/CD?** GitHub Actions runs pytest + black + flake8 on every PR; merge to main deploys to Railway; health check gates traffic.
15. **DDoS?** Per-key token bucket + Cloudflare L7 + gateway IP limits.
16. **Debug a slow endpoint?** Grafana p99 → structured logs by request_id → cProfile → timing logs around the suspect path.
17. **Idempotency — why/how?** Retries cause duplicate POSTs; client sends Idempotency-Key UUID; cache response in Redis 24h; repeat key returns cached. Critical for payments.

**Behavioural**
18. **Hardest part?** Geohash boundary conditions — an edge order needs the 8 neighbours; initially I only checked the home cell and missed riders 100 m away.
19. **More time?** Circuit breaker, OpenTelemetry tracing, saga for payments, chaos testing.
20. **What did you learn?** Event-driven architecture deeply (offsets, consumer groups, partitioning) and production hygiene (logs, metrics, health checks).

**Differentiation**
21. **Different from real Swiggy/Zomato?** Theirs optimizes pure ETA; mine adds a bounded fairness constraint — within a distance band of the nearest, assign to whoever has the fewest orders today. Greedy-nearest reframed as constrained assignment.
22. **What real problem does the band solve?** Naive nearest starves some riders and overloads others — a real gig-economy issue. The band spreads earnings while Δ guarantees SLA. Honest social-impact angle.
23. **Band vs a blended score (α·dist+β·fairness)?** A blend can silently send a far rider (cold food). The band makes the SLA guarantee explicit and tunable — fairness only operates inside Δ.

**✅** All answers cold; 2-minute pitch from memory.

## Day 45 — Final Buffer
Fix last bugs. `git tag v1.0.0 && git push --tags`. Pin the repo. Update LinkedIn + resume. **Rest. You did it.**

---

# Git Workflow

**Daily loop**
```bash
git checkout dev && git pull
git checkout -b feature/kafka-consumer
# code + tests
git add -p
git commit -m "feat: add Kafka consumer for order.dispatched"
git push origin feature/kafka-consumer
# PR → review → merge to dev; Sundays: dev → main
```
**Commit prefixes:** `feat` `fix` `docs` `test` `refactor` `chore` `perf`.
**Branches:** `main` (deployable, protected) · `dev` (integration) · `feature/*` · `fix/*`.
**Pro tip:** 50+ commits over 45 days — recruiters check the contribution graph.

---

# Resume Bullets (under "Projects")
```
DeliverIQ — Order Dispatch API   [GitHub] [Live Demo]
Python · FastAPI · PostgreSQL · Redis · Kafka · Docker
• Designed a food-delivery dispatch system with a min-heap priority queue
  (O(log n)) and geohash-based rider matching (O(1) zone lookup), handling
  500 concurrent requests at p99 < 50ms.
• Built fairness-aware rider assignment balancing rider earnings within a
  bounded distance band — reframing greedy-nearest as a constrained
  assignment problem without breaching delivery SLA.
• Built a token-bucket rate limiter in Redis with <1ms overhead per request;
  cut abusive traffic by 99% in load tests.
• Implemented event-driven architecture with Kafka topics for order-lifecycle
  events, enabling async notifications and decoupled analytics.
• Added idempotency keys for safe retries; deployed the full stack
  (API + PostgreSQL + Redis + Kafka) via Docker Compose and GitHub Actions
  CI/CD to Railway.
```
**Rules:** quantify (ms, RPS, %, Big-O) · use real vocabulary (dispatch, idempotency, event-driven, geohash) · link GitHub + live URL · "built/designed/implemented", never "learned/explored".

---

# The 2-Minute Pitch (memorize)
> "I built DeliverIQ — a backend that solves the order-dispatch problem companies like Zomato and Uber Eats face. The core challenge: given hundreds of incoming orders and available riders, assign them optimally in real time. I use a min-heap priority queue scoring each order by value and wait time, and geohashing to find nearby riders in O(1) instead of computing distance to every rider. What's mine: dispatch is fairness-aware — among riders within a distance band of the nearest, I assign to whoever has the fewest orders today, so earnings stay balanced without delivering cold food. The API has a token-bucket rate limiter in Redis with sub-millisecond overhead and an event-driven Kafka pipeline — when an order dispatches, notifications, analytics, and audit consume the event independently. The whole stack runs in Docker Compose with Prometheus + Grafana, deployed on Railway with GitHub Actions CI/CD. What I'm proudest of: every design decision has a clear reason — I can tell you exactly why token-bucket over leaky-bucket, and Kafka over Redis Pub/Sub."

**Do:** draw the architecture first · lead with the problem · quote numbers · volunteer tradeoffs · have one war story (the geohash boundary bug).
**Don't:** say "I followed a tutorial" · apologize for missing features · list tech alphabetically · monologue past 2 min without pausing.

---

# Final Checklist
**Code:** no hardcoded secrets · docstrings everywhere · no dead code · black/flake8/mypy clean · pinned `requirements.txt` · coverage ≥60%.
**GitHub:** README (desc, badges, live URL, diagram, quickstart, design decisions) · 50+ commits · CI badge · `.env.example` present, `.env` ignored · tag `v1.0.0` · Loom linked · repo pinned.
**Deploy:** `/docs` works · `/health` returns DB+Redis+Kafka · auto-restart · HTTPS · Grafana screenshot.
**Interview:** explain every file · Big-O of every algorithm · "what breaks at 10x" · "what's next" · sketch architecture in 2 min · pitch memorized · 5 war stories ready.

---

# Common Pitfalls
1. **Tutorial hell** — read docs, build immediately. 2. **Refactoring too early** — make it work first (refactor Day 43). 3. **Skipping tests** — silent breakage. 4. **Hardcoding secrets** — `.env` from Day 24. 5. **Big commits** — one logical change each. 6. **Ignoring errors** — read the exact last line (Stuck Protocol). 7. **Not asking for help** — stuck >45 min, ask. 8. **Comparing to others** — your only competition is yesterday-you.

---

# Closing
You're a Codeforces Expert and LeetCode Knight — the algorithmic muscle is already there. This project wraps that muscle in the production skin interviewers want: APIs, databases, caching, queues, events, deployment. Discipline > motivation. Build > watch. Depth > breadth.

On Day 45 you'll have something rare: a project you can defend in any interview because every line came from your fingers — and now every line is correct.

🚀 *See you on Day 45.*
