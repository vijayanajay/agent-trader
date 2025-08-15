### **Phase 1: Setup & Data Foundation (Day 1)**

#### **Task 1: Project Initialization & Environment Setup**

*   **Goal:** Create the complete project structure and install all necessary dependencies.
*   **Source:** Architecture Document (Section 2, 6), PRD (Section 6)

*   **Sub-items to Implement:**
    1.  Create the root project directory: `emergent-alpha/`.
    2.  Create the specified sub-directory structure:
        *   `data/`
        *   `data/ohlcv/`
        *   `src/`
        *   `src/agents/`
        *   `results/`
    3.  Set up a Python 3.10+ virtual environment (e.g., using `venv`).
    4.  Install all required packages from the "Chosen Stack": `pandas`, `yfinance`, `langflow`.
    5.  Create a `requirements.txt` file to lock down dependencies.
    6.  Initialize a Git repository and create an initial commit with the directory structure.
    7.  Create a placeholder `NIFTY200_list.csv` file in the `data/` directory and populate it with a list of stock tickers (e.g., `RELIANCE.NS`, `TCS.NS`, etc.).

*   **Acceptance Criteria (AC):**
    *   The directory structure exactly matches the one defined in the Architecture document.
    *   The Python virtual environment is active and all dependencies are installed without errors.
    *   `pip freeze > requirements.txt` successfully creates the file.

*   **Definition of Done (DoD):**
    *   All sub-items are completed.
    *   The initial project structure is committed to version control.

---

#### **Task 2: Data Acquisition Script (`download_data.py`)**

*   **Goal:** Create a reusable script to download all necessary historical stock data.
*   **Source:** PRD (Section 6), Architecture Document (Section 6)

*   **Sub-items to Implement:**
    1.  Create the file `download_data.py` in the project root.
    2.  The script must read the list of tickers from `data/NIFTY200_list.csv`.
    3.  For each ticker in the list:
        *   Use the `yfinance` library to download historical OHLCV data (e.g., for the last 5-10 years to ensure sufficient lookback).
        *   Implement error handling for tickers that might fail to download.
        *   Save the downloaded data as a CSV file in the `data/ohlcv/` directory.
        *   The filename must match the format specified: `{ticker}.csv` (e.g., `RELIANCE.NS.csv`).
    4.  Add print statements to show progress (e.g., "Downloading RELIANCE.NS... Done.").

*   **Acceptance Criteria (AC):**
    *   Running `python download_data.py` executes without errors.
    *   The `data/ohlcv/` directory is populated with CSV files, one for each valid ticker in the list.
    *   Opening a sample CSV (e.g., `TCS.NS.csv`) shows the expected OHLCV data columns.

*   **Definition of Done (DoD):**
    *   The `download_data.py` script is complete, commented, and functional.
    *   All historical data has been successfully downloaded.
    *   The script and the downloaded data (or a `.gitignore` for the data) are committed to version control.

---

### **Phase 2: Core Logic Implementation (Day 1)**

#### **Task 3: Develop Python Agent Logic**

*   **Goal:** Implement the core data processing and risk calculation logic as standalone Python functions.
*   **Source:** PRD (Agents 1 & 4), Architecture Document (Section 4, 6)

*   **Sub-items to Implement:**
    1.  **`Data_Preprocessor` (in `src/agents/data_preprocessor.py`):**
        *   Create a function `preprocess_data(stock_dataframe, current_date)`.
        *   Implement logic to select the last 60 trading days up to `current_date`.
        *   Calculate 50-day SMA, 200-day SMA, and 14-day ATR using the full dataframe for lookback.
        *   Normalize the 60-day window's close prices and volumes to a 0-1 scale.
        *   Format the output string (`preprocessed_data_string`) exactly as required for the LLM prompt.
        *   The function must return three distinct values: `preprocessed_data_string`, `current_price`, `current_atr`.
    2.  **`Risk_Manager` (in `src/agents/risk_manager.py`):**
        *   Create a function `calculate_risk_params(current_price, current_atr)`.
        *   Implement the stop-loss calculation: `current_price - (2 * current_atr)`.
        *   Implement the take-profit calculation: `current_price + (4 * current_atr)`.
        *   The function must return a dictionary matching the JSON schema: `{"stop_loss": value, "take_profit": value}`.
    3.  **Unit Testing:**
        *   Create a simple test script or use `assert` statements to verify that both functions produce the correct output and data types for a known sample input DataFrame.

