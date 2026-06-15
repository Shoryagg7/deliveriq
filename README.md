# DeliverIQ

> Scalable order dispatch API with priority queuing, geohash-based
> rider matching, and token-bucket rate limiting.
> Built with FastAPI · PostgreSQL · Redis · Docker.

**What makes it different:** fairness-aware dispatch — within a bounded distance
band it balances rider earnings, not just ETA, reframing greedy-nearest as a
constrained assignment problem.

## Architecture

```mermaid
flowchart TD
    Client["Client<br/>POST /orders"]
    Gateway["Gateway<br/>Rate limit + JWT"]
    API["FastAPI service<br/>Routers, validation"]
    Dispatch["Dispatch<br/>Priority queue · O(log n)"]
    Match["Rider matching<br/>Geohash + fairness band"]
    Kafka["Kafka producer<br/>Emits order events"]

    Redis[("Redis<br/>Token bucket · geo · counts")]
    Postgres[("PostgreSQL<br/>Orders · riders")]
    Obs["Prometheus + Grafana<br/>Scrapes /metrics"]

    Notif["Notification<br/>Push, SMS"]
    Analytics["Analytics<br/>Order metrics"]
    Audit["Audit log<br/>Durable trail"]

    Client --> Gateway --> API --> Dispatch --> Match --> Kafka
    Gateway -.-> Redis
    Match -.-> Redis
    API -.-> Postgres
    API -.-> Obs
    Kafka --> Notif
    Kafka --> Analytics
    Kafka --> Audit

    classDef algo fill:#EEEDFE,stroke:#534AB7,color:#26215C;
    classDef store fill:#E1F5EE,stroke:#0F6E56,color:#04342C;
    class Dispatch,Match algo;
    class Redis,Postgres store;
```

## Learning Plan
Following a structured 45-day roadmap → [View Plan](docs/PLAN.md)

## Stack
- Python · FastAPI
- PostgreSQL · SQLAlchemy
- Redis
- Docker + docker compose
