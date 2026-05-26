"""
app.py — Flask web interface for the Multi-Agent Trip Planner
Run:    python app.py
Open:   http://localhost:8080

LangServe API runs separately:
    python serve.py  →  http://localhost:8000/docs
"""
import os, uuid, json, datetime as dt, random, operator, re
from typing import TypedDict, List, Dict, Any, Annotated
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file

# Load .env (OPENAI_API_KEY, etc.) — must come before any os.environ.get()
from dotenv import load_dotenv
load_dotenv()

# ── ReportLab ─────────────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak)

# ── LangGraph ─────────────────────────────────────────────────────────────────
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

random.seed(42)
np.random.seed(42)

# ═══════════════════════════════════════════════════════════════════════════════
#  STATE
# ═══════════════════════════════════════════════════════════════════════════════
class TripState(TypedDict, total=False):
    user_id: str
    thread_id: str
    messages: Annotated[List[dict], operator.add]
    raw_query: str
    trip_preferences: Dict[str, Any]
    user_profile: Dict[str, Any]
    weather_data: Dict[str, Any]
    transport_data: Dict[str, Any]
    hotel_data: Dict[str, Any]
    places_data: Dict[str, Any]
    budget_summary: Dict[str, Any]
    itinerary: Dict[str, Any]
    review_status: Dict[str, Any]
    orchestrator_decision: Dict[str, Any]
    pdf_status: Dict[str, Any]
    retry_count: int

# ═══════════════════════════════════════════════════════════════════════════════
#  LLM WRAPPER
# ═══════════════════════════════════════════════════════════════════════════════
USE_REAL_LLM = bool(os.environ.get("OPENAI_API_KEY"))
if USE_REAL_LLM:
    from langchain_openai import ChatOpenAI
    _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

def llm_call(system: str, user: str) -> str:
    if USE_REAL_LLM:
        from langchain_core.messages import SystemMessage, HumanMessage
        return _llm.invoke([SystemMessage(content=system),
                            HumanMessage(content=user)]).content
    text = (system + " || " + user).lower()
    if "itinerary" in text or "day-wise" in text:
        return ("Day 1: Arrive, check-in, explore. "
                "Day 2: Main sights + local cuisine. "
                "Day 3: Day trip or adventure. "
                "Day 4: Shopping & culture. "
                "Day 5: Leisure & depart.")
    if "review" in text or "approve" in text:
        return '{"approved": true, "issues": []}'
    if "packing" in text:
        return "Sunscreen; comfortable shoes; camera; power bank; light clothes; ID proof."
    if "summary" in text or "headline" in text:
        return "A well-planned trip with great experiences ahead."
    return "Acknowledged."

# ═══════════════════════════════════════════════════════════════════════════════
#  GUARDRAILS
# ═══════════════════════════════════════════════════════════════════════════════
class InputGuardrailError(ValueError):
    pass