*   **Acceptance Criteria (AC):**
    *   The `preprocess_data` function correctly calculates all metrics and returns the three specified outputs in their correct formats.
    *   The `calculate_risk_params` function correctly calculates SL/TP and returns a dictionary.
    *   Unit tests pass for both functions.

*   **Definition of Done (DoD):**
    *   Both Python files (`data_preprocessor.py`, `risk_manager.py`) are created and fully implemented.
    *   The code is clean, commented, and committed to version control.

---

#### **Task 4: Finalize All LLM Prompts**

*   **Goal:** Transcribe and refine all LLM prompts, ensuring they adhere to the architectural principles.
*   **Source:** PRD (Section 5), Architecture Document (Section 5)

*   **Sub-items to Implement:**
    1.  Create a central file (e.g., `prompts.md`) or separate text files to store the prompts.
    2.  Finalize the **`Pattern_Analyser`** prompt, ensuring it explicitly forbids jargon and demands a JSON output with `pattern_description`, `pattern_strength_score`, and `rationale`.
    3.  Finalize the **`Market_Context_Analyser`** prompt, ensuring it demands a JSON output with `sector_trend` and `vix_analysis`.
    4.  Finalize the **`Decision_Synthesizer`** prompt, ensuring it includes the strict decision rules and demands a JSON output with `decision`, `confidence_score`, and `summary_rationale`.
    5.  Finalize the **`Feature_Suggester`** prompt for offline use.
    6.  Review every prompt to confirm it follows the principles: Role-Playing, Strict Instructions, and Structured JSON Output.

*   **Acceptance Criteria (AC):**
    *   All four prompts are documented and exactly match the specifications in the PRD.
    *   The JSON output format is explicitly defined within each prompt's text.

*   **Definition of Done (DoD):**
    *   The file(s) containing the final prompts are created and committed to version control.

---

### **Phase 3: Integration & Orchestration (Day 2)**

#### **Task 5: Build and Test the Langflow Workflow**

*   **Goal:** Assemble all components into a functional pipeline in Langflow and expose it as an API.
*   **Source:** Architecture Document (Section 3), PRD (Section 4)

*   **Sub-items to Implement:**
    1.  Start the Langflow server.
    2.  Create a new flow named "Emergent Alpha v1.0".
    3.  Create custom Langflow components for the Python functions from Task 3. This may involve creating a `src/langflow_components.py` file to wrap the agent functions for easy import into Langflow.
    4.  Drag and drop all required nodes onto the canvas, recreating the `Component Interaction Diagram`:
        *   API Input node.
        *   `Data_Preprocessor` custom component.
        *   `Pattern_Analyser` LLM node.
        *   `Market_Context_Analyser` LLM node (and its preceding Python logic for getting context data).
        *   `Risk_Manager` custom component.
        *   `Decision_Synthesizer` LLM node.
        *   API Output node.
    5.  Connect the nodes exactly as shown in the diagram.
    6.  Configure each LLM node with the correct prompt text from Task 4 and connect it to the Kimi 2 (or equivalent) model.
    7.  Test the flow end-to-end using the Langflow UI with sample data to ensure data flows correctly and the final output is a valid JSON.
    8.  Export the final, working flow as `langflow_export.json` and save it in the project root.

*   **Acceptance Criteria (AC):**
    *   The Langflow graph visually and functionally matches the architecture diagram.
    *   Sending a test request via the Langflow API endpoint returns a `200 OK` status and a valid JSON response.
    *   The JSON response schema matches the output defined for the `Decision_Synthesizer`.

