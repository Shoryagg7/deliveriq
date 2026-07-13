# SQL & DBMS — Zero to Master (from absolute scratch)

> Start here, before everything else in
> [Backend_Interview_Zero_to_Master.md](Backend_Interview_Zero_to_Master.md).
> SQL is the one skill every backend/SDE interview tests directly — a dedicated
> round at most companies — and it's the foundation Levels 1–2 of the backend
> guide build on. This doc assumes you know **nothing** and takes you to
> interview-master level: **concept (why)** → **diagram (see it)** →
> **soundbite / trap** → **practice (do it)**.
>
> **Framing:** SQL is the *language*; PostgreSQL is just where you run it. Run
> every query against your **own DeliverIQ tables** (orders, riders) —
> practicing on a schema you built makes it stick *and* gives you interview
> talking points.

---

# PART A — THE ROADMAP (read this first)

## The path

```
 LEVEL 0        LEVEL 1        LEVEL 2       LEVEL 3      LEVEL 4
 What a DB  →   Reading    →   Aggregation → JOINs    →   Subqueries
 even is        rows                                       & CTEs
 (day 1)        (days 2–5)     (days 6–8)    (days 9–13)  (days 14–17)

 LEVEL 5 ⭐      LEVEL 6        LEVEL 7           LEVEL 8
 Window     →   Writing &  →   DBMS theory   →   Classic interview
 functions      designing      (the "explain      patterns
 (days 18–24)   (days 25–27)    X" round)         (ongoing reps)
                               (days 28–30)
```

**~30 days at 1–1.5 hr/day.** Each level ends with a **gate** — do not move on
until you pass it. Faster is fine if the gates pass; slower is fine too. The
levels are ordered so each one only uses what came before.

## How to study (the method — this matters more than the material)

1. **20/80 rule:** at most 20% of your time watching videos, at least 80%
   typing queries. Watching feels like learning; typing *is* learning.
2. **Never copy-paste a query.** Type it. Your fingers are learning syntax.
3. **Predict-then-run:** before hitting Enter, say out loud what the result
   will be — how many rows, what shape. When you're wrong, *that gap is the
   lesson*. Figure out why before moving on.
4. **Two windows open always:** this doc + a query prompt (`psql` into your
   DeliverIQ DB, or DBeaver). Every concept gets tried on your own tables
   within 60 seconds of reading it.
5. **Weekly review:** re-do the Final Check (end of this doc) every weekend.
   Speed and accuracy both count.

## Where to practice (pick ONE main grind + your own DB)

