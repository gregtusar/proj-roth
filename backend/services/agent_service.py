import sys
import os
import asyncio
from typing import AsyncGenerator, Optional
import json

# Try to import ADK agent, fall back to mock if not available
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from agents.nj_voter_chat_adk.agent import NJVoterChatAgent
    agent = NJVoterChatAgent()
    ADK_AVAILABLE = True
except ImportError:
    print("Warning: ADK not available, using mock agent service")
    from .agent_service_mock import process_message_stream as mock_stream
    from .agent_service_mock import invoke_agent_tool as mock_tool
    from .agent_service_mock import get_available_tools as mock_tools
    ADK_AVAILABLE = False
    agent = None

async def process_message_stream(
    message: str, 
    session_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Process a message through the ADK agent and stream the response
    """
    if not ADK_AVAILABLE:
        async for chunk in mock_stream(message, session_id):
            yield chunk
        return
    
    try:
        # Use the agent's chat method
        # Note: The ADK agent may not support streaming natively,
        # so we'll simulate it by yielding chunks
        result = await asyncio.to_thread(
            agent.chat,
            message
        )
        
        # Extract the response from the result
        if isinstance(result, dict):
            response = result.get("output", "")
        else:
            response = str(result)
        
        # Simulate streaming by yielding chunks
        chunk_size = 20  # Characters per chunk
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i + chunk_size]
            yield chunk
            await asyncio.sleep(0.05)  # Small delay for streaming effect
            
    except Exception as e:
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