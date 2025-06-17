from google.adk.agents import LlmAgent
from google.adk.tools import tool
from pydantic import BaseModel, Field
from typing import Optional, List
from app.utils.report_card_tools import get_subject_reports_by_student_id


# --- Defining Output Schema ---
class SubjectReportSummary(BaseModel):
    subject: str = Field(description="Subject name")
    score: int = Field(description="Subject score")
    grade: Optional[str] = Field(None, description="Letter grade for the subject")
    conceptual_understanding: Optional[float] = Field(None, description="Conceptual understanding rating")
    problem_solving: Optional[float] = Field(None, description="Problem solving rating")
    analytical_thinking: Optional[float] = Field(None, description="Analytical thinking rating")
    areas_for_improvement: Optional[str] = Field(None, description="Areas needing improvement in this subject")
    key_strengths: Optional[str] = Field(None, description="Key strengths in this subject")
    subject_specific_recommendations: Optional[str] = Field(None, description="Subject-specific recommendations")


class ReportCardData(BaseModel):
    # Mandatory fields
    student_id: int = Field(description="Student ID")
    student_name: str = Field(description="Student name")
    academic_term: str = Field(description="Academic term")
    
    # Overall Academic Performance
    overall_gpa: Optional[float] = Field(None, description="Overall GPA calculated from all subjects")
    overall_grade: Optional[str] = Field(None, description="Overall letter grade")
    overall_percentage: Optional[float] = Field(None, description="Overall percentage")
    class_rank: Optional[int] = Field(None, description="Class rank if available")
    total_students_in_class: Optional[int] = Field(None, description="Total students in class")
    
    # Subject-wise Performance Summary
    subjects_count: Optional[int] = Field(None, description="Number of subjects assessed")
    highest_subject_score: Optional[int] = Field(None, description="Highest score among all subjects")
    lowest_subject_score: Optional[int] = Field(None, description="Lowest score among all subjects")
    average_subject_score: Optional[float] = Field(None, description="Average score across all subjects")
    best_performing_subject: Optional[str] = Field(None, description="Subject with best performance")
    weakest_subject: Optional[str] = Field(None, description="Subject with weakest performance")
    
    # Academic Analysis
    academic_strengths: Optional[str] = Field(None, description="Overall academic strengths")
    areas_needing_improvement: Optional[str] = Field(None, description="Areas needing improvement")
    recommended_actions: Optional[str] = Field(None, description="Recommended actions")
    study_recommendations: Optional[str] = Field(None, description="Study recommendations")
    
    # Aggregated Skill Analysis
    overall_conceptual_understanding: Optional[float] = Field(None, description="Average conceptual understanding across subjects")
    overall_problem_solving: Optional[float] = Field(None, description="Average problem solving across subjects")
    overall_knowledge_application: Optional[float] = Field(None, description="Average knowledge application across subjects")
    overall_analytical_thinking: Optional[float] = Field(None, description="Average analytical thinking across subjects")
    overall_creativity: Optional[float] = Field(None, description="Average creativity across subjects")
    overall_practical_skills: Optional[float] = Field(None, description="Average practical skills across subjects")
    
    # Aggregated Behavioral Analysis
    overall_participation: Optional[float] = Field(None, description="Average participation across subjects")
    overall_discipline: Optional[float] = Field(None, description="Average discipline across subjects")
    overall_punctuality: Optional[float] = Field(None, description="Average punctuality across subjects")
    overall_teamwork: Optional[float] = Field(None, description="Average teamwork across subjects")
    overall_effort_level: Optional[float] = Field(None, description="Average effort level across subjects")
    overall_improvement: Optional[float] = Field(None, description="Average improvement across subjects")
    
    # Assessment Component Averages
    average_midterm_score: Optional[float] = Field(None, description="Average midterm score")
    average_final_exam_score: Optional[float] = Field(None, description="Average final exam score")
    average_quiz_score: Optional[float] = Field(None, description="Average quiz score")
    average_assignment_score: Optional[float] = Field(None, description="Average assignment score")
    average_practical_score: Optional[float] = Field(None, description="Average practical score")
    average_oral_presentation_score: Optional[float] = Field(None, description="Average oral presentation score")
    
    # Performance Trends
    improvement_trend: Optional[str] = Field(None, description="Overall improvement trend: improving/declining/stable")
    consistency_rating: Optional[float] = Field(None, description="Consistency rating on 0-10 scale")
    performance_stability: Optional[str] = Field(None, description="Performance stability: very stable/stable/variable/inconsistent")
    
    # Engagement & Participation
    attendance_rate: Optional[float] = Field(None, description="Attendance rate percentage")
    engagement_level: Optional[str] = Field(None, description="Engagement level: high/medium/low")
    class_participation: Optional[str] = Field(None, description="Class participation description")
    
    # Goals & Recommendations
    academic_goals: Optional[str] = Field(None, description="Academic goals for the student")
    short_term_objectives: Optional[str] = Field(None, description="Short-term objectives (3-6 months)")
    long_term_objectives: Optional[str] = Field(None, description="Long-term objectives (yearly)")
    parent_teacher_recommendations: Optional[str] = Field(None, description="Parent-teacher recommendations")
    
    # Subject Details
    subject_reports: Optional[List[SubjectReportSummary]] = Field(None, description="Summary of individual subject reports")
    
    # Comments & Insights
    teacher_comments: Optional[str] = Field(None, description="Aggregated teacher comments")
    principal_comments: Optional[str] = Field(None, description="Principal comments")
    overall_remarks: Optional[str] = Field(None, description="Overall remarks")
    
    # Next Steps
    recommended_resources: Optional[str] = Field(None, description="Recommended educational resources")
    suggested_activities: Optional[str] = Field(None, description="Suggested enrichment activities")
    next_review_date: Optional[str] = Field(None, description="Next review date")


