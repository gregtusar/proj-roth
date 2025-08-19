"""Suppress known harmless warnings from third-party libraries."""

import warnings
import sys

def suppress_adk_warnings():
    """Suppress known harmless warnings from Google ADK and related libraries."""
    
    # Suppress the specific pydantic warning about config_type in SequentialAgent
    warnings.filterwarnings(
        "ignore",
        message="Field name \"config_type\" in \"SequentialAgent\" shadows an attribute in parent \"BaseAgent\"",
        category=UserWarning,
        module="pydantic._internal._fields"
    )
    
    # Also suppress any other pydantic field shadowing warnings from ADK
    warnings.filterwarnings(
        "ignore",
        message=".*shadows an attribute in parent.*",
        category=UserWarning,
        module="pydantic._internal._fields"
    )
    
    # Suppress deprecation warnings from google.auth if present
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module="google.auth"
    )
    
    # Suppress numpy deprecation warnings that might come from dependencies
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module="numpy"
    )

# Call this function when the module is imported
suppress_adk_warnings()