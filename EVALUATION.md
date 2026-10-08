# EVALUATION.md — How the System Is Judged

**Status:** Stage 0 — metrics defined; benchmark built in Stage 3.

This is the most important file in the repository. The project succeeds or fails based on what is measured here.

## Framing

Information Radar is evaluated as an information retrieval **and monitoring** system, not as an AI application. Two standards apply:

- the IR standard — did the system return the documents a person needed, ranked usefully?
- the monitoring standard — did it surface meaningful changes while requiring little inspection?

> **A system should not be considered successful simply because it retrieves or summarizes many documents.**

A system that produces beautiful summaries but misses important changes **fails the evaluation**. Summary quality, fluency, and presentation are secondary to surfacing what matters at low attention cost.

The primary concern is **missed relevant information and missed meaningful changes**.

All metrics below are computed against a **manually judged benchmark** (Stage 3): a set of queries/topics with human judgments for both relevance and meaningful change (`ARCHITECTURE.md`, Evaluation Judgment). Metrics cannot be trusted before that benchmark exists; numbers produced without judgments are labeled as such.

## IR metrics — necessary but insufficient

| Metric | What it tells us |
|---|---|
| **Recall@10** | Of all judged-relevant documents for a query, what fraction appeared in the top 10? Direct measure of early missed information. |
| **Recall@20** | Same, at depth 20. Whether relevant documents are being found at all, just ranked lower. |
| **Precision@10** | Of the top 10 returned, how many are relevant? How much of the person's attention is spent on non-relevant material. |
| **nDCG@10** | Are the relevant documents ranked near the top, in order of usefulness? Rewards ranking quality, penalizes burying highly relevant items. |
| **MRR** | How high does the first relevant document appear? Measures how soon the system gets to something worth reading. |

These metrics are **necessary**: without them, no claim that retrieval works at all is credible. They are **insufficient** for the eventual goal. They measure retrieval given a query — not whether changes worth attention were surfaced, not how many items a person had to inspect, and not whether an important development sat outside every query.

Reporting convention: report per-query values and their mean; never report a mean without the spread or the per-query results. A method that wins on average while failing completely on two topics is not reliable — and reliability is the research question.

Recall metrics require knowing how many relevant documents exist for a query. On a small controlled corpus this is approximated by pooling judgments across all retrieval methods being compared (pooling planned for Stage 3; details TBD).

## Monitoring and attention dimensions

These dimensions address what the IR metrics cannot. Discovery and coverage become measurable with the Stage 3 benchmark; inspection burden and verification time require human use of the system; the last is still an open research direction.

### Discovery

How many relevant or meaningful changes did the system surface? Counted against human judgment per snapshot cycle — not documents returned, but changes a person confirms were worth having surfaced.

### Coverage

What important parts of the information environment were missed? Discovery measures what was found; coverage asks what was not. Both are required: a system can score well on retrieval metrics while entire sources or developments sit outside its reach.

### Inspection burden

How many items did the person need to inspect before deciding what mattered? Includes false candidates, near-duplicates, and items judged not worth acting on. Lower is better at equal discovery.

### Human verification time

How long does it take a person to determine whether surfaced information actually matters? This is the cost side of the value equation: a method that surfaces more candidates but triples verification time may be worse.

### Valuable discoveries per unit of attention

The intended direction of value: **increase useful discoveries while reducing human inspection effort.** **No formula is defined yet.** This is an evaluation direction requiring experimentation — not a metric on record. How discovery and attention trade off (and whether one measure fits all topics) is itself an open question.

## Operational measures

| Measure | What it tells us |
|---|---|
| **Duplicate rate** | Fraction of returned results that are duplicates or near-duplicates. High duplication means deduplication or ranking is failing, and wastes attention. |
| **Source diversity** | How many distinct sources appear, and whether results are dominated by one source. A system that only ever surfaces one venue has a coverage problem. |
| **Retrieval latency** | Time to return results. Not a goal in itself; recorded so that accuracy gains that make the system unusable-slow are visible. |

## "Meaningful change" is an evaluation variable

**Meaningfulness must ultimately involve human judgment.** It is never defined as whatever the algorithm says is important (`PROJECT.md`).

The following are not synonyms:

```text
Relevant
Novel
Changed
Important
Worth investigating
```

A paper can be relevant without representing a meaningful change. A new development can be meaningful even if it is not obviously similar to previous queries.

The Stage 3 benchmark therefore carries **two judgment types**:

- **relevance judgments** → the IR metrics above
- **meaningful-change judgments** → the monitoring and attention dimensions

Whether either judgment can be predicted reliably — by conventional methods or by an LLM — is exactly what the project tests. Until that is tested, "meaningful change" is a human judgment the system is trying to earn, not a quantity it computes.

## Concepts that must not be conflated

These are distinct properties. A system can have one without the others, and reports must say which is being claimed.

```text
Access   Retrieval   Relevance   Novelty   Change   Importance
Coverage   Reliability   Human attention cost   (+ ranking quality)
```

| Concept | Definition | Failure looks like |
|---|---|---|
| **Access** | The document can be reached at all (the system can fetch/read it). | Source exists but is not ingestable; paywall, format, or robots failure. |
| **Retrieval** | Given a query, the system returns the document into its candidate set. | Relevant document exists in the corpus but never appears in results. |
| **Relevance** | A returned document actually pertains to the information need. | System returns topically adjacent but useless material. |
| **Ranking** | (quality within retrieval) Relevant documents appear early enough to be inspected. | Good documents exist in results but at position 40. Measured by nDCG/MRR. |
| **Novelty** | The information is new relative to what the system (or person) already has. | Old material re-surfaced as if it were news. |
| **Change** | The information environment differs from the previous snapshot. | A "new" document that says nothing new; or a real change not detected. |
| **Importance** | The change deserves a person's attention. Never self-assigned — ultimately a human judgment. | Important development flagged as minor; trivial update flagged as major. |
| **Coverage** | The monitored sources and topics are broad enough that important changes fall inside them. | Everything retrieved perfectly from sources that miss the important events. |
| **Reliability** | The above hold consistently, across time and topics, with visible uncertainty when they do not. | Good scores on average, silent failures on the topics a person cares about. |
| **Human attention cost** | The inspection and verification effort the system imposes on a person. | High discovery achieved only by flooding the person with candidates. |

A system may score well on relevance and ranking while having no access (bad sources) or no coverage (narrow corpus), or while imposing an unacceptable attention cost. The research question is about surfacing meaningful changes **reliably and cheaply in attention terms**, which requires all of these.

## What would count as success

TBD — to be set in Stage 3 once the benchmark exists. Working criterion to be replaced, not treated as established: the system repeatedly surfaces changes a person judges worth inspecting, at an inspection burden low enough to be trusted, with missed relevant and meaningful changes low enough that coverage can be believed.

## What is currently unknown

- Judgment protocol details (number of evaluators, disagreement handling, how meaningful-change judgments differ from relevance judgments in practice) — decided in Stage 3.
- Query set design (topic-level queries vs. specific questions) — decided in Stage 3.
- The shape of any "valuable discoveries per unit of attention" measure — **no formula exists**; experimentation required.
- Inspection-burden baselines (how many items a person currently inspects under RSS/search/manual monitoring) — unknown; may need a small human study.
- Baseline numbers of any kind. No measurements exist yet; any number in this repository before Stage 3 is a placeholder, not a result.
