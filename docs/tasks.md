# MVP Task List — Emergent Alpha

Each task is strictly scoped to a maximum of 2 hours. Tasks include: items to implement, tests to cover, acceptance criteria (AC), definition of done (DoD), and an approximate time estimate.

## Task 1 — Project skeleton & sample data (1.5h)

Items to implement:
- Create directory structure: `data/`, `data/ohlcv/`, `src/`, `src/analysis/`, `src/strategy/`, `src/utils/`, `results/`, `tests/`.
- Add a small sample CSV `data/ohlcv/RELIANCE.NS.sample.csv` with ~120 rows (or minimum 60 rows).
- Create a minimal `requirements.txt` listing pinned versions for `pandas`, `yfinance`.
- Initialize git repo (if not present) and add files.

Tests to cover:
- Verify the sample CSV exists and has Date, Open, High, Low, Close, Volume columns.

Acceptance Criteria (AC):
- Directory structure exists and sample CSV is present.
- `requirements.txt` exists.

Definition of Done (DoD):
- Files committed to git.

Time estimate: 1.5 hours

---

## Task 2 — Data preprocessor (1.5h)

Items to implement:
- `src/utils/data_preprocessor.py` with function `preprocess(csv_path, current_date, window=40)` that:
    - Loads CSV to pandas DataFrame.
    - Parses and sorts Date column.
    - Selects last `window` rows ending at `current_date`.
    - Computes 50- and 200-day SMA (use available history; if missing, return NaN).
    - Computes 14-day ATR (simple TR implementation).
    - Normalizes close and volume in window to 0-1 and returns dict: `{"window_df": DataFrame, "sma50": float, "sma200": float, "atr14": float, "current_price": float}`.

Tests to cover:
- `tests/test_preprocessor.py`:
    - Happy path using sample CSV and a valid `current_date`.
    - Edge case: `current_date` earlier than available rows (function raises ValueError).

Acceptance Criteria (AC):
- `preprocess` returns expected keys and types.
- Tests pass locally.

Definition of Done (DoD):
- `src/utils/data_preprocessor.py` and tests are committed.

Time estimate: 1.5 hours

---

## Task 3 — Risk manager (0.5h)

Items to implement:
- `src/utils/risk_manager.py` with function `compute_risk(current_price, atr)` returning `{"stop_loss": float, "take_profit": float}` using stop_loss = price - 2*ATR, take_profit = price + 4*ATR.

Tests to cover:
- `tests/test_risk.py` with:
    - Normal ATR value.
    - ATR == 0 returns stop_loss == take_profit == current_price (documented behavior).

Acceptance Criteria (AC):
- Function returns correct numbers and tests pass.

Definition of Done (DoD):
- File and tests committed.

Time estimate: 0.5 hours

---

## Task 4 — Deterministic pattern scorer (1.5h)

Items to implement:
- `src/strategy/pattern_scorer.py` with `score(window_df)` implementing deterministic scoring:
    - Components: recent 10-day return (scaled), volume surge (current vs median), position vs sma50 (above => bonus).
    - Combine into score 0-10 and return `{"pattern_strength_score": float, "pattern_description": str}`.

Tests to cover:
- `tests/test_scorer.py`:
    - Synthetic bullish window where score is high.
    - Flat window where score is low.

Acceptance Criteria (AC):
- `score` returns float between 0 and 10 and a description string.
- Tests pass.

Definition of Done (DoD):
- File and tests committed.

Time estimate: 1.5 hours

---

## Task 5 — Backtester (2.0h)

Items to implement:
- `backtester.py` (project root) with CLI arg `--ticker <csv-path>`.
- Loop over valid `current_date` in sample series (skip first 60 rows):
    - Call `preprocess` → `score`.
    - If `score >= 7.0`, call `compute_risk` and log trade with entry price, stop_loss, take_profit.
    - Calculate 20-day forward return and whether stop_loss/take_profit hit (check min/max of next 20 closes).
    - Append trade to results list and write `results/results.csv`.

Tests to cover:
- `tests/test_backtester.py`:
    - Run backtester against sample CSV and confirm `results/results.csv` is created.

Acceptance Criteria (AC):
- `python backtester.py --ticker data/ohlcv/RELIANCE.NS.sample.csv` runs and produces `results/results.csv` with expected columns.

Definition of Done (DoD):
- `backtester.py` and test committed; sample run produces results.

Time estimate: 2.0 hours

---

## Task 6 — Analysis script (0.5h)

Items to implement:
- `src/analysis/analyze_results.py` that reads `results/results.csv` and prints: total trades, win rate, profit factor.

Tests to cover:
- Manual verification.

Acceptance Criteria (AC):
- Script prints metrics when run.

Definition of Done (DoD):
- Script committed.

Time estimate: 0.5 hours

---

## Task 7 — README & run instructions (0.5h)

Items to implement:
- `README.md` with short steps:
    - Create venv, pip install -r requirements.txt.
    - Run backtester with sample CSV.
    - Run analyze script.

Tests to cover:
- Manual follow-the-guide verification.

Acceptance Criteria (AC):
- README allows another developer to run the MVP.

Definition of Done (DoD):
- README committed.

Time estimate: 0.5 hours

---

## Task 8 — Quick unit test run & commit (0.5h)

Items to implement:
- Run `pytest -q` locally and fix trivial failures (<=10m). File issues for anything larger.

Acceptance Criteria (AC):
- All tests pass locally or brief issue filed for remaining items.

Definition of Done (DoD):
- Test results committed or issue created.

Time estimate: 0.5 hours

---

Completion note

This replaces the agent-heavy plan with a tight, verifiable MVP where each piece is small and testable. After these tasks, we'll have a runnable deterministic baseline that is easy to compare with LLM-augmented experiments in the next phase.