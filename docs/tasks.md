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

## Task 13 — Implement Trend Quality Score Component

*   **Rationale:** Analysis of `signal_quality_results` reveals a critical flaw: the current `return_score` is higher for losing trades (`STOP_LOSS_HIT`) than for winning trades (`TAKE_PROFIT_HIT`). This indicates the model is incorrectly rewarding sharp, unsustainable price spikes over steady, consistent trends. This task introduces a "trend quality" metric to the scorer. The goal is to penalize volatile price action and reward smooth, consistent upward movement, thereby improving the quality of the primary momentum signal.
*   **Items to implement:**
    - In `src/pattern_scorer.py`, modify the `score` function.
    - Within the 10-day lookback period used for `return_score`, calculate the number of days the price closed higher than the previous day (`up_days`).
    - Create a `trend_consistency_score` multiplier. A simple implementation could be `(up_days / RETURN_LOOKBACK_DAYS)`. This will be a value between 0.0 and 1.0.
    - Modify the `return_score` calculation to be `new_return_score = original_return_score * trend_consistency_score`. This ensures that a high return from a choppy, inconsistent trend is penalized.
    - Update the returned dictionary to include the new `trend_consistency_score` and adjust the `final_score` calculation.
    - Update the `description` string to reflect the new component.
    - In `backtester.py`, ensure the new `trend_consistency_score` is included in the `daily_logs` and saved to the `run_log.csv`.
*   **Tests to cover:**
    - In `tests/test_scorer.py`, add a new test case with a high 10-day return but poor consistency (e.g., 1 big jump, 9 small drops) that results in a penalized (lower) final score.
    - Add a new test case with a moderate, smooth 10-day return (e.g., 8 up days, 2 down days) that results in a rewarded (higher) final score.
    - Update `tests/test_backtester.py` to verify the new `trend_consistency_score` column exists in the generated `run_log.csv`.
*   **Acceptance Criteria (AC):**
    - The `score` function in `pattern_scorer.py` now includes a trend consistency component.
    - The final score correctly penalizes volatile trends and rewards smooth trends.
    - The `run_log.csv` generated by the backtester includes the new score component for analysis.
    - All existing and new unit tests pass (`python -m pytest`).
*   **Definition of Done (DoD):**
    - Changes to `src/pattern_scorer.py`, `backtester.py`, and their respective tests are implemented and committed.
    - A new backtest has been run on `RELIANCE.NS`.
    - The new `signal_quality_results_RELIANCE.NS.csv` has been generated and analyzed to confirm that the mean `return_score` for winning trades is now appropriately correlated with success.
*   **Time estimate:** 3 hours

Status: Completed


## Task 14 — Implement Relative Strength Score Component

*   **Rationale:** The signal quality analysis reveals that the current `return_score` is an anti-signal, rewarding unsustainable spikes. The model is context-blind. This task replaces the absolute return metric with a relative strength metric, comparing the stock's performance to the NIFTY 50 index. A stock outperforming a flat or down market is a much stronger signal than one simply rising with the tide. This is a foundational fix to improve the baseline deterministic model, per rule [H-23].
*   **Items to implement:**
    1.  **Modify `src/pattern_scorer.py`:**
        -   Update the `score` function signature to accept a `market_window_df: pd.DataFrame`.
        -   Remove the `return_score` and `trend_consistency_score` components.
        -   Create a new `relative_strength_score` component (max 4.0 points).
        -   Calculate the 10-day percentage return for the stock.
        -   Calculate the 10-day percentage return for the market index (`market_window_df`).
        -   The score should be based on the *difference*: `relative_return = stock_return - market_return`. A positive difference (outperformance) should yield a positive score. Scale it appropriately (e.g., a 5% outperformance over 10 days maps to the max score).
        -   Update the `final_score` calculation and the `description` string to use the new `relative_strength_score`.
    2.  **Modify `backtester.py`:**
        -   In the main loop, create a slice of the `market_regime` DataFrame corresponding to the `window_df` lookback period.
        -   Pass this `market_window_df` slice to the `score` function.
        -   Update the `daily_logs` to save the new `relative_strength_score`.
*   **Tests to cover:**
    -   In `tests/test_scorer.py`:
        -   Add a test case where the stock is up 5% but the market is up 10%. The `relative_strength_score` should be low or zero.
        -   Add a test case where the stock is up 2% and the market is down 3%. The `relative_strength_score` should be high.
        -   Update existing tests to accommodate the new function signature.
    -   In `tests/test_backtester.py`, verify that the new `relative_strength_score` column exists in the generated `run_log.csv`.
*   **Acceptance Criteria (AC):**
    -   The `score` function now calculates momentum based on relative strength against the market index.
    -   The backtester correctly provides market data to the scorer.
    -   The `run_log.csv` reflects the new scoring component.
    -   All unit tests pass (`python -m pytest`).
*   **Definition of Done (DoD):**
    -   Changes to `src/pattern_scorer.py`, `backtester.py`, and their tests are implemented and committed.
    -   A new backtest is run on `RELIANCE.NS`.
    -   The `signal_quality_results_RELIANCE.NS.csv` is regenerated and analyzed to confirm that the new score is a better predictor of success than the old `return_score`.
