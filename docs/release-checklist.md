# Release checklist

A repeatable checklist for cutting a tagged release of `context-engineering-lab`.
Phase 11 prepares the repository to be release-ready; this checklist is the
procedure to follow when a release is actually cut. **No tag or release is created
as part of Phase 11.**

## 1. Pre-flight: working tree

- [ ] On `main`, up to date with the remote, clean working tree
      (`git status` shows nothing to commit).
- [ ] No `artifacts/`, `dist/`, or other generated files staged (they are
      git-ignored; confirm `git status --ignored` looks right).

## 2. Validation gate

All four must pass from a clean checkout with `pip install -e ".[dev]"`:

- [ ] `ruff check .`
- [ ] `mypy`
- [ ] `pytest`
- [ ] `python -m build`

## 3. Determinism gate

- [ ] `pytest -k reproducible` passes.
- [ ] `pytest tests/test_reproducibility_example.py` passes (the checked-in
      example artifact still regenerates byte-for-byte).
- [ ] `pytest tests/test_no_external_api.py` passes (no network / LLM creep).
- [ ] Re-running a phase produces identical reports, e.g.
      `context-lab run-phase2 --output /tmp/a && context-lab run-phase2 --output /tmp/b && diff /tmp/a/summary.md /tmp/b/summary.md`.

## 4. Documentation consistency

- [ ] `README.md` status section reflects the released phase.
- [ ] `CHANGELOG.md` has a dated entry for the version being released.
- [ ] `docs/roadmap.md` marks the released phase complete.
- [ ] No broken intra-repo Markdown links (the audit script in
      [docs/repository-tour.md](repository-tour.md) or a quick link check).
- [ ] Benchmark/strategy counts in `README.md` and
      [docs/project-summary.md](project-summary.md) match `context-lab list`.
- [ ] `RESULTS.md` numbers were regenerated against the released code.

## 5. Version and metadata

- [ ] Bump `version` in `pyproject.toml` and `src/context_engineering_lab/__init__.py`
      (`__version__`) to the same value (currently both `0.0.0`).
- [ ] Update `version` and `date-released` in `CITATION.cff`.
- [ ] Confirm `authors`, `license`, and URLs in `pyproject.toml` and
      `CITATION.cff` agree.

## 6. Build artifacts

- [ ] `python -m build` produces an sdist and a wheel under `dist/`.
- [ ] `python -m pip install dist/*.whl` into a fresh venv installs and
      `context-lab list` runs.
- [ ] (Optional) `twine check dist/*` passes if publishing to an index.

## 7. Tag and release

- [ ] Create an annotated tag matching the version (e.g. `git tag -a v1.0.0`).
- [ ] Push the tag.
- [ ] Create the release with notes drawn from `CHANGELOG.md`, `RESULTS.md`, and
      `FINDINGS.md`.

## 8. Post-release

- [ ] Bump to the next development version if appropriate.
- [ ] Open a fresh `CHANGELOG.md` "Unreleased" section.

> No-AI-attribution reminder: commits and release notes carry no AI authorship
> trailers, consistent with the rest of the project history.
