#!/usr/bin/env python3
"""Enhanced test script to debug ADK agent system instruction delivery"""

import sys
import os
sys.path.append('agents/nj_voter_chat_adk')

def test_adk_debug():
    try:
        print("=== Enhanced ADK Debug Test ===")
        
        print("1. Testing import and configuration...")
        from agents.nj_voter_chat_adk.agent import NJVoterChatAgent
        from agents.nj_voter_chat_adk.config import SYSTEM_PROMPT, MODEL
        print(f"✓ Successfully imported components")
        print(f"✓ Model: {MODEL}")
        print(f"✓ System prompt: {SYSTEM_PROMPT[:100]}...")
        
        print("2. Testing agent initialization...")
        agent = NJVoterChatAgent()
        print("✓ ADK agent initialized")
        
        print("3. Testing with simple greeting (should show system awareness)...")
        result1 = agent.chat("Hello")
        print(f"✓ Greeting result: {result1}")
        
        print("4. Testing with data question (should use BigQuery tool)...")
        result2 = agent.chat("How many voters are in the database?")
        print(f"✓ Data query result: {result2}")
        
        print("5. Testing with fallback mode...")
        os.environ["ADK_DEBUG_FALLBACK"] = "true"
        agent_fallback = NJVoterChatAgent()
        result3 = agent_fallback.chat("What can you help me with?")
        print(f"✓ Fallback result: {result3}")
        
        print("\n=== Analysis ===")
        responses = [result1, result2, result3]
        for i, resp in enumerate(responses, 1):
            if resp and isinstance(resp, str):
                has_system_awareness = any(keyword in resp.lower() for keyword in 
                    ['data assistant', 'voter data', 'bigquery', 'nj voter', 'sql'])
                print(f"Response {i} shows system awareness: {has_system_awareness}")
            else:
                print(f"Response {i} is invalid: {type(resp)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_adk_debug()
    sys.exit(0 if success else 1)
