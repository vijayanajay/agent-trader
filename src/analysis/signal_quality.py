"""
Analyzes the quality of trade signals by correlating trade outcomes with
daily scorer metrics from the backtest run log.

This script merges the trade results with the detailed daily logs and provides
a statistical summary of key metrics for each trade outcome category (e.g.,
TAKE_PROFIT_HIT, STOP_LOSS_HIT). This helps identify which scorer components
are correlated with successful or failed trades.
"""
import argparse
import sys
from typing import Dict, List, Union

import pandas as pd
from rich.console import Console
from rich.table import Table

__all__: List[str] = ["analyze_signal_quality"]


def analyze_signal_quality(
    results_df: pd.DataFrame, log_df: pd.DataFrame
) -> Dict[str, pd.DataFrame]:
    """
    Merges trade results with daily logs and computes descriptive statistics.

    Args:
        results_df: DataFrame of trade outcomes, must contain 'entry_date' and 'outcome'.
        log_df: DataFrame of daily logs, must contain 'date', 'price', 'atr14',
                and scorer component columns (e.g., 'return_score').

    Returns:
        A dictionary where keys are trade outcomes and values are DataFrames
        containing the statistical summary for that outcome.
    """
    if results_df.empty or log_df.empty:
        return {}

    # Ensure date columns are in the same format for merging
    results_df["entry_date"] = pd.to_datetime(results_df["entry_date"])
    log_df["date"] = pd.to_datetime(log_df["date"])

    # Merge trades with daily logs on the entry date
    merged_df = pd.merge(
        results_df, log_df, left_on="entry_date", right_on="date", how="inner"
    )

    if merged_df.empty:
        return {}

    # Calculate normalized volatility
    merged_df["atr_pct"] = (merged_df["atr14"] / merged_df["price"]) * 100

    # Identify columns for statistical analysis
    analysis_cols = [
        "relative_strength_score",
        "volume_score",
        "sma_score",
        "volatility_score",
        "atr_pct",
    ]
    # Filter out columns that might not exist in the merged_df
    existing_analysis_cols = [col for col in analysis_cols if col in merged_df.columns]

    if not existing_analysis_cols:
        return {}

    # Group by outcome and get descriptive statistics for each group
    grouped = merged_df.groupby("outcome")

    analysis_by_outcome = {}
    for name, group in grouped:
        # describe() on the subgroup gives a clean summary DataFrame
        stats = group[existing_analysis_cols].describe().round(2)
        analysis_by_outcome[str(name)] = stats

    return analysis_by_outcome


# impure
def _print_analysis_tables(
    analysis_by_outcome: Dict[str, pd.DataFrame], console: Console
) -> None:
    """Prints formatted summary tables for each trade outcome."""
    if not analysis_by_outcome:
        console.print("[yellow]No common trades found to analyze.[/yellow]")
        return

    for outcome, stats_df in analysis_by_outcome.items():
        # The stats_df now has a simple index ('count', 'mean', etc.)
        table = Table(
            title=f"[bold green]{outcome} Analysis[/bold green]",
            caption=f"Descriptive statistics for trades resulting in {outcome}",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Metric", style="cyan")

        # Add columns for each of the stats returned by .describe()
        for col in stats_df.columns:
            table.add_column(str(col))

        # Add rows for each statistical metric (mean, std, etc.)
        for metric, row in stats_df.iterrows():
            table.add_row(str(metric), *[f"{val:.2f}" for val in row.values])

        console.print(table)


def write_analysis_csv(analysis_by_outcome: Dict[str, pd.DataFrame], out_path: str) -> None:
    """Write the analysis_by_outcome into a single long-form CSV.

    The output will have columns: outcome, metric (count, mean, std, ...),
    feature (e.g., return_score), and value.
    """
    if not analysis_by_outcome:
        return

    rows = []
    for outcome, stats_df in analysis_by_outcome.items():
        # stats_df: index is metric (count, mean, etc.), columns are features
        for metric in stats_df.index:
            for feature in stats_df.columns:
                val = stats_df.at[metric, feature]
                rows.append({"outcome": outcome, "metric": metric, "feature": feature, "value": val})

    out_df = pd.DataFrame(rows)
    # Pivot to have one row per (outcome, feature) and metric columns
    pivot = out_df.pivot_table(index=["outcome", "feature"], columns="metric", values="value").reset_index()
    # flatten columns
    pivot.columns.name = None
    pivot.to_csv(out_path, index=False)



# impure
def main() -> None:
    """
    CLI entry point to run the signal quality analysis.
    """
    parser = argparse.ArgumentParser(description="Analyze trade signal quality.")
    parser.add_argument(
        "--results",
        type=str,
        required=True,
        help="Path to the backtest results CSV file (e.g., results.csv).",
    )
    parser.add_argument(
        "--log",
        type=str,
        required=True,
        help="Path to the backtest run log CSV file (e.g., run_log.csv).",
    )
    args = parser.parse_args()
    console = Console()

    try:
        results_df = pd.read_csv(args.results)
        log_df = pd.read_csv(args.log)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error: File not found.[/bold red]")
        console.log(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error reading CSV files.[/bold red]")
        console.log(f"Details: {e}")
        sys.exit(1)

    if "outcome" not in results_df.columns:
        console.print(
            "[bold red]Error: 'outcome' column not found in results file.[/bold red]"
        )
        console.print(
            "The results file must contain a column named 'outcome' with "
            "trade results (e.g., 'TAKE_PROFIT_HIT')."
        )
        sys.exit(1)

    analysis_by_outcome = analyze_signal_quality(results_df, log_df)
    _print_analysis_tables(analysis_by_outcome, console)

    # Default output path: results/signal_quality_<RESULTS_BASENAME>.csv
    try:
        import os

        results_base = os.path.splitext(os.path.basename(args.results))[0]
        default_out = os.path.join("results", f"signal_quality_{results_base}.csv")
        write_analysis_csv(analysis_by_outcome, default_out)
        console.print(f"[green]Wrote analysis CSV to:[/green] {default_out}")
    except Exception as e:
        console.print(f"[yellow]Warning: failed to write analysis CSV: {e}[/yellow]")


if __name__ == "__main__":
    main()
