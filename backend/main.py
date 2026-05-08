"""FastAPI server exposing the Travel Planner agent."""
from __future__ import annotations
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from travel_agent import plan_trip

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("travel-planner")

app = FastAPI(title="Travel Planner Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    pax: int = Field(..., ge=1, le=20)
    start_date: str = Field(..., description="ISO date YYYY-MM-DD")
    end_date: str = Field(..., description="ISO date YYYY-MM-DD")
    destination: str = Field(..., min_length=2)
    origin: str = Field("BLR", description="IATA code or city")


class PlanResponse(BaseModel):
    markdown: str
    tokens: dict[str, int] = Field(default_factory=dict)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/plan", response_model=PlanResponse)
async def plan(req: PlanRequest) -> PlanResponse:
    log.info("plan request: %s", req.model_dump())
    try:
        markdown, tokens = await plan_trip(
            pax=req.pax,
            start_date=req.start_date,
            end_date=req.end_date,
            destination=req.destination,
            origin=req.origin,
        )
    except Exception as e:  # noqa: BLE001
        log.exception("plan failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return PlanResponse(markdown=markdown, tokens=tokens)
