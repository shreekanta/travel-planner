"""Travel Planner orchestrator using Claude Agent SDK.

Architecture:
    main agent (orchestrator)
       ├── flight-checker   (sub-agent)  -> search_flights tool
       ├── hotel-checker    (sub-agent)  -> search_hotels tool
       ├── weather-checker  (sub-agent)  -> check_weather tool
       ├── cost-calculator  (sub-agent)  -> calc_trip_cost tool
       └── search_attractions tool       (called directly by orchestrator)

Sub-agents are isolated context windows; the orchestrator delegates to them
via the built-in `Task` tool, then composes the final markdown report.
"""
from __future__ import annotations
import asyncio
import datetime
import json
import os
import pathlib
from typing import Any

from dotenv import load_dotenv
from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
    tool,
)

from tools import (
    USD_TO_INR,
    check_weather,
    search_attractions,
    search_flights,
    search_hotels,
)

load_dotenv()

_TOKEN_LOG = pathlib.Path.home() / ".claude" / "travel_tokens.log"


def _log_tokens(destination: str, pax: int, usage: Any) -> dict[str, int]:
    entry: dict[str, int] = {
        "input_tokens": getattr(usage, "input_tokens", 0),
        "output_tokens": getattr(usage, "output_tokens", 0),
        "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0),
        "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0),
    }
    _TOKEN_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "destination": destination, "pax": pax, **entry}
    with _TOKEN_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return entry


