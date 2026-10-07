import asyncio
from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from pydantic_ai import (
    Agent,
    AgentRunResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
)

from src.agent.schema import Answer
from src.serving.app import app
from src.serving.sse import sse_event, stream_answer, summarize_tool_result

# Payload values come from the corpus, not invention: gold_40_candidates.json
# row 1 (hn 48747990, "We The Flywheel") is the posting DECISIONS: schema cites
# for the Agentic Engineer role and its claude code / cursor / aider stack.
# similarity is not a gold field (runtime-computed) — any float does.
_FULL_HIT = {
    "raw_posting_id": 1234,
    "role_index": 0,
    "title": "Agentic Engineer",
    "company": "We The Flywheel",
    "location": "REMOTE (worldwide)",
    "seniority": "unknown",
    "remote_policy": "remote",
    "employment_type": "contract",
    "stack": ["claude code", "cursor", "aider"],
    "salary_min": None,
    "salary_max": None,
    "salary_currency": None,
    "description": "ship real software with AI coding agents (Claude Code, Cursor, Aider).",
    "source": "hn",
    "external_id": "48747990",
    "similarity": 0.68,
}
_PROJECTED_HIT = {
    "raw_posting_id": 1234,
    "role_index": 0,
    "title": "Agentic Engineer",
    "company": "We The Flywheel",
    "location": "REMOTE (worldwide)",
    "seniority": "unknown",
    "remote_policy": "remote",
    "stack": ["claude code", "cursor", "aider"],
    "salary_min": None,
    "salary_max": None,
    "salary_currency": None,
    "source": "hn",
    "similarity": 0.68,
}
_TOOL_CALL = {"name": "vector_search", "args": {"query": "agentic engineer", "limit": 5}}
_TOOL_RESULT = {"name": "vector_search", "content": [_PROJECTED_HIT]}
_TOOL_RESULT_FRAME = (
    'event: tool_result\ndata: {"name": "vector_search", "content": ['
    '{"raw_posting_id": 1234, "role_index": 0, "title": "Agentic Engineer", '
    '"company": "We The Flywheel", "location": "REMOTE (worldwide)", '
    '"seniority": "unknown", "remote_policy": "remote", "stack": ["claude code", '
    '"cursor", "aider"], "salary_min": null, "salary_max": null, '
    '"salary_currency": null, "source": "hn", "similarity": 0.68}]}\n\n'
)
_ROLE_DETAIL = {
    "raw_posting_id": 1234,
    "role_index": 0,
    "company": "We The Flywheel",
    "title": "Agentic Engineer",
    "location": "REMOTE (worldwide)",
    "seniority": "unknown",
    "remote_policy": "remote",
    "employment_type": "contract",
    "stack": ["claude code", "cursor", "aider"],
    "salary_min": None,
    "salary_max": None,
    "salary_currency": None,
    "description": "ship real software with AI coding agents (Claude Code, Cursor, Aider).",
    "source_quotes": {"company": "We The Flywheel"},
    "source": "hn",
    "external_id": "48747990",
}
_ROLE_DETAIL_TRIMMED = {k: v for k, v in _ROLE_DETAIL.items() if k != "description"}
_ANSWER_TEXT = "Agentic Engineer roles at We The Flywheel lean on claude code, cursor and aider."
_ANSWER_EVIDENCE = ["Agentic Engineer at We The Flywheel - claude code, cursor, aider - hn"]


@pytest.mark.parametrize(
    ("event", "data", "expected"),
    [
        (
            "tool_call",
            _TOOL_CALL,
            (
                "event: tool_call\n"
                'data: {"name": "vector_search", "args": {"query": "agentic engineer", '
                '"limit": 5}}\n\n'
            ),
        ),
        ("tool_result", _TOOL_RESULT, _TOOL_RESULT_FRAME),
        (
            "answer",
            {"answer": _ANSWER_TEXT, "evidence": _ANSWER_EVIDENCE},
            (
                "event: answer\n"
                'data: {"answer": "Agentic Engineer roles at We The Flywheel lean on claude code, '
                'cursor and aider.", "evidence": ["Agentic Engineer at We The Flywheel - '
                'claude code, cursor, aider - hn"]}\n\n'
            ),
        ),
    ],
)
def test_sse_event_format(event: str, data: object, expected: str) -> None:
    # json.dumps, not str(): a Python-repr payload (single quotes) is not JSON,
    # and nothing on the browser side of the SSE connection could parse it.
    assert sse_event(event, data) == expected


