"""
generate_presentation.py
Builds Trip_Planner_Presentation.pdf â€” a slide-style presentation PDF
with a flow diagram for every section of the notebook.
"""
import os, datetime as dt
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, KeepTogether
)
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Polygon, Circle
)
from reportlab.graphics import renderPDF

# â”€â”€ Page setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PW, PH = landscape(A4)   # 841.89 x 595.28 pt
MARGIN  = 1.4 * cm
CW      = PW - 2 * MARGIN   # content width  â‰ˆ 813 pt
CH      = PH - 2 * MARGIN   # content height â‰ˆ 567 pt

# â”€â”€ Color palette â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
DARK    = colors.HexColor('#1F3864')
BLUE    = colors.HexColor('#2E75B6')
LBLUE   = colors.HexColor('#BDD7EE')
TEAL    = colors.HexColor('#00B0A0')
GREEN   = colors.HexColor('#548235')
LGREEN  = colors.HexColor('#E2EFDA')
ORANGE  = colors.HexColor('#C55A11')
LORANGE = colors.HexColor('#FCE4D6')
RED     = colors.HexColor('#C00000')
LRED    = colors.HexColor('#FFE0E0')
YELLOW  = colors.HexColor('#BF8F00')
LYELLOW = colors.HexColor('#FFF2CC')
PURPLE  = colors.HexColor('#7030A0')
LPURPLE = colors.HexColor('#EAD1FF')
GRAY    = colors.HexColor('#595959')
LGRAY   = colors.HexColor('#F2F2F2')
MID     = colors.HexColor('#D9D9D9')
WHITE   = colors.white
BLACK   = colors.black

# â”€â”€ Text styles â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SS = getSampleStyleSheet()

def sty(name, **kw):
    base = kw.pop('parent', SS['Normal'])
    return ParagraphStyle(name, parent=base, **kw)

COVER_TITLE  = sty('CT',  fontSize=38, fontName='Helvetica-Bold',   textColor=WHITE, alignment=1, leading=46)
COVER_SUB    = sty('CS',  fontSize=18, fontName='Helvetica',         textColor=LBLUE, alignment=1, leading=24)
COVER_AUTH   = sty('CA',  fontSize=13, fontName='Helvetica',         textColor=MID,   alignment=1)
SLIDE_HEAD   = sty('SH',  fontSize=22, fontName='Helvetica-Bold',   textColor=WHITE, alignment=0, leading=28)
SLIDE_SUB    = sty('SS2', fontSize=12, fontName='Helvetica',         textColor=LBLUE, alignment=0)
H2           = sty('H2',  fontSize=14, fontName='Helvetica-Bold',   textColor=DARK,  spaceAfter=4)
BODY         = sty('BD',  fontSize=11, fontName='Helvetica',         textColor=BLACK, leading=16, spaceAfter=5)
BODY_SM      = sty('BS',  fontSize=10, fontName='Helvetica',         textColor=GRAY,  leading=14, spaceAfter=4)
BULLET       = sty('BU',  fontSize=11, fontName='Helvetica',         textColor=BLACK, leading=16,
                   leftIndent=14, spaceAfter=4)
CODE_ST      = sty('CD',  fontSize=9,  fontName='Courier',           textColor=DARK,  backColor=LGRAY,
                   leading=13, leftIndent=8, rightIndent=8, spaceAfter=3)
TABLE_HEAD   = sty('TH',  fontSize=10, fontName='Helvetica-Bold',   textColor=WHITE, alignment=1)
TABLE_CELL   = sty('TC',  fontSize=10, fontName='Helvetica',         textColor=BLACK, alignment=1)

# â”€â”€ Drawing primitives â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def rbox(d, x, y, w, h, text, bg=LBLUE, tc=DARK, fs=10, bold=False,
         rx=6, ry=6, border=DARK, bw=1):
    """Rounded rectangle with centered multi-line text."""
    d.add(Rect(x, y, w, h, rx, ry, fillColor=bg, strokeColor=border, strokeWidth=bw))
    lines = str(text).split('\n')
    lh = fs * 1.35
    tot = len(lines) * lh
    y0  = y + h / 2 + tot / 2 - lh * 0.8
    fn  = 'Helvetica-Bold' if bold else 'Helvetica'
    for ln in lines:
        d.add(String(x + w / 2, y0, ln, fontSize=fs, fontName=fn,
                     fillColor=tc, textAnchor='middle'))
        y0 -= lh

def plain_box(d, x, y, w, h, text, bg=LBLUE, tc=DARK, fs=10, bold=False):
    """Plain rectangle with centered multi-line text."""
    d.add(Rect(x, y, w, h, fillColor=bg, strokeColor=DARK, strokeWidth=1))
    lines = str(text).split('\n')
    lh = fs * 1.35
    tot = len(lines) * lh
    y0  = y + h / 2 + tot / 2 - lh * 0.8
    fn  = 'Helvetica-Bold' if bold else 'Helvetica'
    for ln in lines:
        d.add(String(x + w / 2, y0, ln, fontSize=fs, fontName=fn,
                     fillColor=tc, textAnchor='middle'))
        y0 -= lh

def arrowR(d, x1, y, x2, color=DARK, w=1.5):
    """Horizontal right-pointing arrow."""
    if x2 <= x1: return
    d.add(Line(x1, y, x2 - 7, y, strokeColor=color, strokeWidth=w))
    d.add(Polygon([x2-7, y+4, x2, y, x2-7, y-4],
                  fillColor=color, strokeColor=color, strokeWidth=0))

def arrowD(d, x, y1, y2, color=DARK, w=1.5):
    """Vertical downward arrow (y2 < y1)."""
    if y2 >= y1: return
    d.add(Line(x, y1, x, y2 + 7, strokeColor=color, strokeWidth=w))
    d.add(Polygon([x-4, y2+7, x, y2, x+4, y2+7],
                  fillColor=color, strokeColor=color, strokeWidth=0))

def arrowU(d, x, y1, y2, color=DARK, w=1.5):
    """Vertical upward arrow (y2 > y1)."""
    d.add(Line(x, y1, x, y2 - 7, strokeColor=color, strokeWidth=w))
    d.add(Polygon([x-4, y2-7, x, y2, x+4, y2-7],
                  fillColor=color, strokeColor=color, strokeWidth=0))

def diamond(d, cx, cy, hw, hh, text, bg=LYELLOW, tc=DARK, fs=9):
    """Diamond shape."""
    pts = [cx, cy+hh,  cx+hw, cy,  cx, cy-hh,  cx-hw, cy]
    d.add(Polygon(pts, fillColor=bg, strokeColor=DARK, strokeWidth=1))
    lines = str(text).split('\n')
    lh = fs * 1.3
    y0 = cy + (len(lines)-1) * lh / 2
    for ln in lines:
        d.add(String(cx, y0, ln, fontSize=fs, fontName='Helvetica',
                     fillColor=tc, textAnchor='middle'))
        y0 -= lh

