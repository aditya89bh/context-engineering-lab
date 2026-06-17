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
- **Phase 2 status:** *begun.* On `easy-selection`, keyword overlap (a crude
  salience proxy) reaches the oracle ceiling and clearly beats recency at tight
  budgets; on `high-distractor-selection` that advantage disappears when
  distractors share every signal term. So: salience can beat recency, but only
  when content actually separates targets from distractors. Benchmark-specific.

### RQ2 — How much context can be removed before the task breaks?

- **Taxonomy:** Selection × Boundary
- **Test:** Sweep the budget from generous to severe under a fixed selection
  strategy and plot the budget-performance curve.
- **Answer:** Identify the budget at which task success drops below a pre-set
  threshold (the "cliff"), or show the curve degrades smoothly with no cliff.
- **Phase 2 status:** *begun.* The `selection-budget-sweep` experiment plots
  answer support against an item-budget ladder on `high-distractor-selection`.
  For the non-oracle strategies the curve rises smoothly with the budget (no
  sharp cliff on this benchmark), while the oracle stays flat at the ceiling.

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
- **Phase 3 status:** *begun (deterministic compression only).* On
  `compression-fact-preservation`, extractive compressors hold required facts
  down to small token budgets while position-blind truncation drops them once the
  kept end no longer covers the facts. The `compression-budget-sweep` experiment
  traces retention against budget; the oracle holds full retention at a low
  compression ratio. No abstractive/LLM compression is included.

### RQ5 — Is recency a causal proxy for relevance, or merely correlated?

- **Taxonomy:** Temporal × Mechanism
- **Test:** Decorrelate age from relevance in a synthetic generator (place
  relevant items uniformly across time); compare a temporal-decay strategy
  against a relevance-only strategy.
- **Answer:** If decay still helps once age and relevance are decorrelated,
  recency carries independent signal; if its advantage vanishes, recency was
  only a correlate of relevance.
- **Phase 4 status:** *begun.* On `temporal-context-relevance`, varying
  `relevant_age` decorrelates age from relevance: when the signal is recent,
  recency tracks the oracle; when it is old (`old-signal`), recency fails and
  `oldest-first` recovers the signal. So recency is a heuristic about *where
  relevance tends to be*, not relevance itself — it carries no independent signal
  once the generator moves relevance off the recent end. Benchmark-specific.

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
- **Phase 5 status:** *begun.* On `retention-utility-preservation`, the
  `retain-all` reference always overruns the memory budget and keeps every harmful
  item, so under a tight budget selective forgetting policies reach higher
  retention precision and forgetting efficiency than keeping everything. This is a
  one-shot retention decision on a synthetic benchmark, not an eviction-over-time
  store, and the win depends on the budget being below the memory size.

### RQ8 — Does salience-proportional budget allocation beat uniform allocation?

- **Taxonomy:** Attention budget × Comparison
- **Test:** With multiple item sources of differing value, compare uniform,
  salience-proportional, and knapsack allocation of a fixed budget.
- **Answer:** An allocation wins if it raises task success at equal total budget;
  report whether the ranking is stable across budget sizes.
- **Phase 6 status:** *begun.* On `attention-source-allocation`, salience-
  proportional allocation beats uniform when signal is concentrated, but is fooled
  by a `noisy-dominant-source` whose distractors carry inflated salience; a
  capacity-aware quality-led `adaptive` allocator avoids that trap. No single
  deployable allocator wins across all three presets, and uniform is hard to beat
  when sources are balanced. Synthetic and benchmark-specific.

### RQ9 — How does selection degrade as distractors increase?

- **Taxonomy:** Robustness × Robustness
- **Test:** Hold relevant items fixed and increase the fraction of plausible
  distractors; measure task success and selection precision per strategy.
- **Answer:** Rank strategies by distractor sensitivity (the slope of quality
  loss vs. distractor fraction); identify which resist capture by surface
  similarity.
