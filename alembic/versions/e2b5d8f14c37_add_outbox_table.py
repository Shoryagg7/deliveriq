"""transactional outbox

Closes the dual-write hole: dispatch used to commit the order and then publish
to Kafka, so a crash between the two lost the event permanently.

Revision ID: e2b5d8f14c37
Revises: d1a4c7e90b21
"""

import sqlalchemy as sa

from alembic import op

revision = "e2b5d8f14c37"
down_revision = "d1a4c7e90b21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outbox_id"), "outbox", ["id"])
    # Partial index — the relay only ever selects unpublished rows, so there is
    # no reader for the published ones and no reason to index them forever.
    op.create_index(
        "ix_outbox_unpublished",
        "outbox",
        ["created_at"],
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_unpublished", table_name="outbox")
    op.drop_index(op.f("ix_outbox_id"), table_name="outbox")
    op.drop_table("outbox")
