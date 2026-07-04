# DeliverIQ — 45-Day Master Plan (v3.2 — Ubuntu Edition, Corrected)
### Zero Backend Experience → Production-Grade Backend API

**For:** Shorya Gupta — final-year CSE (Thapar, grad 2027) · Codeforces **Expert** · CodeChef 3★ · LeetCode Knight · 1500+ problems. Strong C++/DSA, learning backend.
**System:** Ubuntu Linux (every command here is Ubuntu-specific).
**Stack:** Python 3.14 · FastAPI · SQLAlchemy 2.0 · Pydantic · Alembic · PostgreSQL 18 · Redis · Kafka · Docker.
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
### 📈 The distributed scale-up — ⚠️ scheduled for Day 29, NOT optional

At scale the queue shouldn't live inside one API process. With 2+ API replicas,
two instances could pop and claim the **same** PENDING order — a race.

**Primary path (v4): Postgres `SELECT … FOR UPDATE SKIP LOCKED`.**
When claiming the winner, re-fetch the row `.with_for_update(skip_locked=True)`,
re-check it's still PENDING, then flip to ASSIGNED. The row lock serializes the
claim (only one instance wins); `SKIP LOCKED` means the other instance doesn't
block — it moves to the next order. This **preserves the wait-time aging formula,
the fairness band, and the work-conserving rider loop** exactly as built.

> 🔑 **Why SKIP LOCKED over the Redis sorted set:** a sorted set's score is fixed
> at insert, so it **can't express wait-time aging** (the score would have to
> change every second). It also hides the heap inside Redis. SKIP LOCKED keeps
> the heap logic in the app and adds only the concurrent-claim guard. The sorted
> set (ZADD/ZREVRANGE/ZREM, ZREM as the atomic claim) is now just the "optional
> alt — know the tradeoff" mention.

> 🔑 **Why "later," not "now":** today you run a single uvicorn process — no
> second instance to race with, so there's nothing to demonstrate yet. heapq
> first, by design (it showcases your DSA).

