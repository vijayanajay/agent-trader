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
        *   `src/tools/`
        *   `results/`
    3.  Set up a Python 3.10+ virtual environment (e.g., using `venv`).
    4.  Install all required packages from the "Chosen Stack": `pandas`, `yfinance`, `crewai`.
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

#### **Task 3: Develop CrewAI Agents and Tools**

*   **Goal:** Implement the core agent logic and supporting tools using CrewAI framework.
*   **Source:** PRD (Agents 1-5), Architecture Document (Section 4, 6)

*   **Sub-items to Implement:**
    1.  **Data Processing Tools (in `src/tools/data_tools.py`):**
        *   Create a `preprocess_data(stock_dataframe, current_date)` function.
        *   Implement logic to select the last 60 trading days up to `current_date`.
        *   Calculate 50-day SMA, 200-day SMA, and 14-day ATR using the full dataframe for lookback.
        *   Normalize the 60-day window's close prices and volumes to a 0-1 scale.
        *   Format the output string (`preprocessed_data_string`) exactly as required for the LLM prompt.
        *   Create a `calculate_risk_params(current_price, current_atr)` function for stop-loss and take-profit calculations.
    2.  **Market Tools (in `src/tools/market_tools.py`):**
        *   Create functions to fetch sector indices and VIX data using `yfinance`.
        *   Implement sector mapping logic (e.g., "RELIANCE.NS" -> `^CNXENERGY`).
        *   Create trend calculation functions for market context analysis.
    3.  **CrewAI Agents (in `src/agents/`):**
        *   **`data_preprocessor.py`**: Create DataPreprocessor agent with access to data tools.
        *   **`pattern_analyser.py`**: Create PatternAnalyser agent with LLM capability for emergent pattern recognition.
        *   **`market_context_analyser.py`**: Create MarketContextAnalyser agent with market tools and LLM capability.
        *   **`risk_manager.py`**: Create RiskManager agent with risk calculation tools.
        *   **`decision_synthesizer.py`**: Create DecisionSynthesizer agent with LLM capability for final decisions.
    4.  **Agent Configuration:**
        *   Define each agent's role, goal, backstory, and available tools.
        *   Ensure agents have appropriate LLM access where needed.
        *   Configure agents to output structured JSON responses.
    5.  **Unit Testing:**
        *   Create simple test scripts to verify each tool and agent works independently.
        *   Test with known sample data to ensure correct outputs and data types.

*   **Acceptance Criteria (AC):**
    *   All tool functions correctly calculate metrics and return data in the specified formats.
    *   All CrewAI agents are properly configured with roles, goals, and tools.
    *   Each agent can execute independently and produce structured outputs.
    *   Unit tests pass for all tools and agents.

*   **Definition of Done (DoD):**
    *   All Python files in `src/tools/` and `src/agents/` are created and fully implemented.
    *   The code is clean, commented, and follows CrewAI best practices.
    *   All files are committed to version control.

---

#### **Task 4: Finalize Agent Prompts and CrewAI Configuration**

*   **Goal:** Define agent prompts, roles, and goals that integrate seamlessly with CrewAI framework.
*   **Source:** PRD (Section 5), Architecture Document (Section 5)

*   **Sub-items to Implement:**
    1.  **Agent Role Definitions:**
        *   Define clear roles for each agent (e.g., "Expert Quantitative Analyst" for PatternAnalyser).
        *   Create compelling backstories that prime the LLM for the specific task.
        *   Set specific, measurable goals for each agent.
    2.  **Prompt Integration with CrewAI:**
        *   Adapt the **`Pattern_Analyser`** prompt as the agent's goal and expected output format.
        *   Adapt the **`Market_Context_Analyser`** prompt for market analysis tasks.
        *   Adapt the **`Decision_Synthesizer`** prompt with strict decision rules and JSON output requirements.
        *   Ensure all prompts follow CrewAI's agent configuration patterns.
    3.  **Task Definitions:**
        *   Create specific tasks for each agent that clearly define inputs, processing requirements, and expected outputs.
        *   Define task dependencies and execution order.
        *   Ensure tasks output structured JSON for seamless data flow.
    4.  **Agent Communication Protocol:**
        *   Define how agents will pass data between each other.
        *   Establish clear input/output contracts for each agent.
        *   Ensure JSON schema consistency across all agent interactions.
    5.  **Configuration Validation:**
        *   Create a simple script to validate that all agent configurations are properly formatted.
        *   Test that agents can be instantiated without errors.

