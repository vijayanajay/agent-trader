import pandas as pd
import argparse
from pathlib import Path
from typing import List, Dict, Any

from src.data_preprocessor import normalize_window
from src.pattern_scorer import score
from src.risk_manager import calculate_risk_parameters

# --- Constants ---
LOOKBACK_WINDOW = 40
SMA_PERIOD = 50
ATR_PERIOD = 14
HOLDING_PERIOD = 20
SCORE_THRESHOLD = 7.0


def _calculate_atr(data: pd.DataFrame, period: int) -> pd.Series:
    """Helper to calculate Average True Range."""
    high_low = data["High"] - data["Low"]
    high_close = (data["High"] - data["Close"].shift()).abs()
    low_close = (data["Low"] - data["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


# impure
def run_backtest(ticker: str, data_path: Path, results_path: Path):
    """
    Runs the deterministic backtest for a single ticker.
    This function reads a data file and writes a results file.
    """
    try:
        full_data = pd.read_csv(data_path, index_col="Date", parse_dates=True)
    except FileNotFoundError as e:
        # Per H-12, re-raise exceptions rather than failing silently.
        # Per H-18, do not use print() in library code.
        raise e

    # --- Pre-calculate all indicators once for efficiency ---
    full_data["sma50"] = full_data["Close"].rolling(window=SMA_PERIOD).mean()
    full_data["atr14"] = _calculate_atr(full_data, period=ATR_PERIOD)

    # Drop rows with NaN indicators to ensure data integrity for backtest loop
    full_data.dropna(inplace=True)

    if len(full_data) < HOLDING_PERIOD:
        # Not enough data to run a single backtest after accounting for indicators
        return

    trades: List[Dict[str, Any]] = []

    # Loop through each valid date in the pre-processed data
    for i in range(len(full_data) - HOLDING_PERIOD):
        analysis_date = full_data.index[i]

        # Define the window for analysis
        start_loc = max(0, i - LOOKBACK_WINDOW + 1)
        window_df_raw = full_data.iloc[start_loc : i + 1]

        # Normalize the window for the scorer
        window_df_normalized = normalize_window(window_df_raw)

        current_price = full_data.loc[analysis_date, "Close"]
        current_sma50 = full_data.loc[analysis_date, "sma50"]
        current_atr = full_data.loc[analysis_date, "atr14"]

        score_result = score(window_df_normalized, current_price, current_sma50)
        pattern_score = score_result["pattern_strength_score"]

        if pattern_score >= SCORE_THRESHOLD:
            risk_params = calculate_risk_parameters(current_price, current_atr)

            # Calculate trade outcome over the holding period
            exit_date = full_data.index[i + HOLDING_PERIOD]
            exit_price = full_data.loc[exit_date, "Close"]
            return_pct = ((exit_price - current_price) / current_price) * 100

            trades.append({
                "entry_date": analysis_date.strftime("%Y-%m-%d"),
                "ticker": ticker,
                "entry_price": round(current_price, 2),
                "pattern_score": pattern_score,
                "pattern_description": score_result["pattern_description"],
                "stop_loss": risk_params["stop_loss"],
                "take_profit": risk_params["take_profit"],
                "exit_date": exit_date.strftime("%Y-%m-%d"),
                "exit_price": round(exit_price, 2),
                "return_pct": round(return_pct, 2),
            })

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
