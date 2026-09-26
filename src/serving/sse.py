import json
from collections.abc import AsyncIterator

from pydantic_ai import (
    Agent,
    AgentRunResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelSettings,
)
from pydantic_ai.tool_manager import ToolManager

from src.agent.schema import Answer


def sse_event(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_answer(agent: Agent[None, Answer], question: str) -> AsyncIterator[str]:
    model_settings = ModelSettings(timeout=60, temperature=0)
    with ToolManager.parallel_execution_mode("sequential"):
        async with agent:
            try:
                async with agent.run_stream_events(
                    question, model_settings=model_settings
                ) as events:
                    async for ev in events:
                        if isinstance(ev, FunctionToolCallEvent):
                            yield sse_event(
                                "tool_call", {"name": ev.part.tool_name, "args": ev.part.args}
                            )
                        elif isinstance(ev, FunctionToolResultEvent):
                            yield sse_event("tool_result", {"name": ev.part.tool_name})
                        elif isinstance(ev, AgentRunResultEvent):
                            yield sse_event(
                                "answer",
                                {
                                    "answer": ev.result.output.answer,
                                    "evidence": ev.result.output.evidence,
                                },
                            )
            except Exception as e:
                yield sse_event("error", {"message": str(e)})
                return
