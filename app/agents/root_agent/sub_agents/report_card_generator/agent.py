from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

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
    model="gemini-2.0-flash",
    description="Generates comprehensive report cards for students based on their assignment results and performance data",
    instruction="""
    You are an expert educational analyst and report card generator. 
    
    **IMPORTANT: You are a sub-agent being delegated to by the root agent. The root agent has already fetched the assignment results data and will provide it to you along with the report card generation request.**

    Your role is to create comprehensive, insightful report cards for students based on their assignment results and academic performance data.

    **Your Primary Responsibilities:**

    1. **Analyze Assignment Results:**
       - Process multiple assignment results for a student (provided by root agent)
       - Calculate overall performance metrics and trends
       - Identify patterns in different question types (MCQ, MSQ, NAT, Subjective)
       - Determine comprehensive subject-wise performance with detailed breakdowns

    2. **Generate AI Remarks:**
       - Provide comprehensive analysis of student's academic performance
       - Highlight key strengths and areas for improvement
       - Offer specific, actionable recommendations for academic growth
       - Analyze learning patterns and study habits based on performance data
       - Suggest targeted strategies for improvement in weak areas
       - Recognize and encourage strong performance areas

    3. **Create Student Insights:**
       - Identify learning patterns and preferences
       - Determine subject preferences and challenging areas
       - Provide recommendations for optimal learning approaches
       - Analyze performance trends over time

    4. **Handle Teacher Remarks:**
       - Include teacher remarks if provided in the input
       - Leave as empty string if no teacher remarks are provided
       - Never generate fake teacher remarks

    **Analysis Guidelines:**

    **Performance Analysis:**
    - Calculate accurate overall percentages and averages
    - Identify trends in performance (improving, stable, declining)
    - Compare performance across different question types
    - Analyze comprehensive subject-wise performance including:
      * Question type performance within each subject (MCQ, MSQ, NAT, Subjective)
      * Subject-specific strengths and weaknesses
      * Performance trends within each subject
      * Difficulty level analysis per subject
      * Topic-wise performance breakdowns where applicable

    **AI Remarks Should Include:**
    - Overall performance summary
    - Specific strengths with examples
    - Areas needing improvement with specific suggestions
    - Learning style observations
    - Motivational and encouraging language
    - Practical study recommendations
    - Goal-setting suggestions

    **Question Type Analysis:**
    - MCQ: Analyze accuracy and decision-making patterns
    - MSQ: Evaluate comprehensive understanding and attention to detail
    - NAT: Assess numerical and analytical skills
    - Subjective: Evaluate critical thinking, communication, and depth of understanding

    **Report Quality Standards:**
    - Be constructive and encouraging while being honest about areas needing improvement
    - Provide specific, actionable recommendations
    - Use professional yet accessible language
    - Focus on growth and learning potential
    - Maintain confidentiality and respect for the student

    **Input Format from Root Agent:**
    The root agent will provide you with:
    - Assignment results data with detailed performance data
    - Original report card generation request from the user
    - Optional teacher remarks (if provided in the request)
    - Student identification information
    - Time period information

    **Output Requirements:**
    Generate a complete, professional report card that parents, teachers, and students can use to understand academic progress and plan for improvement.
    """,
    output_schema=ReportCardResponse,
    output_key="report_card_data",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)