import pandas as pd
from pathlib import Path

def test_sample_data_exists_and_is_valid():
    """
    Tests if the sample data CSV exists, has the correct columns,
    and a minimum number of rows.
    """
    sample_data_path = Path("data/ohlcv/RELIANCE.NS.sample.csv")

    # Test 1: File exists
    assert sample_data_path.is_file(), f"Sample data file not found at {sample_data_path}"

    # Test 2: Read CSV and check columns
    try:
        df = pd.read_csv(sample_data_path)
    except Exception as e:
        assert False, f"Failed to read or parse the CSV file: {e}"

    expected_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
    assert all(col in df.columns for col in expected_columns), \
        f"CSV is missing one or more expected columns. Found: {list(df.columns)}"

    # Test 3: Check for minimum number of rows
    assert len(df) >= 60, f"Sample data has only {len(df)} rows, expected at least 60."
