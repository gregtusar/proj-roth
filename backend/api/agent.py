from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from api.auth import get_current_user
from services.agent_service import invoke_agent_tool, get_available_tools

router = APIRouter()

class ToolInvokeRequest(BaseModel):
    tool: str
    args: Dict[str, Any]

class ToolResponse(BaseModel):
    result: Any
    error: Optional[str] = None

@router.post("/invoke", response_model=ToolResponse)
async def invoke_tool(
    request: ToolInvokeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Invoke a specific agent tool directly
    """
    try:
        result = await invoke_agent_tool(request.tool, request.args)
        
        if "error" in result:
            return ToolResponse(result=None, error=result["error"])
        
        return ToolResponse(result=result["result"])
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tool invocation failed: {str(e)}"
        )

@router.get("/tools")
async def list_tools(current_user: dict = Depends(get_current_user)):
    """
    Get list of available agent tools
    """
    return get_available_tools()

class SearchRequest(BaseModel):
    query: str
    analyze: bool = False  # Whether to analyze results with AI

@router.post("/search")
async def search_agent(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Use the agent to search for information
    """
    try:
        # Use the google_search tool to find information
        result = await invoke_agent_tool("google_search", {"query": request.query})
        
        if "error" in result:
            return {"error": result["error"], "results": []}
        
        search_results = result.get("result", {})
        
        # Extract the actual results list from the search response
        if isinstance(search_results, dict):
            actual_results = search_results.get("results", [])
        else:
            actual_results = search_results if isinstance(search_results, list) else []
        
        # If analyze flag is set, process results through the agent
        if request.analyze and actual_results:
            from services.agent_service import process_message_stream
            
            # Create analysis prompt
            # Format search results properly for the prompt
            results_text = "\n".join([
                f"- {r.get('title', 'No title')}: {r.get('snippet', 'No snippet')}"
                for r in actual_results[:5] if isinstance(r, dict)
            ])
            
            analysis_prompt = f"""
            Analyze these search results and provide a concise summary of key findings:
            
            Search Query: {request.query}
            
            Results to analyze:
            {results_text}
            
            Please summarize:
            1. Most relevant information found
            2. Key facts about the person/topic
            3. Notable affiliations or activities
            4. Any public records or mentions
            
            Keep the summary concise and factual.
            """
            
            try:
                # Get agent analysis using the message stream
                summary_parts = []
                async for chunk in process_message_stream(
                    analysis_prompt,
                    session_id=f"search-analysis-{current_user.get('email', 'user')}",
                    user_id=current_user.get('sub'),
                    user_email=current_user.get('email'),
                    model_id="gemini-2.0-flash-exp"
                ):
                    if chunk.get('type') == 'content':
                        summary_parts.append(chunk.get('content', ''))
                
                summary = ''.join(summary_parts)
                
                if summary:
                    return {
                        "summary": summary,
                        "raw_results": actual_results,
                        "full_response": search_results if isinstance(search_results, dict) else {"results": actual_results}
                    }
                else:
                    return search_results if isinstance(search_results, dict) else {"results": actual_results}
                    
            except Exception as analysis_error:
                print(f"Analysis error: {analysis_error}")
                # If analysis fails, return raw results
                return search_results if isinstance(search_results, dict) else {"results": actual_results}
        
        return search_results if isinstance(search_results, dict) else {"results": actual_results}
        
    except Exception as e:
        print(f"Search error: {e}")
        # Return empty results on error rather than failing
        return {"error": str(e), "results": []}