class InputGuardrails:
    VALID_MODES  = {"flight", "train", "car", "any"}
    VALID_VIBES  = {"luxury", "mid", "budget"}
    VALID_TYPES  = {"solo", "couple", "family", "friends", "group"}
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"forget\s+(everything|all|your)\s+(you\s+know|instructions|prompt)",
        r"you\s+are\s+now\s+(?:a|an)\s+",
        r"<\s*script[^>]*>",
        r"system\s*:.*override",
    ]
    MIN_BUDGET_PER_PERSON_PER_DAY = 300
    MAX_DAYS = 30; MAX_TRAVELERS = 20; MAX_QUERY_LEN = 2000

    def validate_all(self, raw_query: str, prefs: dict) -> dict:
        self._check_raw_query(raw_query)
        sanitised = self._check_preferences(prefs)
        self._check_business_rules(sanitised)
        return sanitised

    def _check_raw_query(self, query: str):
        if not isinstance(query, str) or not query.strip():
            raise InputGuardrailError("Query must be a non-empty string.")
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, query.lower(), re.IGNORECASE):
                raise InputGuardrailError("Input rejected: possible injection pattern detected.")
        if len(query) > self.MAX_QUERY_LEN:
            raise InputGuardrailError(f"Query too long (max {self.MAX_QUERY_LEN} chars).")

    def _check_preferences(self, prefs: dict) -> dict:
        s = dict(prefs); errors = []
        if "days" in s:
            try: s["days"] = int(s["days"])
            except: errors.append("'days' must be an integer.")
            else:
                if not (1 <= s["days"] <= self.MAX_DAYS):
                    errors.append(f"'days' must be 1–{self.MAX_DAYS}.")
        if "travelers" in s:
            try: s["travelers"] = int(s["travelers"])
            except: errors.append("'travelers' must be an integer.")
        if "budget" in s:
            try: s["budget"] = float(s["budget"])
            except: errors.append("'budget' must be a number.")
        if "start_date" in s:
            try:
                trip_date = dt.date.fromisoformat(str(s["start_date"]))
                if trip_date < dt.date.today():
                    errors.append("'start_date' is in the past.")
                s["start_date"] = str(trip_date)
            except: errors.append("'start_date' must be YYYY-MM-DD.")
        if "mode_pref" in s and str(s["mode_pref"]).lower() not in self.VALID_MODES:
            errors.append(f"'mode_pref' must be one of {sorted(self.VALID_MODES)}.")
        if "vibe" in s and str(s["vibe"]).lower() not in self.VALID_VIBES:
            errors.append(f"'vibe' must be one of {sorted(self.VALID_VIBES)}.")
        if "travel_type" in s and str(s["travel_type"]).lower() not in self.VALID_TYPES:
            errors.append(f"'travel_type' must be one of {sorted(self.VALID_TYPES)}.")
        if errors:
            raise InputGuardrailError("Validation failed: " + " | ".join(errors))
        return s

    def _check_business_rules(self, prefs: dict):
        src = prefs.get("source", "").lower().strip()
        dst = prefs.get("destination", "").lower().strip()
        if src and dst and src == dst:
            raise InputGuardrailError("Source and destination cannot be the same city.")
        budget = prefs.get("budget", 0)
        days   = prefs.get("days", 1)
        travelers = prefs.get("travelers", 1)
        if budget and days and travelers:
            floor = self.MIN_BUDGET_PER_PERSON_PER_DAY * days * travelers
            if budget < floor:
                raise InputGuardrailError(
                    f"Budget ₹{budget:,.0f} is too low. "
                    f"Minimum for {travelers} traveller(s) over {days} day(s): ₹{floor:,}.")

GUARDRAILS = InputGuardrails()

# ═══════════════════════════════════════════════════════════════════════════════
#  TOOLS
# ═══════════════════════════════════════════════════════════════════════════════
def tool_get_weather(city: str, start: str, days: int) -> Dict[str, Any]:
    base_temp = {"goa": 30, "manali": 14, "leh": 8, "ooty": 18,
                 "jaipur": 32, "shimla": 16, "kerala": 29,
                 "bangalore": 25, "mumbai": 30, "delhi": 28}.get(city.lower(), 25)
    rng = random.Random(hash(city + start))
    forecast = []
    d0 = dt.date.fromisoformat(start)
    for i in range(days):
        cond = rng.choice(["sunny", "sunny", "partly cloudy", "light rain"])
        forecast.append({
            "date": (d0 + dt.timedelta(days=i)).isoformat(),
            "high_c": base_temp + rng.randint(-2, 4),
            "low_c":  base_temp - rng.randint(4, 8),
            "conditions": cond,
            "icon": "☀️" if "sunny" in cond else "⛅" if "cloudy" in cond else "🌧️",
        })
    rain_days = sum(1 for f in forecast if "rain" in f["conditions"])
    return {"city": city, "forecast": forecast,
            "summary": f"Mostly pleasant; {rain_days} day(s) of light rain expected."}