def label(d, x, y, text, color=GRAY, fs=8):
    d.add(String(x, y, text, fontSize=fs, fontName='Helvetica',
                 fillColor=color, textAnchor='middle'))

# â”€â”€ Slide header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def slide_header(title, subtitle='', bg=DARK):
    data = [[Paragraph(title, SLIDE_HEAD)]]
    if subtitle:
        data[0].append(Paragraph(subtitle, SLIDE_SUB))
    t = Table([data[0]], colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), bg),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING',   (0,0), (-1,-1), 16),
        ('RIGHTPADDING',  (0,0), (-1,-1), 16),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    return t

def two_col(L, R, lw=None):
    lw = lw or CW * 0.5
    rw = CW - lw
    t = Table([[L, R]], colWidths=[lw, rw])
    t.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    return t

def badge_table(items, cols=3, cell_bg=LBLUE, cell_tc=DARK):
    """Grid of coloured badge cells."""
    rows, row = [], []
    for i, (txt, bg) in enumerate(items):
        row.append(Paragraph(f'<b>{txt}</b>', sty(f'b{i}', fontSize=10,
                   fontName='Helvetica-Bold', textColor=cell_tc, alignment=1)))
        if len(row) == cols:
            rows.append(row); row = []
    if row:
        while len(row) < cols: row.append(Paragraph('', SS['Normal']))
        rows.append(row)
    cw = CW / cols
    t = Table(rows, colWidths=[cw]*cols, rowHeights=28)
    cmds = [('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('GRID',(0,0),(-1,-1),0.5,WHITE),
            ('TOPPADDING',(0,0),(-1,-1),6),
            ('BOTTOMPADDING',(0,0),(-1,-1),6)]
    for i,(txt,bg) in enumerate(items):
        r,c = divmod(i, cols)
        cmds.append(('BACKGROUND',(c,r),(c,r), bg))
    t.setStyle(TableStyle(cmds))
    return t

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  SLIDE BUILDERS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def slide_cover():
    rows = [
        [Spacer(1, 2.5*cm)],
        [Paragraph('Multi-Agent Trip Planner', COVER_TITLE)],
        [Spacer(1, 0.5*cm)],
        [Paragraph('Built with LangGraph  -  Memory  -  Orchestrator  -  PDF Output', COVER_SUB)],
        [Spacer(1, 0.5*cm)],
        [Paragraph('Author: Kavin K   -   Course: AFDE Prodapt Chennai', COVER_AUTH)],
        [Paragraph(f'Presented: {dt.date.today():%B %Y}', COVER_AUTH)],
    ]
    bg = Table(rows, colWidths=[CW])
    bg.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), DARK),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 20),
        ('RIGHTPADDING',  (0,0), (-1,-1), 20),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    return [bg, PageBreak()]


def slide_big_picture():
    story = [slide_header('01 Â· What Is This System?',
                          'One query in â†’ 9 AI agents working together â†’ professional PDF out', bg=DARK)]
    story.append(Spacer(1, 0.3*cm))

    # Flow diagram: User Query â†’ System â†’ PDF
    dw, dh = CW, 130
    d = Drawing(dw, dh)

    # Three main boxes
    bw, bh = 160, 55
    gap = (dw - 3*bw) / 4

    x1, x2, x3 = gap, gap*2+bw, gap*3+bw*2
    by = (dh - bh) / 2

    rbox(d, x1, by, bw, bh, 'User Query\n"5-day Goa trip,\nBudget â‚¹30,000"',
         bg=LGRAY, tc=DARK, fs=10, rx=8, ry=8)
    rbox(d, x2, by, bw, bh, 'Multi-Agent\nTrip Planner\n(LangGraph)',
         bg=DARK, tc=WHITE, fs=11, bold=True, rx=8, ry=8)
    rbox(d, x3, by, bw, bh, 'Professional\nPDF Trip Report\n(6 sections)',
         bg=GREEN, tc=WHITE, fs=10, rx=8, ry=8)

    arrowR(d, x1+bw, by+bh/2, x2,     color=BLUE, w=2)
    arrowR(d, x2+bw, by+bh/2, x3,     color=BLUE, w=2)

    # "No API keys needed" label under center box
    d.add(String(x2+bw/2, by-18, 'âœ“ Works without API keys', fontSize=9,
                 fontName='Helvetica', fillColor=TEAL, textAnchor='middle'))

    story.append(d)
    story.append(Spacer(1, 0.2*cm))

    # Three key pillars
    pillars = [
        ('ðŸ¤–  Multi-Agent', LBLUE),
        ('ðŸ§   Orchestrator', LPURPLE),
        ('ðŸ’¾  Vector Memory', LGREEN),
        ('ðŸ›¡ï¸  Input Guardrails', LORANGE),
        ('ðŸ“Š  DeepEval Testing', LYELLOW),
        ('ðŸ“„  PDF Report', MID),
    ]
    story.append(badge_table(pillars, cols=6))
    story.append(PageBreak())
    return story


