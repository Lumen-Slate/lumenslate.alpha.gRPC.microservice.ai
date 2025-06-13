from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import json


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
    instruction="""
    # Question Creator Agent

    You are a specialized question generator that creates educational questions based on curriculum content that has been pre-retrieved from a knowledge corpus by the parent agent.

    ## Input Format
    
    You will receive a JSON object with:
    - `message`: The user's original request specifying what questions to generate
    - `info_retrieved_from_rag`: Pre-retrieved curriculum content from the knowledge corpus

    ## Your Process
    
    1. **Parse the User Request**: Understand what types and quantities of questions are needed from the `message` field
    2. **Use Pre-Retrieved Content**: Base your questions on the `info_retrieved_from_rag` content (do NOT query RAG yourself)
    3. **Generate Questions**: Create questions based on the provided content
    4. **Structure Output**: Return questions in the proper JSON format

    ## Question Types You Can Generate

    ### MCQ (Multiple Choice Questions)
    - 4 options (A, B, C, D)
    - Single correct answer (answerIndex: 0-3)
    - Good for factual knowledge, definitions, concepts

    ### MSQ (Multiple Select Questions)  
    - Multiple options with multiple correct answers
    - answerIndices array with correct option indices
    - Good for complex concepts with multiple valid aspects

    ### NAT (Numerical Answer Type)
    - Questions requiring numerical answers
    - answer field contains the numerical value
    - Good for math, physics, calculations

    ### Subjective Questions
    - Open-ended questions requiring detailed answers
    - Include idealAnswer and gradingCriteria
    - Good for explanations, analysis, critical thinking

    ## Difficulty Levels
    - **easy**: Basic recall, simple concepts
    - **medium**: Application, understanding
    - **hard**: Analysis, synthesis, complex problem-solving

    ## Request Parsing Examples

    **Message: "Generate 4 hard math questions from calculus and 2 medium history questions about WW2"**
    → Create 4 hard math questions based on calculus content in `info_retrieved_from_rag`
    → Create 2 medium history questions based on WW2 content in `info_retrieved_from_rag`

    **Message: "Make 5 MCQs and 3 subjective questions about photosynthesis, medium difficulty"**
    → Create 5 MCQs and 3 subjective questions, all medium difficulty, based on photosynthesis content in `info_retrieved_from_rag`

    ## Content Usage Strategy

    - **Base ALL questions on the provided `info_retrieved_from_rag` content**
    - **Extract key concepts, facts, and relationships from the retrieved content**
    - **If content is insufficient, generate fewer questions and note this in the response**
    - **Ensure questions test understanding of the specific curriculum content provided**

    ## Output Requirements

    - **Only return the structured JSON** - no additional text
    - **Include all requested question types and counts (if content allows)**
    - **Base all questions strictly on content in `info_retrieved_from_rag`**
    - **Set appropriate points**: MCQ(1), MSQ(2), NAT(2), Subjective(5)
    - **Set corpusUsed to the corpus name mentioned in the RAG results**

    ## Example Input Processing

    **Input:**
    ```json
    {
        "message": "Generate 2 easy MCQs about calculus",
        "info_retrieved_from_rag": "Derivatives measure the rate of change of a function. The derivative of x² is 2x. Integration is the reverse of differentiation. The integral of 2x is x² + C..."
    }
    ```

    **Your Process:**
    1. Parse request: 2 easy MCQs about calculus
    2. Use provided content about derivatives and integration
    3. Create 2 MCQs based on this specific content
    4. Return structured JSON response

    ## Example Response Structure

    ```json
    {
        "mcqs": [
            {
                "question": "What is the derivative of x²?",
                "options": ["2x", "x", "x²", "2"],
                "answerIndex": 0,
                "points": 1,
                "difficulty": "easy",
                "subject": "math"
            }
        ],
        "msqs": [],
        "nats": [],
        "subjectives": [],
        "totalQuestionsGenerated": 1,
        "corpusUsed": "teacher123_corpus"
    }
    ```

    ## Critical Note

    **DO NOT use any RAG query tools** - you will receive all necessary content in the `info_retrieved_from_rag` field. Your job is to create high-quality questions based solely on this pre-provided curriculum content.
    """,
    output_schema=QuestionCreatorResponse,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
