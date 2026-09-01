# Design: Agent Chat

## Architecture Overview
`app/agents/agent.py` builds a LangChain tool-calling agent using
[`create_agent`](https://docs.langchain.com/oss/python/langchain/agents)
(LangGraph-based agent runtime) with `ChatOpenAI` as the model and the tools
in `app/agents/tools.py`. The FastAPI route depends on `get_agent()` (an
`lru_cache`d factory, same DI pattern as `get_db`/`get_current_user`), so
tests can override it with a fake chat model instead of calling a real LLM.

## API Contract

### `POST /api/v1/agent/chat`
- **Auth:** required (Auth0 JWT bearer token)
- **Request body:**
  ```json
  { "message": "What is 2 + 3?" }
  ```
- **Success response (`200`):**
  ```json
  { "reply": "The answer is 5." }
  ```
- **Error responses:** `422` invalid body (empty/too-long message), `401`
  missing/invalid token.

## Extending
- Add tools: append `@tool`-decorated functions in `app/agents/tools.py` and
  register them in `get_tools()`.
- Swap models: change `build_llm()` in `app/agents/agent.py` (any LangChain
  chat model works, not just `ChatOpenAI`), or use `init_chat_model("provider:model")`.
- Add memory/streaming: see LangChain's `create_agent` docs for
  `checkpointer` (memory) and streaming support.

## Test Plan
- **Backend (pytest, `tests/test_agent.py`):** overrides `get_agent` with a
  `GenericFakeChatModel` subclass that supports `bind_tools` (a no-op),
  proving the real `create_agent` tool-calling loop runs end-to-end
  (tool call → tool result → final reply) without hitting a real LLM API.
  Also covers a no-tool-call reply and the `422` validation case.
- **Frontend:** not wired to a UI in this template; the Kubb-generated
  `chatWithAgentApiV1AgentChatPost` client function is available for use in a
  future page/store, following the same pattern as `specs/todos`.
