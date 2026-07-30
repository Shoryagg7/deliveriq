"""
Prometheus metrics.

Naming follows the convention Prometheus tooling expects:
  <namespace>_<subsystem>_<unit>_total  for counters
  ..._seconds                            for durations, ALWAYS base units

The label sets are deliberately small. Every distinct combination of label
values is a separate time series held in memory by both this process and
Prometheus, so a label with unbounded values (a raw URL path containing
/orders/1, /orders/2, ...) is the classic way to melt a metrics stack. Paths are
therefore recorded as the ROUTE TEMPLATE ("/orders/{order_id}"), which is
bounded by the number of routes.
"""

from prometheus_client import Counter, Gauge, Histogram

NAMESPACE = "deliveriq"

# --- HTTP ------------------------------------------------------------------
http_requests_total = Counter(
    f"{NAMESPACE}_http_requests_total",
    "HTTP requests by method, route template and status class.",
    ["method", "route", "status"],
)

http_request_duration_seconds = Histogram(
    f"{NAMESPACE}_http_request_duration_seconds",
    "HTTP request latency.",
    ["method", "route"],
    # Tuned to this API's shape, not the library default: dispatch does real DB
    # work under lock, so the interesting range is 10ms-1s. Buckets are
    # cumulative, and p99 can only ever be reported to the nearest bucket edge.
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# --- Domain: the things an on-call engineer would actually page on ---------
dispatch_total = Counter(
    f"{NAMESPACE}_dispatch_total",
    "Dispatch attempts by outcome.",
    ["outcome"],  # assigned | no_pending_orders | no_rider_available
)

dispatch_duration_seconds = Histogram(
    f"{NAMESPACE}_dispatch_duration_seconds",
    "Time spent in pick_next_order, including row locks.",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

kafka_events_published_total = Counter(
    f"{NAMESPACE}_kafka_events_published_total",
    "Events handed to the producer (enqueued, not necessarily acked).",
    ["topic"],
)

kafka_events_delivered_total = Counter(
    f"{NAMESPACE}_kafka_events_delivered_total",
    "Delivery-callback outcomes from the broker.",
    ["topic", "outcome"],  # delivered | failed
)

rate_limit_rejections_total = Counter(
    f"{NAMESPACE}_rate_limit_rejections_total",
    "Requests rejected with 429.",
)

idempotent_replays_total = Counter(
    f"{NAMESPACE}_idempotent_replays_total",
    "Requests served from the idempotency cache instead of re-executing.",
)

# --- Readiness -------------------------------------------------------------
# A Gauge, not a Counter: it reports current state, and 0/1 per dependency lets
# a single alert rule cover all of them ("any dependency down for 2m").
dependency_up = Gauge(
    f"{NAMESPACE}_dependency_up",
    "1 if the dependency answered its last readiness probe, else 0.",
    ["dependency"],  # postgres | redis | kafka
)
