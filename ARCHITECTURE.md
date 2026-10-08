# ARCHITECTURE.md — Intended Architecture

**Status:** Stage 0 — documented intent only. Nothing here is implemented.

This file describes the conceptual architecture the project expects to build, in stages (`ROADMAP.md`). It is a contract for future implementation, not a specification of libraries or infrastructure.

## Pipeline

```text
Sources
   ↓
Ingestion
   ↓
Normalization
   ↓
Deduplication
   ↓
Document Store
   ↓
┌─────────────────────────────┐
│ Retrieval                   │
│                             │
│ BM25 / lexical              │
│ Dense / semantic            │
│ Hybrid                      │
└─────────────────────────────┘
   ↓
Reranking
   ↓
Temporal / change detection
   ↓
Evidence extraction
   ↓
Selective LLM reasoning
   ↓
Human inspection
```

Two properties of this pipeline matter:

- **Provenance flows upward.** Every item that reaches human inspection can be traced back through its retrieval run to a stored document with its original URL and source.
- **The human is in the loop by design.** The system surfaces candidates for investigation; it does not close the loop on its own judgment.

## Central architectural principle

**The LLM is not the retrieval system.**

LLMs are treated as one possible component inside the system — never as the source of evidence, never as the sole arbiter of what matters. LLM output is an interpretation or transformation of retrieved information.

Corollaries:

- An LLM-generated summary is not a document and never enters the document store as a source.
- Retrieval results must be measurable with or without any LLM component.
- Uncertainty and retrieval limitations must remain visible to the person inspecting results (`DECISIONS.md`, Decision 6).

## Required comparison

The architecture must support running the same topics, sources, and queries through:

```text
BM25
vs
Dense retrieval
vs
Hybrid retrieval
vs
Hybrid + reranking
vs
Hybrid + selective LLM assistance
```

This means each retrieval method must be a **replaceable component** behind a common interface: same inputs (query/topic, corpus snapshot), same outputs (ranked document IDs with scores), same evaluation harness (`EVALUATION.md`). If one method requires changing the data model or evaluation to run, the architecture has failed this requirement.

## Infrastructure restraint

Do not introduce any of the following unless a later experiment, recorded in `docs/experiments/`, demonstrates a concrete need:

- vector databases
- graph databases
- agents
- orchestration frameworks
- message queues
- microservices

Prefer, in order: a simple file, a single database table, a script, a standard IR library. Storage and language choices are Stage 1 decisions (see proposed decisions in `DECISIONS.md`).

Every choice must be replaceable: retrieval models, embedding models, rerankers, and LLM providers are components behind interfaces, not dependencies baked into the data model.

## Data model (conceptual)

An initial conceptual model. The purpose is to support experiments and provenance — not to model the domain exhaustively. Do not over-engineer the schema.

### Document

| Field | Notes |
|---|---|
| id | stable identifier |
| title | as published |
| URL | original, never rewritten |
| source | references Source |
| author | as published; unknown allowed |
| publication date | from the source; unknown allowed, marked unknown |
| retrieval date | when this system acquired it |
| raw content | as fetched |
| normalized content | cleaned text used for retrieval |
| content hash | for deduplication |

### Source

| Field | Notes |
|---|---|
| id | stable identifier |
| name | e.g. the publication or venue |
| URL | canonical location |
| source type | e.g. academic, official research, technical |
| authority / provenance metadata | what is known about who publishes it and how |

### Topic

| Field | Notes |
|---|---|
| id | stable identifier |
| name | e.g. "Information Retrieval" |
| description | what falls inside and outside the topic |

### Retrieval Run

| Field | Notes |
|---|---|
| id | stable identifier |
| query / topic | what was asked |
| retrieval method | e.g. `bm25`, `dense`, `hybrid`, `hybrid+llm` |
| timestamp | when the run executed |
| parameters | method configuration, recorded verbatim |
| returned document IDs | ordered |
| scores | per returned document |

A retrieval run is the unit of comparison: every method's output on the same query is recorded the same way.

### Snapshot

| Field | Notes |
|---|---|
| id | stable identifier |
| topic | which topic |
| timestamp | when taken |
| document set | documents present at this time |
| detected changes | what changed relative to the previous snapshot |

### Evaluation Judgment

| Field | Notes |
|---|---|
| query | the information need |
| document | the candidate document |
| relevance judgment | e.g. relevant / not relevant / unjudged |
| evaluator | who judged it |
| notes | why, ambiguities, disagreements |

Judgments are the ground truth for `EVALUATION.md`. They are created by a human, not by an LLM, unless an experiment explicitly measures agreement between LLM judgments and human judgments — and reports it as such.
