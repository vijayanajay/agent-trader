# HARD RULES — Emergent Alpha

These 25 hard rules express the combined mindset of Kailash Nadh (pragmatism, minimalism, fast iteration) and Geoffrey Hinton (experimental rigor, measured discovery). Follow them strictly for v1.0 development and early experiments.

──────────────────────────── 3. HARD RULES ───────────────────────────────────

[H-1] Preserve observable behaviour: CLI flags, config shape, filenames, and emitted logs must remain stable across changes unless an explicit migration note accompanies the change.

[H-2] Touch only `src/`, `tests/`, and `docs/`. Leave infra and root files (CI, pyproject, lockfiles) unchanged unless a separate PR documents the reason.

[H-3] Prefer deletion over clever rewrites: remove unused code rather than wrap it in abstraction. Keep the codebase minimal.

[H-4] Zero new abstractions unless they eliminate ≥2 near-identical copies of logic (show before/after examples in the PR description).

[H-5] Every code suggestion or PR must show net LOC delta and a one-line rationale for the delta.

[H-6] Green tests are non-negotiable: no merge without passing unit tests and a short smoke run of the backtester on the sample CSV.

[H-7] 100% type hints. Code must pass `mypy --strict` with no implicit `Any` except in third-party stubs.

[H-8] No mutable global state. Load runtime config once (e.g., in `backtester.py` or `cli.py`) and pass dependencies explicitly; prefer pure functions.

[H-9] Any function or method > 40 logical lines is a smell; refactor or delete unless splitting adds net LOC and clarity.

[H-10] External dependencies limited to the chosen stack: `pandas`, `yfinance`, `crewai`, `openai` (or equivalent LLM client), `pytest`, and `rich`. Add nothing else without a written justification in the PR.

[H-11] Import graph must be acyclic. In-function imports allowed only to avoid heavy startup cost and must include a comment explaining why.

[H-12] Zero silent failures: no bare `except:`; always catch concrete exceptions, log via the shared Console/logger, and re-raise for CLI non-zero exit where appropriate.

[H-13] Network I/O is explicit and confined: all HTTP/LLM/data downloads live only in `src/adapters/` or `src/io/` modules; business logic must be importable and runnable offline.

[H-14] No `TODO`, `FIXME`, or commented-out code allowed in committed diffs — resolve or remove before merge.

[H-15] Max one public class per module; helper classes/functions must be private (prefix with `_`).

[H-16] Pure-function bias: functions with side-effects must carry a `# impure` comment immediately above the definition.

[H-17] Every module declares `__all__` to make its public API explicit; avoid `from x import *`.

[H-18] `print()` allowed only in `cli.py` or dedicated CLI output modules; use the shared `Console`/logger elsewhere.

[H-19] No `eval()`, `exec()`, or runtime monkey-patching.

[H-20] Config keys are `snake_case`. Normalize or reject other keys at load time with a clear error message.

[H-21] Core library must be offline-safe: behavior must not require network access; LLMs and downloads are opt-in adapters.

[H-22] LLM usage is experimental and auditable: every LLM call MUST log `{prompt_version, prompt_hash, model, temperature, token_count, response, timestamp}` to a local audit file.

[H-23] Deterministic baseline first: every LLM-enabled decision path must have a deterministic scorer fallback and an A/B test harness to measure marginal lift.

[H-24] Experiments are reproducible: every run writes a run-config JSON (inputs, scorer mode, prompt_version, seed) to `results/runs/` and seeds all RNGs for deterministic replay.

[H-25] MVP-first constraint: for v1.0 do not introduce CrewAI orchestration until the deterministic single-ticker pipeline (preprocessor → scorer → risk → backtester → analysis) is green and reproducible locally.

---

Notes:
- These rules are intentionally strict to keep experiments fast, auditable, and reproducible. Follow them literally for v1.0; we can relax or extend specific items later with documented justification.
- Suggested follow-up: add `docs/HARD_RULES.md` to the repo and optionally implement a pre-commit hook enforcing the `TODO`/`FIXME` ban and presence of LLM-audit logging for LLM calls.