- **Phase 2 status:** *begun.* Comparing `easy-selection` (few, dissimilar
  distractors) with `high-distractor-selection` (many, look-alike distractors)
  shows precision and recall for every non-oracle strategy collapsing toward
  chance under heavy, content-similar distractor load. A first, coarse reading
  of distractor sensitivity on synthetic data.

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
- **Phase 3 status:** *begun.* On `dense-distractor-compression`, deterministic
  truncation and keyword-preserving compression retain a sizeable share of
  distractor facts (laundering them into the output), whereas the oracle drops
  them entirely. A first, extractive-only reading; abstractive compression is out
  of scope for Phase 3.

### RQ12 — Do gains from a strategy survive distribution shift?

- **Taxonomy:** Robustness × Mechanism
- **Test:** Tune a strategy on one generator configuration and evaluate on a
  shifted one (different distractor style, length, or drift rate).
- **Answer:** Report shift tolerance (retained advantage post-shift). A strategy
  that only wins in-distribution is documented as overfit to its tuning regime.

### RQ13 — Does target position bias position-blind baselines?

- **Taxonomy:** Robustness × Mechanism
- **Test:** Hold the target and distractors fixed but vary where the target sits
  among the candidates (early / middle / late / random); measure task success
  per strategy, separating order-only baselines from content-based ones.
- **Answer:** A baseline is *position-biased* if its success depends on target
  placement rather than relevance. Report which strategies succeed or fail purely
  as a function of position.
- **Phase 2 status:** *begun.* On `position-biased-selection` (target always
  late) `first-n` fails at small budgets while `last-n` and `recency` succeed —
  by position, not by reading content. This confirms order-only baselines can be
  right for the wrong reason and must be read as position probes, not relevance
  selectors.

### RQ14 — Do extractive compressors preserve facts better than truncation?

- **Taxonomy:** Compression × Comparison
- **Test:** On documents with known facts, compare position-based truncation
  (head/tail) against extractive compressors (query-aware keyword preservation,
  sentence-boundary) at matched token budgets; measure information retention and
  answer support after compression.
- **Answer:** An extractive compressor "wins" if it retains more required facts at
  equal budget, especially when the facts are not at the kept end. Null result:
  truncation matches extraction once position is controlled.
- **Phase 3 status:** *begun.* On `compression-fact-preservation`,
  `keyword-preserving` holds the required facts across budgets while head/tail
  truncation only succeed when the facts sit at the kept end; the advantage is
  clearest on `late-signal-compression`. Deterministic, extractive only.

### RQ15 — When do fixed windows fail, and can age-aware weighting do better?

- **Taxonomy:** Temporal × Comparison
- **Test:** On a timeline with controllable signal age and temporal drift, compare
  a fixed window (anchored at a fixed region), a sliding window (anchored at
  "now"), pure recency, and an age-aware weighting of an observable salience
  signal; measure answer support and the temporal age gap as signal age and drift
  vary.
- **Answer:** A window "fails" when the relevant signal lies outside it; report
  the regimes where each window succeeds. Age-aware weighting "wins" if it keeps
  salient-but-not-newest items recency drops — and is shown to be *fooled* when
  drift gives recent decoys high salience.
- **Phase 4 status:** *begun.* On `temporal-context-relevance`, the sliding window
  succeeds only when the signal is recent and the fixed leading window only when
  it is old; `age-weighted` beats recency when salience tags the relevant items,
  but `drift-heavy` pulls it toward recent decoys so no deployable strategy
  matches the oracle. Deterministic, synthetic, and benchmark-specific.

### RQ16 — Which signal should a forgetting policy trust to keep useful and drop harm?

- **Taxonomy:** Forgetting × Comparison
- **Test:** On a memory where useful, stale, harmful, and neutral items carry
  deliberately misaligned observable signals (harmful items recur often and sit
  recently; useful items are spread across time), compare policies that forget by
  recency, frequency, salience, and a blend of the three; measure useful and
  harmful retention rates and forgetting efficiency as noise and harmful density
  vary.
