from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, Text, Float
from . import Base
from enum import Enum
from datetime import datetime, timezone
from sqlalchemy.sql import func

class Role(Enum):
    USER = "user"   
    AGENT = "agent"

class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Subject(Enum):
    MATH = "math"
    SCIENCE = "science"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    ENGLISH = "english"

class UnalteredHistory(Base):
    """Model for storing unaltered message history."""
    __tablename__ = "unaltered_history"
    id = Column(Integer, primary_key=True, index=True)
    teacherId = Column(String, nullable=False)
    message = Column(String, nullable=False)
    role = Column(SQLEnum(Role), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    def __repr__(self):
        return f"<UnalteredHistory(id={self.id}, teacherId='{self.teacherId}', role='{self.role}', timestamp='{self.timestamp}')>"

class Questions(Base):
    """Model for storing questions."""
    __tablename__ = 'questions'
    question_id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(SQLEnum(Subject), nullable=False)
    question = Column(String, nullable=False)
    options = Column(String, nullable=False)  # JSON string of options
    answer = Column(String, nullable=False)  # Correct answer
    difficulty = Column(SQLEnum(Difficulty), nullable=False)

class SubjectReport(Base):
    """Model for storing subject report cards and assessment breakdowns."""
    __tablename__ = 'subject_report'
    report_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    student_id = Column(Integer, nullable=False)
    student_name = Column(String, nullable=False)
    subject = Column(SQLEnum(Subject), nullable=False)
    score = Column(Integer, nullable=False)  # Score out of 100
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    grade_letter = Column(String, nullable=True)  # e.g., A, B, C
    class_name = Column(String, nullable=True)  # e.g., "10th Grade"
    instructor_name = Column(String, nullable=True)
    term = Column(String, nullable=True)  # e.g., "Fall 2025"
    remarks = Column(Text, nullable=True)
    midterm_score = Column(Integer, nullable=True)
    final_exam_score = Column(Integer, nullable=True)
    quiz_score = Column(Integer, nullable=True)
    assignment_score = Column(Integer, nullable=True)
    practical_score = Column(Integer, nullable=True)
    oral_presentation_score = Column(Integer, nullable=True)
    conceptual_understanding = Column(Float, nullable=True)
    problem_solving = Column(Float, nullable=True)
    knowledge_application = Column(Float, nullable=True)
    analytical_thinking = Column(Float, nullable=True)
    creativity = Column(Float, nullable=True)
    practical_skills = Column(Float, nullable=True)
    participation = Column(Float, nullable=True)
    discipline = Column(Float, nullable=True)
    punctuality = Column(Float, nullable=True)
    teamwork = Column(Float, nullable=True)
    effort_level = Column(Float, nullable=True)
    improvement = Column(Float, nullable=True)
    learning_objectives_mastered = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    recommended_resources = Column(Text, nullable=True)
    target_goals = Column(Text, nullable=True)

class RAGContext(Base):
    """Model for storing context for RAG/retrieval-based systems."""
    __tablename__ = "rag_context"
    id = Column(Integer, primary_key=True, index=True)
    teacherId = Column(String, nullable=False)
    context_data = Column(Text, nullable=False)  # Could store embeddings, document refs, etc.
    source = Column(String, nullable=True)  # Source of the context (document name, URL, etc.)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    def __repr__(self):
        return f"<RAGContext(id={self.id}, teacherId='{self.teacherId}', source='{self.source}', timestamp='{self.timestamp}')>"

