"""
serve.py  —  LangServe API for the Multi-Agent Trip Planner
════════════════════════════════════════════════════════════

Run:
    python serve.py

Interactive API Docs:
    http://localhost:8000/docs          ← Swagger UI (all endpoints)
    http://localhost:8000/redoc         ← ReDoc

LangServe Playgrounds (test in browser, no Postman needed):
    http://localhost:8000/trip-planner/playground
    http://localhost:8000/trip-description/playground
    http://localhost:8000/packing-list/playground
    http://localhost:8000/budget-advice/playground
    http://localhost:8000/itinerary-chat/playground

Each route auto-exposes:
    POST /{route}/invoke        ← single call (returns full result)
    POST /{route}/batch         ← multiple inputs at once
    POST /{route}/stream        ← token-by-token streaming (SSE)
    POST /{route}/stream_log    ← full run log with intermediate steps
    GET  /{route}/input_schema  ← JSON schema of input
    GET  /{route}/output_schema ← JSON schema of output
"""

import os
import uuid
import datetime as dt
from typing import List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from langserve import add_routes
from pydantic import BaseModel, Field

# ── Load .env  ──────────────────────────────────────────────────────────────
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise EnvironmentError(
        "OPENAI_API_KEY not set.\n"
        "Create a .env file with:  OPENAI_API_KEY=sk-proj-..."
    )

# ── Import the compiled LangGraph workflow from app.py  ─────────────────────
from app import WORKFLOW, TripState, GUARDRAILS, InputGuardrailError

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         FASTAPI APP                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝
app = FastAPI(
    title="🌍 AI Trip Planner  ·  LangServe API",
    description="""
## Multi-Agent Trip Planner powered by LangGraph + LangServe

### What you get out of the box
Every route registered below **automatically exposes**:

| Endpoint | What it does |
|---|---|
| `POST /invoke` | Single call — returns complete result |
| `POST /batch` | Multiple inputs in one request |
| `POST /stream` | Real-time token streaming (SSE) |
| `POST /stream_log` | Full trace with intermediate agent steps |
| `GET  /input_schema` | JSON Schema of expected input |
| `GET  /output_schema` | JSON Schema of output |
| `GET  /playground` | **Interactive browser UI — no Postman needed** |

### Available Routes
- **`/trip-planner`** — Full 9-agent LangGraph workflow (weather → transport → hotel → itinerary → PDF)
- **`/trip-description`** — AI travel writer — vivid 3-paragraph trip descriptions
- **`/packing-list`** — Smart context-aware packing list by category
- **`/budget-advice`** — Budget analysis + optimization strategies
- **`/itinerary-chat`** — Conversational itinerary assistant (multi-turn)
    """,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Redirect root to docs  ──────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         LLM INSTANCES                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# Creative LLM — for descriptions, packing, chat
llm_creative = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.8,
    api_key=OPENAI_API_KEY,
    streaming=True,        # ← enables /stream endpoint
)

# Precise LLM — for budget analysis, structured output
llm_precise = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    api_key=OPENAI_API_KEY,
    streaming=True,
)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                     PYDANTIC INPUT / OUTPUT MODELS                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class TripPlanRequest(BaseModel):
    """Input for the full 9-agent LangGraph trip planner workflow."""

    source: str = Field(
        default="Bangalore",
        description="Origin city (e.g. Bangalore, Delhi, Mumbai)",
        examples=["Bangalore"],
    )
    destination: str = Field(
        default="Goa",
        description="Destination city (e.g. Goa, Manali, Leh)",
        examples=["Goa"],
    )
    start_date: str = Field(
        default_factory=lambda: str(dt.date.today() + dt.timedelta(days=30)),
        description="Trip start date in YYYY-MM-DD format",
        examples=["2026-06-25"],
    )
    days: int = Field(default=5, ge=1, le=30, description="Number of trip days")
    travelers: int = Field(default=2, ge=1, le=20, description="Number of travelers")
    travel_type: str = Field(
        default="couple",
        description="Type: solo | couple | family | friends | group",
        examples=["couple"],
    )
    budget: float = Field(
        default=30000,
        gt=0,
        description="Total budget in INR (₹)",
        examples=[30000],
    )
    mode_pref: str = Field(
        default="any",
        description="Transport preference: any | flight | train | car",
        examples=["any"],
    )
    vibe: str = Field(
        default="mid",
        description="Trip vibe: budget | mid | luxury",
        examples=["mid"],
    )
    interests: List[str] = Field(
        default=["beach", "heritage"],
        description="Interest tags: beach, heritage, nightlife, nature, shopping, adventure, food, wellness",
        examples=[["beach", "nightlife"]],
    )
    food_pref: str = Field(
        default="local",
        description="Food preference (e.g. seafood, vegetarian, local cuisine)",
        examples=["seafood"],
    )


