"""Example tools available to the sample agent.

Add your own `@tool`-decorated functions here and register them in
`get_tools()`. See https://docs.langchain.com/oss/python/langchain/tools.
"""

from datetime import UTC, datetime

from langchain_core.tools import BaseTool, tool


@tool
def get_current_time() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together and return the result."""
    return a + b


def get_tools() -> list[BaseTool]:
    """Tools registered with the example agent."""
    return [get_current_time, add_numbers]
