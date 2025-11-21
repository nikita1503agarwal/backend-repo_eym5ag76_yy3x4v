import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents

app = FastAPI(title="Men's Tration API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CycleRequest(BaseModel):
    partner_name: Optional[str] = None
    cycle_start: str
    cycle_length: int = 28


PHASES = [
    (0, 5, "period", "Menstruation"),
    (6, 13, "follicular", "Follicular"),
    (14, 15, "ovulation", "Ovulation"),
    (16, 27, "luteal", "Luteal"),
]


def parse_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Date must be YYYY-MM-DD")


def day_in_cycle(cycle_start: datetime, cycle_length: int, target_date: datetime) -> int:
    delta_days = (target_date - cycle_start).days % cycle_length
    return delta_days


def phase_for_day(day_index: int) -> str:
    for start, end, key, _ in PHASES:
        if start <= day_index <= end:
            return key
    return "luteal"


@app.get("/")
def read_root():
    return {"message": "Men's Tration backend is running"}


@app.post("/api/cycle/calculate")
def calculate_cycle(data: CycleRequest):
    start = parse_date(data.cycle_start)
    today = datetime.utcnow()
    idx = day_in_cycle(start, data.cycle_length, today)
    phase = phase_for_day(idx)

    # Next predicted dates
    next_start = start
    while next_start + timedelta(days=data.cycle_length) <= today:
        next_start += timedelta(days=data.cycle_length)
    next_period_start = next_start if next_start >= today else next_start + timedelta(days=data.cycle_length)

    return {
        "today": today.strftime("%Y-%m-%d"),
        "day_in_cycle": idx,
        "phase": phase,
        "next_period_start": next_period_start.strftime("%Y-%m-%d"),
        "cycle_length": data.cycle_length,
    }


@app.get("/api/ideas")
def get_ideas(phase: Optional[str] = None, limit: int = 20):
    filter_dict = {"phase": phase} if phase else {}
    try:
        docs = get_documents("idea", filter_dict=filter_dict, limit=limit)
    except Exception:
        # Fallback seeded ideas if DB not connected
        docs = [
            {"phase": "period", "title": "Comfort kit", "description": "Heat pad, chocolate, tea, low-key movie night"},
            {"phase": "period", "title": "Take chores off her plate", "description": "Run errands, cook, tidy up without being asked"},
            {"phase": "follicular", "title": "Plan a fun date", "description": "She may feel more energetic—try a new activity together"},
            {"phase": "ovulation", "title": "Hype her up", "description": "Compliments and quality time—she'll likely feel confident"},
            {"phase": "luteal", "title": "Gentle support", "description": "Be patient, offer snacks, suggest cozy plans"},
        ]
    # Convert ObjectId and internal fields if any
    for d in docs:
        d.pop("_id", None)
        d.pop("created_at", None)
        d.pop("updated_at", None)
    return {"items": docs}


class ExplainResponse(BaseModel):
    phase: str
    summary: str
    tips: List[str]


@app.get("/api/explain", response_model=ExplainResponse)
def explain(phase: str):
    phase = phase.lower()
    summaries = {
        "period": "Bleeding phase. Energy may be lower; comfort and patience go a long way.",
        "follicular": "Rising hormones and energy. Great for plans, workouts, creativity.",
        "ovulation": "Peak fertility. Confidence and social energy often highest.",
        "luteal": "PMS window. Sensitivity may rise—opt for calm, reassurance, and help.",
    }
    tips_map = {
        "period": [
            "Offer heat pad, cozy foods, and space if needed",
            "Keep plans flexible and low-pressure",
            "Proactively handle chores and logistics",
        ],
        "follicular": [
            "Suggest a new activity or date",
            "Encourage goals and celebrate progress",
            "Share optimistic plans—she may be more up for it",
        ],
        "ovulation": [
            "Give genuine compliments—she may feel her best",
            "Plan social time or a dress-up night",
            "Be playful and confident",
        ],
        "luteal": [
            "Be patient; validate feelings without fixing right away",
            "Keep snacks and water handy; offer gentle support",
            "Avoid big conflicts—focus on comfort and reassurance",
        ],
    }
    if phase not in summaries:
        raise HTTPException(status_code=400, detail="Invalid phase. Use: period, follicular, ovulation, luteal")
    return ExplainResponse(phase=phase, summary=summaries[phase], tips=tips_map[phase])


@app.get("/test")
def test_database():
    from database import db
    status = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            status["database"] = "✅ Available"
            status["database_url"] = "✅ Set"
            status["database_name"] = getattr(db, "name", "✅ Connected")
            status["connection_status"] = "Connected"
            try:
                status["collections"] = db.list_collection_names()[:10]
                status["database"] = "✅ Connected & Working"
            except Exception as e:
                status["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
    except Exception as e:
        status["database"] = f"❌ Error: {str(e)[:50]}"
    import os
    status["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    status["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return status


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
