import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, cast

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from openai import OpenAI

# --- CONFIGURATION ---

# Load environment variables from .env file
load_dotenv()

# Get API key and model from environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "undi95/kimi-2")

# --- LLM CLIENT ---

# impure
def get_llm_client() -> ChatOpenAI:
    """
    Initializes and returns the LangChain-compatible ChatOpenAI client
    configured for OpenRouter.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

    return ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.5,
        max_tokens=2048,
    )



__all__ = ["get_llm_client"]