def tool_search_transport(origin: str, dest: str, date: str, mode_pref: str) -> Dict[str, Any]:
    rng = random.Random(hash(origin + dest + date))
    base = {("bangalore","goa"):4500,("delhi","goa"):6500,("mumbai","goa"):3000,
            ("madurai","bangalore"):3200,("chennai","goa"):5000}.get(
                (origin.lower(), dest.lower()), 5500)
    options = []
    if mode_pref in ("any","flight"):
        options += [
            {"mode":"flight","provider":"IndiGo",    "depart":"07:00","arrive":"08:25","price":base,      "icon":"✈️"},
            {"mode":"flight","provider":"Air India",  "depart":"10:15","arrive":"11:50","price":base+800,  "icon":"✈️"},
        ]
    if mode_pref in ("any","train"):
        options.append({"mode":"train","provider":"Express Train","depart":"20:30","arrive":"10:15+1",
                        "price":int(base*0.4),"icon":"🚂"})
    if mode_pref in ("any","car"):
        options.append({"mode":"car","provider":"Self-drive","depart":"06:00","arrive":"16:00",
                        "price":int(base*0.6),"icon":"🚗"})
    options.sort(key=lambda x: x["price"])
    return {"origin": origin, "destination": dest, "options": options,
            "recommended": options[0] if options else {}}

def tool_search_hotels(city: str, checkin: str, checkout: str,
                       budget_per_night: int, vibe: str) -> Dict[str, Any]:
    catalog = {
        "goa": [
            {"name":"Taj Fort Aguada",    "stars":5,"price":12000,"tags":["beach","luxury","pool"],"img":"🏖️"},
            {"name":"The Leela Goa",      "stars":5,"price":18000,"tags":["beach","luxury","spa"], "img":"🌴"},
            {"name":"Lemon Tree Candolim","stars":4,"price":5500, "tags":["beach","mid","nightlife"],"img":"🍋"},
            {"name":"Cidade de Goa",      "stars":4,"price":7200, "tags":["beach","couple"],        "img":"🏨"},
            {"name":"Backwoods Hostel",   "stars":2,"price":1200, "tags":["budget","solo"],         "img":"🏕️"},
        ],
        "manali": [
            {"name":"Span Resort",       "stars":5,"price":8000, "tags":["mountain","luxury"],"img":"⛰️"},
            {"name":"Johnson Hotel",     "stars":4,"price":4500, "tags":["mountain","mid"],   "img":"🏔️"},
            {"name":"Snow Valley",       "stars":3,"price":2500, "tags":["budget"],           "img":"❄️"},
        ],
    }
    hotels = catalog.get(city.lower(), [
        {"name":f"{city} Grand",    "stars":4,"price":4500,"tags":["mid"],    "img":"🏨"},
        {"name":f"{city} Heritage", "stars":3,"price":2500,"tags":["budget"], "img":"🏛️"},
    ])
    filt = [h for h in hotels if h["price"] <= budget_per_night]
    if not filt: filt = sorted(hotels, key=lambda h: h["price"])[:2]
    if vibe == "luxury":   filt = sorted(filt, key=lambda h: -h["stars"])
    elif vibe == "budget": filt = sorted(filt, key=lambda h: h["price"])
    return {"city": city, "candidates": filt[:5], "top_pick": filt[0] if filt else None}

def tool_explore_places(city: str, interests: List[str]) -> Dict[str, Any]:
    db = {
        "goa": [
            {"name":"Baga Beach",        "category":"beach",    "rating":4.5,"icon":"🏖️"},
            {"name":"Calangute Beach",   "category":"beach",    "rating":4.4,"icon":"🏖️"},
            {"name":"Fort Aguada",       "category":"heritage", "rating":4.3,"icon":"🏰"},
            {"name":"Old Goa Churches",  "category":"heritage", "rating":4.6,"icon":"⛪"},
            {"name":"Tito's Lane",       "category":"nightlife","rating":4.2,"icon":"🎶"},
            {"name":"Anjuna Flea Market","category":"shopping", "rating":4.1,"icon":"🛍️"},
            {"name":"Dudhsagar Falls",   "category":"nature",   "rating":4.7,"icon":"💧"},
        ],
        "manali": [
            {"name":"Rohtang Pass",    "category":"nature",   "rating":4.7,"icon":"⛰️"},
            {"name":"Solang Valley",   "category":"adventure","rating":4.5,"icon":"🎿"},
            {"name":"Hadimba Temple",  "category":"heritage", "rating":4.3,"icon":"🛕"},
            {"name":"Mall Road",       "category":"shopping", "rating":4.0,"icon":"🛍️"},
        ],
    }
    items = db.get(city.lower(), [
        {"name":f"{city} City Centre","category":"sightseeing","rating":4.0,"icon":"🏙️"},
        {"name":f"{city} Nature Park","category":"nature",     "rating":4.2,"icon":"🌿"},
    ])
    if interests:
        scored = []
        for p in items:
            score = sum(1 for tag in interests if tag.lower() in p["category"].lower())
            scored.append((score, p))
        items = [p for _, p in sorted(scored, key=lambda t: -t[0])]
    return {"city": city, "attractions": items[:6]}

