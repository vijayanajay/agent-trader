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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from src.data_preprocessor import preprocess_data
from src.pattern_scorer import score, ScorerConfig
from src.risk_manager import calculate_risk_parameters

# --- Conditional Imports ---
# To avoid heavy imports when not using the LLM scorer
_llm_scorer_imported = False
run_crew_analysis: Optional[Callable[[Any], Dict[str, Any]]] = None
try:
    from src.crew import run_crew_analysis
    _llm_scorer_imported = True
except ImportError as e:
    print(f"LLM scorer import failed: {e}", file=sys.stderr)


@dataclass
class BacktestConfig:
    """Configuration for the backtester execution."""

    scorer_type: str = "deterministic"
    forward_window: int = 20
    score_threshold: float = 7.0
    lookback_window: int = 40
    sma50_period: int = 50
    atr_period: int = 14


# impure
def _load_data(csv_path: str) -> pd.DataFrame:
    """Loads and prepares the main ticker data from a CSV file."""
    try:
        raw_df = pd.read_csv(csv_path, parse_dates=["Date"], index_col="Date")
        raw_df = raw_df[~raw_df.index.duplicated(keep="first")]
        if isinstance(raw_df.index, pd.DatetimeIndex) and raw_df.index.tz is not None:
            raw_df.index = raw_df.index.tz_localize(None)
        return raw_df
    except FileNotFoundError:
        print(f"Error: File not found at {csv_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading or parsing CSV {csv_path}: {e}", file=sys.stderr)
        sys.exit(1)


# impure
def _load_market_data(
    csv_path: str, main_index: pd.DatetimeIndex
) -> Optional[pd.DataFrame]:
    """Loads and prepares the market index data for the regime filter."""
    try:
        market_data_path = Path(csv_path).parent / "^NSEI.csv"
        nifty_df = pd.read_csv(market_data_path, parse_dates=["Date"], index_col="Date")
        if isinstance(nifty_df.index, pd.DatetimeIndex) and nifty_df.index.tz is not None:
            nifty_df.index = nifty_df.index.tz_localize(None)
        if "sma200" not in nifty_df.columns:
            nifty_df["sma200"] = nifty_df["Close"].rolling(window=200).mean()
        return nifty_df[["Close", "sma200"]].reindex(main_index, method="ffill")
    except FileNotFoundError:
        print(
            f"Warning: Market data not found at {market_data_path}. "
            "Proceeding without regime filter.",
            file=sys.stderr,
        )
        return None


def _get_trade_outcome(
    df: pd.DataFrame, i: int, risk_params: Dict[str, float], cfg: BacktestConfig
) -> Dict[str, Any]:
    """Determines the outcome of a trade over the forward window."""
    forward_df = df.iloc[i + 1 : i + 1 + cfg.forward_window]
    min_forward = forward_df["Low"].min()
    max_forward = forward_df["High"].max()

    outcome = "HOLD_20_DAYS"
    if min_forward <= risk_params["stop_loss"]:
        outcome = "STOP_LOSS_HIT"
    elif max_forward >= risk_params["take_profit"]:
        outcome = "TAKE_PROFIT_HIT"

    final_price = df["Close"].iloc[i + cfg.forward_window]
    entry_price = df["Close"].iloc[i]
    fwd_return_pct = ((final_price - entry_price) / entry_price) * 100

    return {"outcome": outcome, "forward_return_pct": round(fwd_return_pct, 2)}


