import argparse
import asyncio
import os

import psycopg
from dotenv import load_dotenv
from pydantic_ai import Agent, AgentRunResult
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.settings import ModelSettings
from pydantic_ai.tool_manager import ToolManager

from src.agent.prompt import SYSTEM_PROMPT
from src.agent.schema import Answer
from src.agent.tools import make_role_detail, make_sql_query, make_vector_search

load_dotenv()


def build_agent(
    model: str = "deepseek:deepseek-v4-flash", conn=None, system_prompt: str = SYSTEM_PROMPT
) -> Agent[None, Answer]:
    tools = [make_sql_query(conn), make_vector_search(conn), make_role_detail(conn)]
    return Agent(model=model, tools=tools, system_prompt=system_prompt, output_type=Answer)


async def ask(agent: Agent[None, Answer], question: str) -> AgentRunResult[Answer]:
    model_settings = ModelSettings(timeout=60, temperature=0)
    with ToolManager.parallel_execution_mode("sequential"):
        return await agent.run(user_prompt=question, model_settings=model_settings)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Pydantic AI DeepSeek Data Assistant Loop")
    parser.add_argument(
        "--question",
        "-q",
        type=str,
        required=True,
        help="The natural language question to ask the agent.",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="deepseek:deepseek-v4-flash",
        help="The target model string designation (default: flash version).",
    )
    args = parser.parse_args()

    db_url = os.environ.get("EVAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError(
            "Database connection URL missing. Please set EVAL_DATABASE_URL or DATABASE_URL."
        )

    with psycopg.connect(db_url) as conn:
        agent = build_agent(model=args.model, conn=conn)
        result = await ask(agent, args.question)
        print(result.output.answer)
        for e in result.output.evidence:
            print("-", e)

        tool_calls_count = sum(
            1
            for msg in result.all_messages()
            if hasattr(msg, "parts")
            for part in msg.parts
            if isinstance(part, ToolCallPart)
        )

        print(f"Called {tool_calls_count} tools")


if __name__ == "__main__":
    asyncio.run(main())
