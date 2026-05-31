# DeliverIQ — 45-Day Master Plan (v2)
### From Zero Dev Experience → Production-Grade Backend Project

**Now with:** Daily resources (docs + YouTube) + folder structure explained step-by-step

---

## How This Plan Is Structured

Each day has:
- 🎯 **Goal** — what you'll achieve
- 📚 **Resources** — official docs + ONE best YouTube video (max 30 min)
- 💻 **Tasks** — exact things to code
- ✅ **End of day** — proof you completed it

**Rule:** Spend max 30 min watching, then START CODING. Don't binge tutorials.

---

## Project Folder Structure (Explained Like You're 5)

You won't build all of this on Day 6. We'll **grow it organically** as you learn. But here's what each piece means so you have context:

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

---

## What is `__init__.py`?

A file named `__init__.py` (often empty) tells Python: *"this folder is a package — you can import code from it."*

Example:
- Folder `app/models/` with `__init__.py` and `order.py`
- In `main.py`, you can write: `from app.models.order import Order`
- Without `__init__.py`, Python might say "module not found"

You'll create one in every folder. They stay empty 99% of the time.

---

# PHASE 1: Python + Git Fundamentals (Days 1–7)

## Day 1 — Install Everything + Hello World

### 🎯 Goal
Get tools installed, write your first Python program, push to GitHub.

