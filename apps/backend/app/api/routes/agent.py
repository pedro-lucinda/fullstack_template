from typing import Any

from fastapi import APIRouter, Depends

from app.agents.agent import get_agent
from app.core.auth import CurrentUser, get_current_user
from app.schemas.agent import AgentChatRequest, AgentChatResponse

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    payload: AgentChatRequest,
    agent: Any = Depends(get_agent),
    user: CurrentUser = Depends(get_current_user),
) -> AgentChatResponse:
    """Send a message to the example LangChain agent and return its final reply."""
    result = await agent.ainvoke({"messages": [{"role": "user", "content": payload.message}]})
    final_message = result["messages"][-1]
    return AgentChatResponse(reply=final_message.content)
