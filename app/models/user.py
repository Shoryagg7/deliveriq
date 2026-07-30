# app/models/user.py
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base
from app.core.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    # bcrypt hash, never the password. Named to make that unmistakable at every
    # call site — `user.password` would invite logging it.
    hashed_password = Column(String, nullable=False)
    # Role, not a boolean. `is_admin` can only express admin/not-admin, but the
    # actor guard on status transitions needs to tell a RIDER from a CUSTOMER —
    # two non-admin roles with completely different permissions.
    role = Column(String, default=UserRole.CUSTOMER.value, nullable=False, index=True)
    # Set for role=rider: which Rider row this login acts as. Without it "the
    # assigned rider may advance THEIR OWN order" is unenforceable — you'd know
    # the caller is a rider but not which one.
    rider_id = Column(Integer, ForeignKey("riders.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    @property
    def is_admin(self) -> bool:
        """Back-compat shim for callers that predate roles."""
        return self.role == UserRole.OPS.value
