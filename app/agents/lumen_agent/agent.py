from google.adk.agents import Agent
from .tools.get_assignment_by_id import get_assignment_by_id
from .tools.get_assignment_results_by_student_id import get_assignment_results_by_student_id
from .tools.get_report_card_by_student_id import get_report_card_by_student_id
from .sub_agents.orchestrated_assessor_agent.agent import orchestrated_assessor_agent
from .sub_agents.orchestrated_assignment_generator_general.agent import orchestrated_assignment_generator_general
from .sub_agents.orchestrated_assignment_generator_tailored.agent import orchestrated_assignment_generator_tailored
from .sub_agents.orchestrated_report_card_generator.agent import orchestrated_report_card_generator
from .sub_agents.orchestrated_general_chat_agent.agent import orchestrated_general_chat_agent
from .root_agent_prompt import root_agent_prompt

lumen_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    description="Manager agent that orchestrates workflows and manages data fetching for sub-agents",
    instruction=root_agent_prompt,
    tools=[get_assignment_by_id, get_report_card_by_student_id, get_assignment_results_by_student_id],
    sub_agents=[orchestrated_general_chat_agent, orchestrated_assessor_agent, orchestrated_assignment_generator_general, orchestrated_assignment_generator_tailored, orchestrated_report_card_generator],
)
