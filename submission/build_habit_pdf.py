# -*- coding: utf-8 -*-
"""Render the concept note on the HABIT Foundation template.

    python submission/build_habit_pdf.py

WHY THIS IS A SEPARATE RENDERER
-------------------------------
build_script_pdf.py produces the project's own house style - sans faces,
colour, wide measure. That is the wrong look here. A concept note sent
back to an organisation on its own template should look like the
template, so this module copies its geometry rather than approximating
it:

    header band   the template's own banner image, lifted from the
                  supplied PDF and drawn on every page at the exact
                  rectangle it occupies there, 9,9 to 585.9,100.4
    page          A4, 72pt margins, matching the template
    type          Times New Roman 12pt, bold for headings and lead-ins
    headings      bold at the left margin
    bullets       marker at 108pt, text at 126pt
    body          indented to 126pt, so prose lines up with the column
                  the template's bullet text sits in

The one deliberate departure is tables. The template has none, and this
note needs them for the comparisons and the financials, so they sit a
little wider than the text column. Everything else follows the template.

Requires reportlab - see submission/requirements-tooling.txt.
"""
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, KeepTogether, Preformatted,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
HEADER_IMG = os.path.join(ASSETS, "habit_header.png")

# --- geometry, read off the supplied template -------------------------
PAGE_W, PAGE_H = A4                      # 595.2 x 841.92
HDR = (9.0, 9.0, 585.9, 100.4)           # left, top, right, bottom
MARGIN_L = 72.0
MARGIN_R = 72.0
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R  # 451.2
BULLET_X = 108.0 - MARGIN_L               # 36
TEXT_X = 126.0 - MARGIN_L                 # 54
BODY_TOP = PAGE_H - HDR[3] - 18.0         # first line sits below the band
BODY_BOTTOM = 54.0

FONT_DIR = os.environ.get("CHANGELOOP_FONT_DIR", r"C:\Windows\Fonts")
BASE, BOLD, ITAL, BOLDITAL, MONO = (
    "TimesNR", "TimesNR-Bold", "TimesNR-Italic", "TimesNR-BoldItalic",
    "CourierNew")


def _register_fonts():
    """Use real Times New Roman when it is on the machine.

    reportlab's built-in Times is metrically close but not identical, and
    the point of this renderer is to match a document the reader already
    has in front of them.
    """
    faces = [
        (BASE, "times.ttf"), (BOLD, "timesbd.ttf"),
        (ITAL, "timesi.ttf"), (BOLDITAL, "timesbi.ttf"),
        (MONO, "cour.ttf"),
    ]
    ok = True
    for name, fn in faces:
        path = os.path.join(FONT_DIR, fn)
        if not os.path.exists(path):
            ok = False
            break
        pdfmetrics.registerFont(TTFont(name, path))
    if not ok:
        return ("Times-Roman", "Times-Bold", "Times-Italic",
                "Times-BoldItalic", "Courier")
    pdfmetrics.registerFontFamily(BASE, normal=BASE, bold=BOLD,
                                  italic=ITAL, boldItalic=BOLDITAL)
    return (BASE, BOLD, ITAL, BOLDITAL, MONO)


F_BASE, F_BOLD, F_ITAL, F_BI, F_MONO = _register_fonts()

LEAD = 15.5          # the template runs roughly 12/15.5
SIZE = 12.0

S_TITLE = ParagraphStyle(
    "t", fontName=F_BOLD, fontSize=SIZE, leading=LEAD,
    alignment=TA_CENTER, spaceAfter=14)
S_SUB = ParagraphStyle(
    "sub", fontName=F_ITAL, fontSize=10.5, leading=13,
    alignment=TA_CENTER, textColor=colors.HexColor("#444444"),
    spaceAfter=16)
S_H2 = ParagraphStyle(
    "h2", fontName=F_BOLD, fontSize=SIZE, leading=LEAD,
    spaceBefore=13, spaceAfter=4, keepWithNext=1)
S_H3 = ParagraphStyle(
    "h3", fontName=F_BOLD, fontSize=SIZE, leading=LEAD,
    leftIndent=TEXT_X - 18, spaceBefore=9, spaceAfter=3, keepWithNext=1)
S_BODY = ParagraphStyle(
    "b", fontName=F_BASE, fontSize=SIZE, leading=LEAD,
    leftIndent=TEXT_X, spaceAfter=7, alignment=TA_JUSTIFY)
S_BULLET = ParagraphStyle(
    "li", fontName=F_BASE, fontSize=SIZE, leading=LEAD,
    leftIndent=TEXT_X, bulletIndent=BULLET_X, spaceAfter=3,
    alignment=TA_JUSTIFY)
S_CELL = ParagraphStyle(
    "c", fontName=F_BASE, fontSize=10, leading=12.5)
S_CELL_H = ParagraphStyle(
    "ch", fontName=F_BOLD, fontSize=10, leading=12.5)
S_CODE = ParagraphStyle(
    "code", fontName=F_MONO, fontSize=9.5, leading=12,
    leftIndent=TEXT_X, spaceBefore=4, spaceAfter=8)

TABLE_X = BULLET_X                       # tables start at the bullet column
TABLE_W = CONTENT_W - TABLE_X


# --- inline markdown --------------------------------------------------
def inline(s):
    s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`(.+?)`", r"<font face='%s'>\1</font>" % F_MONO, s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               r"<link href='\2' color='#0b3d91'>\1</link>", s)
    # a bare url
    s = re.sub(r"(?<!['\">])(https?://[^\s<)]+)",
               r"<link href='\1' color='#0b3d91'>\1</link>", s)
    return s


