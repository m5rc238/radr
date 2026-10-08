# ROADMAP.md — Project Stages

**Current stage: Stage 0.**

Stages are sequential by default: a stage's exit criteria are the next stage's prerequisites. A stage is not "done" because its code exists — it is done when its criteria are met and recorded.

## Stage 0 — Project contract

**Goal:** Establish a clear, version-controlled project contract that future implementation can follow.

**Deliverables:** this repository: `README.md`, `PROJECT.md`, `ARCHITECTURE.md`, `EVALUATION.md`, `SOURCES.md`, `DECISIONS.md`, `ROADMAP.md`, initial commit.

**Exit criteria:**

- research question is unambiguous
- non-goals are explicit
- evaluation criteria are measurable
- architecture is understandable
- data model is sufficient but not over-engineered
- initial topics/sources are clearly bounded
- the hypothesis can actually be falsified
- it is explicit that the LLM is not assumed to be the best retriever

## Stage 1 — Ingestion and corpus

**Goal:** Create a repeatable local corpus from a small set of real sources.

- build ingestion for the sources approved in `SOURCES.md` (verified URLs, recorded dates)
- implement normalization, deduplication (content hash), and the document store per `ARCHITECTURE.md`
- re-run ingestion and reproduce the corpus (repeatability)
- confirm or overturn proposed decisions A–E in `DECISIONS.md`

**Exit criteria:** a small corpus exists locally; every document has provenance (original URL, source, dates); re-running ingestion is repeatable; no source is present without a registry entry.

## Stage 2 — Retrieval baseline

**Goal:** Implement and compare conventional retrieval methods.

- BM25 (lexical) baseline
- dense retrieval (semantic)
- hybrid retrieval
- all three behind the common interface required by `ARCHITECTURE.md`
- every run recorded as a Retrieval Run (method, parameters, scores)

**Exit criteria:** the same queries run against the same corpus snapshot with all methods; results are recorded and reproducible; **no LLM components yet** (Decision 1).

## Stage 3 — Evaluation

**Goal:** Build a manually judged benchmark and measure retrieval performance.

- design a query/topic set
- pool candidate documents across methods; judge relevance by a human
- compute `EVALUATION.md` metrics (Recall@10/@20, Precision@10, nDCG@10, MRR) plus additional measures
- record per-query results, not just means
- replace the working success criterion in `EVALUATION.md` with a measured one

**Exit criteria:** a judged benchmark exists in version control; metrics are reported per method; baseline numbers for BM25/dense/hybrid are on record.

## Stage 4 — Temporal change detection

**Goal:** Compare snapshots and identify meaningful changes over time.

- take snapshots per topic on a cadence
- diff snapshots; detect additions, retirements, and significance
- measure change detection against human judgment (did the flagged changes matter?)

**Exit criteria:** the system answers "what changed since my previous snapshot" with provenance for each change, and the answer has been human-checked at least once per topic.

## Stage 5 — Interface

**Goal:** Build a simple interface for using the system.

Views: **Overview, Changes, Topics, Sources, Search, Evaluation.**

The interface must surface provenance, scores, method identity, and uncertainty (`DECISIONS.md`, Decision 6). Presentation must not hide weak retrieval (`PROJECT.md`, non-goals).

**Exit criteria:** a person can inspect a topic's changes, click through to original sources, and run a search — without reading the database by hand.

## Stage 6 — Selective LLM assistance

**Goal:** Introduce an LLM only where experiments show it provides value.

Candidate uses, each requiring its own before/after experiment in `docs/experiments/`:

- query expansion
- clustering
- evidence extraction
- comparison
- change interpretation
- synthesis

**Exit criteria:** for each LLM component added, an experiment record shows measured improvement (or the component is not added). LLM output is labeled as interpretation, never as evidence (`ARCHITECTURE.md`).

## Stage 7 — Comparative experiments

**Goal:** Compare the complete approaches and measure whether each additional component actually improves outcomes.

```text
BM25
vs dense
vs hybrid
vs hybrid + reranking
vs hybrid + selective LLM assistance
```

Measured on the judged benchmark, including cost: retrieval latency and human verification time (`EVALUATION.md`).

**Exit criteria:** a final comparison exists showing which components helped, which did not, and whether the core hypothesis survived — including, if applicable, a documented failure of the hypothesis (`PROJECT.md`).
