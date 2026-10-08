# Stage 1 Report — Controlled Corpus

**Date:** 2026-10-08 · **Commit:** `1a1d3a7` · **Status:** complete · **Next:** Stage 2 (not started)

This is the closing record for Stage 1 of `ROADMAP.md`: what was built, what it produces, how it was validated, and what is known to be imperfect.

## 1. What was built

The full Stage 1 pipeline — fetch → parse → normalize → dedupe → store → snapshot → inspect — in `radar/`, using Python 3.11 and the standard library only (`sqlite3`, `tomllib`, `urllib`, `xml.etree`, `unittest`; Decision 13). No third-party dependencies, no retrieval, no embeddings, no LLM, no UI.

Interface (Decision 19):

```sh
python -m radar ingest                 # one cycle; creates a snapshot
python -m radar stats                  # corpus statistics
python -m radar snapshots              # list snapshots
python -m radar inspect <doc-id>       # document (id or unique prefix)
python -m radar snapshot <snapshot-id> # snapshot's sources and document set
python -m unittest discover -s tests   # offline test suite
```

## 2. Corpus

- **196 documents** from **9/9 successful sources**; published range 2026-05-11 → 2026-10-07.
- Every document carries: original URL, canonical URL, source id, author, publication date (or explicit unknown), first/last retrieval timestamps, normalized content, content hash, and append-only version history.
- Storage: single SQLite file `data/radar.db` (Decision 12), gitignored and regenerable by re-ingesting (Decision 15).

## 3. Sources

All 9 feed URLs verified live on 2026-10-08 and registered in `SOURCES.md` + `sources/sources.toml`:

- arXiv cs.AI, cs.IR, cs.HC, cs.MA, q-bio.NC (content from feed)
- Google AI Blog, Google DeepMind Blog, Hugging Face Blog (content from page — feeds carry teasers only)
- Import AI (Substack) (content from feed)

Rejected/deferred with reasons recorded: PsyArXiv OSF RSS (returns an HTML SPA, not a feed), Nature News feed (404), Distill (defunct, 404).

## 4. Decisions

Proposed A/B/D/E confirmed and promoted to Established Decisions 12–15 (SQLite storage, Python-stdlib implementation, per-ingest-run snapshots, git boundaries). Proposed C remains proposed — Stage 1 has no providers to isolate.

New Stage 1 decisions 16–21: conservative canonical-URL identity (no http/https merging), content-hash change detection with append-only history (cross-URL identical content retained, never auto-merged), run-wide dedupe (arXiv cross-lists), CLI instead of npm scripts, TOML registry, per-source `content_from`.

`ARCHITECTURE.md`'s Snapshot entity carries a topic field and detected changes; those belong to Stage 4's temporal monitoring. Stage 1 snapshots are corpus-state references only — documented as a staging of that entity in Decision 14, not a redefinition.

## 5. Validation

| # | Check | Result |
|---|---|---|
| A | Fresh ingest from an empty database | 9/9 sources, 196 documents, all with provenance |
| B | Re-run ingestion | 0 new, 0 changed; cross-feed duplicates consistently counted (6/run), never stored |
| C | Changed content (local fixture feed v1 → v2, via CLI) | changed=1, same document id, 2 versions, original content retrievable |
| D | One unreachable source alongside a healthy one | failed source reported + logged, healthy source ingests, exit code 1 |
| E | Delete `data/radar.db` and rebuild | corpus reproduced from empty |

## 6. Tests

49 offline tests (`python -m unittest discover -s tests`), run against a fake fetcher — no network: identity stability, URL normalization, content hashing, exact and cross-feed duplicate detection, repeated ingestion, snapshot creation, observations across snapshots, changed-content history preservation, fetch decompression and binary rejection, RSS/Atom parser behavior.

## 7. Real bugs found and fixed during validation

1. **Silent gzip corruption.** deepmind.google serves gzip-encoded bodies with no `Content-Encoding` header; the first build stored decompressed binary garbage as a document's content. Fixed: `Accept-Encoding: identity`, gzip magic-byte detection, `Content-Encoding` fallback, and rejection of bodies containing NUL bytes (`radar/fetch.py`).
2. **Cross-feed duplicates recorded as changes.** The same paper announced in two arXiv category feeds was processed twice per run; the second feed's differing annotation ("Announce Type: cross") was recorded as a content change. Fixed: run-wide dedupe (Decision 18).
3. **Fixture feed rejected as invalid XML** — a missing namespace declaration in the test fixture; the parser's rejection was correct behavior and the fixture was fixed.

## 8. Known limitations (recorded, not hidden)

- **arXiv announce-type flapping.** arXiv feeds annotate entries with `Announce Type: new|cross`, and that text can flip for the same paper between announcements. Content-hash change detection will record this as a changed document. This is genuine source-side text change, so it is recorded rather than suppressed (Decision 17).
- **Page-mode site chrome.** Blog content fetched in `content_from = "page"` mode includes some navigation/social text alongside the article body after normalization (scripts, nav, header, footer are stripped; inline chrome is not). Retrieval quality implications, if any, are a Stage 2+ question.
- **Cross-URL identical content.** The current corpus contains one pair of different URLs with identical content; both are retained and reported (`identical_content_other_url`), per the conservative policy (Decision 17).
- **First-writer-wins source attribution.** For a paper cross-listed in several registered feeds, `source_id` is whichever feed was processed first in the creating run (Decision 18).
- **Update frequency mostly unknown.** Only arXiv's weekday announcement schedule is known; other sources are marked "unknown (verified 2026-10-08)" in `SOURCES.md` until observed over time.

## 9. Stopped here

Stage 2 (retrieval baseline) has not been started. Stage 1 exit criteria in `ROADMAP.md` are met and recorded above.
