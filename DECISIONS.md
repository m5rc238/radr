# DECISIONS.md — Decision Log

**Status:** Stage 1 complete — proposed decisions A, B, D, E confirmed and promoted below; Stage 1 implementation decisions recorded.

Every architectural decision in this project is recorded here with its reasoning (`PROJECT.md` non-goal: hiding assumptions). Decisions are labeled:

- **Established** — decided; changing one requires editing this file with the reason.
- **Proposed** — suggested, not yet tested or agreed; may be overturned by an experiment or in a later stage.

---

## Established decisions

### Decision 1 — Start with conventional information retrieval before adding LLMs

**Reason:** We need a measurable baseline. Without a non-LLM baseline, any later result attributed to "LLM assistance" is uninterpretable — there is nothing to compare it against, and no way to detect regressions.

**Consequence:** No LLM components enter the system before Stage 7 (selective LLM assistance); Stages 1–3 build the conventional baseline first. This is a sequencing decision, not a claim that LLMs are useless.

### Decision 2 — Use multiple retrieval methods

**Reason:** We want to test whether semantic/LLM approaches actually improve retrieval. A single method answers nothing about what helps; the research question is explicitly comparative (`ARCHITECTURE.md`, required comparison).

**Consequence:** All methods run behind one interface against the same corpus, queries, and judgments.

### Decision 3 — Preserve provenance

**Reason:** A user needs to inspect the original evidence and understand why a document was surfaced. Provenance is also what makes evaluation possible: without original URL, source, and retrieval run recorded, results cannot be audited or reproduced.

**Consequence:** Original URL and source identity are stored per document and flow through to output (`ARCHITECTURE.md`).

### Decision 4 — Keep the initial corpus small

**Reason:** A controlled corpus makes evaluation possible. Recall cannot be measured over a corpus whose relevant-document set is unknown; a small, known corpus can be judged.

**Consequence:** The source registry (`SOURCES.md`) starts nearly empty and grows only with verified entries. Coverage gaps are accepted at first and measured, not hidden.

### Decision 5 — No fancy UI in Stage 0

**Reason:** The retrieval problem should be understood before optimizing presentation. A polished interface over weak retrieval makes weak retrieval harder to notice.

**Consequence:** A minimal interface appears only at Stage 6, after retrieval, evaluation, and temporal monitoring exist.

### Decision 6 — The system must expose uncertainty and retrieval limitations

**Reason:** The project is explicitly investigating *reliable* access to information. A system that conceals what it did not find, or presents LLM interpretation as fact, undermines the very thing being tested (`PROJECT.md`, non-goals).

**Consequence:** Outputs carry provenance, scores, and method identity; unknown fields are marked unknown rather than filled in.

### Decision 7 — Treat attention as a constrained resource

**Reason:** The goal is not simply retrieval accuracy. The eventual system should investigate whether useful information can be surfaced with less human inspection — attention cost is a first-class concern alongside recall and relevance (`PROJECT.md`, attention is a resource).

**Consequence:** Evaluation includes inspection burden and verification time (`EVALUATION.md`); no design may claim success on retrieval metrics alone.

### Decision 8 — Do not build a feed

**Reason:** The project is explicitly investigating an alternative to continuous information consumption. An engagement-optimized or continuously updating surface would work against the research question (`PROJECT.md`, this is not a better feed).

**Consequence:** The interface (Stage 6) supports intermittent inspection; nothing may be optimized for time spent, scrolling, or documents surfaced (`PROJECT.md`, non-goals).

### Decision 9 — Separate retrieval from importance

**Reason:** Finding a document and determining whether it deserves attention are different problems. Collapsing them lets a system claim success by retrieving a lot while surfacing little that matters.

**Consequence:** The pipeline ranks candidates only after retrieval and change detection (`ARCHITECTURE.md`), and evaluation reports discovery and ranking as separate dimensions (`EVALUATION.md`).

