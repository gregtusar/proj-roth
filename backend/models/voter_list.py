from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VoterList(BaseModel):
    id: str
    user_id: str
    user_email: str
    name: str
    description: Optional[str] = ""
    query: str
    prompt: Optional[str] = None
    row_count: int = 0
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

class CreateListRequest(BaseModel):
    name: str
    description: Optional[str] = None
    query: str
    prompt: Optional[str] = None
    row_count: Optional[int] = 0

class UpdateListRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    query: Optional[str] = None
    prompt: Optional[str] = None
    row_count: Optional[int] = None

class ListResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    query: str
    prompt: Optional[str]
    row_count: int
    created_at: str
    updated_at: str