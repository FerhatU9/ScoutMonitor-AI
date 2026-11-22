"""Organization identities and per-organization player watchlists.

Revision ID: 0002
Revises: 0001

This migration is forward-only and intended for Alembic-managed databases.
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("org_id", sa.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "identity_users",
        sa.Column("user_id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("issuer", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("issuer", "subject", name="unique_identity_subject"),
    )

    op.create_table(
        "organization_memberships",
        sa.Column("org_id", sa.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(),
                  sa.ForeignKey("identity_users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("org_id", "user_id", name="organization_memberships_pkey"),
        sa.CheckConstraint(
            "role IN ('owner', 'admin', 'scout', 'reviewer')",
            name="organization_memberships_role_check",
        ),
    )
    op.create_index(
        "ix_organization_memberships_user_id",
        "organization_memberships", ["user_id"],
    )

    op.create_table(
        "organization_watchlist",
        sa.Column("org_id", sa.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False),
        sa.Column("player_id", sa.BigInteger(),
                  sa.ForeignKey("players.player_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_by_user_id", sa.BigInteger(),
                  sa.ForeignKey("identity_users.user_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("org_id", "player_id", name="organization_watchlist_pkey"),
    )


def downgrade() -> None:
    raise RuntimeError(
        "Automatic downgrade is disabled to protect organization memberships "
        "and watchlist records. Use a reviewed backup and migration plan."
    )
