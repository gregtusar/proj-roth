"""
Mock agent service for deployment without ADK
"""
import asyncio
from typing import AsyncGenerator, Optional

async def process_message_stream(
    message: str, 
    session_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Mock implementation that returns a simple response
    """
    response = f"I received your message: '{message}'. The ADK agent is currently being configured. You can still use the List Manager and Maps features."
    
    # Simulate streaming by yielding chunks
    chunk_size = 20
    for i in range(0, len(response), chunk_size):
        chunk = response[i:i + chunk_size]
        yield chunk
        await asyncio.sleep(0.05)

async def invoke_agent_tool(tool_name: str, args: dict) -> dict:
    """
    Mock tool invocation
    """
    return {
        "result": f"Tool '{tool_name}' called with args: {args}",
        "note": "ADK tools are being configured"
    }

def get_available_tools() -> list:
    """
    Get list of available agent tools
    """
    return [
        {
            "name": "bigquery_select",
            "description": "Execute read-only BigQuery SQL queries (coming soon)",
            "parameters": {
                "query": "SQL SELECT query",
                "limit": "Maximum rows to return"
            }
        }
    ]