def slide_architecture():
    story = [slide_header('02 Â· System Architecture',
                          'Orchestrator at the centre â€” 9 specialist agents around it', bg=BLUE)]
    story.append(Spacer(1, 0.25*cm))

    base = os.path.join(os.path.dirname(__file__) if '__file__' in dir() else '.', '')
    img_path = os.path.join(base, 'diagrams', '06_trip_planner_architecture.png')
    if os.path.exists(img_path):
        img = RLImage(img_path, width=CW * 0.78, height=CH * 0.68)
        story.append(img)
    story.append(Spacer(1, 0.15*cm))

    bullets = [
        ('Red box', 'Orchestrator â€” the only decision-maker; routes everything', LRED),
        ('Blue boxes', '4 parallel specialists â€” Weather, Transport, Hotel, Places', LBLUE),
        ('Orange boxes', 'Real APIs these tools would call in production', LORANGE),
        ('Green boxes', 'Final Review â†’ PDF Generator â†’ Downloadable Report', LGREEN),
    ]
    rows = [[Paragraph(f'<b>{k}</b>', sty('bk', fontSize=10, fontName='Helvetica-Bold',
                       textColor=DARK, alignment=1)),
             Paragraph(v, BODY_SM)] for k, v, _ in bullets]
    t = Table(rows, colWidths=[100, CW-104])
    cmds = [('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),4),
            ('BOTTOMPADDING',(0,0),(-1,-1),4),
            ('LEFTPADDING',(0,0),(-1,-1),6),
            ('GRID',(0,0),(-1,-1),0.3,MID)]
    for i,(_,__,bg) in enumerate(bullets):
        cmds.append(('BACKGROUND',(0,i),(0,i), bg))
    t.setStyle(TableStyle(cmds))
    story.append(t)
    story.append(PageBreak())
    return story


def slide_tripstate():
    story = [slide_header('03 Â· TripState â€” The Shared Whiteboard',
                          'All 9 agents read from and write to one single TypedDict', bg=PURPLE)]
    story.append(Spacer(1, 0.3*cm))

    dw, dh = CW, 290
    d = Drawing(dw, dh)

    # Center big state box
    bx, by, bw, bh = dw*0.3, 50, dw*0.4, 210
    d.add(Rect(bx, by, bw, bh, 8, 8, fillColor=LPURPLE, strokeColor=PURPLE, strokeWidth=2))
    d.add(String(bx+bw/2, by+bh-18, 'TripState', fontSize=14,
                 fontName='Helvetica-Bold', fillColor=PURPLE, textAnchor='middle'))

    fields = [
        ('trip_preferences', LBLUE),
        ('weather_data', LBLUE),
        ('transport_data', LBLUE),
        ('hotel_data', LBLUE),
        ('places_data', LBLUE),
        ('budget_summary', LYELLOW),
        ('itinerary', LGREEN),
        ('review_status', LORANGE),
        ('pdf_status', LRED),
        ('messages [ ]', MID),
    ]
    fh = 16
    fy = by + bh - 36
    for name, bg in fields:
        d.add(Rect(bx+10, fy-fh+2, bw-20, fh, 3, 3, fillColor=bg,
                        strokeColor=MID, strokeWidth=0.5))
        d.add(String(bx+bw/2, fy-fh+5, name, fontSize=9, fontName='Courier',
                     fillColor=DARK, textAnchor='middle'))
        fy -= fh + 1

    # Left side agents writing
    agents_L = ['user_input\nagent', 'memory\nagent', 'weather\nagent', 'transport\nagent']
    for i, ag in enumerate(agents_L):
        ax = 8; ay = by + bh - 30 - i * 48
        rbox(d, ax, ay, 100, 36, ag, bg=LBLUE, tc=DARK, fs=8, rx=4, ry=4)
        arrowR(d, ax+100, ay+18, bx-4, color=BLUE, w=1.2)

    # Right side agents writing
    agents_R = ['hotel\nagent', 'places\nagent', 'budget\nagent', 'itinerary\nagent',
                'review\nagent', 'pdf\nagent']
    for i, ag in enumerate(agents_R):
        ax = bx + bw + 8; ay = by + bh - 22 - i * 35
        rbox(d, ax, ay, 100, 28, ag, bg=LGREEN, tc=DARK, fs=8, rx=4, ry=4)
        arrowR(d, bx+bw+4, ay+14, ax-4, color=GREEN, w=1.2)

    # Label
    d.add(String(dw/2, 14, 'Every agent reads from state â€¢ writes its own key â€¢ never touches other keys',
                 fontSize=9, fontName='Helvetica', fillColor=GRAY, textAnchor='middle'))

    # messages annotation
    d.add(String(bx+bw+116, by+14,
                 'messages uses operator.add\nâ†’ parallel writes APPEND\nnot overwrite',
                 fontSize=8, fontName='Helvetica', fillColor=ORANGE, textAnchor='start'))

    story.append(d)
    story.append(PageBreak())
    return story


def slide_llm_wrapper():
    story = [slide_header('04 Â· LLM Wrapper â€” Works With or Without OpenAI',
                          'One function hides the real/mock switch from all agents', bg=TEAL)]
    story.append(Spacer(1, 0.3*cm))

    dw, dh = CW * 0.55, 260
    d = Drawing(dw, dh)

    # llm_call() box at top
    rbox(d, dw/2-90, 215, 180, 34, 'llm_call(system, user)', bg=DARK,
         tc=WHITE, fs=11, bold=True, rx=8, ry=8)
    arrowD(d, dw/2, 215, 165)

    # Decision diamond
    diamond(d, dw/2, 140, 100, 35, 'OPENAI_API_KEY\nset?', fs=10)

    # Yes branch â†’ Real LLM
    arrowR(d, dw/2+100, 140, dw/2+180, color=GREEN, w=1.5)
    rbox(d, dw/2+180, 114, 130, 52, 'ChatOpenAI\ngpt-4o-mini\ntemperature=0.2',
         bg=LGREEN, tc=GREEN, fs=9, rx=6, ry=6)
    d.add(String(dw/2+155, 148, 'YES', fontSize=9, fontName='Helvetica-Bold',
                 fillColor=GREEN, textAnchor='middle'))

    # No branch â†’ Mock LLM
    arrowD(d, dw/2, 105, 55)
    rbox(d, dw/2-90, 18, 180, 52, 'Mock LLM\nrule-based if/elif\ndeterministic output',
         bg=LORANGE, tc=ORANGE, fs=9, rx=6, ry=6)
    d.add(String(dw/2+16, 88, 'NO', fontSize=9, fontName='Helvetica-Bold',
                 fillColor=ORANGE, textAnchor='middle'))

    story_left = [d]

    # Right: what the mock returns
    right_data = [
        ['Prompt containsâ€¦', 'Mock returns'],
        ['"itinerary"',  'Day 1-5 plan text'],
        ['"review"',     '{"approved": true}'],
        ['"packing"',    'sunscreen; swimsuit; â€¦'],
        ['"summary"',    'A relaxed 5-day tripâ€¦'],
        ['anything else','Acknowledged.'],
    ]
    rt = Table(right_data, colWidths=[CW*0.22, CW*0.25])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TEAL),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 10),
        ('GRID',       (0,0), (-1,-1), 0.5, MID),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
    ]))

    right_col = [
        Spacer(1, 0.2*cm),
        Paragraph('<b>Mock LLM behaviour</b>', H2),
        rt,
        Spacer(1, 0.3*cm),
        Paragraph('âœ“ Produces a real PDF with zero API costs', sty('ok', fontSize=10,
                  fontName='Helvetica-Bold', textColor=GREEN)),
        Paragraph('âœ“ Same output every run (seed=42)', sty('ok2', fontSize=10,
                  fontName='Helvetica', textColor=GREEN)),
    ]

    story.append(two_col(story_left, right_col, lw=CW*0.5))
    story.append(PageBreak())
    return story


