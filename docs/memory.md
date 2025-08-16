# Memory

This document records issues, resolutions, and insights gained during the development of "Emergent Alpha" to prevent repeating mistakes.

## 2025-08-15: `yfinance` Data Formatting

- **Issue:** The `yfinance.download()` function returns a pandas DataFrame with a multi-level column header (e.g., `('Close', 'RELIANCE.NS')`). When saved directly to CSV, this creates a malformed header that is difficult to parse.
- **Resolution:** After saving the initial download to a temporary CSV, read it back into pandas using `pd.read_csv(..., header=[0, 1])`, which correctly interprets the multi-level header. Then, drop the unnecessary level (`df.columns = df.columns.droplevel(1)`), select the required columns, and save the cleaned DataFrame to the final destination. This ensures a clean, single-header CSV.
- **Insight:** Always be explicit about data formats. What you see in a DataFrame is not always what you get in a CSV if headers are complex. A two-step save/load process is a robust way to clean the data.

## 2025-08-15: `mypy` strictness with `get_loc`

- **Issue:** `mypy --strict` fails on `df.index.get_loc()` because it can return a slice or a boolean array, not just an `int`, if the index contains duplicate labels. This would cause a runtime error on any subsequent arithmetic.
- **Resolution:** Added an `isinstance(date_loc, int)` check immediately after the `get_loc` call. If the check fails, raise a `ValueError` to prevent the program from continuing with an unexpected type.
- **Insight:** Trust the strict type checker. It often reveals valid, if unlikely, edge cases that should be handled explicitly for more robust code. Asserting assumptions about types makes the code safer.

## 2025-08-15: Documentation Mismatch for File Paths

- **Issue:** `docs/tasks.md` specified that new modules like `data_preprocessor` and `risk_manager` should be placed in a `src/utils/` directory. However, `docs/architecture.md` (in the MVP section) and the existing project structure place these modules directly in `src/`.
- **Resolution:** Followed the existing project structure and the `architecture.md` specification, as they represent the implemented reality. The code was kept in `src/` without the `utils/` subdirectory.
- **Insight:** When documentation conflicts, the architecture document and the existing, working code should take precedence over a task list, which may contain outdated plans. The inconsistency should be noted and resolved in the documentation later.
