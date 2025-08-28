from typing import Any, Dict
import asyncio
import inspect
import time
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.database_manifest import DATABASE_MANIFEST, format_for_llm

from google.adk.agents import Agent
from google.adk.runners import Runner

from .config import MODEL, PROJECT_ID, REGION, SYSTEM_PROMPT
from .bigquery_tool import BigQueryReadOnlyTool
from .google_search_tool import GoogleSearchTool
from .geocoding_tool import GeocodingTool
from .voter_list_tool import VoterListTool
from .debug_config import debug_print, error_print

# Global reference to the current websocket for reasoning events
_current_websocket = None

def _set_websocket(ws):
    """Set the current websocket for streaming reasoning events"""
    global _current_websocket
    _current_websocket = ws

def extract_response_text(result, attempt_num=1, max_attempts=3):
    """
    Robust response extraction function with multiple fallback methods.
    
    Args:
        result: The response object from the ADK agent
        attempt_num: Current attempt number for logging
        max_attempts: Maximum number of extraction attempts
        
    Returns:
        str: Extracted response text or error message
    """
    debug_print(f"[EXTRACT] Attempt {attempt_num}/{max_attempts} - Extracting response from {type(result)}")
    
    # Method 1: Standard ADK response with content.parts
    if hasattr(result, 'content') and hasattr(result.content, 'parts'):
        debug_print(f"[EXTRACT] Method 1: Found content with {len(result.content.parts)} parts")
        text_parts = []
        
        for i, part in enumerate(result.content.parts):
            part_text_length = len(part.text) if hasattr(part, 'text') and part.text else 0
            debug_print(f"[EXTRACT] Part {i}: has_text={hasattr(part, 'text')}, text_length={part_text_length}")
            
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text.strip())
            elif hasattr(part, 'text') and part.text == '':
                # Log when we get an explicitly empty text response from ADK
                debug_print(f"[EXTRACT] WARNING: Part {i} has empty text - ADK returned no content")
                error_print(f"[EXTRACT] ADK returned empty response. This often happens when the model cannot process the request.")
        
        if text_parts:
            final_response = '\n'.join(text_parts)
            debug_print(f"[EXTRACT] Method 1 SUCCESS: Extracted {len(final_response)} characters")
            debug_print(f"[EXTRACT] Response preview: {final_response[:200]}...")
            return final_response
        else:
            debug_print(f"[EXTRACT] Method 1 FAILED: No text content in parts")
            # Check if we got empty parts (ADK returned but with no content)
            if any(hasattr(part, 'text') and part.text == '' for part in result.content.parts):
                error_print(f"[EXTRACT] ADK returned empty text parts - likely a processing error")
    
    # Method 2: Direct text attribute
    if hasattr(result, 'text') and result.text:
        debug_print(f"[EXTRACT] Method 2 SUCCESS: Direct text attribute, {len(result.text)} characters")
        return result.text.strip()
    
    # Method 3: Response as dict with various possible keys
    if isinstance(result, dict):
        debug_print(f"[EXTRACT] Method 3: Dict response with keys: {list(result.keys())}")
        
        # Try common response keys
        for key in ['output', 'response', 'text', 'content', 'message', 'answer']:
            if key in result and result[key]:
                debug_print(f"[EXTRACT] Method 3 SUCCESS: Found content in '{key}' key")
                return str(result[key]).strip()
    
    # Method 4: List of responses (batch responses)
    if isinstance(result, list) and result:
        debug_print(f"[EXTRACT] Method 4: List response with {len(result)} items")
        
        # Try to extract from first item if it has expected structure
        first_item = result[0]
        if hasattr(first_item, 'content'):
            return extract_response_text(first_item, attempt_num, max_attempts)
        elif isinstance(first_item, str):
            debug_print(f"[EXTRACT] Method 4 SUCCESS: String in list")
            return first_item.strip()
    
    # Method 5: String conversion fallback
    if result is not None:
        result_str = str(result).strip()
        if result_str and result_str != 'None' and len(result_str) > 0:
            debug_print(f"[EXTRACT] Method 5 SUCCESS: String conversion, {len(result_str)} characters")
            return result_str
    
    # Method 6: Check for nested response attributes
    for attr in ['response', 'output', 'result', 'data']:
        if hasattr(result, attr):
            nested_result = getattr(result, attr)
            if nested_result:
                debug_print(f"[EXTRACT] Method 6: Trying nested attribute '{attr}'")
                return extract_response_text(nested_result, attempt_num, max_attempts)
    
    # All methods failed
    error_msg = f"[EXTRACT] All extraction methods failed for {type(result)}"
    debug_print(error_msg)
    
    if hasattr(result, '__dict__'):
        debug_print(f"[EXTRACT] Object attributes: {list(result.__dict__.keys())}")
    
    return None

