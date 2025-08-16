"""
Calculates and prints performance metrics from a trade results CSV.

This script reads a CSV file containing trade results and computes:
- Total trades
- Win rate
- Profit factor

The results are printed to the console in a formatted table.
"""
import argparse
import sys
from typing import Dict, List, Union

import pandas as pd
from rich.console import Console
from rich.table import Table

__all__: List[str] = ["analyze_results"]


def analyze_results(results_df: pd.DataFrame) -> Dict[str, Union[int, float]]:
    """
    Analyzes a DataFrame of trade results to calculate key performance metrics.

    Args:
        results_df: DataFrame with a 'return_pct' column.

    Returns:
        A dictionary containing total trades, win rate, and profit factor.
        Returns empty metrics if the DataFrame is empty.
    """
    if results_df.empty:
        return {"total_trades": 0, "win_rate": 0.0, "profit_factor": 0.0}

    total_trades: int = len(results_df)
    winning_trades: pd.Series = results_df[results_df["return_pct"] > 0]["return_pct"]
    losing_trades: pd.Series = results_df[results_df["return_pct"] < 0]["return_pct"]

    win_rate: float = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0.0

    gross_profit: float = winning_trades.sum()
    gross_loss: float = abs(losing_trades.sum())

    profit_factor: float = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
    }


# impure
def main() -> None:
    """
    CLI entry point to read a results CSV and print an analysis summary.
    """
    parser = argparse.ArgumentParser(description="Analyze trade results.")
    parser.add_argument(
        "results_path",
        type=str,
        help="Path to the results CSV file.",
    )
    args = parser.parse_args()

    try:
        results_df: pd.DataFrame = pd.read_csv(args.results_path)
    except FileNotFoundError:
        print(f"Error: File not found at {args.results_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    metrics: Dict[str, Union[int, float]] = analyze_results(results_df)

    console = Console()
    table = Table(title="Backtest Performance Analysis")
    table.add_column("Metric", justify="right", style="cyan", no_wrap=True)
    table.add_column("Value", justify="left", style="magenta")

    table.add_row("Total Trades", str(metrics["total_trades"]))
    table.add_row("Win Rate (%)", f"{metrics['win_rate']:.2f}")
    table.add_row("Profit Factor", f"{metrics['profit_factor']:.2f}")

    console.print(table)


if __name__ == "__main__":
    main()
