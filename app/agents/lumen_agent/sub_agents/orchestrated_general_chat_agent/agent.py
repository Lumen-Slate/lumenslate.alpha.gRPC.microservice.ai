from google.adk.agents import LlmAgent
from .orchestrated_general_chat_prompt import orchestrated_general_chat_prompt

orchestrated_general_chat_agent = LlmAgent(
    name="general_chat_agent",
    model="gemini-2.5-flash-lite",
    description="Handles casual conversations, greetings, and random queries that don't fit into other specialized agents",
    instruction=orchestrated_general_chat_prompt,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
