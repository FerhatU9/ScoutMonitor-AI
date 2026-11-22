"""Database integration tests for an isolated CI PostgreSQL instance.

Disabled by default. Never point these tests at a personal development database.
"""

import os
import unittest
from datetime import date

import psycopg
from psycopg import errors
from sqlalchemy.engine import make_url

from scripts.report_storage import save_pending_report
from scripts.review_actions import review_report

TEST_DATABASE = "scoutmonitor_ci"
TEST_PLAYER_ID = 99999901


@unittest.skipUnless(
    os.getenv("SCOUTMONITOR_RUN_DB_TESTS") == "1",
    "Database integration tests run only in an isolated CI environment",
)
class TestDatabaseIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.getenv("SCOUTMONITOR_DATABASE_URL", "")
        if not url:
            raise RuntimeError("CI database connection is missing")
        settings = make_url(url)
        if settings.database != TEST_DATABASE:
            raise RuntimeError(
                "Integration tests refuse to connect to any database except scoutmonitor_ci"
            )
        cls.settings = settings

    def setUp(self):
        s = self.settings
        self.connection = psycopg.connect(
            host=s.host, port=s.port, dbname=s.database,
            user=s.username, password=s.password,
        )
        # Every test runs inside one transaction, rolled back in tearDown.
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO players (player_id, name, team_id) VALUES (%s, %s, %s)",
                (TEST_PLAYER_ID, "Fictional CI Player", 85),
            )
            cursor.execute(
                """INSERT INTO player_stat_observations
                   (player_id, team_id, season_id, snapshot_date, goals, assists, data_status)
                   VALUES (%s, 85, 27897, %s, 2, 1, 'COMPLETE')""",
                (TEST_PLAYER_ID, date(2026, 11, 16)),
            )

    def tearDown(self):
        self.connection.rollback()
        self.connection.close()

    def _report(self):
        return {
            "player_id": TEST_PLAYER_ID,
            "snapshot_date": "2026-11-16",
            "goals": 2,
            "assists": 1,
            "monitoring_status": "WAITING_FOR_HISTORY",
            "analysis": "Fictional training data; historical trend not established.",
        }

    def _save_report(self):
        return save_pending_report(
            self.connection, TEST_PLAYER_ID, 85, 27897,
            date(2026, 11, 16), "test-model", self._report(),
        )

    def test_initial_schema_and_revision(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT version_num FROM alembic_version")
            self.assertEqual(cursor.fetchone()[0], "0001")
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name IN "
                "('players', 'player_season_stats', 'player_stat_observations', "
                "'performance_alerts', 'ai_reports')"
            )
            self.assertEqual(cursor.fetchone()[0], 5)

    def test_missing_stat_remains_null(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO player_stat_observations
                   (player_id, team_id, season_id, snapshot_date, goals, assists, data_status)
                   VALUES (%s, 85, 27897, %s, 1, NULL, 'PARTIAL')""",
                (TEST_PLAYER_ID, date(2026, 11, 17)),
            )
            cursor.execute(
                "SELECT assists FROM player_stat_observations "
                "WHERE player_id = %s AND snapshot_date = %s",
                (TEST_PLAYER_ID, date(2026, 11, 17)),
            )
            self.assertIsNone(cursor.fetchone()[0])

    def test_pending_report_stored_with_validation(self):
        report_id = self._save_report()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT review_status, validation_status, report_data->>'analysis' "
                "FROM ai_reports WHERE report_id = %s", (report_id,),
            )
            status, validation, analysis = cursor.fetchone()
        self.assertEqual((status, validation), ("PENDING", "PASS"))
        self.assertIn("Fictional", analysis)

    def test_review_approval_and_prevent_second_review(self):
        report_id = self._save_report()
        result = review_report(
            self.connection, report_id, "APPROVED", "CI Reviewer",
        )
        self.assertEqual(result["review_status"], "APPROVED")
        with self.assertRaisesRegex(ValueError, "Review not allowed"):
            review_report(self.connection, report_id, "REJECTED", "CI Reviewer", "Too late")

    def test_reject_missing_reason(self):
        report_id = self._save_report()
        with self.assertRaisesRegex(ValueError, "rejection reason"):
            review_report(self.connection, report_id, "REJECTED", "CI Reviewer")

    def test_invalid_report_facts_rejected_before_insert(self):
        fake = self._report()
        fake["assists"] = 99
        with self.assertRaisesRegex(ValueError, "do not match database"):
            save_pending_report(
                self.connection, TEST_PLAYER_ID, 85, 27897,
                date(2026, 11, 16), "test-model", fake,
            )
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ai_reports")
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_duplicate_snapshot_is_rejected(self):
        with self.assertRaises(errors.UniqueViolation):
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO player_stat_observations
                       (player_id, team_id, season_id, snapshot_date, goals, assists, data_status)
                       VALUES (%s, 85, 27897, %s, 2, 1, 'COMPLETE')""",
                    (TEST_PLAYER_ID, date(2026, 11, 16)),
                )

    def test_approved_report_must_pass_validation(self):
        with self.assertRaises(errors.CheckViolation):
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO ai_reports
                       (player_id, team_id, season_id, snapshot_date, model_name,
                        report_data, validation_status, review_status, reviewer_name, reviewed_at)
                       VALUES (%s, 85, 27897, %s, 'test-model', '{}'::jsonb,
                               'REVIEW_REQUIRED', 'APPROVED', 'CI Reviewer', CURRENT_TIMESTAMP)""",
                    (TEST_PLAYER_ID, date(2026, 11, 16)),
                )


if __name__ == "__main__":
    unittest.main()
