# Memory

This document records issues, resolutions, and insights gained during the development of "Emergent Alpha" to prevent repeating mistakes.

## 2025-08-15: `yfinance` Data Formatting

- **Issue:** The `yfinance.download()` function returns a pandas DataFrame with a multi-level column header (e.g., `('Close', 'RELIANCE.NS')`). When saved directly to CSV, this creates a malformed header that is difficult to parse.
- **Resolution:** After saving the initial download to a temporary CSV, read it back into pandas using `pd.read_csv(..., header=[0, 1])`, which correctly interprets the multi-level header. Then, drop the unnecessary level (`df.columns = df.columns.droplevel(1)`), select the required columns, and save the cleaned DataFrame to the final destination. This ensures a clean, single-header CSV.
- **Insight:** Always be explicit about data formats. What you see in a DataFrame is not always what you get in a CSV if headers are complex. A two-step save/load process is a robust way to clean the data.
