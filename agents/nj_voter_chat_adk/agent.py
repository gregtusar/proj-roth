from typing import Any, Dict
import asyncio
import inspect
import time
import os
from google.adk.agents import Agent
from google.adk.runners import Runner

from .config import MODEL, PROJECT_ID, REGION, SYSTEM_PROMPT
from .bigquery_tool import BigQueryReadOnlyTool
from .google_search_tool import GoogleSearchTool
from .geocoding_tool import GeocodingTool
from .voter_list_tool import VoterListTool
from .debug_config import debug_print, error_print

_bq_tool = BigQueryReadOnlyTool()
# GoogleSearchTool will automatically read from secrets
_search_tool = GoogleSearchTool()
# GeocodingTool will use Google Maps API
_geocoding_tool = GeocodingTool()
# VoterListTool for managing saved lists
_list_tool = VoterListTool()

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
    try:
        result = _bq_tool.run(sql)
        debug_print(f"[DEBUG] BigQuery tool returned: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        return result
    except Exception as e:
        error_print(f"[ERROR] BigQuery tool execution failed: {e}")
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
        result = _geocoding_tool.geocode(address)
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
    try:
        # Use the NJ-specific search method to ensure NJ context
        result = _search_tool.search_nj_specific(query, num_results)
        debug_print(f"[DEBUG] Google search returned {result.get('result_count', 0)} results for query: {query[:100]}")
        return result
    except Exception as e:
        error_print(f"[ERROR] Google search failed: {e}")
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
        
        result = _list_tool.save_voter_list(
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
        
        self._session_service = InMemorySessionService()
        self._memory_service = InMemoryMemoryService()
        self._artifact_service = InMemoryArtifactService()
        self._runner = Runner(
            app_name="nj_voter_chat",
            agent=self,
            session_service=self._session_service,
            memory_service=self._memory_service,
            artifact_service=self._artifact_service
        )
        self._user_id = "streamlit_user"
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
            last = None
            async for chunk in agen:
                last = chunk
            return last

        # Get user context
        user_id = os.environ.get("VOTER_LIST_USER_ID", "default_user")
        user_email = os.environ.get("VOTER_LIST_USER_EMAIL", "user@example.com")
        session_id = self._session_id if hasattr(self, '_session_id') else None

        try:
            debug_print("[DEBUG] NJVoterChatAgent.chat -> using proper ADK Runner invocation")
            from google.adk.agents.run_config import RunConfig
            from google.genai import types
            
            # Use the chat session ID if provided, otherwise create a new one
            # This ensures each chat conversation has its own ADK session
            chat_session_id = os.environ.get("CHAT_SESSION_ID")
            
            # If we have a chat session ID and it's different from current, create new ADK session
            if chat_session_id:
                expected_session_id = f"chat_{chat_session_id}"
                if not hasattr(self, '_session_id') or self._session_id != expected_session_id:
                    self._session_id = expected_session_id
                    # Try to create session, but handle case where it might already exist
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
            else:
                # Fallback: create a new session each time if no chat session ID
                self._session_id = f"session_{int(time.time())}_{os.getpid()}"
                try:
                    session = _run_asyncio(self._session_service.create_session(
                        app_name="nj_voter_chat",
                        user_id=self._user_id,
                        session_id=self._session_id
                    ))
                    debug_print(f"[DEBUG] Created new ADK session (no chat session): {self._session_id}")
                except Exception as e:
                    debug_print(f"[DEBUG] Session creation returned: {e}, continuing with session_id: {self._session_id}")
            
            message_content = types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
            debug_print(f"[DEBUG] User prompt being sent with proper ADK message format: {prompt[:200]}...")
            
            debug_print(f"[DEBUG] Message content structure: {message_content}")
            debug_print(f"[DEBUG] Session ID: {self._session_id}, User ID: {self._user_id}")
            
            debug_print(f"[DEBUG] About to call runner.run_async with RunConfig")
            
            # Configure generation parameters via RunConfig
            max_tokens = int(os.environ.get("ADK_MAX_OUTPUT_TOKENS", "32768"))
            run_config = RunConfig()
            
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
            
            if hasattr(result, 'content') and hasattr(result.content, 'parts'):
                debug_print(f"[DEBUG] Result has content with {len(result.content.parts)} parts")
                text_parts = []
                for i, part in enumerate(result.content.parts):
                    debug_print(f"[DEBUG] Part {i}: has_text={hasattr(part, 'text')}, text_length={len(part.text) if hasattr(part, 'text') and part.text else 0}")
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                
                if text_parts:
                    final_response = '\n'.join(text_parts)
                    debug_print(f"[DEBUG] Extracted text response: {final_response[:200]}...")
                    debug_print(f"[DEBUG] Response indicates system instruction awareness: {'data assistant' in final_response.lower() or 'bigquery' in final_response.lower()}")
                    
                    
                    return final_response
                else:
                    print(f"[WARNING] No text content found in response parts: {result.content.parts}")
                    error_msg = "No response content available."
                    return error_msg
            
            print(f"[WARNING] Unexpected response structure: {type(result)}")
            response = str(result)
            return response
            
        except Exception as e:
            error_print(f"[ERROR] ADK Runner invocation failed: {e}")
            
            error_str = str(e)
            
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
