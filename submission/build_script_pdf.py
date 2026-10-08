# -*- coding: utf-8 -*-
"""Render submission/VIDEO_SCRIPT.md to a formatted PDF.

WHY THIS EXISTS
----------------
The script gets rewritten whenever the story or the numbers change, and a
hand-formatted PDF would silently drift from it the same way figures.json
once drifted from the engine (see build_figures.py). So the PDF is
generated from the committed markdown, not maintained as a parallel
document:

    python submission/build_script_pdf.py

Regenerate it every time VIDEO_SCRIPT.md changes, same discipline as the
deck and the figures file.

Purpose-built for this one file's exact markdown shapes (headings,
tables, blockquotes, fenced code, bullets, numbered lists, bold/italic
stage directions) rather than a general markdown engine - a generic
converter would not know that a line in double-star bold with no "Need:"
or "Click" prefix is a mini step-heading in Version B, or that a short
lead-in line ending in ":" should stay glued to the table or diagram that
follows it. Both of those are specific to how this script is written.

Keeps the document's visual language consistent with the deck and the
UI: Georgia headings, Arial body, the water-blue / pearl palette pulled
from frontend/style.css, so a reader does not meet a third visual
identity for the same project.

Requires reportlab (`pip install reportlab`) and reads TrueType fonts
from the Windows font directory (Arial, Georgia, Courier New). On a
non-Windows machine, point FD at a directory containing equivalent
arial.ttf / arialbd.ttf / ariali.ttf / arialbi.ttf / georgia.ttf /
georgiab.ttf / cour.ttf / courbd.ttf files.
"""
import io
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "VIDEO_SCRIPT.md")
OUT = os.path.join(HERE, "ChangeLoop_Video_Script.pdf")

