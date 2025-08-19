from textwrap import dedent

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

__all__ = ["PATTERN_ANALYSER_PROMPT"]
