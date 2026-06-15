# ─────────────────────────────────────────────
# PART 1: Lists and Dicts
# ─────────────────────────────────────────────

# This is your in-memory "database" for Days 8-10
# before you connect real PostgreSQL
orders = [
    {"id": 1, "value": 250, "status": "PENDING", "customer_id": 101},
    {"id": 2, "value": 800, "status": "DELIVERED", "customer_id": 102},
    {"id": 3, "value": 450, "status": "PENDING", "customer_id": 103},
    {"id": 4, "value": 1200, "status": "ASSIGNED", "customer_id": 101},
    {"id": 5, "value": 90, "status": "CANCELLED", "customer_id": 104},
]

# # --- Basic list operations ---
# print("=== LIST BASICS ===")
# print(len(orders))  # 5  — like v.size()
# print(orders[0])  # first element — like v[0]
# print(orders[-1])  # last element — no C++ equivalent, very useful
# print(orders[1:3])  # slicing: elements at index 1 and 2 — like subarray

# # --- Append and remove ---
# orders.append({"id": 6, "value": 300, "status": "PENDING", "customer_id": 105})
# print(f"After append: {len(orders)} orders")  # 6

# orders.pop()  # removes last — like v.pop_back()
# print(f"After pop: {len(orders)} orders")  # 5

# # --- Dict operations ---
# print("\n=== DICT BASICS ===")
# order = orders[0]
# print(order["value"])  # 250 — like mp["key"]
# print(order.get("tip", 0))  # 0 — safe get with default, no KeyError
# # like mp.count(k) ? mp[k] : default

# order["tip"] = 50  # add new key
# print(order)

# print("value" in order)  # True  — like mp.count("value")
# print("tip" in order)  # True
# print("zone" in order)  # False

# # dict.keys(), .values(), .items()
# print(list(order.keys()))
# print(list(order.values()))
# for key, val in order.items():  # like for (auto& [k,v] : mp)
#     print(f"  {key}: {val}")


# ─────────────────────────────────────────────
# PART 2: Comprehensions — Python's killer feature
# ─────────────────────────────────────────────

# print("\n=== LIST COMPREHENSIONS ===")
# # Syntax: [expression  for item in iterable  if condition]
# #          ^what to    ^loop                  ^filter
# #           keep

# # Get all pending order IDs
# # C++ equivalent:
# #   vector<int> pending_ids;
# #   for (auto& o : orders)
# #       if (o["status"] == "PENDING") pending_ids.push_back(o["id"]);

# pending_ids = [o["id"] for o in orders if o["status"] == "PENDING"]
# print(f"Pending IDs: {pending_ids}")           # [1, 3]

# # Get values of all pending orders
# pending_values = [o["value"] for o in orders if o["status"] == "PENDING"]
# print(f"Pending values: {pending_values}")     # [250, 450]

# # Transform: add priority score to every order
def calculate_priority(value: float, wait: int = 0) -> float:
    return value * 0.4 + wait * 0.6

# scored = [
#     {**o, "priority": calculate_priority(o["value"])}
#     for o in orders
# ]
# # {**o, "priority": ...} means: copy all keys from o, then add "priority"
# # C++ equivalent: structured binding + insert
# print(f"First scored order: {scored[0]}")


# print("\n=== DICT COMPREHENSIONS ===")
# # Build a lookup map: order_id → order value
# # C++ equivalent:
# #   unordered_map<int,float> order_values;
# #   for (auto& o : orders) order_values[o["id"]] = o["value"];
# order_values = {o["id"]: o["value"] for o in orders}
# print(f"Order values map: {order_values}")
# print(f"Value of order 3: {order_values[3]}")  # O(1) lookup

# # Build status groups: status → list of order IDs
# # This is groupBy — you'll use this pattern in analytics endpoints
# from collections import defaultdict  # noqa: E402

# by_status = defaultdict(list)
# for o in orders:
#     by_status[o["status"]].append(o["id"])
# print(f"By status: {dict(by_status)}")


# print("\n=== SET COMPREHENSIONS ===")
# # Get unique customer IDs who have pending orders
# # C++ equivalent: unordered_set<int>
# customers_with_pending = {o["customer_id"] for o in orders if o["status"] == "PENDING"}
# print(f"Customers with pending orders: {customers_with_pending}")

# # Set operations — useful for rider availability checks
# all_customers    = {o["customer_id"] for o in orders}
# active_customers = {o["customer_id"] for o in orders if o["status"] != "CANCELLED"}
# print(f"All: {all_customers}")
# print(f"Active: {active_customers}")
# print(f"Only cancelled: {all_customers - active_customers}")  # set difference

# ─────────────────────────────────────────────
# PART 3: Sorting + Aggregation + any/all
# ─────────────────────────────────────────────

print("\n=== SORTING ===")

# Sort by value ascending — like sort() with custom comparator
by_value_asc = sorted(orders, key=lambda o: o["value"])
print([f"{o['id']}: {o['value']}" for o in by_value_asc])
# Sort by value descending — most expensive first
by_value_desc = sorted(orders, key=lambda o: o["value"], reverse=True)
print([f"{o['id']}: {o['value']}" for o in by_value_desc])

# Sort by priority score (value × 0.4 + wait × 0.6)
# This is exactly what Redis sorted sets do automatically on Day 17
by_priority = sorted(orders,key=lambda o: calculate_priority(o["value"]),reverse=True)
print("By priority:")
print([f"{o['id']}: {calculate_priority(o['value'])}" for o in by_priority])
# lambda is an anonymous function — like C++ lambda:
# C++:    [](auto& o) { return o["value"]; }
# Python: lambda o: o["value"]

print("\n=== AGGREGATION ===")

total_value = sum(o["value"] for o in orders)
print(f"Total order value: ₹{total_value}")

pending_total = sum(o["value"] for o in orders if o["status"] == "PENDING")
print(f"Pending order value: ₹{pending_total}")

avg_value = total_value / len(orders)
print(f"Average order value: ₹{avg_value:.2f}")   # :.2f = 2 decimal places

max_order = max(orders, key=lambda o: o["value"])
min_order = min(orders, key=lambda o: o["value"])
print(max_order)
print(f"Highest value order: #{max_order['id']} (₹{max_order['value']})")
print(f"Lowest value order:  #{min_order['id']} (₹{min_order['value']})")

print("\n=== any() and all() ===")
# These are incredibly useful in API validation

# any() = true if AT LEAST ONE element satisfies condition
# C++: any_of(v.begin(), v.end(), predicate)
has_pending = any(o["status"] == "PENDING" for o in orders)
print(f"Any pending orders? {has_pending}")        # True

# all() = true if EVERY element satisfies condition
# C++: all_of(v.begin(), v.end(), predicate)
all_delivered = all(o["status"] == "DELIVERED" for o in orders)
print(f"All delivered? {all_delivered}")           # False

# Practical use: validate a batch of orders before inserting
batch = [
    {"id": 10, "value": 300, "status": "PENDING", "customer_id": 201},
    {"id": 11, "value": 0,   "status": "PENDING", "customer_id": 202},  # invalid!
]
all_valid = all(o["value"] > 0 for o in batch)
print(all_valid)                                   # False
print(f"Batch all valid? {all_valid}")             # False — catches the zero-value order
