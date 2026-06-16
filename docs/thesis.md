# Repository thesis

## The problem

Every system that reasons over information operates under a budget. A language
model has a finite context window. A robot has finite memory and compute. A
human analyst has finite attention. None of them can hold everything, so all of
them must constantly answer the same question:

> Of everything available, what deserves to be here *right now*?

This question is usually answered implicitly, buried inside retrieval heuristics,
truncation rules, summarization prompts, and cache-eviction policies. When it
fails, the failure is diffuse and hard to attribute: the model "hallucinated,"
the agent "lost track," the pipeline "got slow." We rarely measure the decision
itself.

**context-engineering-lab exists to make that decision explicit, measurable, and
contestable.**

## The claim

We treat *context engineering* as a discipline with its own questions,
trade-offs, and failure modes, distinct from model architecture or prompt
wording. Concretely, we claim:

1. **Context selection is an optimization problem**, not a formatting concern.
   It has an objective (task performance), a constraint (a budget), and a set of
   strategies that can be compared head-to-head.
2. **The strategies generalize across substrates.** A salience rule that helps a
   language agent should be expressible in a way that also applies to a memory
   store or a retrieval cache. We test ideas at the level of strategies, not
   product integrations.
3. **Forgetting and compression are features, not damage.** Discarding
   information can improve performance by reducing distraction and cost. We want
   to find where that boundary sits.

## What counts as a result

A result in this lab is not a working demo. It is a defensible answer to a
question, supported by evidence that another person can reproduce. A result
includes:

- a **question** stated before the experiment is run;
- a **strategy** (or comparison of strategies) under test;
- a **benchmark** and **metrics** chosen for the question, not for the outcome;
- **measurements** with seeds, configuration, and environment recorded;
- an **interpretation** that states what we now believe and how confident we are,
  including negative results and surprises.

If an experiment cannot produce this, it does not belong here yet.

## What this repository is not

- It is not a retrieval-augmented-generation framework. RAG is one application of
  context engineering; it is not the subject.
- It is not a vector database, an agent framework, or a prompt library.
- It is not a leaderboard. We care about *why* a strategy wins or loses under
  specific conditions, not about topping a single number.

## Operating principles

- **Questions before code.** No experiment is written until its question and
  success criteria are written down.
- **Reproducibility is non-negotiable.** Every result is seeded, configured, and
  regenerable. See [definition-of-done.md](definition-of-done.md).
- **Negative results are first-class.** "This did not help, and here is why" is a
  valuable contribution.
- **Small, honest experiments over large, impressive ones.** A clean comparison
  on a synthetic task beats an ambiguous one on a flashy task.

## Audience

This repository is written for research engineers and applied researchers who
build context-bound systems and want principled guidance rather than folklore.
Familiarity with Python and basic experimental method is assumed; deep ML
expertise is not required to read the results.
