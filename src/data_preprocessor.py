# impure
from typing import Dict, Any
import pandas as pd

__all__ = ["preprocess"]

def _calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates the Average True Range (ATR)."""
    high_low = data["High"] - data["Low"]
    high_close = (data["High"] - data["Close"].shift()).abs()
    low_close = (data["Low"] - data["Close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    return atr

def preprocess(
    csv_path: str, current_date: str, window: int = 40
) -> Dict[str, Any]:
    """
    Loads and preprocesses stock data from a CSV file for a given date.

    Args:
        csv_path: Path to the OHLCV CSV file.
        current_date: The date for analysis (YYYY-MM-DD).
        window: The lookback window size.

    Returns:
        A dictionary containing the preprocessed data.

    Raises:
        FileNotFoundError: If the csv_path does not exist.
        ValueError: If current_date is not in the data or not enough data exists.
    """
    try:
        df = pd.read_csv(csv_path, parse_dates=["Date"], index_col="Date")
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    df.sort_index(inplace=True)

    try:
        date_loc = df.index.get_loc(pd.to_datetime(current_date))
    except KeyError:
        raise ValueError(f"Date {current_date} not found in the data.")

    if not isinstance(date_loc, int):
        raise ValueError(
            f"Date {current_date} is not unique. Please clean the data."
        )

    if date_loc < window - 1:
        raise ValueError(
            f"Not enough data for a {window}-day window on {current_date}."
        )

    # --- Calculations on the full dataset before slicing the window ---
    sma50 = df["Close"].rolling(window=50).mean()
    sma200 = df["Close"].rolling(window=200).mean()
    atr14 = _calculate_atr(df, period=14)

    # --- Slice the window ---
    start_loc = date_loc - window + 1
    window_df = df.iloc[start_loc : date_loc + 1].copy()

    # --- Normalize Close and Volume in the window ---
    close_min = window_df["Close"].min()
    close_max = window_df["Close"].max()
    window_df["close_normalized"] = (window_df["Close"] - close_min) / (
        close_max - close_min
    )

    volume_min = window_df["Volume"].min()
    volume_max = window_df["Volume"].max()
    window_df["volume_normalized"] = (window_df["Volume"] - volume_min) / (
        volume_max - volume_min
    )

    current_price = df.loc[pd.to_datetime(current_date), "Close"]

    return {
        "window_df": window_df,
        "sma50": sma50.loc[pd.to_datetime(current_date)],
        "sma200": sma200.loc[pd.to_datetime(current_date)],
        "atr14": atr14.loc[pd.to_datetime(current_date)],
        "current_price": current_price,
    }
