from collections.abc import Iterator

import pytest
from httpx import AsyncClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.main import app
from app.modules.agent.service import build_agent, get_agent


class FakeToolCallingModel(GenericFakeChatModel):
    """A fake chat model that supports `bind_tools` (a no-op) so it can drive
    a real `create_agent` tool-calling loop deterministically in tests."""

    def bind_tools(self, tools, **kwargs):
        return self


def _fake_agent(messages: Iterator[AIMessage]):
    return build_agent(model=FakeToolCallingModel(messages=messages))


@pytest.mark.asyncio
async def test_agent_chat_calls_tool_then_replies(client: AsyncClient):
    fake_messages = iter(
        [
            AIMessage(
                content="",
                tool_calls=[{"name": "add_numbers", "args": {"a": 2, "b": 3}, "id": "1"}],
            ),
            AIMessage(content="The answer is 5."),
        ]
    )
    app.dependency_overrides[get_agent] = lambda: _fake_agent(fake_messages)

    response = await client.post("/api/v1/agent/chat", json={"message": "what is 2+3?"})

    assert response.status_code == 200
    assert response.json() == {"reply": "The answer is 5."}


@pytest.mark.asyncio
async def test_agent_chat_replies_without_tool_call(client: AsyncClient):
    fake_messages = iter([AIMessage(content="Hi there!")])
    app.dependency_overrides[get_agent] = lambda: _fake_agent(fake_messages)

    response = await client.post("/api/v1/agent/chat", json={"message": "hello"})

    assert response.status_code == 200
    assert response.json() == {"reply": "Hi there!"}


@pytest.mark.asyncio
async def test_agent_chat_rejects_empty_message(client: AsyncClient):
    # Override to avoid constructing a real ChatOpenAI client (network calls,
    # invalid without an API key); validation should reject the body first.
    app.dependency_overrides[get_agent] = lambda: _fake_agent(iter([AIMessage(content="")]))

    response = await client.post("/api/v1/agent/chat", json={"message": ""})
    assert response.status_code == 422