class _StubEvents:
    # run_stream_events' contract: an async CM handing out the event iterator.
    def __init__(self, events: list[object], exc: Exception | None = None) -> None:
        self._events = events
        self._exc = exc

    async def __aenter__(self) -> AsyncIterator[object]:
        return self._agen()

    async def __aexit__(self, *exc_info: object) -> None:
        return None

    async def _agen(self) -> AsyncIterator[object]:
        for ev in self._events:
            yield ev
        if self._exc is not None:
            raise self._exc


class _StubAgent:
    # Only the Agent surface stream_answer touches: async CM + run_stream_events.
    def __init__(self, events: list[object], exc: Exception | None = None) -> None:
        self._events = _StubEvents(events, exc)

    async def __aenter__(self) -> "_StubAgent":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        return None

    def run_stream_events(
        self, _question: str, *, model_settings: object | None = None
    ) -> _StubEvents:
        return self._events


def _collect(agent: object, question: str) -> list[str]:
    # stream_answer is async but the repo has no pytest-asyncio; drain it with
    # asyncio.run inside a sync test instead.
    async def run() -> list[str]:
        typed = cast(Agent[None, Answer], agent)
        return [frame async for frame in stream_answer(typed, question)]

    return asyncio.run(run())


def test_stream_answer_maps_events_to_frames() -> None:
    answer = Answer(answer=_ANSWER_TEXT, evidence=_ANSWER_EVIDENCE)
    events = [
        FunctionToolCallEvent(
            part=cast(Any, SimpleNamespace(tool_name="vector_search", args=_TOOL_CALL["args"])),
            args_valid=True,
        ),
        FunctionToolResultEvent(
            part=cast(Any, SimpleNamespace(tool_name="vector_search", content=[_FULL_HIT])),
        ),
        AgentRunResultEvent(result=cast(Any, SimpleNamespace(output=answer))),
    ]

    assert _collect(_StubAgent(events), "agentic engineer") == [
        (
            "event: tool_call\n"
            'data: {"name": "vector_search", "args": {"query": "agentic engineer", '
            '"limit": 5}}\n\n'
        ),
        _TOOL_RESULT_FRAME,
        (
            "event: answer\n"
            'data: {"answer": "Agentic Engineer roles at We The Flywheel lean on claude code, '
            'cursor and aider.", "evidence": ["Agentic Engineer at We The Flywheel - '
            'claude code, cursor, aider - hn"]}\n\n'
        ),
    ]


@pytest.mark.parametrize(
    ("name", "content", "expected"),
    [
        ("vector_search", [_FULL_HIT], [_PROJECTED_HIT]),
        ("role_detail", _ROLE_DETAIL, _ROLE_DETAIL_TRIMMED),
        ("role_detail", None, None),
        (
            "sql_query",
            [{"skill": "python", "roles": 30, "postings": 25}],
            [{"skill": "python", "roles": 30, "postings": 25}],
        ),
        ("future_tool", {"x": 1}, {"x": 1}),
        ("vector_search", "error string", "error string"),
    ],
)
def test_summarize_tool_result(name: str, content: object, expected: object) -> None:
    assert summarize_tool_result(name, content) == expected


def test_stream_answer_emits_error_frame() -> None:
    stub = _StubAgent([], exc=RuntimeError("boom"))
    assert _collect(stub, "q") == ['event: error\ndata: {"message": "boom"}\n\n']


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_requires_query() -> None:
    # Both requests 422 in validation, before the handler opens a DB
    # connection or builds the model, so the suite stays offline.
    with TestClient(app) as client:
        assert client.get("/ask").status_code == 422
        assert client.post("/ask", json={}).status_code == 422
