# Definition of done

This is the bar every contribution must clear. It applies to two kinds of work:
**engineering** changes (code, infrastructure) and **experiments**. An item is
not "done" because it runs; it is done when it meets the criteria below.

## For all changes

- [ ] The change has a clear, single purpose, reflected in its commit(s).
- [ ] `ruff check .` passes with no warnings.
- [ ] `mypy` passes under strict configuration.
- [ ] `pytest` passes, and new behavior is covered by tests.
- [ ] `python -m build` succeeds.
- [ ] Public functions and modules have docstrings; non-obvious intent is
      explained, obvious mechanics are not.
- [ ] No secrets, credentials, or large binary artifacts are committed.
- [ ] No AI/assistant attribution anywhere in code, docs, or history.

## For an experiment

An experiment is done when a careful, skeptical reader could reproduce it and
reach the same conclusion. Concretely:

### Before running

- [ ] The **question** is written down and is answerable.
- [ ] The **hypothesis** (or competing hypotheses) is stated.
- [ ] The **primary comparison** and **metrics** are chosen *before* seeing
      results, to avoid post-hoc cherry-picking.
- [ ] At least one **baseline** is included.

### Methodology

- [ ] Randomness derives from a single root seed (see
      [ADR-0003](adr/0003-deterministic-seeding.md)).
- [ ] The experiment runs across **multiple seeds**, not one.
- [ ] Where a budget exists, performance is measured **across a range**, not at a
      single point.
- [ ] **Cost** is reported alongside **quality**.
- [ ] The benchmark version is recorded.

### Results and interpretation

- [ ] Results report central tendency **and** spread.
- [ ] The **interpretation** states what we now believe and the confidence in it.
- [ ] **Threats to validity** are named (construct validity, shortcuts, leakage).
- [ ] **Negative or null results** are reported honestly, not buried.
- [ ] The result is **regenerable** from the committed definition and recorded
      seed.

## Reviewer's checklist

A reviewer should be able to answer "yes" to all of these before approving:

- Could I rerun this and get the same numbers?
- Is the comparison fair (matched budgets, shared benchmark, sensible baseline)?
- Could a degenerate strategy score well here without the capability claimed?
- Does the interpretation overreach beyond what the evidence supports?
- Is anything reported in isolation that should be reported with its cost or
  spread?

If any answer is "no," the work is not done.
