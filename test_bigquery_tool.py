#!/usr/bin/env python3
"""Test script to verify BigQuery tool configuration in ADK agent"""

import sys
import os
sys.path.append('agents/nj_voter_chat_adk')

def test_bigquery_tool():
    try:
        print("=== Testing BigQuery Tool Configuration ===")
        
        print("1. Testing import and initialization...")
        from agents.nj_voter_chat_adk.agent import NJVoterChatAgent
        print("✓ Successfully imported NJVoterChatAgent")
        
        agent = NJVoterChatAgent()
        print("✓ ADK agent initialized successfully")
        
        print("2. Testing BigQuery tool with simple voter count query...")
        test_prompt = "How many voters are in the database?"
        print(f"Sending prompt: {test_prompt}")
        
        result = agent.chat(test_prompt)
        print(f"✓ Chat result type: {type(result)}")
        print(f"✓ Chat result: {result}")
        
        if "bigquery_select tool is not configured correctly" in result.lower():
            print("✗ BigQuery tool still not configured correctly")
            return False
        
        if "error" in result.lower() and "tool" in result.lower():
            print("✗ Tool configuration error detected")
            print(f"Error response: {result}")
            return False
        
        print("3. Testing with specific county query...")
        result2 = agent.chat('How many voters are in Somerset County?')
        print(f"✓ County query result: {result2}")
        
        if "bigquery_select tool is not configured correctly" in result2.lower():
            print("✗ BigQuery tool still not working for county queries")
            return False
        
        print("\n=== BigQuery Tool Tests Passed! ===")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bigquery_tool()
    sys.exit(0 if success else 1)
