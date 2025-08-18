import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from src.agents.pattern_analyser import FormatDataForLLMTool
from src.crew import run_crew_analysis

# --- MOCKS ---

from typing import Any, Dict

def mock_kickoff_success(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Mocks a successful crew.kickoff() call."""
    return {
        "pattern_description": "Mocked description.",
        "pattern_strength_score": 8.5,
        "rationale": "Mocked rationale.",
    }

def mock_kickoff_invalid_json(*args: Any, **kwargs: Any) -> str:
    """Mocks a crew.kickoff() call that returns malformed JSON."""
    return '{"pattern_description": "Malformed",,}'

def mock_kickoff_error(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Mocks a crew.kickoff() call that returns an error dictionary."""
    return {"error": "API limit reached"}


# --- TESTS ---

class TestAgentUtils(unittest.TestCase):
    def test_format_data_for_llm(self) -> None:
        """Tests the data formatting tool."""
        tool = FormatDataForLLMTool()
        data = {
            "Close": [100, 101, 102],
            "Volume": [1000, 1100, 900],
        }
        # Create a 40-day dataframe for the test
        df = pd.DataFrame(data)
        padding_df = pd.DataFrame(
            [[None, None]] * 37,
            columns=["Close", "Volume"],
            index=[None] * 37
        )
        test_df = pd.concat([padding_df, df]).reset_index(drop=True)
        test_df.index = pd.to_datetime(test_df.index, unit='D')


        formatted_string = tool._run(window_df=test_df)

        self.assertIsInstance(formatted_string, str)
        self.assertIn("Norm Close:", formatted_string)
        self.assertIn("Norm Vol:", formatted_string)
        # Check if normalization is working (last value should be 100)
        self.assertIn("Norm Close: 100", formatted_string.splitlines()[-1])


class TestCrew(unittest.TestCase):
    def setUp(self) -> None:
        """Prepare a sample DataFrame for tests."""
        self.sample_df = pd.DataFrame({
            'Close': range(100, 140),
            'Volume': range(1000, 1040)
        })
        self.sample_df.index = pd.to_datetime(self.sample_df.index, unit='D')


    @patch("src.crew.get_llm_client")
    @patch("src.crew.Crew")
    def test_run_crew_analysis_success(self, mock_crew: MagicMock, mock_get_llm_client: MagicMock) -> None:
        """Tests the crew analysis runner with a successful LLM response."""
        mock_get_llm_client.return_value = MagicMock()
        mock_crew_instance = mock_crew.return_value
        mock_crew_instance.kickoff.return_value = mock_kickoff_success()

        result = run_crew_analysis(self.sample_df)

        self.assertIn("pattern_strength_score", result)
        self.assertEqual(result["pattern_strength_score"], 8.5)
        self.assertNotIn("error", result)

    @patch("src.crew.get_llm_client")
    @patch("src.crew.Crew")
    def test_run_crew_analysis_invalid_json(self, mock_crew: MagicMock, mock_get_llm_client: MagicMock) -> None:
        """Tests the crew runner with a malformed JSON response."""
        mock_get_llm_client.return_value = MagicMock()
        mock_crew_instance = mock_crew.return_value
        mock_crew_instance.kickoff.return_value = '{"bad json"}'

        result = run_crew_analysis(self.sample_df)

        self.assertIn("error", result)
        self.assertEqual(result["error"], "Invalid JSON response from LLM")

    @patch("src.crew.get_llm_client")
    @patch("src.crew.Crew")
    def test_run_crew_analysis_api_error(self, mock_crew: MagicMock, mock_get_llm_client: MagicMock) -> None:
        """Tests the crew runner when the kickoff itself returns an error dict."""
        mock_get_llm_client.return_value = MagicMock()
        mock_crew_instance = mock_crew.return_value
        mock_crew_instance.kickoff.return_value = mock_kickoff_error()

        result = run_crew_analysis(self.sample_df)

        self.assertIn("error", result)
        self.assertEqual(result["error"], "API limit reached")

    def test_run_crew_analysis_invalid_input(self) -> None:
        """Tests that the runner raises an error for invalid input."""
        with self.assertRaises(ValueError):
            run_crew_analysis(pd.DataFrame()) # Empty dataframe
        with self.assertRaises(ValueError):
            run_crew_analysis(None)
