"""Example LangChain agent: a tool-calling agent built with LangChain's
`create_agent` (LangGraph-based agent runtime). See
https://docs.langchain.com/oss/python/langchain/agents.

This is intentionally small — swap the model, extend `app/agents/tools.py`,
or add LangChain middleware as your use case grows.
"""

from functools import lru_cache
from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.agents.tools import get_tools
from app.core.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = (
    "You are a helpful assistant embedded in the Fullstack Template app. "
    "Use tools when they help answer the user's question. Be concise."
)

# `create_agent` returns a compiled LangGraph state graph, which implements
# LangChain's `Runnable` interface (`.invoke`/`.ainvoke`). Aliased for
# readability at call sites instead of using a bare `Any`.
Agent = Runnable[dict[str, Any], dict[str, Any]]


def build_llm() -> BaseChatModel:
    """Build the chat model used by the example agent from app settings."""
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=settings.openai_temperature,
    )


def build_agent(model: BaseChatModel | None = None) -> Agent:
    """Build the example tool-calling agent.

    Accepts an optional `model` so tests/other callers can swap in a fake
    chat model without touching global config.
    """
    return create_agent(
        model or build_llm(),
        tools=get_tools(),
        system_prompt=SYSTEM_PROMPT,
    )


@lru_cache
def get_agent() -> Agent:
    """FastAPI dependency: build (and cache) the default agent for the process.

    Overridden in tests via `app.dependency_overrides` with a fake model, the
    same pattern used for `get_db`/`get_current_user`.
    """
    return build_agent()