# ---------------------------------------------------------------- fonts --
FD = os.environ.get("CHANGELOOP_FONT_DIR", r"C:\Windows\Fonts")
pdfmetrics.registerFont(TTFont("Body", os.path.join(FD, "arial.ttf")))
pdfmetrics.registerFont(TTFont("Body-Bold", os.path.join(FD, "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Body-Italic", os.path.join(FD, "ariali.ttf")))
pdfmetrics.registerFont(TTFont("Body-BoldItalic", os.path.join(FD, "arialbi.ttf")))
pdfmetrics.registerFontFamily(
    "Body", normal="Body", bold="Body-Bold",
    italic="Body-Italic", boldItalic="Body-BoldItalic")

pdfmetrics.registerFont(TTFont("Head", os.path.join(FD, "georgia.ttf")))
pdfmetrics.registerFont(TTFont("Head-Bold", os.path.join(FD, "georgiab.ttf")))

pdfmetrics.registerFont(TTFont("Mono", os.path.join(FD, "cour.ttf")))
pdfmetrics.registerFont(TTFont("Mono-Bold", os.path.join(FD, "courbd.ttf")))

# --------------------------------------------------------------- palette --
WATER        = colors.HexColor("#1a6b7c")
WATER_INK    = colors.HexColor("#125462")
WATER_PALE   = colors.HexColor("#eaf3f4")
PEARL        = colors.HexColor("#f7f8f5")
AQUIFER      = colors.HexColor("#eceff0")
AQUIFER_DEEP = colors.HexColor("#e2e7e9")
GRAPHITE     = colors.HexColor("#1e2927")
SLATE        = colors.HexColor("#55635f")
SLATE2       = colors.HexColor("#65726f")
HAIR         = colors.HexColor("#dfe4e2")
HAIR2        = colors.HexColor("#cdd5d3")
EMERALD      = colors.HexColor("#0d7a57")
EMERALD_PALE = colors.HexColor("#e9f5ef")
CORAL        = colors.HexColor("#b23a2b")
CORAL_PALE   = colors.HexColor("#fbeae7")
AMBER        = colors.HexColor("#a4620a")
AMBER_PALE   = colors.HexColor("#fbf1e4")
WHITE        = colors.white

PAGE_W, PAGE_H = A4
M_L, M_R, M_T, M_B = 20 * mm, 20 * mm, 20 * mm, 20 * mm
CONTENT_W = PAGE_W - M_L - M_R

# ---------------------------------------------------------------- styles --
def ps(name, **kw):
    base = dict(fontName="Body", fontSize=10, leading=14.5,
                textColor=GRAPHITE, spaceAfter=7, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)

S_EYEBROW   = ps("eyebrow", fontName="Body-Bold", fontSize=9.5, leading=12,
                  textColor=WATER, spaceAfter=6)
S_TITLE     = ps("title", fontName="Head-Bold", fontSize=25, leading=29,
                  textColor=GRAPHITE, spaceAfter=6)
S_SUBTITLE  = ps("subtitle", fontSize=11, leading=16, textColor=SLATE,
                  spaceAfter=4)

S_BANNER_EYE = ps("bannereye", fontName="Body-Bold", fontSize=9.5, leading=12,
                   textColor=colors.HexColor("#bfe3e9"), spaceAfter=3)
S_BANNER_TITLE = ps("bannertitle", fontName="Head-Bold", fontSize=18,
                     leading=22, textColor=WHITE, spaceAfter=0)

S_H2 = ps("h2", fontName="Head-Bold", fontSize=13.3, leading=16,
          textColor=WATER_INK, spaceBefore=13, spaceAfter=2)
S_H2_APPENDIX_EYE = ps("h2apx", fontName="Body-Bold", fontSize=9.5, leading=12,
                        textColor=WATER_INK, spaceAfter=2)
S_H2_APPENDIX = ps("h2apxt", fontName="Head-Bold", fontSize=16, leading=20,
                    textColor=GRAPHITE, spaceAfter=2)

S_MINIHEAD = ps("minihead", fontName="Body-Bold", fontSize=11, leading=15,
                 textColor=WATER_INK, spaceBefore=11, spaceAfter=4)

S_BODY      = ps("body", fontSize=10, leading=14.5, spaceAfter=7)
S_STAGE     = ps("stage", fontName="Body-Italic", fontSize=9.2, leading=13,
                  textColor=SLATE2, spaceBefore=1, spaceAfter=4)
S_NEED      = ps("need", fontSize=9.3, leading=13, textColor=AMBER,
                  spaceBefore=1, spaceAfter=5)
S_CLICK     = ps("click", fontName="Body-Bold", fontSize=10.3, leading=14.5,
                  textColor=WATER_INK, spaceBefore=1, spaceAfter=6)
S_BULLET    = ps("bullet", fontSize=10, leading=14, spaceAfter=3,
                  leftIndent=14)
S_NUM       = ps("num", fontSize=10, leading=14.5, spaceAfter=6,
                  leftIndent=16)

S_QUOTE = ps("quote", fontSize=11, leading=16.5, spaceAfter=0)
S_QUOTE_LABEL = ps("quotelabel", fontName="Body-Bold", fontSize=8.3,
                    leading=11, textColor=WATER, spaceAfter=3)

S_CELL      = ps("cell", fontSize=9, leading=12.5)
S_CELL_B    = ps("cellb", fontSize=9, leading=12.5, fontName="Body-Bold")
S_CELLHEAD  = ps("cellhead", fontName="Body-Bold", fontSize=9, leading=12,
                  textColor=WHITE)

S_CODE = ParagraphStyle("code", fontName="Mono", fontSize=8.4, leading=12.2,
                         textColor=GRAPHITE)

S_FOOTNOTE = ps("footnote", fontSize=10, leading=16, spaceAfter=0,
                 fontName="Body-Italic", textColor=SLATE)

# ------------------------------------------------------------- inline md --
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(t):
    t = esc(t)
    t = re.sub(r"`([^`]+)`",
               lambda m: '<font face="Mono" size="9">' + m.group(1) + '</font>',
               t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", t)
    return t


def P(text, style):
    return Paragraph(inline(text), style)


# ------------------------------------------------------------ md parsing --
def parse_blocks(lines):
    blocks = []
    i, n = 0, len(lines)
    while i < n:
        raw = lines[i]
        s = raw.strip()
        if s == "":
            i += 1
            continue
        if s == "---":
            blocks.append(("hr",))
            i += 1
            continue
        if s.startswith("# "):
            blocks.append(("h1", s[2:].strip()))
            i += 1
            continue
        if s.startswith("## "):
            blocks.append(("h2", s[3:].strip()))
            i += 1
            continue
        if s.startswith("```"):
            i += 1
            code_lines = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i].rstrip("\n"))
                i += 1
            i += 1
            blocks.append(("code", code_lines))
            continue
        if s.startswith("|"):
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            blocks.append(("table", table_lines))
            continue
        if s.startswith(">"):
            quote_lines = []
            while i < n and lines[i].strip().startswith(">"):
                ql = lines[i].strip()[1:]
                quote_lines.append(ql.strip())
                i += 1
            paras, cur = [], []
            for ql in quote_lines:
                if ql == "":
                    if cur:
                        paras.append(" ".join(cur))
                        cur = []
                else:
                    cur.append(ql)
            if cur:
                paras.append(" ".join(cur))
            blocks.append(("quote", paras))
            continue
        if s.startswith("- "):
            items = []
            while i < n and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:].strip())
                i += 1
            blocks.append(("bullets", items))
            continue
        if re.match(r"^\d+\.\s", s):
            items = []
            while i < n and re.match(r"^\d+\.\s", lines[i].strip()):
                m = re.match(r"^(\d+)\.\s(.*)$", lines[i].strip())
                items.append((m.group(1), m.group(2)))
                i += 1
            blocks.append(("numbered", items))
            continue
        stop_prefixes = ("#", "|", ">", "```", "- ")
        para_lines = [s]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if nxt == "" or nxt == "---" or nxt.startswith(stop_prefixes) \
               or re.match(r"^\d+\.\s", nxt):
                break
            para_lines.append(nxt)
            i += 1
        blocks.append(("para", " ".join(para_lines)))
    return blocks