# --------------------------------------------------------------------------- #
# Custom MCP tools                                                            #
# --------------------------------------------------------------------------- #
@tool(
    "search_flights",
    "Search flight options between origin and destination for given dates and pax count.",
    {
        "origin": str, "destination": str,
        "depart_date": str, "return_date": str, "pax": int,
    },
)
async def flights_tool(args: dict[str, Any]) -> dict[str, Any]:
    data = search_flights(
        origin=args["origin"], destination=args["destination"],
        depart_date=args["depart_date"], return_date=args["return_date"],
        pax=int(args["pax"]),
    )
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool(
    "search_hotels",
    "Search hotels in destination for stay range and pax count.",
    {"destination": str, "check_in": str, "check_out": str, "pax": int},
)
async def hotels_tool(args: dict[str, Any]) -> dict[str, Any]:
    data = search_hotels(
        destination=args["destination"], check_in=args["check_in"],
        check_out=args["check_out"], pax=int(args["pax"]),
    )
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool(
    "check_weather",
    "Get a daily weather forecast for destination across the date range.",
    {"destination": str, "start_date": str, "end_date": str},
)
async def weather_tool(args: dict[str, Any]) -> dict[str, Any]:
    data = check_weather(
        destination=args["destination"],
        start_date=args["start_date"], end_date=args["end_date"],
    )
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool(
    "search_attractions",
    "List top 5 attractions for the destination with estimated costs.",
    {"destination": str},
)
async def attractions_tool(args: dict[str, Any]) -> dict[str, Any]:
    data = search_attractions(destination=args["destination"])
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool(
    "calc_trip_cost",
    "Calculate estimated total trip cost from component totals. Returns JSON cost breakdown.",
    {
        "flight_total_usd": int,
        "hotel_total_usd": int,
        "attractions_total_usd": int,
        "pax": int,
        "days": int,
    },
)
async def cost_tool(args: dict[str, Any]) -> dict[str, Any]:
    flight = int(args["flight_total_usd"])
    hotel = int(args["hotel_total_usd"])
    attractions = int(args["attractions_total_usd"])
    pax = int(args["pax"])
    days = int(args["days"])
    food = 50 * pax * days
    total = flight + hotel + attractions + food
    data = {
        "items": [
            {"item": "Flights",                                         "usd": flight,      "inr": int(flight * USD_TO_INR)},
            {"item": "Hotel (recommended)",                             "usd": hotel,       "inr": int(hotel * USD_TO_INR)},
            {"item": "Attractions",                                     "usd": attractions, "inr": int(attractions * USD_TO_INR)},
            {"item": f"Food & Local (USD 50/pax/day × {days}d × {pax}pax)", "usd": food,  "inr": int(food * USD_TO_INR)},
            {"item": "**Total**",                                       "usd": total,       "inr": int(total * USD_TO_INR)},
        ],
        "per_person_usd": total // pax,
        "per_person_inr": int((total // pax) * USD_TO_INR),
    }
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


travel_mcp = create_sdk_mcp_server(
    name="travel-tools",
    version="1.0.0",
    tools=[flights_tool, hotels_tool, weather_tool, attractions_tool, cost_tool],
)


# --------------------------------------------------------------------------- #
# Sub-agent definitions                                                       #
# --------------------------------------------------------------------------- #
SUBAGENTS = {
    "flight-checker": AgentDefinition(
        description="Specialist that searches and ranks flight options.",
        prompt=(
            "You are a flight specialist. ALWAYS call the `search_flights` tool "
            "with the supplied parameters. Then return a concise markdown table "
            "with columns: Airline | Flight | Depart | Duration | Stops | "
            "Price/Pax (USD) | Total (USD) | Total (INR). End with one line "
            "recommending the best option (cheapest if direct, else best value)."
        ),
        tools=["mcp__travel-tools__search_flights"],
        model="haiku",
    ),
    "hotel-checker": AgentDefinition(
        description="Specialist that searches and ranks hotels.",
        prompt=(
            "You are a hotel specialist. ALWAYS call `search_hotels` with the "
            "given parameters. Return a concise markdown table with columns: "
            "Hotel | Tier | Rating | Neighborhood | Rooms | Per Night (USD) | "
            "Total (USD) | Total (INR). End with one line recommending the "
            "best mid-range option by default."
        ),
        tools=["mcp__travel-tools__search_hotels"],
        model="haiku",
    ),
    "weather-checker": AgentDefinition(
        description="Specialist that fetches the weather forecast.",
        prompt=(
            "You are a weather specialist. ALWAYS call `check_weather`. Return "
            "a concise markdown table with columns: Date | Conditions | High "
            "(C/F) | Low (C/F) | Precip%. End with a single packing tip based "
            "on the conditions."
        ),
        tools=["mcp__travel-tools__check_weather"],
        model="haiku",
    ),
    "cost-calculator": AgentDefinition(
        description="Specialist that computes the estimated total trip cost breakdown.",
        prompt=(
            "You are a trip cost specialist. You will receive five integers: "
            "flight_total_usd, hotel_total_usd, attractions_total_usd, pax, days. "
            "ALWAYS call `calc_trip_cost` with those exact values. "
            "Return a markdown table with columns: Item | USD | INR. "
            "End with one line: 'Per person: USD X / INR Y'."
        ),
        tools=["mcp__travel-tools__calc_trip_cost"],
        model="haiku",
    ),
}


# --------------------------------------------------------------------------- #
# Orchestrator                                                                #
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """You are a Travel Planner orchestrator. The user will give you:
origin, destination, start date, end date, pax.

WORKFLOW (mandatory):
1. Use the `Task` tool to delegate to subagent `flight-checker` with origin, destination, depart_date=start, return_date=end, pax.
2. Use `Task` to delegate to subagent `hotel-checker` with destination, check_in=start, check_out=end, pax.
3. Use `Task` to delegate to subagent `weather-checker` with destination, start_date, end_date.
4. Call `mcp__travel-tools__search_attractions` directly for the destination.
5. Extract these integers from the results so far:
   - flight_total_usd: Total (USD) of the RECOMMENDED flight from flight-checker
   - hotel_total_usd: Total (USD) of the RECOMMENDED hotel from hotel-checker
   - attractions_total_usd: sum of all attraction est_cost_usd_per_pax × pax
   - days: (end_date − start_date) in calendar days
   Then use `Task` to delegate to `cost-calculator` with a message listing those integers.
6. Compose a FINAL REPORT in markdown with these sections IN ORDER:

   ## Trip Summary
   Table: Field | Value (rows: Destination, Origin, Dates, Days, Pax)

   ## Flights
   Insert the flight-checker table verbatim. Add one-line recommendation.

   ## Hotels
   Insert the hotel-checker table verbatim. Add one-line recommendation.

   ## Weather
   Insert the weather-checker table verbatim.

   ## Top Attractions
   Table: Attraction | Type | Est. Cost / Pax (USD) | Est. Cost / Pax (INR)

   ## Estimated Total Cost
   Insert the cost-calculator table verbatim.

   ## Notes & Tips
   2 short bullets max.

RULES:
- Use ONLY markdown tables. No long prose paragraphs.
- INR conversion: 1 USD = 83 INR. Show whole numbers.
- Default origin if missing: BLR (Bangalore).
- Be brief and dense. The user prefers tables over text."""


async def plan_trip(
    pax: int,
    start_date: str,
    end_date: str,
    destination: str,
    origin: str = "BLR",
) -> tuple[str, dict[str, int]]:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Copy .env to .env and fill it in."
        )

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"travel-tools": travel_mcp},
        agents=SUBAGENTS,
        allowed_tools=[
            "Task",
            "mcp__travel-tools__search_flights",
            "mcp__travel-tools__search_hotels",
            "mcp__travel-tools__check_weather",
            "mcp__travel-tools__search_attractions",
            "mcp__travel-tools__calc_trip_cost",
        ],
        permission_mode="bypassPermissions",
        max_turns=25,
        model="claude-sonnet-4-5",
    )

    user_msg = (
        f"Plan my trip:\n"
        f"- Origin: {origin}\n"
        f"- Destination: {destination}\n"
        f"- Start date: {start_date}\n"
        f"- End date: {end_date}\n"
        f"- Pax: {pax}\n\n"
        f"Delegate to flight-checker, hotel-checker, and weather-checker "
        f"sub-agents, call search_attractions directly, then delegate cost "
        f"calculation to cost-calculator. Assemble the final report exactly "
        f"per the system prompt format."
    )

    final_text_parts: list[str] = []
    usage_dict: dict[str, int] = {}
    async with ClaudeSDKClient(options=options) as client:
        await client.query(user_msg)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        final_text_parts.append(block.text)
            elif isinstance(msg, ResultMessage):
                if hasattr(msg, "usage") and msg.usage is not None:
                    usage_dict = _log_tokens(destination, pax, msg.usage)

    # The last assistant message tends to be the report. Join all and trim.
    full = "\n\n".join(p for p in final_text_parts if p.strip())
    # Heuristic: keep from the last "## Trip Summary" onward if present.
    marker = "## Trip Summary"
    if marker in full:
        full = full[full.rfind(marker):]
    return full.strip(), usage_dict


if __name__ == "__main__":
    out, tokens = asyncio.run(
        plan_trip(pax=2, start_date="2026-06-15",
                  end_date="2026-06-20", destination="Tokyo", origin="BLR")
    )
    print(out)
    print(f"\nTokens: {tokens}")
