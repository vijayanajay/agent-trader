# -*- coding: utf-8 -*-
import pandas as pd

__all__ = ["normalize_window"]


def normalize_window(window_df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes the 'Close' and 'Volume' columns of a DataFrame to a 0-1 scale.

    This is a pure transformation function. It assumes the input DataFrame
    is valid and ready for normalization.

    Args:
        window_df: A DataFrame containing 'Close' and 'Volume' columns.

    Returns:
        The DataFrame with added 'close_normalized' and 'volume_normalized' cols.
    """
    df = window_df.copy()

    # Normalize 'Close'
    close_min = df["Close"].min()
    close_max = df["Close"].max()
    if close_max > close_min:
        df["close_normalized"] = (df["Close"] - close_min) / (
            close_max - close_min
        )
    else:
        df["close_normalized"] = 0.5  # Neutral value if price is flat

    # Normalize 'Volume'
    volume_min = df["Volume"].min()
    volume_max = df["Volume"].max()
    if volume_max > volume_min:
        df["volume_normalized"] = (df["Volume"] - volume_min) / (
            volume_max - volume_min
        )
    else:
        df["volume_normalized"] = 0.0  # No volume surge if volume is flat

    return df
