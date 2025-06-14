from google.adk.agents import LlmAgent
from .general_chat_prompt import general_chat_prompt

general_chat_agent = LlmAgent(
    name="general_chat_agent",
    model="gemini-2.0-flash",
    description="Handles casual conversations, greetings, and random queries that don't fit into other specialized agents",
    instruction=general_chat_prompt,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
) 