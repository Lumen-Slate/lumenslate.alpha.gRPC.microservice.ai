from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import json
from .question_creator_prompt import question_creator_prompt

# --- Question Structure Models (based on GIN backend) ---
class MCQQuestion(BaseModel):
    question: str = Field(description="The question text")
    options: List[str] = Field(description="List of 4 multiple choice options")
    answerIndex: int = Field(description="Index of correct answer (0-3)")
    points: int = Field(default=1, description="Points for the question")
    difficulty: str = Field(description="Difficulty level: 'easy', 'medium', or 'hard'")
    subject: str = Field(description="Subject of the question")


class MSQQuestion(BaseModel):
    question: str = Field(description="The question text")
    options: List[str] = Field(description="List of multiple select options")
    answerIndices: List[int] = Field(description="List of indices of correct answers")
    points: int = Field(default=2, description="Points for the question")
    difficulty: str = Field(description="Difficulty level: 'easy', 'medium', or 'hard'")
    subject: str = Field(description="Subject of the question")


class NATQuestion(BaseModel):
    question: str = Field(description="The question text")
    answer: float = Field(description="Numerical answer")
    points: int = Field(default=2, description="Points for the question")
    difficulty: str = Field(description="Difficulty level: 'easy', 'medium', or 'hard'")
    subject: str = Field(description="Subject of the question")


class SubjectiveQuestion(BaseModel):
    question: str = Field(description="The question text")
    idealAnswer: Optional[str] = Field(default=None, description="Sample ideal answer")
    gradingCriteria: List[str] = Field(default_factory=list, description="Grading criteria points")
    points: int = Field(default=5, description="Points for the question")
    difficulty: str = Field(description="Difficulty level: 'easy', 'medium', or 'hard'")
    subject: str = Field(description="Subject of the question")


class QuestionCreatorResponse(BaseModel):
    mcqs: List[MCQQuestion] = Field(default_factory=list, description="Generated MCQ questions")
    msqs: List[MSQQuestion] = Field(default_factory=list, description="Generated MSQ questions")
    nats: List[NATQuestion] = Field(default_factory=list, description="Generated NAT questions")
    subjectives: List[SubjectiveQuestion] = Field(default_factory=list, description="Generated subjective questions")
    totalQuestionsGenerated: int = Field(description="Total number of questions generated")
    corpusUsed: str = Field(description="Name of the corpus used for generating questions")


question_creator = LlmAgent(
    name="question_creator",
    model="gemini-2.5-flash-preview-04-17",
    description="Educational Question Generator using pre-retrieved curriculum content. Creates questions based on provided RAG information.",
    instruction=question_creator_prompt,
    output_schema=QuestionCreatorResponse,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
