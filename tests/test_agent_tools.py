import os

import psycopg
import pytest
from dotenv import load_dotenv
from pydantic_ai import Tool

from src.agent.tools import make_sql_query

load_dotenv()


def test_sql_query_schema_contract() -> None:
    # No DB: proves the whitelist + teaching facts survive docstring resolution,
    # and that the factory is pure (a bare object AttributeErrors on any conn use).
    fn = make_sql_query(object())
    td = Tool(fn).tool_def

    props = td.parameters_json_schema["properties"]
    assert props["query"]["enum"] == [
        "skill_frequency",
        "salary_by_currency",
        "salary_by_seniority",
    ]
    assert set(props) == {"query", "limit", "currency"}

    desc = (td.description or "").lower()
    for fact in ("monthly", "postings", "currency"):
        assert fact in desc


@pytest.fixture(scope="module")
def eval_conn():
    with psycopg.connect(os.environ["EVAL_DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM db_meta")
            row = cur.fetchone()
        assert row is not None and row[0] == "eval", "not the frozen snapshot"
        yield conn


def test_skill_frequency_shape(eval_conn) -> None:
    rows = make_sql_query(eval_conn)(query="skill_frequency", limit=3)
    assert 0 < len(rows) <= 3
    for r in rows:
        assert set(r) == {"skill", "roles", "postings"}
    # SKILL_FREQUENCY_SQL orders by roles DESC, so the list is non-increasing.
    assert all(rows[i]["roles"] >= rows[i + 1]["roles"] for i in range(len(rows) - 1))


def test_salary_by_currency_shape(eval_conn) -> None:
    rows = make_sql_query(eval_conn)(query="salary_by_currency")
    assert rows
    for r in rows:
        assert set(r) == {"currency", "n", "median_max_monthly"}


def test_salary_by_seniority_shape(eval_conn) -> None:
    rows = make_sql_query(eval_conn)(query="salary_by_seniority", currency="USD")
    assert rows
    for r in rows:
        assert set(r) == {"seniority", "roles", "with_salary", "median_max_monthly"}