def tool_budget_calculator(transport: Dict, hotel: Dict, nights: int,
                           travelers: int, daily_food: int = 800,
                           daily_activities: int = 500) -> Dict[str, Any]:
    rec = transport.get("recommended", {})
    transport_cost = rec.get("price", 0) * travelers
    if rec.get("mode") in ("train", "car"):
        transport_cost = int(transport_cost * 0.7)
    hotel_cost    = hotel["top_pick"]["price"] * nights if hotel.get("top_pick") else 0
    food_cost     = daily_food * (nights + 1) * travelers
    activity_cost = daily_activities * (nights + 1) * travelers
    total = transport_cost + hotel_cost + food_cost + activity_cost
    if total == 0: total = 1
    return {
        "transport_cost": transport_cost, "hotel_cost": hotel_cost,
        "food_cost": food_cost,           "activity_cost": activity_cost,
        "total": total,
        "breakdown_pct": {
            "transport":  round(100 * transport_cost / total, 1),
            "hotel":      round(100 * hotel_cost / total, 1),
            "food":       round(100 * food_cost / total, 1),
            "activities": round(100 * activity_cost / total, 1),
        }
    }

# ═══════════════════════════════════════════════════════════════════════════════
#  MEMORY STORE
# ═══════════════════════════════════════════════════════════════════════════════
EMB_DIM = 256

def _embed(text: str) -> np.ndarray:
    vec = np.zeros(EMB_DIM, dtype=np.float32)
    for tok in text.lower().split():
        vec[hash(tok) % EMB_DIM] += 1.0
    n = np.linalg.norm(vec)
    return vec / n if n else vec

class MemoryStore:
    def __init__(self):
        self._texts: List[str] = []
        self._meta:  List[dict] = []
        self._vecs:  List[np.ndarray] = []

    def add(self, text: str, meta: dict):
        self._texts.append(text); self._meta.append(meta)
        self._vecs.append(_embed(text))

    def query(self, q: str, k: int = 3) -> List[dict]:
        if not self._vecs: return []
        qv   = _embed(q)
        sims = np.array([float(np.dot(qv, v)) for v in self._vecs])
        idx  = sims.argsort()[::-1][:k]
        return [{"text": self._texts[i], "meta": self._meta[i], "score": float(sims[i])}
                for i in idx]

GLOBAL_MEMORY = MemoryStore()

# ═══════════════════════════════════════════════════════════════════════════════
#  AGENTS
# ═══════════════════════════════════════════════════════════════════════════════
def user_input_agent(state: TripState) -> TripState:
    prefs = dict(state.get("trip_preferences", {}))
    prefs.setdefault("source", "Bangalore"); prefs.setdefault("destination", "Goa")
    prefs.setdefault("start_date", str(dt.date.today() + dt.timedelta(days=30)))
    prefs.setdefault("days", 5);  prefs.setdefault("travelers", 2)
    prefs.setdefault("travel_type", "couple"); prefs.setdefault("budget", 30000)
    prefs.setdefault("mode_pref", "flight");   prefs.setdefault("vibe", "mid")
    prefs.setdefault("interests", ["beach", "heritage"]); prefs.setdefault("food_pref", "local")
    return {"trip_preferences": prefs,
            "messages": [{"role": "system", "content": "User input parsed."}]}

def memory_retrieval_agent(state: TripState) -> TripState:
    p = state["trip_preferences"]
    query = f"{p.get('destination','')} {p.get('vibe','')} {p.get('food_pref','')}"
    hits  = GLOBAL_MEMORY.query(query, k=3)
    return {"user_profile": {"recalled": [h["text"] for h in hits]},
            "messages": [{"role": "system", "content": f"Memory recalled {len(hits)} item(s)."}]}

def weather_agent(state: TripState) -> TripState:
    p = state["trip_preferences"]
    return {"weather_data": tool_get_weather(p["destination"], p["start_date"], p["days"])}

