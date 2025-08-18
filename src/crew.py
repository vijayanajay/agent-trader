import json
from typing import Any, Dict, cast

import pandas as pd
from crewai import Crew, Task

from src.adapters.llm import get_llm_client
from src.agents.pattern_analyser import create_pattern_analyser_agent


# impure
def run_crew_analysis(data_window: pd.DataFrame) -> Dict[str, Any]:
    """
    Initializes and runs the crew for a given data window, returning the
    parsed JSON result from the LLM.
    """
    if not isinstance(data_window, pd.DataFrame) or data_window.empty:
        raise ValueError("A valid data_window DataFrame must be provided.")

    # 1. Get LLM client
    llm_client = get_llm_client()

    # 2. Create the agent
    analyst_agent = create_pattern_analyser_agent(llm_client)

    # 3. Define the analysis task. The tool will format the data.
    # The `description` provides the context for the task.
    analysis_task = Task(
        description=(
            "Use the provided tool to format the 40-day data window. "
            "Then, analyze the formatted data to identify emergent patterns "
            "and assess the 20-day forward outlook."
        ),
        expected_output=(
            "A single JSON object with three keys: 'pattern_description', "
            "'pattern_strength_score', and 'rationale'."
        ),
        agent=analyst_agent,
        tools=analyst_agent.tools,
    )

    # 4. Assemble and run the crew
    crew = Crew(
        agents=[analyst_agent],
        tasks=[analysis_task],
        verbose=0,  # Set to 0 for production, 2 for debugging
    )

    # The `window_df` is passed as input, which the tool will use.
    result = crew.kickoff(inputs={"window_df": data_window})
    if not result:
        return {"error": "No response from crew"}

    # The result from kickoff should be the raw JSON string from the LLM.
    if isinstance(result, str):
        try:
            return cast(Dict[str, Any], json.loads(result))
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response from LLM",
                "response": result,
            }
    # If the LLM client already parsed it (e.g., via response_format),
    # it might be a dict.
    elif isinstance(result, dict):
        return result

    return {
        "error": "Unexpected response type from crew",
        "response": str(result),
    }


__all__ = ["run_crew_analysis"]
