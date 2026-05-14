"""
MongoDB Document Models for Session Storage
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """Single chat message model"""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    sender: str  # "User" or "AI"
    message: str
    response_type: Optional[str] = None  # "aws_query_response", "requirement_follow_up", etc.

class ExtractedRequirements(BaseModel):
    """Structured requirements JSON"""
    project_type: Optional[str] = None
    scalability: Optional[str] = None
    storage: Optional[str] = None
    security: Optional[str] = None
    compute: Optional[str] = None
    region: Optional[str] = None
    database: Optional[str] = None
    networking: Optional[str] = None
    deployment_preferences: Optional[str] = None

class SessionDocument(BaseModel):
    """MongoDB session document model"""
    session_id: str
    user_id: Optional[str] = None
    mode: str  # "aws_chat" or "requirement_extraction"
    chat_history: List[ChatMessage] = Field(default_factory=list)
    extracted_requirements: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_complete: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    # Follow-up clarification state
    pending_clarification: bool = False
    clarification_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # clarification_context shape:
    # { "original_query": str, "options_offered": List[str], "round": int }