def transport_agent(state: TripState) -> TripState:
    p = state["trip_preferences"]
    return {"transport_data": tool_search_transport(p["source"], p["destination"],
                                                    p["start_date"], p["mode_pref"])}

def hotel_agent(state: TripState) -> TripState:
    p = state["trip_preferences"]; retries = state.get("retry_count", 0)
    per_night = max(800, int(p["budget"] / max(p["days"], 1) / 2 * (0.7 ** retries)))
    end = (dt.date.fromisoformat(p["start_date"]) + dt.timedelta(days=p["days"])).isoformat()
    vibe = "budget" if retries > 0 else p["vibe"]
    return {"hotel_data": tool_search_hotels(p["destination"], p["start_date"], end, per_night, vibe)}

def places_agent(state: TripState) -> TripState:
    p = state["trip_preferences"]
    return {"places_data": tool_explore_places(p["destination"], p["interests"])}

def budget_agent(state: TripState) -> TripState:
    p = state["trip_preferences"]
    summary = tool_budget_calculator(state["transport_data"], state["hotel_data"],
                                     nights=p["days"]-1, travelers=p["travelers"])
    summary["target"] = p["budget"]; summary["over_budget"] = summary["total"] > p["budget"]
    return {"budget_summary": summary}

def itinerary_agent(state: TripState) -> TripState:
    p = state["trip_preferences"]
    places = state["places_data"]["attractions"]
    days_n = p["days"]; plan = []; pool = list(places)

    def pop(): return pool.pop(0)["name"] if pool else "Free time"

    for d in range(1, days_n + 1):
        if d == 1:
            plan.append({"day":d,"morning":"Arrive & check-in","afternoon":pop(),"evening":"Welcome dinner"})
        elif d == days_n:
            plan.append({"day":d,"morning":pop(),"afternoon":"Check-out & lunch","evening":"Depart"})
        else:
            plan.append({"day":d,"morning":pop(),"afternoon":pop(),
                         "evening":"Nightlife" if "nightlife" in p["interests"] and d==2 else "Local dinner"})
    head = llm_call("You are a concise travel writer.",
                    f"Give a 1-sentence headline for a {days_n}-day "
                    f"{p['travel_type']} trip to {p['destination']}.")
    return {"itinerary": {"days": plan, "headline": head}}

def final_review_agent(state: TripState) -> TripState:
    issues = []
    if state["budget_summary"].get("over_budget"):
        issues.append("Total cost exceeds budget.")
    rain = sum(1 for d in state["weather_data"]["forecast"] if "rain" in d["conditions"])
    if rain >= 3:
        issues.append(f"{rain} rainy days — consider indoor alternatives.")
    if not state["hotel_data"].get("top_pick"):
        issues.append("No hotel matched the budget.")
    return {"review_status": {"approved": len(issues) == 0, "issues": issues}}

MAX_RETRIES = 3

def orchestrator(state: TripState) -> TripState:
    updates: dict = {}
    if state.get("pdf_status"):
        nxt, reason = "END", "PDF complete."
    elif not state.get("trip_preferences"):
        nxt, reason = "user_input", "No preferences yet."
    elif not state.get("user_profile"):
        nxt, reason = "memory", "Need memory recall."
    elif not (state.get("weather_data") and state.get("hotel_data") and
              state.get("transport_data") and state.get("places_data")):
        nxt, reason = "specialists_fanout", "Gathering data."
    elif not state.get("budget_summary"):
        nxt, reason = "budget", "Compute budget."
    elif not state.get("itinerary"):
        nxt, reason = "itinerary", "Build plan."
    elif not state.get("review_status"):
        nxt, reason = "review", "Final review."
    else:
        rev = state["review_status"]; retries = state.get("retry_count", 0)
        if rev["approved"]:
            nxt, reason = "memory_update", "Approved → PDF."
        elif retries >= MAX_RETRIES:
            nxt, reason = "memory_update", "Max retries → finalize."
        else:
            issues = " ".join(rev["issues"]).lower()
            if "budget" in issues or "hotel" in issues:
                nxt, reason = "hotel", "Over budget → retry hotel."
            elif "rain" in issues:
                nxt, reason = "places", "Rainy → re-pick attractions."
            else:
                nxt, reason = "memory_update", "Finalize."
            updates.update({"budget_summary": {}, "itinerary": {}, "review_status": {}})
            updates["retry_count"] = retries + 1

    updates["orchestrator_decision"] = {"next": nxt, "reason": reason}
    updates["messages"] = [{"role": "orchestrator", "content": f"→ {nxt}: {reason}"}]
    return updates

