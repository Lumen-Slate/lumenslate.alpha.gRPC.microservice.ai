from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List
from .assignment_generator_tailored_prompt import assignment_generator_tailored_prompt

# --- Defining Output Schema (SAME AS assignment_generator_general) ---
class AssignmentQuestion(BaseModel):
    type: str = Field(
        default="assignment_generator_general", 
        description="Type of assignment generator, always 'assignment_generator_general'"
    )
    subject: str = Field(
        description="The subject for the questions (e.g., math, english, science, history)"
    )
    numberOfQuestions: int = Field(
        description="Number of questions requested for this subject",
        alias="number_of_questions"
    )
    difficulty: str = Field(
        default=None,
        description="Optional difficulty level: 'easy', 'medium', or 'hard'. If not specified, questions from all difficulty levels will be included."
    )


class QuestionsResponse(BaseModel):
    title: str = Field(
        description="Title of the assignment"
    )
    body: str = Field(
        description="Description of the assignment"
    )
    questionsRequested: List[AssignmentQuestion] = Field(
        description="List of question requests with subject and count information",
        alias="questions_requested"
    )


assignment_generator_tailored = LlmAgent(
    name="assignment_generator_tailored",
    model="gemini-2.5-flash-lite",
    description="Analyzes teacher requests and generates tailored assignment question specifications based on student report card data provided by the root agent",
    instruction=assignment_generator_tailored_prompt,
    output_schema=QuestionsResponse,
    output_key="questions_requested",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)