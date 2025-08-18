from textwrap import dedent
from typing import List

import pandas as pd
from crewai import Agent
from langchain_openai import ChatOpenAI

# --- AGENT PROMPT ---

PATTERN_ANALYSER_PROMPT = dedent(
    """\
    You are an expert quantitative analyst specializing in identifying emergent
    patterns in financial time-series data. Your task is to analyze the
    provided 40-day data for a stock and assess the likelihood of a
    significant price increase over the next 20 days.

    **Instructions:**
    1.  **Avoid Technical Jargon:** Do NOT use names like "Head and Shoulders,"
        "Cup and Handle," or "Flag." Instead, describe the behavior you
        observe in plain language.
    2.  **Focus on Price & Volume Dynamics:** Describe the relationship between
        price movement and volume. For example: "Price is consolidating in a
        tight range on decreasing volume," or "Price is showing strong upward
        momentum with consistently high volume."
    3.  **Provide a Score:** Based on your analysis, provide a
        "Pattern Strength Score" from 0 (very bearish) to 10 (very bullish)
        for a 20-day forward outlook.
    4.  **Justify Your Score:** Provide a brief, clear rationale for your score.

    **Data Provided:**
    {formatted_data}

    **Required Output Format (JSON):**
    {{
      "pattern_description": "Your detailed description of the price and volume behavior.",
      "pattern_strength_score": <Your score from 0 to 10>,
      "rationale": "Your justification for the score."
    }}
"""
)

# --- DATA FORMATTING ---

def format_data_for_llm(window_df: pd.DataFrame) -> str:
    """
    Formats the provided DataFrame into a clean, normalized text block.
    """
    if len(window_df) != 40:
        padding = 40 - len(window_df)
        window_df = pd.concat([pd.DataFrame([[None] * len(window_df.columns)], columns=window_df.columns, index=[None] * padding), window_df])

    close_min, close_max = window_df["Close"].min(), window_df["Close"].max()
    volume_min, volume_max = window_df["Volume"].min(), window_df["Volume"].max()

    close_range = close_max - close_min if close_max > close_min else 1
    volume_range = volume_max - volume_min if volume_max > volume_min else 1

    window_df = window_df.copy()
    window_df["norm_close"] = ((window_df["Close"] - close_min) / close_range) * 100
    window_df["norm_volume"] = ((window_df["Volume"] - volume_min) / volume_range) * 100

    data_lines: List[str] = []
    for _, row in window_df.iterrows():
        if pd.notna(row['Close']):
            data_lines.append(
                f"Date: {row.name.strftime('%Y-%m-%d')}, "
                f"Close: {row['Close']:.2f}, "
                f"Norm Close: {row['norm_close']:.0f}, "
                f"Volume: {row['Volume']:,.0f}, "
                f"Norm Vol: {row['norm_volume']:.0f}"
            )
    return "\n".join(data_lines)


# --- AGENT DEFINITION ---

def create_pattern_analyser_agent(llm_client: ChatOpenAI) -> Agent:
    """
    Creates the Pattern Analyser agent with its specific prompt and LLM.
    """
    return Agent(
        role="Expert Quantitative Analyst",
        goal=dedent(
            """\
            Analyze 40-day stock data to identify emergent patterns and assess
            the 20-day forward outlook."""
        ),
        backstory=dedent(
            """\
            You are a seasoned quantitative analyst, trained to see signals in
            the noise of financial markets. You ignore common technical jargon,
            focusing instead on the fundamental dynamics of price, volume, and
            momentum. Your analysis is prized for its clarity and objectivity."""
        ),
        llm=llm_client,
        allow_delegation=False,
        verbose=True,  # Set to True for debugging
        tools=[],
    )

__all__ = ["create_pattern_analyser_agent", "PATTERN_ANALYSER_PROMPT", "format_data_for_llm"]
