# PROJECT.md — What Information Radar Is

**Status:** Stage 0 — project contract. No implementation exists yet.

## Research question

> **Can a retrieval system reliably surface information that is relevant and important enough that a person would otherwise have needed to find it themselves?**

Everything in this repository exists to answer that question. The project compares conventional information retrieval methods with AI-assisted retrieval and reasoning, and measures the difference.

The question the eventual system should let a person ask is:

> What changed since my previous snapshot that is worth investigating?

## Problem

The problem is not "keeping up with news." It is **information overload combined with imperfect retrieval**.

Two facts sit together:

1. There is more potentially relevant material than a person can monitor manually.
2. Retrieval is imperfect: systems miss things, rank badly, and mix primary evidence with commentary.

LLMs make information easier to access without necessarily making access to the information that *matters* more reliable. An LLM can produce a fluent answer while the important document never entered the result set. Fluency and coverage are different properties, and this project treats them as such.

The system therefore needs to investigate, as distinct dimensions:

- **retrieval quality** — does the system return the documents a person needed?
- **recall** — of the relevant documents that exist, what fraction were found?
- **relevance** — are returned documents actually pertinent to the question?
- **source coverage** — are the important sources represented at all?
- **novelty** — is this new relative to what was already known?
- **provenance** — can every surfaced item be traced to an original source?
- **temporal change** — what actually changed since the last snapshot?
- **human verification cost** — how much work does a person spend confirming results?

These dimensions are not interchangeable. `EVALUATION.md` defines how each is measured.

## Core hypothesis

> A combination of conventional information retrieval methods, temporal analysis, source metadata, and selective LLM assistance may provide a more reliable information-monitoring system than relying on an LLM to decide what information matters from the beginning.

**This is a hypothesis, not an assumption.** The system must be designed so that the hypothesis can fail.

### How the hypothesis can fail

The hypothesis fails if, on a manually judged benchmark (`EVALUATION.md`):

- a simple lexical baseline (BM25) matches or beats the more complex pipelines on recall of relevant documents, showing that added machinery buys nothing; or
- LLM-assisted stages do not improve measured outcomes enough to justify their added cost, opacity, and verification burden; or
- no configuration reliably surfaces important documents that a person would otherwise have missed — the central claim — over repeated snapshot cycles.

Failure is a valid and reportable result. Experiment records go in `docs/experiments/`.

## Non-goals

This project is **not**, initially, any of the following:

- a general-purpose search engine
- a chatbot
- a replacement for reading primary sources
- a system that determines objective truth automatically
- an autonomous research agent
- a system that summarizes the entire internet
- a system that maximizes the amount of information consumed
- an addictive news feed
- a system that hides retrieval uncertainty behind an LLM
- a showcase for impressive AI-generated summaries
- production infrastructure built prematurely

If a proposed feature serves one of these, it is out of scope until the project's stages say otherwise (`ROADMAP.md`).

## Initial scope

### Topics

The initial topic set is deliberately small:

1. AI systems
2. Human-AI Interaction
3. Information Retrieval
4. AI agents
5. HCI
6. Cognitive science
7. Evidence / epistemic research

These topics are **not permanent**. Topics are configurable: adding, removing, or renaming a topic must not require restructuring the system. Each topic has an id, a name, and a description (see the data model in `ARCHITECTURE.md`).

### Source strategy

Prefer sources where **provenance and publication dates are clear**. Initial source tiers, in order:

1. Research papers / academic publications
2. Official research or technical publications (labs, standards bodies, vendors' own research pages)
3. High-quality technical sources

Constraints:

- Do not attempt to ingest the entire web during the first experiment.
- Preserve the **original URL and source identity for every document**.
- An LLM-generated summary is **never** a source. It may be an output of the system; it is not evidence.

Concrete source entries live in `SOURCES.md`. No source enters the corpus until its URL and identity are recorded there.
