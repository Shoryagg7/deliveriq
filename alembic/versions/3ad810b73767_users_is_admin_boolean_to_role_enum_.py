"""users: is_admin boolean to role enum plus rider link

Revision ID: 3ad810b73767
Revises: c7e7b85119bf
Create Date: 2026-07-30 16:12:06.325109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ad810b73767'
down_revision: Union[str, Sequence[str], None] = 'c7e7b85119bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """is_admin (boolean) -> role (customer|rider|ops), preserving existing admins.

    Hand-edited from the autogenerate, which had three defects:
      1. added `role` NOT NULL with no server_default — fails outright on any
         table that already has rows;
      2. dropped `is_admin` with no backfill — every existing admin would have
         been silently demoted to customer, an authorization regression that no
         test would catch because the column simply stops existing;
      3. the downgrade re-added is_admin NOT NULL with no default — same
         failure in reverse, so the migration was not actually reversible.
    """
    # 1. add nullable-with-default so existing rows are valid immediately
    op.add_column(
        "users",
        sa.Column("role", sa.String(), nullable=False, server_default="customer"),
    )
    # 2. BACKFILL before the source column disappears
    op.execute("UPDATE users SET role = 'ops' WHERE is_admin = true")

    op.add_column("users", sa.Column("rider_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)
    op.create_foreign_key(
        "fk_users_rider_id", "users", "riders", ["rider_id"], ["id"]
    )
    # 3. only now is is_admin redundant
    op.drop_column("users", "is_admin")


def downgrade() -> None:
    """Reverse, preserving ops users as admins."""
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.execute("UPDATE users SET is_admin = true WHERE role = 'ops'")
    op.drop_constraint("fk_users_rider_id", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_column("users", "rider_id")
    op.drop_column("users", "role")