def slide_guardrails():
    story = [slide_header('05 Â· Input Guardrails â€” 3-Layer Validation',
                          'Every input is validated BEFORE any agent or LLM sees it', bg=ORANGE)]
    story.append(Spacer(1, 0.25*cm))

    dw, dh = CW, 200
    d = Drawing(dw, dh)

    bw, bh = 138, 68
    gap = (dw - 4*bw - 100) / 5
    y_box = (dh - bh) / 2

    # Input
    rbox(d, gap, y_box+10, 90, 50, 'User Input\n(raw query\n+ prefs)', bg=LGRAY, tc=DARK, fs=9, rx=6)

    positions = [
        (gap+90+gap,   'Guard 1\nRaw Query',   'â€¢ Injection scan\nâ€¢ Off-topic block\nâ€¢ 2000-char cap', LORANGE),
        (gap*3+90+bw,  'Guard 2\nPreferences', 'â€¢ 9-field types\nâ€¢ Date range check\nâ€¢ Valid enums',   LYELLOW),
        (gap*4+90+bw*2,'Guard 3\nBusiness',    'â€¢ src â‰  dst\nâ€¢ Budget floor\n  â‚¹300/person/day',       LGREEN),
    ]

    prev_x = gap + 90
    for i, (x, title, desc, bg) in enumerate(positions):
        arrowR(d, prev_x, y_box+10+25, x, color=DARK, w=1.5)
        # Guard box (split into header + body)
        d.add(Rect(x, y_box, bw, bh, 6, 6, fillColor=bg, strokeColor=DARK, strokeWidth=1))
        d.add(Rect(x, y_box+bh-22, bw, 22, 6, 6, fillColor=ORANGE, strokeColor=DARK, strokeWidth=1))
        d.add(Rect(x, y_box+bh-22, bw, 11, fillColor=ORANGE, strokeColor=ORANGE, strokeWidth=0))
        d.add(String(x+bw/2, y_box+bh-15, title.replace('\n', ' '),
                     fontSize=9, fontName='Helvetica-Bold', fillColor=WHITE, textAnchor='middle'))
        lines = desc.split('\n')
        fy = y_box + bh - 34
        for ln in lines:
            d.add(String(x+8, fy, ln, fontSize=8, fontName='Helvetica',
                         fillColor=DARK, textAnchor='start'))
            fy -= 13
        prev_x = x + bw

    # Arrow to agents
    ax = prev_x + gap
    arrowR(d, prev_x, y_box+10+25, ax, color=GREEN, w=2)
    rbox(d, ax, y_box+10, 90, 50, 'Agents\n& LLMs', bg=LGREEN, tc=GREEN, fs=10, bold=True, rx=6)

    # Error path
    d.add(String(dw/2, 14, 'âœ— Any guard fails â†’ InputGuardrailError raised â†’ orchestrator handles gracefully',
                 fontSize=9, fontName='Helvetica-Bold', fillColor=RED, textAnchor='middle'))

    # LLM sanitiser note
    d.add(String(dw/2, dh-14,
                 'Bonus: LLM Input Sanitiser â€” strips control chars, caps length before every llm_call()',
                 fontSize=8.5, fontName='Helvetica', fillColor=DARK, textAnchor='middle'))

    story.append(d)

    # What each guard catches table
    data = [
        ['Guard', 'What it blocks', 'Example that fails'],
        ['Guard 1 â€” Raw Query',    'Prompt injection; off-topic; >2000 chars',
         '"Ignore all previous instructionsâ€¦"'],
        ['Guard 2 â€” Preferences', 'Wrong types; bad dates; unknown enums',
         'start_date="yesterday", days="lots"'],
        ['Guard 3 â€” Business',    'Source = destination; budget too low',
         'source="Goa", dest="Goa" or budget=â‚¹100 for 5 days'],
    ]
    t = Table(data, colWidths=[130, CW*0.38, CW*0.36])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ORANGE),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('GRID',       (0,0), (-1,-1), 0.5, MID),
        ('ROWBACKGROUNDS', (0,1),(-1,-1),[WHITE, LORANGE]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(Spacer(1, 0.15*cm))
    story.append(t)
    story.append(PageBreak())
    return story


def slide_tools():
    story = [slide_header('06 Â· Tools â€” Mock APIs (Swappable)',
                          'Each tool is a Python function with # TODO: real API â€” swap any time', bg=colors.HexColor('#C55A11'))]
    story.append(Spacer(1, 0.25*cm))

    dw, dh = CW, 200
    d = Drawing(dw, dh)

    tools = [
        ('tool_get_weather()\ncity, start, days', 'OpenWeather\nAPI',   LBLUE,   BLUE),
        ('tool_search_transport()\norigin, dest, mode', 'Skyscanner /\nIRCTC',   LPURPLE, PURPLE),
        ('tool_search_hotels()\ncity, budget, vibe', 'Booking.com\nAPI',    LGREEN,  GREEN),
        ('tool_explore_places()\ncity, interests', 'Google\nPlaces API', LYELLOW, YELLOW),
        ('tool_budget_calculator()\ntransport+hotel+food', 'Pure Python\nMath',       LORANGE, ORANGE),
    ]

    n = len(tools)
    tw = (dw - 20) / n
    for i, (mock, real, bg, tc) in enumerate(tools):
        x = 10 + i * tw
        # Mock tool box
        rbox(d, x+4, 110, tw-8, 58, mock, bg=bg, tc=tc, fs=9, rx=5, ry=5)
        d.add(String(x+tw/2, 100, 'â†•  swap', fontSize=8, fontName='Helvetica-Bold',
                     fillColor=GRAY, textAnchor='middle'))
        # Real API box
        rbox(d, x+4, 30, tw-8, 50, real, bg=LGRAY, tc=GRAY, fs=9, rx=5, ry=5, border=MID, bw=1)

    d.add(String(dw/2, 195, 'Mock tools (used now â€” deterministic, seed=42)',
                 fontSize=9, fontName='Helvetica-Bold', fillColor=DARK, textAnchor='middle'))
    d.add(String(dw/2, 15, 'Real APIs (swap in production â€” interface stays the same)',
                 fontSize=9, fontName='Helvetica-Bold', fillColor=GRAY, textAnchor='middle'))

    story.append(d)
    story.append(Spacer(1, 0.2*cm))

    row = [[
        Paragraph('<b>Why mock tools?</b>', sty('wm', fontSize=11, fontName='Helvetica-Bold', textColor=DARK)),
        Paragraph('âœ“ Zero API cost   âœ“ Same output every run (seeded)   âœ“ No rate limits   âœ“ Works offline',
                  sty('why', fontSize=10, fontName='Helvetica', textColor=DARK)),
    ]]
    info = Table(row, colWidths=[130, CW-134])
    info.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), LGRAY),
        ('TOPPADDING', (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING', (0,0),(-1,-1), 10),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
    ]))
    story.append(info)
    story.append(PageBreak())
    return story


