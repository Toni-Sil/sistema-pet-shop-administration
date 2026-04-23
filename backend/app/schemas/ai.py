from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    role: str # user, assistant, system
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    context: Optional[Dict[str, Any]] = None

class AIAction(BaseModel):
    label: str
    type: str # navigate, whatsapp, modal
    payload: Any
    target_selector: Optional[str] = None # CSS selector for the UI element to highlight

class ChatResponse(BaseModel):
    response: str
    agent_id: str
    model_used: Optional[str] = None
    suggestions: Optional[List[str]] = None
    actions: Optional[List[AIAction]] = None
