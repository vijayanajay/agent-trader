# -*- coding: utf-8 -*-
import pandas as pd

__all__ = ["preprocess_data"]


def _calculate_atr(df: pd.DataFrame, period: int) -> pd.Series:
    """Calculates the Average True Range (ATR)."""
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(
        axis=1, skipna=False
    )
    return tr.rolling(window=period).mean()


def preprocess_data(
    df: pd.DataFrame, sma_period: int, atr_period: int
) -> pd.DataFrame:
    """
    Calculates all required technical indicators and cleans the DataFrame.

    Args:
        df: The raw OHLCV DataFrame, indexed by Date.
        sma_period: The period for the simple moving average.
        atr_period: The period for the Average True Range.

    Returns:
        A DataFrame with calculated indicators and NaN rows dropped.
    """
    processed_df = df.copy()
    processed_df.sort_index(inplace=True)
    processed_df["sma50"] = processed_df["Close"].rolling(window=sma_period).mean()
    processed_df["atr14"] = _calculate_atr(processed_df, atr_period)

    # Drop rows with NaNs from indicator calculations
    processed_df.dropna(inplace=True)
    return processed_df