- **Answer:** A signal "wins" if it keeps useful items while dropping harm; report
  the regimes where each fails. Recency and frequency are expected to retain harm
  (it is recent and frequent); salience tracks utility when signals are
  well-separated and degrades under overlap; no deployable policy should match the
  oracle, which reads ground-truth utility.
- **Phase 5 status:** *begun.* On `retention-utility-preservation`, recency and
  frequency retain harmful items as expected; with low noise a salience policy
  approaches the oracle's forgetting efficiency, but on the high-noise
  `harmful-memory` preset every deployable policy falls well short of it. Whether
  the hybrid blend beats the best single signal varies by preset and is measured,
  not assumed. Deterministic, synthetic, and benchmark-specific.

### RQ17 — When does uniform attention allocation fail, and what should replace it?

- **Taxonomy:** Attention budget × Comparison
- **Test:** Across sources that vary in size, quality, and signal concentration —
  including a large source whose salience overstates its signal — compare uniform,
  size-proportional, salience-proportional, capacity-aware quality-led, and
  winner-take-most splits of a fixed budget; measure signal capture, wasted
  attention, and source coverage as concentration and quality imbalance vary.
- **Answer:** Uniform "fails" when sources differ in value: report the regimes
  where it wastes budget on weak sources. A replacement "wins" if it raises signal
  capture at equal budget without being baited by the noisy source; no deployable
  allocator should match the oracle, which reads ground-truth signal counts.
- **Phase 6 status:** *begun.* On `attention-source-allocation`, uniform is
  competitive only on `balanced-sources`; on `concentrated-signal` it wastes
  budget on near-empty sources while winner-take-most and the quality-led adaptive
  allocator approach the oracle; on `noisy-dominant-source`, size- and
  salience-based splits pour budget into the trap while the adaptive allocator
  resists it. Deterministic, synthetic, and benchmark-specific.

### RQ18 — How do context primitives interact when composed into a pipeline?

- **Taxonomy:** Composition × Interaction
- **Test:** On cases that exercise several primitives at once (relevant, harmful,
  stale, and distractor items spread across sources and a timeline), run each
  primitive alone and chained pipelines (e.g. `retention->selection`,
  `temporal->retention`, `retention->attention`); contrast each pipeline with the
  baseline standing in for its final stage using interaction gain, degradation
  rate, and compensation effect, plus harmful retention and recall.
- **Answer:** A composition "helps" if it beats that baseline on a metric (e.g. a
  forgetting stage cuts harmful retention a selector keeps) and "hurts" if it
  degrades one (e.g. a recency window drops spread-out relevant items a selector
  would keep). Report which combinations dominate under which budgets; no
  deployable pipeline should match the oracle ceiling.
- **Phase 7 status:** *begun.* On `interaction-context-pipeline`, a
  frequency-aware retention stage before selection or attention cuts
  `harmful_retention_rate` relative to those primitives alone (which keep traps
  that carry the query terms), while a recency window before selection lowers
  `selection_recall` by discarding old-but-relevant items. Which composition
  dominates depends on the preset and budget and is measured, not assumed.
  Results are about specific compositions, not context systems in general.

### RQ19 — Do context strategies still help when the context resembles real working information?

- **Taxonomy:** Selection × Realism
- **Test:** On deterministic, fully synthetic benchmarks shaped like real context
  sources (email threads, meeting notes, support tickets, document revisions,
  memory logs), where the answer depends on an older email, a current decision,
  a working fix, or a current revision while superseded, conflicting, stale, and
  harmful records add realistic noise, run a curated lineup of *existing*
  strategies and compositions and an oracle ceiling. Score answer support and
  recall alongside `current_truth_support`, `superseded_fact_retention`,
  `conflict_selection_rate`, harmful retention, and stale selection.
- **Answer:** A strategy "remains useful" on a scenario if it recovers the answer
  while keeping conflicting/superseded/harmful selection low relative to a
  content-only keyword baseline. Report which strategy behaves sensibly on which
  scenario; behaviour is expected to differ by family (e.g. recency is right when
  the truth is the newest revision but wrong when it is an old email).
