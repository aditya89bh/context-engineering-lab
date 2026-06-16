# Research questions

This is the working catalog of questions the lab exists to answer. Each question
is **testable** — it names what would be measured and what outcome would settle
it — and is **mapped to the [taxonomy](taxonomy.md)** by operation and question
family. The catalog is the source from which concrete experiments are drawn; it
is expected to grow and to be pruned as questions are answered.

Each entry lists: the question, its taxonomy cell, the form of a test, and the
observation that would count as an answer (including a clear negative result).

---

### RQ1 — Does any salience signal beat recency?

- **Taxonomy:** Salience × Comparison
- **Test:** On a task with known-relevant items, compare selection driven by each
  salience signal (recency, frequency, novelty, semantic relevance) against a
  recency-only baseline at matched budgets.
- **Answer:** A signal "wins" if it yields higher task success at equal budget
  with non-overlapping uncertainty intervals. Null result: no signal beats
  recency, implying recency is a sufficient proxy here.

### RQ2 — How much context can be removed before the task breaks?

- **Taxonomy:** Selection × Boundary
- **Test:** Sweep the budget from generous to severe under a fixed selection
  strategy and plot the budget-performance curve.
- **Answer:** Identify the budget at which task success drops below a pre-set
  threshold (the "cliff"), or show the curve degrades smoothly with no cliff.

### RQ3 — Does diversity-aware selection beat pure top-k under redundancy?

- **Taxonomy:** Selection × Comparison
- **Test:** Construct instances with controllable redundancy among relevant
  items; compare top-k by salience against a diversity-aware (MMR-style)
  selector at equal budgets.
- **Answer:** Diversity-aware selection wins if it raises selection recall and
  task success as redundancy increases. Null: no advantage, even at high
  redundancy.

### RQ4 — How aggressively can context be compressed before quality falls?

- **Taxonomy:** Compression × Boundary
- **Test:** Apply extractive and abstractive compression at increasing
  compression ratios; measure information retention against an uncompressed
  reference and downstream task success.
- **Answer:** Locate the compression ratio at which retention or task success
  begins to fall, yielding a compression-quality frontier per method.

### RQ5 — Is recency a causal proxy for relevance, or merely correlated?

- **Taxonomy:** Temporal × Mechanism
- **Test:** Decorrelate age from relevance in a synthetic generator (place
  relevant items uniformly across time); compare a temporal-decay strategy
  against a relevance-only strategy.
- **Answer:** If decay still helps once age and relevance are decorrelated,
  recency carries independent signal; if its advantage vanishes, recency was
  only a correlate of relevance.

### RQ6 — Which temporal decay shape best matches a known drift process?

- **Taxonomy:** Temporal × Comparison
- **Test:** Generate streams with a controlled drift/half-life; compare
  exponential vs. power-law decay (and no decay) by task success.
- **Answer:** The decay family whose curve tracks the generator's drift should
  dominate; a mismatch should underperform "no decay," quantifying the cost of
  the wrong temporal prior.

### RQ7 — Does active forgetting outperform keeping everything?

- **Taxonomy:** Forgetting × Comparison
- **Test:** Under a capacity-limited store, compare eviction policies (LRU,
  lowest-salience, decayed) against an unbounded "keep all" store on downstream
  task success and cost.
- **Answer:** Forgetting wins if a bounded store matches or beats "keep all" on
  quality at lower cost, demonstrating that discarding can help. Null: keeping
  everything is never worse.

### RQ8 — Does salience-proportional budget allocation beat uniform allocation?

- **Taxonomy:** Attention budget × Comparison
- **Test:** With multiple item sources of differing value, compare uniform,
  salience-proportional, and knapsack allocation of a fixed budget.
- **Answer:** An allocation wins if it raises task success at equal total budget;
  report whether the ranking is stable across budget sizes.

### RQ9 — How does selection degrade as distractors increase?

- **Taxonomy:** Robustness × Robustness
- **Test:** Hold relevant items fixed and increase the fraction of plausible
  distractors; measure task success and selection precision per strategy.
- **Answer:** Rank strategies by distractor sensitivity (the slope of quality
  loss vs. distractor fraction); identify which resist capture by surface
  similarity.

### RQ10 — How much store poisoning can a strategy tolerate?

- **Taxonomy:** Robustness × Robustness
- **Test:** Inject an increasing fraction of poisoned items into the store;
  measure downstream task success per selection/forgetting strategy.
- **Answer:** Report poisoning sensitivity and the poisoning fraction at which
  each strategy's quality crosses a failure threshold.

### RQ11 — Does compression help or hurt robustness to distractors?

- **Taxonomy:** Compression × Mechanism
- **Test:** Combine compression with distractor-laden inputs; compare distractor
  sensitivity with and without a compression stage.
- **Answer:** Determine whether compression launders distractors into summaries
  (worse robustness) or filters them out (better robustness).

### RQ12 — Do gains from a strategy survive distribution shift?

- **Taxonomy:** Robustness × Mechanism
- **Test:** Tune a strategy on one generator configuration and evaluate on a
  shifted one (different distractor style, length, or drift rate).
- **Answer:** Report shift tolerance (retained advantage post-shift). A strategy
  that only wins in-distribution is documented as overfit to its tuning regime.

---

## Maintenance

- A question is **retired** when an experiment answers it; the answer and the
  experiment that produced it are linked here.
- A question is **rejected** if it cannot be made testable or duplicates an
  existing entry (see the anti-redundancy rule in [taxonomy.md](taxonomy.md)).
- New questions must name their taxonomy cell and the observation that would
  settle them before they are added.
