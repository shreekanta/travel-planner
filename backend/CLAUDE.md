# Backend CLAUDE Guidance

This document provides specific guidance for the backend development within the TravelPlanner project.

## Standards and Best Practices
@import url("../CLAUDE.md") # Example: import shared root guidance
@import url("./backend_standards.md") # Example: import backend-specific standards

## Backend Commands

### Backend (FastAPI + Claude Agent SDK)

```bash
# From project root using uv (preferred — uv.lock is present)
uv run uvicorn backend.main:app --reload --port 8000

# Or activate the venv directly
source .venv/bin/activate
cd backend && uvicorn main:app --reload --port 8000

# Smoke-test the agent without the UI (runs plan_trip for Tokyo)
cd backend && python travel_agent.py

# Health check
curl http://localhost:8000/health
```

## Backend Specifics
*   ... (add backend-specific instructions here)
