## PRD: Project "Emergent Alpha"

*   **Version:** 1.0
*   **Date:** October 26, 2023
*   **Author:** System AI
*   **Status:** The deterministic backtester (MVP) is complete. The `Pattern_Analyser` agent (Task 15) is implemented and integrated behind a `--scorer llm` flag.

### 1. Overview

**Project "Emergent Alpha"** is a rapid-development initiative to create a decision-support system for identifying 20-day "buy" opportunities in Indian large and mid-cap stocks. The core philosophy blends Geoffrey Hinton's approach of discovering emergent patterns from raw data with Kailash Nadh's pragmatic focus on simplicity, speed, and using minimal, robust tools.

The system will be built as an agentic workflow using CrewAI and Python. CrewAI provides a lightweight, code-first approach to multi-agent orchestration without the overhead of visual workflow builders. It will ingest standard OHLCV data and leverage a Large Language Model (LLM) as a general-purpose pattern recognition engine, avoiding hard-coded technical analysis rules. The goal is to have a functional, backtestable prototype within a 2-day sprint.

### 2. Goal & Objectives

**Primary Goal:** To build a functional, backtestable trading idea generation system that can process stock data and output high-probability "BUY" signals for a 20-day holding period.

**Key Objectives (v1.0):**
1.  **Rapid Prototyping:** Implement a working end-to-end system in under 48 hours.
2.  **Code-First:** Use CrewAI's simple Python-based agent framework to maintain full control and transparency.
3.  **Emergent Analysis:** Empower the LLM to identify patterns from numerical sequences rather than enforcing pre-defined technical indicators.
4.  **Backtestability:** Create a simple framework to run the system over historical data and evaluate its performance.
5.  **Modularity:** Design the system with distinct, swappable agents for easy experimentation.

### 3. Scope

| In Scope (v1.0)                                          | Out of Scope (v1.0)                                         |
| -------------------------------------------------------- | ----------------------------------------------------------- |
| Analysis of Indian Large & Mid-cap stocks (Nifty 200)    | Small-cap, micro-cap, or international stocks               |
| Generation of "BUY" signals only                         | "SELL" or "SHORT" signals                                   |
| 20-day fixed holding period for backtesting              | Dynamic exit strategies or trailing stop-losses             |
| Input from a single OHLCV CSV file per stock             | Real-time data feeds or multiple data sources (news, etc.)  |
| Backtesting on historical data                           | Live trading execution or paper trading integration         |
| Use of CrewAI, Python, `pandas`, `yfinance`              | Complex machine learning models (e.g., LSTMs, Transformers) |
| A meta-agent for suggesting feature improvements         | Automated feature engineering and selection                 |

### 4. System Architecture & Flow Diagram

The system operates as a crew of specialized agents coordinated by CrewAI. Each agent has a specific role and expertise, working together sequentially to analyze stock data and make trading decisions. The orchestration is managed through simple Python code, maintaining transparency and control.

**High-Level Flow:**

```mermaid
graph TD
    A[Input: Stock OHLCV CSV] --> B(Agent 1: Data_Preprocessor);
    B --> C(Agent 2: Pattern_Analyser);
    A --> D(Agent 3: Market_Context_Analyser);
    B --> E(Agent 4: Risk_Manager);
    C --> F(Agent 5: Decision_Synthesizer);
    D --> F;
    E --> F;
    F --> G[Output: Trade Decision (BUY/PASS) + Rationale];

    subgraph "Offline Analysis"
        H(Agent 6: Feature_Suggester)
    end
```

### 5. Agentic Workflow: Detailed Breakdown

This section details each agent in the flow.

---

#### **Agent 1: `Data_Preprocessor`**

*   **Purpose:** To ingest the raw OHLCV data, calculate necessary metrics, and format it into a clean, LLM-friendly text block.
*   **Type:** CrewAI Agent with Python tools.
*   **Inputs:**
    *   `stock_dataframe`: A pandas DataFrame from the OHLCV CSV.
    *   `current_date`: The date for which the analysis is being performed.
*   **Processing Logic:**
    1.  Select the last 60 trading days of data leading up to the `current_date`.
    2.  Calculate:
        *   50-day Simple Moving Average (SMA).
        *   200-day Simple Moving Average (SMA).
        *   14-day Average True Range (ATR).
        *   Daily percentage change.
    3.  Normalize the closing prices and volumes of the 60-day window to a scale of 0 to 1.
    4.  Determine the current price's position relative to the 50-day and 200-day MAs (e.g., "+5.2%" or "-1.8%").
    5.  Format all this information into a single, structured string.
