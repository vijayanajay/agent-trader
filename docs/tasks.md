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
 
Status: Completed

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
 
Status: Completed

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
 
Status: Completed

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
 
Status: Completed

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
 
Status: Completed

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
 
Status: Completed

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
 
Status: Completed

---

## Task 8 — Quick unit test run & commit (0.5h)

Items to implement:
- Run `pytest -q` locally and fix trivial failures (<=10m). File issues for anything larger.

Acceptance Criteria (AC):
- All tests pass locally or brief issue filed for remaining items.

Definition of Done (DoD):
- Test results committed or issue created.

Time estimate: 0.5 hours
 
Status: Completed

## Task 9 — Daily run log: Scorer analysis & tuning (1.5h)

Items to implement:
- Update scorer output (`src/pattern_scorer.py`):
    - Make the `score(...)` function return intermediate component scores in addition to the final score and description.
    - New return shape (example):

```python
return {
        "final_score": total_score,
        "return_score": return_score,
        "volume_score": volume_score,
        "sma_score": sma_score,
        "description": desc,
}
```

    - Rename `pattern_strength_score` → `final_score` and `pattern_description` → `description` (or keep description key consistent).

- Collect per-day scorer data in the backtester (`backtester.py`):
    - In `run_backtest(...)` create `daily_logs: List[Dict] = []` before the main loop.
    - Inside the loop, after calling `score(...)`, build a `log_entry` with date, price, indicators (e.g., `atr14`, `sma50`), and the scorer component fields, then `daily_logs.append(log_entry)`.
    - Use the new `final_score` key for decision logic (replace uses of `pattern_strength_score`).

- Save the detailed run log separately:
    - After `run_backtest` / in `main()`, if `daily_logs` is non-empty, convert to a pandas DataFrame and write to `results/runs/<ticker_name>.run_log.csv`.
    - Ensure the directory exists (`os.makedirs(..., exist_ok=True)`).
    - Add required imports: `import os` and `from pathlib import Path`.

Tests to cover:
- Add/extend a unit/integration test that runs the backtester on the sample CSV and verifies that `results/runs/<ticker>.run_log.csv` is created and contains expected columns: `date, price, atr14, sma50, final_score, return_score, volume_score, sma_score`.
- Optional: assert that existing `results/results.csv` is still produced with the original trade columns and content shape.

Acceptance Criteria (AC):
- `src/pattern_scorer.py` returns intermediate component scores and `final_score` key.
- `backtester.py` collects a per-day `daily_logs` list and writes `results/runs/<ticker>.run_log.csv` containing the required columns.
- Existing trade result output (`results/results.csv`) remains unchanged in format and content (aside from using `final_score` for logging `pattern_score`).

Definition of Done (DoD):
- Changes to `src/pattern_scorer.py` and `backtester.py` implemented and committed.
- One test added/updated verifying the run log file and its columns.
- Example run (using sample CSV) produces `results/runs/RELIANCE.NS.sample.run_log.csv`.

Time estimate: 1.5 hours

Status: Completed

## Task 10 — Post-Mortem Analysis of Trade Signals (1.5h)

Items to implement:
- Create a new script `src/analysis/signal_quality.py` that accepts two CLI arguments: `--results <path_to_results.csv>` and `--log <path_to_run_log.csv>`.
- In the script:
    - Load both CSV files into pandas DataFrames.
    - Merge the trade results with the daily run log on the date (`entry_date` and `date`).
    - Calculate a normalized volatility column: `atr_pct = (atr14 / price) * 100`.
    - Group the resulting DataFrame by the `outcome` column (e.g., `TAKE_PROFIT_HIT`, `STOP_LOSS_HIT`).
    - For each outcome group, print a statistical summary (using `.describe()`) for the key columns: `return_score`, `volume_score`, `sma_score`, and `atr_pct`.
    - Use the `rich` library to format the output into clear, readable tables for each group.
- Update `README.md` with instructions on how to run this new analysis script.

Tests to cover:
- `tests/test_analysis.py`: Add a simple test that runs `signal_quality.py` on the sample results and log files, asserting that it completes with a zero exit code and the output contains expected headers (e.g., "TAKE_PROFIT_HIT Analysis").

Acceptance Criteria (AC):
- The script `src/analysis/signal_quality.py` is created and executable.
- Running the script with the sample data produces a console output with distinct statistical tables for each trade outcome.
- The analysis includes the new `atr_pct` metric.
- The `README.md` is updated with a new usage example for this script.

Definition of Done (DoD):
- `src/analysis/signal_quality.py` and its corresponding test are implemented and committed.
- `README.md` is updated.
- The script has been run locally against the existing `results.csv` and `RELIANCE.NS.run_log.csv` to generate initial insights.

Time estimate: 1.5 hours