- **Phase 8 status:** *begun.* On these naturalistic scenarios, an importance-aware
  `salience-retention` recovers the answer while cutting `conflict_selection_rate`
  and `superseded_fact_retention` relative to keyword overlap on the email,
  meeting, and revision families, and cuts `harmful_retention_rate` on the support
  and memory-log families; a recency window is the right signal on the revision
  family (current = newest) but discards the old relevant email. Results are
  specific to these synthetic scenarios, not claims about real workplace context.

### RQ20 — Taken together, which strategies dominate, and where do they fail?

- **Taxonomy:** Comparison × Synthesis
- **Test:** Aggregate the Phase 2-8 result artifacts into one cell per
  `(benchmark, strategy, metric, budget)`, pick a higher-is-better primary metric
  per benchmark, and compute strategy profiles, pairwise dominance over shared
  cells (wins/losses/ties and the non-dominated frontier), oracle gaps and an
  oracle-normalized score, mechanical failure flags (budget collapse, wide oracle
  gap, budget-driven degradation), and stability (seed variance, budget
  sensitivity, ranking volatility). No new strategy, benchmark, or metric.
- **Answer:** A strategy "dominates" another only on the cells they share; a
  strategy is "close to its oracle" when its normalized score nears 1.0; a
  strategy "fails" a benchmark when a flag fires. Report the frontier and the
  flags rather than a single winner, since primary metrics differ by benchmark.
- **Phase 9 status:** *begun.* Synthesis confirms the per-phase picture without
  overturning it: oracle ceilings top the dominance and normalized tables;
  importance-aware strategies (`salience-retention`, `retention->selection`) sit
  closest to their oracles; budget-ignoring references can exceed a budgeted
  oracle on one metric (negative oracle distance); and disjoint-benchmark
  strategies never compare, so the frontier is wide. Numbers regenerate via
  `context-lab run-phase9`. Specific to these synthetic artifacts, not general
  claims.

### RQ21 — How robust are strategies when a benchmark's assumptions are stressed?

- **Taxonomy:** Robustness × Boundary
- **Test:** Perturb the Phase 8 naturalistic benchmarks without touching ground
  truth — inject distractors, inject contradictions, amplify stale/superseded
  items, and corrupt the observable `source_quality` and `salience` signals toward
  misleading values — then re-run a curated lineup of *existing* strategies and an
  oracle ceiling on baseline vs perturbed. Measure `degradation` (oriented
  `baseline - perturbed`) and `robustness_score` (fraction retained) per
  `(strategy, benchmark, perturbation, metric)`, plus whether the oracle gap
  widens. No new primitive, strategy, or benchmark family.
- **Answer:** A strategy "degrades gracefully" on a stressor when its degradation
  is small and its robustness near 1.0; it is "sensitive" when a specific
  perturbation drives a large degradation on a specific metric. Report the
  strategy, benchmark, perturbation, and metric for each claim — never a blanket
  label.
- **Phase 10 status:** *begun.* Under `contradiction-injection` on
  `revision-current-truth`, `temporal->selection` shows the largest
  `conflict_selection_rate` degradation; under `salience-corruption` on
  `support-stale-fix`, `salience-retention` loses nearly all `answer_support`
  (robustness ~0.0) while `attention->selection` is unaffected on
  `stale_selection_rate`; under `distractor-injection` on `email-old-signal`,
  `recency` degrades most on `answer_support`; and the oracle gap widens, rather
  than closes, under every stressor. Numbers regenerate via
  `context-lab run-phase10`. Specific to these synthetic stressors, not general
  claims.

---

## Maintenance

- A question is **retired** when an experiment answers it; the answer and the
  experiment that produced it are linked here.
- A question is **rejected** if it cannot be made testable or duplicates an
  existing entry (see the anti-redundancy rule in [taxonomy.md](taxonomy.md)).
- New questions must name their taxonomy cell and the observation that would
  settle them before they are added.
