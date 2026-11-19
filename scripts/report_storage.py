from psycopg.types.json import Jsonb


def save_pending_report(
    connection,
    player_id,
    team_id,
    season_id,
    snapshot_date,
    model_name,
    report_data,
):
    # Check the main report fields
    if report_data.get("player_id") != player_id:
        raise ValueError("Player ID does not match.")

    if report_data.get("snapshot_date") != str(snapshot_date):
        raise ValueError("Snapshot date does not match.")

    if not report_data.get("monitoring_status"):
        raise ValueError("Monitoring status is missing.")

    if not str(report_data.get("analysis", "")).strip():
        raise ValueError("Report analysis is missing.")

    with connection.cursor() as cursor:

        # Check goals and assists against PostgreSQL
        cursor.execute(
            """

SELECT goals, assists
FROM player_stat_observations
WHERE player_id = %s
  AND team_id = %s
  AND season_id = %s
  AND snapshot_date = %s
  AND data_status = 'COMPLETE'
  AND goals IS NOT NULL
  AND assists IS NOT NULL

            """,
            (player_id, team_id, season_id, snapshot_date),
        )

        source = cursor.fetchone()

        if source is None:
            raise ValueError("Matching source statistics not found.")

        if (
            report_data.get("goals"),
            report_data.get("assists"),
        ) != source:
            raise ValueError("Report statistics do not match database.")

        # Save report for human review
        cursor.execute(
            """
            INSERT INTO ai_reports (
                player_id,
                team_id,
                season_id,
                snapshot_date,
                model_name,
                report_data,
                validation_status,
                review_status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, 'PASS', 'PENDING'
            )
            RETURNING report_id
            """,
            (
                player_id,
                team_id,
                season_id,
                snapshot_date,
                model_name,
                Jsonb(report_data),
            ),
        )

        report_id = cursor.fetchone()[0]

    return report_id