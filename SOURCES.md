# SOURCES.md — Source Registry

**Status:** Stage 0 — registry structure defined; concrete entries recorded in Stage 1.

## Purpose

This file is the controlled corpus's source of truth. A source enters the system only when it has an entry here, and every document in the system must trace back to a registered source (`ARCHITECTURE.md`, Document → Source).

The goal is a **small, evaluable corpus**, not broad coverage. Coverage is a metric (`EVALUATION.md`), not a starting assumption.

## Rules

1. **No invented URLs.** Every URL recorded here must be verified (checked live) at the time it is recorded, with the date it was verified. Entries in this file currently carry no URLs for that reason.
2. **An LLM-generated summary is not a source.** It may be produced by the system; it is never registered as evidence.
3. **Every document keeps its original URL and source identity.** Normalization may clean text; it must not strip attribution.
4. **Prefer sources with clear provenance and publication dates** (`PROJECT.md`, source strategy): research papers first, official research/technical publications second, high-quality technical sources third.
5. **Access status is recorded honestly.** If a source is paywalled, partial, or format-limited, that is written down as a known access constraint, not discovered later as a surprise.

## Entry format

Each source entry records:

```text
Name
Type            (academic | official-research | technical | other)
URL             (verified, with verification date)
Topic           (which of the configured topics it serves)
Why it is included
Primary / secondary
Update frequency if known     (else: unknown)
Access constraints if any     (else: none known)
```

## Registry

### Active sources

*None yet.* Sources are added in Stage 1 as ingestion is built, each with a verified URL.

### Candidate sources (under consideration — no URLs recorded yet)

These are candidates only. None is approved until its URL is verified and the entry above is completed.

| Name | Type | Topic(s) | Why it is included | Primary / secondary | Update frequency | Notes |
|---|---|---|---|---|---|---|
| arXiv | academic | AI systems, Information Retrieval, AI agents, HCI | Preprint server with clear per-paper dates and IDs; large share of relevant literature | Primary (of the papers it hosts) | unknown | Full-text access expected; to be confirmed in Stage 1 |
| ACL Anthology | academic | Information Retrieval, Human-AI Interaction, HCI | Stable, citable venue archive with consistent metadata | Primary | unknown | Access and bulk-download terms to be confirmed in Stage 1 |
| OpenReview | academic | AI systems, Human-AI Interaction, HCI | Public reviews and decisions; useful provenance beyond the paper itself | Primary | unknown | API access to be confirmed in Stage 1 |
| PsyArXiv | academic | Cognitive science, Evidence / epistemic research | Preprints in psychology/cognitive science, where the topic list reaches beyond CS | Primary | unknown | Coverage and metadata quality to be assessed in Stage 1 |
| Lab research pages (individual labs, e.g. company research sections) | official-research | AI systems, AI agents | Where official technical reports appear before or instead of papers | Primary (of their own reports) | unknown | Per-lab entries to be added individually, never as one catch-all entry |
| Standards / major conference proceedings libraries (e.g. ACM DL) | academic | HCI | Canonical HCI literature | Primary | unknown | Likely paywalled; access constraint to be recorded before inclusion |

### Rejected or deferred sources

*None recorded yet.* When a source is considered and rejected (or deferred), record the name, date, and reason, so the decision is not silently re-litigated.
