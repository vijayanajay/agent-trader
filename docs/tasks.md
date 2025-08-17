# Emergent Alpha — concise source-of-truth (Tasks 1–10)

This section is the authoritative, condensed record of Tasks 1–10: what was implemented, the tests added, acceptance criteria, and current status. Use this as the single source of truth when deciding whether a behavior exists or what still needs work.

Summary (implemented)
- Project skeleton, sample data, and requirements. Directories, sample CSV (`data/ohlcv/RELIANCE.NS.sample.csv`), and `requirements.txt` added.
- Data preprocessor (`src/data_preprocessor.py`): loads CSVs, parses dates, computes SMA50/SMA200 and ATR14, and returns preprocessed frames and scalar indicators used by the backtester.
- Risk manager (`src/risk_manager.py`): `calculate_risk_parameters(current_price, atr14)` returns `stop_loss` and `take_profit` (stop = price - 2*ATR, take = price + 4*ATR behavior documented and tested).
- Pattern scorer (`src/pattern_scorer.py`): deterministic scorer implemented and extended to accept `atr14` and return component scores including `volatility_score` (inverse ATR%), `return_score`, `volume_score`, `sma_score`, `final_score`, and a human-readable `description`.
- Backtester (`backtester.py`): iterates historical data, applies market-regime filter (using `^NSEI` sma200 if available), calls the scorer, logs daily scorer components into `daily_logs`, writes both `results/results_<TICKER>.csv` (trades) and `results/runs/<TICKER>.run_log.csv` (per-day logs). Decision threshold uses `final_score`.
- Analysis scripts (`src/analysis/results.py`, `src/analysis/signal_quality.py`):
    - `results.py` prints overall backtest metrics (total trades, win rate, profit factor).
    - `signal_quality.py` merges `results` with the `run_log`, computes `atr_pct = (atr14 / price) * 100`, and prints per-outcome descriptive stats (now includes `volatility_score` and `atr_pct`). It also exports a long-form CSV `results/signal_quality_<results_basename>.csv`.

Tests added / updated
- Unit tests covering preprocessor, scorer, risk manager, backtester, and analysis functions are present in `tests/` (see individual test files). Key tests verify scorer component outputs, run_log CSV generation, and `signal_quality` CLI behavior.
- CLI integration tests for `results` and `signal_quality` ensure scripts run and print expected headers.

Acceptance criteria (what's guaranteed)
- Backtester produces two outputs when trades/logs are present:
    - `results/results_<TICKER>.csv` — trade list with: entry_date, entry_price, pattern_score/final_score, pattern_desc, stop_loss, take_profit, outcome, forward_return_pct.
    - `results/runs/<TICKER>.run_log.csv` — daily log with date, price, atr14, sma50, and scorer component columns (return_score, volume_score, sma_score, volatility_score, final_score, description).
- `signal_quality.py` reads the two files, merges on entry date, computes `atr_pct`, and outputs descriptive statistics per outcome (printed tables + `results/signal_quality_<results_basename>.csv`).

Current status
- Tasks 1–10: Implemented and tested locally (status: Completed). The codebase reflects the changes described above.

Notes and next-light improvements
- Tests showed a pytest cache permission warning on Windows when writing `.pytest_cache` — this is environmental and does not indicate functional failure; fix by adjusting directory permissions if desired.
- Recommend periodically regenerating `results/runs/<TICKER>.run_log.csv` after changes to scoring logic to keep `signal_quality` analysis up to date.


## Task 11 — Implement Market Regime Filter (Deterministic)

**Rationale:** The current signal generation is context-blind, leading to many failed trades in hostile market conditions. This task implements the simplest, most effective filter: only trade when the broader market is in an uptrend. This is a pragmatic MVP of the `Market_Context_Analyser` agent.
**Items to implement:**
    - In `backtester.py`, at the start of the `run_backtest` function, use `yfinance` to download the historical data for the NIFTY 50 index (`^NSEI`).
    - Calculate a 200-day Simple Moving Average (SMA) on the index's closing prices.
    - Inside the main date loop, before the scoring logic is called, add a market regime check:
        - Get the index's closing price and its 200-day SMA for the `current_date`.
        - If the index close is below its 200-day SMA, `continue` to the next day, skipping all scoring and trade logic.
    - Add `yfinance` to the main `requirements.txt` if it's not already there for the backtester's environment.
**Tests to cover:**
    - Update `tests/test_backtester.py` to ensure the script still runs to completion without errors after adding the market filter logic. The test does not need to assert the correctness of the filter itself, only the integrity of the script's execution.
**Acceptance Criteria (AC):**
    - `backtester.py` now includes logic to filter trades based on the NIFTY 50's 200-day SMA.
    - The script runs without error on the `RELIANCE.NS` data.
    - The new `results_RELIANCE.NS.csv` file shows a different (likely smaller) number of trades than the previous run.
**Definition of Done (DoD):**
    - Changes to `backtester.py` are implemented and committed.
    - `pytest` passes.
    - A new backtest has been run on `RELIANCE.NS` and the results have been briefly analyzed to confirm the filter is working as expected.
**Time estimate:** 1.5 hours


## Task 12 — Add Volatility Score Component

*   **Rationale:** The `signal_quality_results` show a weak correlation between lower volatility (`atr_pct`) and successful trades. This task formalizes that observation by adding an inverse volatility score, rewarding signals that occur during periods of lower price volatility.
*   **Items to implement:**
    - Modify the function signature in `src/pattern_scorer.py` from `score(window_df, current_price, sma50)` to `score(window_df, current_price, sma50, atr14)`.
    - Inside the `score` function:
        - Calculate `atr_pct = (atr14 / current_price) * 100`.
        - Create a new `volatility_score` component (max 2.0 points). The score should be inversely proportional to `atr_pct`. For example, a score of 2.0 for `atr_pct` < 1.5, a score of 0 for `atr_pct` > 4.0, and scaled linearly in between.
        - Add the `volatility_score` to the `total_score`.
        - Update the returned dictionary and the `description` string to include the new component.
    - In `backtester.py`, update the call to `score(...)` to pass the `atr14` value.
    - In `backtester.py`, ensure the new `volatility_score` is included in the `daily_logs` and saved to the `run_log.csv`.
*   **Tests to cover:**
    - In `tests/test_scorer.py`, update existing tests for the new function signature.
    - Add a new test case with low ATR that results in a high `volatility_score`.
    - Add a new test case with high ATR that results in a `volatility_score` of 0.
    - In `tests/test_backtester.py`, update the test to verify that the new `volatility_score` column exists in the generated `run_log.csv`.
*   **Acceptance Criteria (AC):**
    - `pattern_scorer.py` now incorporates a volatility-based score component.
    - `backtester.py` is updated to support the new scorer signature and logging.
    - The generated `run_log.csv` includes the `volatility_score`.
    - All tests pass.
*   **Definition of Done (DoD):**
    - Changes to `pattern_scorer.py`, `backtester.py`, and their respective tests are implemented and committed.
    - A new backtest has been run, and the new `signal_quality_results.csv` is generated to evaluate the impact of the change.
*   **Time estimate:** 1.5 hours

Status: Completed