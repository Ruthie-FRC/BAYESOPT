# Contributing — SideKick / bayesopt (short)

Thanks for contributing! This is an open source project made by one
high schooler, so I apologize if code reviews, updates, or answering questions takes time.

Please try to make changes clear, small, and above all, test your 
changes.

Quick workflow
1. Fork, clone, create a branch (e.g. feat/xxx or fix/yyy).
2. Make focused commits, run tests/linters locally.
3. Push branch and open a PR against main (link issue if present).
4. Address reviews; rebase/squash if requested.

Etiquette (short)
- Be respectful and constructive.
- Ask questions instead of assuming.
- Explain why a change is needed and how you validated it.

Commit message (required)
Format:
<type>(scope): short imperative summary

Body:
- State value change clearly: "from X → Y on Z" and why.
- Add testing/compatibility notes as needed.

Types: feat, fix, docs, style, refactor, perf, test, chore

Example:
- feat(optimizer): change default learning_rate from 0.01 → 0.001
  Body: "Changed Adam default LR 0.01 → 0.001 to improve noisy-data stability. Added unit test."

## Examples

Good commit + PR example (clear, concrete)

- Commit title:
  feat(optimizer): reduce default Adam learning_rate 0.01 → 0.001

- Commit body:
  - What changed value-wise: changed Adam (adaptive motion estimate) default learning_rate in bayesopt/optimizer.py from 0.01 → 0.001.
  - Why: reduced overshooting and improved stability on noisy datasets (see issue #42).
  - Tests: updated tests/test_optimizer.py::test_default_lr to assert new default.
  - Files changed: bayesopt/optimizer.py, tests/test_optimizer.py, docs/usage.md (if applicable).

- PR description (short & required):
  - Summary: Reduced Adam default LR 0.01 → 0.001 to improve noisy-data stability.
  - Details:
    - What changed: Adam.default_lr 0.01 → 0.001 in bayesopt/optimizer.py
    - Why: training on noisy datasets showed unstable convergence; lowering LR reduced oscillation.
    - How validated: ran unit tests and a small example run below.
  - Validation steps (maintainers/reviewers):
    1. Run unit test: pytest -k test_default_lr
    2. Run a quick example: python examples/adam_demo.py --max-evals 10
    3. Confirm no regression in CI and review updated test assertions.
  - Related: Closes #42

Bad commit/PR (what to avoid)
- Title: "fix stuff"
- Body: no before/after values, no tests, no explanation.

PR checklist
- Branch uses naming convention.
- Tests added/updated where applicable.
- Linter run.
- Docs updated for public API changes.
- PR description states: what changed, from what → to what, why, and how to validate.

Issues
Provide summary, steps to reproduce, environment, and logs or minimal examples.

That's it — short, clear, and testable contributions are preferred.
