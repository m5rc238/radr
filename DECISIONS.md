# DECISIONS.md — Decision Log

**Status:** Stage 0 — initial decisions recorded.

Every architectural decision in this project is recorded here with its reasoning (`PROJECT.md` non-goal: hiding assumptions). Decisions are labeled:

- **Established** — decided for Stage 0; changing one requires editing this file with the reason.
- **Proposed** — suggested, not yet tested or agreed; may be overturned by an experiment or in Stage 1.

---

## Established decisions

### Decision 1 — Start with conventional information retrieval before adding LLMs

**Reason:** We need a measurable baseline. Without a non-LLM baseline, any later result attributed to "LLM assistance" is uninterpretable — there is nothing to compare it against, and no way to detect regressions.

**Consequence:** Stages 1–3 contain no LLM components. This is a sequencing decision, not a claim that LLMs are useless.

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

**Consequence:** A minimal interface appears only at Stage 5, after retrieval and evaluation exist.

### Decision 6 — The system must expose uncertainty and retrieval limitations

**Reason:** The project is explicitly investigating *reliable* access to information. A system that conceals what it did not find, or presents LLM interpretation as fact, undermines the very thing being tested (`PROJECT.md`, non-goals).

**Consequence:** Outputs carry provenance, scores, and method identity; unknown fields are marked unknown rather than filled in.

---

## Proposed decisions

*Labelled proposed. These are starting points for Stage 1; they are not established facts and should be revisited with evidence.*

### Proposed A — Storage: flat files + a single relational database (e.g. SQLite); no vector database

**Reason:** The corpus is small and the data model is simple (`ARCHITECTURE.md`). Dense retrieval can be computed with a standard library over embeddings stored in a table or file. A vector database is infrastructure without a demonstrated need.

**Status:** Proposed. Revisit if an experiment measures a concrete need (`ARCHITECTURE.md`, infrastructure restraint).

### Proposed B — Implementation language: Python

**Reason:** Mature standard IR libraries and evaluation tooling exist in Python; lowest-friction path to a boring, measurable pipeline.

**Status:** Proposed. Confirm in Stage 1; the choice does not affect the data model.

### Proposed C — Provider isolation for embeddings, rerankers, and LLMs

**Reason:** Retrieval models, embedding models, rerankers, and LLM providers must be replaceable (`PROJECT.md` constraints). All external model calls go through one thin interface, and runs record which provider/model/parameters produced them.

**Status:** Proposed.

### Proposed D — Immutable corpus snapshots

**Reason:** Retrieval runs are only comparable if every method ran against the same corpus at the same state. Snapshots give each retrieval run a corpus-version reference, making results reproducible.

**Status:** Proposed. Fits the Snapshot entity in `ARCHITECTURE.md`; exact mechanism decided in Stage 1.

### Proposed E — What is version-controlled

**Reason:** Small, high-value, human-made artifacts belong in git: documentation, judgments, experiment records, configuration. Large, regenerable artifacts (raw corpus, indexes, embeddings, run outputs) do not (`.gitignore`).

**Status:** Proposed. Exact boundaries set when the corpus format is chosen in Stage 1.

### Proposed F — Human judgment as ground truth

**Reason:** Relevance judgments are made by a human. LLM-generated judgments may be *studied* (e.g. agreement with human judgments) but are not ground truth unless an experiment shows otherwise and reports it explicitly (`EVALUATION.md`).

**Status:** Proposed. Protocol (number of evaluators, disagreement handling) decided in Stage 3.
