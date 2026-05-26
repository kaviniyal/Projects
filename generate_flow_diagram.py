"""
Generate notebook_flow_diagram.png — full architecture flow for Trip_Planner_Assignment.ipynb
Run:  python generate_flow_diagram.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ── colour palette ─────────────────────────────────────────────────────────
C = {
    "bg":           "#F0F4F8",
    "input":        "#1565C0",   # deep blue
    "guard":        "#C62828",   # deep red
    "state":        "#37474F",   # blue-grey
    "orch":         "#6A1B9A",   # purple
    "setup":        "#2E7D32",   # green
    "mem":          "#E65100",   # deep orange
    "specialist":   "#00695C",   # teal
    "process":      "#00838F",   # cyan-dark
    "output":       "#283593",   # indigo
    "eval":         "#4E342E",   # brown
    "sidebar":      "#546E7A",   # blue-grey light
    "arrow":        "#37474F",
    "retry":        "#C62828",
}

FIG_W, FIG_H = 15, 24

fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=C["bg"])
ax  = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
ax.set_facecolor(C["bg"])


# ── helpers ────────────────────────────────────────────────────────────────
def box(cx, cy, w, h, title, color, subtitle="", fs=9, alpha=0.93):
    """Draw a rounded rectangle centred at (cx, cy)."""
    rect = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.18",
        facecolor=color, edgecolor="white",
        linewidth=2, zorder=3, alpha=alpha,
    )
    ax.add_patch(rect)
    if subtitle:
        ax.text(cx, cy + h * 0.17, title, ha="center", va="center",
                fontsize=fs, fontweight="bold", color="white", zorder=4)
        ax.text(cx, cy - h * 0.22, subtitle, ha="center", va="center",
                fontsize=fs - 1.5, color="white", zorder=4, style="italic",
                alpha=0.9)
    else:
        ax.text(cx, cy, title, ha="center", va="center",
                fontsize=fs, fontweight="bold", color="white", zorder=4,
                multialignment="center")


def arr(x1, y1, x2, y2, color=None, lw=1.8, rad=0.0, ls="solid"):
    color = color or C["arrow"]
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>", color=color, lw=lw,
            linestyle=ls,
            connectionstyle=f"arc3,rad={rad}",
        ),
        zorder=2,
    )


def label(x, y, txt, color="#555555", fs=7.5, bold=False, italic=False):
    ax.text(x, y, txt, ha="center", va="center", fontsize=fs,
            color=color,
            fontweight="bold" if bold else "normal",
            style="italic" if italic else "normal",
            zorder=5)


def section_bg(x, y, w, h, color, title=""):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.2",
        facecolor=color, edgecolor="none",
        linewidth=0, zorder=1, alpha=0.12,
    )
    ax.add_patch(rect)
    if title:
        ax.text(x + 0.2, y + h - 0.15, title, ha="left", va="top",
                fontsize=7, color=color, alpha=0.7, zorder=2, style="italic")


# ══════════════════════════════════════════════════════════════════════════════
#  TITLE
# ══════════════════════════════════════════════════════════════════════════════
ax.text(7.5, 23.5, "Trip Planner Notebook — Architecture Flow",
        ha="center", va="center", fontsize=16, fontweight="bold", color="#1A237E", zorder=6)
ax.text(7.5, 23.0, "LangGraph · Multi-Agent Orchestration · Memory · Guardrails · PDF · DeepEval",
        ha="center", va="center", fontsize=9, color="#455A64", zorder=6)

# horizontal rule
ax.plot([0.5, 14.5], [22.7, 22.7], color="#B0BEC5", lw=1.2, zorder=2)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION BACKGROUNDS
# ══════════════════════════════════════════════════════════════════════════════
section_bg(0.3,  21.6, 14.4, 1.1,  C["input"],  "INPUT")
section_bg(0.3,  19.8, 14.4, 1.7,  C["guard"],  "GUARDRAILS")
section_bg(0.3,  17.4, 14.4, 2.3,  C["orch"],   "ORCHESTRATOR LOOP")
section_bg(0.3,  13.1, 14.4, 4.2,  C["specialist"], "SPECIALIST AGENTS  (fan-out, parallel)")
section_bg(0.3,   9.0, 14.4, 4.0,  C["process"],    "PROCESSING PIPELINE")
section_bg(0.3,   4.8, 14.4, 4.1,  C["output"],     "OUTPUT")
section_bg(0.3,   1.5, 14.4, 3.2,  C["eval"],       "EVALUATION")


# ══════════════════════════════════════════════════════════════════════════════
#  ROW 1  — USER INPUT
# ══════════════════════════════════════════════════════════════════════════════
box(7.5, 22.1, 7.0, 0.7,
    "User Query  /  trip_preferences  dict",
    C["input"],
    subtitle="source · destination · days · travelers · budget · mode_pref · vibe · interests",
    fs=9)

arr(7.5, 21.75, 7.5, 21.4)


# ══════════════════════════════════════════════════════════════════════════════
#  ROW 2  — GUARDRAILS
# ══════════════════════════════════════════════════════════════════════════════
BOX_GUARD_Y = 21.0
for i, (lbl, sub) in enumerate([
    ("Guard 1\nRaw Query",   "injection scan\n+ length cap"),
    ("Guard 2\nPreferences", "9-field type\n& range checks"),
    ("Guard 3\nBusiness Rules", "src ≠ dst\nbudget floor"),
]):
    bx = 3.5 + i * 4.0
    box(bx, BOX_GUARD_Y, 3.2, 0.75, lbl, C["guard"], subtitle=sub, fs=8)
    if i < 2:
        arr(bx + 1.6, BOX_GUARD_Y, bx + 2.4, BOX_GUARD_Y, lw=1.4)

arr(7.5, 20.62, 7.5, 20.25)
label(8.2, 20.42, "valid ✓", C["guard"], fs=7.5, italic=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ROW 3  — TRIPSTATE SCHEMA
# ══════════════════════════════════════════════════════════════════════════════
box(7.5, 19.95, 7.0, 0.55,
    "TripState  (TypedDict)  —  shared state flowing through all nodes",
    C["state"], fs=8.5)

arr(7.5, 19.67, 7.5, 19.15)


# ══════════════════════════════════════════════════════════════════════════════
#  ROW 4  — ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════
box(7.5, 18.8, 8.0, 0.65,
    "ORCHESTRATOR  (Supervisor / Router)",
    C["orch"],
    subtitle="rule-based dispatch  ·  decides next node every pass  ·  MAX_RETRIES = 3",
    fs=9)

# branches out left & right
arr(3.5, 18.8,  2.2, 18.15,  lw=1.5)   # → user_input
arr(5.5, 18.8,  4.8, 18.15,  lw=1.5)   # → memory
arr(9.5, 18.8, 10.5, 17.65,  lw=1.5)   # → specialists fan-out
# straight down (to budget after all data collected)
arr(7.5, 18.47, 7.5, 13.5,   lw=1.6)


# ══════════════════════════════════════════════════════════════════════════════
#  ROW 5  — SETUP AGENTS  (left side)
# ══════════════════════════════════════════════════════════════════════════════
box(2.2, 17.8, 2.8, 0.65,
    "User Input\nAgent",
    C["setup"],
    subtitle="defaults + setdefault()",
    fs=8)

box(4.8, 17.8, 2.8, 0.65,
    "Memory Retrieval\nAgent",
    C["mem"],
    subtitle="query MemoryStore (k=3)",
    fs=8)

# memory store (sidebar)
box(0.9, 16.9, 1.6, 0.7,
    "Memory\nStore",
    C["mem"],
    subtitle="vector DB\n(NumPy/FAISS)",
    fs=7.5)

ax.annotate("", xy=(1.7, 17.8), xytext=(2.3, 17.8),
            arrowprops=dict(arrowstyle="<->", color=C["mem"], lw=1.4), zorder=2)
ax.annotate("", xy=(1.7, 17.1), xytext=(0.9, 17.25),
            arrowprops=dict(arrowstyle="<->", color=C["mem"], lw=1.2), zorder=2)

# back to orchestrator
arr(2.2, 17.48, 5.5, 18.55, color=C["arrow"], lw=1.2, rad=-0.25)
arr(4.8, 17.48, 5.5, 18.55, color=C["arrow"], lw=1.2, rad=0.15)


# ══════════════════════════════════════════════════════════════════════════════
#  ROW 6  — SPECIALISTS FAN-OUT
# ══════════════════════════════════════════════════════════════════════════════
box(10.5, 17.35, 2.5, 0.55, "Specialists\nFan-out Node", C["specialist"], fs=8)

SPEC_Y   = 16.3
SPEC_XS  = [8.2, 9.9, 11.6, 13.3]
SPEC_DATA = [
    ("Weather\nAgent",   "OpenWeatherMap\n(mock)"),
    ("Transport\nAgent", "Skyscanner/IRCTC\n(mock)"),
    ("Hotel\nAgent",     "Booking.com\n(mock)"),
    ("Places\nAgent",    "Google Places\n(mock)"),
]

for sx, (lbl, sub) in zip(SPEC_XS, SPEC_DATA):
    box(sx, SPEC_Y, 1.55, 0.75, lbl, C["specialist"], subtitle=sub, fs=7.5)
    arr(sx, 16.65, 10.5, 17.07, color=C["specialist"], lw=1.1)
    arr(sx, 15.92, sx,   15.42, color=C["specialist"], lw=1.0)

# Specialist tool results boxes
TOOL_Y = 15.15
TOOL_DATA = [
    ("weather_data", C["specialist"]),
    ("transport_data", C["specialist"]),
    ("hotel_data", C["specialist"]),
    ("places_data", C["specialist"]),
]
for sx, (lbl, col) in zip(SPEC_XS, TOOL_DATA):
    box(sx, TOOL_Y, 1.4, 0.42, lbl, col, fs=7)

# all tool results feed back to orchestrator
for sx in SPEC_XS:
    arr(sx, 14.94, 9.5, 18.63, color="#00695C", lw=1.0, rad=0.15)

label(12.2, 14.3, "→ back to orchestrator", C["specialist"], fs=7, italic=True)


# ══════════════════════════════════════════════════════════════════════════════
#  LLM WRAPPER SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
box(1.1, 13.6, 1.8, 1.0,
    "LLM\nWrapper",
    C["sidebar"],
    subtitle="Real (ChatOpenAI)\nor Mock (rule-based)",
    fs=7.5)

# dashed lines from LLM wrapper to itinerary and packing
ax.annotate("", xy=(4.3, 11.3), xytext=(2.0, 13.1),
            arrowprops=dict(arrowstyle="-|>", color=C["sidebar"], lw=1.2,
                            linestyle="dashed",
                            connectionstyle="arc3,rad=-0.2"), zorder=2)
ax.annotate("", xy=(4.3, 8.6), xytext=(2.0, 13.1),
            arrowprops=dict(arrowstyle="-|>", color=C["sidebar"], lw=1.2,
                            linestyle="dashed",
                            connectionstyle="arc3,rad=0.3"), zorder=2)
label(1.55, 12.3, "headline\n+ packing", C["sidebar"], fs=6.5, italic=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PROCESSING PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
PIPE_X = 7.5

# Budget
box(PIPE_X, 13.1, 5.5, 0.65,
    "Budget Agent",
    C["process"],
    subtitle="tool_budget_calculator()  ·  computes total  ·  sets over_budget flag",
    fs=9)
arr(PIPE_X, 12.77, PIPE_X, 12.25)

# Itinerary
box(PIPE_X, 11.95, 5.5, 0.65,
    "Itinerary Agent",
    C["process"],
    subtitle="day-wise plan from attractions  ·  llm_call() for headline",
    fs=9)
arr(PIPE_X, 11.62, PIPE_X, 11.1)

# Review
box(PIPE_X, 10.8, 5.5, 0.65,
    "Final Review Agent",
    C["process"],
    subtitle="budget check  ·  rainy days  ·  hotel exists  ·  transport exists",
    fs=9)

# Approved path
arr(PIPE_X, 10.47, PIPE_X, 9.95, color="#2E7D32", lw=1.8)
label(8.5, 10.2, "approved ✓", "#2E7D32", fs=7.5, italic=True)

# ── RETRY LOOP ──────────────────────────────────────────────────────────────
ax.annotate("", xy=(11.6, 18.55), xytext=(10.8, 10.8),
            arrowprops=dict(
                arrowstyle="-|>", color=C["retry"], lw=2.0,
                linestyle="dashed",
                connectionstyle="arc3,rad=-0.5",
            ), zorder=2)
ax.text(13.1, 14.8,
        "retry loop\n(issues found)\nhotel / transport\n/ weather",
        ha="center", va="center", fontsize=7.5, color=C["retry"],
        style="italic", zorder=5,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFEBEE",
                  edgecolor=C["retry"], alpha=0.9))


# ══════════════════════════════════════════════════════════════════════════════
#  OUTPUT
# ══════════════════════════════════════════════════════════════════════════════
# Memory update
box(PIPE_X, 9.65, 5.5, 0.55,
    "Memory Update Agent  →  persist trip to MemoryStore",
    C["mem"], fs=8.5)

# dashed line back to memory store
ax.annotate("", xy=(1.7, 16.55), xytext=(4.7, 9.65),
            arrowprops=dict(arrowstyle="-|>", color=C["mem"], lw=1.2,
                            linestyle="dashed",
                            connectionstyle="arc3,rad=0.45"), zorder=2)

arr(PIPE_X, 9.37, PIPE_X, 8.85)

# PDF Generator
box(PIPE_X, 8.55, 8.0, 0.65,
    "PDF Generator Agent  (ReportLab)",
    C["output"],
    subtitle="Section 1: Transport  ·  Section 2: Hotel  ·  Section 3: Itinerary  "
             "·  Section 4: Budget  ·  Section 5: Packing  ·  Section 6: Emergency",
    fs=9)

arr(PIPE_X, 8.22, PIPE_X, 7.7)

# PDF artifact
box(PIPE_X, 7.45, 3.0, 0.45, "trip_report.pdf  (6 pages)", C["output"], fs=8.5)
arr(PIPE_X, 7.22, PIPE_X, 6.7)


# ══════════════════════════════════════════════════════════════════════════════
#  EVALUATION
# ══════════════════════════════════════════════════════════════════════════════
box(PIPE_X, 6.4, 9.0, 0.65,
    "DeepEval Evaluation Suite  (Section 14)",
    C["eval"],
    subtitle="TC-A: AnswerRelevancy  ·  TC-B: Faithfulness  ·  TC-C: ContextualRelevancy  "
             "·  HallucinationMetric",
    fs=9)

# Two sub-paths
arr(5.5, 6.07, 4.3, 5.55)
arr(9.5, 6.07, 10.7, 5.55)

box(4.3, 5.25, 3.5, 0.55,
    "LLM-Judge Metrics\n(OPENAI_API_KEY + deepeval)",
    C["eval"], fs=8)

box(10.7, 5.25, 3.5, 0.55,
    "Rule-Based Fallback\n(12 assertions, no key needed)",
    C["eval"], fs=8)

arr(4.3,  4.97, 7.5, 4.35)
arr(10.7, 4.97, 7.5, 4.35)

box(PIPE_X, 4.1, 4.5, 0.45, "Evaluation Report  /  PASS · FAIL", "#263238", fs=8.5)


# ══════════════════════════════════════════════════════════════════════════════
#  NOTEBOOK SECTION INDEX  (right sidebar)
# ══════════════════════════════════════════════════════════════════════════════
SIDE_X = 14.3
sections = [
    ("§2",  "State Schema",        22.1),
    ("§3",  "LLM Wrapper",         21.0),
    ("§3.5","Guardrails",          20.25),
    ("§4",  "Tools (mock APIs)",   16.3),
    ("§5",  "Memory Store",        16.9),
    ("§6",  "Specialist Agents",   17.8),
    ("§7",  "Orchestrator",        18.8),
    ("§8",  "PDF Generator",       8.55),
    ("§9",  "LangGraph Graph",     18.0),
    ("§10", "Demo Run",            22.0),
    ("§14", "DeepEval Suite",      6.4),
]
ax.text(SIDE_X, 22.5, "Section\nIndex", ha="center", va="center",
        fontsize=7.5, fontweight="bold", color="#455A64")
for sec, name, yref in sections:
    yt = 22.2 - sections.index((sec, name, yref)) * 0.75
    ax.text(SIDE_X, yt, f"{sec}  {name}", ha="center", va="center",
            fontsize=6.5, color="#455A64",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                      edgecolor="#B0BEC5", alpha=0.8))


# ══════════════════════════════════════════════════════════════════════════════
#  LEGEND
# ══════════════════════════════════════════════════════════════════════════════
LEG_X, LEG_Y = 0.5, 3.3
ax.text(LEG_X, LEG_Y, "Legend", fontsize=8.5, fontweight="bold", color="#333")
LEGEND_ITEMS = [
    (C["input"],      "User Input"),
    (C["guard"],      "Guardrails"),
    (C["state"],      "State Schema"),
    (C["orch"],       "Orchestrator"),
    (C["setup"],      "Setup Agents"),
    (C["mem"],        "Memory"),
    (C["specialist"], "Specialist Agents"),
    (C["process"],    "Processing Agents"),
    (C["output"],     "Output / PDF"),
    (C["eval"],       "Evaluation"),
    (C["sidebar"],    "LLM Wrapper"),
]
cols = 4
for idx, (col, lbl) in enumerate(LEGEND_ITEMS):
    row = idx // cols
    c   = idx % cols
    lx  = LEG_X + c * 3.4
    ly  = LEG_Y - 0.45 - row * 0.38
    rect = FancyBboxPatch((lx, ly - 0.1), 0.3, 0.25,
                          boxstyle="round,pad=0.04",
                          facecolor=col, edgecolor="none", zorder=3)
    ax.add_patch(rect)
    ax.text(lx + 0.42, ly + 0.025, lbl, fontsize=7, va="center", color="#333")

# arrow legend
ly2 = LEG_Y - 1.5
ax.annotate("", xy=(LEG_X + 0.5, ly2), xytext=(LEG_X, ly2),
            arrowprops=dict(arrowstyle="-|>", color=C["arrow"], lw=1.5))
ax.text(LEG_X + 0.65, ly2, "normal flow", fontsize=7, va="center", color="#333")

ax.annotate("", xy=(LEG_X + 4.0, ly2), xytext=(LEG_X + 3.5, ly2),
            arrowprops=dict(arrowstyle="-|>", color=C["retry"], lw=1.5,
                            linestyle="dashed"))
ax.text(LEG_X + 4.15, ly2, "retry / dashed path", fontsize=7, va="center", color="#333")

ax.annotate("", xy=(LEG_X + 8.5, ly2), xytext=(LEG_X + 8.0, ly2),
            arrowprops=dict(arrowstyle="-|>", color=C["sidebar"], lw=1.5,
                            linestyle="dashed"))
ax.text(LEG_X + 8.65, ly2, "LLM call", fontsize=7, va="center", color="#333")

ax.annotate("", xy=(LEG_X + 11.5, ly2), xytext=(LEG_X + 11.0, ly2),
            arrowprops=dict(arrowstyle="<->", color=C["mem"], lw=1.5))
ax.text(LEG_X + 11.65, ly2, "read/write", fontsize=7, va="center", color="#333")

# footer
ax.plot([0.3, 14.7], [1.35, 1.35], color="#B0BEC5", lw=1)
ax.text(7.5, 1.1,
        "Trip_Planner_Assignment.ipynb  ·  AFDE Prodapt Chennai  ·  Day 9 Assignment",
        ha="center", fontsize=7.5, color="#78909C")


# ══════════════════════════════════════════════════════════════════════════════
#  SAVE
# ══════════════════════════════════════════════════════════════════════════════
out = r"c:/Users/kavin.k/Desktop/FDE Trainer Github/New folder/notebook_flow_diagram.png"
plt.savefig(out, dpi=160, bbox_inches="tight",
            facecolor=C["bg"], edgecolor="none")
print("Saved ->", out)
