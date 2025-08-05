from google.adk.agents import Agent
from .tools.get_assignment_by_id import get_assignment_by_id
from .tools.get_assignment_results_by_student_id import get_assignment_results_by_student_id
from .tools.get_report_card_by_student_id import get_report_card_by_student_id
from .sub_agents.assessor_agent.agent import assessor_agent
from .sub_agents.assignment_generator_general.agent import assignment_generator_general
from .sub_agents.assignment_generator_tailored.agent import assignment_generator_tailored
from .sub_agents.report_card_generator.agent import report_card_generator
from .sub_agents.general_chat_agent.agent import general_chat_agent
from .root_agent_prompt import root_agent_prompt

root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash-lite",
    description="Manager agent that orchestrates workflows and manages data fetching for sub-agents",
    instruction=root_agent_prompt,
    tools=[get_assignment_by_id, get_report_card_by_student_id, get_assignment_results_by_student_id],
    sub_agents=[general_chat_agent, assessor_agent, assignment_generator_general, assignment_generator_tailored, report_card_generator],
)