def _emit_reasoning_event(event_type: str, data: Dict[str, Any]):
    """Emit a reasoning event through the websocket if available"""
    global _current_websocket
    if _current_websocket:
        try:
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, create task
                asyncio.create_task(_current_websocket.emit('reasoning_event', {
                    'type': event_type,
                    'data': data,
                    'timestamp': time.time()
                }))
            except RuntimeError:
                # No async loop, we're in sync context - just log for now
                debug_print(f"[DEBUG] Reasoning event (sync): {event_type} - {data}")
        except Exception as e:
            debug_print(f"[DEBUG] Failed to emit reasoning event: {e}")

_bq_tool = None
_search_tool = None
_geocoding_tool = None
_list_tool = None

def _get_bq_tool():
    global _bq_tool
    if _bq_tool is None:
        _bq_tool = BigQueryReadOnlyTool()
    return _bq_tool

def _get_search_tool():
    global _search_tool
    if _search_tool is None:
        _search_tool = GoogleSearchTool()
    return _search_tool

def _get_geocoding_tool():
    global _geocoding_tool
    if _geocoding_tool is None:
        _geocoding_tool = GeocodingTool()
    return _geocoding_tool

def _get_list_tool():
    global _list_tool
    if _list_tool is None:
        _list_tool = VoterListTool()
    return _list_tool

