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
    print(f"[Agent] Session context: session_id={session_id}, user_id={user_id}")
    
    if not ADK_AVAILABLE:
        print("[Agent] Error: ADK agent not available")
        yield "Error: Agent service not available. Please check server logs."
        return
    
    try:
        # Set user context for prompt logging
        if user_id:
            os.environ["VOTER_LIST_USER_ID"] = user_id
            
            # Load and set user's custom prompt if available
            try:
                from services.user_settings_service import get_user_settings_service
                settings_service = get_user_settings_service()
                custom_prompt = await settings_service.get_custom_prompt(user_id)
                if custom_prompt:
                    os.environ["USER_CUSTOM_PROMPT"] = custom_prompt
                    print(f"[Agent] Loaded custom prompt for user {user_id}: {len(custom_prompt)} chars")
                else:
                    if "USER_CUSTOM_PROMPT" in os.environ:
                        del os.environ["USER_CUSTOM_PROMPT"]
            except Exception as e:
                print(f"[Agent] Could not load custom prompt: {e}")
                if "USER_CUSTOM_PROMPT" in os.environ:
                    del os.environ["USER_CUSTOM_PROMPT"]
        
        if user_email:
            os.environ["VOTER_LIST_USER_EMAIL"] = user_email
        os.environ["CLIENT_TYPE"] = "react"
        
        # CRITICAL: Pass the chat session_id to the agent so it can maintain separate ADK sessions
        # This enables conversation context to be maintained across messages
        if session_id:
            os.environ["CHAT_SESSION_ID"] = session_id
            print(f"[Agent] Using chat session_id for ADK session: {session_id}")
            
            # Load conversation history if this is an existing session
            # The agent will handle this internally through session_integration
            print(f"[Agent] Session {session_id} will load its conversation history")
        else:
            # Clear session ID if not provided to start fresh
            if "CHAT_SESSION_ID" in os.environ:
                del os.environ["CHAT_SESSION_ID"]
            print("[Agent] No session_id provided, starting fresh conversation")
        
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
        print(f"[Agent] Session ID: {session_id}")
        print(f"[Agent] Using agent: {type(agent).__name__}")
        
        # The agent's chat() method will handle session management based on CHAT_SESSION_ID
        # It will load conversation history internally for context
        
        # Use the agent's chat method with retry logic for robustness
        max_attempts = 3
        result = None
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            print(f"[Agent] Chat attempt {attempt}/{max_attempts}")
            try:
                result = await asyncio.to_thread(
                    agent.chat,
                    message
                )
                print(f"[Agent] Chat attempt {attempt} succeeded")
                break
            except Exception as e:
                last_error = e
                print(f"[Agent] Chat attempt {attempt} failed: {e}")
                if attempt < max_attempts:
                    print(f"[Agent] Retrying in 0.5 seconds...")
                    await asyncio.sleep(0.5)
                else:
                    print(f"[Agent] All chat attempts failed, using last error")
                    raise last_error
        
        print(f"[Agent] Got result from agent: {type(result)}")
        print(f"[Agent] Result preview: {str(result)[:200]}...")
        
        # Use the robust response extraction function from agent.py for consistency
        from agents.nj_voter_chat_adk.agent import extract_response_text
        
        print(f"[Agent] Using robust extraction method for consistency...")
        response = extract_response_text(result, attempt_num=1, max_attempts=3)
        
        # Final validation and cleanup
        if not response or not response.strip():
            error_msg = f"Empty response extracted after {max_attempts} attempts. Agent type: {type(agent).__name__}, Result type: {type(result)}"
            print(f"[Agent] ERROR: {error_msg}")
            
            # Try one more extraction method for debugging
            if hasattr(result, '__dict__'):
                print(f"[Agent] Result attributes: {list(result.__dict__.keys())}")
            
            # Provide user-friendly error with retry suggestion
            response = "I'm having trouble generating a response right now. This might be a temporary issue. Please try your question again, or try rephrasing it."
        else:
            response = response.strip()
            print(f"[Agent] Successfully extracted response: {len(response)} characters")
        
        print(f"[Agent] Final response validation passed, starting stream")
        print(f"[Agent] Response preview: {response[:100]}...")
        
        # Now stream the validated response
        chunk_size = 20  # Characters per chunk
        total_chunks = (len(response) + chunk_size - 1) // chunk_size
        
        for i in range(0, len(response), chunk_size):
            chunk_num = (i // chunk_size) + 1
            chunk = response[i:i + chunk_size]
            print(f"[Agent] Streaming chunk {chunk_num}/{total_chunks}: '{chunk[:10]}...'")
            yield chunk
            await asyncio.sleep(0.05)  # Small delay for streaming effect
        
        print("[Agent] Finished streaming response successfully")
            
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