> 🟥 **Resume dependency — do not skip.** Your resume says "distributed." That
> word is only earned once this is built (Day 29) and you've shown the
> multi-instance race + SKIP LOCKED fix, run via `docker compose --scale api=3`.
> If you finish without it, soften the wording ("designed for horizontal
> scaling" / "stateless API with externalized state") rather than leave an
> indefensible claim.

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
> Full concept→soundbite→gotcha writeup is in Interview_notes §14–15. One-line summary: geohash for a coarse O(1)-ish candidate set (home cell + 8 neighbours), haversine to rank it, then a fairness band — among riders within Δ of the nearest, assign the least-loaded. Reframes greedy-nearest as a bounded constrained-assignment problem; the hard band makes the SLA guarantee explicit and tunable (a blended score could silently send a far rider).

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

## Day 20 — Rider Lifecycle + Redis Pub/Sub (Pre-Kafka)

### 🎯 Goal
Wire dispatch → rider assignment with a full BUSY↔AVAILABLE lifecycle, then
publish an `order.dispatched` event and consume it — to *feel* Pub/Sub's
fire-and-forget flaw before adopting Kafka.

### Step 1 — rider goes BUSY on assignment (dual-store)
`geohash_service.py` — new helper:
```python
def remove_rider_from_index(rider_id: int):
    cell = redis_client.hget(f"rider:{rider_id}:loc", "cell")
    if cell:
        redis_client.srem(f"geohash:{cell}", rider_id)
```
`dispatch.py` — after assigning, before commit:
```python
rider = db.query(Rider).filter(Rider.id == rider_id).first()
rider.status = "BUSY"               # Postgres truth
remove_rider_from_index(rider_id)   # Redis mirror: out of geohash cells
db.commit()
```
> Availability is enforced in Redis: a BUSY rider isn't in any cell, so
> `select_rider` can't see them. `select_rider` itself needs zero changes.

### Step 2 — rider freed on DELIVERED / CANCELLED
`orders.py` `update_status`, after applying the new status:
```python
reindex = None
if body.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED) and order.rider_id:
    rider = db.query(Rider).filter(Rider.id == order.rider_id).first()
    if rider:
        rider.status = "AVAILABLE"
        if body.status == OrderStatus.DELIVERED:
            rider.current_lat = order.drop_lat   # rider is at the drop now
            rider.current_lon = order.drop_lon
        reindex = (rider.id, rider.current_lat, rider.current_lon)  # capture pre-commit
db.commit()
if reindex:
    update_rider_location(*reindex)   # rider re-enters a geohash cell → selectable
```
> Capture `reindex` BEFORE commit — commit expires attributes, so reading
> `rider.current_lat` after would fire a surprise reload.
> DELIVERED relocates to the drop; CANCELLED keeps current location.

### Step 3 — publish the event (after commit)
`dispatch.py`, after `db.commit()`:
```python
import json, time
redis_client.publish(
    "order.dispatched",
    json.dumps({"order_id": order_id, "rider_id": rider_id, "ts": time.time()}),
)
```
> Publish AFTER commit — only announce a fact that's already durable, or a
> listener could react to an assignment that then rolls back.

### Step 4 — the subscriber
`app/workers/notification_worker.py`:
```python
import json
from app.core.redis_client import redis_client

pubsub = redis_client.pubsub()
pubsub.subscribe("order.dispatched")
print("Notification worker listening on 'order.dispatched'...")
for msg in pubsub.listen():
    if msg["type"] != "message":   # skip the subscribe-confirmation frame
        continue
    data = json.loads(msg["data"])
    print(f"[notify] order {data['order_id']} → rider {data['rider_id']}")
```
Run in a 2nd terminal: `python -m app.workers.notification_worker`

### 🔥 Break It On Purpose — feel fire-and-forget
1. Worker running → dispatch → worker prints the event.
2. Stop the worker → dispatch again (200 OK) → restart worker → it prints
   **nothing** about the missed event. The event is gone forever.
> Pub/Sub delivers only to listeners alive at publish time. No queue, no
> replay, no record. That permanent loss is exactly why Kafka comes next.

### ✅ End of Day
Full rider lifecycle (AVAILABLE→BUSY→AVAILABLE with re-indexing), event
published on dispatch, consumed by a worker — and you've felt why Pub/Sub
loses events when the consumer is down.
---
### 📊 Current end-to-end flow (as of Day 20)

```mermaid
%% Dispatch (priority heap + fairness match + BUSY) and order completion
%% (free rider + re-index), plus the fire-and-forget Pub/Sub edge.

flowchart TD
    subgraph DISPATCH["POST /orders/dispatch"]
        A[Query PENDING orders from Postgres] --> B{Any pending?}
        B -- no --> B404[404: no pending orders]
        B -- yes --> C["Build max-heap<br/>priority = value + wait_minutes x AGING_WEIGHT"]
        C --> D[Pop highest-priority order]
        D --> E["select_rider<br/>home cell + 8 neighbours<br/>haversine rank<br/>fairness band &#916;<br/>fewest orders_today, then nearest"]
        E --> F{"Rider found?<br/>(only AVAILABLE riders<br/>are present in cells)"}
        F -- no --> G{Heap empty?}
        G -- "no (try next order)" --> D
        G -- yes --> H404[404: orders exist but no rider available]
        F -- yes --> I["transition PENDING to ASSIGNED<br/>order.rider_id = rider<br/>orders_today++ (inside select_rider)"]
        I --> J["rider.status = BUSY (Postgres truth)<br/>srem rider from geohash cell (Redis enforce)"]
        J --> K[(db.commit)]
        K --> L[["publish order.dispatched<br/>{order_id, rider_id, ts}"]]
        L --> M[return order_id + rider_id]
    end

    L -. fire-and-forget .-> N{Worker alive<br/>at publish time?}
    N -- yes --> O["notification_worker prints<br/>[notify] order to rider"]
    N -- no --> P["event lost forever<br/>no queue, no replay<br/>(this is why Kafka comes next)"]

    M -. rider is now BUSY,<br/>out of the pool .-> Q

    subgraph FINISH["PATCH /orders/{id}/status"]
        Q[validate transition] --> R{"DELIVERED or CANCELLED<br/>and order.rider_id set?"}
        R -- no --> S[(commit status only)]
        R -- yes --> T[rider.status = AVAILABLE]
        T --> U{DELIVERED?}
        U -- yes --> V[move rider to drop coords]
        U -- no --> W[keep current coords]
        V --> X[(db.commit)]
        W --> X
        X --> Y["update_rider_location<br/>srem old + sadd new cell<br/>rider selectable again"]
    end
```
## Day 21 — Integration Testing (with proper isolation)

### 🎯 Goal
Test the whole dispatch engine end-to-end through HTTP — create, validate,
dispatch, BUSY enforcement, delivery-frees-rider, illegal transitions — against
an **isolated** test database and Redis, reset before every test.

> ⚠️ **Deviation from v3.2:** the original Day 21 hit the real dev DB. That
> pollutes dev data and makes tests non-repeatable (IDs drift, re-runs see stale
> rows). Built proper isolation instead: a throwaway test DB + Redis logical DB
> 15 + an autouse reset fixture. "How do you isolate tests?" is a real interview
> question — this is the answer.

### Step 1 — test database + deps
```bash
# one-time: create a throwaway DB owned by the same user
sudo -u postgres psql -c "CREATE DATABASE deliveriq_test_db OWNER deliveriq_user;"

pip install pytest pytest-cov httpx && pip freeze > requirements.txt
```

### Step 2 — make Redis DB selectable (env-var seam)
`app/core/redis_client.py`:
```python
import os
import redis

REDIS_DB = int(os.getenv("REDIS_DB", "0"))   # tests set 15; default 0 unchanged
redis_client = redis.Redis(host="localhost", port=6379, db=REDIS_DB, decode_responses=True)
```
> Redis has 16 logical DBs (0–15). Tests use 15 so they never touch dev data on
> 0. `redis_client` is a module global (no `Depends` to override), so the clean
> seam is an env var read at import time — set it BEFORE the app imports.

### Step 3 — the test harness, `tests/conftest.py`
```python
import os
os.environ["REDIS_DB"] = "15"   # MUST be set before app imports redis_client

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.redis_client import redis_client
from app.main import app
from app.models.order import Order  # noqa: F401 — register tables on Base
from app.models.rider import Rider  # noqa: F401

TEST_DATABASE_URL = "postgresql://deliveriq_user:password@localhost:5432/deliveriq_test_db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_state():
    """Fresh tables + fresh Redis before EVERY test → full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    redis_client.flushdb()
    yield


@pytest.fixture
def client():
    """TestClient whose get_db points at the test database."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```
```bash
touch tests/__init__.py
python -m pytest -q          # expect: 0 items, no errors (harness loads)
```

### Step 4 — the tests, `tests/test_orders.py`
```python
def _make_rider(client, lat=28.6139, lon=77.2090):
    r = client.post("/riders", json={"name": "Suresh", "current_lat": lat, "current_lon": lon})
    assert r.status_code == 201
    return r.json()["id"]


def _make_order(client, lat=28.6139, lon=77.2090):
    r = client.post("/orders", json={
        "customer_id": 1, "restaurant_id": 1, "value": 500,
        "pickup_lat": lat, "pickup_lon": lon,
        "drop_lat": 19.0760, "drop_lon": 72.8777,   # Mumbai drop
    })
    assert r.status_code == 201
    return r.json()["id"]


def test_create_order(client):
    r = client.post("/orders", json={
        "customer_id": 1, "restaurant_id": 1, "value": 500,
        "pickup_lat": 28.6139, "pickup_lon": 77.2090,
        "drop_lat": 28.7041, "drop_lon": 77.1025,
    })
    assert r.status_code == 201
    body = r.json()
    assert body["value"] == 500
    assert body["status"] == "PENDING"
    assert body["id"] == 1               # proves per-test reset (no stale rows)


def test_invalid_value_rejected(client):
    r = client.post("/orders", json={
        "customer_id": 1, "restaurant_id": 1, "value": -10,   # Field(gt=0) → 422
        "pickup_lat": 28.6, "pickup_lon": 77.2, "drop_lat": 28.7, "drop_lon": 77.3,
    })
    assert r.status_code == 422


def test_get_missing_order_404(client):
    assert client.get("/orders/999").status_code == 404


def test_dispatch_assigns_rider(client):
    rider_id = _make_rider(client)
    order_id = _make_order(client)
    r = client.post("/orders/dispatch")
    assert r.status_code == 200
    assert r.json()["dispatched"] == {"order_id": order_id, "rider_id": rider_id}
    assert client.get(f"/orders/{order_id}").json()["status"] == "ASSIGNED"


def test_busy_rider_not_dispatched_again(client):
    _make_rider(client)
    _make_order(client)
    _make_order(client)                      # 2 orders, 1 rider
    assert client.post("/orders/dispatch").status_code == 200   # rider → BUSY
    assert client.post("/orders/dispatch").status_code == 404   # none AVAILABLE


def test_delivery_frees_rider(client):
    rider_id = _make_rider(client)
    order_id = _make_order(client)
    client.post("/orders/dispatch")          # rider BUSY
    client.patch(f"/orders/{order_id}/status", json={"status": "PICKED_UP"})
    client.patch(f"/orders/{order_id}/status", json={"status": "DELIVERED"})
    # freed + relocated to the drop → a Mumbai-pickup order matches them
    new_order = client.post("/orders", json={
        "customer_id": 2, "restaurant_id": 1, "value": 300,
        "pickup_lat": 19.0760, "pickup_lon": 72.8777,
        "drop_lat": 28.6, "drop_lon": 77.2,
    }).json()["id"]
    r = client.post("/orders/dispatch")
    assert r.status_code == 200
    assert r.json()["dispatched"] == {"order_id": new_order, "rider_id": rider_id}


def test_illegal_transition_rejected(client):
    order_id = _make_order(client)
    r = client.patch(f"/orders/{order_id}/status", json={"status": "DELIVERED"})
    assert r.status_code == 400   # PENDING→DELIVERED skips steps → illegal
```
```bash
pytest -v                                    # 7 passed
pytest --cov=app --cov-report=term-missing   # 86% — read the "Missing" column
```

### 🐛 Gotchas hit
- **`/usr/bin/pytest` shadowing the venv** — `which pytest` showed the system
  one (no fastapi). Fixed by removing `python3-pytest` (apt dry-run confirmed no
  collateral) and `hash -r`. `python -m pytest` is the shadow-proof invocation.
- **`collected 0 items`** — tests must live in `tests/test_*.py` with the
  `test_` prefix, or pytest skips them.

### `.gitignore` additions
```
.coverage
.pytest_cache/
htmlcov/
```

### ✅ End of Day
7 integration tests covering the full dispatch lifecycle, isolated test DB +
Redis, 86% coverage. Tests are repeatable and order-independent.
# DeliverIQ — Plan Ahead (v4, Days 22→45 reorganized)

> Replaces Days 22–45 of v3.2. Days 1–21 are done and unchanged.
> Reordered by **dependency**, with the logical gaps in v3.2 fixed.
> Same per-day rhythm (goal → key code/decision → gotcha → ✅), but lighter on
> tutorial prose — you build each day with full code in-session.

---

## What changed from v3.2 (and why the reorder)

| # | Problem in v3.2 | Fix in v4 |
|---|---|---|
| 1 | Migrations never run in Docker/Railway (`create_all` gone since Day 14) → no tables | Migration entrypoint (`alembic upgrade head`) added to Dockerize day; Railway release command |
| 2 | `Settings` created but never consumed; test seams hardcoded → CI breaks | **Config day moved up (Day 23)**; `database.py`/`redis_client.py`/Kafka refactored to read it; test URLs env-driven |
| 3 | Rate limiter throttles Locust (1 IP → 100 tokens → 429) | Env toggle `RATE_LIMIT_ENABLED` + per-key option, added in the limiter-hardening day before load test |
| 4 | Idempotency middleware `response.body` bug | Rewritten to consume `body_iterator` and rebuild the response |
| 5 | Kafka `localhost:9092` breaks in Compose/Upstash | Bootstrap from config (`kafka:9092` in Compose, SASL_SSL on Upstash) |
| 6 | "Distributed" via Redis sorted set discards aging + work-conserving loop | **Primary path = Postgres `SELECT … FOR UPDATE SKIP LOCKED`** (preserves aging + fairness + rider loop); sorted-set is an optional alt |
| 7 | JWT day drops Day-19 ownership/role checks; no User model/migration | Auth day expanded: User model + migration + the deferred status-endpoint authz |
| 8 | Rate-limiter read-write race real at multi-instance, never fixed | Atomic Lua/pipeline in the hardening day, before scaling |
| 9 | Health check omits Kafka | Added to the health day |
| 10 | Custom exceptions unused; name clash with `InvalidTransition` | Integrated into real raises; renamed to avoid clash |
| 11 | `request_id` cited in interviews, never built | Added to the logging day (correlation middleware) |
| 12 | Rider penalty (Day-19 deferred) unscheduled, no field | Scheduled a small slot in the auth/events area; or explicitly drop + soften |

Minor cleanups folded in: routers are **plural** in real code (`orders.py`, `riders.py`) — reconcile the structure doc; `last_assigned_at` is a dead write (remove in the quality sweep); `INTERVIEW_NOTES.md` → use the real `Interview_prep.md`.

---

# PHASE 4 — Production Hardening (local) · Days 22–26

## Day 22 — Structured Logging + request_id correlation ✅

**Goal:** JSON logs, and a `request_id` on every log line so you can trace one
request end-to-end.

**Why:** JSON logs are queryable in an aggregator (Loki/ELK); `print()` is a dead
string. request_id ties every line of one request together so interleaved
requests are untangleable.

### 1. `app/core/request_context.py` — the contextvar + log filter
```python
import contextvars
import logging

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True
```

### 2. `app/core/logging_config.py` — JSON formatter + setup
```python
import json
import logging
from datetime import UTC, datetime

from app.core.request_context import RequestIdFilter


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        return json.dumps(log)


def setup_logging():
    handler = logging.StreamHandler()          # logs → stdout
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()                       # drop uvicorn's default text handler
    root.addHandler(handler)
    root.setLevel(logging.INFO)
```

### 3. `app/middleware/request_id.py` — UUID per request
```python
import uuid
from fastapi import Request
from app.core.request_context import request_id_var


async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)              # store for this request's context
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### 4. `app/main.py` — wire it (request_id registered LAST = outermost)
```python
from app.core.logging_config import setup_logging
from app.middleware.rate_limiter import rate_limit_middleware
from app.middleware.request_id import request_id_middleware

setup_logging()
app = FastAPI(title="DeliverIQ")
# ... include_routers ...
app.middleware("http")(rate_limit_middleware)   # inner
app.middleware("http")(request_id_middleware)    # outer (registered last)
```

### 5. `app/workers/notification_worker.py` — print() → logger
```python
import logging
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("deliveriq.worker")
# ...
logger.info(f"[notify] order {data['order_id']} → rider {data['rider_id']}")
```
> The worker doesn't run through main.py, so it calls setup_logging() itself.

**Gotcha:** FastAPI runs middleware last-registered-first, so request_id
registered last runs outermost → every downstream log (incl. rate limiter)
carries the id. contextvars (not a global) keeps ids from bleeding across
concurrent async requests.
## Day 22 — Testing
```bash
# 1. start server, confirm clean boot
uvicorn app.main:app --reload      # wait for "Application startup complete"

# 2. header + JSON log with non-null request_id
curl -i http://localhost:8000/health
# → response headers contain: x-request-id: <uuid>
# → uvicorn terminal shows:
#   {"timestamp":"...","level":"INFO","logger":"deliveriq",
#    "message":"health check hit","request_id":"<same-uuid-family>"}

# 3. null case (log outside a request) — save any file, watchfiles logs:
#   {"...","logger":"watchfiles.main","request_id":null}   ← correct, not a bug

# 4. regression
python -m pytest -q                # all green
```

**✅** Every log line is JSON with a request_id; one request is greppable across
the app and the worker.
---
## Day 23 — Centralized Config (.env + Settings) ✅

**Goal:** one config object; zero hardcoded URLs; env-driven test seams so
Docker and CI work later.

```bash
pip install pydantic-settings python-dotenv && pip freeze > requirements.txt
```

### 1. `app/core/config.py`
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_enabled: bool = True
    rate_limit_capacity: int = 100
    rate_limit_refill_per_min: int = 100


settings = Settings()
```

### 2. Consume it

`app/core/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`app/core/redis_client.py`:
```python
import redis
from app.core.config import settings

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
```

`app/middleware/rate_limiter.py` (top):
```python
from app.core.config import settings

BUCKET_SIZE = settings.rate_limit_capacity
REFILL_RATE = settings.rate_limit_refill_per_min / 60

# inside middleware, first line:
    if not settings.rate_limit_enabled:
        return await call_next(request)
```

### 3. `.env` (gitignored) + `.env.example` (committed)
```
# .env
DATABASE_URL=postgresql://deliveriq_user:password@localhost:5432/deliveriq_db
REDIS_URL=redis://localhost:6379/0

# .env.example
DATABASE_URL=
REDIS_URL=redis://localhost:6379/0
```

### 4. conftest — env before import (replaces Day-21 REDIS_DB)
```python
import os
os.environ["DATABASE_URL"] = "postgresql://deliveriq_user:password@localhost:5432/deliveriq_test_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
# ... then imports; engine = create_engine(os.environ["DATABASE_URL"])
```

**Gotcha:** `settings = Settings()` runs at import, so conftest must set env
*before* importing the app. Same import-time seam as Day 21, now for both stores.

## Day 23 — Testing
```bash
# 1. no hardcoded URLs outside config.py
grep -rn "postgresql://" app/      # only app/core/config.py (default) may match
grep -rn "localhost:6379" app/     # same

# 2. .env exists and is gitignored
ls -la .env .env.example
git check-ignore .env              # prints ".env" → ignored

# 3. app still boots reading .env
uvicorn app.main:app --reload      # no "field required" pydantic error

# 4. tests hit the TEST stores (env set in conftest before import)
python -m pytest -q                # 7 passed at this point
```
**✅** No hardcoded URLs outside config; tests green; env-driven for Docker/CI.
---
## Day 24 — Custom Exceptions (integrated) ✅

**Goal:** one JSON error envelope, wired into real raises — not dead classes.

### 1. `app/core/exceptions.py`
```python
class DeliverIQError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

class OrderNotFound(DeliverIQError):     status_code = 404; code = "ORDER_NOT_FOUND"
class RiderNotFound(DeliverIQError):     status_code = 404; code = "RIDER_NOT_FOUND"
class NoPendingOrders(DeliverIQError):   status_code = 404; code = "NO_PENDING_ORDERS"
class RiderUnavailable(DeliverIQError):  status_code = 409; code = "RIDER_UNAVAILABLE"
class InvalidTransition(DeliverIQError): status_code = 400; code = "INVALID_TRANSITION"
```

### 2. `main.py` — one base handler
```python
@app.exception_handler(DeliverIQError)
async def deliveriq_error_handler(request: Request, exc: DeliverIQError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message},
    )
