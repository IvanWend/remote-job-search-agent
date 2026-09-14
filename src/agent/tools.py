from collections.abc import Callable
from typing import Any, Literal, assert_never

from src.storage import analytics

# The whitelist is the type: the model can only name one of these three, and
# pydantic-ai rejects anything else before it reaches this function. No SQL
# string ever crosses the model -> DB boundary.
QueryName = Literal["skill_frequency", "salary_by_currency", "salary_by_seniority"]


def make_sql_query(conn) -> Callable[..., list[dict[str, Any]]]:
    # Closure, not a conn param: a conn in the signature would leak into the tool
    # schema the model sees. The build is pure (no conn use) — the contract test
    # passes a dummy object to prove it.
    def sql_query(
        query: QueryName,
        *,
        limit: int = 20,
        currency: str = "USD",
    ) -> list[dict[str, Any]]:
        """Answer a canned analytics question over the structured corpus.

        Median figures are monthly medians of salary_max, in the currency's own
        units (RUB rows read ~10^4, USD ~10^5 — never mix them). A null currency
        means the source never stated one and its median is intentionally absent.
        Report postings, not roles, when asked how many jobs want a skill.

        Args:
            query: Which of the three hand-written analytics shapes to run.
            limit: Top-N skills returned, used only by skill_frequency.
            currency: Currency for the salary-by-seniority split, used only by that query.
        """
        if query == "skill_frequency":
            return [r._asdict() for r in analytics.skill_frequency(conn, limit)]
        if query == "salary_by_currency":
            return [r._asdict() for r in analytics.salary_by_currency(conn)]
        if query == "salary_by_seniority":
            return [r._asdict() for r in analytics.salary_by_seniority(conn, currency)]
        assert_never(query)

    return sql_query
