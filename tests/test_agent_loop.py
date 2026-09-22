from src.agent.loop import build_agent


def test_build_agent_registers_three_tools() -> None:
    # No DB and no model: build_agent is pure, so a bare object() would
    # AttributeError on any build-time conn use. This also imports loop.py, so a
    # broken import there fails the gate instead of only a manual run.
    agent = build_agent(conn=object())

    # _function_toolset is pydantic-ai's private store of the tools passed to
    # Agent(...); there is no public name-enumeration API, and its .tools dict is
    # keyed by the name the model calls.
    assert set(agent._function_toolset.tools) == {"sql_query", "vector_search", "role_detail"}
