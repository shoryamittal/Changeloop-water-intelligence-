# -*- coding: utf-8 -*-
"""Render the 12-section concept note (HABIT Foundation template) to PDF.

    python submission/build_concept_note_habit.py

This is the startup-format note: title page, vision and mission, business
model, market and competition, financials, funding ask. The other builder,
build_concept_note.py, renders the shorter problem-and-solution version.
Both quote the same engine and both are checked by
check_concept_note.py.

Requires reportlab - see submission/requirements-tooling.txt.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from build_script_pdf import render          # noqa: E402

SRC = os.path.join(HERE, "concept_note", "CONCEPT_NOTE_HABIT.md")
OUT = os.path.join(HERE, "ChangeLoop_Concept_Note_HABIT.pdf")


def main():
    if not os.path.exists(SRC):
        raise SystemExit("missing source: " + SRC)
    render(
        src=SRC,
        out=OUT,
        title="ChangeLoop — Concept Note",
        subject="Concept note - HABIT Foundation template",
        subtitle="In a zero-discharge dyeing factory, the coal bill is set "
                 "by the salt that goes in, not the water that comes out. "
                 "This is a tool that shows the planner that cost while "
                 "they are still choosing.",
        footer_text="ChangeLoop  ·  Concept note",
        appendix_heading="",
        quote_label=None,
        running_header="ChangeLoop  ·  Concept note",
    )
    print("\nwrote %s" % OUT)


if __name__ == "__main__":
    main()
