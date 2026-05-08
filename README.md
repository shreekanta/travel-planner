# Travel Planner Agent

Multi-agent travel planner built with **Claude Agent SDK (Python)** + **FastAPI** backend and a **Vite + Vanilla TS** frontend.

## Architecture

```
        ┌──────────────────────┐
        │   Frontend (Vite TS) │
        │   form → POST /plan  │
        └──────────┬───────────┘
                   │ JSON (pax, dates, destination, origin)
        ┌──────────▼───────────┐
        │  FastAPI  (main.py)  │
        └──────────┬───────────┘
                   │
        ┌──────────▼───────────┐
        │  Orchestrator agent  │  Claude Agent SDK
        │  (travel_agent.py)   │
        └──┬─────────┬─────────┬──────────────┐
           │ Task    │ Task    │ Task         │ direct tool
   ┌───────▼──┐  ┌───▼──────┐  ┌▼─────────┐   │
   │ flight-  │  │ hotel-   │  │ weather- │   │
   │ checker  │  │ checker  │  │ checker  │   │
   └────┬─────┘  └────┬─────┘  └────┬─────┘   │
        │             │             │         │
   search_flights search_hotels  check_weather  search_attractions
        (mock data tools — backend/tools.py)
```

The orchestrator delegates to three sub-agents (each with isolated context) via the SDK's built-in `Task` tool, calls `search_attractions` directly, then assembles a final markdown report (Trip Summary, Flights, Hotels, Weather, Attractions, Cost, Tips).

## Inputs / Output

| Input         | Type    | Example       |
|---------------|---------|---------------|
| pax           | int     | 2             |
| start_date    | YYYY-MM-DD | 2026-06-15 |
| end_date      | YYYY-MM-DD | 2026-06-20 |
| destination   | string  | Tokyo         |
| origin        | string  | BLR (default) |

| Output    | Description                                   |
|-----------|-----------------------------------------------|
| markdown  | Full report (tables only) — rendered in UI    |

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env .env        # add your ANTHROPIC_API_KEY
uvicorn main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/health`

Smoke-test the agent without the UI:

```bash
python travel_agent.py
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev          # opens http://localhost:5173
```

Optionally point the UI at a non-default backend:

```bash
VITE_API=http://localhost:8000 npm run dev
```

## File map

| File                          | Purpose                                  |
|-------------------------------|------------------------------------------|
| backend/tools.py              | Mock flight/hotel/weather/attractions    |
| backend/travel_agent.py       | Orchestrator + 3 sub-agents (SDK)        |
| backend/main.py               | FastAPI `POST /plan` endpoint            |
| backend/requirements.txt      | Python deps                              |
| frontend/index.html           | Single-page shell                        |
| frontend/src/main.ts          | Form + fetch + markdown render           |
| frontend/src/style.css        | Dark theme, responsive                   |
| frontend/package.json         | Vite + TS + marked                       |

## Swap mock data for real APIs

Replace function bodies in `backend/tools.py`:

| Tool                | Real API option                                  |
|---------------------|--------------------------------------------------|
| search_flights      | Amadeus Flight Offers / Skyscanner / Kiwi        |
| search_hotels       | Booking.com / Amadeus Hotel / Hotels.com         |
| check_weather       | OpenWeatherMap / WeatherAPI / Tomorrow.io        |
| search_attractions  | Google Places / TripAdvisor Content              |

The MCP tool wrappers in `travel_agent.py` and the sub-agent prompts stay the same.

## Notes

| Item       | Value                                                   |
|------------|---------------------------------------------------------|
| Model      | claude-sonnet-4-5 (orchestrator), haiku (sub-agents)    |
| FX rate    | 1 USD = 83 INR (hard-coded in tools.py — change there)  |
| Default origin | BLR                                                 |
