from pydantic import BaseModel, Field

class AgentInput(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    query: str = Field(..., description="The query or input provided by the user.")