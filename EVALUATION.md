# EVALUATION.md — How the System Is Judged

**Status:** Stage 0 — metrics defined; benchmark built in Stage 3.

This is the most important file in the repository. The project succeeds or fails based on what is measured here.

## Framing

Information Radar is evaluated **as an information retrieval system**, not as an AI application. The standards are IR standards: did the system return the documents a person needed, and did it rank them usefully?

The primary concern is **missed relevant information**. A system that produces beautiful summaries but fails to retrieve important documents is not successful. Summary quality, fluency, and presentation are secondary to coverage of what matters.

All metrics below are computed against a **manually judged benchmark** (Stage 3): a set of queries/topics with human relevance judgments for candidate documents (`ARCHITECTURE.md`, Evaluation Judgment). Metrics cannot be trusted before that benchmark exists; numbers produced without judgments are labeled as such.

## Retrieval metrics

| Metric | What it tells us |
|---|---|
| **Recall@10** | Of all judged-relevant documents for a query, what fraction appeared in the top 10? Direct measure of early missed information. |
| **Recall@20** | Same, at depth 20. Whether relevant documents are being found at all, just ranked lower. |
| **Precision@10** | Of the top 10 returned, how many are relevant? How much of the person's attention is spent on non-relevant material. |
| **nDCG@10** | Are the relevant documents ranked near the top, in order of usefulness? Rewards ranking quality, penalizes burying highly relevant items. |
| **MRR** | How high does the first relevant document appear? Measures how soon the system gets to something worth reading. |

Reporting convention: report per-query values and their mean; never report a mean without the spread or the per-query results. A method that wins on average while failing completely on two topics is not reliable — and reliability is the research question.

Recall metrics require knowing how many relevant documents exist for a query. On a small controlled corpus this is approximated by pooling judgments across all retrieval methods being compared (pooling is planned for Stage 3; details TBD).

## Additional measures

| Measure | What it tells us |
|---|---|
| **Duplicate rate** | Fraction of returned results that are duplicates or near-duplicates of each other. High duplication means deduplication or ranking is failing, and wastes attention. |
| **Source diversity** | How many distinct sources appear in a result set, and whether results are dominated by one source. A system that only ever surfaces one venue has a coverage problem. |
| **Retrieval latency** | Time to return results. Not a goal in itself; recorded so that accuracy gains that make the system unusable-slow are visible. |
| **Human verification time** | How long a person spends confirming that surfaced documents are real, relevant, and correctly characterized. This is the cost side of the value equation: a method that surfaces more candidates but triples verification time may be worse. |
| **Number of relevant discoveries** | Documents judged relevant that the person had **not** seen before and would likely have missed. This is the closest measurable proxy for the research question. |

## Concepts that must not be conflated

These are distinct properties. A system can have one without the others, and reports must say which is being claimed.

```text
Access      Retrieval     Relevance    Ranking     Coverage     Reliability
```

| Concept | Definition | Failure looks like |
|---|---|---|
| **Access** | The document can be reached at all (the system can fetch/read it). | Source exists but is not ingestable; paywall, format, or robots failure. |
| **Retrieval** | Given a query, the system returns the document into its candidate set. | Relevant document exists in the corpus but never appears in results. |
| **Relevance** | A returned document actually pertains to the information need. | System returns topically adjacent but useless material. |
| **Ranking** | Relevant documents appear early enough to be inspected. | Good documents exist in the results but at position 40. |
| **Coverage** | The set of sources and topics the system monitors is broad enough that important changes fall inside it. | Everything is retrieved perfectly from sources that miss the important events. |
| **Reliability** | The above hold consistently, across time and topics, with visible uncertainty when they do not. | Good scores on average, silent failures on the topics a person cares about. |

A system may score well on relevance and ranking while having no access (bad sources) or no coverage (narrow corpus). The research question is about **reliable** surfacing of important information, which requires all six.

## What would count as success

TBD — to be set in Stage 3 once the benchmark exists. Working criterion to be replaced, not treated as established: the system repeatedly surfaces relevant, previously-unseen documents at a rate a person judges worth the verification time, with missed relevant information low enough to trust.

## What is currently unknown

- Judgment protocol details (number of evaluators, disagreement handling) — decided in Stage 3.
- Query set design (topic-level queries vs. specific questions) — decided in Stage 3.
- Baseline numbers of any kind. No measurements exist yet; any number in this repository before Stage 3 is a placeholder, not a result.