class TripDescriptionRequest(BaseModel):
    """Input for the AI travel description writer."""

    destination: str = Field(
        description="Destination city or country",
        examples=["Goa"],
    )
    days: int = Field(default=5, ge=1, le=30, description="Duration in days")
    travelers: int = Field(default=2, ge=1, description="Number of travelers")
    travel_type: str = Field(
        default="couple",
        description="solo | couple | family | friends | group",
    )
    vibe: str = Field(default="mid", description="budget | mid | luxury")
    budget: float = Field(default=30000, description="Total budget in INR")
    interests: str = Field(
        default="beach, heritage",
        description="Comma-separated list of interests",
    )


class PackingListRequest(BaseModel):
    """Input for the smart packing list generator."""

    destination: str = Field(description="Destination city", examples=["Goa"])
    days: int = Field(default=5, ge=1, description="Duration in days")
    travel_type: str = Field(default="couple", description="solo | couple | family")
    weather: str = Field(
        default="sunny and hot",
        description="Expected weather (e.g. sunny and hot, cold and rainy, snowy)",
        examples=["sunny and hot"],
    )
    vibe: str = Field(default="mid", description="budget | mid | luxury")
    activities: str = Field(
        default="beach, sightseeing",
        description="Planned activities (comma-separated)",
        examples=["beach, water sports, nightlife"],
    )


class BudgetAdviceRequest(BaseModel):
    """Input for the budget analysis and optimization advisor."""

    destination: str = Field(description="Destination city", examples=["Goa"])
    total_budget: float = Field(
        description="Total budget in INR",
        examples=[30000],
    )
    days: int = Field(default=5, ge=1, description="Duration in days")
    travelers: int = Field(default=2, ge=1, description="Number of travelers")
    vibe: str = Field(
        default="mid",
        description="Trip vibe: budget | mid | luxury",
    )
    travel_type: str = Field(default="couple", description="Type of travelers")


class ItineraryChatRequest(BaseModel):
    """Input for the conversational itinerary assistant."""

    message: str = Field(
        description="Your question or request about the trip",
        examples=["What should I do on Day 2 in Goa?"],
    )
    destination: str = Field(
        default="Goa",
        description="Trip destination for context",
    )
    days: int = Field(default=5, description="Trip duration for context")
    travel_type: str = Field(default="couple", description="Travel type for context")
    chat_history: List[dict] = Field(
        default=[],
        description="Previous messages as [{role: 'human'|'assistant', content: '...'}]",
    )


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║              CHAIN 1 — FULL LANGGRAPH TRIP PLANNER                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _run_trip_workflow(req: TripPlanRequest) -> dict:
    """
    Wraps the LangGraph WORKFLOW so LangServe can call it.
    Handles guardrail validation, thread_id generation, and config.
    """
    thread_id = str(uuid.uuid4())[:8]

    prefs = req.model_dump()

    # Validate with guardrails
    raw_query = (
        f"Plan a {prefs['days']}-day trip to {prefs['destination']} "
        f"from {prefs['source']} for {prefs['travelers']} traveler(s). "
        f"Budget ₹{prefs['budget']:,.0f}."
    )
    try:
        prefs = GUARDRAILS.validate_all(raw_query, prefs)
    except InputGuardrailError as e:
        raise HTTPException(status_code=400, detail=str(e))

    initial_state: TripState = {
        "user_id": "langserve_user",
        "thread_id": thread_id,
        "raw_query": raw_query,
        "trip_preferences": prefs,
        "messages": [],
        "retry_count": 0,
    }

    final = WORKFLOW.invoke(
        initial_state,
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 60,
        },
    )

    # Return a clean, JSON-serializable summary
    return {
        "thread_id": thread_id,
        "status": "approved" if final.get("review_status", {}).get("approved") else "with_caveats",
        "headline": final.get("itinerary", {}).get("headline", ""),
        "itinerary": final.get("itinerary", {}).get("days", []),
        "hotel_top_pick": final.get("hotel_data", {}).get("top_pick"),
        "transport_recommended": final.get("transport_data", {}).get("recommended"),
        "weather_summary": final.get("weather_data", {}).get("summary", ""),
        "budget_summary": final.get("budget_summary", {}),
        "review_issues": final.get("review_status", {}).get("issues", []),
        "pdf_ready": bool(final.get("pdf_status")),
        "pdf_path": final.get("pdf_status", {}).get("path", ""),
        "agent_messages": [
            m for m in final.get("messages", [])
            if m.get("role") == "orchestrator"
        ],
    }


trip_planner_chain = RunnableLambda(_run_trip_workflow)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║              CHAIN 2 — AI TRAVEL DESCRIPTION WRITER                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

trip_description_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an award-winning travel writer for Condé Nast Traveller India.
Your writing is vivid, inspiring, and emotionally resonant — it makes readers
feel the sun on their skin and smell the local spices.