### 📚 Resources
- **Install Python:** [python.org/downloads](https://www.python.org/downloads/) — get 3.11+
  - ⚠️ On Windows: **CHECK "Add Python to PATH"** during install
- **Install VS Code:** [code.visualstudio.com](https://code.visualstudio.com/)
- **Install Git:** [git-scm.com/downloads](https://git-scm.com/downloads)
- **Create GitHub account:** [github.com](https://github.com)
- **Watch:** [Python in 1 Hour — Programming with Mosh](https://www.youtube.com/watch?v=kqtD5dpn9C8) *(watch only first 30 min — variables, loops, functions)*
- **Setup video:** [Python + VS Code Setup — Corey Schafer](https://www.youtube.com/watch?v=-nh9rCzPJ20) *(15 min)*

### 💻 Tasks
1. Install Python, VS Code, Git
2. Open VS Code → install extension: **"Python"** by Microsoft
3. Create a folder anywhere called `deliveriq`
4. Open it in VS Code
5. Create `hello.py`:
   ```python
   name = "DeliverIQ"
   print(f"Welcome to {name}!")

   # Try this: list, dict, loop
   foods = ["pizza", "burger", "biryani"]
   for f in foods:
       print(f"Delivering: {f}")
   ```
6. Run in VS Code terminal: `python hello.py`

### ✅ End of Day
- You see `Welcome to DeliverIQ!` in your terminal
- You can confidently say: *"I installed Python and ran my first program"*

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

### ✅ End of Day
- You understand functions, type hints, classes, `self`, `__init__`

---

## Day 3 — Python Data Structures + List Comprehensions

### 🎯 Goal
Master Python's "magic" syntax that you'll use everywhere.

### 📚 Resources
- **Watch:** [Python List Comprehensions — Corey Schafer](https://www.youtube.com/watch?v=3dt4OGnU5sM) *(20 min)*
- **Docs:** [Python Data Structures](https://docs.python.org/3/tutorial/datastructures.html)

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

# Create virtual env
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# You should see (venv) in your terminal prompt

# Install FastAPI
pip install fastapi uvicorn[standard]

# Freeze versions
pip freeze > requirements.txt

# Commit
git add requirements.txt
git commit -m "chore: add FastAPI dependencies"
git push
```

### ✅ End of Day
- `(venv)` appears in your terminal
- `requirements.txt` lists `fastapi`, `uvicorn`, etc.
- You understand: venv = "private box of libraries for THIS project only"

---

## Day 6 — Build the App Structure (Hands-On)

### 🎯 Goal
Create the project skeleton — but understand EACH file as you make it.

### 📚 Resources
- **Watch:** [FastAPI Tutorial — first 20 min by ArjanCodes](https://www.youtube.com/watch?v=SORiTsvnU28)
- **Docs:** [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)

### 💻 Tasks

We'll build the structure **piece by piece**, understanding each step.

**Step 1: Create `app/` folder and `__init__.py`**
```bash
mkdir app
touch app/__init__.py    # On Windows: type nul > app\__init__.py
```
*Why?* `app/` will hold all your code. `__init__.py` makes Python treat it as a package.

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
- ✅ Virtual environments
- ✅ FastAPI runs locally
- ✅ Project has clean structure starting to form

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
from fastapi import FastAPI

app = FastAPI(title="DeliverIQ")

# Fake in-memory database for now
orders_db = {
    1: {"id": 1, "value": 250, "status": "PENDING"},
    2: {"id": 2, "value": 800, "status": "DELIVERED"},
}

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    if order_id not in orders_db:
        return {"error": "Not found"}
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

Test in Swagger UI — try sending invalid data (negative value), see auto-rejection.

### ✅ End of Day
- You understand: Pydantic = automatic validation + auto-docs in Swagger

---

## Day 10 — PostgreSQL Setup

### 🎯 Goal
Install PostgreSQL, create your database, connect with a GUI.

### 📚 Resources
- **Watch:** [PostgreSQL Setup — Programming with Mosh](https://www.youtube.com/watch?v=qw--VYLpxG4) *(first 20 min)*
- **Install Postgres:** [postgresql.org/download](https://www.postgresql.org/download/)
- **Install DBeaver GUI:** [dbeaver.io/download](https://dbeaver.io/download/)
- **OR easier: Docker:** `docker run -d --name deliveriq-pg -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15`

### 💻 Tasks
1. Install Postgres (or use Docker command above)
2. Install DBeaver
3. Connect to Postgres in DBeaver (host: `localhost`, user: `postgres`, password: what you set)
4. Create a database: right-click → `Create Database` → name it `deliveriq_db`
5. Verify by browsing in DBeaver

### ✅ End of Day
- DBeaver shows you connected to `deliveriq_db`
- You can right-click → "SQL Editor" → run `SELECT 1;` successfully

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

DATABASE_URL = "postgresql://postgres:password@localhost:5432/deliveriq_db"

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

**Create `app/routers/orders.py`:**
```bash
mkdir app/routers
touch app/routers/__init__.py
```

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
- Same as Day 11–12 (reference back if stuck)

### 💻 Tasks
- Create `app/models/rider.py` — fields: id, name, current_lat, current_lon, is_available, created_at
- Create `app/schemas/rider.py` — `RiderCreate`, `RiderResponse`
- Create `app/routers/riders.py` — POST, GET, list
- Register router in `main.py`

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

## Day 15 — Redis Setup + Basics

### 🎯 Goal
Install Redis, learn the 10 commands you'll use 90% of the time.

### 📚 Resources
- **Watch:** [Redis in 20 minutes — Fireship](https://www.youtube.com/watch?v=G1rOthIU-uo)
- **Watch:** [Redis Crash Course — Hussein Nasser](https://www.youtube.com/watch?v=jgpVdJB2sKQ) *(deeper)*
- **Docs:** [Redis Data Types](https://redis.io/docs/data-types/)
- **Install:** Docker — `docker run -d --name deliveriq-redis -p 6379:6379 redis:7`
- **GUI:** [RedisInsight](https://redis.io/docs/connect/insight/) (free)

### 💻 Tasks
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

### 🎯 Goal
Build the rate limiter — your #1 interview talking point.

### 📚 Resources
- **Watch:** [Token Bucket Algorithm — ByteByteGo](https://www.youtube.com/watch?v=mhUQe4BKZXs) *(7 min, gold)*
- **Read:** [Cloudflare's Rate Limiting Explanation](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/)
- **Docs:** [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)

### 💻 Tasks

Create `app/middleware/rate_limiter.py`:
```bash
mkdir app/middleware
touch app/middleware/__init__.py
```

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

**Test it:** Open terminal, run this 110 times fast:
```bash
for i in {1..110}; do curl http://localhost:8000/health; done
# Or on Windows PowerShell:
1..110 | ForEach-Object { curl http://localhost:8000/health }
```

You'll see 429 errors after the 100th. **MAGIC. You just built rate limiting.**

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

### 💻 Tasks

Create `app/services/dispatch.py`:
```bash
mkdir app/services
touch app/services/__init__.py
```

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

In `app/routers/orders.py`, after creating order, call `add_to_dispatch_queue()`.
Create new endpoint `POST /dispatch` that calls `pop_highest_priority()`.

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

Add `PATCH /orders/{id}/status` endpoint that uses this.

### ✅ End of Day
- Trying to mark DELIVERED → PENDING returns 400 error

---

## Day 20 — Redis Pub/Sub (Pre-Kafka Practice)

### 🎯 Goal
Build event publishing — we'll upgrade to Kafka in Week 5.

### 📚 Resources
- **Watch:** [Redis Pub/Sub — Hussein Nasser](https://www.youtube.com/watch?v=KIFA_fFzSbo)
- **Docs:** [Redis Pub/Sub](https://redis.io/docs/manual/pubsub/)

### 💻 Tasks
Publish event when order dispatched:
```python
redis_client.publish("order.dispatched", json.dumps({
    "order_id": order_id,
    "rider_id": rider_id,
    "timestamp": time.time()
}))
```

Create a separate script `app/workers/notification_worker.py`:
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

Run in separate terminal: `python -m app.workers.notification_worker`.
Now dispatch an order — see notification log.

### ✅ End of Day
- Pub/Sub works
- You feel the limitation: if worker is off, message is lost (this is why we'll move to Kafka)

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
    response = client.post("/orders", json={"value": -10, ...})
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
DATABASE_URL=postgresql://postgres:password@localhost:5432/deliveriq_db
REDIS_URL=redis://localhost:6379
```

Create `.env.example` (commit this, NOT `.env`):
```
DATABASE_URL=
REDIS_URL=
```

Use `settings.database_url` everywhere instead of hardcoded strings.

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
Create `Dockerfile` in project root:
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

## Day 26 — docker-compose for Full Stack

### 🎯 Goal
One command starts FastAPI + Postgres + Redis.

### 📚 Resources
- **Watch:** [docker-compose Tutorial — TechWorld with Nana](https://www.youtube.com/watch?v=DM65_JyGxCo) *(15 min)*
- **Docs:** [docker-compose reference](https://docs.docker.com/compose/)

### 💻 Tasks
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/deliveriq_db
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: deliveriq_db
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

Run: `docker-compose up --build`. Visit `localhost:8000/docs`.

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

# PHASE 5: Kafka + Advanced Features (Days 29–35)

## Day 29 — Kafka Theory

### 🎯 Goal
Understand Kafka before touching it.

### 📚 Resources
- **Watch:** [Kafka in 100 Seconds — Fireship](https://www.youtube.com/watch?v=uvb00oaa3k8) *(2 min)*
- **Watch:** [Apache Kafka Explained — Confluent](https://www.youtube.com/watch?v=06iRM1Ghr1k) *(7 min, official)*
- **Watch:** [Kafka Deep Dive — Hussein Nasser](https://www.youtube.com/watch?v=Ch5VhJzaoaI) *(30 min)*
- **Course (free):** [Confluent Kafka 101](https://developer.confluent.io/learn-kafka/apache-kafka/events/)

### 💻 Tasks
**No code today.** Just learn:
- Topic, Partition, Offset, Producer, Consumer, Consumer Group
- Why Kafka > Redis Pub/Sub: persistence, replay, scaling

Write a 1-page note in your own words. This goes into your interview prep.

### ✅ End of Day
- You can explain Kafka in 2 minutes to a beginner

---

## Day 30 — Kafka in docker-compose

### 🎯 Goal
Get Kafka running locally.

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

Run `docker-compose up`. Visit `localhost:8080` → Kafka UI.

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
- Events appear in Kafka UI under `order.dispatched` topic

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
Create 3 workers, each in own file:
- `notification_consumer.py` — group `notifications`
- `analytics_consumer.py` — group `analytics` (writes to DB)
- `audit_consumer.py` — group `audit-log` (writes to file)

All consume the same `order.dispatched` topic. Each gets its own copy.

**This is gold.** In an interview, you say:
> "I have 3 independent consumers — notifications, analytics, audit — each consuming the same Kafka topic via different consumer groups. They scale and fail independently. That's event-driven architecture."

### ✅ End of Day
- 3 separate worker scripts, all reading same topic, doing different things

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

### ✅ End of Day
- Same `Idempotency-Key` returns same response on retry

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

Add `/auth/register`, `/auth/login` endpoints. Protect `/admin/stats` with JWT bearer dependency.

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
Visual dashboard for showpiece screenshot.

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

Login to Grafana (`admin`/`admin`), add Prometheus as data source, build dashboard with:
- Request rate
- p95/p99 latency
- Error rate
- Active orders

**Take SCREENSHOTS.** These go in README.

### ✅ End of Day
- You have a Grafana dashboard screenshot — interview gold

---

## Day 38 — Health Checks

### 🎯 Goal
Production-ready health endpoint.

### 💻 Tasks
```python
@app.get("/health")
def health(db: Session = Depends(get_db)):
    checks = {}
    try:
        db.execute("SELECT 1")
        checks["db"] = "up"
    except: checks["db"] = "down"

    try:
        redis_client.ping()
        checks["redis"] = "up"
    except: checks["redis"] = "down"

    all_up = all(v == "up" for v in checks.values())
    status_code = 200 if all_up else 503
    return JSONResponse(content={"status": "ok" if all_up else "degraded", **checks}, status_code=status_code)
```

### ✅ End of Day
- Health check covers DB + Redis + Kafka

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
- Write README with: description, badges, live URL, architecture diagram, quickstart, design decisions, load test results, screenshot of Grafana

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
- Add docstrings to every function
- Squash messy commits with `git rebase -i`

---

## Day 44 — Interview Drills

### 📚 Resources
- **Watch:** [System Design Mock Interviews — Hello Interview](https://www.youtube.com/@hello_interview)

### 💻 Tasks
- Write answers to all 20 interview questions from your notes
- Record yourself doing the 2-min pitch
- Sketch architecture from memory on paper
- Practice with a friend if possible

---

## Day 45 — Final Buffer

### 💻 Tasks
- Tag release: `git tag v1.0.0 && git push --tags`
- Pin repo on GitHub profile
- Update LinkedIn projects section
- Update resume with project bullets
- **Rest. You did it.**

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

## When Stuck
1. **Read the exact error message** (90% of the time it tells you the fix)
2. **Google the exact error**
3. **Ask Claude/ChatGPT** with: error + relevant code + what you tried
4. **Stack Overflow** for tricky ones
5. **Discord:** [FastAPI Discord](https://discord.gg/VQjSZaeJmf), [Python Discord](https://pythondiscord.com)

---

# Final Sanity Check

Before you start Day 1, ensure:
- [ ] You have a Windows/Mac/Linux laptop with ~10GB free disk space
- [ ] You can dedicate 3–4 hours daily (no exceptions for 45 days)
- [ ] You have a GitHub account
- [ ] You're emotionally ready to be confused — that's the LEARNING part

**Don't read this whole doc again.** Open Day 1. Start.

🚀 *See you on Day 45.*