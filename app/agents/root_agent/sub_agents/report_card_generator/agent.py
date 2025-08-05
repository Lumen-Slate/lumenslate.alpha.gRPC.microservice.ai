from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List
from .report_card_generator_prompt import report_card_generator_prompt

class AssignmentSummary(BaseModel):
    assignmentId: str = Field(..., description="The unique identifier of the assignment", alias="assignment_id")
    assignmentTitle: str = Field(..., description="The title of the assignment", alias="assignment_title")
    percentageScore: float = Field(..., description="Percentage score for this assignment", alias="percentage_score")
    subject: str = Field(..., description="Subject of the assignment")

class SubjectPerformance(BaseModel):
    subjectName: str = Field(..., description="Name of the subject", alias="subject_name")
    percentageScore: float = Field(..., description="Overall percentage score in this subject", alias="percentage_score")
    assignmentCount: int = Field(..., description="Number of assignments completed in this subject", alias="assignment_count")
    
    # Question type breakdown within this subject
    mcqAccuracy: float = Field(default=0.0, description="MCQ accuracy rate in this subject", alias="mcq_accuracy")
    msqAccuracy: float = Field(default=0.0, description="MSQ accuracy rate in this subject", alias="msq_accuracy")
    natAccuracy: float = Field(default=0.0, description="NAT accuracy rate in this subject", alias="nat_accuracy")
    subjectiveAvgScore: float = Field(default=0.0, description="Average score on subjective questions in this subject", alias="subjective_avg_score")
    
    # Subject-specific analysis
    strengths: List[str] = Field(default=[], description="Top strengths in this subject")
    weaknesses: List[str] = Field(default=[], description="Areas needing improvement in this subject")
    improvementTrend: str = Field(default="stable", description="Performance trend in this subject", alias="improvement_trend")

class OverallPerformance(BaseModel):
    totalAssignmentsCompleted: int = Field(..., description="Total number of assignments completed", alias="total_assignments_completed")
    overallPercentage: float = Field(..., description="Overall percentage score across all assignments", alias="overall_percentage")
    improvementTrend: str = Field(..., description="Overall performance trend (improving, stable, declining)", alias="improvement_trend")
    strongestQuestionType: str = Field(..., description="Question type where student performs best", alias="strongest_question_type")
    weakestQuestionType: str = Field(..., description="Question type needing most improvement", alias="weakest_question_type")

class StudentInsights(BaseModel):
    keyStrengths: List[str] = Field(..., description="Top 3 academic strengths", alias="key_strengths")
    areasForImprovement: List[str] = Field(..., description="Top 3 areas needing improvement", alias="areas_for_improvement")
    recommendedActions: List[str] = Field(..., description="Top 3 specific recommendations", alias="recommended_actions")

class ReportCard(BaseModel):
    studentId: str = Field(..., description="The unique identifier of the student", alias="student_id")
    studentName: str = Field(..., description="The name of the student", alias="student_name")
    reportPeriod: str = Field(..., description="The time period this report covers", alias="report_period")
    generationDate: str = Field(..., description="Date when the report card was generated", alias="generation_date")
    
    # Performance Data
    overallPerformance: OverallPerformance = Field(..., description="Overall academic performance summary", alias="overall_performance")
    subjectPerformance: List[SubjectPerformance] = Field(default=[], description="Performance breakdown by subject", alias="subject_performance")
    assignmentSummaries: List[AssignmentSummary] = Field(default=[], description="Recent assignment summaries", alias="assignment_summaries")
    
    # Analysis and Remarks
    aiRemarks: str = Field(..., description="AI-generated comprehensive analysis of student's performance, strengths, weaknesses, and recommendations", alias="ai_remarks")
    teacherRemarks: str = Field(default="", description="Teacher's comments and observations (empty if not provided)", alias="teacher_remarks")
    studentInsights: StudentInsights = Field(..., description="Key insights about the student's performance", alias="student_insights")

class ReportCardResponse(BaseModel):
    reportCard: ReportCard = Field(..., description="The complete report card for the student", alias="report_card")

# --- Creating Report Card Generator Agent ---
report_card_generator = LlmAgent(
    name="report_card_generator",
    model="gemini-2.5-flash-lite",
    description="Generates comprehensive report cards for students based on their assignment results and performance data",
    instruction=report_card_generator_prompt,
    output_schema=ReportCardResponse,
    output_key="report_card_data",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)