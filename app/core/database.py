from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Pool sized EXPLICITLY (G08). The default is 5 + 10 overflow, which is not what
# the capacity arithmetic in the docs assumes — and an undocumented default is
# a number nobody can reason about at 3am.
#
# pool_pre_ping: issue a cheap SELECT 1 before handing a connection out. Without
# it, every Postgres restart hands out dead connections until each one is
# individually discovered by failing a real query — a self-inflicted error spike
# after routine maintenance. The ping costs a round trip; the alternative costs
# an incident.
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=settings.db_pool_recycle,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency: one DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