def slide_memory():
    story = [slide_header('07 Â· Memory Store â€” Semantic Vector Database',
                          'Remembers user preferences across trips using cosine similarity', bg=PURPLE)]
    story.append(Spacer(1, 0.2*cm))

    dw, dh = CW, 220
    d = Drawing(dw, dh)

    # === add() path (top) ===
    rbox(d, 10, 158, 110, 45, 'New memory\n"User loves beach\nand seafood"',
         bg=LGRAY, tc=DARK, fs=9, rx=5)
    arrowR(d, 120, 180, 170, color=PURPLE, w=1.5)
    rbox(d, 170, 158, 120, 45, '_embed(text)\nsentence-transformers\nall-MiniLM-L6-v2',
         bg=LPURPLE, tc=PURPLE, fs=9, rx=5)
    arrowR(d, 290, 180, 340, color=PURPLE, w=1.5)
    rbox(d, 340, 140, 100, 80, 'MemoryStore\n_texts[]\n_vecs[]\n_meta[]',
         bg=DARK, tc=WHITE, fs=9, bold=True, rx=5)
    d.add(String(dw/2-80, 215, 'add() path', fontSize=9, fontName='Helvetica-Bold',
                 fillColor=PURPLE, textAnchor='middle'))

    # === query() path (bottom) ===
    rbox(d, 10, 58, 110, 45, 'Query\n"Goa mid seafood"',
         bg=LYELLOW, tc=DARK, fs=9, rx=5)
    arrowR(d, 120, 80, 170, color=ORANGE, w=1.5)
    rbox(d, 170, 58, 120, 45, '_embed(query)\nâ†’ query vector\n(384 dimensions)',
         bg=LYELLOW, tc=ORANGE, fs=9, rx=5)
    arrowR(d, 290, 80, 340, color=ORANGE, w=1.5)
    rbox(d, 340, 50, 100, 55, 'dot product\nsimilarity\nfor each vec',
         bg=LORANGE, tc=ORANGE, fs=9, rx=5)

    # Arrow from store down to similarity
    arrowD(d, 390, 140, 105, color=ORANGE, w=1.2)

    arrowR(d, 440, 77, 490, color=GREEN, w=1.5)
    rbox(d, 490, 55, 120, 45, 'Return top-k\nmost similar\nmemories',
         bg=LGREEN, tc=GREEN, fs=10, bold=True, rx=5)

    d.add(String(200, 24, 'query() path', fontSize=9, fontName='Helvetica-Bold',
                 fillColor=ORANGE, textAnchor='middle'))

    # Fallback note
    d.add(String(dw-100, 195,
                 'No sentence-transformers?\nâ†’ hashed bag-of-words\nfallback (auto)',
                 fontSize=8, fontName='Helvetica', fillColor=GRAY, textAnchor='middle'))

    story.append(d)

    # Production swap note
    swap = [
        ['In this notebook', 'In production'],
        ['NumPy-based MemoryStore (30 lines)', 'Chroma / FAISS / Pinecone'],
        ['sentence-transformers (local model)', 'OpenAI text-embedding-3-small'],
        ['In-process (lost on restart)', 'Persistent disk/cloud storage'],
    ]
    t = Table(swap, colWidths=[CW*0.46, CW*0.46])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), PURPLE),
        ('TEXTCOLOR',  (0,0),(-1,0), WHITE),
        ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0),(-1,-1), 10),
        ('GRID',       (0,0),(-1,-1), 0.5, MID),
        ('ROWBACKGROUNDS', (0,1),(-1,-1),[WHITE, LPURPLE]),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('ALIGN',      (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
    ]))
    story.append(Spacer(1, 0.15*cm))
    story.append(t)
    story.append(PageBreak())
    return story


def slide_agents():
    story = [slide_header('08 Â· Specialist Agents â€” One Job Each',
                          'Each agent: read state â†’ call tool â†’ return updated keys only', bg=BLUE)]
    story.append(Spacer(1, 0.2*cm))

    agents = [
        ('1. user_input\nagent',    'Validates & fills\ndefault prefs',    LBLUE,   DARK),
        ('2. memory\nagent',        'Recalls past\nuser preferences',       LPURPLE, PURPLE),
        ('3. weather\nagent',       'Gets 5-day\nforecast',                 LBLUE,   DARK),
        ('4. transport\nagent',     'Searches flights\ntrains & cars',       LBLUE,   DARK),
        ('5. hotel\nagent',         'Finds hotels\nwithin budget',           LBLUE,   DARK),
        ('6. places\nagent',        'Discovers top\nattractions',            LBLUE,   DARK),
        ('7. budget\nagent',        'Calculates total\ncost breakdown',       LYELLOW, DARK),
        ('8. itinerary\nagent',     'Builds day-wise\nplan (+ LLM)',         LGREEN,  GREEN),
        ('9. final_review\nagent',  'Checks budget,\nweather, completeness', LORANGE, ORANGE),
    ]

    dw, dh = CW, 200
    d = Drawing(dw, dh)

    n = 9
    cols = 5; rows_n = 2
    bw_a, bh_a = (dw - 30) / cols - 6, 58
    gx = ((dw - 30) / cols)

    for i, (name, role, bg, tc) in enumerate(agents):
        col = i % cols
        row = i // cols
        x = 15 + col * gx
        y = dh - bh_a - 20 - row * (bh_a + 16)
        rbox(d, x, y, bw_a, bh_a, f'{name}\n{role}', bg=bg, tc=tc, fs=8, rx=5, ry=5)

    # Pattern label at bottom
    d.add(String(dw/2, 10,
                 'Pattern: def agent(state: TripState) â†’ dict  Â·  Read â†’ Tool â†’ Return {key: value}',
                 fontSize=9, fontName='Courier', fillColor=DARK, textAnchor='middle'))

    story.append(d)
    story.append(Spacer(1, 0.1*cm))

    # Parallel note
    para_note = Table([[
        Paragraph('âš¡ 4 agents run in PARALLEL', sty('pn', fontSize=11,
                  fontName='Helvetica-Bold', textColor=BLUE)),
        Paragraph('Weather, Transport, Hotel, Places all fire at the same time '
                  'via the specialists_fanout node. They write to different state keys â€” '
                  'no collision. LangGraph waits for all 4 before proceeding.',
                  sty('pnd', fontSize=10, fontName='Helvetica', textColor=DARK)),
    ]], colWidths=[170, CW-174])
    para_note.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), LBLUE),
        ('TOPPADDING', (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING', (0,0),(-1,-1), 10),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ('GRID',       (0,0),(-1,-1), 0.5, BLUE),
    ]))
    story.append(para_note)
    story.append(PageBreak())
    return story


