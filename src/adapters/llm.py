import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import httpx

# --- KAILASH NADH APPROACH: EXPLICITLY CONTROL PROBLEMATIC PARAMETERS ---

# Apply patches immediately when this module is imported
def _apply_patches():
    """Apply all necessary patches using Kailash Nadh's approach of explicitly controlling problematic parameters."""
    
    # Fix 1: Patch httpx clients to handle proxies correctly
    # This fixes the "Client.__init__() got an unexpected keyword argument 'proxies'" error
    try:
        # Store original methods
        original_client_init = httpx.Client.__init__
        original_async_client_init = httpx.AsyncClient.__init__
        
        def patched_client_init(self, *args, **kwargs):
            """Remove proxies argument to avoid compatibility issues."""
            kwargs.pop('proxies', None)
            return original_client_init(self, *args, **kwargs)
        
        def patched_async_client_init(self, *args, **kwargs):
            """Remove proxies argument to avoid compatibility issues."""
            kwargs.pop('proxies', None)
            return original_async_client_init(self, *args, **kwargs)
        
        # Apply patches
        httpx.Client.__init__ = patched_client_init
        httpx.AsyncClient.__init__ = patched_async_client_init
    except Exception:
        pass
    
    # Fix 2: Create a mock module to prevent crewai_tools import issues
    # This prevents the "ImportError: cannot import name 'BaseTool' from 'crewai.tools'" error
    # Kailash Nadh approach: Provide exactly what's needed rather than fighting with imports
    try:
        # Check if we need to create a mock to prevent import issues
        if 'crewai.tools' not in sys.modules:
            # Import the module where BaseTool actually exists
            from crewai.tools import tool_usage
            
            # Create a mock module that has BaseTool
            import types
            mock_tools_module = types.ModuleType('crewai.tools')
            mock_tools_module.BaseTool = tool_usage.BaseTool
            
            # Add it to sys.modules to prevent the problematic import
            sys.modules['crewai.tools'] = mock_tools_module
    except Exception:
        pass

# Apply patches immediately
_apply_patches()

# --- CONFIGURATION ---

# Load environment variables from .env file
load_dotenv()

# Get API key and model from environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "moonshotai/kimi-k2:free")

# --- LLM CLIENT ---

# impure
def get_llm_client() -> ChatOpenAI:
    """
    Initializes and returns the LangChain-compatible ChatOpenAI client
    configured for OpenRouter.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

    # The simplest way to configure the client for OpenRouter, avoiding
    # potential version incompatibilities with proxy handling in underlying
    # libraries. OpenRouter recommends setting Referer and X-Title headers.
    return ChatOpenAI(
        model=f"{LLM_MODEL}" if LLM_MODEL else None,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.5,
        max_tokens=2048,
        default_headers={
            "HTTP-Referer": "http://localhost:3000",  # Recommended by OpenRouter
            "X-Title": "Agent Trader",  # Recommended by OpenRouter
        },
    )



__all__ = ["get_llm_client"]
