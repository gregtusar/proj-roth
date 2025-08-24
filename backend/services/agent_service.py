import sys
import os
import asyncio
from typing import AsyncGenerator, Optional
import json

# Fix the import path to avoid conflicts with installed 'agents' package
# Insert the project root at the beginning of sys.path to prioritize local imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import the local agents package
try:
    # Force reload to ensure we get the local version
    if 'agents' in sys.modules:
        # Remove the conflicting agents module
        for key in list(sys.modules.keys()):
            if key.startswith('agents'):
                del sys.modules[key]
    
    from agents.nj_voter_chat_adk.agent import NJVoterChatAgent
    agent = NJVoterChatAgent()
    ADK_AVAILABLE = True
    print("Successfully loaded NJ Voter Chat ADK agent")
except (ImportError, AttributeError) as e:
    print(f"Error loading ADK agent: {e}")
    print(f"sys.path: {sys.path[:3]}")  # Debug: show first 3 paths
    # Don't fall back to mock - we want to fix this
    raise

async def process_message_stream(
    message: str, 
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Process a message through the ADK agent and stream the response
    """
    print(f"[Agent] Processing message: {message[:50]}... ADK_AVAILABLE={ADK_AVAILABLE}")
    
    if not ADK_AVAILABLE:
        print("[Agent] Error: ADK agent not available")
        yield "Error: Agent service not available. Please check server logs."
        return
    
    try:
        # Set user context for prompt logging
        if user_id:
            os.environ["VOTER_LIST_USER_ID"] = user_id
        if user_email:
            os.environ["VOTER_LIST_USER_EMAIL"] = user_email
        os.environ["CLIENT_TYPE"] = "react"
        
        # CRITICAL: Pass the chat session_id to the agent so it can maintain separate ADK sessions
        if session_id:
            os.environ["CHAT_SESSION_ID"] = session_id
            print(f"[Agent] Using chat session_id for ADK session: {session_id}")
        
        # For testing: return a simple response immediately
        if message.lower().strip() == "test":
            test_response = "This is a test response from the agent service. If you see this, the streaming is working!"
            print(f"[Agent] Returning test response: {test_response}")
            chunk_size = 20
            for i in range(0, len(test_response), chunk_size):
                chunk = test_response[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.05)
            return
        
        print(f"[Agent] Calling agent.chat with message: {message[:50]}...")
        
        # Reset the agent's session for each chat conversation
        # This ensures each conversation has its own ADK session and token budget
        if session_id:
            # Force the agent to use a new session for this conversation
            agent._session_id = f"chat_{session_id}"
            print(f"[Agent] Set ADK session to: chat_{session_id}")
        
        # Use the agent's chat method
        # Note: The ADK agent may not support streaming natively,
        # so we'll simulate it by yielding chunks
        result = await asyncio.to_thread(
            agent.chat,
            message
        )
        
        print(f"[Agent] Got result from agent: {type(result)} - {str(result)[:100]}...")
        
        # Extract the response from the result
        if isinstance(result, dict):
            response = result.get("output", "")
        else:
            response = str(result)
        
        # If we got an empty response, provide feedback
        if not response:
            response = "I'm having trouble generating a response. Please try again or check the server logs."
            print("[Agent] Warning: Empty response from agent")
        
        print(f"[Agent] Streaming response: {len(response)} characters")
        
        # Simulate streaming by yielding chunks
        chunk_size = 20  # Characters per chunk
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i + chunk_size]
            yield chunk
            await asyncio.sleep(0.05)  # Small delay for streaming effect
        
        print("[Agent] Finished streaming response")
            
    except Exception as e:
        print(f"[Agent] Error: {e}")
        import traceback
        traceback.print_exc()
        yield f"Error: {str(e)}"

async def invoke_agent_tool(tool_name: str, args: dict) -> dict:
    """
    Directly invoke a specific agent tool
    """
    try:
        from agents.nj_voter_chat_adk.bigquery_tool import BigQueryReadOnlyTool
        from agents.nj_voter_chat_adk.geocoding_tool import GeocodingTool
        from agents.nj_voter_chat_adk.search_tool import GoogleSearchTool
        
        tools = {
            "bigquery_select": BigQueryReadOnlyTool(),
            "geocode_address": GeocodingTool(),
            "google_search": GoogleSearchTool()
        }
        
        if tool_name not in tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        tool = tools[tool_name]
        result = await asyncio.to_thread(tool.run, args)
        return {"result": result}
        
    except Exception as e:
        return {"error": str(e)}

def get_available_tools() -> list:
    """
    Get list of available agent tools
    """
    return [
        {
            "name": "bigquery_select",
            "description": "Execute read-only BigQuery SQL queries",
            "parameters": {
                "query": "SQL SELECT query",
                "limit": "Maximum rows to return (default: 1000)"
            }
        },
        {
            "name": "geocode_address",
            "description": "Convert addresses to geographic coordinates",
            "parameters": {
                "address": "Address to geocode"
            }
        },
        {
            "name": "google_search",
            "description": "Search for current NJ political information",
            "parameters": {
                "query": "Search query"
            }
        }
    ]