def slide_orchestrator():
    story = [slide_header('09 Â· Orchestrator â€” The Brain / Router',
                          'Checks state after every step and decides what runs next', bg=RED)]
    story.append(Spacer(1, 0.2*cm))

    dw, dh = CW * 0.58, 300
    d = Drawing(dw, dh)

    dw2 = dw / 2

    # START
    rbox(d, dw2-40, 270, 80, 24, 'START', bg=DARK, tc=WHITE, fs=10, bold=True, rx=12)
    arrowD(d, dw2, 270, 240)

    # Orchestrator centre
    rbox(d, dw2-65, 200, 130, 36, 'ORCHESTRATOR\n(checks state)', bg=RED, tc=WHITE,
         fs=11, bold=True, rx=8)

    # 6 decision branches going down
    branches = [
        (dw2-220, 'no prefs?',       'user_input',    LGRAY),
        (dw2-130, 'no memory?',      'memory',        LPURPLE),
        (dw2-40,  'no data?',        'specialists\nfanout', LBLUE),
        (dw2+50,  'no budget?',      'budget',        LYELLOW),
        (dw2+130, 'no itinerary?',   'itinerary',     LGREEN),
        (dw2+210, 'no review?',      'review',        LORANGE),
    ]

    for bx, cond, action, bg in branches:
        # Line down
        d.add(Line(dw2, 200, bx, 148, strokeColor=DARK, strokeWidth=0.8))
        d.add(String(bx, 156, cond, fontSize=7, fontName='Helvetica',
                     fillColor=GRAY, textAnchor='middle'))
        rbox(d, bx-40, 110, 80, 34, action, bg=bg, tc=DARK, fs=8, rx=4)
        # Return arrow back
        d.add(Line(bx, 110, dw2-10 + branches.index((bx,cond,action,bg))*4, 236,
                   strokeColor=MID, strokeWidth=0.6, strokeDashArray=[3,2]))

    # Approved path
    arrowD(d, dw2, 200, 140)
    d.add(String(dw2+8, 158, 'approved?', fontSize=8, fontName='Helvetica-Bold',
                 fillColor=GREEN, textAnchor='start'))
    rbox(d, dw2-50, 80, 100, 30, 'memory_update\nâ†’ pdf â†’ END', bg=LGREEN, tc=GREEN,
         fs=8, bold=True, rx=4)

    # Retry loop
    d.add(String(50, 58, 'â†» retry loop (max 3x):\nclear budget/itinerary/review\nâ†’ re-run failing agent',
                 fontSize=8, fontName='Helvetica', fillColor=ORANGE, textAnchor='start'))

    story_left = [d]

    right_items = [
        Spacer(1, 0.3*cm),
        Paragraph('<b>Why rule-based?</b>', H2),
        Paragraph('Transparent, debuggable, deterministic.', BODY_SM),
        Spacer(1, 0.2*cm),
        Paragraph('<b>Swap for LLM routing?</b>', H2),
        Paragraph('Yes â€” replace the if/elif with:\n'
                  'llm_call(SUPERVISOR_PROMPT, state)\n'
                  'Same graph works identically.', CODE_ST),
        Spacer(1, 0.3*cm),
        Paragraph('<b>Retry logic</b>', H2),
        Paragraph('If review fails:', BODY_SM),
        Paragraph('â€¢ Over budget â†’ retry hotel agent', BULLET),
        Paragraph('â€¢ Too rainy â†’ retry places agent', BULLET),
        Paragraph('â€¢ Transport issue â†’ retry transport', BULLET),
        Paragraph('â€¢ Gives up after 3 retries', BULLET),
        Spacer(1, 0.2*cm),
        Paragraph('<b>Checkpointing</b>', H2),
        Paragraph('MemorySaver saves full state after\nevery step â†’ crash recovery & replay.',
                  BODY_SM),
    ]

    story.append(two_col(story_left, right_items, lw=CW*0.56))
    story.append(PageBreak())
    return story


def slide_langgraph():
    story = [slide_header('10 Â· LangGraph Workflow â€” The Compiled Graph',
                          '13 nodes Â· fan-out parallelism Â· conditional edges Â· MemorySaver checkpoints', bg=DARK)]
    story.append(Spacer(1, 0.2*cm))

    base = '.'
    img_path = os.path.join(base, 'trip_planner_graph.png')
    if os.path.exists(img_path):
        img = RLImage(img_path, width=CW * 0.6, height=CH * 0.48)
        story.append(img)
    story.append(Spacer(1, 0.15*cm))

    concepts = [
        ['Concept', 'What it means in this graph', 'Code'],
        ['Fan-out', '4 specialists run in parallel â€” one edge from fanout to each',
         'g.add_edge("specialists_fanout", "weather")  Ã—4'],
        ['Conditional edge', 'Orchestrator decides the next node each pass',
         'g.add_conditional_edges("orchestrator", route_fn, {...})'],
        ['MemorySaver', 'Full state saved after every step â€” crash-safe & resumable',
         'app = g.compile(checkpointer=MemorySaver())'],
        ['thread_id', 'Isolates each trip planning session',
         'config={"configurable": {"thread_id": "..."}}'],
    ]
    t = Table(concepts, colWidths=[90, CW*0.4, CW*0.37])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), DARK),
        ('TEXTCOLOR',  (0,0),(-1,0), WHITE),
        ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0),(-1,-1), 9),
        ('GRID',       (0,0),(-1,-1), 0.5, MID),
        ('ROWBACKGROUNDS', (0,1),(-1,-1),[WHITE, LGRAY]),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ('FONTNAME',   (2,1),(2,-1), 'Courier'),
        ('FONTSIZE',   (2,1),(2,-1), 8),
    ]))
    story.append(t)
    story.append(PageBreak())
    return story


