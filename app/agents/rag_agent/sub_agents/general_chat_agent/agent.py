from google.adk.agents import LlmAgent
from .general_chat_agent_prompt import general_chat_agent_prompt

general_chat_agent = LlmAgent(
    name="general_chat_agent",
    model="gemini-2.5-flash-lite",
    description="Handles casual conversations, greetings, and random queries. Also knowledgeable about the RAG agent system and can explain its capabilities. Not to be used for generating questions.",
    instruction=general_chat_agent_prompt,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
) 