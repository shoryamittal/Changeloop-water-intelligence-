# -*- coding: utf-8 -*-
"""Render the SANKALP 2026 concept note to PDF.

    python submission/build_concept_note.py

The note quotes a lot of engine output - the plant utilisation figures, the
evidence mix, the cluster projection, the per-shift comparison. Those were
checked against the running API when the note was written, and
submission/check_concept_note.py re-checks them, so a coefficient change
cannot silently turn the note into a document that quotes numbers the system
no longer produces.

Requires reportlab - see submission/requirements-tooling.txt.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from build_script_pdf import render          # noqa: E402

SRC = os.path.join(HERE, "concept_note", "CONCEPT_NOTE.md")
OUT = os.path.join(HERE, "ChangeLoop_Concept_Note.pdf")


def main():
    if not os.path.exists(SRC):
        raise SystemExit("missing source: " + SRC)

    render(
        src=SRC,
        out=OUT,
        title="ChangeLoop — Concept Note",
        subject="SANKALP 2026 Students Track - concept note",
        subtitle="In a zero-discharge dyeing factory, the coal bill is set "
                 "by the salt that goes in, not the water that comes out. "
                 "This is a tool that shows the planner that cost while "
                 "they are still choosing.",
        footer_text="ChangeLoop  ·  SANKALP 2026 Students Track  "
                    "·  Concept note",
        # the sources sit inline with the claims they support
        appendix_heading="",
        # a blockquote here is a pull quote, not a spoken line
        quote_label=None,
        running_header="ChangeLoop  ·  Concept note",
    )
    print("\nwrote %s" % OUT)


if __name__ == "__main__":
    main()
