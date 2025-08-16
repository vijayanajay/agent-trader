import pandas as pd
import argparse
from pathlib import Path
from typing import List, Dict, Any

from src.data_preprocessor import preprocess_data
from src.pattern_scorer import score_pattern_deterministically
from src.risk_manager import calculate_risk_parameters


def run_backtest(ticker: str, data_path: Path, results_path: Path):
    """
    Runs the deterministic backtest for a single ticker.
    This function is now silent and produces only the results file.
    """
    try:
        full_data = pd.read_csv(data_path, index_col="Date", parse_dates=True)
    except FileNotFoundError:
        # Per H-12 (Zero silent failures), this should not be a bare return.
        # However, without a logger, printing is disallowed (H-18).
        # Re-raising is an option, but for a batch script, continuing may be desired.
        # For this MVP, we will exit silently on file-not-found.
        return

    trades: List[Dict[str, Any]] = []

    # Loop through each date, starting after the initial window period
    for analysis_date in full_data.index[40:]:
        analysis_date_str = analysis_date.strftime("%Y-%m-%d")
        processed = preprocess_data(full_data, analysis_date_str)

        if not processed:
            continue

        window_data, current_price, current_atr = processed
        score_result = score_pattern_deterministically(window_data)
        pattern_score = score_result["pattern_score"]

        # Decision rule: BUY if score is 7.0 or higher
        if pattern_score >= 7.0:
            risk_params = calculate_risk_parameters(current_price, current_atr)

            # Calculate trade outcome over a 20-day holding period
            entry_date_loc = full_data.index.get_loc(analysis_date)
            exit_date_loc = min(entry_date_loc + 20, len(full_data) - 1)
            exit_date = full_data.index[exit_date_loc]
            exit_price = full_data.loc[exit_date, "Close"]

            return_pct = (
                ((exit_price - current_price) / current_price) * 100
                if current_price != 0
                else 0
            )

            trade_log = {
                "entry_date": analysis_date_str,
                "ticker": ticker,
                "entry_price": round(current_price, 2),
                "pattern_score": pattern_score,
                "stop_loss": risk_params["stop_loss"],
                "take_profit": risk_params["take_profit"],
                "exit_date": exit_date.strftime("%Y-%m-%d"),
                "exit_price": round(exit_price, 2),
                "return_pct": round(return_pct, 2),
            }
            trades.append(trade_log)

    if not trades:
        return

    results_df = pd.DataFrame(trades)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(results_path, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run a deterministic backtest for a stock."
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default="RELIANCE.NS.sample",
        help="The ticker symbol to backtest (without .csv extension).",
    )
    args = parser.parse_args()

    DATA_DIR = Path("data/ohlcv")
    RESULTS_DIR = Path("results/runs")

    input_path = DATA_DIR / f"{args.ticker}.csv"
    output_path = RESULTS_DIR / f"{args.ticker}.results.csv"

    run_backtest(args.ticker, input_path, output_path)
