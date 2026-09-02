# Tasks: Agent Chat

- [x] Backend: add `langchain`, `langchain-openai`, `langchain-core` dependencies
- [x] Backend: example tools (`app/modules/agent/tools.py`) (Req: US-1)
- [x] Backend: tool-calling agent factory (`app/modules/agent/service.py`) (Req: US-1)
- [x] Backend: `POST /api/v1/agent/chat` route + schemas (Req: US-1)
- [x] Backend: pytest coverage — tool-call loop, no-tool-call reply, validation (Req: US-1)
- [x] Export OpenAPI spec to `packages/api-spec/openapi.json`
- [x] Frontend: regenerate Kubb client (adds `chatWithAgentApiV1AgentChatPost`)
- [ ] Frontend: UI/store for agent chat (not included yet — left as an exercise;
      follow the pattern in `specs/todos`)
