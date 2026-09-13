import logging
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Both upserts recompute the whole visible window every run: ON CONFLICT makes
# it idempotent, and the SELECT can only see the last 90 days, so months that
# have been purged are never re-inserted and their rollup rows freeze in place.
# The skill rollup carries roles AND postings so the stack fill-down inflation
# stays visible in the trend, same split as analytics.skill_frequency.
SKILL_ROLLUP_SQL = """
INSERT INTO monthly_skill_frequency (month, skill, roles, postings)
SELECT date_trunc('month', r.posted_at)::date,
       unnest(s.stack) AS skill,
       count(*) AS roles,
       count(DISTINCT s.raw_posting_id) AS postings
FROM structured_postings s
JOIN raw_postings r ON r.id = s.raw_posting_id
GROUP BY 1, 2
ON CONFLICT (month, skill) DO UPDATE
  SET roles = EXCLUDED.roles, postings = EXCLUDED.postings
"""

# Grouped by (month, currency) so percentiles never mix currencies. NULL
# currency is coalesced to a sentinel because NULLs in a PRIMARY KEY never
# conflict with each other — two NULL-currency rows for one month would both
# insert instead of upserting.
SALARY_ROLLUP_SQL = """
INSERT INTO monthly_salary (month, currency, n, median_min, median_max)
SELECT date_trunc('month', r.posted_at)::date,
       COALESCE(s.salary_currency, 'unknown'),
       count(*),
       percentile_cont(0.5) WITHIN GROUP (ORDER BY s.salary_min)::int,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY s.salary_max)::int
FROM structured_postings s
JOIN raw_postings r ON r.id = s.raw_posting_id
WHERE s.salary_max IS NOT NULL
GROUP BY 1, 2
ON CONFLICT (month, currency) DO UPDATE
  SET n = EXCLUDED.n, median_min = EXCLUDED.median_min, median_max = EXCLUDED.median_max
"""


def refresh(conn) -> None:
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(SKILL_ROLLUP_SQL)
        skill_rows = cur.rowcount
        cur.execute(SALARY_ROLLUP_SQL)
        salary_rows = cur.rowcount
    logger.info("Rollup upserted: %d skill rows, %d salary rows.", skill_rows, salary_rows)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        refresh(conn)


if __name__ == "__main__":
    main()