*   **Output:** A formatted string containing all the prepared data for the next agents.
    *   `preprocessed_data_string`: A text block.
    *   `current_price`: The closing price on `current_date`.
    *   `current_atr`: The ATR value on `current_date`.

---

#### **Agent 2: `Pattern_Analyser` (The Hinton Core)**

*   **Purpose:** To analyze the numerical data provided by the preprocessor and identify emergent patterns indicative of a potential upward move, without being biased by human-defined pattern names.
*   **Type:** CrewAI Agent with LLM capability.
*   **Input:** `preprocessed_data_string` from Agent 1.
*   **Initial Prompt:**
    ```
    You are an expert quantitative analyst specializing in identifying emergent patterns in financial time-series data. Your task is to analyze the provided 60-day data for a stock and assess the likelihood of a significant price increase over the next 20 days.

    **Instructions:**
    1.  **Avoid Technical Jargon:** Do NOT use names like "Head and Shoulders," "Cup and Handle," or "Flag." Instead, describe the behavior you observe in plain language.
    2.  **Focus on Price & Volume Dynamics:** Describe the relationship between price movement and volume. For example: "Price is consolidating in a tight range on decreasing volume," or "Price is showing strong upward momentum with consistently high volume."
    3.  **Provide a Score:** Based on your analysis, provide a "Pattern Strength Score" from 0 (very bearish) to 10 (very bullish) for a 20-day forward outlook.
    4.  **Justify Your Score:** Provide a brief, clear rationale for your score.

    **Data Provided:**
    {preprocessed_data_string}

    **Required Output Format (JSON):**
    {
      "pattern_description": "Your detailed description of the price and volume behavior.",
      "pattern_strength_score": <Your score from 0 to 10>,
      "rationale": "Your justification for the score."
    }
    ```
*   **Output:** A JSON string with the analysis.

---

#### **Agent 3: `Market_Context_Analyser`**

*   **Purpose:** To provide broader market and sector context to avoid taking good trades in a bad environment.
*   **Type:** CrewAI Agent with Python tools and LLM capability.
*   **Input:** `stock_ticker` (e.g., "RELIANCE.NS").
*   **Processing Logic:**
    1.  **(Python Tool)** A mapping function determines the stock's sector index (e.g., "RELIANCE.NS" -> `^CNXENERGY`).
    2.  **(Python Tool)** Use `yfinance` to download the last 60 days of data for the relevant sector index and for India VIX (`^INDIAVIX`).
    3.  **(Python Tool)** Calculate the recent trend of the sector (e.g., percentage change over 20 days) and the current level of VIX.
    4.  **(LLM)** Pass this information to the agent's LLM capability to classify the context.
*   **Initial Prompt (for the LLM part):**
    ```
    Analyze the following market context data and provide a simple classification.
    - Sector Index 20-day Trend: {sector_trend_percent}%
    - Current India VIX: {vix_level}

    Classify the Sector Trend as one of: [Strong Uptrend, Mild Uptrend, Sideways, Mild Downtrend, Strong Downtrend].
    Classify the VIX Level as one of: [Low (Complacency), Moderate (Normal), High (Fear), Extreme (Panic)].

    **Required Output Format (JSON):**
    {
      "sector_trend": "Your classification",
      "vix_analysis": "Your classification"
    }
    ```
*   **Output:** A JSON string with market context classifications.

---

#### **Agent 4: `Risk_Manager`**

*   **Purpose:** To calculate a predefined stop-loss and take-profit target for any potential trade.
*   **Type:** CrewAI Agent with Python tools.
*   **Inputs:**
    *   `current_price` from Agent 1.
    *   `current_atr` from Agent 1.
*   **Processing Logic:**
    1.  Calculate Stop-Loss: `stop_loss = current_price - (2 * current_atr)`.
    2.  Calculate Take-Profit: `take_profit = current_price + (4 * current_atr)`. (Ensures a 1:2 Risk-Reward ratio).
*   **Output:** A JSON object: `{"stop_loss": <value>, "take_profit": <value>}`.

---

#### **Agent 5: `Decision_Synthesizer`**

*   **Purpose:** The final decision-making agent. It integrates all prior analyses and makes the final "BUY" or "PASS" call based on a set of rules.
*   **Type:** CrewAI Agent with LLM capability.
*   **Inputs:**
    *   Output from `Pattern_Analyser`.
    *   Output from `Market_Context_Analyser`.
    *   Output from `Risk_Manager`.
