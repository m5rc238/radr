# Information Radar

Information Radar is an experiment in detecting **meaningful changes in a defined information environment** without requiring continuous monitoring. It is a research project with a falsifiable hypothesis and measured evaluation.

> **This project does not assume that LLMs are the best way to retrieve information. It is designed to test that question.**

## The problem

People currently rely on feeds, alerts, search, newsletters, manual monitoring, and increasingly AI systems to stay informed. These approaches reduce some costs but can also create noise, attention burden, or incomplete retrieval. The goal here is not to maximize information consumption — it is to **minimize the attention required to remain meaningfully informed**. Full problem framing: `PROJECT.md`.

## Research question

> **Can a retrieval and monitoring system reliably surface relevant and meaningful changes in a defined information environment while reducing the amount of information a person needs to inspect?**

This is an empirical question. The system compares conventional information retrieval (BM25, dense, hybrid, reranking) with AI-assisted retrieval, agentic search, and LLM reasoning — and measures what each approach finds **and what each costs in human attention** (`EVALUATION.md`).

## The experiment being prepared

Build a small, reproducible corpus from a few clearly defined sources; run competing retrieval approaches over periodic snapshots of the same topics; and judge the results by hand — both **relevance** and **meaningful change**. Methods are compared on what they find (recall, discovery, coverage) and what they cost (inspection burden, verification time). The comparison includes conventional IR baselines first and LLM/agentic variants later, so the hypothesis in `PROJECT.md` can fail.

## Current stage

**Stage 1 — controlled corpus.** A small corpus builds end-to-end from registered sources: fetch → parse → normalize → dedupe → store → snapshot → inspect, as a Python CLI. 196 documents from 9 verified sources, each with full provenance; re-ingestion is repeatable. Next stage (retrieval baseline) not started.

### Quickstart (Stage 1)

```sh
python -m radar ingest                 # one ingestion cycle; creates a snapshot
python -m radar stats                  # corpus statistics
python -m radar snapshots              # list snapshots
python -m radar inspect <doc-id>       # a document (id or unique prefix)
python -m radar snapshot <snapshot-id> # a snapshot's sources and document set
python -m unittest discover -s tests   # test suite (no network needed)
```

Python 3.11+, standard library only. Corpus lives in `data/radar.db` (gitignored; delete it and re-run `ingest` to rebuild). Source registry: `sources/sources.toml` (mirrors `SOURCES.md`).

## Planned stages

| Stage | Focus |
|---|---|
| 0 | Project contract |
| 1 | Controlled corpus: small, reproducible, clearly defined sources *(current)* |
| 2 | Retrieval baseline: BM25, dense, hybrid |
| 3 | Evaluation benchmark: human judgments for relevance and meaningful change |
| 4 | Temporal monitoring: detect changes between snapshots |
| 5 | Attention-aware ranking: reduce what a person must inspect |
| 6 | Simple interface: changes, sources, evidence, inspection |
| 7 | Selective LLM assistance, only where experiments show benefit |
| 8 | Search strategy adaptation: recognizing and fixing retrieval gaps |

These stages are a research path, not commitments; later stages may be revised or dropped (`ROADMAP.md`).

## Repository map

| File | Contents |
|---|---|
| `PROJECT.md` | Broader problem, research question, hypothesis, non-goals, scope |
| `ARCHITECTURE.md` | Monitoring loop, architectural principles, conceptual data model |
| `EVALUATION.md` | Metrics, attention-cost dimensions, concepts that must not be conflated |
| `SOURCES.md` | Source registry and rules for adding sources |
| `DECISIONS.md` | Decision log: established and proposed decisions with reasoning |
| `ROADMAP.md` | Stages, goals, exit criteria |
| `radar/` | Stage 1 ingestion pipeline and CLI |
| `sources/sources.toml` | Machine-readable source registry (mirrors `SOURCES.md`) |
| `tests/` | Corpus-integrity tests (offline; fake fetcher) |
| `data/radar.db` | Corpus database — gitignored, regenerable by re-ingesting |
| `docs/experiments/` | Experiment records (question, method, result, conclusion) |

## How to contribute or experiment

1. Read `PROJECT.md` (hypothesis and non-goals) and `DECISIONS.md` (constraints) first.
2. Every experiment — especially one that could falsify the hypothesis — is recorded in `docs/experiments/` using the format in `docs/experiments/README.md`.
3. New sources go through `SOURCES.md` with a verified URL; no invented URLs.
4. Architectural changes are logged in `DECISIONS.md` with reasoning. Assumptions are documented, not hidden.
5. Unknowns are marked unknown. LLM output is interpretation, never evidence.

## Constraints in one line

Do not overbuild; do not hide assumptions; do not invent evidence; do not use an LLM as an authority; do not optimize for novelty; keep every component replaceable.
