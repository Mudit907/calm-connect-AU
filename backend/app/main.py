"""
CalmConnect API — FastAPI service wrapping the v2 recommender.

Endpoints:
  GET  /health               liveness check (also reports whether ML
                              artifacts are present, since v2 fails loudly
                              rather than silently degrading if untrained)
  POST /recommend             main recommendation endpoint, requires a
                              client-generated session_id
  GET  /history/{session_id}  this session's logged interactions, for the
                              trend view — see app/db.py for what
                              "session_id" does and does not mean
  GET  /crisis-resources       AU crisis support info (always available, no model needed)

Every /recommend call is written to a SQLite database (app/db.py),
tagged with the caller-supplied session_id. There is no authentication
and no link between a session_id and any real identity — it is a random
token the frontend generates and stores client-side. If a person clears
their browser storage, their history is gone; this is a stated, deliberate
privacy property (see README.md), not a bug to fix later.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.db import get_session_history, init_db, log_interaction
from app.recommender import ML_ARTIFACT_DIR, get_au_season, recommend


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CalmConnect Recommender API",
    description=(
        "Mood- and context-aware therapy recommendation service, backed by a "
        "trained mental-health category classifier and a dedicated, "
        "recall-tuned escalation trigger. See ml/DESIGN.md and "
        "ml/ESCALATION_LADDER.md in the repo for the full modeling writeup."
    ),
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mudit907.github.io", "http://localhost:5500", "http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=128, description="Client-generated anonymous session token")
    age: int = Field(..., ge=10, le=110, description="User age in years")
    text: str = Field(..., min_length=1, max_length=1000, description="Free-text mood description")


class TherapyScore(BaseModel):
    id: str
    label: str
    score: float
    page: str


class RecommendResponse(BaseModel):
    category: str
    category_confidence: float
    season: str
    ranked: list[TherapyScore]
    escalation_flag: bool
    escalation_probability: float


class HistoryPoint(BaseModel):
    timestamp_utc: str
    category: str
    category_confidence: float
    escalation_flag: bool
    escalation_probability: float
    season: str
    top_recommendation: str


AU_CRISIS_RESOURCES = {
    "lifeline": {"name": "Lifeline Australia", "phone": "13 11 14", "available": "24/7"},
    "beyond_blue": {"name": "Beyond Blue", "phone": "1300 22 4636", "available": "24/7"},
    "kids_helpline": {"name": "Kids Helpline", "phone": "1800 55 1800", "available": "24/7, for under 25s"},
    "emergency": {"name": "Emergency services", "phone": "000", "available": "24/7"},
}


def _models_present() -> bool:
    return (
        os.path.exists(os.path.join(ML_ARTIFACT_DIR, "category_classifier.joblib"))
        and os.path.exists(os.path.join(ML_ARTIFACT_DIR, "escalation_trigger.joblib"))
    )


@app.get("/health")
def health():
    return {
        "status": "ok" if _models_present() else "degraded - ML models not trained",
        "current_au_season": get_au_season(),
        "models_trained": _models_present(),
    }


@app.get("/crisis-resources")
def crisis_resources():
    return AU_CRISIS_RESOURCES


@app.post("/recommend", response_model=RecommendResponse)
def post_recommend(req: RecommendRequest):
    if not _models_present():
        raise HTTPException(
            status_code=503,
            detail=(
                "ML models not trained yet. Run the pipeline in backend/ml/ "
                "(see backend/ml/run_pipeline.sh) before calling /recommend."
            ),
        )

    try:
        result = recommend(age=req.age, text=req.text)
    except Exception as exc:  # surfaced as 500, not silently swallowed
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {exc}")

    log_interaction(req.session_id, req.age, req.text, result)

    return RecommendResponse(
        category=result.category,
        category_confidence=result.category_confidence,
        season=result.season,
        ranked=result.ranked,
        escalation_flag=result.escalation_flag,
        escalation_probability=result.escalation_probability,
    )


@app.get("/history/{session_id}", response_model=list[HistoryPoint])
def get_history(session_id: str):
    rows = get_session_history(session_id)
    return [
        HistoryPoint(
            timestamp_utc=r["timestamp_utc"],
            category=r["category"],
            category_confidence=r["category_confidence"],
            escalation_flag=bool(r["escalation_flag"]),
            escalation_probability=r["escalation_probability"],
            season=r["season"],
            top_recommendation=r["top_recommendation"],
        )
        for r in rows
    ]
