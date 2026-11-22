"""Create the existing ScoutMonitor AI application schema on a NEW database.

Revision ID: 0001
Revises:
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("player_id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("team_id", sa.BigInteger()),
        sa.Column("jersey_number", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "player_season_stats",
        sa.Column("player_id", sa.BigInteger(), sa.ForeignKey("players.player_id"), nullable=False),
        sa.Column("team_id", sa.BigInteger(), nullable=False),
        sa.Column("season_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("goals", sa.Integer()),
        sa.Column("assists", sa.Integer()),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("player_id", "team_id", "season_id", "snapshot_date", name="player_season_stats_pkey"),
        sa.CheckConstraint("goals >= 0", name="player_season_stats_goals_check"),
        sa.CheckConstraint("assists >= 0", name="player_season_stats_assists_check"),
    )

    op.create_table(
        "player_stat_observations",
        sa.Column("player_id", sa.BigInteger(), sa.ForeignKey("players.player_id"), nullable=False),
        sa.Column("team_id", sa.BigInteger(), nullable=False),
        sa.Column("season_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("goals", sa.Integer()),
        sa.Column("assists", sa.Integer()),
        sa.Column("data_status", sa.Text(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("player_id", "team_id", "season_id", "snapshot_date", name="player_stat_observations_pkey"),
        sa.CheckConstraint("goals >= 0", name="player_stat_observations_goals_check"),
        sa.CheckConstraint("assists >= 0", name="player_stat_observations_assists_check"),
        sa.CheckConstraint("data_status IN ('COMPLETE', 'PARTIAL', 'NOT_REPORTED')", name="player_stat_observations_data_status_check"),
    )

    op.create_table(
        "performance_alerts",
        sa.Column("alert_id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("player_id", sa.BigInteger(), sa.ForeignKey("players.player_id"), nullable=False),
        sa.Column("team_id", sa.BigInteger(), nullable=False),
        sa.Column("season_id", sa.BigInteger(), nullable=False),
        sa.Column("previous_snapshot_date", sa.Date(), nullable=False),
        sa.Column("current_snapshot_date", sa.Date(), nullable=False),
        sa.Column("goals_increase", sa.Integer(), nullable=False),
        sa.Column("assists_increase", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("goals_increase >= 0", name="performance_alerts_goals_increase_check"),
        sa.CheckConstraint("assists_increase >= 0", name="performance_alerts_assists_increase_check"),
        sa.CheckConstraint("goals_increase > 0 OR assists_increase > 0", name="positive_change"),
        sa.CheckConstraint("current_snapshot_date > previous_snapshot_date", name="valid_alert_dates"),
        sa.UniqueConstraint("player_id", "team_id", "season_id", "previous_snapshot_date", "current_snapshot_date", name="unique_performance_alert"),
    )

    op.create_table(
        "ai_reports",
        sa.Column("report_id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("player_id", sa.BigInteger(), sa.ForeignKey("players.player_id"), nullable=False),
        sa.Column("team_id", sa.BigInteger(), nullable=False),
        sa.Column("season_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("report_data", JSONB(), nullable=False),
        sa.Column("validation_status", sa.Text(), nullable=False),
        sa.Column("review_status", sa.Text(), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("reviewer_name", sa.Text()),
        sa.Column("review_notes", sa.Text()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("jsonb_typeof(report_data) = 'object'", name="ai_reports_report_data_check"),
        sa.CheckConstraint("review_status IN ('PENDING', 'APPROVED', 'REJECTED')", name="ai_reports_review_status_check"),
        sa.CheckConstraint("validation_status IN ('PASS', 'REVIEW_REQUIRED')", name="ai_reports_validation_status_check"),
        sa.CheckConstraint("review_status <> 'APPROVED' OR validation_status = 'PASS'", name="approved_only_if_valid"),
        sa.CheckConstraint(
            "(review_status = 'PENDING' AND reviewer_name IS NULL AND reviewed_at IS NULL) "
            "OR (review_status IN ('APPROVED', 'REJECTED') AND reviewer_name IS NOT NULL AND reviewed_at IS NOT NULL)",
            name="review_decision_complete",
        ),
    )
    op.create_index(
        "unique_player_snapshot_report",
        "ai_reports",
        ["player_id", "team_id", "season_id", "snapshot_date"],
        unique=True,
    )


def downgrade() -> None:
    # Dropping report and player tables could destroy records.
    raise RuntimeError(
        "Automatic schema downgrade is disabled to protect ScoutMonitor AI data. "
        "Restore a reviewed backup instead."
    )
