# Requirements: Agent Chat

## Overview
An example LangChain agent, exposed over the API, demonstrating how to add
LLM-powered features to the backend: a tool-calling agent that can answer
questions and invoke simple tools (e.g. arithmetic, current time).

## User Stories

### US-1: Chat with the example agent
As an authenticated user, I want to send a message to the agent and get a
reply, so that I can see how an LLM-backed feature is wired into this
template.

**Acceptance Criteria (EARS format):**
- WHEN an authenticated user submits a non-empty message (1-2000 chars) THE
  SYSTEM SHALL run the agent and return its final natural-language reply.
- IF the agent's reasoning requires a tool (e.g. arithmetic) THE SYSTEM SHALL
  invoke the tool and incorporate its result before replying.
- IF the message is empty or missing THEN THE SYSTEM SHALL reject the request
  with a `422` validation error.
- IF the request has no valid Auth0 bearer token THEN THE SYSTEM SHALL reject
  the request with a `401` error.

## Out of Scope
- Multi-turn conversation history / memory
- Streaming responses
- User-configurable models/tools via the API

## Open Questions
- None