def parse(md):
    """Markdown subset -> flowables, in the template's shapes."""
    out = []
    lines = md.replace("\r\n", "\n").split("\n")
    i, n = 0, len(lines)
    first_h1 = True

    while i < n:
        raw = lines[i]
        s = raw.strip()

        if not s:
            i += 1
            continue

        if s == "---":
            i += 1
            continue

        if s.startswith("# "):
            text = s[2:].strip()
            if first_h1:
                out.append(Paragraph(inline(text), S_TITLE))
                first_h1 = False
            else:
                out.append(Paragraph(inline(text), S_H2))
            i += 1
            continue

        if s.startswith("### "):
            out.append(Paragraph(inline(s[4:].strip()), S_H3))
            i += 1
            continue

        if s.startswith("## "):
            out.append(Paragraph(inline(s[3:].strip()), S_H2))
            i += 1
            continue

        if s.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(Preformatted("\n".join(buf), S_CODE))
            continue

        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            t = _table(rows)
            if isinstance(t, list):
                out.extend(t)
            elif t is not None:
                out.append(t)
            continue

        if s.startswith("- ") or s.startswith("* "):
            while i < n and (lines[i].strip().startswith("- ")
                             or lines[i].strip().startswith("* ")):
                item = lines[i].strip()[2:].strip()
                i += 1
                # consume wrapped continuation lines
                while (i < n and lines[i].strip()
                       and not lines[i].strip().startswith(("- ", "* ", "#",
                                                            "|", "```"))
                       and lines[i].startswith(("  ", "\t"))):
                    item += " " + lines[i].strip()
                    i += 1
                out.append(Paragraph(inline(item), S_BULLET,
                                     bulletText="\u2022"))
            out.append(Spacer(1, 4))
            continue

        # a paragraph: gather until a blank line or a block marker
        buf = [s]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (not nxt or nxt == "---"
                    or nxt.startswith(("#", "|", "```", "- ", "* "))):
                break
            buf.append(nxt)
            i += 1
        out.append(Paragraph(inline(" ".join(buf)), S_BODY))

    return out


def _split_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def _table(rows):
    if len(rows) < 2:
        return None
    header = _split_row(rows[0])
    sep = _split_row(rows[1])
    if not all(set(c) <= set("-: ") and c for c in sep):
        # no separator line - treat as plain rows
        body_rows = [_split_row(r) for r in rows]
        header = None
    else:
        body_rows = [_split_row(r) for r in rows[2:]]

    ncol = max([len(header)] if header else [0]
               + [len(r) for r in body_rows] or [1])
    data = []
    blank_header = header is not None and not any(c for c in header)

    if header is not None and not blank_header:
        data.append([Paragraph(inline(c), S_CELL_H) for c in
                     (header + [""] * (ncol - len(header)))])
    for r in body_rows:
        data.append([Paragraph(inline(c), S_CELL) for c in
                     (r + [""] * (ncol - len(r)))])
    if not data:
        return None

    # first column a little wider: it usually carries the label
    if ncol == 1:
        widths = [TABLE_W]
    else:
        first = TABLE_W * (0.34 if ncol > 2 else 0.42)
        rest = (TABLE_W - first) / (ncol - 1)
        widths = [first] + [rest] * (ncol - 1)

    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=
              1 if (header is not None and not blank_header) else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9a9a9a")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header is not None and not blank_header:
        style.append(("BACKGROUND", (0, 0), (-1, 0),
                      colors.HexColor("#f2e3e0")))
    t.setStyle(TableStyle(style))
    # Small tables stay whole. Large ones are allowed to break, with the
    # header row repeated - locking them together orphans the heading
    # above at the foot of the previous page.
    if len(data) <= 3:
        return KeepTogether([Spacer(1, 2), t, Spacer(1, 9)])
    return [Spacer(1, 2), t, Spacer(1, 9)]


# --- page furniture ---------------------------------------------------
def _page(canvas, doc):
    canvas.saveState()
    if os.path.exists(HEADER_IMG):
        x0, y0, x1, y1 = HDR
        canvas.drawImage(HEADER_IMG, x0, PAGE_H - y1,
                         width=x1 - x0, height=y1 - y0,
                         preserveAspectRatio=False, mask="auto")
    canvas.setFont(F_BASE, 9)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(PAGE_W / 2.0, 32, str(canvas.getPageNumber()))
    canvas.restoreState()


def render(src, out, subtitle=None, title=None):
    md = open(src, encoding="utf-8").read()
    story = parse(md)
    if subtitle:
        # sits right under the centred title, like the template's own
        story.insert(1, Paragraph(inline(subtitle), S_SUB))

    doc = BaseDocTemplate(
        out, pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=PAGE_H - BODY_TOP, bottomMargin=BODY_BOTTOM,
        title=title or "Concept Note", author="Shorya Ashish Mittal",
        subject="Concept note")
    frame = Frame(MARGIN_L, BODY_BOTTOM, CONTENT_W,
                  BODY_TOP - BODY_BOTTOM, id="body",
                  leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame],
                                       onPage=_page)])
    doc.build(story)
    return out


def main():
    src = os.path.join(HERE, "concept_note", "CONCEPT_NOTE_HABIT.md")
    out = os.path.join(HERE, "ChangeLoop_Concept_Note_HABIT.pdf")
    if not os.path.exists(src):
        raise SystemExit("missing source: " + src)
    if not os.path.exists(HEADER_IMG):
        raise SystemExit(
            "missing header image: " + HEADER_IMG + "\nIt is lifted from "
            "the supplied template PDF; see the repository notes.")
    render(src, out, subtitle="Concept Note")
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
