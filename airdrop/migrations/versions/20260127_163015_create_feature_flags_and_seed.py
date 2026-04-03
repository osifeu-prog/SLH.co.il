"""create feature_flags and seed AIRDROP_ENABLED

Revision ID: 20260127163015
Revises:
Create Date: 2026-01-27 16:30:15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260127163015"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feature_flags",
        sa.Column("key", sa.String(length=128), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO feature_flags (key, enabled, description)
            VALUES (:k, :e, :d)
            ON CONFLICT (key) DO UPDATE
              SET enabled = EXCLUDED.enabled,
                  description = EXCLUDED.description,
                  updated_at = now()
            """
        ).bindparams(
            k="AIRDROP_ENABLED",
            e=True,
            d="Global switch for airdrop requests",
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM feature_flags WHERE key = :k").bindparams(k="AIRDROP_ENABLED"))
    op.drop_table("feature_flags")