*   **Acceptance Criteria (AC):**
    *   All five agents have well-defined roles, goals, and backstories.
    *   Agent tasks clearly specify input/output requirements and JSON schemas.
    *   All agents can be instantiated and configured without errors.

*   **Definition of Done (DoD):**
    *   Agent configurations are documented and integrated into the agent classes.
    *   Configuration validation scripts pass successfully.
    *   All agent definitions are committed to version control.

---

### **Phase 3: Integration & Orchestration (Day 2)**

#### **Task 5: Build and Test the CrewAI Workflow**

*   **Goal:** Assemble all agents into a functional crew and test the complete workflow.
*   **Source:** Architecture Document (Section 3), PRD (Section 4)

*   **Sub-items to Implement:**
    1.  **Create Main Crew Configuration (`src/crew.py`):**
        *   Import all agent classes from the agents module.
        *   Import all required tools from the tools module.
        *   Define the main crew with all five agents.
        *   Configure agent assignments and tool access.
    2.  **Define Crew Tasks:**
        *   Create sequential tasks that match the `Component Interaction Diagram`.
        *   Task 1: Data preprocessing with DataPreprocessor agent.
        *   Task 2: Pattern analysis with PatternAnalyser agent.
        *   Task 3: Market context analysis with MarketContextAnalyser agent.
        *   Task 4: Risk calculations with RiskManager agent.
        *   Task 5: Final decision synthesis with DecisionSynthesizer agent.
    3.  **Configure Task Dependencies:**
        *   Ensure proper data flow between tasks.
        *   Set up context sharing between agents.
        *   Define input/output mappings for each task.
    4.  **Crew Execution Logic:**
        *   Create a `process_stock_analysis()` function that takes stock data and date as inputs.
        *   Implement crew.kickoff() with proper input formatting.
        *   Add error handling for crew execution failures.
    5.  **End-to-End Testing:**
        *   Test the complete crew workflow with sample stock data.
        *   Verify that each agent executes in sequence and produces expected outputs.
        *   Validate that the final output matches the Decision_Synthesizer JSON schema.
        *   Test error handling with invalid or missing data.

*   **Acceptance Criteria (AC):**
    *   The CrewAI crew executes all agents in the correct sequence.
    *   Sample crew execution returns a valid JSON response matching the expected schema.
    *   Error handling works correctly for various failure scenarios.

*   **Definition of Done (DoD):**
    *   The `src/crew.py` file is fully implemented and tested.
    *   End-to-end crew execution is successful with sample data.
    *   All crew configuration and test files are committed to version control.

---

### **Phase 4: Backtesting & Validation (Day 2)**

#### **Task 6: Develop the Backtester Script (`backtester.py`)**

*   **Goal:** Create the master script that runs the entire system over historical data and evaluates its performance.
*   **Source:** Architecture Document (Section 6)

*   **Sub-items to Implement:**
    1.  Create the file `backtester.py` in the project root.
    2.  **Initialization:**
        *   Import necessary libraries (`pandas`, `os`, `datetime`) and the CrewAI crew.
        *   Initialize the crew from `src/crew.py`.
        *   Load the list of tickers from `data/NIFTY200_list.csv`.
    3.  **Looping Logic:**
        *   Implement the outer loop to iterate through each stock ticker.
        *   Implement the inner loop to iterate through each valid date in the stock's DataFrame (ensuring enough lookback data).
    4.  **Crew Execution:**
        *   Inside the loop, slice the DataFrame to get the required data window.
        *   Prepare the inputs dictionary for the crew execution.
        *   Implement the `crew.kickoff(inputs={...})` call within a `try-except` block to handle execution errors gracefully.
    5.  **Response Processing:**
        *   Parse the JSON response from the crew execution.
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
    6.  Run the `Feature_Suggester` agent by creating a separate crew or using the agent directly with its prompt.
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