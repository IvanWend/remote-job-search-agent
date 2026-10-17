from typing import Literal

from pydantic import BaseModel, Field

# A table cell is a number (counts, medians, salaries) or a label (skill, company,
# title, seniority); null is the tool's own "no value", rendered as an explicit
# absence rather than a fabricated figure.
Cell = str | int | float | None


class Table(BaseModel):
    kind: Literal["bars", "table"] = Field(
        description=(
            '"bars" for a skill-frequency ranking (rows are [skill, count] pairs); '
            '"table" for any other tabular result (headers + rows).'
        )
    )
    title: str = Field(description="One short label for the table.")
    headers: list[str] = Field(
        default_factory=list,
        description="Column headers; empty for a bars table.",
    )
    rows: list[list[Cell]] = Field(
        default_factory=list,
        description=(
            "Data rows. Numbers copied exactly as the tools returned them — "
            "monthly, in their own currency, never converted or rounded."
        ),
    )


class Quote(BaseModel):
    id: int = Field(description="1-based citation number, referenced from key_finding as [n].")
    company: str | None = Field(
        default=None,
        description="Company, copied from the structured record.",
    )
    title: str | None = Field(
        default=None,
        description="Role title, copied from the structured record.",
    )
    source: str = Field(description="Board the posting came from (hn, remotive, web3, habr).")
    seniority: str | None = Field(
        default=None,
        description="Seniority level from the structured record.",
    )
    stack: list[str] = Field(default_factory=list, description="Skills from the structured record.")
    salary_min: int | None = Field(
        default=None,
        description="Monthly minimum salary, in its own currency.",
    )
    salary_max: int | None = Field(
        default=None,
        description="Monthly maximum salary, in its own currency.",
    )
    salary_currency: str | None = Field(
        default=None,
        description="ISO 4217 currency code, never converted.",
    )
    text: str = Field(
        description=(
            "A verbatim contiguous substring of the role's source_quotes (or its raw "
            "posting text), backing the claim it is attached to."
        ),
    )


class Answer(BaseModel):
    headline: str = Field(description="One sentence that directly answers the question.")
    key_finding: str = Field(
        description=(
            "The strongest numeric claim, citing the supporting quotes by id as [n]. "
            "If a salary figure excludes roles whose currency was never stated, say so."
        )
    )
    tables: list[Table] = Field(
        default_factory=list,
        description="At most 3 tables, each from tool output.",
    )
    quotes: list[Quote] = Field(
        default_factory=list,
        description="At most 5 quotes, each from tool output.",
    )
