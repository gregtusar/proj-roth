"""Debug configuration for NJ Voter Chat agent."""

import os

# Control debug output - set to False to disable debug messages
DEBUG_ENABLED = os.environ.get('DEBUG', 'false').lower() == 'true'

def debug_print(message: str):
    """Print debug message only if debugging is enabled."""
    if DEBUG_ENABLED:
        print(message)

def error_print(message: str):
    """Always print error messages."""
    print(message)