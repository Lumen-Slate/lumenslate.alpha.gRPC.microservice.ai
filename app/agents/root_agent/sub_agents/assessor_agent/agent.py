from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List, Union
from .assessor_agent_prompt import assessor_agent_prompt

class MCQResult(BaseModel):
    questionId: str = Field(..., description="The unique identifier of the MCQ question", alias="question_id")
    studentAnswer: int = Field(..., description="The student's selected answer index", alias="student_answer")
    correctAnswer: int = Field(..., description="The correct answer index", alias="correct_answer")
    pointsAwarded: int = Field(..., description="Points awarded for this question", alias="points_awarded")
    maxPoints: int = Field(..., description="Maximum points possible for this question", alias="max_points")
    isCorrect: bool = Field(..., description="Whether the answer is correct", alias="is_correct")

class MSQResult(BaseModel):
    questionId: str = Field(..., description="The unique identifier of the MSQ question", alias="question_id")
    studentAnswers: List[int] = Field(..., description="The student's selected answer indices", alias="student_answers")
    correctAnswers: List[int] = Field(..., description="The correct answer indices", alias="correct_answers")
    pointsAwarded: int = Field(..., description="Points awarded for this question", alias="points_awarded")
    maxPoints: int = Field(..., description="Maximum points possible for this question", alias="max_points")
    isCorrect: bool = Field(..., description="Whether the answer is correct", alias="is_correct")

class NATResult(BaseModel):
    questionId: str = Field(..., description="The unique identifier of the NAT question", alias="question_id")
    studentAnswer: Union[int, float] = Field(..., description="The student's numerical answer", alias="student_answer")
    correctAnswer: Union[int, float] = Field(..., description="The correct numerical answer", alias="correct_answer")
    pointsAwarded: int = Field(..., description="Points awarded for this question", alias="points_awarded")
    maxPoints: int = Field(..., description="Maximum points possible for this question", alias="max_points")
    isCorrect: bool = Field(..., description="Whether the answer is correct", alias="is_correct")

class SubjectiveGrading(BaseModel):
    questionId: str = Field(..., description="The unique identifier of the subjective question", alias="question_id")
    studentAnswer: str = Field(..., description="The student's written answer", alias="student_answer")
    idealAnswer: str = Field(..., description="The ideal answer for comparison", alias="ideal_answer")
    gradingCriteria: List[str] = Field(..., description="List of grading criteria", alias="grading_criteria")
    pointsAwarded: int = Field(..., description="Points awarded based on assessment", alias="points_awarded")
    maxPoints: int = Field(..., description="Maximum points possible for this question", alias="max_points")
    assessmentFeedback: str = Field(..., description="Detailed feedback on the student's answer", alias="assessment_feedback")
    criteriaMet: List[str] = Field(..., description="List of criteria that were met by the student", alias="criteria_met")
    criteriaMissed: List[str] = Field(..., description="List of criteria that were missed by the student", alias="criteria_missed")

class AssessmentResult(BaseModel):
    assignmentId: str = Field(..., description="The unique identifier of the assignment", alias="assignment_id")
    studentId: str = Field(..., description="The unique identifier of the student", alias="student_id")
    totalPointsAwarded: int = Field(..., description="Total points awarded across all questions", alias="total_points_awarded")
    totalMaxPoints: int = Field(..., description="Total maximum points possible", alias="total_max_points")
    percentageScore: float = Field(..., description="Percentage score (points awarded / max points * 100)", alias="percentage_score")
    mcqResults: List[MCQResult] = Field(default=[], description="Results for MCQ questions", alias="mcq_results")
    msqResults: List[MSQResult] = Field(default=[], description="Results for MSQ questions", alias="msq_results")
    natResults: List[NATResult] = Field(default=[], description="Results for NAT questions", alias="nat_results")
    subjectiveResults: List[SubjectiveGrading] = Field(default=[], description="Results for subjective questions", alias="subjective_results")

class AssessorResponse(BaseModel):
    assessmentResult: AssessmentResult = Field(..., description="The complete assessment result for the student", alias="assessment_result")

assessor_agent = LlmAgent(
    name="assessor_agent",
    model="gemini-2.5-flash-lite",
    description="Assesses student answers for assignments across MCQ, MSQ, NAT, and subjective question types",
    instruction=assessor_agent_prompt,
    output_schema=AssessorResponse,
    output_key="assignment_result",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