def slide_demo_run():
    story = [slide_header('11 Â· Demo Run â€” 18 Steps Live',
                          'Input: "5-day Goa trip from Bangalore, â‚¹30,000, couple, flight"', bg=TEAL)]
    story.append(Spacer(1, 0.2*cm))

    dw, dh = CW, 230
    d = Drawing(dw, dh)

    steps = [
        ('00', 'orchestrator',        'â†’ memory',           LPURPLE),
        ('01', 'memory',              'recalled 2 items',    LPURPLE),
        ('02', 'orchestrator',        'â†’ fanout',            LBLUE),
        ('03', 'specialists_fanout',  'dispatch Ã—4',         LBLUE),
        ('04-07', 'hotel / places\ntransport / weather', 'parallel!', LBLUE),
        ('08', 'orchestrator',        'â†’ budget',            LYELLOW),
        ('09', 'budget',              'calculated',          LYELLOW),
        ('10', 'orchestrator',        'â†’ itinerary',         LGREEN),
        ('11', 'itinerary',           'day plan built',      LGREEN),
        ('12', 'orchestrator',        'â†’ review',            LORANGE),
        ('13', 'review',              'âœ“ APPROVED',          LGREEN),
        ('14', 'orchestrator',        'â†’ memory_updateâ†’pdf', LGREEN),
        ('15', 'memory_update',       'memory saved',        LPURPLE),
        ('16', 'pdf agent',           'trip_report.pdf âœ“',   LGREEN),
        ('17', 'orchestrator',        'â†’ END',               DARK),
    ]

    cols = 5
    bw_s = (dw - 20) / cols - 4
    bh_s = 32
    row_h = bh_s + 8

    for i, (step, node, note, bg) in enumerate(steps):
        col = i % cols
        row = i // cols
        x = 10 + col * (bw_s + 4)
        y = dh - 20 - row * row_h - bh_s

        tc = WHITE if bg == DARK else DARK
        rbox(d, x, y, bw_s, bh_s, f'[{step}] {node}\n{note}',
             bg=bg, tc=tc, fs=7.5, rx=4)

    d.add(String(dw/2, 8, 'Total runtime: < 5 seconds  Â·  Output: trip_report.pdf',
                 fontSize=9, fontName='Helvetica-Bold', fillColor=GREEN, textAnchor='middle'))

    story.append(d)
    story.append(Spacer(1, 0.15*cm))

    # Results table
    results = [
        ['Output', 'Value'],
        ['Hotel',     'Backwoods Hostel (fits â‚¹30k budget)'],
        ['Transport', 'IndiGo flight â€” â‚¹4,500'],
        ['Total cost','â‚¹26,800  (under â‚¹30,000 âœ“)'],
        ['Headline',  "A relaxed 5-day couple's beach trip to Goa with seafood and nightlife."],
        ['Review',    'âœ“ APPROVED â€” 0 issues'],
        ['PDF',       'trip_report.pdf â€” 6 sections, A4 format'],
    ]
    t = Table(results, colWidths=[90, CW-94])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), TEAL),
        ('TEXTCOLOR',  (0,0),(-1,0), WHITE),
        ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0),(-1,-1), 10),
        ('GRID',       (0,0),(-1,-1), 0.5, MID),
        ('ROWBACKGROUNDS', (0,1),(-1,-1),[WHITE, LGRAY]),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ('FONTNAME',   (0,5),(0,5), 'Helvetica-Bold'),
        ('TEXTCOLOR',  (0,5),(0,5), GREEN),
    ]))
    story.append(t)
    story.append(PageBreak())
    return story


def slide_pdf_output():
    story = [slide_header('12 Â· PDF Generator â€” 6-Section Trip Report',
                          'ReportLab builds a professional A4 PDF from the final state', bg=GREEN)]
    story.append(Spacer(1, 0.2*cm))

    dw, dh = CW, 180
    d = Drawing(dw, dh)

    sections = [
        ('Cover Page',      'Route, headline,\napproval status',     DARK,    WHITE),
        ('Â§1 Transport',    'All options table\nrecommended flight',  LBLUE,   DARK),
        ('Â§2 Hotel',        'Candidates table\ntop pick highlighted', LPURPLE, DARK),
        ('Â§3 Itinerary\n+ Weather', 'Day-wise plan\n+ forecast table', LGREEN, DARK),
        ('Â§4 Budget',       'Cost breakdown\nover/under message',     LYELLOW, DARK),
        ('Â§5 Packing',      'LLM-generated\nchecklist â˜',            LORANGE, DARK),
        ('Â§6 Emergency',    'India contacts\nhotel reception',        LRED,    DARK),
    ]

    n = len(sections)
    bw_p = (dw - 20) / n - 4
    bh_p = 120

    for i, (title, desc, bg, tc) in enumerate(sections):
        x = 10 + i * (bw_p + 4)
        rbox(d, x, 40, bw_p, bh_p, f'{title}\n\n{desc}',
             bg=bg, tc=tc, fs=8, rx=5)
        # Page number indicator at bottom
        d.add(String(x + bw_p/2, 25, f'Page {i+1}', fontSize=7,
                     fontName='Helvetica', fillColor=GRAY, textAnchor='middle'))

    d.add(String(dw/2, 170, 'Each section draws data directly from the final TripState â€” no re-computation',
                 fontSize=9, fontName='Helvetica', fillColor=DARK, textAnchor='middle'))

    d.add(String(dw/2, 8, 'Generated with ReportLab  Â·  A4 format  Â·  Available at: trip_report.pdf',
                 fontSize=9, fontName='Helvetica-Bold', fillColor=GREEN, textAnchor='middle'))

    story.append(d)
    story.append(Spacer(1, 0.2*cm))

    info = [
        ['Agent reads from state', 'Writes to PDF'],
        ['trip_preferences',       'Cover: route, days, travelers, budget'],
        ['itinerary["headline"]',  'Cover: AI-generated headline'],
        ['transport_data',         'Section 1: All options + recommended'],
        ['hotel_data',             'Section 2: Candidates + top pick'],
        ['itinerary + weather_data','Section 3: Day plan + forecast table'],
        ['budget_summary',         'Section 4: Breakdown table + delta message'],
        ['llm_call(packing prompt)','Section 5: Packing checklist items'],
    ]
    t = Table(info, colWidths=[CW*0.38, CW*0.54])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), GREEN),
        ('TEXTCOLOR',  (0,0),(-1,0), WHITE),
        ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0),(-1,-1), 9),
        ('GRID',       (0,0),(-1,-1), 0.5, MID),
        ('ROWBACKGROUNDS', (0,1),(-1,-1),[WHITE, LGREEN]),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ('FONTNAME',   (0,1),(-1,-1), 'Courier'),
        ('FONTSIZE',   (0,1),(-1,-1), 8),
    ]))
    story.append(t)
    story.append(PageBreak())
    return story


