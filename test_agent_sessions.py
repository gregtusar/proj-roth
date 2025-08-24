#!/usr/bin/env python3
"""Test agent session persistence integration"""

import asyncio
import os
import sys

sys.path.append("agents/nj_voter_chat_adk")

from agent import NJVoterChatAgent
from user_context import user_context

async def test_agent_sessions():
    """Test agent with persistent sessions"""
    print("Testing agent session persistence...")
    
    user_context.set_user_context(
        user_id="test_user_123",
        user_email="test@example.com",
        session_id="test_session_456"
    )
    
    agent = NJVoterChatAgent()
    
    print("\n1. First message...")
    response1 = agent.chat("Hello, can you help me find voters in Summit?")
    print(f"Response: {response1[:100]}...")
    
    print("\n2. Follow-up message...")
    response2 = agent.chat("What about Democrats specifically?")
    print(f"Response: {response2[:100]}...")
    
    print("\n3. Creating new agent instance (simulating restart)...")
    agent2 = NJVoterChatAgent()
    
    print("\n4. Testing session continuity...")
    response3 = agent2.chat("Can you remind me what we were discussing?")
    print(f"Response: {response3[:100]}...")
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_agent_sessions())
