# Non-goals

Defining what this repository is *not* keeps its scope honest and protects the
research from drifting into adjacent product categories. The [thesis](thesis.md)
states the positive aim; this document states the boundaries.

Each non-goal explains what we avoid and why, and points to what we study
instead.

## This is not a RAG framework

We are not building a retrieval-augmented-generation library, pipeline, or
product. RAG is *one application* of context engineering, not its subject. We
study the underlying decisions — salience, selection, compression, forgetting —
as strategies that can be compared in isolation. Findings may inform a RAG
system, but shipping one is out of scope.

## This is not a vector database or an ANN benchmark

We do not implement, optimize, or benchmark vector stores or approximate
nearest-neighbor indexes. Retrieval here is treated as a candidate-generation
step whose quality we can control synthetically; index throughput, recall@k of
ANN libraries, and storage engines are explicitly not what we measure.

## This is not a prompt-engineering cookbook

We are not collecting prompt templates, wording tricks, or model-specific
incantations. Prompt phrasing is a confound we control for, not a variable we
celebrate. Our results are about *what information* belongs in context, not about
*how to phrase* instructions to a particular model.

## This is not a long-context leaderboard

We do not chase a single headline number on a public long-context benchmark, and
we do not rank models. We care about *why* a context strategy succeeds or fails
under specified conditions and budgets. A leaderboard rewards overfitting to one
number; we report budget-performance curves, costs, and robustness instead.

## This is not an agent framework

We are not building an orchestration layer for tools, planning, or multi-agent
systems. Agents are a setting where context decisions matter, but tool routing,
control flow, and agent ergonomics are out of scope. When an experiment needs a
"consumer," it uses the simplest one that can answer the question.

## This is not an LLM wrapper or SDK

We are not providing a client, gateway, caching layer, or convenience wrapper
over model providers. Where a model is needed as a consumer, it is an
interchangeable component behind a minimal interface, not the product. The core
stays dependency-light and model-agnostic (see
[architecture.md](architecture.md)).

## What we study instead

If a proposed change moves the repository toward any of the above, it belongs
elsewhere. The questions we *do* pursue are catalogued in
[research-questions.md](research-questions.md) and organized by
[taxonomy.md](taxonomy.md): how intelligent systems decide what context to
retain, compress, retrieve, prioritize, and forget.
