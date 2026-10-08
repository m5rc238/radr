# PROJECT.md — What Information Radar Is

**Status:** Stage 0 — project contract. No implementation exists yet.

## The broader problem

> **How can a person remain meaningfully informed about changes in an information environment without having to continuously monitor that environment themselves?**

People currently use many approaches to stay informed: doomscrolling and endless social feeds, algorithmic feeds, news sites, newsletters and digests, RSS readers, keyword alerts, search engines, manually monitoring sources, LLM summaries, RAG systems, and AI research agents.

Each reduces some costs while introducing others:

- feeds can create enormous information volume and encourage continuous attention
- algorithmic feeds may optimize for engagement rather than importance
- newsletters reduce volume but require someone else to decide what deserves attention
- RSS and alerts provide more control but can still create large amounts of noise
- search works well when you know what to look for, but is weaker when you don't know what you are missing
- LLMs and RAG can reduce reading and retrieval costs, but may miss important information or give users a false sense of coverage
- manual monitoring can produce high-quality results but is expensive in time and attention

Underneath these approaches sits **information overload combined with imperfect retrieval**: there is more potentially relevant material than a person can monitor manually, and retrieval is imperfect — systems miss things, rank badly, and mix primary evidence with commentary. LLMs make information easier to access without necessarily making access to the information that *matters* more reliable. An LLM can produce a fluent answer while the important document never entered the result set. Fluency and coverage are different properties, and this project treats them as such.

Information Radar investigates a different approach:

> **Periodically examine a defined information environment, detect potentially meaningful changes, and surface only the changes that are worth a person's attention.**

The goal is therefore **not to maximize information consumption**. The goal is to:

> **Minimize the attention required to remain meaningfully informed.**

## Research question

> **Can a retrieval and monitoring system reliably surface relevant and meaningful changes in a defined information environment while reducing the amount of information a person needs to inspect?**

This is an empirical question, not a claim. The project does not assert that the answer is yes; it builds the means to find out, and the hypothesis below is designed so the answer can be no.

The eventual system should let a person ask:

> What changed since my previous snapshot that is worth investigating?

### Open long-term question

> Can such a system surface information that a person would otherwise have missed?

This is preserved as the motivating, long-term research direction — **not** as the initial measurable claim. Establishing what a person would otherwise have encountered is difficult to do rigorously, so early evaluation rests on what is measurable now: retrieval judgments, change judgments, and inspection effort (`EVALUATION.md`).

## Core hypothesis

> A combination of conventional information retrieval methods, temporal analysis, source metadata, and selective LLM assistance may surface relevant and meaningful changes with less human inspection than either continuous manual monitoring or an LLM deciding from the beginning what information matters.

**This is a hypothesis, not an assumption.** It is an empirical claim to be tested, and the system must be designed so it can fail.

### How the hypothesis can fail

The hypothesis fails if, on a manually judged benchmark (`EVALUATION.md`):

- a simple lexical baseline (BM25) matches or beats the more complex pipelines on recall of relevant documents, showing that added machinery buys nothing; or
- LLM-assisted stages do not improve measured outcomes enough to justify their added cost, opacity, and verification burden; or
- configurations that do surface meaningful changes do so only by flooding the person with candidates to inspect, so attention cost does not actually fall; or
- no configuration reliably surfaces changes a person judges worth inspecting, over repeated snapshot cycles.

Failure is a valid and reportable result. Experiment records go in `docs/experiments/`.

## Concepts that must not be collapsed

```text
Access
Retrieval
Relevance
Novelty
Change
Importance
Coverage
Reliability
Human attention cost
```

These are distinct properties. For example:

- A document can be easy to access but irrelevant.
- A document can be highly relevant but not represent a meaningful change.
- A document can be novel but unimportant.
- A system can retrieve many relevant documents while still missing an important development.
- A system can produce excellent summaries while having poor retrieval coverage.

The project investigates these distinctions rather than hiding them. `EVALUATION.md` defines how each is measured — or why it is not yet measurable.

## Current approaches under investigation

The alternatives a person uses today to stay informed. The strengths and problems below are **design problems and hypotheses to investigate**, not established findings; the project has measured nothing yet.

| Approach | Strength | Problem |
| --- | --- | --- |
| Endless feeds / doomscrolling | Very low effort to encounter information | High volume, fragmented attention, weak intentionality |
| Algorithmic feeds | Convenient personalization | Ranking may optimize engagement rather than importance |
| Newsletters / digests | Reduces information volume | Someone else determines what deserves attention |
| RSS / alerts | User-controlled sources | Can still create noise and monitoring burden |
| Search | Good for known questions | Poorer when you don't know what you're missing |
| LLM summaries | Reduces reading effort | Can obscure retrieval limitations and uncertainty |
| RAG | Connects generation to retrieved sources | Retrieval can still miss important information |
| AI agents | Can iterate and search | More search does not necessarily mean better discovery |
| Manual monitoring | Potentially high-quality judgment | Expensive in time and attention |

Information Radar's proposed alternative sits outside this table: periodic, defined monitoring that surfaces only detected changes — an approach this project must demonstrate rather than assume.

## This is not a better feed

A feed asks:

> **What should I consume next?**

Information Radar asks:

> **What changed that may be worth my attention?**

A feed encourages continuous consumption. Information Radar should instead support **intermittent inspection**. The intended interaction is closer to:

```text
Information environment
        ↓
Periodic monitoring
        ↓
Detect changes
        ↓
Filter / rank
        ↓
Explain why something may matter
        ↓
Human inspection
```

The system should not assume that every retrieved item deserves to be read.

## "Meaningful change" is an unresolved concept

**Meaningfulness is an evaluation variable that must ultimately involve human judgment.** It must not be defined as whatever the algorithm says is important.

The following are not synonyms:

```text
Relevant
Novel
Changed
Important
Worth investigating
```

- A paper can be relevant without representing a meaningful change.
- A new development can be meaningful even if it is not obviously similar to previous queries.

The project should eventually investigate whether systems can identify these distinctions reliably. Until then, "meaningful change" is a placeholder for a judgment the system must earn from a person, not a quantity it already computes. This is recorded as an open evaluation problem in `EVALUATION.md`.

## Attention is a resource

Information Radar treats human attention as a constrained resource.

The objective is not:

> maximize information consumed

It is closer to:

> maximize useful discovery per unit of human attention

This is a **research direction**, not an established metric or a proven optimization target; no formula exists yet (`EVALUATION.md`).

The concern is framed in terms of attention cost, information volume, monitoring burden, distraction, opportunity cost, and cognitive load. The project claims only that these costs are borne by people who monitor information environments; it does not claim stronger effects than the evidence supports.

## Non-goals

This project is **not**, initially, any of the following:

- a general-purpose search engine
- a chatbot
- a replacement for reading primary sources
- a system that determines objective truth automatically
- an autonomous research agent
- a system that summarizes the entire internet
- a system that maximizes the amount of information consumed
- an addictive news feed or another engagement-optimized feed
- a system that hides retrieval uncertainty behind an LLM or behind polished summaries
- a showcase for impressive AI-generated summaries
- production infrastructure built prematurely
- a system that maximizes time spent in the application
- a system that maximizes the number of documents surfaced
- a system that encourages continuous information monitoring
- something optimized for scrolling
- something optimized for novelty for its own sake
- something built on the assumption that more information is better
- something that equates personalization with relevance
- something that assumes an LLM can determine importance automatically

The project explicitly resists the incentive structure of attention-maximizing information products. If a proposed feature serves one of these, it is out of scope until the project's stages say otherwise (`ROADMAP.md`).

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