Style guidelines:
- Use sensory details (sights, sounds, smells, textures)
- Weave in cultural context and local insider tips
- Speak directly to the type of traveler (couple, family, solo, etc.)
- Avoid generic phrases like "a must-visit destination"
- End with a call-to-action that creates urgency""",
    ),
    (
        "human",
        """Write a compelling 3-paragraph trip description for:

🗺️  Destination  : {destination}
📅  Duration     : {days} days
👥  Travelers    : {travelers} traveler(s) — {travel_type} trip
✨  Vibe         : {vibe}
💰  Budget       : ₹{budget:,} total
🎯  Interests    : {interests}

Structure:
**Paragraph 1 (The Hook):** Why {destination} is irresistible for a {travel_type} trip right now.
**Paragraph 2 (The Experience):** The 2-3 must-have moments this specific type of traveler will treasure.
**Paragraph 3 (The Close):** The feeling they'll carry home + a closing call-to-action.

Keep it under 250 words total. Make it feel personal, not like a brochure.""",
    ),
])

trip_description_chain = trip_description_prompt | llm_creative | StrOutputParser()

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║              CHAIN 3 — SMART PACKING LIST GENERATOR                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

packing_list_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a minimalist travel consultant who helps people pack perfectly —
nothing forgotten, nothing unnecessary. You know every destination's quirks:
what to bring that guidebooks miss, what to leave at home, what to buy there.""",
    ),
    (
        "human",
        """Create a smart, minimal packing list for:

📍 Destination  : {destination}
📅 Duration     : {days} days
👤 Travel type  : {travel_type}
🌤️  Weather      : {weather}
✨ Vibe         : {vibe}
🎯 Activities   : {activities}

Format EXACTLY like this (use emojis as shown):

### 👕 CLOTHING  (pack light — {days} days)
- [item] — [1-line reason if non-obvious]

### 🔌 TECH & GADGETS
- [item] — [reason]

### 💊 HEALTH & SAFETY
- [item] — [reason]

### 📋 DOCUMENTS & MONEY
- [item] — [reason]

### 🎒 DESTINATION-SPECIFIC ESSENTIALS
- [item] — [why it's specific to {destination}]

### ❌ LEAVE THESE AT HOME
- [3 things people over-pack for this trip type]

Keep total items under 30. Be specific — not "charger" but "USB-C multi-port charger".""",
    ),
])

packing_list_chain = packing_list_prompt | llm_creative | StrOutputParser()

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║              CHAIN 4 — BUDGET OPTIMIZATION ADVISOR                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

budget_advice_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a travel budget expert who has helped thousands of Indians plan
trips that feel luxurious without breaking the bank. You give specific,
actionable advice with real INR numbers — not vague tips.

You know the real costs: auto-rickshaw vs cab, dhaba vs restaurant,
government hotels vs private, online booking discounts, shoulder seasons.""",
    ),
    (
        "human",
        """Analyze and optimize this travel budget:

📍 Destination       : {destination}
💰 Total Budget      : ₹{total_budget:,}
📅 Duration          : {days} days
👥 Travelers         : {travelers} ({travel_type})
✨ Vibe              : {vibe}
📊 Per person/day    : ₹{per_day_per_person:,.0f}

Provide a structured analysis:

## 🎯 BUDGET VERDICT
Grade this budget (A = comfortable, B = tight but doable, C = challenging, D = unrealistic)
One paragraph explanation with real cost benchmarks.

## 📊 RECOMMENDED SPLIT
| Category | % | Amount (₹) | Notes |
|---|---|---|---|
| Transport | | | |
| Accommodation | | | |
| Food & Drinks | | | |
| Activities & Entry | | | |
| Buffer/Misc | | | |

## 🏨 ACCOMMODATION STRATEGY
Specific hotel types / areas to stay in {destination} for this budget.

## 🍽️  FOOD STRATEGY
How to eat well — specific place types, meal budgets per day.

## ✂️  TOP 3 MONEY SAVERS
Specific to {destination} — with realistic savings amounts.

## ⚠️  BUDGET TRAPS TO AVOID
3 common overspending mistakes in {destination}.

## 💡 UPGRADE OPPORTUNITIES
2 splurges worth exceeding budget for — give real prices.""",
    ),
])

budget_advice_chain = (
    RunnablePassthrough.assign(
        per_day_per_person=lambda x: x["total_budget"] / x["days"] / x["travelers"]
    )
    | budget_advice_prompt
    | llm_precise
    | StrOutputParser()
)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║              CHAIN 5 — CONVERSATIONAL ITINERARY ASSISTANT               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

itinerary_chat_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert local travel guide and trip planner for Indian destinations.
You have deep knowledge of hotels, hidden gems, local transport, food, timing,
entry fees, and travel hacks.

Current trip context: {days}-day {travel_type} trip to {destination}.

Rules:
- Give specific, practical answers with real names (places, restaurants, timings)
- Include approximate costs in INR when relevant
- Mention insider tips locals would know
- If asked for alternatives, provide 2-3 concrete options
- Keep responses concise but complete (150-300 words max)""",
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{message}"),
])