```

### 3. `order_state.py` — import InvalidTransition (remove local class)
```python
from app.core.exceptions import InvalidTransition
```

### 4. `dispatch.py` — raise specific errors instead of returning None
```python
if not pending:
    raise NoPendingOrders("No pending orders to dispatch")
# ... after the while-loop finds no rider:
raise RiderUnavailable("Orders are pending but no rider is available nearby")
```

### 5. Routers — typed raises, no try/except
- `orders.py`: `OrderNotFound`; `transition()` raises `InvalidTransition` → base handler → 400 (no try/except).
- `riders.py`: `RiderNotFound`, `RiderUnavailable` (match).

**Gotcha:** InvalidTransition is now a DeliverIQError → the 400 comes from the
base handler, not a manual HTTPException. no-rider is 409 (conflict), not 404.
Optional envelope test:
```python
def test_error_envelope(client):
    r = client.get("/orders/999")
    assert r.json() == {"error": "ORDER_NOT_FOUND", "message": "Order 999 not found"}
```

## Day 24 — Testing
```bash
# 1. envelope shape on a missing order
curl -s http://localhost:8000/orders/999 | python -m json.tool
# → {"error": "ORDER_NOT_FOUND", "message": "Order 999 not found"}

# 2. illegal transition → 400 through the SAME envelope
curl -s -X PATCH http://localhost:8000/orders/1/status \
  -H "Content-Type: application/json" -d '{"status":"DELIVERED"}'