def memory_update_agent(state: TripState) -> TripState:
    p = state["trip_preferences"]
    GLOBAL_MEMORY.add(
        f"Planned trip to {p['destination']} for {p['travelers']} ({p['travel_type']}), "
        f"vibe={p['vibe']}, budget={p['budget']}.",
        {"type": "trip_history"}
    )
    return {"messages": [{"role": "system", "content": "Memory updated."}]}

def specialists_fanout(state: TripState) -> TripState:
    return {"messages": [{"role": "system", "content": "Dispatching specialists."}]}

def route_from_orchestrator(state: TripState) -> str:
    return state["orchestrator_decision"]["next"]

# ═══════════════════════════════════════════════════════════════════════════════
#  PDF GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
def pdf_generator_agent(state: TripState, out_path: str = "trip_report.pdf") -> TripState:
    p=state["trip_preferences"]; bud=state["budget_summary"]; hot=state["hotel_data"]
    tra=state["transport_data"]; wea=state["weather_data"];   it=state["itinerary"]
    rev=state["review_status"]

    doc = SimpleDocTemplate(out_path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    H1   = ParagraphStyle("H1",  parent=styles["Heading1"],  fontSize=20,
                          textColor=colors.HexColor("#1F3864"), spaceAfter=10)
    H2   = ParagraphStyle("H2",  parent=styles["Heading2"],  fontSize=14,
                          textColor=colors.HexColor("#2E75B6"), spaceAfter=6)
    Body = styles["BodyText"]

    story = []

    # Cover
    story += [Spacer(1,3*cm),
              Paragraph(f"{p['source']} → {p['destination']}", H1),
              Paragraph(f"{p['days']}-day {p['travel_type']} trip · {p['travelers']} traveler(s) · "
                        f"Budget ₹{p['budget']:,}", Body),
              Spacer(1,0.4*cm),
              Paragraph(f"<b>Headline:</b> {it['headline']}", Body),
              Spacer(1,0.4*cm),
              Paragraph("✓ APPROVED" if rev["approved"] else "⚠ Completed with caveats",
                        ParagraphStyle("st", parent=Body,
                                       textColor=colors.green if rev["approved"] else colors.orange)),
              Spacer(1,0.5*cm),
              Paragraph(f"Generated on {dt.datetime.now():%Y-%m-%d %H:%M}",
                        ParagraphStyle("sm", parent=Body, fontSize=8, textColor=colors.grey)),
              PageBreak()]

    def mk_table(rows, col_w, hdr_color=colors.HexColor("#4F81BD")):
        t = Table(rows, colWidths=col_w)
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),hdr_color),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey),
            ("FONTSIZE",(0,0),(-1,-1),9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F2F2F2")]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ]))
        return t

    from reportlab.lib.units import cm as _cm

    # Transport
    story += [Paragraph("Section 1 · Transport", H1)]
    rec = tra.get("recommended", {})
    story += [Paragraph(f"<b>Recommended:</b> {rec.get('provider','–')} ({rec.get('mode','–')}) · "
                        f"{rec.get('depart','–')} → {rec.get('arrive','–')} · "
                        f"<b>₹{rec.get('price',0):,}</b>", Body), Spacer(1,0.3*cm)]
    rows = [["Mode","Provider","Depart","Arrive","Price (₹)"]] + [
        [o["mode"],o["provider"],o["depart"],o["arrive"],f"{o['price']:,}"]
        for o in tra.get("options",[])]
    story += [mk_table(rows,[60,120,70,80,80]), PageBreak()]

    # Hotel
    top = hot.get("top_pick") or {}
    story += [Paragraph("Section 2 · Hotel", H1),
              Paragraph(f"<b>Top pick:</b> {top.get('name','–')} · {top.get('stars',0)}★ · "
                        f"₹{top.get('price',0):,}/night", Body), Spacer(1,0.3*cm)]
    rows = [["Hotel","Stars","₹/night","Tags"]] + [
        [h["name"],h["stars"],f"{h['price']:,}",", ".join(h["tags"])]
        for h in hot.get("candidates",[])]
    story += [mk_table(rows,[160,50,70,130]), PageBreak()]

    # Itinerary
    story += [Paragraph("Section 3 · Itinerary", H1)]
    rows = [["Day","Morning","Afternoon","Evening"]] + [
        [f"Day {d['day']}",d["morning"],d["afternoon"],d["evening"]]
        for d in it["days"]]
    story += [mk_table(rows,[1.5*_cm,5*_cm,5*_cm,5*_cm]), Spacer(1,0.5*cm),
              Paragraph("<b>Weather Forecast</b>", H2)]
    rows = [["Date","Conditions","High°C","Low°C"]] + [
        [w["date"],w["conditions"],w["high_c"],w["low_c"]]
        for w in wea["forecast"]]
    story += [mk_table(rows,[80,120,60,60], hdr_color=colors.HexColor("#70AD47")), PageBreak()]

    # Budget
    story += [Paragraph("Section 4 · Budget", H1)]
    rows = [["Category","Amount (₹)","%"],
            ["Transport",  f"{bud['transport_cost']:,}", f"{bud['breakdown_pct']['transport']}%"],
            ["Hotel",      f"{bud['hotel_cost']:,}",     f"{bud['breakdown_pct']['hotel']}%"],
            ["Food",       f"{bud['food_cost']:,}",      f"{bud['breakdown_pct']['food']}%"],
            ["Activities", f"{bud['activity_cost']:,}",  f"{bud['breakdown_pct']['activities']}%"],
            ["TOTAL",      f"{bud['total']:,}",           "100%"],
            ["Target",     f"{bud['target']:,}",          ""]]
    story += [mk_table(rows,[120,100,60]), Spacer(1,0.3*cm),
              Paragraph(f"Under budget by ₹{bud['target']-bud['total']:,}" if not bud["over_budget"]
                        else f"Over budget by ₹{bud['total']-bud['target']:,}", Body), PageBreak()]

    # Packing
    story += [Paragraph("Section 5 · Packing Checklist", H1)]
    packing = llm_call("You are a travel packing assistant.",
                       f"List 6 items for a {p['travel_type']} trip to {p['destination']}. "
                       f"Weather: {wea['forecast'][0]['conditions']}. Semicolon-separated.")
    for item in [s.strip() for s in packing.replace(",",";").split(";") if s.strip()][:8]:
        story.append(Paragraph(f"☐  {item}", Body))
    story += [PageBreak(), Paragraph("Section 6 · Emergency Contacts", H1)]
    rows = [["Service","Number"],["Emergency","112"],["Police","100"],
            ["Ambulance","108"],["Tourist Helpline","1363"],
            ["Your Hotel", top.get("name","–")]]
    story.append(mk_table(rows,[200,200], hdr_color=colors.HexColor("#C0504D")))

    doc.build(story)
    return {"pdf_status": {"path": os.path.abspath(out_path),
                            "generated_at": dt.datetime.now().isoformat()},
            "messages": [{"role":"system","content":f"PDF → {out_path}"}]}

# ═══════════════════════════════════════════════════════════════════════════════
#  BUILD LANGGRAPH
# ═══════════════════════════════════════════════════════════════════════════════
def build_graph():
    g = StateGraph(TripState)
    g.add_node("orchestrator",     orchestrator)
    g.add_node("user_input",       user_input_agent)
    g.add_node("memory",           memory_retrieval_agent)
    g.add_node("specialists_fanout", specialists_fanout)
    g.add_node("weather",          weather_agent)
    g.add_node("transport",        transport_agent)
    g.add_node("hotel",            hotel_agent)
    g.add_node("places",           places_agent)
    g.add_node("budget",           budget_agent)
    g.add_node("itinerary",        itinerary_agent)
    g.add_node("review",           final_review_agent)
    g.add_node("memory_update",    memory_update_agent)

    def pdf_agent_node(state: TripState) -> TripState:
        tid = state.get("thread_id", "default")
        out = os.path.join("outputs", f"trip_{tid}.pdf")
        return pdf_generator_agent(state, out_path=out)

    g.add_node("pdf", pdf_agent_node)
    g.add_edge(START, "orchestrator")
    g.add_conditional_edges("orchestrator", route_from_orchestrator,
        {"user_input":"user_input","memory":"memory","specialists_fanout":"specialists_fanout",
         "budget":"budget","itinerary":"itinerary","review":"review","hotel":"hotel",
         "places":"places","transport":"transport","memory_update":"memory_update","END":END})
    for n in ["user_input","memory","budget","itinerary","review"]:
        g.add_edge(n, "orchestrator")
    for s in ["weather","transport","hotel","places"]:
        g.add_edge("specialists_fanout", s)
        g.add_edge(s, "orchestrator")
    g.add_edge("memory_update", "pdf")
    g.add_edge("pdf", "orchestrator")
    return g.compile(checkpointer=MemorySaver())

WORKFLOW = build_graph()
print("✓ LangGraph workflow compiled.")

# ═══════════════════════════════════════════════════════════════════════════════
#  FLASK APP
# ═══════════════════════════════════════════════════════════════════════════════
flask_app = Flask(__name__)
os.makedirs("outputs", exist_ok=True)

@flask_app.route("/")
def index():
    return render_template("index.html")

@flask_app.route("/plan", methods=["POST"])
def plan():
    try:
        data = request.json or {}
        # Build preferences
        interests = data.get("interests", [])
        if isinstance(interests, str):
            interests = [i.strip() for i in interests.split(",") if i.strip()]

        prefs = {
            "source":      data.get("source", "Bangalore").strip().title(),
            "destination": data.get("destination", "Goa").strip().title(),
            "start_date":  data.get("start_date", str(dt.date.today() + dt.timedelta(days=30))),
            "days":        int(data.get("days", 5)),
            "travelers":   int(data.get("travelers", 2)),
            "travel_type": data.get("travel_type", "couple").lower(),
            "budget":      float(data.get("budget", 30000)),
            "mode_pref":   data.get("mode_pref", "any").lower(),
            "vibe":        data.get("vibe", "mid").lower(),
            "interests":   interests,
            "food_pref":   data.get("food_pref", "local"),
        }

        # Validate
        raw_query = (f"Plan a {prefs['days']}-day trip to {prefs['destination']} "
                     f"from {prefs['source']} for {prefs['travelers']} traveler(s). "
                     f"Budget ₹{prefs['budget']:,.0f}.")
        GUARDRAILS.validate_all(raw_query, prefs)

        # Run workflow
        thread_id = str(uuid.uuid4())[:8]
        initial_state: TripState = {
            "user_id":          "web_user",
            "thread_id":        thread_id,
            "raw_query":        raw_query,
            "trip_preferences": prefs,
            "messages":         [],
            "retry_count":      0,
        }
        final = WORKFLOW.invoke(
            initial_state,
            config={"configurable": {"thread_id": thread_id}, "recursion_limit": 60}
        )

        it  = final.get("itinerary", {})
        bud = final.get("budget_summary", {})
        hot = final.get("hotel_data", {})
        tra = final.get("transport_data", {})
        wea = final.get("weather_data", {})
        rev = final.get("review_status", {})

        return jsonify({
            "ok":        True,
            "thread_id": thread_id,
            "headline":  it.get("headline", ""),
            "approved":  rev.get("approved", False),
            "issues":    rev.get("issues", []),
            "itinerary": it.get("days", []),
            "hotel": {
                "top":        hot.get("top_pick"),
                "candidates": hot.get("candidates", []),
            },
            "transport": {
                "recommended": tra.get("recommended"),
                "options":     tra.get("options", []),
            },
            "weather":  wea.get("forecast", []),
            "weather_summary": wea.get("summary", ""),
            "budget":   bud,
            "pdf_ready": bool(final.get("pdf_status")),
        })

    except InputGuardrailError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()}), 500

@flask_app.route("/download/<thread_id>")
def download(thread_id):
    path = os.path.join("outputs", f"trip_{thread_id}.pdf")
    if not os.path.exists(path):
        return "PDF not found", 404
    return send_file(path, as_attachment=True,
                     download_name=f"Trip_Report_{thread_id}.pdf",
                     mimetype="application/pdf")

if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    flask_app.run(debug=debug, host="0.0.0.0", port=port, use_reloader=False)

