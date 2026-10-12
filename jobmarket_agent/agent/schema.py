from pydantic import BaseModel, Field


class Answer(BaseModel):
    answer: str = Field(
        description=(
            "The direct answer and nothing else — no tables, no alternatives, no offers. "
            "If a salary figure excludes roles whose currency was never stated, say so."
        )
    )
    evidence: list[str] = Field(
        default_factory=list,
        description=(
            "Tool-derived citations backing the answer — role + stack + source; empty when none."
        ),
    )
