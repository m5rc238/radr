# SOURCES.md — Source Registry

**Status:** Stage 1 — active registry in use; 9 sources verified and ingesting (2026-10-08). Machine-readable configuration: `sources/sources.toml`.

## Purpose

This file is the controlled corpus's source of truth. A source enters the system only when it has an entry here, and every document in the system must trace back to a registered source (`ARCHITECTURE.md`, Document → Source).

The goal is a **small, evaluable corpus**, not broad coverage. Coverage is a metric (`EVALUATION.md`), not a starting assumption.

## Rules

1. **No invented URLs.** Every URL recorded here must be verified (checked live) at the time it is recorded, with the date it was verified.
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

All feed URLs below returned HTTP 200 with a parseable feed on **2026-10-08** (the verification date). Access method is direct feed fetch (RSS/Atom) via the polite fetcher (`radar/fetch.py`: robots.txt honored, 1 s delay, identifiable User-Agent).

| Name | Type | Feed URL (verified 2026-10-08) | Topic(s) | Why it is included | Primary / secondary | Update frequency | Access constraints |
|---|---|---|---|---|---|---|---|
| arXiv cs.AI | academic | https://rss.arxiv.org/rss/cs.AI | AI systems | Core AI systems preprints with stable IDs and per-paper dates | Primary (of the papers it hosts) | Weekday announcements (arXiv schedule) | Abstracts full text in feed; full PDFs not fetched |
| arXiv cs.IR | academic | https://rss.arxiv.org/rss/cs.IR | Information Retrieval | The retrieval literature this project is about | Primary | Weekday announcements | Same as above |
| arXiv cs.HC | academic | https://rss.arxiv.org/rss/cs.HC | HCI, Human-AI Interaction | Interface/interaction research for later stages | Primary | Weekday announcements | Same as above |
| arXiv cs.MA | academic | https://rss.arxiv.org/rss/cs.MA | AI agents | Multi-agent systems coverage | Primary | Weekday announcements | Same as above |
| arXiv q-bio.NC | academic | https://rss.arxiv.org/rss/q-bio.NC | Cognitive science | Extends the topic list beyond CS, as the Stage 0 candidates intended | Primary | Weekday announcements | Same as above |
| Google AI Blog | official-research | https://blog.google/technology/ai/rss/ | AI systems | Official technical announcements with dates; content fetched from the linked page (feed carries teasers only) | Primary (of its own posts) | Unknown (verified 2026-10-08) | None known |
| Google DeepMind Blog | official-research | https://deepmind.google/blog/rss.xml | AI systems, AI agents | Official research announcements; page-content mode | Primary (of its own posts) | Unknown (verified 2026-10-08) | None known |
| Hugging Face Blog | technical | https://huggingface.co/blog/feed.xml | AI systems, AI agents | High-signal technical write-ups; page-content mode | Secondary | Unknown (verified 2026-10-08) | None known |
| Import AI (Substack) | technical | https://importai.substack.com/feed | AI systems, Evidence / epistemic research | Long-running research newsletter with full text in the feed | Secondary | Unknown (verified 2026-10-08) | None known |

Notes:

- **Content provenance per source** is configured in `sources/sources.toml` (`content_from = "feed"` for arXiv and Import AI, whose feeds carry full abstracts/body text; `content_from = "page"` for the three blogs, whose feeds carry teasers only).
- The five arXiv feeds are **category-specific entries**, not one catch-all "arXiv" entry, so provenance stays precise. The same paper cross-listed in two categories is deduplicated by canonical URL within a run (`DECISIONS.md`, Decision 18).
- One cross-URL identical-content pair exists in the current corpus and is retained, not merged (`DECISIONS.md`, Decision 17).

### Candidate sources (under consideration — no URLs recorded yet)

These are candidates only. None is approved until its URL is verified and the entry above is completed.

| Name | Type | Topic(s) | Why it is included | Primary / secondary | Update frequency | Notes |
|---|---|---|---|---|---|---|
| ACL Anthology | academic | Information Retrieval, Human-AI Interaction, HCI | Stable, citable venue archive with consistent metadata | Primary | unknown | Access and bulk-download terms to be confirmed |
| OpenReview | academic | AI systems, Human-AI Interaction, HCI | Public reviews and decisions; useful provenance beyond the paper itself | Primary | unknown | API access to be confirmed |
| ACM Digital Library | academic | HCI | Canonical HCI literature | Primary | unknown | Likely paywalled; access constraint to be recorded before inclusion |
| Additional lab research pages | official-research | AI systems, AI agents | Same pattern as the DeepMind/Google/HF entries above; per-lab entries only, never one catch-all | Primary (of their own reports) | unknown | DeepMind, Google AI, and Hugging Face are now active; others added individually |

### Rejected or deferred sources

Recorded with date and reason so the decision is not silently re-litigated.

| Name | Date | Reason |
|---|---|---|
| PsyArXiv (OSF RSS) | 2026-10-08 | Candidate in Stage 0. The OSF preprint RSS endpoint returns an HTML single-page app, not a feed; no machine-readable feed verified. Deferred until a working API/feed path is found. |
| Nature News (`nhumbeh.rss`) | 2026-10-08 | Feed URL returns 404. Not usable as registered. |
| Distill | 2026-10-08 | Publication is defunct; archive URLs return 404. Not usable as a live source. |
