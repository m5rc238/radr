# ROADMAP.md — Project Stages

**Current stage: Stage 1 — complete (2026-10-08). Next: Stage 2 (not started).**

Stages are sequential by default: a stage's exit criteria are the next stage's prerequisites. A stage is not "done" because its code exists — it is done when its criteria are met and recorded.

**Later stages are hypotheses about a possible research path, not guarantees.** No stage beyond Stage 0 is committed to implementation; stages may be reordered, revised, or dropped when evidence warrants.

## Stage 0 — Project contract

**Goal:** Define the problem, scope, data model, architecture, and evaluation framework as a version-controlled contract.

**Deliverables:** this repository: `README.md`, `PROJECT.md`, `ARCHITECTURE.md`, `EVALUATION.md`, `SOURCES.md`, `DECISIONS.md`, `ROADMAP.md`, commits.

**Exit criteria:**

- the research question — surfacing meaningful changes while reducing what a person must inspect — is unambiguous
- the project is clearly distinguished from feeds, search, RSS, newsletters, RAG, and AI agents
- non-goals are explicit
- "meaningful change" is documented as an unresolved evaluation problem, not a defined quantity
- retrieval and importance are separated as distinct problems
- evaluation criteria are measurable, with attention-cost dimensions marked as research directions where no measure exists yet
- architecture is understandable as a monitoring loop
- data model is sufficient but not over-engineered
- initial topics/sources are clearly bounded
- the hypothesis can actually be falsified
- it is explicit that the LLM is an experimental component, not an authority or assumed-best retriever
- another researcher could read the repository and state what experiment is being prepared

## Stage 1 — Controlled corpus

**Goal:** Build a small, reproducible corpus from clearly defined sources.

- build ingestion for the sources approved in `SOURCES.md` (verified URLs, recorded dates)
- implement normalization, deduplication (content hash), and the document store per `ARCHITECTURE.md`
- re-run ingestion and reproduce the corpus (repeatability)
- confirm or overturn proposed decisions A–E in `DECISIONS.md`

**Exit criteria:** a small corpus exists locally; every document has provenance (original URL, source, dates); re-running ingestion is repeatable; no source is present without a registry entry.

**Status: complete (2026-10-08).** 9 sources verified live and registered (`SOURCES.md`); pipeline `fetch → parse → normalize → dedupe → store → snapshot → inspect` implemented in `radar/` (Python 3.11, standard library only) with a CLI (`python -m radar …`). First full run: 9/9 sources, 196 documents, each with original URL, source, publication and retrieval dates. Repeat run: 0 new, 0 changed — re-ingestion is repeatable, with cross-feed duplicates consistently counted (6 per run, arXiv cross-lists) rather than stored. Corpus deleted and rebuilt from empty as a validated step. 49 automated tests pass (`python -m unittest discover -s tests`), covering identity stability, URL normalization, content hashing, exact-duplicate detection (including cross-feed duplicates), repeated ingestion, snapshot creation, observations across snapshots, changed-content history preservation, and parser behavior. Proposed decisions A, B, D, E confirmed and promoted to Decisions 12–15 (`DECISIONS.md`); implementation decisions 16–21 recorded there.

## Stage 2 — Retrieval baseline

**Goal:** Compare conventional retrieval approaches.

- BM25 (lexical) baseline
- dense retrieval (semantic)
- hybrid retrieval
- all three behind the common interface required by `ARCHITECTURE.md`
- every run recorded as a Retrieval Run (method, parameters, scores)

**Exit criteria:** the same queries run against the same corpus snapshot with all methods; results are recorded and reproducible; **no LLM components yet** (Decision 1).

## Stage 3 — Evaluation benchmark

**Goal:** Create human judgments for relevance **and meaningful change**, and measure retrieval performance.

- design a query/topic set
- pool candidate documents across methods; judge relevance by a human
- collect human judgments of meaningful change for pooled and newly detected items
- compute the `EVALUATION.md` IR metrics (Recall@10/@20, Precision@10, nDCG@10, MRR) plus operational measures
- record per-query results, not just means
- replace the working success criterion in `EVALUATION.md` with a measured one

**Exit criteria:** a judged benchmark (both judgment types) exists in version control; metrics are reported per method; baseline numbers for BM25/dense/hybrid are on record.

## Stage 4 — Temporal monitoring

**Goal:** Detect changes between snapshots.

- take snapshots per topic on a cadence
- diff snapshots; detect additions, retirements, and significance
- measure change detection against human meaningful-change judgments (did the flagged changes matter?)

**Exit criteria:** the system answers "what changed since my previous snapshot" with provenance for each change, and the answer has been human-checked at least once per topic.

## Stage 5 — Attention-aware ranking

**Goal:** Investigate whether the system can **reduce the number of items a person needs to inspect** without losing meaningful changes.

- rank change candidates with inspection cost as an explicit concern, not only relevance
- measure inspection burden (items inspected, verification time) at equal or better discovery than baseline ranking
- record results as experiment records in `docs/experiments/`

**Exit criteria:** at least one measured comparison of inspection burden between ranking strategies; no attention-saving claim exists without a measurement (`EVALUATION.md` — the discoveries-per-attention measure is still an open direction).

## Stage 6 — Simple interface

**Goal:** Build a minimal interface around changes, sources, evidence, and inspection.

Views: **Changes, Topics, Sources, Evidence/inspection, Search, Evaluation.**

The interface must surface provenance, scores, method identity, and uncertainty (`DECISIONS.md`, Decision 6). Presentation must not hide weak retrieval or encourage continuous monitoring (`PROJECT.md`, non-goals).

**Exit criteria:** a person can inspect a topic's changes, see why each was surfaced, click through to original sources, and run a search — without reading the database by hand.

## Stage 7 — Selective LLM assistance

**Goal:** Introduce LLMs only where experiments demonstrate measurable benefit.

Candidate uses, each requiring its own before/after experiment in `docs/experiments/`:

- query expansion
- clustering
- evidence extraction
- comparison
- change interpretation
- synthesis

**Exit criteria:** for each LLM component added, an experiment record shows measured improvement on judged metrics — including any increase in inspection burden — or the component is not added. LLM output is labeled as interpretation, never as evidence (`ARCHITECTURE.md`).

## Stage 8 — Search strategy adaptation

**Goal:** Investigate whether the system can **recognize retrieval gaps and change how it searches**.

- detect signs that the current strategy is underperforming (low yield, empty change sets, coverage gaps, judged misses)
- try altered queries, sources, or methods in response
- measure whether adaptation improves judged outcomes over a fixed strategy

**Exit criteria:** at least one experiment record showing gap recognition → strategy change → measured effect, positive or negative. This stage may find that adaptation does not pay off; that is a valid result.

---

## Comparison runs through every stage

The required comparison in `ARCHITECTURE.md` (BM25 vs dense vs hybrid vs hybrid+reranking vs hybrid+LLM vs agentic search) is not a single stage — it is measured progressively as each component becomes available, on the Stage 3 benchmark, including cost measures: retrieval latency, inspection burden, and human verification time (`EVALUATION.md`).

The closing synthesis — which components helped, which did not, and whether the core hypothesis survived, including a documented failure if that is the result (`PROJECT.md`) — is a standing deliverable of the later stages.
