"""
fetch_ohlcv.py

Download OHLCV CSV files for tickers listed in config/tickers.json using yfinance.
Supports dry-run (no network), simple retries, and per-ticker overrides.

Usage:
  python scripts/fetch_ohlcv.py --config config/tickers.json [--dry-run]

This script is intended for local use and need not be committed to GitHub.
"""

import argparse
import json
import os
import time
from pathlib import Path

# We'll import yfinance lazily so the script can be syntax-checked without the library installed.

RETRIES = 2
RETRY_DELAY = 1.0


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def download_ticker(symbol, interval, period, start, end, output_path, dry_run=False):
    filename = Path(output_path) / f"{symbol}.csv"
    print(f"-> {symbol}: interval={interval} period={period} start={start} end={end} -> {filename}")
    if dry_run:
        return True

    try:
        import yfinance as yf
    except Exception as e:
        print("yfinance not available. Install with: pip install yfinance")
        return False

    for attempt in range(1, RETRIES + 1):
        try:
            # Use yf.Ticker.history for precise control
            ticker = yf.Ticker(symbol)
            if start or end:
                df = ticker.history(interval=interval, start=start, end=end)
            else:
                df = ticker.history(interval=interval, period=period)

            if df is None or df.empty:
                print(f"Warning: no data for {symbol}")
                return False

            # Ensure columns include Open/High/Low/Close/Volume
            df = df.loc[:, [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]]
            df.to_csv(filename, index=True)
            print(f"Saved {filename} ({len(df)} rows)")
            return True
        except Exception as e:
            print(f"Attempt {attempt} failed for {symbol}: {e}")
            if attempt < RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return False


def main():
    parser = argparse.ArgumentParser(description="Fetch OHLCV using yfinance based on a ticker config file")
    parser.add_argument("--config", default="config/tickers.json", help="Path to ticker config JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without downloading")
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"Config file not found: {cfg_path}")
        return 2

    cfg = load_config(cfg_path)
    defaults = cfg.get("defaults", {})
    output_dir = defaults.get("output_dir", "data/ohlcv")
    ensure_dir(output_dir)

    tickers = cfg.get("tickers", [])
    normalized = []
    for t in tickers:
        if isinstance(t, str):
            normalized.append({"symbol": t})
        elif isinstance(t, dict):
            normalized.append(t)

    success = True
    # Always download the NIFTY 50 index as it's required for the regime filter
    print("\nFetching required market index (^NSEI)...")
    nifty_defaults = defaults.copy()
    nifty_ok = download_ticker(
        symbol="^NSEI",
        interval=nifty_defaults.get("interval", "1d"),
        period=nifty_defaults.get("period", "10y"),
        start=None,
        end=None,
        output_path=output_dir,
        dry_run=args.dry_run
    )
    if not nifty_ok:
        print("Warning: Failed to download ^NSEI data. Backtester regime filter may not work.")
        success = False


    print("\nFetching tickers from config...")
    for t in normalized:
        symbol = t.get("symbol") or t.get("ticker") or next(iter(t.values()))
        interval = t.get("interval", defaults.get("interval"))
        period = t.get("period", defaults.get("period"))
        start = t.get("start")
        end = t.get("end")
        out = t.get("output_dir", output_dir)
        ensure_dir(out)
        # Only allow Indian tickers (basic check: .NS or .BO suffix)
        if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
            print(f"Skipping non-Indian ticker: {symbol}")
            continue # This is not a failure, just a skip.

        ok = download_ticker(symbol, interval, period, start, end, out, dry_run=args.dry_run)
        if not ok:
            success = False # A failure to download a listed ticker is a failure.

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
