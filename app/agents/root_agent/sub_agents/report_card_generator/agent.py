from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AssignmentSummary(BaseModel):
    assignment_id: str = Field(..., description="The unique identifier of the assignment")
    assignment_title: str = Field(..., description="The title of the assignment")
    percentage_score: float = Field(..., description="Percentage score for this assignment")
    subject: str = Field(..., description="Subject of the assignment")

class SubjectPerformance(BaseModel):
    subject_name: str = Field(..., description="Name of the subject")
    percentage_score: float = Field(..., description="Overall percentage score in this subject")
    assignment_count: int = Field(..., description="Number of assignments completed in this subject")
    
    # Question type breakdown within this subject
    mcq_accuracy: float = Field(default=0.0, description="MCQ accuracy rate in this subject")
    msq_accuracy: float = Field(default=0.0, description="MSQ accuracy rate in this subject")
    nat_accuracy: float = Field(default=0.0, description="NAT accuracy rate in this subject")
    subjective_avg_score: float = Field(default=0.0, description="Average score on subjective questions in this subject")
    
    # Subject-specific analysis
    strengths: List[str] = Field(default=[], description="Top strengths in this subject")
    weaknesses: List[str] = Field(default=[], description="Areas needing improvement in this subject")
    improvement_trend: str = Field(default="stable", description="Performance trend in this subject")

class OverallPerformance(BaseModel):
    total_assignments_completed: int = Field(..., description="Total number of assignments completed")
    overall_percentage: float = Field(..., description="Overall percentage score across all assignments")
    improvement_trend: str = Field(..., description="Overall performance trend (improving, stable, declining)")
    strongest_question_type: str = Field(..., description="Question type where student performs best")
    weakest_question_type: str = Field(..., description="Question type needing most improvement")

class StudentInsights(BaseModel):
    key_strengths: List[str] = Field(..., description="Top 3 academic strengths")
    areas_for_improvement: List[str] = Field(..., description="Top 3 areas needing improvement")
    recommended_actions: List[str] = Field(..., description="Top 3 specific recommendations")

class ReportCard(BaseModel):
    student_id: str = Field(..., description="The unique identifier of the student")
    student_name: str = Field(..., description="The name of the student")
    report_period: str = Field(..., description="The time period this report covers")
    generation_date: str = Field(..., description="Date when the report card was generated")
    
    # Performance Data
    overall_performance: OverallPerformance = Field(..., description="Overall academic performance summary")
    subject_performance: List[SubjectPerformance] = Field(default=[], description="Performance breakdown by subject")
    assignment_summaries: List[AssignmentSummary] = Field(default=[], description="Recent assignment summaries")
    
    # Analysis and Remarks
    ai_remarks: str = Field(..., description="AI-generated comprehensive analysis of student's performance, strengths, weaknesses, and recommendations")
    teacher_remarks: str = Field(default="", description="Teacher's comments and observations (empty if not provided)")
    student_insights: StudentInsights = Field(..., description="Key insights about the student's performance")

class ReportCardResponse(BaseModel):
    report_card: ReportCard = Field(..., description="The complete report card for the student")

# --- Creating Report Card Generator Agent ---
report_card_generator = LlmAgent(
    name="report_card_generator",
    model="gemini-2.0-flash",
    description="Generates comprehensive report cards for students based on their assignment results and performance data",
    instruction="""
    You are an expert educational analyst and report card generator. Your role is to create comprehensive, insightful report cards for students based on their assignment results and academic performance data.

    **Your Primary Responsibilities:**

    1. **Analyze Assignment Results:**
       - Process multiple assignment results for a student
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

    **Input Format Expected:**
    - List of assignment results with detailed performance data
    - Optional teacher remarks
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