### Decision 10 — Separate novelty from meaningfulness

**Reason:** New information is not necessarily important information. Treating "new" as "worth attention" is how feeds manufacture volume.

**Consequence:** Novelty/change detection and importance judgment are distinct steps and distinct judgment types; a novel item is not promoted on novelty alone (`EVALUATION.md`, concepts that must not be conflated).

### Decision 11 — Treat meaningfulness as an empirical question

**Reason:** The system should not silently encode its own definition of importance without evaluation. "Meaningful change" must ultimately involve human judgment (`PROJECT.md`).

**Consequence:** The benchmark carries human meaningful-change judgments (Stage 3); any model-scored importance is evaluated against those judgments, never substituted for them.

### Decision 12 — Storage: one SQLite file; no vector database (confirmed from Proposed A)

**Reason:** Confirmed in Stage 1. The corpus is small and the data model is simple (`ARCHITECTURE.md`); everything needed (documents, versions, observations, snapshots, runs) lives in one SQLite database with plain tables. A vector database remains infrastructure without a demonstrated need.

**Consequence:** Corpus state is `data/radar.db` (gitignored, regenerable by re-ingesting). Dense retrieval in Stage 2 can store embeddings in ordinary tables; revisit only with a measured need (`ARCHITECTURE.md`, infrastructure restraint).

### Decision 13 — Implementation language: Python 3.11, standard library only for Stage 1 (confirmed from Proposed B)

**Reason:** Confirmed in Stage 1. `sqlite3`, `tomllib`, `urllib`, `xml.etree`, and `unittest` cover the entire Stage 1 pipeline with zero third-party dependencies — nothing to pin, audit, or break.

**Consequence:** Stage 1 ships with no `requirements.txt`. Any later stage that needs a third-party library (e.g. an IR library in Stage 2) records the addition here with its justification; the choice does not affect the data model.

### Decision 14 — Every ingest run creates an immutable corpus snapshot (confirmed from Proposed D)

**Reason:** Confirmed in Stage 1. Retrieval runs are only comparable if every method ran against the same corpus state; snapshotting per ingest run is the simplest mechanism that guarantees it.

**Consequence:** Each `python -m radar ingest` records a snapshot: the run's timestamp, per-source status, and the exact set of documents observed (a document can belong to several snapshots; its history is append-only — Decision 17). Interpretation note: `ARCHITECTURE.md` also gives Snapshot a *topic* field and *detected changes*; those are produced by Stage 4's temporal monitoring, not by ingestion. Stage 1 snapshots are corpus-state references only — a staging of that entity, not a redefinition of it.

### Decision 15 — Version-control boundaries (confirmed from Proposed E)

**Reason:** Confirmed in Stage 1: small, high-value, human-made artifacts belong in git; large, regenerable ones do not.

**Consequence:** In git: documentation, `sources/sources.toml`, `radar/`, `tests/`. Ignored (`.gitignore`): `data/`, `*.db` — the corpus is rebuilt by re-ingestion, and the rebuild is validated as part of Stage 1 exit criteria.

### Decision 16 — Document identity is the conservative canonical URL

**Reason:** Identity must be stable across runs and sources without ever merging two documents that are not provably the same. A canonical form of the URL is the only identity signal available before fetching content.

**Consequence:** `doc_id = sha256(canonical_url)[:16]`. Canonicalization is deliberately conservative: lowercase host, drop fragment, drop known tracking parameters (`utm_*`, `fbclid`, …), sort remaining query parameters, strip trailing slash, remove default ports. **http and https are not merged** — mapping schemes could wrongly fuse distinct documents; a duplicate with both schemes would surface as a cross-URL identical-content report instead (Decision 17).

### Decision 17 — Change detection by content hash; history is append-only; identical content at different URLs is retained

**Reason:** Content must be comparable across runs without overwriting evidence. Automatic merging of same-content documents risks destroying provenance; the conservative failure mode is to keep both and report.

