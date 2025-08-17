# -*- coding: utf-8 -*-
"""
A simple, deterministic backtester for a single ticker.

This script iterates through historical data, applies a scoring model,
and logs hypothetical trades to a CSV file.

Usage:
    python backtester.py --ticker data/ohlcv/RELIANCE.NS.sample.csv
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.data_preprocessor import preprocess_data
from src.pattern_scorer import score
from src.risk_manager import calculate_risk_parameters

# --- Configuration ---
# The number of future data points required to determine trade outcome.
FORWARD_WINDOW = 20
# The score threshold to trigger a "BUY" signal.
SCORE_THRESHOLD = 7.0
# Parameters for indicators.
SMA50_PERIOD = 50
ATR_PERIOD = 14


# impure
def run_backtest(
    csv_path: str, lookback_window: int
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Runs the backtest logic for a given ticker CSV.

    This function is marked as impure because it interacts with the filesystem
    (reading a file) and can exit the program.
    """
    try:
        raw_df = pd.read_csv(csv_path, parse_dates=["Date"], index_col="Date")
        # Ensure the index is unique, keeping the first entry on duplicates.
        raw_df = raw_df[~raw_df.index.duplicated(keep="first")]
        # Remove timezone information to prevent dtype conflicts later.
        if isinstance(raw_df.index, pd.DatetimeIndex) and raw_df.index.tz is not None:
            raw_df.index = raw_df.index.tz_localize(None)
    except FileNotFoundError:
        print(f"Error: File not found at {csv_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading or parsing CSV {csv_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Load Market Data for Regime Filter ---
    market_regime = None
    try:
        # The market data must be pre-downloaded by a separate script.
        market_data_path = Path(csv_path).parent / "^NSEI.csv"
        nifty_df = pd.read_csv(market_data_path, parse_dates=["Date"], index_col="Date")
        # Remove timezone information to prevent dtype conflicts.
        if isinstance(nifty_df.index, pd.DatetimeIndex) and nifty_df.index.tz is not None:
            nifty_df.index = nifty_df.index.tz_localize(None)
        if "sma200" not in nifty_df.columns:
            nifty_df["sma200"] = nifty_df["Close"].rolling(window=200).mean()
        # Align index data with the stock data, filling missing dates.
        market_regime = nifty_df[["Close", "sma200"]].reindex(raw_df.index, method="ffill")
    except FileNotFoundError:
        print(f"Warning: Market data file not found at {market_data_path}. Proceeding without regime filter.", file=sys.stderr)


    min_df_len = lookback_window + FORWARD_WINDOW + 50
    if len(raw_df) < min_df_len:
        # Not an error, just not enough data to process.
        return [], []

    # --- Feature Engineering ---
    df = preprocess_data(
        raw_df,
        sma50_period=SMA50_PERIOD,
        atr_period=ATR_PERIOD,
    )

    if len(df) < (lookback_window + FORWARD_WINDOW):
        return [], []

    trades: List[Dict[str, Any]] = []
    daily_logs: List[Dict[str, Any]] = []

    # Iterate from the first possible day to the last possible day.
    for i in range(len(df) - FORWARD_WINDOW):
        # Ensure we have enough lookback data.
        if i < lookback_window:
            continue

        current_date = df.index[i]

        # --- Apply Market Regime Filter ---
        if market_regime is not None:
            try:
                # Ensure a DataFrame is returned, then extract scalar values from the first row.
                regime_data = market_regime.loc[[current_date]]
                close_val = regime_data["Close"].iloc[0]
                sma_val = regime_data["sma200"].iloc[0]

                if pd.notna(sma_val) and (close_val < sma_val):
                    continue  # Skip if market is in a downtrend.
            except KeyError:
                 # If date not in index, continue without filter for that day.
                 pass


        window_df = df.iloc[i - lookback_window : i]

        current_price = df["Close"].iloc[i]
        sma50 = df["sma50"].iloc[i]
        atr14 = df["atr14"].iloc[i]

        score_result = score(window_df, current_price, sma50, atr14)

        # Log daily signals and indicators.
        log_entry = {
            "date": current_date.strftime("%Y-%m-%d"),
            "price": current_price,
            "atr14": atr14,
            "sma50": sma50,
            **score_result,
        }
        daily_logs.append(log_entry)

        if score_result["final_score"] >= SCORE_THRESHOLD:
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
                    "pattern_score": score_result["final_score"],
                    "pattern_desc": score_result["description"],
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "outcome": outcome,
                    "forward_return_pct": round(forward_return_pct, 2),
                }
            )

    return trades, daily_logs

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
    parser.add_argument(
        "--lookback",
        type=int,
        default=40,
        help="The lookback window size for feature calculation (default: 40).",
    )
    args = parser.parse_args()

    # Derive a filename-friendly ticker name from the provided path.
    # Use Path.stem so `data/ohlcv/RELIANCE.NS.csv` -> "RELIANCE.NS".
    ticker_name = Path(args.ticker).stem

    trades, daily_logs = run_backtest(args.ticker, args.lookback)

    # --- Save Trades ---
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    trade_output_path = results_dir / f"results_{ticker_name}.csv"
    if trades:
        results_df = pd.DataFrame(trades)
        results_df.to_csv(trade_output_path, index=False)
        print(
            f"Backtest complete. Found {len(trades)} trades. "
            f"Results saved to {trade_output_path}"
        )
    else:
        print("Backtest complete. No trades were triggered.")
        # Create empty file with headers if no trades found.
        pd.DataFrame(
            columns=[
                "entry_date", "entry_price", "pattern_score", "pattern_desc",
                "stop_loss", "take_profit", "outcome", "forward_return_pct",
            ]
        ).to_csv(trade_output_path, index=False)

    # --- Save Daily Run Log ---
    if daily_logs:
        ticker_name = Path(args.ticker).stem
        log_dir = Path("results/runs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_output_path = log_dir / f"{ticker_name}.run_log.csv"

        log_df = pd.DataFrame(daily_logs)
        log_df.to_csv(log_output_path, index=False, float_format="%.2f")
        print(f"Daily run log saved to {log_output_path}")


if __name__ == "__main__":
    main()