# → 400 {"error":"INVALID_TRANSITION", ...}

# 3. dispatch failure reasons are now distinct
curl -s -X POST http://localhost:8000/orders/dispatch
# empty DB        → 404 {"error":"NO_PENDING_ORDERS", ...}
# orders, no rider → 409 {"error":"RIDER_UNAVAILABLE", ...}

# 4. regression (updated: busy-rider test asserts 409 now)
python -m pytest -q                # 8 passed (envelope test added)
```

**✅** Missing order → `{"error":"ORDER_NOT_FOUND",...}`; every router uses typed
exceptions; dispatch failures are specific (404 vs 409). 8 tests pass.
---
## Day 25 — Rate-Limiter Hardening (atomic Lua) ✅

**Goal:** kill the read-write race — collapse refill+check+decrement into one
atomic Lua script. (Toggle + config already done Day 23.)

**Why:** 3 separate Redis ops (HGETALL→compute→HSET) let two concurrent requests
read the same count and both pass. Redis runs a Lua script atomically → one
indivisible operation.

### `app/middleware/rate_limiter.py`
```python
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.redis_client import redis_client

BUCKET_SIZE = settings.rate_limit_capacity
REFILL_RATE = settings.rate_limit_refill_per_min / 60
TTL = 120

RATE_LIMIT_LUA = """
local data = redis.call('HMGET', KEYS[1], 'tokens', 'last_refill')
local tokens = tonumber(data[1])
local last = tonumber(data[2])
local cap = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])
if tokens == nil then
  tokens = cap
  last = now
else
  tokens = math.min(cap, tokens + (now - last) * rate)
end
if tokens < 1 then
  return -1
end
tokens = tokens - 1
redis.call('HSET', KEYS[1], 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', KEYS[1], ttl)
return tostring(tokens)
"""

