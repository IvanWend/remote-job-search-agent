from datetime import UTC, datetime, timedelta

# The rolling freshness window. Enforced in two places on purpose: purge.py
# deletes what has aged out, load.py drops aged-out rows before they are ever
# inserted. Age-purge alone means every run re-inserts the same expired
# postings the boards still serve, which the next purge deletes again.
WINDOW_DAYS = 90

# Cut as a live source (Phase 1b). Kept out of the schema CHECK too, but the
# purge is what actually removes the rows already in the table.
CUT_SOURCES = ("adzuna",)


def window_cutoff(now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) - timedelta(days=WINDOW_DAYS)
