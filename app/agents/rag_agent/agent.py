from google.adk.agents import Agent

from .sub_agents.general_chat_agent.agent import general_chat_agent
from .sub_agents.question_creator.agent import question_creator
from .tools.rag_query import rag_query
from .rag_agent_prompt import rag_agent_prompt

rag_agent = Agent(
    name="rag_agent",
    model="gemini-2.0-flash",
    description="Retrieves information from RAG corpus and delegates tasks to appropriate agents",
    tools=[rag_query],
    instruction=rag_agent_prompt,
    sub_agents=[general_chat_agent, question_creator]
)