# -*- coding: utf-8 -*-
"""
Adapter for making audited calls to a Large Language Model.
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict

import httpx
from dotenv import load_dotenv

from src.prompts import PATTERN_ANALYSER_PROMPT

__all__ = ["get_llm_analysis"]

# --- CONFIGURATION ---
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "moonshotai/kimi-k2:free")

# --- CONSTANTS ---
PROMPT_VERSION = "1.0"
LLM_API_URL = "https://openrouter.ai/api/v1/chat/completions"
AUDIT_LOG_PATH = Path("results/llm_audit.log")

# Ensure the directory for the audit log exists
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _calculate_prompt_hash(prompt: str) -> str:
    """Calculates a SHA256 hash of the prompt content."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


# impure
def _log_llm_audit(
    prompt: str,
    prompt_hash: str,
    model: str,
    temperature: float,
    response: str,
    token_count: int,
) -> None:
    """
    Logs the LLM call details to a local audit file, per H-22.
    """
    audit_record = {
        "prompt_version": PROMPT_VERSION,
        "prompt_hash": prompt_hash,
        "model": model,
        "temperature": temperature,
        "token_count": token_count,
        "response": response,
        "timestamp": time.time(),
    }
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(audit_record) + "\n")


# impure
def get_llm_analysis(formatted_data: str) -> Dict[str, Any]:
    """
    Calls the LLM with the provided data and returns the parsed JSON response.
    This function is impure as it performs network I/O and writes to a log file.
    """
    if not OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY not found"}

    temperature = 0.2  # Lower temperature for more deterministic, analytical output
    prompt_content = PATTERN_ANALYSER_PROMPT.format(formatted_data=formatted_data)
    prompt_hash = _calculate_prompt_hash(prompt_content)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Emergent Alpha",
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt_content}],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(LLM_API_URL, headers=headers, json=payload)
            response.raise_for_status()

        response_data = response.json()
        raw_response_text = response_data["choices"][0]["message"]["content"]
        token_count = response_data["usage"]["total_tokens"]

        # Log the successful call
        _log_llm_audit(
            prompt=prompt_content,
            prompt_hash=prompt_hash,
            model=str(LLM_MODEL),
            temperature=temperature,
            response=raw_response_text,
            token_count=token_count,
        )

        # Use regex to find the JSON object within the response string
        try:
            # The regex looks for a string that starts with { and ends with }, accounting for nested braces.
            match = re.search(r'\{.*\}', raw_response_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                # Now, clean the extracted string from actual newline characters and escaped quotes
                cleaned_json_str = json_str.replace('\n', ' ').replace('\r', '').replace('\\"', '"')
                return json.loads(cleaned_json_str)
            else:
                 raise json.JSONDecodeError("No JSON object found in response", raw_response_text, 0)
        except json.JSONDecodeError as e:
            error_details = f"Failed to parse LLM response: {e}. Response: {raw_response_text}"
            return {"error": "API_RESPONSE_ERROR", "details": error_details}

    except httpx.HTTPStatusError as e:
        error_details = f"HTTP error: {e.response.status_code} - {e.response.text}"
        return {"error": "API_HTTP_ERROR", "details": error_details}
    except (json.JSONDecodeError, KeyError) as e:
        error_details = f"Failed to parse LLM response: {e}"
        return {"error": "API_RESPONSE_ERROR", "details": error_details}
    except Exception as e:
        error_details = f"An unexpected error occurred: {e}"
        return {"error": "UNKNOWN_API_ERROR", "details": error_details}
