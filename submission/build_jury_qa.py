# -*- coding: utf-8 -*-
"""Render each jury Q&A answer to its own PDF.

WHY THIS EXISTS
----------------
The competition answers quote figures that come from the engine - the
per-shift impact, the 480 candidates, the evidence mix, the cluster
projection. If those were typed into a document by hand they would drift
the moment the engine changed, which is exactly what happened to
figures.json and to the deck before they were generated instead.

So each answer lives as markdown in submission/jury_qa/ and is rendered
here, in the same house style as the video script PDF:

    python submission/build_jury_qa.py

One PDF per question, because the answers are submitted separately.

Requires reportlab - see submission/requirements-tooling.txt.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from build_script_pdf import render          # noqa: E402

QA_DIR = os.path.join(HERE, "jury_qa")

# Each entry: source file, output name, cover subtitle, footer label.
# The subtitle is what a judge reads under the title before anything else,
# so it states the question rather than describing the document.
DOCS = [
    ("Q1_the_problem.md", "ChangeLoop_Q1_The_Problem.pdf",
     "Which water challenge, where, and why the approaches that exist "
     "today do not close it.",
     "Question 1  ·  The problem"),

    ("Q2_how_it_works.md", "ChangeLoop_Q2_How_It_Works.pdf",
     "How the system works, what was tested, and what has not been "
     "measured yet.",
     "Question 2  ·  How it works"),

    ("Q3_what_is_new.md", "ChangeLoop_Q3_What_Is_New.pdf",
     "What already exists, what is genuinely new here, and the difference "
     "between them.",
     "Question 3  ·  What is new"),

    ("Q4_impact.md", "ChangeLoop_Q4_Impact.pdf",
     "How much is saved, who benefits, and which figures are projections "
     "rather than results.",
     "Question 4  ·  Impact"),

    ("Q5_scale.md", "ChangeLoop_Q5_Scale.pdf",
     "What changes at cluster scale, and which parts are not solved yet.",
     "Question 5  ·  Scale"),
]


def main():
    missing = [src for src, _, _, _ in DOCS
               if not os.path.exists(os.path.join(QA_DIR, src))]
    if missing:
        raise SystemExit("missing source files: " + ", ".join(missing))

    for src, out, subtitle, footer in DOCS:
        qnum = src[1]
        render(
            src=os.path.join(QA_DIR, src),
            out=os.path.join(HERE, out),
            title="ChangeLoop — " + footer.split("·")[0].strip(),
            subject="SANKALP 2026 Students Track - jury answer",
            subtitle=subtitle,
            footer_text="ChangeLoop  ·  SANKALP 2026 Students Track  "
                        "·  " + footer,
            # these documents have no reference appendix; the supporting
            # notes are part of the body
            appendix_heading="",
            # a blockquote here is a pull quote, not a spoken line
            quote_label=None,
            cover_number="0" + qnum,
            running_header="ChangeLoop  ·  " + footer,
        )
    print("\n%d answer PDFs written to %s" % (len(DOCS), HERE))


if __name__ == "__main__":
    main()
