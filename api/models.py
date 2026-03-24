from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class IntentClassification(BaseModel):
    intent: str
    confidence: float
    reasoning: str

class ChatResponse(BaseModel):
    intent_classification: IntentClassification
    response_type: str
    question_analysis: Optional[str] = None
    answer: Optional[str] = None
    tips: Optional[str] = None
    session_id: Optional[str] = None