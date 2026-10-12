import argparse
import logging
import os

import psycopg
from dotenv import load_dotenv

from jobmarket_agent.ingestion.retention import CUT_SOURCES, WINDOW_DAYS

load_dotenv()

logger = logging.getLogger(__name__)

COUNT_SQL = """
SELECT source,
       count(*)                                                    AS total,
       count(*) FILTER (WHERE source = ANY(%(cut)s))               AS cut_source,
       count(*) FILTER (WHERE posted_at < now() - make_interval(days => %(days)s))
                                                                   AS expired
  FROM raw_postings
 GROUP BY source
 ORDER BY source;
"""

DELETE_SQL = """
DELETE FROM raw_postings
 WHERE source = ANY(%(cut)s)
    OR posted_at < now() - make_interval(days => %(days)s);
"""


def assert_live(conn) -> None:
    # The whole point of db_meta: a purge pointed at the restored eval snapshot
    # would destroy the eval baseline, and the snapshot is the one thing in this
    # project that cannot be re-fetched. Absent or non-'live' both refuse.
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM db_meta")
            row = cur.fetchone()
    except psycopg.errors.UndefinedTable as exc:
        raise RuntimeError(
            "db_meta is missing — this database does not declare whether it is live "
            "or an eval snapshot. Apply db/schema/003_retention.sql first."
        ) from exc

    if row is None:
        raise RuntimeError("db_meta has no row — refusing to purge a database of unknown role.")
    if row[0] != "live":
        raise RuntimeError(f"db_meta.role is {row[0]!r}, not 'live' — refusing to purge.")


def purge(conn, *, apply: bool) -> int:
    assert_live(conn)
    params = {"cut": list(CUT_SOURCES), "days": WINDOW_DAYS}

    with conn.cursor() as cur:
        cur.execute(COUNT_SQL, params)
        rows = cur.fetchall()

    doomed = 0
    for source, total, cut_source, expired in rows:
        # A cut-source row can also be expired; count it once.
        going = cut_source + expired if source not in CUT_SOURCES else total
        doomed += going
        logger.info("%-9s total=%-6d deleting=%-6d keeping=%d", source, total, going, total - going)

    if not apply:
        logger.info("DRY RUN — %d rows would be deleted. Re-run with --apply.", doomed)
        return 0

    with conn.cursor() as cur:
        cur.execute(DELETE_SQL, params)
        deleted = int(cur.rowcount)
    conn.commit()
    logger.info("Deleted %d rows.", deleted)
    return deleted


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    parser = argparse.ArgumentParser(description="Purge cut sources and postings past the window.")
    parser.add_argument("--apply", action="store_true", help="actually delete (default: dry run)")
    args = parser.parse_args()

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        purge(conn, apply=args.apply)
