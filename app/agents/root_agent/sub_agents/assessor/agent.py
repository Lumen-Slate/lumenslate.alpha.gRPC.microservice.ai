from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import Optional


# --- Defining Output Schema ---
class SubjectReportData(BaseModel):
    # Mandatory fields (excluding auto-generated ones)
    student_id: Optional[str] = Field(None, description="Student ID if mentioned")
    student_name: Optional[str] = Field(None, description="Student name if mentioned")
    subject: Optional[str] = Field(None, description="Subject being assessed (math, science, history, geography, english)")
    score: Optional[int] = Field(None, description="Overall score out of 100 if mentioned")
    
    # Optional basic information
    grade_letter: Optional[str] = Field(None, description="Grade letter (A, B, C, D, F) if mentioned")
    class_name: Optional[str] = Field(None, description="Class name or grade level if mentioned")
    instructor_name: Optional[str] = Field(None, description="Instructor/teacher name if mentioned")
    term: Optional[str] = Field(None, description="Academic term/semester if mentioned")
    remarks: Optional[str] = Field(None, description="General remarks or comments about the student")
    
    # Assessment component breakdown
    midterm_score: Optional[int] = Field(None, description="Midterm exam score if mentioned")
    final_exam_score: Optional[int] = Field(None, description="Final exam score if mentioned")
    quiz_score: Optional[int] = Field(None, description="Quiz score if mentioned")
    assignment_score: Optional[int] = Field(None, description="Assignment score if mentioned")
    practical_score: Optional[int] = Field(None, description="Practical/lab score if mentioned")
    oral_presentation_score: Optional[int] = Field(None, description="Oral presentation score if mentioned")
    
    # Skill evaluation (0-10 scale or percentage)
    conceptual_understanding: Optional[float] = Field(None, description="Conceptual understanding rating/score")
    problem_solving: Optional[float] = Field(None, description="Problem solving ability rating/score")
    knowledge_application: Optional[float] = Field(None, description="Knowledge application rating/score")
    analytical_thinking: Optional[float] = Field(None, description="Analytical thinking rating/score")
    creativity: Optional[float] = Field(None, description="Creativity rating/score")
    practical_skills: Optional[float] = Field(None, description="Practical skills rating/score")
    
    # Behavioral metrics
    participation: Optional[float] = Field(None, description="Class participation rating/score")
    discipline: Optional[float] = Field(None, description="Discipline/behavior rating/score")
    punctuality: Optional[float] = Field(None, description="Punctuality rating/score")
    teamwork: Optional[float] = Field(None, description="Teamwork ability rating/score")
    effort_level: Optional[float] = Field(None, description="Effort level rating/score")
    improvement: Optional[float] = Field(None, description="Improvement over time rating/score")
    
    # Advanced insights
    learning_objectives_mastered: Optional[str] = Field(None, description="Learning objectives that were mastered")
    areas_for_improvement: Optional[str] = Field(None, description="Areas where student needs improvement")
    recommended_resources: Optional[str] = Field(None, description="Recommended resources for further learning")
    target_goals: Optional[str] = Field(None, description="Target goals for the student")


class AssessorResponse(BaseModel):
    assessment_data: SubjectReportData = Field(description="Extracted assessment information from the input")


# --- Creating Assessor Agent ---
assessor = LlmAgent(
    name="assessor",
    model="gemini-2.0-flash",
    description="Analyzes student assessment information and extracts structured data for subject reports",
    instruction="""
        You are an Academic Assessment Data Extractor.
        Your task is to analyze input containing student assessment information and extract relevant data to populate a subject report.

        INPUT FORMATS YOU MAY RECEIVE:
        1. Plain text: Direct assessment information
        2. JSON with written_query and audio_description: {"written_query": "text", "audio_description": "transcribed audio"}
        3. JSON with written_query and image_description: {"written_query": "text", "image_description": "extracted text from image"}
        4. JSON with null written_query: {"written_query": null, "audio_description": "transcribed audio"} or {"written_query": null, "image_description": "extracted text from image"}

        EXTRACTION GUIDELINES:
        - Parse ALL available information from both written_query and audio/image descriptions
        - Extract any student assessment data that matches the SubjectReport fields
        - Standardize subject names to: "math", "science", "history", "geography", "english"
        - For scores, convert percentages or other formats to 0-100 scale when possible
        - For skill evaluations and behavioral metrics, use 0-10 scale or percentage (0-100)
        - Only include fields where you find relevant information - leave others as null
        - If information is ambiguous or unclear, make reasonable interpretations
        - Focus on academic assessment data, not general conversation

        EXAMPLES OF INFORMATION TO EXTRACT:
        - Student names, IDs, grades, scores
        - Subject being assessed
        - Specific assessment component scores (midterm, final, quiz, etc.)
        - Skill ratings (problem solving, creativity, etc.)
        - Behavioral observations (participation, effort, etc.)
        - Academic insights (strengths, weaknesses, recommendations)
        - Class information (grade level, instructor, term)

        IMPORTANT:
        - Your response MUST be valid JSON matching the schema structure
        - Only populate fields where you have actual information from the input
        - Do not make up or assume information not present in the input
        - If no relevant assessment data is found, return mostly null values
        - Be thorough in extracting all available relevant information
    """,
    output_schema=AssessorResponse,
    output_key="assessment_data",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