# -------------------------------------------------------- table builders --
TABLE_WIDTHS = {
    3: {
        "version": (0.17, 0.12, 0.71),
        "numbers": (0.37, 0.27, 0.36),
    },
    2: {
        "jury": (0.27, 0.73),
        "avoid": (0.42, 0.58),
    },
}


def classify_table(header):
    h = " ".join(header).lower()
    if "runs" in h and "use it for" in h:
        return "version"
    if "jury should be thinking" in h:
        return "jury"
    if "where" in h and "number" in h and "source" in h:
        return "numbers"
    if "do not say" in h:
        return "avoid"
    return "generic"


def build_table(table_lines):
    rows = []
    for tl in table_lines:
        if re.match(r"^\|[\s:|-]+\|$", tl):
            continue
        cells = [c.strip() for c in tl.strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return None
    header, body = rows[0], rows[1:]
    ncols = len(header)
    kind = classify_table(header)

    weights = TABLE_WIDTHS.get(ncols, {}).get(kind)
    if weights:
        col_w = [CONTENT_W * w for w in weights]
    else:
        col_w = [CONTENT_W / ncols] * ncols

    data = [[Paragraph(inline(c), S_CELLHEAD) for c in header]]
    highlight_row = None
    for ri, row in enumerate(body):
        cells = row + [""] * (ncols - len(row))
        if kind == "version" and "Record this one" in cells[-1]:
            highlight_row = ri + 1
        data.append([Paragraph(inline(c), S_CELL) for c in cells])

    style = [
        ("BACKGROUND", (0, 0), (-1, 0), WATER_INK),
        ("GRID", (0, 0), (-1, -1), 0.5, HAIR2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for ri in range(1, len(data)):
        if ri == highlight_row:
            style.append(("BACKGROUND", (0, ri), (-1, ri), EMERALD_PALE))
        elif ri % 2 == 0:
            style.append(("BACKGROUND", (0, ri), (-1, ri), PEARL))
    if kind == "avoid" and ncols == 2:
        for ri in range(1, len(data)):
            if ri != highlight_row and ri % 2 != 0:
                style.append(("BACKGROUND", (0, ri), (0, ri), CORAL_PALE))
                style.append(("BACKGROUND", (1, ri), (1, ri), EMERALD_PALE))

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle(style))
    return t


def build_code(code_lines, bg=AQUIFER, border=HAIR2):
    text = "\n".join(code_lines)
    pre = Preformatted(text, S_CODE)
    t = Table([[pre]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.6, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return t


def build_quote(paras, label="SAY THIS"):
    content = []
    content.append(Paragraph(label, S_QUOTE_LABEL))
    for idx, ptext in enumerate(paras):
        st = S_QUOTE if idx == len(paras) - 1 else \
            ParagraphStyle("q", parent=S_QUOTE, spaceAfter=8)
        content.append(Paragraph(inline(ptext), st))
    inner = Table([[content]], colWidths=[CONTENT_W - 5])
    inner.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    outer = Table([[Paragraph("", S_BODY), inner]], colWidths=[5, CONTENT_W - 5])
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), WATER),
        ("BACKGROUND", (1, 0), (1, 0), AQUIFER),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return outer


MINI_RE = re.compile(r"^\*\*[AB]\d+\.")
ITALIC_LINE_RE = re.compile(r"^\*[^*].*[^*]\*$|^\*[^*]\*$")


def classify_para(text):
    t = text.strip()
    if MINI_RE.match(t):
        return "mini"
    if ITALIC_LINE_RE.match(t):
        return "stage"
    if t.startswith("**Need:**"):
        return "need"
    if re.match(r"^\*\*(Click|No fault)", t):
        return "click"
    return "body"


# ------------------------------------------------------------- build doc --
def banner(text, first=False):
    if " — " in text:
        eye, title = text.split(" — ", 1)
    else:
        eye, title = "", text
    if first:
        flow = [
            Paragraph(eye.upper(), S_EYEBROW),
            Paragraph(title.title(), S_TITLE),
            Paragraph(
                "A screen-recording narration for the SANKALP 2026 "
                "submission &mdash; the problem, why it has not been "
                "solved, and how ChangeLoop solves it, step by step.",
                S_SUBTITLE),
            HRFlowable(width="100%", thickness=1.4, color=WATER,
                       spaceBefore=6, spaceAfter=14),
        ]
        return flow
    cell = [
        Paragraph(eye.upper(), S_BANNER_EYE),
        Paragraph(title, S_BANNER_TITLE),
    ]
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WATER_INK),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 13),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 13),
    ]))
    return [t, Spacer(1, 14)]


