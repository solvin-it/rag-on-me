from pydantic import BaseModel
from typing import Dict, Any

# TODO: Expand this schema as needed
class IngestRequest(BaseModel):
    file_path: str

class ChatMessage(BaseModel):
    role: str 
    content: str
    
class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    thread_id: str | None = None

class ChatResponse(BaseModel):
    output: Dict[str, Any]
    checkpoint_id: str | None = None
    num_messages: int