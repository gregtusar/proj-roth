#!/usr/bin/env python3
"""Test the Google Search integration with the NJ Voter Chat agent."""

import os
import sys

# Set up environment
os.environ["GOOGLE_SEARCH_API_KEY"] = "AIzaSyAgF90DnYRfBlTAppH3Unv2vK5yrav5Pzw"
os.environ["GOOGLE_SEARCH_ENGINE_ID"] = "91907e5365c574113"

# Add parent path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from agents.nj_voter_chat_adk.agent import NJVoterChatAgent

print("=" * 60)
print("Testing NJ Voter Chat Agent with Google Search")
print("=" * 60)
print()

# Initialize agent
print("Initializing agent...")
agent = NJVoterChatAgent()
print()

# Test queries
test_queries = [
    "Who is the current governor of New Jersey?",
    "What are the latest NJ election results?",
    "Tell me about Phil Murphy"
]

for query in test_queries:
    print(f"Query: {query}")
    print("-" * 40)
    
    try:
        response = agent.chat(query)
        print(f"Response: {response[:500]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    print()

print("=" * 60)
print("Test complete!")
print("=" * 60)