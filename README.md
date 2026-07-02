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

    subgraph MW["FastAPI middleware chain (per request)"]
        ReqID["request_id<br/>(outermost, contextvars)"]
        Idem["Idempotency<br/>(POST, cached response)"]
        RL["Rate limit<br/>(token bucket, atomic Lua)"]
    end

    subgraph REPLICAS["API replicas (--scale api=3)"]
        API["FastAPI service<br/>Routers · validation · JWT dep (authz)"]
        Dispatch["Dispatch<br/>Priority heap + aging · O(log n)"]
        Match["Rider matching<br/>Geohash + fairness band"]
    end

    Kafka["Kafka producer<br/>order.dispatched (config-driven bootstrap)"]
    Redis[("Redis<br/>Token bucket · geo index · orders_today · idempotency")]
    Postgres[("PostgreSQL<br/>orders · riders · users")]
    Obs["Prometheus + Grafana<br/>scrapes /metrics"]

    Notif["Notifications<br/>consumer group"]
    Analytics["Analytics<br/>consumer group → DB"]
    Audit["Audit log<br/>consumer group → file"]

    Client --> ReqID --> Idem --> RL --> API
    API --> Dispatch
    Dispatch -->|"claim: SELECT … FOR UPDATE SKIP LOCKED"| Postgres
    Dispatch --> Match
    Match -.-> Redis
    Dispatch -->|"after db.commit"| Kafka
    RL -.-> Redis
    Idem -.-> Redis
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
##
And for SQL [View Plan](docs/SQL.md)
##
And for Interview Notes [Notes](docs/Interview_prep.md)
##
And for Resources (youtube links or official docs) [resources](docs/All_Resources_in_One_Place.md)

## Stack
- Python · FastAPI
- PostgreSQL · SQLAlchemy
- Redis
- Docker + docker compose
