from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.assessor.agent import assessor
from .sub_agents.assignment_generator_general.agent import assignment_generator_general
from .sub_agents.assignment_generator_tailored.agent import assignment_generator_tailored
from .sub_agents.report_card_generator.agent import report_card_generator

root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash",
    description="Manager agent",
    instruction="""
    You are a manager agent that is responsible for overseeing the work of the other agents.

    Always delegate the task to the appropriate agent. Use your best judgement 
    to determine which agent to delegate to.

    You are responsible for delegating tasks to the following agent:
    - assessor
    - assignment_generator_general
    - assignment_generator_tailored
    - report_card_generator
    """,
    sub_agents=[assessor, assignment_generator_general, assignment_generator_tailored, report_card_generator],
)