*   **Initial Prompt:**
    ```
    You are the final decision-making module of a trading system. Your task is to synthesize all available information and issue a final trade decision.

    **Decision Rules (Strict):**
    1.  The `pattern_strength_score` MUST be 7.0 or higher.
    2.  The `sector_trend` MUST NOT be 'Mild Downtrend' or 'Strong Downtrend'.
    3.  The `vix_analysis` MUST NOT be 'High (Fear)' or 'Extreme (Panic)'.

    **If all rules are met, the decision is BUY. Otherwise, it is PASS.**

    **Analysis Data:**
    - Pattern Analysis: {output_from_pattern_analyser}
    - Market Context: {output_from_market_context_analyser}
    - Risk Parameters: {output_from_risk_manager}

    **Required Output Format (JSON):**
    {
      "decision": "[BUY/PASS]",
      "confidence_score": <A score from 1-10, only if decision is BUY>,
      "summary_rationale": "A one-sentence summary explaining the final decision."
    }
    ```
*   **Output:** A JSON string containing the final trade decision.

---

#### **Agent 6: `Feature_Suggester` (Offline Meta-Agent)**

*   **Purpose:** To provide ideas on how to improve the system's predictive power by adding new features. This agent is run manually, not as part of the main crew.
*   **Type:** CrewAI Agent with LLM capability.
*   **Input:** A manually written prompt describing the current system.
*   **Initial Prompt:**
    ```
    I have a trading model that uses OHLCV, 50/200-day MAs, and ATR for Indian stocks to predict 20-day forward returns. To improve its accuracy, please suggest 5 additional data columns I could create. For each suggestion, provide:
    1.  The feature name (e.g., "Relative Strength Index (14)").
    2.  How to calculate it from OHLCV data or fetch it using the 'yfinance' library.
    3.  The rationale for why it would improve the model's predictive power.
    ```
*   **Output:** A text block with detailed suggestions for new features.

### 6. Implementation Plan (2-Day Sprint)

**Day 1: Component Build & Unit Test (8 Hours)**

*   **(1 hr) Setup:** Environment setup (`Python`, `CrewAI`, `pandas`, `yfinance`).
*   **(2 hrs) Data Acquisition:** Write a Python script to download historical OHLCV data for Nifty 200 stocks from `yfinance` and save them as individual CSVs.
*   **(3 hrs) Agent Development:** Create CrewAI agents with their respective tools and capabilities. Define agent roles, goals, and backstories. Test individual agents with sample data to ensure they produce correct outputs.
*   **(2 hrs) Prompt Engineering:** Draft and refine the prompts for agents that use LLM capabilities (`Pattern_Analyser`, `Market_Context_Analyser`, and `Decision_Synthesizer`).

**Day 2: Integration, Backtesting, and Review (8 Hours)**

*   **(3 hrs) CrewAI Integration:** Assemble the crew of agents in Python code. Define tasks for each agent and set up the sequential workflow. Create a simple main script that orchestrates the crew execution. Test the end-to-end flow with a single stock's data to ensure data flows correctly between agents.
*   **(4 hrs) Backtester Script:** Write a master Python script (`backtester.py`) that:
    *   Loops through all downloaded stock CSVs.
    *   For each day in the historical data, it instantiates the crew with the required 60-day lookback data.
    *   Logs the `BUY` signals, entry price, and calculates the actual 20-day forward return.
    *   Saves all trades and their outcomes to a `results.csv` file.
*   **(1 hr) Analysis & Review:** Use pandas to analyze `results.csv`. Calculate key performance metrics. Run the `Feature_Suggester` agent to get ideas for v1.1.

### 7. Success Metrics

The success of the v1.0 prototype will be measured by:
*   **Completion:** A functional, end-to-end pipeline is completed within the 2-day timeframe.
*   **Backtest Win Rate:** > 55% on the historical dataset.
*   **Profit Factor:** (Gross Profit / Gross Loss) > 1.5.
*   **Qualitative Feedback:** The rationales provided by the system are logical and insightful.

### 8. MVP Plan (Kailash Nadh pragmatism)

This MVP plan focuses on delivering a minimal, verifiable prototype in the shortest time with the least friction. It trades fancy orchestration for repeatability and fast learning.

