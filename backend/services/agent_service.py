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
    # Don't create a singleton - we'll create agents dynamically with different models
    ADK_AVAILABLE = True
    print("Successfully loaded NJ Voter Chat ADK agent module")
except (ImportError, AttributeError) as e:
    print(f"Error loading ADK agent: {e}")
    print(f"sys.path: {sys.path[:3]}")  # Debug: show first 3 paths
    # Don't fall back to mock - we want to fix this
    raise

# Import session manager for unified session handling
from core.session_manager import get_session_manager, UnifiedSession
from core.request_context import set_request_context, get_current_request_context, get_context_value

# Cache agents per session to maintain context
# Updated to use unified cache keys from SessionManager
_agent_cache = {}
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "evictions": 0
}

async def process_message_stream(
    message: str, 
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    model_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Process a message through the ADK agent and stream the response
    """
    print(f"[Agent] Processing message: {message[:50]}... ADK_AVAILABLE={ADK_AVAILABLE}")
    print(f"[Agent] Session context: session_id={session_id}, user_id={user_id}, model_id={model_id}")
    
    if not ADK_AVAILABLE:
        print("[Agent] Error: ADK agent not available")
        yield "Error: Agent service not available. Please check server logs."
        return
    
    # Generate unique request ID for tracing
    import uuid
    request_id = str(uuid.uuid4())
    
    # Load custom prompt if available
    custom_prompt = None
    if user_id:
        try:
            from services.user_settings_service import get_user_settings_service
            settings_service = get_user_settings_service()
            custom_prompt = await settings_service.get_custom_prompt(user_id)
            if custom_prompt:
                print(f"[Agent] Loaded custom prompt for user {user_id}: {len(custom_prompt)} chars")
        except Exception as e:
            print(f"[Agent] Could not load custom prompt: {e}")
    
    # Use context manager instead of environment variables
    with set_request_context(
        user_id=user_id or "anonymous",
        user_email=user_email or "anonymous@example.com",
        session_id=session_id or "",
        model_id=model_id or "gemini-2.0-flash-exp",
        request_id=request_id,
        custom_prompt=custom_prompt,
        client_type="react",
        verbose_mode=False
    ) as ctx:
        print(f"[Agent] Request context set: {ctx.to_dict()}")
        
        # Also set user context for Google Docs tools (backward compatibility)
        if user_id:
            from agents.nj_voter_chat_adk.user_context import user_context
            user_context.set_user_context(
                user_id=user_id,
                user_email=user_email or "user@example.com",
                session_id=session_id
            )
            print(f"[Agent] Set user context for Google Docs: user_id={user_id}, email={user_email}")
        
        # Set environment variables for backward compatibility during migration
        # TODO: Remove these once all code is migrated to use context vars
        if user_id:
            os.environ["VOTER_LIST_USER_ID"] = user_id
        if user_email:
            os.environ["VOTER_LIST_USER_EMAIL"] = user_email
        if session_id:
            os.environ["CHAT_SESSION_ID"] = session_id
        if model_id:
            os.environ["ADK_MODEL"] = model_id
        if custom_prompt:
            os.environ["USER_CUSTOM_PROMPT"] = custom_prompt
        os.environ["CLIENT_TYPE"] = "react"
        
        print(f"[Agent] Using chat session_id for ADK session: {session_id}")
        print(f"[Agent] Using model: {model_id or 'default'}")
        
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
        
        # Get or create unified session for better cache management
        session_mgr = get_session_manager()
        unified_session = None
        
        if session_id and user_id:
            unified_session = session_mgr.get_session(session_id)
            if not unified_session:
                unified_session = session_mgr.create_session(session_id, user_id, model_id)
                print(f"[Agent] Created new unified session for {session_id}")
            elif unified_session.model_id != model_id:
                # Model changed, update session and clear old cache
                old_cache_key = unified_session.get_agent_cache_key()
                if old_cache_key in _agent_cache:
                    del _agent_cache[old_cache_key]
                    _cache_stats["evictions"] += 1
                unified_session.update_model(model_id)
                print(f"[Agent] Updated session model from {unified_session.model_id} to {model_id}")
        
        # Generate cache key using unified session
        if unified_session:
            cache_key = unified_session.get_agent_cache_key()
        else:
            # Fallback for sessions without unified management
            cache_key = f"anonymous:{model_id}:{session_id or 'nosession'}"
        
        # Check cache with improved key
        if cache_key in _agent_cache:
            agent = _agent_cache[cache_key]
            _cache_stats["hits"] += 1
            print(f"[Agent] Cache HIT for key {cache_key[:30]}... (stats: {_cache_stats})")
        else:
            # Create new agent instance for this session+model
            from agents.nj_voter_chat_adk.agent import NJVoterChatAgent
            agent = NJVoterChatAgent()  # This will use the ADK_MODEL env var we just set
            _cache_stats["misses"] += 1
            
            if unified_session or session_id:  # Cache if we have any session info
                _agent_cache[cache_key] = agent
                print(f"[Agent] Cache MISS - Created new agent for key {cache_key[:30]}... (stats: {_cache_stats})")
                
                # Improved cache cleanup with LRU-like behavior
                if len(_agent_cache) > 100:
                    # Remove entries for users with no active sessions
                    cleanup_count = 0
                    for key in list(_agent_cache.keys()):
                        if cleanup_count >= 20:  # Limit cleanup to prevent blocking
                            break
                        # Check if this is an old session key
                        if ":" in key:
                            parts = key.split(":")
                            if len(parts) >= 2:
                                check_user_id = parts[0]
                                user_sessions = session_mgr.get_user_sessions(check_user_id)
                                if not any(s.has_active_connections() for s in user_sessions):
                                    del _agent_cache[key]
                                    cleanup_count += 1
                                    _cache_stats["evictions"] += 1
                    
                    if cleanup_count > 0:
                        print(f"[Agent] Cache cleanup: evicted {cleanup_count} entries (stats: {_cache_stats})")
            else:
                print(f"[Agent] Created new agent without caching (no session)")
        
        print(f"[Agent] Calling agent.chat with message: {message[:50]}...")
        print(f"[Agent] Session ID: {session_id}")
        print(f"[Agent] Using agent: {type(agent).__name__} (cached: {cache_key in _agent_cache})")
        
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
    
    # Context is automatically cleaned up when exiting the 'with' block
    # This ensures no context leakage between requests
    
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

def clear_session_agent_cache(session_id: str, model_id: Optional[str] = None):
    """
    Clear agent cache for a specific session when model changes.
    Now uses unified cache keys for proper cleanup.
    """
    session_mgr = get_session_manager()
    unified_session = session_mgr.get_session(session_id)
    
    if unified_session:
        # Use unified cache key for targeted removal
        if model_id:
            # Create temporary session with specific model to get the right key
            temp_session = UnifiedSession(session_id, unified_session.user_id, model_id)
            cache_key = temp_session.get_agent_cache_key()
            if cache_key in _agent_cache:
                del _agent_cache[cache_key]
                _cache_stats["evictions"] += 1
                print(f"[Agent] Cleared cache for unified key: {cache_key[:30]}...")
        else:
            # Clear all entries for this session (all models)
            keys_to_remove = []
            for key in _agent_cache.keys():
                if session_id in key:  # Check if session_id is part of the cache key
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del _agent_cache[key]
                _cache_stats["evictions"] += 1
            
            print(f"[Agent] Cleared {len(keys_to_remove)} cache entries for session {session_id}")
    else:
        # Fallback to old-style cleanup for backward compatibility
        old_style_key = (session_id, model_id) if model_id else None
        if old_style_key and old_style_key in _agent_cache:
            del _agent_cache[old_style_key]
            _cache_stats["evictions"] += 1
            print(f"[Agent] Cleared old-style cache key: {old_style_key}")

def clear_user_agent_cache(user_id: str):
    """
    Clear all agent cache entries for a specific user.
    Useful for cleanup when user logs out or on errors.
    """
    keys_to_remove = []
    for key in _agent_cache.keys():
        # Check if this key belongs to the user
        if isinstance(key, str) and key.startswith(f"{user_id}:"):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del _agent_cache[key]
        _cache_stats["evictions"] += 1
    
    if keys_to_remove:
        print(f"[Agent] Cleared {len(keys_to_remove)} cache entries for user {user_id}")
    
    return len(keys_to_remove)

def get_agent_cache_stats() -> dict:
    """
    Get statistics about the agent cache performance.
    """
    total_entries = len(_agent_cache)
    hit_rate = _cache_stats["hits"] / max(1, _cache_stats["hits"] + _cache_stats["misses"])
    
    return {
        "total_entries": total_entries,
        "hits": _cache_stats["hits"],
        "misses": _cache_stats["misses"],
        "evictions": _cache_stats["evictions"],
        "hit_rate": round(hit_rate * 100, 2),
        "cache_keys": list(_agent_cache.keys())[:10]  # Sample of keys for debugging
    }

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