def slide_deepeval():
    story = [slide_header('13 Â· DeepEval â€” Automated Quality Evaluation',
                          '4 rule-based metrics (no API key) + 2 LLM-based metrics (with OpenAI key)', bg=colors.HexColor('#1F3864'))]
    story.append(Spacer(1, 0.2*cm))

    dw, dh = CW, 165
    d = Drawing(dw, dh)

    metrics = [
        ('BudgetAdherence\nMetric',    'Total cost â‰¤\nstated budget?', LYELLOW, DARK, '1.00', 'PASS'),
        ('PreferenceMatch\nMetric',    'Interests in\nitinerary text?', LPURPLE, DARK, '0.67', 'PASS'),
        ('Itinerary\nCompleteness',    'Days + headline\n+ hotel + transport?', LGREEN, DARK, '1.00', 'PASS'),
        ('Review\nApproval',           'final_review\napproved?',       LORANGE, DARK, '1.00', 'PASS'),
        ('AnswerRelevancy\n(OpenAI)',   'Itinerary relevant\nto query?',  LBLUE,  DARK, 'â€”',   'LLM'),
        ('Faithfulness\n(OpenAI)',      'No hallucinations\nin output?',  LBLUE,  DARK, 'â€”',   'LLM'),
    ]

    n = len(metrics)
    bw_m = (dw - 20) / n - 4

    for i, (name, desc, bg, tc, score, result) in enumerate(metrics):
        x = 10 + i * (bw_m + 4)
        rbox(d, x, 60, bw_m, 90, f'{name}\n\n{desc}', bg=bg, tc=tc, fs=8, rx=5)
        # Score badge
        sbg = LGREEN if result == 'PASS' else LBLUE if result == 'LLM' else LRED
        stc = GREEN if result == 'PASS' else BLUE if result == 'LLM' else RED
        rbox(d, x+6, 36, bw_m-12, 20, f'Score: {score}  [{result}]',
             bg=sbg, tc=stc, fs=8, bold=True, rx=3)

    d.add(String(dw/2, 20, 'TC-1: Goa trip â€” 4/4 rule-based PASS  Â·  TC-2: Your trip â€” 3/4 PASS (Preference Match failed â†’ real finding!)',
                 fontSize=8.5, fontName='Helvetica-Bold', fillColor=DARK, textAnchor='middle'))

    d.add(String(dw/2, 152, 'Rule-based metrics (no API needed)',
                 fontSize=9, fontName='Helvetica-Bold', fillColor=DARK, textAnchor='middle'))
    d.add(String(dw*5/6 + 20, 152, 'LLM-based (needs key)',
                 fontSize=9, fontName='Helvetica-Bold', fillColor=BLUE, textAnchor='middle'))

    story.append(d)
    story.append(Spacer(1, 0.15*cm))

    tc2_note = Table([[
        Paragraph('âš ï¸  TC-2 Preference Match FAIL is a REAL finding', sty('rn', fontSize=11,
                  fontName='Helvetica-Bold', textColor=ORANGE)),
        Paragraph('Bangalore trip interests = ["nature", "party"] â€” '
                  'neither word appeared in the itinerary output text. '
                  'This tells us the itinerary_agent needs to reference user interests '
                  'more explicitly when attraction data is sparse. '
                  '<b>Evaluation found a real bug.</b>',
                  sty('rnd', fontSize=10, fontName='Helvetica', textColor=DARK)),
    ]], colWidths=[200, CW-204])
    tc2_note.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), LORANGE),
        ('TOPPADDING', (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING', (0,0),(-1,-1), 10),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ('GRID',       (0,0),(-1,-1), 0.5, ORANGE),
    ]))
    story.append(tc2_note)
    story.append(PageBreak())
    return story


def slide_summary():
    story = [slide_header('14 Â· Summary â€” What Was Built',
                          'Every assignment deliverable met + production-ready design patterns', bg=DARK)]
    story.append(Spacer(1, 0.2*cm))

    left_items = [
        Paragraph('<b>Assignment Deliverables âœ“</b>', H2),
        Spacer(1, 0.1*cm),
    ]
    checklist = [
        ('Architecture diagram',      'Section 1 â€” diagrams/06_trip_planner_architecture.png'),
        ('LangGraph workflow',         'Section 9 â€” 13-node compiled graph'),
        ('Agent design (9 agents)',    'Section 6 â€” one function per agent'),
        ('Orchestrator logic',         'Section 7 â€” rule-based router + retry loop'),
        ('Tool design (5 tools)',      'Section 4 â€” mock APIs, swappable'),
        ('Memory system',              'Section 5 â€” vector store, semantic recall'),
        ('PDF generator',              'Section 8 â€” ReportLab, 6-section A4'),
        ('Working demo',               'Section 10 â€” app.stream(), 18 steps'),
        ('Input Guardrails',           'Section 3.5 â€” 3-layer validation'),
        ('DeepEval evaluation',        'Section 14 â€” 4+2 metrics, 2 test cases'),
    ]
    for item, where in checklist:
        left_items.append(Paragraph(f'<b>âœ“</b> {item}', BULLET))
    left_items.append(Spacer(1, 0.1*cm))
    left_items.append(Paragraph(f'<i>{where}</i>', BODY_SM))

    right_items = [
        Paragraph('<b>Production Upgrades (Easy)</b>', H2),
        Spacer(1, 0.1*cm),
    ]
    upgrades = [
        ('Real Weather',    'Replace tool_get_weather()  â†’  OpenWeatherMap API'),
        ('Real Flights',    'Replace tool_search_transport()  â†’  Skyscanner/Amadeus'),
        ('Real Hotels',     'Replace tool_search_hotels()  â†’  Booking.com API'),
        ('Real LLM',        'Set OPENAI_API_KEY  â†’  gpt-4o-mini auto-activated'),
        ('Real Vector DB',  'Swap MemoryStore class  â†’  Chroma / FAISS / Pinecone'),
        ('LLM Routing',     'Replace if/elif  â†’  llm_call(SUPERVISOR_PROMPT, state)'),
    ]
    data = [['Upgrade', 'What to change']] + [[k, v] for k, v in upgrades]
    t = Table(data, colWidths=[80, CW*0.38])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), DARK),
        ('TEXTCOLOR',  (0,0),(-1,0), WHITE),
        ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0),(-1,-1), 9),
        ('GRID',       (0,0),(-1,-1), 0.5, MID),
        ('ROWBACKGROUNDS', (0,1),(-1,-1),[WHITE, LGRAY]),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ('FONTNAME',   (1,1),(1,-1), 'Courier'),
        ('FONTSIZE',   (1,1),(1,-1), 8),
    ]))
    right_items.append(t)
    right_items.append(Spacer(1, 0.15*cm))
    right_items.append(Paragraph(
        '<b>Key pattern:</b> Agents are pure functions. Tools are swappable. '
        'State is typed. Graph is compiled. All production patterns â€” just mock data.',
        sty('kp', fontSize=10, fontName='Helvetica', textColor=DARK, backColor=LYELLOW,
            leftIndent=6, rightIndent=6)))

    story.append(two_col(left_items, right_items, lw=CW*0.46))
    story.append(PageBreak())
    return story


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  ASSEMBLE & BUILD
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def build():
    out = 'Trip_Planner_Presentation.pdf'
    doc = SimpleDocTemplate(
        out,
        pagesize=landscape(A4),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title='Multi-Agent Trip Planner â€” Presentation',
        author='Kavin K',
    )

    story = []
    story += slide_cover()
    story += slide_big_picture()
    story += slide_architecture()
    story += slide_tripstate()
    story += slide_llm_wrapper()
    story += slide_guardrails()
    story += slide_tools()
    story += slide_memory()
    story += slide_agents()
    story += slide_orchestrator()
    story += slide_langgraph()
    story += slide_demo_run()
    story += slide_pdf_output()
    story += slide_deepeval()
    story += slide_summary()

    doc.build(story)
    print(f'âœ“ Saved {out}  ({os.path.getsize(out):,} bytes,  15 slides)')
    return out

if __name__ == '__main__':
    build()

