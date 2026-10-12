import os

from pydantic_ai import UsageLimits
from pydantic_ai.settings import ModelSettings


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw else default


def usage_limits() -> UsageLimits:
    # request_limit = max turns (one model request each). Token caps are the
    # spend proxy: the model registry carries no DeepSeek cost, so cost_limit
    # would warn and never fire (see DECISIONS: Agent).
    return UsageLimits(
        request_limit=_int("AGENT_MAX_REQUESTS", 8),
        tool_calls_limit=_int("AGENT_MAX_TOOL_CALLS", 12),
        total_tokens_limit=_int("AGENT_TOTAL_TOKENS", 50_000),
        output_tokens_limit=_int("AGENT_OUTPUT_TOKENS", 4_000),
    )


def model_settings() -> ModelSettings:
    return ModelSettings(timeout=60, temperature=0)
