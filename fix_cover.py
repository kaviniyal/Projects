import re

with open('generate_presentation.py', 'r', encoding='utf-8') as f:
    src = f.read()

cover_new = '''def slide_cover():
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
    return [bg, PageBreak()]'''

src2 = re.sub(r'def slide_cover\(\):.*?return \[bg, PageBreak\(\)\]',
              cover_new, src, flags=re.DOTALL)

if src2 == src:
    print('ERROR: pattern not matched!')
    # Debug: find the function
    idx = src.find('def slide_cover')
    print(repr(src[idx:idx+400]))
else:
    print('Cover function replaced OK')
    with open('generate_presentation.py', 'w', encoding='utf-8') as f:
        f.write(src2)
    print('File saved.')
