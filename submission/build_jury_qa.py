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
     "Question 1 &mdash; which water challenge, where, and why current "
     "approaches fail.",
     "Question 1  ·  The problem"),

    ("Q2_how_it_works.md", "ChangeLoop_Q2_How_It_Works.pdf",
     "Question 2 &mdash; how the system works, and what has actually been "
     "measured.",
     "Question 2  ·  How it works"),

    ("Q3_what_is_new.md", "ChangeLoop_Q3_What_Is_New.pdf",
     "Question 3 &mdash; what is new, the closest existing methods, and the "
     "difference.",
     "Question 3  ·  What is new"),

    ("Q4_impact.md", "ChangeLoop_Q4_Impact.pdf",
     "Question 4 &mdash; how much is saved, for whom, and what is projection "
     "rather than result.",
     "Question 4  ·  Impact"),

    ("Q5_scale.md", "ChangeLoop_Q5_Scale.pdf",
     "Question 5 &mdash; what changes at scale, and what is not solved yet.",
     "Question 5  ·  Scale"),
]


def main():
    missing = [src for src, _, _, _ in DOCS
               if not os.path.exists(os.path.join(QA_DIR, src))]
    if missing:
        raise SystemExit("missing source files: " + ", ".join(missing))

    for src, out, subtitle, footer in DOCS:
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
        )
    print("\n%d answer PDFs written to %s" % (len(DOCS), HERE))


if __name__ == "__main__":
    main()
