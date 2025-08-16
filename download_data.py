import yfinance as yf
import pandas as pd
import os
from pathlib import Path

# Define the ticker and the output path
TICKER = "RELIANCE.NS"
OUTPUT_DIR = Path("data/ohlcv")
OUTPUT_PATH = OUTPUT_DIR / f"{TICKER}.sample.csv"
TEMP_PATH = OUTPUT_DIR / f"{TICKER}.tmp.csv"

def download_sample_data(ticker: str, output_path: Path, temp_path: Path):
    """
    Downloads ~120 days of sample OHLCV data for a given ticker
    and saves it to a CSV file.
    """
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Download 6 months of data to ensure we have at least 120 trading days
    data = yf.download(ticker, period="6mo", auto_adjust=False)

    # Take last 120 rows
    sample_data = data.tail(120).copy()

    # Save to a temporary csv file
    sample_data.to_csv(temp_path)

    # Read the temporary file back, skipping the problematic headers
    df = pd.read_csv(temp_path, header=[0, 1], index_col=0)

    # Flatten the multi-level column index
    df.columns = df.columns.droplevel(1)

    # Select and rename columns
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df.index.name = 'Date'

    # Save the cleaned data
    df.to_csv(output_path)

    # Clean up the temporary file
    os.remove(temp_path)

    print(f"Successfully created sample data for {ticker} at {output_path}")

if __name__ == "__main__":
    download_sample_data(TICKER, OUTPUT_PATH, TEMP_PATH)