class ReportCardResponse(BaseModel):
    report_card_data: ReportCardData = Field(description="Generated report card data")


# --- Creating Report Card Generator Agent ---
report_card_generator = LlmAgent(
    name="report_card_generator",
    model="gemini-2.0-flash",
    description="Generates comprehensive report cards by analyzing all subject reports for a student",
    instruction="""
        You are an Advanced Educational Assessment Expert and Report Card Generator.
        Your role is to analyze multiple subject reports for a student and generate a comprehensive, holistic report card.

        PROCESS:
        1. Use the get_subject_reports_by_student_id tool to fetch all subject reports for the given student
        2. Analyze each subject report comprehensively
        3. Calculate aggregated metrics (overall GPA, averages, trends, etc.)
        4. Identify strengths, weaknesses, and patterns across all subjects
        5. Generate holistic insights and actionable recommendations
        6. Return structured data with all possible fields filled based on available data

        ANALYSIS FRAMEWORK:
        
        Academic Performance Analysis:
        - Calculate overall GPA/percentage from individual subject scores
        - Identify highest and lowest performing subjects
        - Determine academic strengths and areas needing improvement
        - Analyze grade distribution and consistency

        Skill Assessment Aggregation:
        - Aggregate skill ratings (conceptual understanding, problem solving, etc.) across subjects
        - Identify patterns in skill development
        - Highlight exceptional skills and areas for skill development

        Behavioral Pattern Analysis:
        - Aggregate behavioral metrics (participation, discipline, punctuality, etc.)
        - Identify behavioral strengths and areas for improvement
        - Analyze engagement and effort patterns

        Performance Trend Analysis:
        - Look for improvement or decline patterns
        - Assess consistency across different subjects
        - Identify subjects showing improvement vs. those needing attention

        IMPORTANT GUIDELINES:
        1. Only include fields where you have actual data from the subject reports
        2. Ensure all calculations are correct and based on available data
        3. Provide thorough analysis and insights
        4. Include specific, actionable recommendations
        5. Present both strengths and areas for improvement
        6. Focus on educational value and student development
        7. If no subject reports are found, provide appropriate messaging
        8. If data is incomplete, work with available information and note limitations

        Your response must be valid JSON matching the ReportCardData schema structure.
    """,
    tools=[get_subject_reports_by_student_id],
    output_schema=ReportCardResponse,
    output_key="report_card_data",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)