_rate_limit = redis_client.register_script(RATE_LIMIT_LUA)


async def rate_limit_middleware(request: Request, call_next):
    if not settings.rate_limit_enabled:
        return await call_next(request)

    client_key = request.headers.get("X-API-Key") or request.client.host  # type: ignore
    bucket_key = f"rate_limit:{client_key}"
    now = time.time()

    result = _rate_limit(keys=[bucket_key], args=[BUCKET_SIZE, REFILL_RATE, now, TTL])

    if result == "-1" or result == -1:
        return JSONResponse(
            status_code=429, content={"error": "Rate limit exceeded. Try again later."}
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(int(float(result)))
    return response
```

**Gotcha:** script returns `tostring(tokens)` (Lua/Redis truncates bare numbers)
→ parse with `float(result)`. `register_script` uses EVALSHA (sends hash, not
body).

## Day 25 — Testing
```bash
# 1. burst → throttle (proves Lua path works end-to-end)
URL=http://localhost:8000/health
for i in $(seq 1 105); do curl -s -o /dev/null -w "%{http_code} " "$URL"; done; echo
# → ~100 × 200, then 429s

# 2. header still present on allowed requests
curl -i http://localhost:8000/health | grep -i x-ratelimit
# → x-ratelimit-remaining: <n>

# 3. verify ONE round-trip (optional): watch Redis commands live
redis-cli monitor            # in a 2nd terminal; curl once →
# a single EVALSHA line (not HGETALL+HSET+EXPIRE separately). Ctrl+C to exit.

# 4. regression
python -m pytest -q                # 8 passed (9 after boundary-coord test)
```
**✅** One atomic round-trip per request; concurrent requests can't desync the
bucket; multi-instance-safe for Day 29.
---
## Day 26 — Admin Analytics Endpoint ✅

**Goal:** `GET /admin/stats` aggregation on its own router (JWT locks it Day 35).

### `app/routers/admin.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.order import Order
from app.models.rider import Rider

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_orders = db.query(func.count(Order.id)).scalar()
    avg_value = db.query(func.avg(Order.value)).scalar()
    status_rows = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    rider_rows = db.query(Rider.status, func.count(Rider.id)).group_by(Rider.status).all()
    return {
        "total_orders": total_orders,
        "avg_order_value": round(avg_value, 2) if avg_value else 0,
        "orders_by_status": {s: c for s, c in status_rows},
        "riders_by_status": {s: c for s, c in rider_rows},
    }
```

Register: `app.include_router(admin.router)`

**Gotcha:** `func.avg` → None on empty table (guard it); `group_by` omits
zero-count statuses.
## Day 26 — Testing
```bash
# 1. empty-ish DB
curl -s http://localhost:8000/admin/stats | python -m json.tool
# → {"total_orders": 0, "avg_order_value": 0, "orders_by_status": {}, ...}

# 2. seed + re-check counts move
curl -s -X POST http://localhost:8000/orders -H "Content-Type: application/json" \
  -d '{"customer_id":1,"restaurant_id":1,"value":500,"pickup_lat":28.61,"pickup_lon":77.20,"drop_lat":28.7,"drop_lon":77.1}'
curl -s http://localhost:8000/admin/stats | python -m json.tool
# → total_orders +1, orders_by_status shows PENDING

# 3. regression
python -m pytest -q
```
**✅** `/admin/stats` returns live counts (open now; locked Day 35).
---

# PHASE 5 — Containerization (done right) · Days 27–28

## Day 27 — Dockerize (with migrations) + Load Test
**Goal:** the app runs in a container **with its schema applied**, then measure real throughput.

`Dockerfile`:
```dockerfile
FROM python:3.14-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```
> **The migration fix:** `alembic upgrade head` runs **before** uvicorn, so the container always has the current schema. Without this the container has no tables.

**Load test** (after the container runs, or against local):
```bash
pip install locust
```
- Locust task posts orders; **set a unique `X-API-Key` per user** (or run with `RATE_LIMIT_ENABLED=false`) so the limiter doesn't turn the test into a wall of 429s.
- Screenshot p99/RPS for the README.

**Gotcha:** `libpq-dev`/`gcc` in the image because `psycopg2-binary` *usually* ships a wheel but the source build needs them; safe to include. The rate-limit toggle is why your numbers are now honest.

**✅** Container boots, migrates, serves; load test shows real p99/RPS (not 429s).

---

## Day 28 — Docker Compose (full local stack, multi-instance ready)
**Goal:** one command brings up API + Postgres + Redis, with readiness gating and migrations.

- `docker-compose.yml`: `api`, `db` (postgres:18, named volume), `redis`. Env from Compose → `settings`.
- **Healthcheck on `db`** + `depends_on: { db: { condition: service_healthy } }` — so the API waits for Postgres to actually accept connections, not just "started". (v3.2's `depends_on` alone doesn't wait for readiness.)
- The API's entrypoint already runs `alembic upgrade head`, so the schema lands on first `up`.

**Gotcha:** stop native services first (`sudo systemctl stop postgresql redis-server`) to free 5432/6379. Kafka is **not** here yet — it joins on Day 33.

**🔥 Break It:** drop the healthcheck → API races Postgres → `connection refused`. Restore.

**✅** `docker compose up --build` → `/docs` live, schema migrated, DB persists across restarts.

---

# PHASE 6 — Earn "Distributed" (honest) · Day 29

## Day 29 — Multi-Instance Dispatch + Atomic Claim ⭐  *(this is where "distributed" becomes true)*
**Goal:** run multiple API replicas and prove no order is double-dispatched — **without losing aging or fairness**.

**Primary path — Postgres `SELECT … FOR UPDATE SKIP LOCKED`:**
- Today `pick_next_order` reads all PENDING, builds the aged heap, loops to find a serviceable order. With 2+ instances, two could pick the same order.
- Fix: when claiming the winner, re-fetch that row with `.with_for_update(skip_locked=True)` inside the transaction and re-check it's still PENDING before flipping to ASSIGNED. The row lock means only one instance claims it; `SKIP LOCKED` means the other instance doesn't block — it moves to the next order. **Aging, fairness, and the work-conserving loop all stay exactly as built** — you only added a lock on the claim.

**Demonstrate:**
```bash
docker compose up --build --scale api=3
```
Fire concurrent dispatch calls; confirm each order assigned exactly once (check `rider_id` uniqueness / no double-assign in logs).

**The war story:** "Two instances raced on the same PENDING order. I claim with `SELECT … FOR UPDATE SKIP LOCKED` — the lock serializes the claim, SKIP LOCKED keeps the other instance working instead of blocking. Chose it over a Redis sorted set because the sorted set's static score can't express my wait-time aging, and I'd lose the fairness loop."

> **Optional alt (mention, don't necessarily build):** Redis sorted set + `ZREM` atomic claim. Faster, but the score is fixed at insert so aging needs re-scoring, and it hides the heap. Know the tradeoff; the SKIP LOCKED version is the one that keeps your DSA story intact.

**Also surfaces here:** the rate-limiter is already atomic (Day 25), so it's multi-instance-safe. The rider-sync dual-writes are per-rider and idempotent enough for this scale (note reconciliation as the recovery path).

**✅** `--scale api=3`, concurrent dispatch, every order assigned exactly once; "distributed" is earned and demonstrable.

---

# PHASE 7 — Event Streaming (Kafka) · Days 30–33

## Day 30 — Kafka Theory + Compose
**Goal:** understand Kafka vs Pub/Sub, get a broker running in Compose.
- 1-page note: Topic, Partition, Offset, Producer, Consumer, Consumer Group; why Kafka > Pub/Sub (durable, replayable, consumer groups).
- Add Kafka to `docker-compose.yml`. **Prefer KRaft mode (no Zookeeper)** with a modern `confluentinc/cp-kafka` — simpler than the Zookeeper combo. Add `kafka-ui` for inspection.

**Gotcha:** `KAFKA_ADVERTISED_LISTENERS` must expose both an in-network listener (`kafka:9092`, used by the API container) and a host listener (`localhost:9092`, for your shell). Getting these wrong is the #1 Kafka-in-Docker failure.

**✅** Kafka + UI up; you can explain it in 2 minutes.

---

## Day 31 — Producer (config-driven)
**Goal:** publish `order.dispatched` to Kafka instead of Redis Pub/Sub.
```bash
pip install confluent-kafka
```
- `app/core/kafka_producer.py`: `Producer({"bootstrap.servers": settings.kafka_bootstrap})`.
- In `dispatch.py`, replace `redis_client.publish(...)` with `publish_event("order.dispatched", {...})`.

**Gotcha:** `settings.kafka_bootstrap` = `kafka:9092` inside Compose, `localhost:9092` from your shell. **Never hardcode** (the v3.2 bug). Keep the Redis-publish git history — it's the "felt the flaw, then upgraded" story.

**✅** Dispatch produces an event visible in kafka-ui.

---

## Day 32 — Consumer
**Goal:** a Kafka consumer replaces the Pub/Sub worker.
- `app/workers/notification_consumer.py`: `group.id="notifications"`, `auto.offset.reset="earliest"`, poll loop.

**Prove durability (the Day-20 flaw, now fixed):** stop the consumer, dispatch, restart → it **replays the missed event from its offset**. This is the concrete payoff of the Kafka migration.

**✅** Producer + consumer working; missed-while-down events replay.

---

## Day 33 — Multiple Consumer Groups
**Goal:** `notifications`, `analytics` (writes DB), `audit` (writes file) — three groups, one topic, independent offsets/failure.
- Interview answer (already in plan) about consumer groups + replay.

**✅** Three workers, one topic, each independent.

---

# PHASE 8 — Reliability + Auth · Days 34–35

## Day 34 — Idempotency Keys (fixed middleware)
**Goal:** safe retries — duplicate `Idempotency-Key` returns the cached response, no reprocessing.

**The fix (v3.2's bug):** in `BaseHTTPMiddleware` you can't read `response.body` directly — consume the iterator and rebuild:
```python
response = await call_next(request)
body = b"".join([chunk async for chunk in response.body_iterator])
redis_client.setex(f"idempotency:{key}", 86400, body)
# rebuild because the iterator is now exhausted:
return Response(content=body, status_code=response.status_code,
                headers=dict(response.headers), media_type=response.media_type)
```
- Only for POST; only when the header is present.
- **Middleware order:** request_id (outer) → idempotency → rate limit, or document the chosen order and why.

**Gotcha:** caching a dispatch response on replay is *desirable* (prevents double-dispatch) but the cached body is a snapshot — note that in interviews. Razorpay gold.

**✅** Same key returns the identical cached response; the body is actually captured (not empty).

---

## Day 35 — JWT Auth + User model + the deferred Day-19 authz
**Goal:** authentication **and** the ownership/role checks Day 19 deferred — not just locking one endpoint.
```bash
pip install "pyjwt" "passlib[bcrypt]"
```
- **User model + Alembic migration** (id, email, hashed_password, role ∈ {customer, rider, ops}). This is a schema change → real migration, not skipped.
- `/auth/register`, `/auth/login` (bcrypt hash, JWT issue). A `get_current_user` bearer dependency.
- **Protect `/admin/stats`** (role = ops).
- **Fulfil the Day-19 promise on `PATCH /orders/{id}/status`:** the assigned rider may advance their own order; ops may cancel; a customer may not touch status. This is the *permitted-actor* guard layered on top of the *legal-transition* guard. Two orthogonal checks, both now present.

**Gotcha:** `passlib[bcrypt]` has a known `bcrypt 4.x` warning on newer Pythons — pin `bcrypt<4.1` or use `pyjwt`+`bcrypt` directly if it errors. The User table is the project's third migration — review the autogenerate.

**✅** Login issues a JWT; `/admin/stats` requires ops; status transitions enforce both legality *and* actor.

> **Rider penalty (Day-19 deferred) — decide here:** either (a) add a `penalty_count` column to riders + increment on ASSIGNED→CANCELLED-by-rider (small migration + one line in the status handler), or (b) explicitly drop it and keep it a "what I'd add next" talking point. Don't leave it implied-but-absent.

---

# PHASE 9 — Observability + Deploy · Days 36–40

## Day 36 — Prometheus Metrics
- `prometheus-fastapi-instrumentator` → `/metrics`. **✅** endpoint live.

## Day 37 — Grafana Dashboard
- Prometheus + Grafana in Compose; dashboard: request rate, p95/p99, error rate, active orders. Screenshot. **✅**

## Day 38 — Health Checks (DB + Redis + **Kafka**)
- `/health` checks all three (v3.2 omitted Kafka). `db.execute(text("SELECT 1"))`, `redis_client.ping()`, and a Kafka broker metadata/ping. 503 if any down.
- Replaces the trivial `/health` from Day 6/12.

**Gotcha:** Kafka liveness = fetch cluster metadata with a short timeout; don't block the health endpoint waiting on a dead broker. **✅** `/health` reflects all three.

## Day 39 — CI/CD (env-driven so it actually passes)  *(moved before deploy — green tests gate the deploy)*
`.github/workflows/ci.yml`:
- Postgres + Redis service containers.
- **Create the test DB/user** in a step (or point `DATABASE_URL`/`REDIS_URL` env at the CI services — this is why Day 23 made them env-driven). Without this, the hardcoded conftest URL fails in CI.
- Run `pytest --cov=app`, then `black --check`, `flake8` (matches interview Q14's claim).

**Gotcha:** the conftest reads `DATABASE_URL`/`REDIS_URL` from env (Day 23), so CI just sets them to its service containers — no code change. **✅** Green CI badge; tests + lint on every PR.

## Day 40 — Deploy to Railway
- Deploy from GitHub (Dockerfile auto-detected). Postgres + Redis plugins set `DATABASE_URL`/`REDIS_URL`.
- **Migrations:** the Dockerfile entrypoint already runs `alembic upgrade head` on boot — so deploy migrates automatically. (Confirm Railway doesn't parallel-boot replicas that race the migration; if so, use a one-off release command.)
- **Kafka on deploy:** Upstash Kafka free tier → set `kafka_bootstrap` + **SASL_SSL** credentials in config (local was PLAINTEXT; managed needs SASL). If this is heavy, it's acceptable to demo Kafka **locally** and note it in the README — don't let Kafka block the live URL.
- **X-Forwarded-For:** behind Railway's proxy, read the real client IP from `X-Forwarded-For` **only after** confirming a trusted proxy; else it's spoofable. This is where the Day-25 limiter's keying finalizes.

**Gotcha:** managed Kafka auth ≠ local PLAINTEXT — the producer/consumer config branches on environment. **✅** Live public `/docs`; `/health` green.

---

# PHASE 10 — Polish + Interview Prep · Days 41–45

## Day 41 — README + Architecture Diagram
- Excalidraw architecture (now accurate: API replicas, SKIP LOCKED claim, Kafka groups, Redis index, Prometheus/Grafana). README: desc, badges, live URL, diagram, quickstart, **design decisions** (SKIP LOCKED vs sorted set, token-bucket, Kafka vs Pub/Sub), load numbers, Grafana shot. **✅**

## Day 42 — Demo Video
- 3-min Loom: Swagger → create/dispatch → DBeaver row → Kafka event in UI → Grafana → trigger rate limiter → **scale api=3 + concurrent dispatch with no double-assign**. **✅**

## Day 43 — Code Quality Sweep
- `black app/ && flake8 app/ && mypy app/`. Fix the SQLAlchemy `Mapped[]` annotations to clear the `# type: ignore`s (Day-43 commitment). Remove dead code (the `last_assigned_at` write nobody reads). Docstrings. **✅**

## Day 44 — Interview Drills
- Consolidate `Interview_prep.md` (not "INTERVIEW_NOTES.md"). Update the question bank to match what got built:
  - **Q13 (concurrent dispatch):** answer is now **SKIP LOCKED** (primary) with ZREM as the alt — not "prefer ZREM".
  - Add: request_id tracing, the atomic Lua limiter, the SKIP LOCKED race story.
- Time the 2-min pitch; sketch the architecture from memory. **✅**

## Day 45 — Final Buffer
- `git tag v1.0.0`, pin repo, update LinkedIn + resume. **Resume "distributed" is now earned** (Day 29). **✅**

---

## Resume / pitch deltas to make after this plan
- "distributed" is **true** once Day 29 ships (SELECT … FOR UPDATE SKIP LOCKED across `--scale api=3`). If you skip Day 29, soften to "designed for horizontal scaling".
- Swap the dispatch-concurrency line in the pitch/bank from "ZREM" to "SKIP LOCKED" (keeps aging + fairness — a stronger, more honest answer).
- Load numbers are now defensible (limiter toggled/keyed for the test).

## Still optional (know, don't necessarily build)
- Sliding-window rate limiter (~20 lines, Redis sorted set) — talking point only.
- Redis sorted-set dispatch — the alt to SKIP LOCKED; mention the tradeoff.
- Circuit breaker, OpenTelemetry tracing, saga for payments — "what's next" answers.
