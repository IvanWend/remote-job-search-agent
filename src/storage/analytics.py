import argparse
import logging
import os
from typing import NamedTuple

import psycopg
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class SkillCount(NamedTuple):
    skill: str
    roles: int
    postings: int


class CurrencySalary(NamedTuple):
    currency: str | None
    n: int
    median_max_monthly: int | None


class SenioritySalary(NamedTuple):
    seniority: str
    roles: int
    with_salary: int
    median_max_monthly: int | None


SKILL_FREQUENCY_SQL = """
SELECT unnest(stack) AS skill,
       count(*) AS roles,
       count(DISTINCT raw_posting_id) AS postings
FROM structured_postings
GROUP BY 1
ORDER BY roles DESC, skill
LIMIT %(limit)s
"""

SALARY_BY_CURRENCY_SQL = """
SELECT salary_currency,
       count(*) AS n,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY salary_max)::int AS median_max_monthly
FROM structured_postings
WHERE salary_max IS NOT NULL
GROUP BY 1
ORDER BY n DESC, salary_currency
"""

# The currency filter is not optional: percentile_cont over a mixed-currency
# list returns a midpoint that is neither currency (mid = 49 RUB + 41 USD landed
# at 80,500/mo, above senior's USD median). median_max ignores NULL salary_max,
# so with_salary still shows coverage even though salary_max IS NOT NULL is absent.
SALARY_BY_SENIORITY_SQL = """
SELECT seniority,
       count(*) AS roles,
       count(salary_max) AS with_salary,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY salary_max)::int AS median_max_monthly
FROM structured_postings
WHERE salary_currency = %(currency)s
GROUP BY seniority
ORDER BY median_max_monthly DESC NULLS LAST, seniority
"""


def skill_frequency(conn, limit: int = 20) -> list[SkillCount]:
    with conn.cursor() as cur:
        cur.execute(SKILL_FREQUENCY_SQL, {"limit": limit})
        return [SkillCount(*row) for row in cur.fetchall()]


def salary_by_currency(conn) -> list[CurrencySalary]:
    with conn.cursor() as cur:
        cur.execute(SALARY_BY_CURRENCY_SQL)
        return [CurrencySalary(*row) for row in cur.fetchall()]


def salary_by_seniority(conn, currency: str = "USD") -> list[SenioritySalary]:
    with conn.cursor() as cur:
        cur.execute(SALARY_BY_SENIORITY_SQL, {"currency": currency})
        return [SenioritySalary(*row) for row in cur.fetchall()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analytics over the structured corpus")
    parser.add_argument("--limit", type=int, default=20, help="Top-N skills to show")
    parser.add_argument("--currency", default="USD", help="Currency for the seniority split")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    args = parse_args()

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        logger.info("=== skill frequency (roles vs postings) ===")
        for s in skill_frequency(conn, args.limit):
            logger.info("%-16s roles=%-4d postings=%d", s.skill, s.roles, s.postings)

        logger.info("=== salary by currency (monthly median of salary_max) ===")
        for c in salary_by_currency(conn):
            logger.info(
                "%-8s n=%-4d median_max_monthly=%s",
                c.currency or "(null)",
                c.n,
                c.median_max_monthly,
            )

        logger.info("=== salary by seniority (%s, monthly median of salary_max) ===", args.currency)
        for r in salary_by_seniority(conn, args.currency):
            logger.info(
                "%-8s roles=%-4d with_salary=%-4d median_max_monthly=%s",
                r.seniority,
                r.roles,
                r.with_salary,
                r.median_max_monthly,
            )


if __name__ == "__main__":
    main()
