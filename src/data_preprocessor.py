# -*- coding: utf-8 -*-
import pandas as pd

__all__ = ["preprocess_data"]


def _calculate_atr(df: pd.DataFrame, period: int) -> pd.Series:
    """
    Calculates the Average True Range (ATR) using a simple rolling mean.
    Note: Wilder's smoothing is a common alternative but a simple moving average
    is used here for simplicity and to align with the project's MVP philosophy.
    """
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(
        axis=1, skipna=False
    )
    return tr.rolling(window=period).mean()


def preprocess_data(
    df: pd.DataFrame,
    sma50_period: int,
    sma200_period: int,
    atr_period: int,
    normalize_window: bool = False,
) -> pd.DataFrame:
    """
    Calculates all required technical indicators and cleans the DataFrame.

    Args:
        df: The raw OHLCV DataFrame, indexed by Date.
        sma50_period: The period for the 50-day simple moving average.
        sma200_period: The period for the 200-day simple moving average.
        atr_period: The period for the Average True Range.
        normalize_window: If True, normalizes Close and Volume to a 0-1 scale.

    Returns:
        A DataFrame with calculated indicators and NaN rows dropped.
    """
    processed_df = df.copy()
    processed_df.sort_index(inplace=True)
    processed_df["sma50"] = (
        processed_df["Close"].rolling(window=sma50_period).mean()
    )
    processed_df["sma200"] = (
        processed_df["Close"].rolling(window=sma200_period).mean()
    )
    processed_df["atr14"] = _calculate_atr(processed_df, atr_period)
    processed_df["pct_change"] = processed_df["Close"].pct_change()

    if normalize_window:
        close_min = processed_df["Close"].min()
        close_max = processed_df["Close"].max()
        volume_min = processed_df["Volume"].min()
        volume_max = processed_df["Volume"].max()

        processed_df["close_norm"] = (processed_df["Close"] - close_min) / (
            close_max - close_min
        )
        processed_df["volume_norm"] = (processed_df["Volume"] - volume_min) / (
            volume_max - volume_min
        )

    # Drop rows with NaNs from indicator calculations
    processed_df.dropna(inplace=True)
    return processed_df
