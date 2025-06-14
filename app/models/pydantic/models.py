from pydantic import BaseModel, Field
from typing import Optional

class AgentInput(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    query: Optional[str] = Field(None, description="The query or input provided by the user.")