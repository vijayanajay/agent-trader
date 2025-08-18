#!/usr/bin/env python3
"""
Wrapper script to run the backtester with necessary patches applied.
This follows the Kailash Nadh approach of explicitly controlling problematic parameters.
"""
import sys
import types

# Apply patches before any other imports
def apply_patches():
    """Apply all necessary patches before importing other modules."""
    try:
        # Patch 1: Fix httpx proxy issues
        import httpx
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
        
        httpx.Client.__init__ = patched_client_init
        httpx.AsyncClient.__init__ = patched_async_client_init
        
        # Patch 2: Fix crewai.tools import issues
        # Create a mock module that provides what's needed to prevent import errors
        if 'crewai.tools' not in sys.modules:
            from crewai.tools import tool_usage
            
            # Create a mock module
            mock_tools_module = types.ModuleType('crewai.tools')
            
            # Add BaseTool (which exists in tool_usage)
            mock_tools_module.BaseTool = tool_usage.BaseTool
            
            # Add EnvVar (create a simple mock class)
            class EnvVar:
                def __init__(self, *args, **kwargs):
                    pass
            
            mock_tools_module.EnvVar = EnvVar
            
            # Add the mock module to sys.modules
            sys.modules['crewai.tools'] = mock_tools_module
            
    except Exception as e:
        print(f"Warning: Failed to apply patches: {e}", file=sys.stderr)

# Apply patches first
apply_patches()

# Now import and run the backtester
if __name__ == "__main__":
    from backtester import main
    main()