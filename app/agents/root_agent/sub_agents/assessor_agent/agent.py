from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

class MCQResult(BaseModel):
    question_id: str = Field(..., description="The unique identifier of the MCQ question")
    student_answer: int = Field(..., description="The student's selected answer index")
    correct_answer: int = Field(..., description="The correct answer index")
    points_awarded: int = Field(..., description="Points awarded for this question")
    max_points: int = Field(..., description="Maximum points possible for this question")
    is_correct: bool = Field(..., description="Whether the answer is correct")

class MSQResult(BaseModel):
    question_id: str = Field(..., description="The unique identifier of the MSQ question")
    student_answers: List[int] = Field(..., description="The student's selected answer indices")
    correct_answers: List[int] = Field(..., description="The correct answer indices")
    points_awarded: int = Field(..., description="Points awarded for this question")
    max_points: int = Field(..., description="Maximum points possible for this question")
    is_correct: bool = Field(..., description="Whether the answer is correct")

class NATResult(BaseModel):
    question_id: str = Field(..., description="The unique identifier of the NAT question")
    student_answer: Union[int, float] = Field(..., description="The student's numerical answer")
    correct_answer: Union[int, float] = Field(..., description="The correct numerical answer")
    points_awarded: int = Field(..., description="Points awarded for this question")
    max_points: int = Field(..., description="Maximum points possible for this question")
    is_correct: bool = Field(..., description="Whether the answer is correct")

class SubjectiveGrading(BaseModel):
    question_id: str = Field(..., description="The unique identifier of the subjective question")
    student_answer: str = Field(..., description="The student's written answer")
    ideal_answer: str = Field(..., description="The ideal answer for comparison")
    grading_criteria: List[str] = Field(..., description="List of grading criteria")
    points_awarded: int = Field(..., description="Points awarded based on assessment")
    max_points: int = Field(..., description="Maximum points possible for this question")
    assessment_feedback: str = Field(..., description="Detailed feedback on the student's answer")
    criteria_met: List[str] = Field(..., description="List of criteria that were met by the student")
    criteria_missed: List[str] = Field(..., description="List of criteria that were missed by the student")

class AssessmentResult(BaseModel):
    assignment_id: str = Field(..., description="The unique identifier of the assignment")
    student_id: str = Field(..., description="The unique identifier of the student")
    total_points_awarded: int = Field(..., description="Total points awarded across all questions")
    total_max_points: int = Field(..., description="Total maximum points possible")
    percentage_score: float = Field(..., description="Percentage score (points awarded / max points * 100)")
    mcq_results: List[MCQResult] = Field(default=[], description="Results for MCQ questions")
    msq_results: List[MSQResult] = Field(default=[], description="Results for MSQ questions")
    nat_results: List[NATResult] = Field(default=[], description="Results for NAT questions")
    subjective_results: List[SubjectiveGrading] = Field(default=[], description="Results for subjective questions")

class AssessorResponse(BaseModel):
    assessment_result: AssessmentResult = Field(..., description="The complete assessment result for the student")

assessor_agent = LlmAgent(
    name="assessor_agent",
    model="gemini-2.0-flash",
    description="Assesses student answers for assignments across MCQ, MSQ, NAT, and subjective question types",
    instruction="""
    You are an expert assessor agent that evaluates student performance on assignments. Your role is to:

    1. **For MCQ (Multiple Choice Questions):**
       - Compare the student's selected answer index with the correct answer index
       - Award full points if correct, zero points if incorrect
       - Mark as correct/incorrect accordingly

    2. **For MSQ (Multiple Select Questions):**
       - Compare the student's selected answer indices with the correct answer indices
       - Award full points only if ALL correct options are selected and NO incorrect options are selected
       - Mark as correct/incorrect accordingly

    3. **For NAT (Numerical Answer Type Questions):**
       - Compare the student's numerical answer with the correct numerical answer
       - Award full points if the answer matches exactly (consider reasonable precision for floating-point numbers)
       - Mark as correct/incorrect accordingly

    4. **For Subjective Questions:**
       - Carefully analyze the student's written answer against the ideal answer and grading criteria
       - Award points based on how well the student's answer meets the criteria and matches the ideal answer
       - Provide detailed assessment feedback explaining the grading decision
       - List which criteria were met and which were missed
       - Points should be proportional to the quality and completeness of the answer

    **Assessment Guidelines:**
    - Be fair and consistent in grading
    - For subjective questions, consider partial credit based on the quality of the response
    - Provide constructive feedback that helps the student understand their performance
    - Ensure total points awarded never exceed the maximum points possible
    - Calculate percentage scores accurately

    **Input Format Expected:**
    The input should contain:
    - Assignment data with questions and their correct answers/criteria
    - Student answer sheet with their responses
    - Question details including points allocation

    **Output Requirements:**
    Provide a structured assessment result with:
    - Individual question results grouped by type
    - Total points and percentage calculation
    - Detailed feedback for subjective questions
    """,
    output_schema=AssessorResponse,
    output_key="assignment_result",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