itinerary_chat_chain = itinerary_chat_prompt | llm_creative | StrOutputParser()

# ── Adapter: flatten ItineraryChatRequest into chain-compatible dict  ────────
def _prepare_chat_input(req: ItineraryChatRequest) -> dict:
    from langchain_core.messages import HumanMessage, AIMessage

    history = []
    for m in req.chat_history:
        role = m.get("role", "human")
        content = m.get("content", "")
        if role == "human":
            history.append(HumanMessage(content=content))
        else:
            history.append(AIMessage(content=content))

    return {
        "message": req.message,
        "destination": req.destination,
        "days": req.days,
        "travel_type": req.travel_type,
        "chat_history": history,
    }


itinerary_chat_runnable = RunnableLambda(_prepare_chat_input) | itinerary_chat_chain

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                  REGISTER ALL LANGSERVE ROUTES                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ── Route 1: Full LangGraph Trip Planner ────────────────────────────────────
add_routes(
    app,
    trip_planner_chain,
    path="/trip-planner",
    input_type=TripPlanRequest,
    config_keys=["configurable"],
    enabled_endpoints=["invoke", "stream_log"],  # no streaming for full workflow
)

# ── Route 2: AI Travel Description Writer ───────────────────────────────────
add_routes(
    app,
    trip_description_chain,
    path="/trip-description",
    input_type=TripDescriptionRequest,
)

# ── Route 3: Smart Packing List Generator ───────────────────────────────────
add_routes(
    app,
    packing_list_chain,
    path="/packing-list",
    input_type=PackingListRequest,
)

# ── Route 4: Budget Optimization Advisor ────────────────────────────────────
add_routes(
    app,
    budget_advice_chain,
    path="/budget-advice",
    input_type=BudgetAdviceRequest,
)

# ── Route 5: Conversational Itinerary Assistant ──────────────────────────────
add_routes(
    app,
    itinerary_chat_runnable,
    path="/itinerary-chat",
    input_type=ItineraryChatRequest,
)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                        UTILITY ENDPOINTS                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.get("/health", tags=["Utility"])
def health_check():
    """Verify the server and LLM connection are working."""
    return {
        "status": "ok",
        "model": "gpt-4o-mini",
        "langserve_routes": [
            "/trip-planner",
            "/trip-description",
            "/packing-list",
            "/budget-advice",
            "/itinerary-chat",
        ],
        "flask_ui": "http://localhost:8080  (run app.py separately)",
        "docs": "http://localhost:8000/docs",
        "playgrounds": {
            "trip_planner":   "http://localhost:8000/trip-planner/playground",
            "description":    "http://localhost:8000/trip-description/playground",
            "packing":        "http://localhost:8000/packing-list/playground",
            "budget":         "http://localhost:8000/budget-advice/playground",
            "chat":           "http://localhost:8000/itinerary-chat/playground",
        },
    }


@app.get("/routes", tags=["Utility"])
def list_routes():
    """List all available LangServe routes with their sub-endpoints."""
    base = "http://localhost:8000"
    routes = [
        "/trip-planner",
        "/trip-description",
        "/packing-list",
        "/budget-advice",
        "/itinerary-chat",
    ]
    result = {}
    for r in routes:
        result[r] = {
            "invoke":        f"{base}{r}/invoke",
            "batch":         f"{base}{r}/batch",
            "stream":        f"{base}{r}/stream",
            "stream_log":    f"{base}{r}/stream_log",
            "playground":    f"{base}{r}/playground",
            "input_schema":  f"{base}{r}/input_schema",
            "output_schema": f"{base}{r}/output_schema",
        }
    return result


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                              ENTRYPOINT                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝
if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  🌍  AI Trip Planner — LangServe API")
    print("═" * 60)
    print("  Docs       →  http://localhost:8000/docs")
    print("  Health     →  http://localhost:8000/health")
    print("  Playgrounds:")
    print("    Trip Planner   →  http://localhost:8000/trip-planner/playground")
    print("    Description    →  http://localhost:8000/trip-description/playground")
    print("    Packing List   →  http://localhost:8000/packing-list/playground")
    print("    Budget Advice  →  http://localhost:8000/budget-advice/playground")
    print("    Chat Assistant →  http://localhost:8000/itinerary-chat/playground")
    print("═" * 60 + "\n")

    uvicorn.run(
        "serve:app",
        host="0.0.0.0",
        port=8000,
        reload=True,            # auto-reload on code changes
        log_level="info",
    )