def bigquery_select(sql: str) -> Dict[str, Any]:
    """Executes read-only SELECT queries on approved BigQuery tables with smart field mapping.
    
    Args:
        sql (str): The SQL query to execute. Must be a SELECT query against approved tables.
                  Common field names like 'voter_id', 'party', 'address' are automatically mapped
                  to the correct schema field names.
        
    Returns:
        Dict[str, Any]: Query results including rows, row_count, truncated flag, elapsed time, 
                       original SQL, and mapped SQL. If an error occurs, returns error information
                       instead of raising an exception.
    """
    print(f"\n[TOOL INVOKED] bigquery_select")
    print(f"[SQL QUERY] {sql[:500]}...")
    
    # Emit reasoning event if we're in a streaming context
    _emit_reasoning_event("tool_start", {
        "tool": "bigquery_select", 
        "query": sql,  # Send full query for debugging
        "truncated": len(sql) > 1000,
        "query_length": len(sql)
    })
    
    try:
        result = _get_bq_tool().run(sql)
        debug_print(f"[DEBUG] BigQuery tool returned: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
        # Log result size
        if isinstance(result, dict):
            row_count = result.get('row_count', 0)
            result_str = str(result)
            print(f"[TOOL RESULT] Rows returned: {row_count}")
            print(f"[TOOL RESULT SIZE] {len(result_str)} characters / ~{len(result_str)//4} tokens")
            if len(result_str) > 100000:
                print(f"[WARNING] Large result: {len(result_str)} characters!")
            
            # Emit reasoning event with results summary
            _emit_reasoning_event("tool_result", {
                "tool": "bigquery_select",
                "rows": row_count,
                "size_chars": len(result_str),
                "size_tokens": len(result_str) // 4
            })
        
        return result
    except Exception as e:
        error_print(f"[ERROR] BigQuery tool execution failed: {e}")
        _emit_reasoning_event("tool_error", {
            "tool": "bigquery_select",
            "error": str(e)
        })
        return {
            "error": f"BigQuery tool execution failed: {str(e)}",
            "sql": sql,
            "rows": [],
            "row_count": 0
        }

def geocode_address(address: str) -> Dict[str, Any]:
    """Convert an address to latitude/longitude coordinates using Google Maps.
    
    Args:
        address (str): The address to geocode. Can be a full address, business name, 
                      or landmark (e.g., "123 Main St, Summit, NJ" or "Summit train station").
                      If no state is specified, New Jersey will be assumed.
    
    Returns:
        Dict[str, Any]: Contains latitude, longitude, and formatted_address if successful,
                       or error information if geocoding fails. Useful for finding exact
                       locations to use in geospatial BigQuery queries.
    
    Example:
        >>> geocode_address("Summit train station")
        {"latitude": 40.7155, "longitude": -74.3574, "formatted_address": "Summit Station, Summit, NJ 07901, USA"}
    """
    try:
        result = _get_geocoding_tool().geocode(address)
        debug_print(f"[DEBUG] Geocoding result for '{address}': {result}")
        return result
    except Exception as e:
        error_print(f"[ERROR] Geocoding failed: {e}")
        return {
            "error": f"Geocoding failed: {str(e)}",
            "address": address
        }

def google_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Search Google for current information about NJ politics, elections, and voter-related topics.
    
    Args:
        query (str): The search query. Will automatically add NJ context if not present.
        num_results (int): Number of results to return (max 10, default 5).
    
    Returns:
        Dict[str, Any]: Search results including title, snippet, and link for each result.
                       Returns error information if search fails or API is not configured.
    """
    print(f"\n[TOOL INVOKED] google_search")
    print(f"[SEARCH QUERY] {query[:200]}")
    print(f"[NUM RESULTS] {num_results}")
    
    # Emit reasoning event
    _emit_reasoning_event("tool_start", {
        "tool": "google_search",
        "query": query,  # Send full query
        "num_results": num_results,
        "query_length": len(query)
    })
    
    try:
        # Use the NJ-specific search method to ensure NJ context
        result = _get_search_tool().search_nj_specific(query, num_results)
        debug_print(f"[DEBUG] Google search returned {result.get('result_count', 0)} results for query: {query[:100]}")
        
        # Log result size
        result_str = str(result)
        print(f"[TOOL RESULT SIZE] {len(result_str)} characters / ~{len(result_str)//4} tokens")
        
        # Emit reasoning event with results
        _emit_reasoning_event("tool_result", {
            "tool": "google_search",
            "results_count": result.get('result_count', 0),
            "size_chars": len(result_str),
            "size_tokens": len(result_str) // 4
        })
        
        return result
    except Exception as e:
        error_print(f"[ERROR] Google search failed: {e}")
        _emit_reasoning_event("tool_error", {
            "tool": "google_search",
            "error": str(e)
        })
        return {
            "error": f"Google search failed: {str(e)}",
            "query": query,
            "results": []
        }

def save_voter_list(list_name: str, description: str, sql_query: str, row_count: int) -> Dict[str, Any]:
    """Save a voter list for later retrieval and sharing.
    
    IMPORTANT: You should proactively save lists when:
    - A query returns a meaningful set of voters (any size)
    - The user asks questions like "Who are all the voters that..."
    - The user explicitly asks to save a list with phrases like "save this list"
    
    Args:
        list_name (str): A descriptive name for the list (auto-generate based on the query).
                        Examples: "Democrats in Summit", "High-frequency voters born after 1990"
        description (str): The original user query/question that generated this list.
        sql_query (str): The exact SQL query used to generate the list (for re-running).
        row_count (int): The number of voters in the result set.
    
    Returns:
        Dict[str, Any]: Contains success status, list_id if successful, or error information.
    
    Example:
        >>> save_voter_list(
        ...     "Young Democrats in Summit",
        ...     "Show me all Democrats under 30 in Summit",
        ...     "SELECT * FROM voters WHERE demo_party = 'DEM' AND age < 30 AND muni_name = 'SUMMIT'",
        ...     127
        ... )
        {"success": True, "list_id": "abc123", "message": "List 'Young Democrats in Summit' saved successfully"}
    """
    try:
        # Get user context from session (will be set by the app)
        import os
        user_id = os.environ.get("VOTER_LIST_USER_ID", "default_user")
        user_email = os.environ.get("VOTER_LIST_USER_EMAIL", "user@example.com")
        
        # Enhanced logging for debugging
        debug_print(f"[DEBUG] Attempting to save list:")
        debug_print(f"  - User ID: {user_id}")
        debug_print(f"  - User Email: {user_email}")
        debug_print(f"  - List Name: {list_name}")
        debug_print(f"  - Row Count: {row_count}")
        debug_print(f"  - SQL Query Length: {len(sql_query)} chars")
        
        result = _get_list_tool().save_voter_list(
            user_id=user_id,
            user_email=user_email,
            list_name=list_name,
            description_text=description,
            sql_query=sql_query,
            row_count=row_count,
            model_name=MODEL
        )
        
        if result.get("success"):
            debug_print(f"[DEBUG] Successfully saved voter list '{list_name}' with ID: {result.get('list_id')}")
        else:
            error_print(f"[ERROR] Failed to save list: {result.get('error')}")
        
        return result
    except Exception as e:
        import traceback
        error_print(f"[ERROR] Exception while saving voter list: {e}")
        error_print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": f"Failed to save list: {str(e)}",
            "list_id": None
        }

class NJVoterChatAgent(Agent):
    def __init__(self):
        import os
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
        os.environ["GOOGLE_CLOUD_LOCATION"] = REGION
        
        # Log system prompt size
        print(f"[SYSTEM PROMPT SIZE] {len(SYSTEM_PROMPT)} characters / ~{len(SYSTEM_PROMPT)//4} tokens")
        debug_print(f"[DEBUG] Initializing agent with instruction: {SYSTEM_PROMPT[:100]}...")
        
        super().__init__(
            name="nj_voter_chat", 
            model=MODEL, 
            tools=[bigquery_select, google_search, geocode_address, save_voter_list], 
            instruction=SYSTEM_PROMPT
        )
        debug_print(f"[DEBUG] Agent initialized successfully with instruction parameter and tools: bigquery_select, google_search, geocode_address, save_voter_list")
        self._initialize_services()
    
    def _initialize_services(self):
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
        from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
        from google.adk.runners import Runner
        from .session_integration import SessionIntegration
        
        self._session_service = InMemorySessionService()
        self._memory_service = InMemoryMemoryService()
        self._artifact_service = InMemoryArtifactService()
        
        self._persistent_sessions = SessionIntegration()
        
        self._runner = Runner(
            app_name="nj_voter_chat",
            agent=self,
            session_service=self._session_service,
            memory_service=self._memory_service,
            artifact_service=self._artifact_service
        )
        self._user_id = "default_user"
        self._session_id = None

    def chat(self, prompt: str):
        def _run_asyncio(coro):
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                new_loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(new_loop)
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
                    asyncio.set_event_loop(loop)
            else:
                return asyncio.run(coro)

        async def _consume_async_gen(agen):
            # Collect ALL chunks, not just the last one!
            all_chunks = []
            last = None
            chunk_count = 0
            total_size = 0
            async for chunk in agen:
                chunk_count += 1
                chunk_str = str(chunk)
                total_size += len(chunk_str)
                
                # Store ALL chunks for proper processing
                all_chunks.append(chunk)
                
                # Log significant events
                if hasattr(chunk, '__class__'):
                    event_type = chunk.__class__.__name__
                    print(f"[ADK EVENT {chunk_count}] Type: {event_type}, Size: {len(chunk_str)} chars")
                    
                    # Emit ADK reasoning event with full content for debugging
                    _emit_reasoning_event("adk_event", {
                        "event_number": chunk_count,
                        "event_type": event_type,
                        "size_chars": len(chunk_str),
                        "size_tokens": len(chunk_str) // 4,
                        "content": chunk_str,  # Send full content for debugging
                        "truncated": len(chunk_str) > 2000
                    })
                    
                    # Check for tool calls
                    if 'tool' in chunk_str.lower() or 'function' in chunk_str.lower():
                        print(f"[TOOL ACTIVITY DETECTED] {chunk_str[:500]}")
                        _emit_reasoning_event("adk_tool_activity", {
                            "content": chunk_str,  # Full content for debugging
                            "preview": chunk_str[:500] if len(chunk_str) > 500 else chunk_str
                        })
                
                last = chunk
            
            print(f"[ADK COMPLETE] Total events: {chunk_count}, Total size: {total_size} chars / ~{total_size//4} tokens")
            _emit_reasoning_event("adk_complete", {
                "total_events": chunk_count,
                "total_size_chars": total_size,
                "total_size_tokens": total_size // 4
            })
            
            # CRITICAL FIX: Combine ALL text from ALL chunks, not just return one chunk
            # ADK may send content across multiple chunks that need to be assembled
            combined_text_parts = []
            final_chunk = None
            
            print(f"[ADK] Processing {len(all_chunks)} chunks to extract complete response")
            
            for i, chunk in enumerate(all_chunks):
                if hasattr(chunk, 'content') and hasattr(chunk.content, 'parts'):
                    # Extract text from this chunk's parts
                    for part in chunk.content.parts:
                        if hasattr(part, 'text') and part.text and part.text.strip():
                            combined_text_parts.append(part.text.strip())
                            print(f"[ADK] Chunk {i+1}: Found text part with {len(part.text)} chars")
                    
                    # Keep the last chunk that had content as our template
                    if combined_text_parts:
                        final_chunk = chunk
            
            # If we found text across chunks, create a combined response
            if combined_text_parts and final_chunk:
                combined_text = '\n'.join(combined_text_parts)
                print(f"[ADK] Combined {len(combined_text_parts)} text parts into {len(combined_text)} total chars")
                
                # Modify the final chunk to contain all combined text
                # This preserves the chunk structure while including all content
                if hasattr(final_chunk, 'content') and hasattr(final_chunk.content, 'parts'):
                    if final_chunk.content.parts:
                        # Replace the text in the first part with combined text
                        if hasattr(final_chunk.content.parts[0], 'text'):
                            final_chunk.content.parts[0].text = combined_text
                            print(f"[ADK] Updated final chunk with combined text")
                
                return final_chunk
            
            # If no content chunks found at all, return the last chunk (original behavior)
            print(f"[ADK] No content chunks found in any of {len(all_chunks)} chunks, returning last chunk")
            return last

        # Get user context
        user_id = os.environ.get("VOTER_LIST_USER_ID", "default_user")
        user_email = os.environ.get("VOTER_LIST_USER_EMAIL", "user@example.com")
        chat_session_id = os.environ.get("CHAT_SESSION_ID")
        session_id = self._session_id if hasattr(self, '_session_id') else None
        
        persistent_session_id = None
        try:
            persistent_session_id = _run_asyncio(self._persistent_sessions.create_or_get_session(
                user_id=user_id,
                user_email=user_email,
                session_id=chat_session_id
            ))
            
            _run_asyncio(self._persistent_sessions.add_message(
                session_id=persistent_session_id,
                user_id=user_id,
                message_type="user",
                message_text=prompt
            ))
        except Exception as e:
            print(f"Error with persistent session: {e}")
            persistent_session_id = None

        try:
            debug_print("[DEBUG] NJVoterChatAgent.chat -> using proper ADK Runner invocation")
            from google.adk.agents.run_config import RunConfig
            from google.genai import types
            
            # Use the chat session ID if provided, otherwise create a new one
            # This ensures each chat conversation has its own ADK session
            chat_session_id = os.environ.get("CHAT_SESSION_ID")
            
            # If we have a chat session ID and it's different from current, handle session properly
            if chat_session_id:
                expected_session_id = f"chat_{chat_session_id}"
                
                # Check if we need to switch to a different session or create new one
                if not hasattr(self, '_session_id') or self._session_id != expected_session_id:
                    previous_session_id = getattr(self, '_session_id', None)
                    self._session_id = expected_session_id
                    
                    # Load conversation history for context if this is an existing chat session
                    debug_print(f"[DEBUG] Loading conversation history for session: {chat_session_id}")
                    try:
                        # Get the conversation history from persistent storage
                        history = _run_asyncio(self._persistent_sessions.get_session_history(
                            session_id=chat_session_id,
                            user_id=user_id
                        ))
                        
                        if history:
                            debug_print(f"[DEBUG] Found {len(history)} messages in conversation history")
                            # The history will be used to provide context for the current conversation
                            # Store it for later use in the prompt
                            self._conversation_history = history
                        else:
                            debug_print(f"[DEBUG] No conversation history found for session {chat_session_id}")
                            self._conversation_history = []
                    except Exception as e:
                        debug_print(f"[DEBUG] Error loading conversation history: {e}")
                        self._conversation_history = []
                    
                    # Try to create ADK session, but handle case where it might already exist
                    try:
                        session = _run_asyncio(self._session_service.create_session(
                            app_name="nj_voter_chat",
                            user_id=self._user_id,
                            session_id=self._session_id
                        ))
                        debug_print(f"[DEBUG] Created new ADK session for chat: {self._session_id}")
                    except Exception as e:
                        debug_print(f"[DEBUG] Session creation returned: {e}, continuing with session_id: {self._session_id}")
                else:
                    debug_print(f"[DEBUG] Reusing ADK session for chat: {self._session_id}")
                    # Session already active, conversation history should already be loaded
            else:
                # Fallback: create a new session each time if no chat session ID
                self._session_id = f"session_{int(time.time())}_{os.getpid()}"
                self._conversation_history = []  # No history for new sessions
                try:
                    session = _run_asyncio(self._session_service.create_session(
                        app_name="nj_voter_chat",
                        user_id=self._user_id,
                        session_id=self._session_id
                    ))
                    debug_print(f"[DEBUG] Created new ADK session (no chat session): {self._session_id}")
                except Exception as e:
                    debug_print(f"[DEBUG] Session creation returned: {e}, continuing with session_id: {self._session_id}")
            
            # Check for user custom prompt and prepend it to the message if available
            custom_prompt = os.environ.get("USER_CUSTOM_PROMPT", "").strip()
            if custom_prompt:
                # Prepend the custom instructions to the user's message
                enhanced_prompt = f"[User's Custom Instructions: {custom_prompt}]\n\n{prompt}"
                print(f"[CUSTOM PROMPT] Adding {len(custom_prompt)} chars of custom instructions to prompt")
            else:
                enhanced_prompt = prompt
            
            message_content = types.Content(
                role="user",
                parts=[types.Part(text=enhanced_prompt)]
            )
            
            # Log token estimation for the prompt
            print(f"\n[AGENT INVOCATION] Starting ADK agent processing")
            print(f"[USER PROMPT] {prompt[:200]}{'...' if len(prompt) > 200 else ''}")
            print(f"[PROMPT SIZE] {len(prompt)} characters / ~{len(prompt)//4} tokens")
            print(f"[SESSION ID] {self._session_id}")
            
            debug_print(f"[DEBUG] User prompt being sent with proper ADK message format: {prompt[:200]}...")
            debug_print(f"[DEBUG] Message content structure: {message_content}")
            debug_print(f"[DEBUG] Session ID: {self._session_id}, User ID: {self._user_id}")
            debug_print(f"[DEBUG] About to call runner.run_async with RunConfig")
            
            # Configure generation parameters via RunConfig
            max_tokens = int(os.environ.get("ADK_MAX_OUTPUT_TOKENS", "32768"))
            run_config = RunConfig()
            
            # Log RunConfig details
            print(f"[RUN CONFIG] max_llm_calls: {run_config.max_llm_calls}")
            
            # Set a limit on context/history to prevent token overflow
            # The model has a 1M token limit, but with system prompt + history + query + response
            # we need to leave room. Setting a conservative limit.
            if hasattr(run_config, 'max_context_tokens'):
                run_config.max_context_tokens = 800000  # Leave ~250k for response
            
            # Set generation parameters if available in RunConfig
            if hasattr(run_config, 'generation_config'):
                debug_print(f"[DEBUG] Setting generation_config with max_output_tokens={max_tokens}")
                run_config.generation_config = {
                    "max_output_tokens": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40
                }
            elif hasattr(run_config, 'max_output_tokens'):
                debug_print(f"[DEBUG] Setting max_output_tokens={max_tokens} directly")
                run_config.max_output_tokens = max_tokens
            else:
                debug_print(f"[DEBUG] No generation config fields found in RunConfig")
            
            if hasattr(run_config, 'request'):
                run_config.request = message_content
                debug_print(f"[DEBUG] Using RunConfig.request field for message content")
                try:
                    agen = self._runner.run_async(
                        user_id=self._user_id,
                        session_id=self._session_id,
                        run_config=run_config
                    )
                except ValueError as e:
                    if "Session not found" in str(e):
                        debug_print(f"[DEBUG] Session not found, creating new session and retrying")
                        # Create a new session with timestamp to avoid conflicts
                        self._session_id = f"chat_{chat_session_id}_{int(time.time())}" if chat_session_id else f"session_{int(time.time())}_{os.getpid()}"
                        try:
                            session = _run_asyncio(self._session_service.create_session(
                                app_name="nj_voter_chat",
                                user_id=self._user_id,
                                session_id=self._session_id
                            ))
                            debug_print(f"[DEBUG] Created fresh ADK session: {self._session_id}")
                        except Exception as se:
                            debug_print(f"[DEBUG] Session creation error (continuing): {se}")
                        # Retry with new session
                        agen = self._runner.run_async(
                            user_id=self._user_id,
                            session_id=self._session_id,
                            run_config=run_config
                        )
                    else:
                        raise
            else:
                debug_print(f"[DEBUG] Using original new_message parameter with fixed structure")
                try:
                    agen = self._runner.run_async(
                        user_id=self._user_id,
                        session_id=self._session_id,
                        new_message=message_content,
                        run_config=run_config
                    )
                except ValueError as e:
                    if "Session not found" in str(e):
                        debug_print(f"[DEBUG] Session not found, creating new session and retrying")
                        # Create a new session with timestamp to avoid conflicts
                        self._session_id = f"chat_{chat_session_id}_{int(time.time())}" if chat_session_id else f"session_{int(time.time())}_{os.getpid()}"
                        try:
                            session = _run_asyncio(self._session_service.create_session(
                                app_name="nj_voter_chat",
                                user_id=self._user_id,
                                session_id=self._session_id
                            ))
                            debug_print(f"[DEBUG] Created fresh ADK session: {self._session_id}")
                        except Exception as se:
                            debug_print(f"[DEBUG] Session creation error (continuing): {se}")
                        # Retry with new session
                        agen = self._runner.run_async(
                            user_id=self._user_id,
                            session_id=self._session_id,
                            new_message=message_content,
                            run_config=run_config
                        )
                    else:
                        raise
            debug_print(f"[DEBUG] Runner.run_async returned: {type(agen)}")
            
            if inspect.isasyncgen(agen):
                try:
                    result = _run_asyncio(_consume_async_gen(agen))
                except ValueError as e:
                    if "Session not found" in str(e):
                        debug_print(f"[DEBUG] Session not found during async consumption, creating new session and retrying")
                        # Create a completely new session with timestamp
                        self._session_id = f"chat_{int(time.time())}_{os.getpid()}"
                        try:
                            session = _run_asyncio(self._session_service.create_session(
                                app_name="nj_voter_chat",
                                user_id=self._user_id,
                                session_id=self._session_id
                            ))
                            debug_print(f"[DEBUG] Created fresh ADK session after error: {self._session_id}")
                        except Exception as se:
                            debug_print(f"[DEBUG] Session creation error (continuing): {se}")
                        
                        # Retry with completely new session
                        if hasattr(run_config, 'request'):
                            agen = self._runner.run_async(
                                user_id=self._user_id,
                                session_id=self._session_id,
                                run_config=run_config
                            )
                        else:
                            agen = self._runner.run_async(
                                user_id=self._user_id,
                                session_id=self._session_id,
                                new_message=message_content,
                                run_config=run_config
                            )
                        result = _run_asyncio(_consume_async_gen(agen))
                    else:
                        raise
                except AttributeError as e:
                    # aiohttp compatibility issue - happens when using BigQuery tool
                    # but doesn't prevent the tool from working
                    if "ClientConnectorDNSError" in str(e):
                        error_print(f"[WARNING] aiohttp compatibility issue (ignoring): {e}")
                        # The tool execution continues despite this error
                        # Return a message indicating to retry
                        return "I'm processing your database query. Due to a temporary compatibility issue, please send your request again and it should work."
                    else:
                        raise
            else:
                result = agen
            
            # Use robust response extraction with retry logic
            max_extraction_attempts = 3
            final_response = None
            
            for attempt in range(1, max_extraction_attempts + 1):
                debug_print(f"[CHAT] Response extraction attempt {attempt}/{max_extraction_attempts}")
                
                final_response = extract_response_text(result, attempt, max_extraction_attempts)
                
                if final_response and len(final_response.strip()) > 0:
                    break
                
                if attempt < max_extraction_attempts:
                    debug_print(f"[CHAT] Extraction attempt {attempt} failed, retrying...")
                    # Small delay before retry
                    import time
                    time.sleep(0.1)
            
            # Validate extracted response
            if final_response and len(final_response.strip()) > 0:
                debug_print(f"[CHAT] Successfully extracted response: {len(final_response)} characters")
                debug_print(f"[CHAT] Response preview: {final_response[:200]}...")
                debug_print(f"[CHAT] Response indicates system instruction awareness: {'data assistant' in final_response.lower() or 'bigquery' in final_response.lower()}")
                
                # Store response in persistent session if configured
                if persistent_session_id:
                    try:
                        _run_asyncio(self._persistent_sessions.add_message(
                            session_id=persistent_session_id,
                            user_id=user_id,
                            message_type="assistant",
                            message_text=final_response
                        ))
                        debug_print(f"[CHAT] Response stored in session {persistent_session_id}")
                    except Exception as e:
                        error_print(f"[ERROR] Failed to store assistant response: {e}")
                
                return final_response
            else:
                # All extraction attempts failed
                error_print(f"[ERROR] Failed to extract valid response after {max_extraction_attempts} attempts")
                error_print(f"[ERROR] Result type: {type(result)}")
                
                # Check if this was an ADK empty response
                if hasattr(result, 'content') and hasattr(result.content, 'parts'):
                    if any(hasattr(part, 'text') and part.text == '' for part in result.content.parts):
                        error_msg = ("I received an empty response from the model. This sometimes happens with complex queries involving donors or financial data. "
                                   "Please try rephrasing your request, or break it down into simpler parts. "
                                   "For example, you could first search for voters in Bernardsville, then filter by party affiliation.")
                        return error_msg
                
                # Generic extraction failure
                error_msg = "I'm having trouble generating a proper response. The agent appears to be working but couldn't extract the response. Please try your request again."
                return error_msg
            
        except Exception as e:
            error_print(f"[ERROR] ADK Runner invocation failed: {e}")
            
            error_str = str(e)
            
            # Check for token limit errors
            if 'exceeds the maximum number of tokens' in error_str or 'token count' in error_str.lower():
                print(f"[INFO] Token limit exceeded. The conversation history is too large.")
                # Provide a helpful message to the user
                return ("I've hit the token limit due to our conversation history being too long. "
                       "This typically happens with complex queries that involve multiple analyses. "
                       "Please try one of these options:\n"
                       "1. Start a new chat session for this complex analysis\n"
                       "2. Break down your request into smaller parts\n"
                       "3. Ask me to focus on specific aspects rather than comprehensive analysis\n\n"
                       "For your strategy question, you could ask me to:\n"
                       "- First analyze voter demographics\n"
                       "- Then analyze donor patterns\n"
                       "- Finally create targeted lists based on specific criteria")
            
            if any(keyword in error_str.lower() for keyword in ['bigquery', 'unrecognized name', 'invalid query', 'query failed']):
                print(f"[INFO] Detected BigQuery-related error, returning user-friendly message")
                return f"I encountered an issue with the database query: {error_str}. Please try rephrasing your question or check the field names you're using. Common field names include: id, demo_party, addr_residential_city, county_name, latitude, longitude."
            
            raise RuntimeError(
                f"Unable to invoke ADK agent using proper Runner patterns: {e}. "
                "This indicates a fundamental issue with ADK integration. "
                "Please check ADK installation and dependencies."
            )

    def __call__(self, prompt: str):
        """Direct Agent invocation bypassing Runner - matches travel-concierge pattern"""
        debug_print(f"[DEBUG] NJVoterChatAgent.__call__ -> direct agent invocation")
        debug_print(f"[DEBUG] User prompt: {prompt[:200]}...")
        
        try:
            from google.genai import types
            message = types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
            
            result = super().generate_content([message])
            
            if hasattr(result, 'text') and result.text:
                debug_print(f"[DEBUG] Direct agent response: {result.text[:200]}...")
                return result.text
            elif hasattr(result, 'content') and hasattr(result.content, 'parts'):
                text_parts = []
                for part in result.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    response = '\n'.join(text_parts)
                    debug_print(f"[DEBUG] Direct agent response: {response[:200]}...")
                    return response
            
            print(f"[WARNING] Unexpected direct agent response structure: {type(result)}")
            return str(result)
            
        except Exception as e:
            error_print(f"[ERROR] Direct agent invocation failed: {e}")
            debug_print(f"[DEBUG] Falling back to Runner approach")
            return self.chat(prompt)
    
    def invoke(self, prompt: str):
        """Alternative invocation method"""
        return self.__call__(prompt)
