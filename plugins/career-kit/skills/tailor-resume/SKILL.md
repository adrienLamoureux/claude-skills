---
name: tailor-resume
description: Tailor the résumé in a resume-forge checkout to one job posting — a few truthful data edits, a match report with honest gaps, and a rendered PDF. Use when the user runs /tailor-resume, pastes a job description or job URL and asks to tailor, adapt or target their résumé or CV, or asks how well their résumé matches a role.
argument-hint: "<job file | job URL | pasted posting>"
---

# Tailor résumé

Content and layout stay apart: you edit **data** only. `templates/resume.typ` owns the look and
you never touch it. Run from the root of a resume-forge checkout:

| Path | Role |
|---|---|
| `data/baseline.yaml` | The master résumé: the only source of facts. Keys: `basics`, `summary`, `skills`, `experience`, `education`, `highlights`. |
| `data/sources/` | Extra true context (brag doc, LinkedIn export). Facts here may be used; cite them in the report. |
| `data/jobs/<slug>.md` | The posting. |
| `scripts/render.sh <data> [out]` | Typst render; `output/<slug>/tailored.yaml` renders to `output/<slug>/resume.pdf`. |

If these are missing, say so and stop.

## Truthfulness (non-negotiable)

- Never invent or inflate an employer, title, date, metric, skill, tool or responsibility.
- Allowed edits: reorder, select, shorten, and reword a true fact using the posting's words
  when they mean the same thing.
- A requirement the baseline does not support is an **honest gap** in the report, never a
  new line in the résumé.
- Keep numbers exactly as the baseline states them.

## Workflow

1. **Get the posting.** A path → read it. A URL → fetch it and save the text to
   `data/jobs/<slug>.md`. Pasted text → save it the same way. `<slug>` is
   `<company>-<role>`, kebab-case.
2. **Read** `data/baseline.yaml` and every file in `data/sources/`.
3. **Extract requirements** from the posting: must-haves, nice-to-haves and its exact
   keywords (tools, methods, domain words).
4. **Write `output/<slug>/tailored.yaml`.** Copy the baseline, keep its schema, then make
   only the few edits that matter most:
   - the summary leads with the two or three things this role weighs most;
   - skills are reordered so matching ones come first;
   - each role's bullets are reordered, and the weakest ones dropped if space is tight;
   - true facts reuse the posting's keyword where it is the same thing (e.g. "CI/CD").
5. **Write `output/<slug>/match-report.md`:**
   - a requirements table: requirement · covered / partial / gap · the baseline line that proves it;
   - keywords the posting uses that the résumé now contains, and those it still lacks;
   - honest gaps, each with a one-line way to address it in a cover letter or interview;
   - ATS notes: single column, real text, standard headings, no keyword stuffing;
   - a list of every edit made, each next to the original line.
6. **Render:** `scripts/render.sh output/<slug>/tailored.yaml`. Fix data errors if Typst fails.
7. **Report** in a few lines: the PDF path, the coverage count, the top gaps.

## Privacy

resume-forge may be a public repository. Job files and tailored outputs show which roles the
user is applying to. Do not `git add`, commit or push anything under `data/jobs/` or `output/`;
leave version control to the user and remind them once.
