from pydantic import BaseModel
from typing import Dict, Any

# TODO: Expand this schema as needed
class IngestRequest(BaseModel):
    file_path: str

class ChatMessage(BaseModel):
    role: str 
    content: str
    # TODO: Enforce allowed roles and normalize aliases during validation.
    
class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    thread_id: str | None = None
    # TODO: Validate message count, total input size, and optional history window settings.

class ChatResponse(BaseModel):
    output: Dict[str, Any]
    checkpoint_id: str | None = None
    num_messages: int
    # TODO: Consider flattening the response payload to avoid nested message wrappers.
