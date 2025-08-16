# -*- coding: utf-8 -*-
"""
A simple, deterministic backtester for a single ticker.

This script iterates through historical data, applies a scoring model,
and logs hypothetical trades to a CSV file.

Usage:
    python backtester.py --ticker data/ohlcv/RELIANCE.NS.sample.csv
"""
import argparse
import sys
from typing import Dict, List, Any

import pandas as pd

from src.data_preprocessor import preprocess_data
from src.pattern_scorer import score
from src.risk_manager import calculate_risk_parameters

# --- Configuration ---
# The number of historical data points required for feature calculations.
LOOKBACK_WINDOW = 40
# The number of future data points required to determine trade outcome.
FORWARD_WINDOW = 20
# Minimum number of rows required in the raw CSV to run the backtest.
MIN_DF_LEN = LOOKBACK_WINDOW + FORWARD_WINDOW + 50  # Add buffer for SMA/ATR calc
# The score threshold to trigger a "BUY" signal.
SCORE_THRESHOLD = 7.0
# Parameters for indicators.
SMA_PERIOD = 50
ATR_PERIOD = 14


# impure
def run_backtest(csv_path: str) -> List[Dict[str, Any]]:
    """
    Runs the backtest logic for a given ticker CSV.

    This function is marked as impure because it interacts with the filesystem
    (reading a file) and can exit the program.
    """
    try:
        raw_df = pd.read_csv(csv_path, parse_dates=["Date"], index_col="Date")
    except FileNotFoundError:
        print(f"Error: File not found at {csv_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading or parsing CSV {csv_path}: {e}", file=sys.stderr)
        sys.exit(1)

    if len(raw_df) < MIN_DF_LEN:
        # Not an error, just not enough data to process.
        return []

    # --- Feature Engineering ---
    df = preprocess_data(raw_df, sma_period=SMA_PERIOD, atr_period=ATR_PERIOD)

    if len(df) < (LOOKBACK_WINDOW + FORWARD_WINDOW):
        return []

    trades: List[Dict[str, Any]] = []

    # Iterate from the first possible day to the last possible day.
    for i in range(len(df) - FORWARD_WINDOW):
        # Ensure we have enough lookback data.
        if i < LOOKBACK_WINDOW:
            continue

        current_date = df.index[i]
        window_df = df.iloc[i - LOOKBACK_WINDOW : i]

        current_price = df["Close"].iloc[i]
        sma50 = df["sma50"].iloc[i]
        atr14 = df["atr14"].iloc[i]

        score_result = score(window_df, current_price, sma50)

        if score_result["pattern_strength_score"] >= SCORE_THRESHOLD:
            risk_params = calculate_risk_parameters(current_price, atr14)
            stop_loss = risk_params["stop_loss"]
            take_profit = risk_params["take_profit"]

            forward_window_df = df.iloc[i + 1 : i + 1 + FORWARD_WINDOW]
            min_price_forward = forward_window_df["Low"].min()
            max_price_forward = forward_window_df["High"].max()

            outcome = "HOLD_20_DAYS"
            if min_price_forward <= stop_loss:
                outcome = "STOP_LOSS_HIT"
            elif max_price_forward >= take_profit:
                outcome = "TAKE_PROFIT_HIT"

            final_price = df["Close"].iloc[i + FORWARD_WINDOW]
            forward_return_pct = ((final_price - current_price) / current_price) * 100

            trades.append(
                {
                    "entry_date": current_date.strftime("%Y-%m-%d"),
                    "entry_price": round(current_price, 2),
                    "pattern_score": score_result["pattern_strength_score"],
                    "pattern_desc": score_result["pattern_description"],
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "outcome": outcome,
                    "forward_return_pct": round(forward_return_pct, 2),
                }
            )

    return trades

# impure
def main() -> None:
    """
    Main function to parse arguments and run the backtester.
    Impure due to filesystem I/O and printing.
    """
    parser = argparse.ArgumentParser(description="Emergent Alpha Backtester")
    parser.add_argument(
        "--ticker",
        type=str,
        required=True,
        help="Path to the ticker CSV file (e.g., data/ohlcv/RELIANCE.NS.sample.csv).",
    )
    args = parser.parse_args()

    trades = run_backtest(args.ticker)

    output_path = "results/results.csv"
    if trades:
        results_df = pd.DataFrame(trades)
        results_df.to_csv(output_path, index=False)
        print(f"Backtest complete. Found {len(trades)} trades. Results saved to {output_path}")
    else:
        print("Backtest complete. No trades were triggered.")
        # Create empty file with headers if no trades found.
        pd.DataFrame(columns=[
            "entry_date", "entry_price", "pattern_score", "pattern_desc",
            "stop_loss", "take_profit", "outcome", "forward_return_pct"
        ]).to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
