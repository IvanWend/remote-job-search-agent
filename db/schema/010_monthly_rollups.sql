-- 010_monthly_rollups.sql
-- Aggregates that outlive the 90-day purge. structured_postings only ever
-- holds the rolling window, so a refresh (rollups.py) upserts over whatever
-- is visible now; once a month's source rows are purged, its rollup row is
-- never touched again and stays as frozen history. No backfill, no "recompute
-- only recent months" logic — the SELECT physically cannot see aged-out rows.
--
-- month keys on date_trunc('month', posted_at), not thread_month: the purge
-- filters on posted_at, so rollup months and purge boundaries line up exactly.
--
-- Two tables, not one: skill frequency and salary have different dimensions,
-- and one wide table would leave half its columns NULL on every row.
--
-- Re-runnable: applying twice is a no-op.

BEGIN;

CREATE TABLE IF NOT EXISTS monthly_skill_frequency (
    month     DATE NOT NULL,
    skill     TEXT NOT NULL,
    roles     INT  NOT NULL,
    postings  INT  NOT NULL,
    PRIMARY KEY (month, skill)
);

CREATE TABLE IF NOT EXISTS monthly_salary (
    month      DATE NOT NULL,
    currency   TEXT NOT NULL,
    n          INT  NOT NULL,
    median_min INT,
    median_max INT,
    PRIMARY KEY (month, currency)
);

COMMIT;
