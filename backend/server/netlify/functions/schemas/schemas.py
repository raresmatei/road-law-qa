# src/python_be/server/utils/schemas.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RegisterRequest(BaseModel):
    username: str
    password: str

class RegisterResponse(BaseModel):
    id: int
    username: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_admin: bool
    
class MessageItem(BaseModel):
    role: str
    content: str
    created_at: Optional[datetime]

class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None  # omit to start a new chat
    message: str

class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    # history: List[MessageItem]      # full chat history so far
    
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    
class Match(BaseModel):
    score: float
    metadata: dict
    
class QueryResponse(BaseModel):
    matches: list[Match]
    prompt: str
    
class IngestRequest(BaseModel):
    url: str
    
class AnswerResponse(BaseModel):
    answer: str

class MessageItem(BaseModel):
    role: str
    content: str
    created_at: Optional[datetime]

class ConversationSummary(BaseModel):
    conversation_id: int
    created_at: datetime
    summary: Optional[str] = None

class ConversationHistory(BaseModel):
    conversation_id: int
    messages: List[MessageItem]