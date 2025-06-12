from pydantic import BaseModel, Field
from fastapi import UploadFile
from typing import Optional

class AgentInput(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    query: str = Field(..., description="The query or input provided by the user.")
    file: Optional[UploadFile] = Field(None, description="Optional file upload (image, audio, etc.)")