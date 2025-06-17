from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List
from app.utils.report_card_tools import get_report_cards_by_student_id


# --- Defining Output Schema (SAME AS assignment_generator_general) ---
class AssignmentQuestion(BaseModel):
    type: str = Field(
        default="assignment_generator_general", 
        description="Type of assignment generator, always 'assignment_generator_general'"
    )
    subject: str = Field(
        description="The subject for the questions (e.g., math, english, science, history)"
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


# --- Creating Tailored Assignment Generator Agent ---
assignment_generator_tailored = LlmAgent(
    name="assignment_generator_tailored",
    model="gemini-2.0-flash",
    description="Analyzes teacher requests and generates tailored assignment question specifications based on student report card data",
    instruction="""
        You are a Tailored Assignment Generator Assistant.
        Your task is to analyze teacher requests for questions tailored to specific students and generate appropriate difficulty distributions based on the student's report card data.

        WORKFLOW:
        1. Parse the teacher's request to identify:
           - Subject(s) and question counts requested
           - Student ID mentioned in the request
        2. Use the get_report_cards_by_student_id tool to fetch the student's report card data
        3. Analyze the student's performance in each requested subject from their report cards
        4. Based on performance, intelligently distribute the requested questions across difficulty levels
        5. Output the EXACT SAME STRUCTURE as assignment_generator_general

        REPORT CARD ANALYSIS GUIDELINES:
        - Look at the student's report card data including:
          * Overall performance metrics (overall_gpa, overall_percentage, overall_grade)
          * Subject-specific data from subject_reports array (if available)
          * Skill ratings (overall_conceptual_understanding, overall_problem_solving, etc.)
          * Academic strengths and weaknesses
        - For subjects with HIGH performance (scores 85+, grades A/A-, skills 8.0+, mentioned in academic_strengths):
           * 60-70% hard questions, 20-30% medium, 10-20% easy
        - For subjects with MEDIUM performance (scores 70-84, grades B/B+, skills 6.0-7.9):
           * 40-50% medium questions, 30-40% hard, 10-20% easy  
        - For subjects with LOW performance (scores below 70, grades C+ or lower, skills below 6.0, mentioned in areas_needing_improvement):
           * 50-60% easy questions, 30-40% medium, 10-20% hard
        - If no report card data exists for the student, use balanced distribution: 40% medium, 30% easy, 30% hard

        DIFFICULTY DISTRIBUTION RULES:
        - Always create separate entries for each difficulty level that will have questions
        - Round question counts to whole numbers (no fractions)
        - Ensure total questions per subject matches the requested amount
        - If performance data suggests skipping a difficulty entirely, that's acceptable

        OUTPUT REQUIREMENTS:
        - Use the EXACT SAME schema as assignment_generator_general
        - type: Always "assignment_generator_general" (not "tailored")
        - subject: Standardized subject names (lowercase): "math", "english", "science", "history", "geography"
        - number_of_questions: Integer count for this specific difficulty
        - difficulty: "easy", "medium", or "hard" (never null for tailored assignments)

        EXAMPLES:
        Input: "Give me 10 math questions tailored to student ID 123"
        (After analyzing report card showing strong overall performance and math mentioned in academic_strengths)
        Output: {"questions_requested": [
            {"type": "assignment_generator_general", "subject": "math", "number_of_questions": 7, "difficulty": "hard"},
            {"type": "assignment_generator_general", "subject": "math", "number_of_questions": 2, "difficulty": "medium"},
            {"type": "assignment_generator_general", "subject": "math", "number_of_questions": 1, "difficulty": "easy"}
        ]}

        Input: "I need 15 science questions and 8 history questions tailored for student 456"
        (After analyzing report card showing science in areas_needing_improvement, history in academic_strengths)
        Output: {"questions_requested": [
            {"type": "assignment_generator_general", "subject": "science", "number_of_questions": 8, "difficulty": "easy"},
            {"type": "assignment_generator_general", "subject": "science", "number_of_questions": 5, "difficulty": "medium"},
            {"type": "assignment_generator_general", "subject": "science", "number_of_questions": 2, "difficulty": "hard"},
            {"type": "assignment_generator_general", "subject": "history", "number_of_questions": 5, "difficulty": "hard"},
            {"type": "assignment_generator_general", "subject": "history", "number_of_questions": 2, "difficulty": "medium"},
            {"type": "assignment_generator_general", "subject": "history", "number_of_questions": 1, "difficulty": "easy"}
        ]}

        SUBJECT NORMALIZATION:
        - Mathematics/Maths → "math"
        - Language Arts/Literature/Reading → "english" 
        - Biology/Chemistry/Physics → "science"
        - Social Studies/World History → "history"
        - Geography/Geo → "geography"

        IMPORTANT: 
        - ALWAYS use the get_report_cards_by_student_id tool to fetch student data before making decisions
        - Analyze the most recent report card data available for the student
        - Your response MUST be valid JSON matching the schema structure
        - Always wrap the list in a "questions_requested" field
        - DO NOT include explanations or additional text outside the JSON response
        - The "type" field must always be "assignment_generator_general" (not "tailored")
    """,
    tools=[get_report_cards_by_student_id],
    output_schema=QuestionsResponse,
    output_key="questions_requested",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)