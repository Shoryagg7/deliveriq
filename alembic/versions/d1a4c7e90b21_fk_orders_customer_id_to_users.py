"""orders.customer_id -> users.id foreign key

Closes the last Tier-1 ownership gap. Since the auth hardening, customer_id is
derived from the verified token, so the handler already guarantees it points at
a real user. This makes the DATABASE guarantee it too: application-level
invariants get bypassed by scripts, fixtures and future endpoints, constraints
do not.

ON DELETE RESTRICT rather than CASCADE, deliberately: deleting a customer must
not silently vaporise their order history. Orders are business records; the
delete should fail loudly and force an explicit decision.

Revision ID: d1a4c7e90b21
Revises: 3ad810b73767
"""

import sqlalchemy as sa

from alembic import op

revision = "d1a4c7e90b21"
down_revision = "3ad810b73767"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Pre-existing rows can reference customer ids that never were users — the
    # old API took customer_id from the request body, and seed scripts used
    # random integers. The constraint cannot be added while they exist.
    #
    # These are demo rows with no owner and no way to recover one, so they are
    # deleted. Stated plainly rather than hidden: on a real system this step
    # would be a data-migration decision, not a DELETE in a schema migration.
    op.execute(
        """
        DELETE FROM orders
        WHERE customer_id NOT IN (SELECT id FROM users)
        """
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_foreign_key(
        "fk_orders_customer_id_users",
        "orders",
        "users",
        ["customer_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_orders_customer_id_users", "orders", type_="foreignkey")
    op.drop_index("ix_orders_customer_id", table_name="orders")