*   **Definition of Done (DoD):**
    *   The Langflow workflow is fully assembled, tested, and operational.
    *   The `langflow_export.json` file is saved and committed to version control.

---

### **Phase 4: Backtesting & Validation (Day 2)**

#### **Task 6: Develop the Backtester Script (`backtester.py`)**

*   **Goal:** Create the master script that runs the entire system over historical data and evaluates its performance.
*   **Source:** Architecture Document (Section 6)

*   **Sub-items to Implement:**
    1.  Create the file `backtester.py` in the project root.
    2.  **Initialization:**
        *   Import necessary libraries (`pandas`, `requests`, `os`, `datetime`).
        *   Define the Langflow API endpoint URL.
        *   Load the list of tickers from `data/NIFTY200_list.csv`.
    3.  **Looping Logic:**
        *   Implement the outer loop to iterate through each stock ticker.
        *   Implement the inner loop to iterate through each valid date in the stock's DataFrame (ensuring enough lookback data).
    4.  **API Interaction:**
        *   Inside the loop, slice the DataFrame to get the required data window.
        *   Prepare the JSON payload for the `POST` request to the Langflow API.
        *   Implement the `requests.post()` call within a `try-except` block to handle API errors gracefully.
    5.  **Response Processing:**
        *   Parse the JSON response from the API.
        *   If the `decision` is "BUY", proceed to log the trade.
        *   Calculate the actual 20-day forward return from the historical data.
        *   Determine the trade `outcome` by checking if the `stop_loss` or `take_profit` was hit within the 20-day window.
        *   Append a dictionary containing all trade details (`date`, `ticker`, `entry_price`, `stop_loss`, `take_profit`, `20d_return`, `outcome`, `rationale`) to a results list.
    6.  **Finalization:**
        *   After the loops complete, convert the list of trade dictionaries into a pandas DataFrame.
        *   Generate a timestamped filename (e.g., `backtest_results_20231027_1530.csv`).
        *   Save the results DataFrame to a CSV file in the `results/` directory.
        *   Calculate and print the summary performance metrics (Total Trades, Win Rate, Profit Factor) to the console.

*   **Acceptance Criteria (AC):**
    *   The script runs to completion over the entire dataset without crashing.
    *   A correctly formatted CSV file is generated in the `results/` directory.
    *   The console output displays the final summary performance metrics.

*   **Definition of Done (DoD):**
    *   The `backtester.py` script is fully implemented, commented, and functional.
    *   The script is committed to version control.

---

#### **Task 7: Full System Execution, Analysis, and Review**

*   **Goal:** Run the complete backtest, analyze the results against success metrics, and generate ideas for the next iteration.
*   **Source:** PRD (Section 7), Architecture Document (Section 7)

*   **Sub-items to Implement:**
    1.  Execute `python backtester.py` to run the full backtest on all Nifty 200 stocks.
    2.  Monitor the execution for any recurring errors.
    3.  Once complete, analyze the final `results.csv` file.
    4.  Verify the performance against the PRD's success metrics:
        *   Is the Win Rate > 55%?
        *   Is the Profit Factor > 1.5?
    5.  Perform a qualitative review of 10-15 "BUY" rationales from the results to assess if they are logical.
    6.  Run the `Feature_Suggester` agent by sending its prompt to the LLM and save the output.
    7.  Document the final results and findings in a `README.md` file.

*   **Acceptance Criteria (AC):**
    *   A full backtest run is completed.
    *   The performance metrics are calculated and explicitly compared against the project goals.
    *   The qualitative review of rationales is complete.
    *   A list of suggested features for v1.1 has been generated and saved.

*   **Definition of Done (DoD):**
    *   The project is fully executed, and the results are documented.
    *   The final `results.csv` and the `README.md` with the performance summary are committed to version control.
    *   The project is considered complete for v1.0.