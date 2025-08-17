#!/usr/bin/env python3
"""Test script to verify prompt delivery to ADK agent"""

import sys
import os
sys.path.append('agents/nj_voter_chat_adk')

def test_prompt_delivery():
    try:
        print("=== Testing ADK Agent Prompt Delivery ===")
        
        print("1. Testing import and initialization...")
        from agents.nj_voter_chat_adk.agent import NJVoterChatAgent
        from agents.nj_voter_chat_adk.config import SYSTEM_PROMPT
        print("✓ Successfully imported NJVoterChatAgent and SYSTEM_PROMPT")
        
        print(f"2. System prompt configured: {SYSTEM_PROMPT[:100]}...")
        
        agent = NJVoterChatAgent()
        print("✓ ADK agent initialized successfully")
        
        print("3. Testing prompt delivery with specific question...")
        test_prompt = "How many voters are in the database?"
        print(f"Sending prompt: {test_prompt}")
        
        result = agent.chat(test_prompt)
        print(f"✓ Chat result type: {type(result)}")
        print(f"✓ Chat result: {result}")
        
        if "I am ready" in result or "waiting" in result.lower() or "not received" in result.lower():
            print("✗ Agent still not processing prompts correctly")
            print("Response suggests agent didn't receive the actual question")
            return False
        
        print("4. Testing with another voter data question...")
        result2 = agent.chat('What counties have the most Republican voters?')
        print(f"✓ Second query result: {result2}")
        
        if "I am ready" in result2 or "waiting" in result2.lower() or "not received" in result2.lower():
            print("✗ Agent still not processing second prompt correctly")
            print(f"Problematic response: {result2}")
            return False
        
        print("\n=== Prompt Delivery Tests Passed! ===")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_prompt_delivery()
    sys.exit(0 if success else 1)
