# Information Radar

A personal information retrieval system that helps a person detect **meaningful changes in a set of topics over time**, without constant information monitoring. It is built as a research project with a falsifiable hypothesis and measured evaluation.

> **This project does not assume that an LLM is the best retrieval mechanism. It is designed to test that question.**

## Research question

> **Can a retrieval system reliably surface information that is relevant and important enough that a person would otherwise have needed to find it themselves?**

The system compares conventional information retrieval (BM25, dense, hybrid, reranking) with AI-assisted retrieval and reasoning, and measures the difference.

## Why retrieval quality matters

LLMs make information easier to access without necessarily making access to the information that *matters* more reliable. A fluent answer and a complete result set are different properties. This project measures recall, relevance, coverage, provenance, and human verification cost — the properties that determine whether important information was actually found. See `EVALUATION.md`.

The system is judged as an information retrieval system, not as an AI application. **The primary concern is missed relevant information.**

## Current stage

**Stage 0 — project contract.** This repository contains documentation only: the problem definition, intended architecture, evaluation plan, source registry, decision log, and roadmap. No application code exists yet.

## Planned stages

| Stage | Focus |
|---|---|
| 0 | Project contract *(current)* |
| 1 | Ingestion and a small, repeatable local corpus |
| 2 | Retrieval baseline: BM25, dense, hybrid |
| 3 | Manually judged benchmark and measured performance |
| 4 | Temporal change detection across snapshots |
| 5 | Simple interface: overview, changes, topics, sources, search, evaluation |
| 6 | Selective LLM assistance, only where experiments show value |
| 7 | Comparative experiments across the complete approaches |

Details and exit criteria: `ROADMAP.md`.

## Repository map

| File | Contents |
|---|---|
| `PROJECT.md` | Problem, core hypothesis, non-goals, initial scope |
| `ARCHITECTURE.md` | Intended pipeline, architectural principles, conceptual data model |
| `EVALUATION.md` | Metrics, additional measures, concepts that must not be conflated |
| `SOURCES.md` | Source registry and rules for adding sources |
| `DECISIONS.md` | Decision log: established and proposed decisions with reasoning |
| `ROADMAP.md` | Stages, goals, exit criteria |
| `docs/experiments/` | Experiment records (question, method, result, conclusion) |

## How to contribute or experiment

1. Read `PROJECT.md` (hypothesis and non-goals) and `DECISIONS.md` (constraints) first.
2. Every experiment — especially one that could falsify the hypothesis — is recorded in `docs/experiments/` using the format in `docs/experiments/README.md`.
3. New sources go through `SOURCES.md` with a verified URL; no invented URLs.
4. Architectural changes are logged in `DECISIONS.md` with reasoning. Assumptions are documented, not hidden.
5. Unknowns are marked unknown. LLM output is interpretation, never evidence.

## Constraints in one line

Do not overbuild; do not hide assumptions; do not invent evidence; do not use an LLM as an authority; do not optimize for novelty; keep every component replaceable.