| Platform | What it's for | When |
|---|---|---|
| Your own DeliverIQ Postgres | trying every concept on a real schema you built | throughout, daily |
| [SQLBolt](https://sqlbolt.com) | interactive absolute basics, zero setup, in-browser | Level 0–1 (day 1–3) |
| [pgexercises.com](https://pgexercises.com) | guided Postgres exercises, gentle ramp | Levels 1–4 |
| 🥇 [LeetCode — Top SQL 50](https://leetcode.com/studyplan/top-sql-50/) | **the main grind** — curated, ordered, interview-style | Level 1 onward, daily |
| [practicewindowfunctions.com](https://www.practicewindowfunctions.com) | 75+ dedicated window-function drills | Level 5 |
| [DataLemur](https://datalemur.com) | real company SQL questions, interview-focused | Levels 5–8 |
| [StrataScratch](https://www.stratascratch.com) | Uber/Airbnb/Netflix real questions | Levels 5–8 |
| [HackerRank SQL](https://www.hackerrank.com/domains/sql) | extra free volume if you want more reps | optional |

## Videos (watch per-level, not all at once)

- [freeCodeCamp · SQL Full Course (Mike Dane)](https://www.youtube.com/playlist?list=PL-7OvuNicwAsTJLTE6Y-xVBOp_Fw2MFwE)
  — Levels 0–4 & 6: watch only the section named in each level.
- [Gate Smashers · DBMS playlist](https://www.youtube.com/gatesmashers) —
  Level 7 theory: normalization ([playlist](https://www.youtube.com/playlist?list=PLjgyGylma3IFNC7sNZOSbwGQPK_MYtCFW)),
  keys, indexing, ACID, [transactions & concurrency](https://www.youtube.com/watch?v=t5hsV9lC1rU),
  isolation levels, correlated subqueries, Nth-highest salary.
- Window functions (Level 5, watch both):
  [Real-World Examples](https://www.youtube.com/watch?v=ZJGp6KtuTZQ) ·
  [Beginner → Pro · Intellipaat](https://www.youtube.com/watch?v=C3ECf4kj4W8)

---
---

# LEVEL 0 — What a database even is (Day 1)

## 0.1 The problem databases solve

You could store app data in a text file or an Excel sheet. Three things kill
that the moment software depends on it:

1. **Concurrency** — two programs writing one file at once corrupt it. A
   database safely handles thousands of simultaneous readers/writers.
2. **Integrity** — a file happily stores an order pointing to a rider that
   doesn't exist, or a price of `"banana"`. A database *refuses* — rules live
   in the schema.
3. **Speed at scale** — finding one row in a million-line file means reading
   the whole file. A database with an index does it in a few steps.

A **relational database** stores data in **tables** — typed columns × rows —
and **SQL** (Structured Query Language) is how you talk to it.

```
  YOU (or your app)                    DATABASE SERVER (Postgres, :5432)
 ┌──────────────────┐   SQL text     ┌──────────────────────────────────┐
 │ psql / DBeaver / │ ─────────────► │ parser → planner → executor      │
 │ FastAPI app      │                │            │                     │
 │                  │ ◄───────────── │            ▼                     │
 └──────────────────┘   result rows  │   tables on DISK (durable)       │
                                     └──────────────────────────────────┘
```

The one mind-shift from normal programming: **SQL is declarative.** You state
*WHAT* you want ("all pending orders, highest value first"); the engine decides
*HOW* (which index, which order of operations). You never write the loop.

**Soundbite:** "SQL is declarative — I describe the result set, the query
planner picks the algorithm. That's why the same query can be fast or slow
depending on indexes: I control the what, the planner controls the how."

## 0.2 Your first queries (on your own data)

Connect to your project DB and look around:

```sql
SELECT * FROM orders;             -- every column (*), every row
SELECT id, value FROM orders;     -- just these columns
SELECT * FROM riders;
```

That's already real SQL. Reading rows is Level 1; everything else builds on it.

## 🎯 GATE 0 — move on when you can:
- Explain to a friend why an app uses Postgres instead of a JSON file
  (concurrency, integrity, speed).
- Connect to your DB and SELECT from both tables without looking anything up.
- **Practice:** [SQLBolt](https://sqlbolt.com) lessons 1–6 (in-browser,
  ~45 min).

---
---

# LEVEL 1 — Reading rows: SELECT mastery (Days 2–5)

## 1.1 The clauses

```sql
SELECT id, value, status          -- which COLUMNS (or * for all)
FROM orders                       -- which TABLE
WHERE status = 'PENDING'          -- which ROWS (filter)
  AND value > 200
ORDER BY value DESC               -- sort (DESC = high→low; default ASC)
LIMIT 5;                          -- cut to first N (OFFSET n skips n first)
```

WHERE toolbox: `=  <>  >  >=  <  <=` · `AND OR NOT` · `IN ('A','B')` ·
`BETWEEN 100 AND 500` · `LIKE 'RA%'` (`%` = any chars, `_` = one char) ·
`DISTINCT` in the SELECT de-duplicates the output.

## 1.2 THE diagram — logical execution order ⭐

You *write* clauses in one order; the engine *runs* them in another. This one
diagram explains half of all SQL confusion, now and at Level 5:

```
 You WRITE:                          Engine RUNS:
 SELECT status, COUNT(*)             1. FROM      orders        get the table
 FROM orders                         2. WHERE     value > 100   filter ROWS
 WHERE value > 100                   3. GROUP BY  status        form groups
 GROUP BY status                     4. HAVING    COUNT(*) > 5  filter GROUPS
 HAVING COUNT(*) > 5                 5. SELECT    compute output columns
 ORDER BY 2 DESC                     6. ORDER BY  sort the result
 LIMIT 3;                            7. LIMIT     cut it
```

Consequences you'll hit constantly:
- `WHERE` runs **before** `SELECT` → you can't use a SELECT alias in WHERE.
- `WHERE` runs **before** grouping → it can never see `COUNT(*)` (that's what
  HAVING is for, Level 2).
- `ORDER BY` runs **after** SELECT → it *can* use aliases.

## 1.3 NULL — the third truth value ⭐

`NULL` means **unknown**, not zero and not empty-string. Any comparison with
NULL yields NULL (not TRUE, not FALSE), and WHERE only keeps rows that are
**TRUE**:

```
 WHERE rider_id = NULL    → always 0 rows (NULL = NULL is NULL, not TRUE!)
 WHERE rider_id IS NULL   → ✅ the unassigned orders
 WHERE rider_id <> 5      → silently DROPS rows where rider_id IS NULL
                            (unknown <> 5 is unknown → not TRUE → filtered out)
```

**Trap (asked constantly):** "Why does `WHERE col <> 'X'` not return rows where
col is NULL?" — because NULL comparisons are unknown, and WHERE keeps only TRUE.
Handle NULLs explicitly: `IS NULL / IS NOT NULL / COALESCE(col, fallback)`.

## 🎯 GATE 1 — move on when you can, cold:
- Write a filtered, sorted, limited query on `orders` in one go, no reference.
- Explain the 7-step execution order and *why* WHERE can't use an alias.
- Predict what `WHERE rider_id <> 5` does with NULLs — and fix it.
- **Watch:** freeCodeCamp → Basic Queries, Wildcards, ORDER BY (~30 min).
- **Practice:** SQLBolt through lesson 12 · LeetCode SQL 50 → "Select" section
  (first ~5 problems) · pgexercises "Basic" set.
- **DeliverIQ tie:** top-5 pending orders by value; all orders with no rider.

---
---

# LEVEL 2 — Aggregation: collapsing rows (Days 6–8)

## 2.1 The mental model

Aggregates (`COUNT SUM AVG MIN MAX`) collapse many rows into one number.
`GROUP BY` says *what to collapse per*:

```
 orders                          GROUP BY status
 ┌─────────┬───────┐            ┌──────────────────────────────┐
 │ status  │ value │            │ PENDING  bucket: ▓▓▓ (3 rows)│→ 1 output row:
 │ PENDING │  100  │            │                              │  PENDING, 3, 216.6
 │ PENDING │  400  │   ─────►   │ ASSIGNED bucket: ▓▓  (2 rows)│→ 1 output row:
 │ PENDING │  150  │            │                              │  ASSIGNED, 2, 525.0
 │ ASSIGNED│  800  │            └──────────────────────────────┘
 │ ASSIGNED│  250  │             SELECT status, COUNT(*), AVG(value)
 └─────────┴───────┘             FROM orders GROUP BY status;
```

One output row **per group**. Rule: every SELECT column is either **in the
GROUP BY** or **inside an aggregate** — anything else is ambiguous (which row's
value would it be?) and Postgres rejects it.

## 2.2 WHERE vs HAVING (the #1 beginner trap)

Recall the execution order: WHERE filters **rows before** grouping; HAVING
filters **groups after**.

```sql
SELECT rider_id, COUNT(*) AS n
FROM orders
WHERE status = 'DELIVERED'      -- rows in: only delivered orders counted
GROUP BY rider_id
HAVING COUNT(*) > 5;            -- groups out: only busy riders survive
```

## 2.3 COUNT's three faces + the NULL-in-aggregates rule

```
 COUNT(*)              counts ROWS                 → 10
 COUNT(rider_id)       counts NON-NULL values      → 7  (skips unassigned!)
 COUNT(DISTINCT rider_id)  counts unique non-NULL  → 3
```

All aggregates **ignore NULLs** (`AVG(col)` averages only the non-null values)
— and `AVG` over an empty/all-null set returns **NULL, not 0** (→ the guard in
IP §33). This NULL-skipping is exam material everywhere.

## 🎯 GATE 2 — move on when you can:
- Draw the bucket diagram from memory for a GROUP BY query.
- State why `SELECT status, value ... GROUP BY status` is illegal.
- Answer instantly: `COUNT(*)` vs `COUNT(col)` on a column with NULLs.
- **Watch:** freeCodeCamp → Functions + Aggregation.
- **Practice:** LeetCode SQL 50 → "Sorting & Grouping" section (all of it).
- **DeliverIQ tie:** orders per status; average value per status; riders with
  more than 1 assigned order.

---
---

# LEVEL 3 — JOINs: combining tables (Days 9–13)

## 3.1 Why data is split across tables (keys, 60 seconds)

The rider's name is stored **once**, in `riders`; orders point at it via
`rider_id` (**foreign key** → `riders.id`, the **primary key**). One fact, one
place — update Asha's name in one row, not in 500 copied orders. (Formal
version: normalization, Level 6.) JOINs are how you stitch the facts back
together at read time.

## 3.2 The four joins — as rows, not Venn diagrams

```
 orders o                riders r
 ┌────┬──────────┐       ┌────┬───────┐
 │ id │ rider_id │       │ id │ name  │
 │ 1  │    2     │       │ 2  │ Asha  │
 │ 2  │   NULL   │       │ 3  │ Ravi  │      ← Ravi has no orders
 │ 3  │    2     │       └────┴───────┘
 └────┴──────────┘       ← order 2 unassigned

 SELECT o.id, r.name FROM orders o <JOIN> riders r ON o.rider_id = r.id;

 INNER JOIN → only matches          LEFT JOIN → ALL left rows, NULLs padded
 │ 1 │ Asha │                       │ 1 │ Asha │
 │ 3 │ Asha │                       │ 2 │ NULL │  ← kept!
 (order 2 and Ravi vanish)          │ 3 │ Asha │

 RIGHT JOIN → all RIGHT rows        FULL JOIN → everything from both sides
 │ 1 │ Asha │                       │ 1 │ Asha │
 │ 3 │ Asha │                       │ 2 │ NULL │
 │ ∅ │ Ravi │  ← kept!              │ 3 │ Asha │
                                    │ ∅ │ Ravi │
```

In practice you use INNER and LEFT 95% of the time (a RIGHT JOIN is just a LEFT
JOIN written backwards).

## 3.3 The anti-join — "rows with NO match" ⭐

"Orders with no rider" / "customers who never ordered" — a top-3 interview
pattern:

```sql
SELECT o.*                          -- way 1: LEFT JOIN ... IS NULL
FROM orders o
LEFT JOIN riders r ON o.rider_id = r.id
WHERE r.id IS NULL;                 -- keep only the NULL-padded rows

SELECT o.* FROM orders o            -- way 2: NOT EXISTS (Level 4)
WHERE NOT EXISTS (SELECT 1 FROM riders r WHERE r.id = o.rider_id);
```

## 3.4 The ON-vs-WHERE trap on LEFT JOIN ⭐

"Why is my LEFT JOIN dropping rows?" — the classic:

```sql
-- BROKEN: filters AFTER padding → NULL-padded rows fail the WHERE → INNER JOIN
... LEFT JOIN riders r ON o.rider_id = r.id
WHERE r.status = 'AVAILABLE';

-- RIGHT: extra condition on the RIGHT table goes in the ON
... LEFT JOIN riders r ON o.rider_id = r.id AND r.status = 'AVAILABLE';
```

Rule: on a LEFT JOIN, conditions about the **right** table belong in `ON`;
conditions about the **left** table belong in `WHERE`.

**Also know:** **self-join** — a table joined to itself with two aliases
(`riders a JOIN riders b ON a.cell = b.cell AND a.id < b.id` → pairs of riders
in the same geohash cell).

## 🎯 GATE 3 — move on when you can:
- Reproduce the four-join diagram from memory for those two tables.
- Write the anti-join both ways without reference.
- Explain the ON-vs-WHERE trap and fix a broken example.
- **Watch:** freeCodeCamp → Joins. *(Gate Smashers "Joins vs Nested vs
  Correlated Subquery" is gold for placements.)*
- **Practice:** LeetCode SQL 50 → "Basic Joins" (do ALL) · pgexercises "Joins".
- **DeliverIQ tie:** each order with its rider's name (LEFT JOIN — keep
  unassigned); riders who have never been assigned (anti-join).

---
---

# LEVEL 4 — Subqueries & CTEs (Days 14–17)

## 4.1 The three shapes of subquery

```sql
-- SCALAR: returns one value; usable anywhere a value goes
SELECT * FROM orders WHERE value > (SELECT AVG(value) FROM orders);

-- LIST: returns a column; use with IN / NOT IN / EXISTS
SELECT * FROM riders
WHERE id IN (SELECT rider_id FROM orders WHERE status = 'ASSIGNED');

-- CORRELATED ⭐: inner query references the OUTER row → re-runs PER ROW
SELECT o.* FROM orders o
WHERE o.value > (SELECT AVG(i.value) FROM orders i
                 WHERE i.status = o.status);
--                                  ▲ each outer row plugs ITS status in:
--                    "orders above the average OF THEIR OWN status group"
```

```
 CORRELATED = a loop in disguise:
 for each outer row o:                 ← that's why they can be slow,
     run inner query using o.status      and why interviewers ask
     keep o if condition holds           "how would you rewrite this?"
                                         (answer: JOIN or window function)
```

## 4.2 The NOT IN / NULL landmine ⭐ (senior-signal trap)

```sql
SELECT * FROM riders
WHERE id NOT IN (SELECT rider_id FROM orders);   -- rider_id has NULLs...
-- → returns ZERO ROWS. ALWAYS.
```

Why: `id NOT IN (2, NULL)` unfolds to `id <> 2 AND id <> NULL` — and
`id <> NULL` is NULL (Level 1.3), so the whole condition is never TRUE.
**`NOT EXISTS` does not have this problem** — it's the safe default for
"has no match."

## 4.3 CTEs — naming your steps

`WITH` gives a subquery a name; chain them to decompose a problem (the SQL
version of breaking a CP problem into subproblems — readability scores points):

```sql
WITH delivered AS (
    SELECT rider_id, COUNT(*) AS n
    FROM orders WHERE status = 'DELIVERED'
    GROUP BY rider_id
),
busy AS (
    SELECT * FROM delivered WHERE n > 5
)
SELECT r.name, b.n
FROM busy b JOIN riders r ON r.id = b.rider_id;
```

**Recursive CTEs** (`WITH RECURSIVE`) walk hierarchies — org charts, category
trees, "manager chains." Know that they exist and the shape (base case
`UNION ALL` recursive step); one practice problem is enough.

## 🎯 GATE 4 — move on when you can:
- Explain correlated vs plain subquery with the "loop in disguise" framing.
- State the NOT IN / NULL trap from memory and why NOT EXISTS is safe.
- Refactor a nested two-level subquery into a clean WITH chain.
- **Watch:** Gate Smashers → "Correlated Subquery" + "EXISTS and NOT EXISTS".
- **Practice:** LeetCode SQL 50 → "Subqueries" section (all).
- **DeliverIQ tie:** orders above their status-group's average value
  (correlated); riders with no orders via NOT EXISTS.

---
---

# LEVEL 5 ⭐ — Window Functions (Days 18–24) — THE BIG ONE

> The single most-asked advanced SQL topic at Uber/Razorpay/PhonePe-tier
> companies. **Over-invest here** — this is where candidates win or lose the
> SQL round. Give it a full week.

## 5.1 The mental model — GROUP BY's opposite

```
 GROUP BY:  many rows  →  ONE row per group      (detail rows are GONE)
 WINDOW:    every row KEPT + a new column computed over its group

 ROW_NUMBER() OVER (PARTITION BY status ORDER BY value DESC) AS rn

 ┌────┬──────────┬───────┬────┐
 │ id │ status   │ value │ rn │
 ├────┼──────────┼───────┼────┤
 │ 7  │ PENDING  │  900  │ 1  │ ┐ partition 1: PENDING rows,
 │ 2  │ PENDING  │  400  │ 2  │ │ numbered by value DESC
 │ 9  │ PENDING  │  150  │ 3  │ ┘
 │ 4  │ ASSIGNED │  800  │ 1  │ ┐ partition 2: numbering RESTARTS
 │ 1  │ ASSIGNED │  250  │ 2  │ ┘
 └────┴──────────┴───────┴────┘
   every original row is still here — the window just ADDED a column
```

Anatomy: `FUNCTION() OVER (PARTITION BY <group> ORDER BY <sort>)` —
"compute FUNCTION over each PARTITION, walking rows in this ORDER."
No PARTITION BY = one window over the whole table.

## 5.2 The ranking trio — know the tie behavior cold

```
 value:        900   900   700
 ROW_NUMBER →   1     2     3     unique numbers, ties broken arbitrarily
 RANK       →   1     1     3     ties share, next rank SKIPS
 DENSE_RANK →   1     1     2     ties share, NO skip
```

"Second highest value" with duplicates present? `DENSE_RANK = 2` — if you say
ROW_NUMBER you just failed the follow-up. This exact distinction is asked
everywhere.

## 5.3 The 4 patterns that cover ~90% of questions

```sql
-- 1. TOP-N PER GROUP (the most-asked SQL question, period)
WITH ranked AS (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY status
                                 ORDER BY value DESC) AS rn
  FROM orders o
)
SELECT * FROM ranked WHERE rn <= 3;      -- top 3 per status

-- 2. RUNNING TOTAL
SUM(value) OVER (ORDER BY created_at)                    -- cumulative revenue

-- 3. ROW vs PREVIOUS ROW (streaks, day-over-day deltas)
value - LAG(value) OVER (ORDER BY created_at)            -- change vs previous
--      LEAD(...) looks forward instead

-- 4. GROUP STAT WITHOUT COLLAPSING (compare each row to its group)
value - AVG(value) OVER (PARTITION BY status)            -- delta vs group avg
```

## 5.4 The trap: windows can't go in WHERE ⭐

Execution order (Level 1.2): window functions compute during **SELECT (step
5)** — after WHERE (step 2). So `WHERE rn = 1` on the same level is illegal.
**The fix is the CTE-then-filter shape in pattern 1** — wrap, then filter
outside. Interviewers deliberately test this exact gotcha.

*(Frames — `ROWS BETWEEN ...` — exist to fine-tune running windows, e.g. a
7-day moving average. Recognize the syntax; don't memorize it.)*

## 🎯 GATE 5 — move on when you can:
- Write top-N-per-group from a blank editor in under 3 minutes.
- Recite the tie table (ROW_NUMBER/RANK/DENSE_RANK) and pick the right one for
  "2nd highest with duplicates."
- Explain from the execution-order diagram *why* a window can't sit in WHERE.
- **Watch:** both Level-5 videos listed in Part A.
- **Practice:** [practicewindowfunctions.com](https://www.practicewindowfunctions.com)
  (aim for 30+) · LeetCode SQL 50 → window problems · then DataLemur windows.
- **DeliverIQ tie:** top-3 orders per status; running revenue by day; each
  rider's order-count rank.

---
---

# LEVEL 6 — Writing & designing data (Days 25–27)

## 6.1 The write statements

```sql
INSERT INTO orders (customer_id, value, status) VALUES (1, 250.0, 'PENDING');

UPDATE orders SET status = 'CANCELLED' WHERE id = 3;
DELETE FROM orders WHERE id = 3;
```

**The horror story every engineer tells:** `UPDATE`/`DELETE` **without a
WHERE** hits *every row in the table*, instantly. Discipline: write the WHERE
first, or run it as a SELECT first to see what you're about to touch. Inside a
transaction (`BEGIN; ... ROLLBACK;`) you get an undo button — Level 7.

## 6.2 Designing a table

```sql
CREATE TABLE orders (
    id          SERIAL PRIMARY KEY,             -- auto-incrementing PK
    customer_id INT      NOT NULL,              -- required
    value       NUMERIC(10,2) NOT NULL CHECK (value > 0),
    status      TEXT     NOT NULL DEFAULT 'PENDING',
    rider_id    INT      REFERENCES riders(id), -- FK: must exist in riders
    created_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (customer_id, created_at)
);
```

Constraints are the DB **refusing bad data** — the last line of defense behind
your API validation (two layers, deliberately → IP §4). Types to know:
`INT/BIGINT`, `NUMERIC` (exact — money), `FLOAT` (approximate — never money),
`TEXT/VARCHAR(n)` (same performance in Postgres), `BOOLEAN`,
`TIMESTAMPTZ` (with timezone — default to this), `DATE`, `UUID`, `JSONB`.

## 6.3 Normalization — the WHY in one diagram

```
 UNNORMALIZED — rider's info copied into every order:
 orders: │ id │ value │ rider_name │ rider_phone │
         │ 1  │ 250   │ Asha       │ 98x-11      │   Asha changes her number →
         │ 5  │ 800   │ Asha       │ 98x-11      │   update N rows; miss one →
         │ 9  │ 150   │ Asha       │ 98x-11      │   two "truths" (UPDATE ANOMALY)

 NORMALIZED — the fact lives ONCE, orders point at it:
 orders: │ id │ value │ rider_id │ ──► riders: │ id │ name │ phone │
```

The normal forms, for interviews:
- **1NF:** atomic cells — no lists in a column (`'2,7,9'` in one cell is the sin).
- **2NF/3NF:** every non-key column depends on **the key, the whole key, and
  nothing but the key** — no column depending on part of a composite key (2NF)
  or on another non-key column (3NF, e.g. storing `city` and `city_pincode`
  together).
- **Denormalization** = deliberately copying data back in for read speed,
  accepting the update anomaly — a *choice*, made later, with eyes open
  (→ backend guide §1.2).

## 🎯 GATE 6 — move on when you can:
- CREATE a sensible `payments` table for DeliverIQ from scratch — right types,
  constraints, FK.
- Tell the update-anomaly story and define 1NF/2NF/3NF in one line each.
- **Watch:** Gate Smashers normalization playlist (1NF→BCNF).
- **Practice:** design 2–3 small schemas on paper (library, food app,
  ride-sharing); write the CREATE TABLEs; find what's wrong with a
  denormalized version.

---
---

# LEVEL 7 — DBMS theory: the "explain X" round (Days 28–30)

> Round-1 interviews ask you to *explain*, not query. Most of the deep material
> lives in the backend guide — this level is the SQL-side summary + pointers.

## 7.1 Indexes
B-tree, O(log n) vs seq scan, write cost, composite/leftmost-prefix, partial
indexes, `EXPLAIN ANALYZE` → **backend guide §2.1** (read it now — with
Levels 1–6 done, it will land). One-liner: *"an index trades write speed and
space for read speed; I index what WHERE/JOIN/ORDER BY touch, and verify with
EXPLAIN."*

## 7.2 Transactions, ACID, isolation
`BEGIN → COMMIT/ROLLBACK`, the ACID letters concretely, isolation levels and
their anomalies (dirty/non-repeatable/phantom reads), locking →
**backend guide §2.2–2.5**. Try it live in two `psql` windows: `BEGIN` +
`UPDATE` in one, watch the other block, then `COMMIT` — seeing a lock beats
reading about one.

## 7.3 Keys taxonomy (definition round, 15 minutes)
- **Super key:** any column set that uniquely identifies a row.
- **Candidate key:** a *minimal* super key (no removable column).
- **Primary key:** the candidate key you chose. **Alternate:** the ones you
  didn't.
- **Composite key:** a key of 2+ columns.
- **Surrogate vs natural:** made-up id (`SERIAL`) vs real-world attribute
  (email). Default to surrogate — natural keys change (people change emails).
- **Foreign key:** enforced pointer to another table's PK.

## 7.4 Rapid-fire differences (memorize the table)

| Question | Answer in one line |
|---|---|
| `DELETE` vs `TRUNCATE` vs `DROP` | rows-by-WHERE (logged, rollback-able) / all rows fast (resets identity) / the whole table, gone |
| `UNION` vs `UNION ALL` | dedupes (sort cost!) / keeps duplicates (faster — default to ALL) |
| `VARCHAR` vs `TEXT` (PG) | same perf; VARCHAR(n) just adds a length check |
| `WHERE` vs `HAVING` | rows before grouping / groups after |
| `RANK` vs `DENSE_RANK` | skips after ties / doesn't |
| PK vs UNIQUE | one per table, no NULLs / many allowed, NULLs allowed |
| `NUMERIC` vs `FLOAT` | exact (money) / approximate (never money) |
| clustered vs non-clustered index | table stored in index order / separate structure pointing at rows (PG has only the latter; `CLUSTER` is one-off) |

## 7.5 SQL vs NoSQL (the closer)
Relational: schema, JOINs, ACID — for related data needing consistency (orders!).
Document/KV (Mongo/Redis): flexible shape, horizontal-scale-first, weaker
cross-record guarantees — for hot ephemeral or unstructured data. Your project
literally uses both correctly → the soundbite is IP §2 (Postgres for truth,
Redis for hot state) — that's a better answer than any abstract comparison.

## 🎯 GATE 7 — move on when you can:
Answer in 30 seconds each, out loud: *What's an index and its trade-off? Walk me
through ACID. What's a dirty read? RANK vs DENSE_RANK? DELETE vs TRUNCATE? Why
did you pick Postgres over Mongo?*
- **Watch:** Gate Smashers → Keys · Indexing · ACID · Transactions &
  Concurrency · Isolation levels.

---
---

# LEVEL 8 — Classic interview patterns (ongoing reps)

The recurring puzzles interviewers reuse. Recognize the pattern → apply the
template. Just like CP: **patterns, not memorization** — solve "Nth-highest"
once properly and you own the whole family.

| Pattern | Template |
|---|---|
| **Nth-highest value** | `DENSE_RANK() OVER (ORDER BY v DESC)` → `= N` (or the `OFFSET N-1 LIMIT 1` + DISTINCT trick — know both) |
| **Find duplicates** | `GROUP BY col HAVING COUNT(*) > 1` |
| **Top-N per group** | Level 5 pattern 1 — the most-asked question in SQL |
| **Rows with no match** | anti-join: `LEFT JOIN … IS NULL` or `NOT EXISTS` |
| **Consecutive rows / streaks** | `LAG`, or the row-number-difference trick (`date - ROW_NUMBER() day-interval` groups a streak) |
| **Department with max X** | top-N per group again, N=1 |
| **Day-over-day change** | `v - LAG(v) OVER (ORDER BY day)` |
| **Deduplicate keeping newest** | `ROW_NUMBER() OVER (PARTITION BY key ORDER BY created_at DESC)` → keep `rn = 1` |

**Practice:** finish LeetCode SQL 50 completely → DataLemur / StrataScratch
medium+ (real company questions) → LeetCode "Database" tagged hards if you're
cruising.

---

# FINAL CHECK — SQL-interview ready when all of these are automatic

1. Top-3 orders by value **per status** (window + CTE filter)
2. Riders with **more than 5** orders today (`GROUP BY` + `HAVING`)
3. **2nd-highest** order value — twice: window AND correlated subquery
4. Orders **with no assigned rider** — twice: anti-join AND `NOT EXISTS`
5. **Running total** of order value by day
6. Explain out loud: execution order · NULL three-valued logic ·
   ON-vs-WHERE on LEFT JOIN · NOT IN + NULL · RANK vs DENSE_RANK ·
   WHERE vs HAVING · index trade-off · ACID

Re-run this list every weekend. When it's all reflex, SQL is done — move to
[Backend_Interview_Zero_to_Master.md](Backend_Interview_Zero_to_Master.md)
Level 2 (it continues exactly where Level 7 here points), and keep 2–3
LeetCode SQL problems per week as maintenance reps.
