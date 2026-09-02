from fastapi import APIRouter, Depends

from app.core.auth import CurrentUser, get_current_user
from app.core.constants import API_V1_PREFIX
from app.modules.agent.schemas import AgentChatRequest, AgentChatResponse
from app.modules.agent.service import Agent, get_agent

router = APIRouter(prefix=f"{API_V1_PREFIX}/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    payload: AgentChatRequest,
    agent: Agent = Depends(get_agent),
    user: CurrentUser = Depends(get_current_user),
) -> AgentChatResponse:
    """Send a message to the example LangChain agent and return its final reply."""
    result = await agent.ainvoke({"messages": [{"role": "user", "content": payload.message}]})
    final_message = result["messages"][-1]
    # `content` is typed as `str | list` on LangChain messages (list is used for
    # multimodal content blocks); the example agent only ever produces text.
    reply = (
        final_message.content
        if isinstance(final_message.content, str)
        else str(final_message.content)
    )
    return AgentChatResponse(reply=reply)
