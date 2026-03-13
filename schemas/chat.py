from pydantic import BaseModel

class CreateChatReq(BaseModel):
    id: str
    title : str = "New Chat"

class MessageReq(BaseModel):
    content: str
    
    