*   **Time estimate:** 4 hours

Status: Completed

## Task 15 — Activate the "Hinton Core": Implement LLM Pattern Analyser Agent

Rationale: The deterministic scorer provides a stable baseline. This task activates the project's core hypothesis: that an LLM can identify "emergent" patterns beyond simple heuristics. To achieve this pragmatically and avoid framework complexities noted in the project memory, the LLM was implemented as a direct adapter rather than a full CrewAI agent. It functions as an alternative scoring engine, allowing for a clean A/B comparison against the deterministic model, per rule [H-23].
Items Implemented:
LLM Adapter: Created src/adapters/llm.py to handle direct API calls to an LLM provider (OpenRouter) using httpx. This approach was chosen for simplicity and robustness, bypassing the crewai framework for this core task.
Data Formatting: Implemented format_data_for_llm in src/data_preprocessor.py to prepare a clean, normalized 40-day text block for the LLM prompt.
Prompt Management: Centralized the PATTERN_ANALYSER_PROMPT in src/prompts.py, using the exact text from the PRD.
LLM Audit Logging: The adapter strictly adheres to rule [H-22], logging every LLM call's metadata and response to results/llm_audit.log.
Backtester Integration:
Added a --scorer llm command-line argument to backtester.py.
When this mode is active, the backtester calls get_llm_analysis instead of the local score function.
The final_score for a trade signal is taken directly from the pattern_strength_score in the LLM's JSON response. The deterministic score components are completely bypassed in this mode.
Updated Logging: The daily_logs and the final trade results CSV were updated to include llm_pattern_score and llm_pattern_description when running in llm mode.
Tests Covered:
In tests/test_backtester.py, a new test test_backtester_llm_scorer_happy_path was added.
This test uses @patch to mock the get_llm_analysis function, ensuring the test runs without actual API calls.
It asserts that when --scorer llm is used, the backtester correctly calls the LLM adapter and that the resulting run_log.csv and trade list contain the new llm_ specific columns.
Acceptance Criteria (AC):
The backtester.py script accepts a --scorer llm argument.
When run with this flag, the script successfully calls the get_llm_analysis function for each day of the backtest.
A results/llm_audit.log file is created and populated with structured log entries.
The results/runs/<TICKER>.run_log.csv file contains the llm_pattern_score and llm_pattern_description columns.
The results/results_<TICKER>.csv file is generated based on the LLM-driven scores.
Definition of Done (DoD):
All new and modified code is committed to src/, tests/, and docs/.
All unit tests pass (python -m pytest).
A short backtest run on RELIANCE.NS.sample.csv using --scorer llm completes successfully and generates all expected output files.
The PRD and Architecture documents are updated to reflect the new implementation status.
Time estimate: 24 hours
Status: Completed (Refactored from original CrewAI plan)


## Task 16 — Implement Event-Based LLM Triggering

*   **Rationale:** Calling the LLM on every day of a backtest is inefficient. This task implements an "event-based" trigger to invoke an optional LLM scorer only on days with significant market action, focusing analysis on high-potential inflection points.
*   **Items to implement:**
    1.  **Modify `backtester.py`:**
        -   Add a single new command-line argument: `--llm` (as a boolean flag, `action="store_true"`).
        -   Inside the main backtest loop, check if the `--llm` flag is active.
        -   If `--llm` is active, implement the event detection logic:
            -   **Volume Spike:** `current_volume > 2.5 * 50-day_median_volume`.
            -   **SMA Crossover:** `price_today > sma50_today` AND `price_yesterday < sma50_yesterday`.
            -   If either event is detected, call the `get_llm_analysis` function from the LLM adapter. The `final_score` will be the `pattern_strength_score` from the LLM.
            -   If no event is detected, the score for that day is 0, and the LLM is **not** called.
        -   If `--llm` is **not** active, the backtester runs the existing deterministic `score()` function as default.
        -   Add a `trigger_event` column to the `daily_logs` to record what triggered the LLM call (e.g., "VOLUME_SPIKE").
*   **Tests to cover:**
    -   In `tests/test_backtester.py`, create a new test using a synthetic DataFrame with a clear volume spike and an SMA crossover.
    -   Mock the `get_llm_analysis` function.
    -   Run the backtester function programmatically with `use_llm_scorer=True`.
    -   Assert that the mocked LLM function was called **exactly twice**—only on the days where the events occurred.
*   **Acceptance Criteria (AC):**
    -   The `backtester.py` script accepts a `--llm` flag.
    -   Running with `--llm` results in a small, targeted number of LLM calls logged in `llm_audit.log`.
    -   The `run_log.csv` contains a `trigger_event` column, populated only on days the LLM was called.
    -   Running without the flag produces the same deterministic results as before.
*   **Definition of Done (DoD):**
    -   Changes to `backtester.py` and `tests/test_backtester.py` are implemented.
    -   All unit tests pass.
    -   A sample run on `RELIANCE.NS.sample.csv --llm` completes and demonstrates the event-based triggering.
*   **Status:** Not Started