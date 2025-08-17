# Project: Emergent Alpha

Emergent Alpha is a decision-support system for identifying 20-day "buy" opportunities in stocks. The core philosophy blends discovering emergent patterns from raw data with a pragmatic focus on simplicity, speed, and using minimal, robust tools.

This MVP provides a deterministic, backtestable pipeline for a single stock ticker.

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

1.  **Clone the repository:**
    ```sh
    git clone <repository-url>
    cd emergent-alpha
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    ```

3.  **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

## Usage

The process involves running a backtest on sample data and then analyzing the results.

1.  **Run the Backtester:**
    This command will run the backtesting script on the sample Reliance Industries data. It will generate a `results/results.csv` file if any trade signals are found.

    The default lookback window for analysis is 40 days. You can change this with the `--lookback` flag:
    ```sh
    python backtester.py --ticker data/ohlcv/RELIANCE.NS.csv --lookback 60
    ```

2.  **Analyze the Results:**
    This command reads the output from the backtester and prints a performance summary, including total trades, win rate, and profit factor.
    ```sh
    python -m src.analysis.results results/runs/RELIANCE.NS.run_log.csv
    ```

Note: the trade results CSV (`results/results_<TICKER>.csv`) now includes numeric scorer columns in addition to `pattern_desc`:
- `return_score`, `trend_consistency_score`, `volume_score`, `sma_score`, `volatility_score`


3.  **Analyze Signal Quality:**
    This command correlates trade outcomes (e.g., wins vs. losses) with the daily scorer metrics that were present on the day of the trade signal. It helps you understand *why* the strategy is making its decisions.

    It requires both the trade results file and the daily run log file.
    ```sh
    python -m src.analysis.signal_quality --results results/results_RELIANCE.NS.csv --log results/runs/RELIANCE.NS.run_log.csv
    ```

The signal-quality analysis writes a CSV `results/signal_quality_<RESULTS_BASENAME>.csv` containing descriptive stats for each feature (features include the numeric scorer columns listed above). Use this file to correlate which score components predict successful trades.

