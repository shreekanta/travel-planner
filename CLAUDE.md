# CLAUDE.md - Shared Guidance

This file provides general guidance to Claude Code (claude.ai/code) when working with code in this repository.
For frontend-specific guidance, see `frontend/CLAUDE.md`.
For backend-specific guidance, see `backend/CLAUDE.md`.

## Environment

`ANTHROPIC_API_KEY` must be set in `backend/.env` before running the backend.

## Architecture

The system is a multi-agent travel planner. The key layers are:

1. **`frontend/src/main.ts`** — Single-page form that POSTs `{pax, start_date, end_date, destination, origin}` to `POST /plan` and renders the returned markdown.

2. **`backend/main.py`** — FastAPI server. One endpoint (`POST /plan`) that calls `plan_trip()` and returns `{markdown}`. Thin wrapper with no business logic.

3. **`backend/travel_agent.py`** — All agent logic:
   - Wraps the four Python tool functions from `tools.py` as MCP tools using `@tool` decorator and `create_sdk_mcp_server`.
   - Defines three `AgentDefinition` sub-agents (`flight-checker`, `hotel-checker`, `weather-checker`), each using `haiku` and restricted to their one MCP tool.
   - The `plan_trip()` async function runs the orchestrator agent (`claude-sonnet-4-5`) which delegates to sub-agents via the built-in `Task` tool, calls `search_attractions` directly, then assembles a structured markdown report.

4. **`backend/tools.py`** — Deterministic mock implementations of the four data tools (`search_flights`, `search_hotels`, `check_weather`, `search_attractions`). Uses `hashlib.md5` seeding for reproducible results. **Replace function bodies here to wire in real APIs** (Amadeus, Booking.com, OpenWeatherMap, Google Places) — the MCP wrappers and agent prompts do not need to change.

### Tool → sub-agent binding

MCP tool names follow the pattern `mcp__travel-tools__<tool_name>`. Sub-agent `AgentDefinition.tools` lists only the MCP tools that sub-agent may call. The orchestrator's `allowed_tools` includes `Task` plus all four MCP tools.

### Report format

The orchestrator's `SYSTEM_PROMPT` in `travel_agent.py` strictly defines the output format (7 sections, markdown tables only). `plan_trip()` extracts from the last `## Trip Summary` marker in the assembled response.

## Key constants

| Constant | Location | Value |
|---|---|---|
| `USD_TO_INR` | `backend/tools.py:12` | `83.0` |
| Orchestrator model | `travel_agent.py:212` | `claude-sonnet-4-5` |
| Sub-agent model | `travel_agent.py` (each `AgentDefinition`) | `haiku` |
| Default origin | throughout | `BLR` (Bangalore) |
| Max turns | `travel_agent.py:210` | `25` |
