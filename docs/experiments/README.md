# Experiment records

Every experiment in this project is recorded here as a short, self-contained markdown file. Experiments are how the project's hypothesis can fail visibly (`PROJECT.md`) and how decisions get evidence (`DECISIONS.md`).

## When to write one

Write a record whenever you:

- compare two retrieval methods, models, or configurations
- introduce or remove an LLM component (Stage 7+)
- test an assumption listed as *proposed* in `DECISIONS.md`
- produce a measurement that could change a decision
- run something that failed — failures are results

## File naming

```text
YYYY-MM-DD-short-slug.md
```

Example: `2026-10-07-bm25-vs-dense-pilot.md`

## Template

```markdown
# <title>

**Date:** YYYY-MM-DD
**Stage:** <roadmap stage>
**Status:** pilot | complete | superseded by <file>
**Decision affected:** <DECISIONS.md entry, if any>

## Question
The single thing this experiment tried to find out.

## Method
What was run, on what corpus/queries, with which parameters.
Enough detail to reproduce. If something was approximate, say so.

## Results
Numbers with context (per-query where applicable), or observations.
No results yet? Say "no measurement yet" — do not estimate.

## Conclusion
What the results support, at the strength the evidence allows.
A conclusion may be "inconclusive".

## What would change this conclusion
The next measurement that would overturn or strengthen it.
```

## Rules

- Mark unknowns as unknown; do not fill gaps with plausible numbers (`PROJECT.md` constraints).
- LLM output used inside an experiment is a component under test, not evidence about the experiment.
- Superseded records are kept, not deleted. History is part of the evidence.
