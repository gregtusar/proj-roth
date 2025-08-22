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