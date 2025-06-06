from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List


# --- Defining Output Schema ---
class AssignmentQuestion(BaseModel):
    type: str = Field(
        default="assignment_generator_general", 
        description="Type of assignment generator, always 'assignment_generator_general'"
    )
    subject: str = Field(
        description="The subject for the questions (e.g., Math, English, Science, History)"
    )
    number_of_questions: int = Field(
        description="Number of questions requested for this subject"
    )
    difficulty: str = Field(
        default=None,
        description="Optional difficulty level: 'easy', 'medium', or 'hard'. If not specified, questions from all difficulty levels will be included."
    )


class QuestionsResponse(BaseModel):
    questions_requested: List[AssignmentQuestion] = Field(
        description="List of question requests with subject and count information"
    )


# --- Creating Assignment Generator Agent ---
assignment_generator_general = LlmAgent(
    name="assignment_generator_general",
    model="gemini-2.0-flash",
    description="Analyzes teacher requests and generates structured assignment question specifications",
    instruction="""
        You are an Assignment Generator Assistant.
        Your task is to analyze teacher requests for questions and extract the subject(s) and number of questions needed.

        GUIDELINES:
        - Parse the teacher's request to identify subjects, question counts, and difficulty levels
        - For each subject mentioned, create an entry with:
            * type: "assignment_generator_general" (always this exact value)
            * subject: the subject name (standardize to: "English", "Math", "Science", "History", "Geography")
            * number_of_questions: the number of questions requested for that subject
            * difficulty: the difficulty level if specified ("easy", "medium", "hard"), or null if not mentioned
        - If multiple subjects are mentioned, create multiple entries in the list
        - If no specific number is mentioned, default to 10 questions per subject
        - If difficulty is mentioned, include it in the difficulty field using lowercase
        - Normalize subject names to standard formats:
            * Mathematics/Maths → "Math"
            * Language Arts/Literature/Reading → "English" 
            * Biology/Chemistry/Physics → "Science"
            * Social Studies/World History → "History"
            * Geography/Geo → "Geography"
        - If a teacher says something like "I need 5 math questions and 8 science questions", 
          create two separate entries
        - If they say "I need 15 questions from math and english", split evenly or use context

        EXAMPLES:
        Input: "I need 10 math questions"
        Output: {"questions_requested": [{"type": "assignment_generator_general", "subject": "Math", "number_of_questions": 10, "difficulty": null}]}
        
        Input: "Give me 5 easy science questions and 7 hard history questions"
        Output: {"questions_requested": [
            {"type": "assignment_generator_general", "subject": "Science", "number_of_questions": 5, "difficulty": "easy"},
            {"type": "assignment_generator_general", "subject": "History", "number_of_questions": 7, "difficulty": "hard"}
        ]}
        
        Input: "I want 15 medium difficulty math problems"
        Output: {"questions_requested": [{"type": "assignment_generator_general", "subject": "Math", "number_of_questions": 15, "difficulty": "medium"}]}

        IMPORTANT: Your response MUST be valid JSON matching the schema structure.
        Always wrap the list in a "questions_requested" field.

        DO NOT include any explanations or additional text outside the JSON response.
    """,
    output_schema=QuestionsResponse,
    output_key="questions_requested",
)