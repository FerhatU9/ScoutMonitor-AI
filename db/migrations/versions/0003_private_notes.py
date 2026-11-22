"""Organization-owned private scouting notes with PostgreSQL row security.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_scouting_notes",
        sa.Column("note_id", sa.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.org_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("player_id", sa.BigInteger(),
                  sa.ForeignKey("players.player_id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("author_user_id", sa.BigInteger(),
                  sa.ForeignKey("identity_users.user_id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("length(btrim(title)) BETWEEN 1 AND 150",
                           name="scouting_notes_valid_title"),
        sa.CheckConstraint("length(btrim(body)) BETWEEN 1 AND 5000",
                           name="scouting_notes_valid_body"),
    )
    op.create_index("ix_scouting_notes_org_created", "organization_scouting_notes",
                    ["org_id", "created_at", "note_id"])

    # Organization and membership are checked *again* in PostgreSQL, not just
    # in the API. A separate non-superuser application role must be used.
    op.execute("ALTER TABLE organization_scouting_notes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE organization_scouting_notes FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY scouting_notes_member_read
        ON organization_scouting_notes
        FOR SELECT
        USING (
            org_id = NULLIF(current_setting('scoutmonitor.org_id', true), '')::uuid
            AND EXISTS (
                SELECT 1 FROM organization_memberships m
                JOIN organizations o ON o.org_id = m.org_id
                WHERE m.org_id = organization_scouting_notes.org_id
                  AND m.user_id = NULLIF(current_setting('scoutmonitor.user_id', true), '')::bigint
                  AND m.active AND o.active
            )
        )
    """)
    op.execute("""
        CREATE POLICY scouting_notes_author_insert
        ON organization_scouting_notes
        FOR INSERT
        WITH CHECK (
            org_id = NULLIF(current_setting('scoutmonitor.org_id', true), '')::uuid
            AND author_user_id = NULLIF(current_setting('scoutmonitor.user_id', true), '')::bigint
            AND EXISTS (
                SELECT 1 FROM organization_memberships m
                JOIN organizations o ON o.org_id = m.org_id
                WHERE m.org_id = organization_scouting_notes.org_id
                  AND m.user_id = organization_scouting_notes.author_user_id
                  AND m.role IN ('owner', 'admin', 'scout')
                  AND m.active AND o.active
            )
        )
    """)


def downgrade() -> None:
    raise RuntimeError(
        "Automatic downgrade disabled: private scouting notes must not be dropped."
    )
