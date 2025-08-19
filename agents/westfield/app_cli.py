"""
CLI interface for Westfield Agent using ADK
"""

import os
import sys
from pathlib import Path
import logging
from typing import Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.westfield.agent import chat_with_agent
from agents.westfield.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main CLI interface for Westfield Agent."""
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables")
        sys.exit(1)
    
    print("=" * 60)
    print("Westfield Agent - NJ Local Politics Intelligence")
    print("=" * 60)
    print("\nMonitoring Reddit for local political discussions...")
    print("Type 'help' for available commands or 'quit' to exit\n")
    
    session_id = None
    
    while True:
        try:
            # Get user input
            query = input("You: ").strip()
            
            # Handle special commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if query.lower() == 'help':
                print("\nAvailable queries:")
                print("- What are the trending political topics?")
                print("- Search for discussions about [topic]")
                print("- What are people saying about property taxes?")
                print("- Show me recent posts about the school board")
                print("- Update the database with new posts")
                print("- What issues are people discussing in Westfield?")
                print("\nCommands:")
                print("- help: Show this help message")
                print("- clear: Clear conversation history")
                print("- quit: Exit the application\n")
                continue
            
            if query.lower() == 'clear':
                session_id = None
                print("Conversation history cleared.\n")
                continue
            
            if not query:
                continue
            
            # Send to agent
            print("\nAgent: ", end="", flush=True)
            response = chat_with_agent(query, session_id)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit.\n")
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\nError occurred: {e}\n")


if __name__ == "__main__":
    main()