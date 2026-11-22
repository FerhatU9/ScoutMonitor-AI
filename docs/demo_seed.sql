-- ScoutMonitor AI: fictional demonstration data
-- Based on docs/schema.sql (PostgreSQL 18 schema).
-- For the separate scoutmonitor_portfolio_test database ONLY.
-- No real players, API tokens, passwords, or AI-generated reports are included.
-- Safe to rerun: existing demonstration rows are left unchanged.
--
-- Example states:
--   Demo Player A: COMPLETE, with two historical snapshots
--   Demo Player B: PARTIAL (assists unknown)
--   Demo Player C: NOT_REPORTED (both statistics unknown)
--   Demo Player D: NOT_COLLECTED (no observation row exists)
--
-- Important: NULL means unknown/not reported, NOT zero.

BEGIN;

DO $$
BEGIN
    IF current_database() <> 'scoutmonitor_portfolio_test' THEN
        RAISE EXCEPTION
            'Demo seed cancelled: connected to %, expected scoutmonitor_portfolio_test',
            current_database();
    END IF;
END
$$;

-- All names below are fictional placeholders.
INSERT INTO public.players (player_id, name, team_id, jersey_number)
VALUES
    (990001, 'Demo Player A', 85, 11),
    (990002, 'Demo Player B', 85, 12),
    (990003, 'Demo Player C', 85, 13),
    (990004, 'Demo Player D', 85, 14)
ON CONFLICT (player_id) DO NOTHING;

-- The verified, complete snapshots used by the historical monitoring workflow.
INSERT INTO public.player_season_stats
    (player_id, team_id, season_id, snapshot_date, goals, assists)
VALUES
    (990001, 85, 27897, DATE '2026-11-15', 1, 1),
    (990001, 85, 27897, DATE '2026-11-16', 3, 2)
ON CONFLICT (player_id, team_id, season_id, snapshot_date) DO NOTHING;

-- Multi-player observations include missing values explicitly as NULL.
INSERT INTO public.player_stat_observations
    (player_id, team_id, season_id, snapshot_date, goals, assists, data_status)
VALUES
    (990001, 85, 27897, DATE '2026-11-15', 1, 1, 'COMPLETE'),
    (990001, 85, 27897, DATE '2026-11-16', 3, 2, 'COMPLETE'),
    (990002, 85, 27897, DATE '2026-11-16', 2, NULL, 'PARTIAL'),
    (990003, 85, 27897, DATE '2026-11-16', NULL, NULL, 'NOT_REPORTED')
ON CONFLICT (player_id, team_id, season_id, snapshot_date) DO NOTHING;

-- Demo Player D deliberately has no row in player_stat_observations.
-- The app should display NOT_COLLECTED when no observation is stored.
-- AI reports and performance alerts are intentionally not seeded.

COMMIT;

-- Verification: four fictional players should be returned. The fourth has
-- NULL observation fields, because NOT_COLLECTED is a derived UI state.
SELECT
    p.name,
    p.player_id,
    o.snapshot_date,
    o.goals,
    o.assists,
    COALESCE(o.data_status, 'NOT_COLLECTED') AS data_status
FROM public.players AS p
LEFT JOIN LATERAL (
    SELECT snapshot_date, goals, assists, data_status
    FROM public.player_stat_observations AS o
    WHERE o.player_id = p.player_id
      AND o.team_id = 85
      AND o.season_id = 27897
    ORDER BY o.snapshot_date DESC
    LIMIT 1
) AS o ON TRUE
WHERE p.player_id BETWEEN 990001 AND 990004
ORDER BY p.player_id;
