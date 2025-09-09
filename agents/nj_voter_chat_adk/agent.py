from typing import Any, Dict, Optional, List
import asyncio
import inspect
import time
import os
import sys
import json
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
from .pdl_tool import PDLEnrichmentTool
from .google_docs_tool import GoogleDocsTool
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
    Enhanced to handle all ADK response formats including streaming and edge cases.
    
    Args:
        result: The response object from the ADK agent
        attempt_num: Current attempt number for logging
        max_attempts: Maximum number of extraction attempts
        
    Returns:
        str: Extracted response text or None if extraction fails
    """
    debug_print(f"[EXTRACT] Attempt {attempt_num}/{max_attempts} - Extracting response from {type(result)}")
    
    # Track if we found an explicitly empty response
    found_empty_response = False
    extracted_texts = []
    
    # Method 1: Standard ADK response with content.parts
    if hasattr(result, 'content') and hasattr(result.content, 'parts'):
        debug_print(f"[EXTRACT] Method 1: Found content with {len(result.content.parts)} parts")
        
        for i, part in enumerate(result.content.parts):
            part_info = {
                'has_text': hasattr(part, 'text'),
                'text_is_none': hasattr(part, 'text') and part.text is None,
                'text_is_empty': hasattr(part, 'text') and part.text == '',
                'text_length': len(part.text) if hasattr(part, 'text') and part.text else 0
            }
            debug_print(f"[EXTRACT] Part {i}: {part_info}")
            
            if hasattr(part, 'text'):
                if part.text:
                    # Found actual text content
                    text = part.text.strip()
                    if text:
                        extracted_texts.append(text)
                        debug_print(f"[EXTRACT] Part {i}: Extracted {len(text)} chars")
                elif part.text == '':
                    # Explicitly empty response from ADK
                    found_empty_response = True
                    debug_print(f"[EXTRACT] Part {i}: Empty text (ADK returned no content)")
                elif part.text is None:
                    # None response - different from empty string
                    debug_print(f"[EXTRACT] Part {i}: None text (no response generated)")
            
            # Also check for other part types (tool_use, function_call, etc.)
            if hasattr(part, 'tool_use'):
                debug_print(f"[EXTRACT] Part {i}: Contains tool_use")
            if hasattr(part, 'function_call'):
                debug_print(f"[EXTRACT] Part {i}: Contains function_call")
        
        if extracted_texts:
            # Successfully extracted text from parts
            final_response = '\n'.join(extracted_texts)
            debug_print(f"[EXTRACT] Method 1 SUCCESS: Extracted {len(final_response)} characters from {len(extracted_texts)} parts")
            debug_print(f"[EXTRACT] Response preview: {final_response[:200]}...")
            return final_response
        elif found_empty_response:
            # ADK explicitly returned empty - this is different from extraction failure
            debug_print(f"[EXTRACT] Method 1: ADK returned empty response (not a failure)")
            error_print(f"[EXTRACT] Model returned empty response. Possible reasons:")
            error_print(f"  - Request triggered safety filters")
            error_print(f"  - Model couldn't process the specific request")
            error_print(f"  - Temporary model issue")
            # Return a user-friendly message instead of None
            return "I apologize, but I couldn't generate a response for your request. Please try rephrasing your question or asking something else."
    
    # Method 2: Direct text attribute
    if hasattr(result, 'text'):
        if result.text:
            text = result.text.strip()
            if text:
                debug_print(f"[EXTRACT] Method 2 SUCCESS: Direct text attribute, {len(text)} characters")
                return text
        elif result.text == '':
            found_empty_response = True
            debug_print(f"[EXTRACT] Method 2: Empty text attribute")
    
    # Method 3: Response as dict with various possible keys
    if isinstance(result, dict):
        debug_print(f"[EXTRACT] Method 3: Dict response with keys: {list(result.keys())}")
        
        # Try common response keys in priority order
        priority_keys = ['text', 'output', 'response', 'content', 'message', 'answer', 'result']
        for key in priority_keys:
            if key in result:
                value = result[key]
                if value:
                    if isinstance(value, str):
                        text = value.strip()
                        if text:
                            debug_print(f"[EXTRACT] Method 3 SUCCESS: Found text in '{key}' key ({len(text)} chars)")
                            return text
                    elif hasattr(value, '__dict__'):
                        # Nested object - recursively extract
                        debug_print(f"[EXTRACT] Method 3: Nested object in '{key}', recursing")
                        nested_text = extract_response_text(value, attempt_num + 1, max_attempts)
                        if nested_text:
                            return nested_text
                elif value == '':
                    found_empty_response = True
                    debug_print(f"[EXTRACT] Method 3: Empty value in '{key}' key")
    
    # Method 4: List of responses (batch or streaming responses)
    if isinstance(result, list) and result:
        debug_print(f"[EXTRACT] Method 4: List response with {len(result)} items")
        
        list_texts = []
        for idx, item in enumerate(result):
            if isinstance(item, str):
                text = item.strip()
                if text:
                    list_texts.append(text)
                    debug_print(f"[EXTRACT] Method 4: Item {idx} is string ({len(text)} chars)")
            elif hasattr(item, 'content') or hasattr(item, 'text'):
                # Recursive extraction for structured items
                item_text = extract_response_text(item, attempt_num + 1, max_attempts)
                if item_text:
                    list_texts.append(item_text)
                    debug_print(f"[EXTRACT] Method 4: Item {idx} extracted ({len(item_text)} chars)")
        
        if list_texts:
            # Check if texts are incremental or duplicates
            unique_texts = []
            seen = set()
            for text in list_texts:
                if text not in seen:
                    unique_texts.append(text)
                    seen.add(text)
            
            if len(unique_texts) == 1:
                debug_print(f"[EXTRACT] Method 4 SUCCESS: Single unique text from list")
                return unique_texts[0]
            else:
                combined = ' '.join(unique_texts)
                debug_print(f"[EXTRACT] Method 4 SUCCESS: Combined {len(unique_texts)} unique texts")
                return combined
    
    # Method 5: Check for nested response attributes
    nested_attrs = ['response', 'output', 'result', 'data', 'message', 'completion']
    for attr in nested_attrs:
        if hasattr(result, attr):
            nested_result = getattr(result, attr)
            if nested_result and nested_result != result:  # Avoid infinite recursion
                debug_print(f"[EXTRACT] Method 5: Trying nested attribute '{attr}'")
                nested_text = extract_response_text(nested_result, attempt_num + 1, max_attempts)
                if nested_text:
                    return nested_text
    
    # Method 6: String conversion fallback (last resort)
    if result is not None and not found_empty_response:
        try:
            result_str = str(result).strip()
            # Filter out unhelpful string representations
            if (result_str and 
                result_str != 'None' and 
                not result_str.startswith('<') and  # Avoid object repr strings
                not result_str.startswith('object at') and
                len(result_str) > 10):  # Minimum meaningful length
                debug_print(f"[EXTRACT] Method 6 SUCCESS: String conversion fallback, {len(result_str)} characters")
                return result_str
        except Exception as e:
            debug_print(f"[EXTRACT] Method 6 failed: String conversion error: {e}")
    
    # All methods failed
    if found_empty_response:
        # We found empty responses - this is different from extraction failure
        debug_print(f"[EXTRACT] Found empty response markers - model returned no content")
        return "I couldn't generate a response for your request. Please try rephrasing your question."
    else:
        # Complete extraction failure
        error_msg = f"[EXTRACT] All extraction methods failed for {type(result)}"
        debug_print(error_msg)
        
        if hasattr(result, '__dict__'):
            attrs = list(result.__dict__.keys())[:10]  # Limit to first 10 attrs
            debug_print(f"[EXTRACT] Object attributes: {attrs}")
        
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
_pdl_tool = None

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

def _get_pdl_tool():
    global _pdl_tool
    if _pdl_tool is None:
        _pdl_tool = PDLEnrichmentTool()
    return _pdl_tool

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

def pdl_batch_enrichment(master_ids: List[str], min_likelihood: int = 5, skip_existing: bool = True, force: bool = False) -> Dict[str, Any]:
    """Batch enrichment from People Data Labs for multiple voters (up to 100 at once).
    
    IMPORTANT COST OPTIMIZATION: Use this for lists of 3+ people instead of individual enrichments.
    - Batch processing is MUCH faster: 100 people in ~2 seconds vs ~2 minutes individually
    - Same cost per successful match ($0.25 each), but more efficient
    - Automatically skips recently enriched individuals to save money
    
    Args:
        master_ids (List[str]): List of voter master_ids to enrich (max 100)
        min_likelihood (int): Minimum confidence score (1-10, default 5)
                             Lower = more matches but less accurate (try 4 for max coverage)
                             Higher = fewer matches but more accurate (8 for high confidence)
                             Recommended: Start with 5, then try 4 if no matches
        skip_existing (bool): Skip individuals enriched in last 6 months (default True)
        force (bool): Bypass cost confirmations (use carefully!)
    
    Returns:
        Dict[str, Any]: Batch results including:
                       - batch_summary: Stats on successful/failed enrichments
                       - enriched: List of successfully enriched individuals
                       - already_enriched: Individuals skipped (already have data)
                       - cost: Total cost for new enrichments
                       - suggestions: If no matches, provides helpful next steps
    
    Examples:
        >>> # Enrich a list of high-value donors
        >>> master_ids = ["voter123", "voter456", "voter789"]
        >>> pdl_batch_enrichment(master_ids, min_likelihood=5)
        {"status": "batch_complete", "batch_summary": {"successful": 2, "cost": 0.50}, ...}
    """
    try:
        tool = _get_pdl_tool()
        
        print(f"\n[TOOL INVOKED] pdl_batch_enrichment")
        print(f"[BATCH SIZE] {len(master_ids)} individuals")
        print(f"[PARAMETERS] min_likelihood={min_likelihood}, skip_existing={skip_existing}")
        
        _emit_reasoning_event("tool_start", {
            "tool": "pdl_batch_enrichment",
            "batch_size": len(master_ids),
            "parameters": {"min_likelihood": min_likelihood, "skip_existing": skip_existing}
        })
        
        result = tool.trigger_batch_enrichment(
            master_ids=master_ids,
            min_likelihood=min_likelihood,
            skip_existing=skip_existing,
            require_confirmation=not force
        )
        
        _emit_reasoning_event("tool_end", {
            "tool": "pdl_batch_enrichment",
            "status": result.get("status"),
            "summary": result.get("batch_summary", {})
        })
        
        # Print summary for console
        if result.get("status") == "batch_complete":
            summary = result.get("batch_summary", {})
            print(f"[BATCH COMPLETE] {summary.get('successful', 0)}/{summary.get('attempted', 0)} enriched")
            print(f"[COST] ${summary.get('cost', 0):.2f}")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Batch enrichment failed: {str(e)}")
        _emit_reasoning_event("tool_error", {
            "tool": "pdl_batch_enrichment",
            "error": str(e)
        })
        return {
            "status": "error",
            "error": str(e),
            "message": "Batch enrichment failed"
        }

def pdl_enrichment(master_id: str, action: str = "fetch", min_likelihood: int = 8, force: bool = False) -> Dict[str, Any]:
    """Fetch or trigger People Data Labs enrichment for a voter.
    
    IMPORTANT: PDL enrichment costs $0.25 per API call. Use sparingly and only for high-value voters.
    
    Args:
        master_id (str): The voter's master_id from the database
        action (str): Either "fetch" to get existing data or "enrich" to trigger new enrichment
        min_likelihood (int): For enrichment, minimum confidence score (1-10, default 8)
                             Lower values = more matches but less accurate
                             Higher values = fewer matches but more accurate
        force (bool): For enrichment, bypass cost controls and existing data checks (use carefully!)
    
    Returns:
        Dict[str, Any]: Contains enrichment data or status information including:
                       - For existing data: Full PDL profile with job, education, social media, etc.
                       - For new enrichment: Cost information and enrichment results
                       - For errors: Status and error messages
    
    Examples:
        >>> # First check if data exists
        >>> pdl_enrichment("abc123", action="fetch")
        {"status": "found", "enrichment": {...full PDL data...}}
        
        >>> # Trigger new enrichment if needed
        >>> pdl_enrichment("abc123", action="enrich", min_likelihood=8)
        {"status": "enriched", "cost": 0.25, "enrichment": {...}}
    """
    try:
        tool = _get_pdl_tool()
        
        if action == "fetch":
            return tool.get_enrichment(master_id)
        elif action == "enrich":
            return tool.trigger_enrichment(
                master_id,
                min_likelihood=min_likelihood,
                skip_if_exists=not force,
                require_confirmation=not force
            )
        elif action == "session_summary":
            return tool.get_session_summary()
        else:
            return {
                "status": "error",
                "message": f"Invalid action: {action}. Use 'fetch' or 'enrich'"
            }
    except Exception as e:
        error_print(f"[ERROR] PDL enrichment failed: {e}")
        return {
            "status": "error",
            "error": f"PDL enrichment failed: {str(e)}"
        }

def create_google_doc(title: str, content: str = "", user_id: Optional[str] = None) -> str:
    """Create a new Google Doc with the specified title and content.
    
    Args:
        title (str): The title of the document
        content (str): The initial content of the document (optional)
        user_id (str): The ID of the user creating the document (optional, will use session if not provided)
        
    Returns:
        str: JSON string with document details including doc_id, title, and URL
    """
    import asyncio
    
    async def _create_doc():
        tool = GoogleDocsTool()
        
        # Get user_id from session if not provided
        nonlocal user_id
        if not user_id:
            from .user_context import get_current_user_id
            user_id = get_current_user_id()
            if not user_id:
                return json.dumps({
                    'error': 'No user context available. Please ensure you are logged in.'
                })
        
        result = await tool.create_document(title=title, content=content, user_id=user_id)
        debug_print(f"[GOOGLE_DOCS] Document created: {result}")
        return result
    
    try:
        # Try to get the running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, run the coroutine in the existing loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _create_doc())
                return future.result()
        except RuntimeError:
            # No running loop, create a new one
            return asyncio.run(_create_doc())
    except Exception as e:
        error_print(f"[ERROR] Failed to create Google Doc: {e}")
        return json.dumps({
            'error': f'Failed to create document: {str(e)}'
        })

def read_google_doc(doc_id: str, user_id: Optional[str] = None) -> str:
    """Read the content of a Google Doc.
    
    Args:
        doc_id (str): The ID of the document to read
        user_id (str): The ID of the user requesting the document (optional, will use session if not provided)
        
    Returns:
        str: JSON string with document content including doc_id, title, content, and URL
    """
    import asyncio
    
    async def _read_doc():
        tool = GoogleDocsTool()
        
        # Get user_id from session if not provided
        nonlocal user_id
        if not user_id:
            from .user_context import get_current_user_id
            user_id = get_current_user_id()
            if not user_id:
                return json.dumps({
                    'error': 'No user context available. Please ensure you are logged in.'
                })
        
        result = await tool.read_document(doc_id=doc_id, user_id=user_id)
        debug_print(f"[GOOGLE_DOCS] Document read: {doc_id}")
        return result
    
    try:
        # Try to get the running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, run the coroutine in the existing loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _read_doc())
                return future.result()
        except RuntimeError:
            # No running loop, create a new one
            return asyncio.run(_read_doc())
    except Exception as e:
        error_print(f"[ERROR] Failed to read Google Doc: {e}")
        return json.dumps({
            'error': f'Failed to read document: {str(e)}'
        })

def list_google_docs(user_id: Optional[str] = None) -> str:
    """List all Google Docs owned by the user.
    
    Args:
        user_id (str): The ID of the user (optional, will use session if not provided)
        
    Returns:
        str: JSON string with list of documents including doc_id, title, created_at, updated_at, and URL
    """
    import asyncio
    
    async def _list_docs():
        tool = GoogleDocsTool()
        
        # Get user_id from session if not provided
        nonlocal user_id
        if not user_id:
            from .user_context import get_current_user_id
            user_id = get_current_user_id()
            if not user_id:
                return json.dumps({
                    'error': 'No user context available. Please ensure you are logged in.'
                })
        
        result = await tool.list_documents(user_id=user_id)
        debug_print(f"[GOOGLE_DOCS] Listed documents for user {user_id}")
        return result
    
    try:
        # Try to get the running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, run the coroutine in the existing loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _list_docs())
                return future.result()
        except RuntimeError:
            # No running loop, create a new one
            return asyncio.run(_list_docs())
    except Exception as e:
        error_print(f"[ERROR] Failed to list Google Docs: {e}")
        return json.dumps({
            'error': f'Failed to list documents: {str(e)}'
        })

def update_google_doc(doc_id: str, content: str, user_id: Optional[str] = None) -> str:
    """Update the content of a Google Doc.
    
    Args:
        doc_id (str): The ID of the document to update
        content (str): The new content for the document
        user_id (str): The ID of the user updating the document (optional, will use session if not provided)
        
    Returns:
        str: JSON string with update status
    """
    import asyncio
    
    async def _update_doc():
        tool = GoogleDocsTool()
        
        # Get user_id from session if not provided
        nonlocal user_id
        if not user_id:
            from .user_context import get_current_user_id
            user_id = get_current_user_id()
            if not user_id:
                return json.dumps({
                    'error': 'No user context available. Please ensure you are logged in.'
                })
        
        result = await tool.update_document(doc_id=doc_id, content=content, user_id=user_id)
        debug_print(f"[GOOGLE_DOCS] Document updated: {doc_id}")
        return result
    
    try:
        # Try to get the running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, run the coroutine in the existing loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _update_doc())
                return future.result()
        except RuntimeError:
            # No running loop, create a new one
            return asyncio.run(_update_doc())
    except Exception as e:
        error_print(f"[ERROR] Failed to update Google Doc: {e}")
        return json.dumps({
            'error': f'Failed to update document: {str(e)}'
        })

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
            tools=[
                bigquery_select, 
                google_search, 
                geocode_address, 
                save_voter_list, 
                pdl_enrichment,
                pdl_batch_enrichment,
                create_google_doc,
                read_google_doc,
                list_google_docs,
                update_google_doc
            ], 
            instruction=SYSTEM_PROMPT
        )
        debug_print(f"[DEBUG] Agent initialized successfully with instruction parameter and tools: bigquery_select, google_search, geocode_address, save_voter_list, pdl_enrichment, pdl_batch_enrichment, create_google_doc, read_google_doc, list_google_docs, update_google_doc")
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
            # Use the improved ADK chunk handler for proper partial flag handling
            from .adk_chunk_handler import ADKChunkHandler
            
            handler = ADKChunkHandler()
            all_chunks = []
            last = None
            chunk_count = 0
            total_size = 0
            
            # Collect all chunks while processing them properly
            async for chunk in agen:
                chunk_count += 1
                chunk_str = str(chunk)
                total_size += len(chunk_str)
                
                # Store chunk for final processing
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
            
            # IMPROVED: Robust ADK response extraction handling all formats
            combined_text = ""
            final_chunk = None
            text_parts = []
            has_empty_response = False
            
            print(f"[ADK] Processing {len(all_chunks)} chunks with correct partial flag logic")
            
            # First pass: Analyze chunk structure and collect all text
            for i, chunk in enumerate(all_chunks):
                chunk_info = {
                    'index': i + 1,
                    'type': type(chunk).__name__,
                    'has_content': hasattr(chunk, 'content'),
                    'has_parts': False,
                    'text_found': False,
                    'text_length': 0
                }
                
                # Method 1: Standard ADK response with content.parts
                if hasattr(chunk, 'content') and hasattr(chunk.content, 'parts'):
                    chunk_info['has_parts'] = True
                    parts_count = len(chunk.content.parts) if chunk.content.parts else 0
                    
                    for j, part in enumerate(chunk.content.parts):
                        if hasattr(part, 'text'):
                            if part.text:
                                text = part.text.strip()
                                if text:
                                    text_parts.append(text)
                                    chunk_info['text_found'] = True
                                    chunk_info['text_length'] = len(text)
                                    print(f"[ADK] Chunk {i+1}.{j+1}: Found text ({len(text)} chars)")
                            elif part.text == '':
                                # Explicitly empty response from ADK
                                has_empty_response = True
                                print(f"[ADK] Chunk {i+1}.{j+1}: Empty text response (ADK returned no content)")
                
                # Method 2: Direct text attribute on chunk
                elif hasattr(chunk, 'text') and chunk.text:
                    text = chunk.text.strip()
                    if text:
                        text_parts.append(text)
                        chunk_info['text_found'] = True
                        chunk_info['text_length'] = len(text)
                        print(f"[ADK] Chunk {i+1}: Direct text attribute ({len(text)} chars)")
                
                # Method 3: Check for response/output attributes
                elif hasattr(chunk, 'response') and chunk.response:
                    if isinstance(chunk.response, str):
                        text = chunk.response.strip()
                        if text:
                            text_parts.append(text)
                            chunk_info['text_found'] = True
                            chunk_info['text_length'] = len(text)
                            print(f"[ADK] Chunk {i+1}: Response attribute ({len(text)} chars)")
                
                # Keep track of chunks with content structure for final result
                if chunk_info['text_found'] or (chunk_info['has_parts'] and not has_empty_response):
                    final_chunk = chunk
                
                # Log chunk analysis
                if chunk_info['text_found']:
                    print(f"[ADK] Chunk {chunk_info['index']}: {chunk_info['type']} - {chunk_info['text_length']} chars extracted")
                elif chunk_info['has_parts']:
                    print(f"[ADK] Chunk {chunk_info['index']}: {chunk_info['type']} - has parts but no text")
                else:
                    print(f"[ADK] Chunk {chunk_info['index']}: {chunk_info['type']} - no recognizable content structure")
            
            # Handle incremental vs complete responses
            # Check if we have partial/streaming indicators
            if text_parts:
                # Check for duplicate content (sometimes ADK sends the same response multiple times)
                unique_texts = []
                seen = set()
                for text in text_parts:
                    if text not in seen:
                        unique_texts.append(text)
                        seen.add(text)
                
                # Determine if responses are incremental or complete replacements
                if len(unique_texts) == 1:
                    # Same text repeated - use it
                    combined_text = unique_texts[0]
                    print(f"[ADK] Single unique response found: {len(combined_text)} chars")
                else:
                    # Multiple different texts - check if they're incremental
                    # If each subsequent text contains the previous, it's a complete replacement
                    is_replacement = True
                    for i in range(1, len(text_parts)):
                        if text_parts[i-1] not in text_parts[i]:
                            is_replacement = False
                            break
                    
                    if is_replacement and text_parts:
                        # Use the last (most complete) response
                        combined_text = text_parts[-1]
                        print(f"[ADK] Using last complete response: {len(combined_text)} chars")
                    else:
                        # Incremental responses - combine them
                        combined_text = ' '.join(unique_texts)
                        print(f"[ADK] Combined {len(unique_texts)} incremental responses: {len(combined_text)} chars")
            
            # Prepare final result
            if combined_text and final_chunk:
                print(f"[ADK] Final response extracted: {len(combined_text)} chars")
                
                # Try to preserve chunk structure while updating with complete text
                if hasattr(final_chunk, 'content') and hasattr(final_chunk.content, 'parts'):
                    if final_chunk.content.parts and hasattr(final_chunk.content.parts[0], 'text'):
                        final_chunk.content.parts[0].text = combined_text
                        print(f"[ADK] Updated final chunk with complete response")
                elif hasattr(final_chunk, 'text'):
                    final_chunk.text = combined_text
                    print(f"[ADK] Updated final chunk text attribute")
                
                # Emit final response info for debugging
                _emit_reasoning_event("adk_response_extracted", {
                    "total_chunks": len(all_chunks),
                    "text_chunks_found": len(text_parts),
                    "unique_responses": len(unique_texts) if 'unique_texts' in locals() else 1,
                    "final_length": len(combined_text),
                    "has_empty_response": has_empty_response
                })
                
                return final_chunk
            elif has_empty_response:
                # ADK explicitly returned empty response
                print(f"[ADK] WARNING: ADK returned empty response - model may have refused or failed to process")
                error_print(f"[ADK] Empty response from model. This can happen when:")
                error_print(f"  - The request violates model safety guidelines")
                error_print(f"  - The model cannot process the specific request format")
                error_print(f"  - There's a temporary model issue")
                
                # Return last chunk but mark it as empty
                if last and hasattr(last, 'content') and hasattr(last.content, 'parts'):
                    if last.content.parts and hasattr(last.content.parts[0], 'text'):
                        last.content.parts[0].text = "I encountered an issue generating a response. Please try rephrasing your question or try again."
                
                return last
            else:
                # No text found at all
                print(f"[ADK] ERROR: No text content found in any of {len(all_chunks)} chunks")
                error_print(f"[ADK] Failed to extract response from chunks. Debug info:")
                for i, chunk in enumerate(all_chunks[-3:]):  # Log last 3 chunks for debugging
                    error_print(f"  Chunk {i}: type={type(chunk).__name__}, attrs={list(chunk.__dict__.keys()) if hasattr(chunk, '__dict__') else 'N/A'}")
                
                return last

        # Get user context
        user_id = os.environ.get("VOTER_LIST_USER_ID", "default_user")
        user_email = os.environ.get("VOTER_LIST_USER_EMAIL", "user@example.com")
        chat_session_id = os.environ.get("CHAT_SESSION_ID")
        session_id = self._session_id if hasattr(self, '_session_id') else None
        
        # Only use the session_id passed from WebSocket for loading history
        # DON'T create sessions here - WebSocket handler already creates them
        # This prevents duplicate/orphan sessions from being created
        persistent_session_id = chat_session_id  # Use the session created by WebSocket
        
        # Note: We no longer call create_or_get_session here because:
        # 1. WebSocket handler creates the session if needed (websocket.py lines 130-135)
        # 2. WebSocket handler saves all messages (websocket.py lines 158, 247)
        # 3. Agent only needs the session_id to load conversation history
        
        if not persistent_session_id:
            print(f"[Agent] No session_id provided, conversation history won't be available")
        else:
            print(f"[Agent] Using session_id from WebSocket: {persistent_session_id}")

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
                
                # REMOVED: Don't save assistant message here - WebSocket handler already saves it
                # This was causing duplicate messages in Firestore
                # The WebSocket handler in backend/core/websocket.py handles all message persistence
                
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
            
            # Check for corrupted message history (data/text conflict)
            if "oneof field 'data' is already set" in error_str or "Cannot set 'text'" in error_str:
                print(f"[INFO] Detected corrupted conversation history with data/text conflict")
                print(f"[INFO] This happens when the conversation history contains malformed messages")
                
                # Clear the corrupted session and retry with a fresh one
                old_session_id = self._session_id
                self._session_id = f"fresh_{int(time.time())}_{os.getpid()}"
                self._conversation_history = []
                
                print(f"[INFO] Creating fresh session {self._session_id} to bypass corrupted history")
                
                try:
                    # Create a completely new session
                    session = _run_asyncio(self._session_service.create_session(
                        app_name="nj_voter_chat",
                        user_id=self._user_id,
                        session_id=self._session_id
                    ))
                    print(f"[INFO] Created fresh ADK session, retrying request")
                    
                    # Retry the request with the fresh session
                    return self.chat(prompt)
                    
                except Exception as retry_error:
                    print(f"[ERROR] Failed to recover with fresh session: {retry_error}")
                    return ("I encountered an issue with the conversation history that appears to be corrupted. "
                           "This can happen when mixing different types of content in messages. "
                           "Please start a new chat session to continue. "
                           "If this persists, try clearing your browser cache and refreshing the page.")
            
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