# impure
def run_backtest(
    csv_path: str, cfg: BacktestConfig, scorer_cfg: ScorerConfig
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Runs the backtest logic for a given ticker CSV. Impure due to I/O.
    """
    if cfg.scorer_type == "llm" and not _llm_scorer_imported:
        print("Error: --scorer llm requires crewai and dependencies.", file=sys.stderr)
        print("Please run 'pip install -r requirements.txt'.", file=sys.stderr)
        sys.exit(1)
    raw_df = _load_data(csv_path)
    market_regime = _load_market_data(csv_path, raw_df.index)

    min_len = cfg.lookback_window + cfg.forward_window + 50
    if len(raw_df) < min_len:
        return [], []

    df = preprocess_data(
        raw_df, sma50_period=cfg.sma50_period, atr_period=cfg.atr_period
    )

    trades: List[Dict[str, Any]] = []
    daily_logs: List[Dict[str, Any]] = []

    for i in range(cfg.lookback_window, len(df) - cfg.forward_window):
        current_date = df.index[i]

        if market_regime is not None:
            try:
                regime_now = market_regime.loc[current_date]
                if pd.notna(regime_now["sma200"]) and (regime_now["Close"] < regime_now["sma200"]):
                    continue
            except KeyError:
                print(
                    f"Warning: Market data for {current_date.date()} not found. "
                    "Skipping regime filter for this day.",
                    file=sys.stderr,
                )

        window_df = df.iloc[i - cfg.lookback_window : i]
        current_price = df["Close"].iloc[i]

        if cfg.scorer_type == "llm" and run_crew_analysis is not None:
            llm_result = run_crew_analysis(window_df)
            if "error" in llm_result:
                print(f"LLM Error on {current_date.date()}: {llm_result.get('error')}", file=sys.stderr)
                score_result = {"final_score": 0, "description": "LLM_ERROR"}
            else:
                # Mimic the deterministic scorer's output structure
                llm_score_raw = llm_result.get("pattern_strength_score")
                # Handle case where score is null or missing
                if llm_score_raw is None or llm_score_raw == "null":
                    llm_score = 0.0
                else:
                    try:
                        llm_score = float(llm_score_raw)
                    except (ValueError, TypeError):
                        llm_score = 0.0
                        
                # Keep other scores for now, though they won't be in final_score
                _, _, sma_score, vol_score = score(window_df, pd.DataFrame(), current_price, df["sma50"].iloc[i], df["atr14"].iloc[i], scorer_cfg, components_only=True)
                score_result = {
                    "llm_pattern_score": llm_score,
                    "llm_pattern_description": llm_result.get("pattern_description", ""),
                    "final_score": llm_score, # For LLM, final_score is just the LLM's score
                    "description": llm_result.get("rationale", ""),
                    "sma_score": sma_score,
                    "volatility_score": vol_score,
                }
        else:
             market_window_df = (
                market_regime.iloc[i - cfg.lookback_window : i]
                if market_regime is not None
                else pd.DataFrame()
             )
             score_result = score(
                window_df,
                market_window_df,
                current_price,
                df["sma50"].iloc[i],
                df["atr14"].iloc[i],
                scorer_cfg,
            )

        log_entry = {"date": current_date.strftime("%Y-%m-%d"), "price": current_price, **df.iloc[i].to_dict(), **score_result}
        daily_logs.append(log_entry)

        if score_result["final_score"] >= cfg.score_threshold:
            risk_params = calculate_risk_parameters(current_price, df["atr14"].iloc[i])
            trade_outcome = _get_trade_outcome(df, i, risk_params, cfg)
            trade_entry = {
                "entry_date": current_date.strftime("%Y-%m-%d"),
                "entry_price": round(current_price, 2),
                "pattern_score": score_result["final_score"],
                "pattern_desc": score_result["description"],
                **risk_params,
                **trade_outcome,
            }
            # Add relevant scores based on which scorer was used
            if cfg.scorer_type == "llm":
                trade_entry["llm_pattern_score"] = score_result.get("llm_pattern_score", 0.0)
                trade_entry["llm_pattern_description"] = score_result.get("llm_pattern_description", "")
            else:
                trade_entry["relative_strength_score"] = score_result.get("relative_strength_score", 0.0)
                trade_entry["volume_score"] = score_result.get("volume_score", 0.0)

            trade_entry["sma_score"] = score_result.get("sma_score", 0.0)
            trade_entry["volatility_score"] = score_result.get("volatility_score", 0.0)

            trades.append(trade_entry)
    return trades, daily_logs


# impure
def _save_results(
    trades: List[Dict[str, Any]], daily_logs: List[Dict[str, Any]], ticker_name: str, scorer_type: str
) -> None:
    """Saves trade results and daily logs to CSV files."""
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    trade_output_path = results_dir / f"results_{ticker_name}.csv"

    if trades:
        pd.DataFrame(trades).to_csv(trade_output_path, index=False)
        print(f"Found {len(trades)} trades. Results saved to {trade_output_path}")
    else:
        print("No trades triggered.")
        # Ensure empty file has the correct headers for downstream processing
        base_cols = [
            "entry_date", "entry_price", "pattern_score", "pattern_desc",
            "sma_score", "volatility_score",
            "stop_loss", "take_profit", "outcome", "forward_return_pct"
        ]
        if scorer_type == "llm":
            scorer_cols = ["llm_pattern_score", "llm_pattern_description"]
        else:
            scorer_cols = ["relative_strength_score", "volume_score"]
        pd.DataFrame(columns=base_cols + scorer_cols).to_csv(trade_output_path, index=False)

    if daily_logs:
        log_dir = Path("results/runs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_output_path = log_dir / f"{ticker_name}.run_log.csv"
        pd.DataFrame(daily_logs).to_csv(log_output_path, index=False, float_format="%.2f")
        print(f"Daily run log saved to {log_output_path}")


# impure
def main() -> None:
    """Main function to parse arguments and run the backtester."""
    parser = argparse.ArgumentParser(description="Emergent Alpha Backtester")
    parser.add_argument(
        "--ticker", type=str, required=True, help="Path to the ticker CSV file."
    )
    parser.add_argument(
        "--scorer",
        type=str,
        default="deterministic",
        choices=["deterministic", "llm"],
        help="Scoring model to use (default: deterministic)."
    )
    parser.add_argument(
        "--lookback", type=int, default=40, help="Lookback window size (default: 40)."
    )
    args = parser.parse_args()

    ticker_name = Path(args.ticker).stem
    bt_config = BacktestConfig(
        scorer_type=args.scorer,
        lookback_window=args.lookback
    )
    scorer_config = ScorerConfig()

    trades, daily_logs = run_backtest(args.ticker, bt_config, scorer_config)
    _save_results(trades, daily_logs, ticker_name, args.scorer)


if __name__ == "__main__":
    # To use the LLM scorer, you need to set the OPENROUTER_API_KEY in a .env file
    # e.g.: OPENROUTER_API_KEY="your-key"
    main()