**Consequence:** `content_hash = sha256(normalized_content)`; a change appends a row to `document_versions` and never rewrites prior versions — old content stays retrievable. If two different canonical URLs produce the same content hash, both documents are **retained** and the run report counts `identical_content_other_url`; nothing is auto-rejected. Known source-side quirk, recorded honestly: arXiv feeds annotate entries with `Announce Type: new|cross`, and that text can flip for the same paper between announcements — genuine source-side text change, so it is recorded as a changed document rather than suppressed.

### Decision 18 — Deduplication scope: one attempt per canonical URL per ingest run

**Reason:** The same paper legitimately appears in multiple registered feeds (arXiv cross-lists announce it in each category feed). Processing it once per run keeps run reports meaningful and prevents a second feed's annotation differences from being recorded as content changes.

**Consequence:** A run-wide seen-set: the first occurrence of a canonical URL in a run wins; later occurrences from any source are counted as `duplicates` and skipped. First-writer-wins means a document's `source_id` is the first registered source that carried it in the run that created it; the per-document URL remains the URL as discovered.

### Decision 19 — Stage 1 interface is a CLI, not npm scripts

**Reason:** The Stage 1 spec's `npm run …` examples assumed a Node toolchain; the implementation follows Decision 13 (Python) and needs no task runner.

**Consequence:** Commands are `python -m radar ingest | stats | inspect <doc-id> | snapshot <id> | snapshots`, each accepting `--config` and `--db`. Same capabilities as the spec's examples (ingest, statistics, document inspection, snapshot inspection); capability parity, different spelling. Exit code is non-zero when any source failed, so partial runs are visible to scripts.

### Decision 20 — Source registry is TOML

**Reason:** The Stage 1 spec allows a format other than YAML; TOML is readable by humans and parsed by the Python standard library (`tomllib`), keeping Decision 13's zero-dependency promise.

**Consequence:** `sources/sources.toml` is the machine-readable registry; `SOURCES.md` remains the human-facing registry and decision record. The two are kept consistent by construction: every source in the TOML has a verified entry in `SOURCES.md`.

### Decision 21 — Per-source content provenance (`content_from`)

**Reason:** Feeds differ: arXiv and Import AI carry full abstract/body text; the blog feeds carry teasers only. Treating them uniformly would either store teaser text as corpus content (weak evidence) or fetch pages that don't need fetching.

**Consequence:** Each source declares `content_from = "feed"` or `"page"` in `sources/sources.toml`. Page mode fetches the entry's own URL through the same polite fetcher (robots, delay, decompression, binary rejection) and stores the normalized page text; fetch failures are recorded per entry without failing the source.

---

## Proposed decisions

*Labelled proposed. These are starting points for later stages; they are not established facts and should be revisited with evidence.*

**Resolved in Stage 1:** Proposed A (storage) → Decision 12; Proposed B (language) → Decision 13; Proposed D (snapshots) → Decision 14; Proposed E (version-control boundaries) → Decision 15. Promoted to Established above after implementation and validation. **Proposed C** remains proposed: Stage 1 has no embeddings, rerankers, or LLMs to isolate — it becomes testable when the first provider enters (Stage 2 or later).

### Proposed C — Provider isolation for embeddings, rerankers, and LLMs

**Reason:** Retrieval models, embedding models, rerankers, and LLM providers must be replaceable (`PROJECT.md` constraints). All external model calls go through one thin interface, and runs record which provider/model/parameters produced them.

**Status:** Proposed.

### Proposed F — Human judgment as ground truth

**Reason:** Relevance judgments are made by a human. LLM-generated judgments may be *studied* (e.g. agreement with human judgments) but are not ground truth unless an experiment shows otherwise and reports it explicitly (`EVALUATION.md`).

**Status:** Proposed. Protocol (number of evaluators, disagreement handling) decided in Stage 3.
