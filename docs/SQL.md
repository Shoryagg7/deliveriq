# SQL Interview Prep — 8-Session Sprint

> **Framing:** SQL is the *language*; PostgreSQL is just where you run it.
> You're learning SQL. Run every query against your **own DeliverIQ tables**
> (orders, riders) once they exist (Day 10–11) — practicing on a schema you
> built makes it stick *and* gives you interview talking points.

**How to use this:** one session/day alongside the DeliverIQ build, or batch it.
Watch the linked video for the concept, then grind the practice set. Don't just
watch — **the reps in the practice platform are where the learning happens.**

**Practice platforms (pick one as your main grind):**
- 🥇 [LeetCode — Top SQL 50](https://leetcode.com/studyplan/top-sql-50/) — curated, ordered, CP-style. **Best fit for you.**
- [DataLemur](https://datalemur.com) — real company SQL questions (Nick Singh), interview-focused.
- [StrataScratch](https://www.stratascratch.com) — Uber/Airbnb/Netflix real questions.
- [HackerRank SQL](https://www.hackerrank.com/domains/sql) — large free question bank.

---

## Session 0 — THEORY DAY (the "explain X" questions)

### 🎯 Goal
Be able to *explain*, not query: how databases work under the hood. These are the
conceptual questions ("what's an index?", "explain ACID") that come in round 1.

### 🎥 Watch — [Gate Smashers · DBMS Complete Playlist](https://www.youtube.com/gatesmashers)
Watch only these topics (find them by lecture title in the DBMS playlist):
- **Normalization** (1NF → BCNF) — [normalization playlist](https://www.youtube.com/playlist?list=PLjgyGylma3IFNC7sNZOSbwGQPK_MYtCFW)
- **Keys** — primary, foreign, candidate, composite
- **Indexing** — B-tree / B+-tree, why an index turns O(n) scan into O(log n) lookup
- **ACID properties** + **[Transactions & Concurrency](https://www.youtube.com/watch?v=t5hsV9lC1rU)**
- **Isolation levels** — read uncommitted → serializable; dirty/phantom reads

### ✅ Done when
You can answer out loud, in 30s each: *What's an index and what's the trade-off?*
*What does ACID stand for?* *Why normalize?* *What's a dirty read?*

> **C++ bridge:** an index is a `std::map`/B-tree over a column — O(log n) lookup
> instead of scanning the whole table. The trade-off (slower writes, extra space)
> is the same one you weigh choosing a data structure in CP.

---

## Cluster 1 — SELECT · WHERE · ORDER BY · LIMIT

### 🎯 Goal
Pull and filter rows. The foundation everything else builds on.

### 🎥 Watch — [freeCodeCamp · SQL Full Course (Mike Dane)](https://www.youtube.com/playlist?list=PL-7OvuNicwAsTJLTE6Y-xVBOp_Fw2MFwE)
Sections: Basic Queries, Wildcards (`LIKE`), `ORDER BY`. *(~30 min)*

### ⌨️ Practice
LeetCode SQL 50 → the "Select" + "Basic Joins" intro problems (first ~8).

### 🔗 DeliverIQ tie
`SELECT * FROM orders WHERE status = 'PENDING' ORDER BY value DESC LIMIT 5;`

---

## Cluster 2 — Aggregates · GROUP BY · HAVING

### 🎯 Goal
Collapse many rows into summaries. `COUNT/SUM/AVG/MIN/MAX`, grouping, and
filtering *groups* with `HAVING` (vs filtering *rows* with `WHERE`).

### 🎥 Watch
freeCodeCamp course → Functions + Aggregation sections.
*(Gate Smashers also has a dedicated "SQL Aggregate Functions" lecture.)*

### ⌨️ Practice
LeetCode SQL 50 → "Sorting & Grouping" section.

### 🔗 DeliverIQ tie
`SELECT status, COUNT(*) FROM orders GROUP BY status HAVING COUNT(*) > 1;`

### 💡 Interview trap
`WHERE` filters **before** grouping; `HAVING` filters **after**. Mixing them up
is the #1 beginner mistake — know exactly which runs when.

---

## Cluster 3 — JOINs (inner · left · self)

### 🎯 Goal
Combine tables. Inner vs left (and when rows go missing), plus the self-join.

### 🎥 Watch
freeCodeCamp course → Joins section.
*(Gate Smashers "Difference between Joins, Nested Subquery and Correlated Subquery" is gold for placements.)*

### ⌨️ Practice
LeetCode SQL 50 → "Basic Joins" section (do all).

### 🔗 DeliverIQ tie
Join `orders` to `riders` on the assigned rider to list each order with its
rider's name. **Self-join example:** riders in the same geohash cell.

### 💡 Interview trap
"Why is my LEFT JOIN dropping rows?" — usually a `WHERE` on the right table that
should've been a condition inside the `ON`. Classic gotcha; expect it.

---

## Cluster 4 — Subqueries (incl. correlated)

### 🎯 Goal
Queries inside queries. Scalar subqueries, `IN`/`NOT IN`/`EXISTS`, and the
**correlated** subquery (re-runs per outer row).

### 🎥 Watch
Gate Smashers DBMS playlist → "Correlated Subquery in SQL with Example"
+ "EXISTS and NOT EXISTS" lectures.

### ⌨️ Practice
LeetCode SQL 50 → "Subqueries" section.

### 💡 Interview trap
`NOT IN` breaks silently if the subquery returns a `NULL`. `NOT EXISTS` doesn't.
Knowing this one distinction signals real depth.

---

## Cluster 5 — Window Functions ⭐ THE BIG ONE

### 🎯 Goal
The single most-asked advanced SQL topic at Uber/Razorpay/PhonePe-tier companies.
`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG/LEAD`, running totals, **top-N per group**.
**Over-invest here** — this is where candidates win or lose the SQL round.

### 🎥 Watch (do both)
- [Understand SQL Window Functions w/ Real-World Examples](https://www.youtube.com/watch?v=ZJGp6KtuTZQ)
- [Master Window Functions (Beginner → Pro) · Intellipaat](https://www.youtube.com/watch?v=C3ECf4kj4W8)

### ⌨️ Practice
- LeetCode SQL 50 → "Advanced Window Function" problems
- [practicewindowfunctions.com](https://www.practicewindowfunctions.com) — 75+ dedicated drills

### 🧠 The 4 patterns that cover most questions
1. **Top-N per group** — `ROW_NUMBER() OVER (PARTITION BY g ORDER BY x DESC)` → keep `= 1`
2. **Running total** — `SUM(x) OVER (ORDER BY date)`
3. **Row-vs-previous** — `LAG(x) OVER (ORDER BY date)` (streaks, day-over-day change)
4. **Ranking w/ ties** — `RANK` vs `DENSE_RANK` (know the difference cold)

### 💡 Interview trap
You **cannot** put a window function in a `WHERE` (it runs after). Wrap it in a
CTE/subquery and filter on the alias outside. This exact gotcha is a frequent test.

---

## Cluster 6 — CTEs (`WITH`) + Recursive

### 🎯 Goal
Name and stack subqueries for readable, multi-step queries. Plus recursive CTEs
for hierarchies (org charts, category trees).

### 🎥 Watch
freeCodeCamp course → CTE section *(or search "SQL CTE explained" on the channel)*.

### ⌨️ Practice
Re-solve 2–3 of your gnarliest Cluster-5 window problems using a CTE — same answer,
far more readable. That refactor *is* the lesson.

### 💡 Why interviewers love it
A clean `WITH` chain shows you can decompose a problem — the SQL version of
breaking a CP problem into subproblems. Readability scores points.

---

## Cluster 7 — Classic Patterns (the "named" questions)

### 🎯 Goal
The recurring puzzles interviewers reuse. Recognize the pattern → apply the template.

### 🎯 The hit list
- **Nth-highest salary/value** — Gate Smashers has a dedicated "Find Nth Highest Salary" lecture
- **Find duplicates** — `GROUP BY ... HAVING COUNT(*) > 1`
- **Second-highest per group** — window function, `RANK() = 2`
- **Consecutive rows / streaks** — `LAG`/`LEAD` or row-number diff trick
- **Department/category with max X** — top-N per group again

### ⌨️ Practice
LeetCode SQL 50 → remaining problems + tagged "Database" hard problems.

### 💡 Mindset
Just like CP: these are **patterns, not memorization**. Once you've solved
"Nth-highest" once, you own the whole family. Build your template, reuse it.

---

## Final check — can you do these cold?
1. Top-3 orders by value **per status** (window function)
2. Riders with **more than 5** orders today (`GROUP BY` + `HAVING`)
3. **2nd-highest** order value (window or correlated subquery — both)
4. Orders **with no assigned rider** (`LEFT JOIN ... IS NULL` or `NOT EXISTS`)
5. **Running total** of order value by day

If all five are automatic, you're SQL-interview ready. Then it's just steady reps
on LeetCode SQL 50 to stay sharp.
