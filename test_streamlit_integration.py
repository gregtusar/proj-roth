#!/usr/bin/env python3
"""Test script to verify Streamlit-to-ADK integration works properly"""

import sys
import os
sys.path.append('agents/nj_voter_chat_adk')

def test_streamlit_integration():
    try:
        print("=== Testing Streamlit-to-ADK Integration ===")
        
        print("1. Testing import and initialization...")
        from agents.nj_voter_chat_adk.agent import NJVoterChatAgent
        from agents.nj_voter_chat_adk.config import SYSTEM_PROMPT
        print("✓ Successfully imported NJVoterChatAgent and SYSTEM_PROMPT")
        
        print(f"2. System prompt configured: {SYSTEM_PROMPT[:100]}...")
        
        agent = NJVoterChatAgent()
        print("✓ ADK agent initialized successfully")
        
        print("3. Testing direct user prompt delivery (no prepending)...")
        test_prompt = "How many voters are in the database?"
        print(f"Sending prompt: {test_prompt}")
        
        result = agent.chat(test_prompt)
        print(f"✓ Chat result type: {type(result)}")
        print(f"✓ Chat result: {result}")
        
        if "I am ready" in result or "waiting" in result.lower() or "not received" in result.lower():
            print("✗ Agent still not processing prompts correctly")
            print("Response suggests agent didn't receive the actual question")
            return False
        
        if "bigquery_select tool is not configured correctly" in result.lower():
            print("✗ BigQuery tool configuration issue detected")
            return False
        
        print("4. Testing with specific voter data question...")
        result2 = agent.chat('What counties have the most Republican voters?')
        print(f"✓ County query result: {result2}")
        
        if "I am ready" in result2 or "waiting" in result2.lower() or "not received" in result2.lower():
            print("✗ Agent still not processing second prompt correctly")
            print(f"Problematic response: {result2}")
            return False
        
        print("5. Testing with simple question...")
        result3 = agent.chat('Hello, can you help me with voter data?')
        print(f"✓ Simple query result: {result3}")
        
        if "I am ready" in result3 or "waiting" in result3.lower() or "not received" in result3.lower():
            print("✗ Agent still not processing simple prompt correctly")
            return False
        
        print("\n=== Streamlit-to-ADK Integration Tests Passed! ===")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_streamlit_integration()
    sys.exit(0 if success else 1)
