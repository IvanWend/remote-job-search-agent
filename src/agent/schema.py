from pydantic import BaseModel, Field


class Answer(BaseModel):
    answer: str = Field(
        description="The direct answer and nothing else — no tables, no alternatives, no follow-up offers."
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Verbatim source quotes backing the answer; empty when none.",
    )
