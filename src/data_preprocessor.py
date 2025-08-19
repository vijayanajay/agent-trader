# -*- coding: utf-8 -*-
import pandas as pd

__all__ = ["preprocess_data", "format_data_for_llm"]


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
    atr_period: int,
    normalize_window: bool = False,
) -> pd.DataFrame:
    """
    Calculates all required technical indicators and cleans the DataFrame.

    Args:
        df: The raw OHLCV DataFrame, indexed by Date.
        sma50_period: The period for the 50-day simple moving average.
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


def format_data_for_llm(window_df: pd.DataFrame) -> str:
    """
    Formats the provided DataFrame into a clean, normalized text block for the LLM.
    """
    # Ensure there are 40 days, padding with empty rows if necessary
    if len(window_df) < 40:
        padding_rows = 40 - len(window_df)
        empty_df = pd.DataFrame(
            index=pd.to_datetime(pd.date_range(
                start=window_df.index.min() - pd.Timedelta(days=padding_rows),
                periods=padding_rows
            )),
            columns=window_df.columns
        )
        window_df = pd.concat([empty_df, window_df])

    # Normalize Close and Volume
    close_min, close_max = window_df["Close"].min(), window_df["Close"].max()
    volume_min, volume_max = window_df["Volume"].min(), window_df["Volume"].max()

    # Avoid division by zero if all values are the same
    close_range = close_max - close_min if close_max > close_min else 1
    volume_range = volume_max - volume_min if volume_max > volume_min else 1

    # Use a temporary copy for normalization calculations
    temp_df = window_df.copy()
    temp_df["norm_close"] = ((temp_df["Close"] - close_min) / close_range) * 100
    temp_df["norm_volume"] = ((temp_df["Volume"] - volume_min) / volume_range) * 100

    data_lines = []
    for date, row in temp_df.iterrows():
        if pd.notna(row['Close']):
            data_lines.append(
                f"Date: {date.strftime('%Y-%m-%d')}, "
                f"Close: {row['Close']:.2f}, "
                f"Norm Close: {row['norm_close']:.0f}, "
                f"Volume: {row['Volume']:,.0f}, "
                f"Norm Vol: {row['norm_volume']:.0f}"
            )
        else:
            # Represent padded rows clearly
            data_lines.append(f"Date: {date.strftime('%Y-%m-%d')}, [no data]")

    return "\n".join(data_lines)