Goals:
- Deliver an end-to-end pipeline for a single ticker that produces reproducible `results.csv` containing trades and 20-day outcomes.
- Prefer deterministic, testable components first; add LLM capability as an optional, instrumented enhancement.

Concrete steps (ordered, 48-hour friendly):
1. Create a minimal code layout:
    - `data/preprocessor.py` — read CSV or `yfinance`, compute 50/200 SMA, 14-day ATR, daily pct change, and return a normalized window (N=40 by default).
    - `strategy/pattern_scorer.py` — two modes: `deterministic` (fast, used for backtests) and `llm` (optional). Deterministic scorer = normalized recent return + volume surge + MA position, scaled to 0–10.
    - `risk/risk_manager.py` — stop_loss = price - 2*ATR, take_profit = price + 4*ATR.
    - `backtester.py` — iterate dates for one ticker, call preprocessor → scorer → risk → decision, log trades to `results.csv`.
    - `analysis/analyze_results.py` — compute win rate, profit factor, trade count.
2. Add a single, small sample CSV for one representative ticker (e.g., `data/RELIANCE.NS.sample.csv`) so runs are instant.
3. Add unit tests for `preprocessor` and `risk_manager` (happy path + ATR=0 edge case).
4. Run a single-ticker backtest and capture `results.csv`. Confirm the pipeline runs without LLM keys or CrewAI.
5. If the deterministic baseline is noisy or promising, enable `llm` mode on a small subset and compare outputs.

Acceptance criteria:
- `backtester.py` completes for one ticker and writes `results.csv`.
- `analyze_results.py` prints win rate and profit factor.
- Minimal tests pass locally.

Trade-offs and rationale (Kailash mindset):
- Keep orchestration minimal: CrewAI and multi-agent choreography are high-value later; validate signal first.
- Use deterministic scoring to create a stable baseline for comparison; LLM should improve interpretation, not be the entire pipeline.

### 9. Next phase (Kailash pragmatism + Hinton experimentation)

After the MVP confirms the pipeline and provides reproducible metrics, the next phase balances pragmatic product work (Kailash) with experimental discovery (Hinton). Focus areas and prioritized experiments:

1. Stabilize & scale (practical / product):
    - Expand backtesting to a curated set of 50 tickers (diverse sectors) and run batched jobs.
    - Add robust data plumbing: ticker list, download scripts, CSV canonicalization, daily cron-friendly runner.
    - Add reproducible experiment tracking: store run config, scorer mode, LLM prompt version, and results (simple JSON per run).
    - Add basic visualization for results (PNL curve, trade distribution) to speed decision making.

2. Integrate LLMs carefully (experimental / Hinton-style):
    - Treat the LLM as an experimental oracle: run it on a held-out subset and measure marginal benefit vs deterministic scorer.
    - Use controlled A/B tests: for the same date/ticker, compare decisions using `deterministic` vs `llm` modes and log discrepancies.
    - Iterate prompts and temperature: keep prompt versions pinned and add a tiny utilities folder to version prompts and parse outputs.

3. Modular agent rollout (orchestration):
    - Once the LLM shows marginal value, implement the CrewAI crew with 3 core agents: `Data_Preprocessor`, `Pattern_Analyser` (LLM-enabled), and `Decision_Synthesizer`.
    - Keep Market_Context and Risk_Manager as lightweight local functions for now; promote to agents if orchestration helps experiments.

4. Research experiments (Hinton-style exploratory work):
    - Probe emergent representations: feed raw normalized windows to LLMs and ask for compressed pattern tokens; track if these tokens correlate with returns.
    - Use ensembling of small deterministic indicators with LLM-derived features and measure combined performance.
    - Explore contrastive prompts: ask the LLM to compare two nearby windows and explain which is more likely to lead to a 20-day rise — capture explanations as features.

5. Safety & sanity checks:
    - Add checks for corporate actions and large gaps; flag or skip dates with extreme adjustments.
    - Add audit logs for LLM calls (prompt version, seed, response) to allow reproducible analysis.

Deliverables for next phase:
 - Batched backtester for 50 tickers with run metadata saved per run.
 - Visualization dashboard (static HTML + plots) for P&L, trade coverage, and signal distribution.
 - A small experimental report comparing deterministic baseline vs LLM-augmented results.

Closing note (Kailash + Hinton): iterate fast, measure carefully. Build the simplest reliable baseline first, then use carefully instrumented LLM experiments to chase marginal wins. Focus on short feedback loops and reproducible comparisons.