def h2_flow(text):
    if text.strip() == "Numbers to get right":
        return [
            Paragraph("REFERENCE", S_H2_APPENDIX_EYE),
            Paragraph(text, S_H2_APPENDIX),
            HRFlowable(width="100%", thickness=1.1, color=WATER,
                       spaceBefore=4, spaceAfter=12),
        ]
    return [
        Paragraph(text, S_H2),
        HRFlowable(width="100%", thickness=0.6, color=HAIR2,
                   spaceBefore=2, spaceAfter=9),
    ]


def main():
    lines = io.open(SRC, encoding="utf-8").read().splitlines()
    blocks = parse_blocks(lines)

    PAGEBREAK_BEFORE_H1 = {"ChangeLoop — video script": False}  # cover: no break
    seen_first_h1 = [False]

    out = []            # final flowables
    buf = []            # current KeepTogether buffer
    grouping = [False]  # are we accumulating a group right now
    # KeepTogether is only worth its blank-space cost inside the
    # step-by-step Version A / Version B walkthroughs, where splitting a
    # heading from its spoken quote across a page boundary actually hurts
    # the presenter. Reference material (the intro, the jury-think table,
    # the appendix) flows naturally instead, so a section that does not
    # fit in the remaining space just continues on the next page rather
    # than leaving the rest of the current page empty.
    in_version = [False]
    pending_lead_in = [None]  # a short ":"-ending paragraph awaiting its block

    def flush():
        if buf:
            out.append(KeepTogether(list(buf)))
            buf.clear()

    def emit(flowables):
        """Route a block's flowables to the buffer or straight to the page,
        gluing a short lead-in paragraph ("Salt is the thread ...:") to the
        table/code/quote that follows it so the two never land on separate
        pages."""
        if pending_lead_in[0] is not None:
            flowables = [pending_lead_in[0]] + flowables
            pending_lead_in[0] = None
            unit = [KeepTogether(flowables)]
        else:
            unit = flowables
        if grouping[0]:
            buf.extend(unit)
        else:
            out.extend(unit)

    for b in blocks:
        kind = b[0]

        if kind == "hr":
            continue  # headings carry their own rule

        if kind == "h1":
            text = b[1]
            flush()
            grouping[0] = False
            if not seen_first_h1[0]:
                seen_first_h1[0] = True
                out.extend(banner(text, first=True))
                in_version[0] = False
            else:
                out.append(PageBreak())
                out.extend(banner(text, first=False))
                in_version[0] = text.strip().startswith("VERSION")
            continue

        if kind == "h2":
            text = b[1]
            if text.strip() == "Numbers to get right":
                flush()
                grouping[0] = False
                in_version[0] = False
                out.append(PageBreak())
                out.extend(h2_flow(text))
                continue
            flush()
            if in_version[0]:
                buf.extend(h2_flow(text))
                grouping[0] = True
            else:
                out.extend(h2_flow(text))
                grouping[0] = False
            continue

        # ---- content blocks ----
        flowables = []
        if kind == "quote":
            flowables.append(build_quote(b[1]))
            flowables.append(Spacer(1, 9))
        elif kind == "code":
            flowables.append(build_code(b[1]))
            flowables.append(Spacer(1, 9))
        elif kind == "table":
            t = build_table(b[1])
            if t is not None:
                flowables.append(t)
                flowables.append(Spacer(1, 10))
        elif kind == "bullets":
            for item in b[1]:
                flowables.append(P("\u2022  " + item, S_BULLET))
        elif kind == "numbered":
            for num, item in b[1]:
                flowables.append(P("%s.  %s" % (num, item), S_NUM))
        elif kind == "para":
            text = b[1]
            cls = classify_para(text)
            if cls == "mini":
                flush()
                buf.append(P(text, S_MINIHEAD))
                grouping[0] = True
                continue
            elif cls == "stage":
                flowables.append(P(text, S_STAGE))
            elif cls == "need":
                rest = text.strip()[len("**Need:**"):].strip()
                flowables.append(Paragraph(
                    '<b>Why this step exists:</b> ' + inline(rest), S_NEED))
            elif cls == "click":
                flowables.append(P(text, S_CLICK))
            else:
                if text.strip().rstrip("*").endswith(":") and len(text) < 90:
                    # a short lead-in line - glue it to whatever follows
                    # instead of emitting it now
                    pending_lead_in[0] = P(text, S_BODY)
                    continue
                flowables.append(P(text, S_BODY))

        emit(flowables)

    flush()

    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=M_L, rightMargin=M_R, topMargin=M_T, bottomMargin=M_B,
        title="ChangeLoop \u2014 Video Script", author="Shorya Mittal",
        subject="SANKALP 2026 submission narration script")

    def footer(c, d):
        c.saveState()
        c.setStrokeColor(HAIR)
        c.setLineWidth(0.6)
        c.line(M_L, 15 * mm, PAGE_W - M_R, 15 * mm)
        c.setFont("Body", 8)
        c.setFillColor(SLATE2)
        c.drawString(M_L, 11.3 * mm,
                     "ChangeLoop  \u00b7  SANKALP 2026 Students Track  \u00b7  Video Script")
        c.drawRightString(PAGE_W - M_R, 11.3 * mm, "Page %d" % d.page)
        c.restoreState()

    doc.build(out, onFirstPage=footer, onLaterPages=footer)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
