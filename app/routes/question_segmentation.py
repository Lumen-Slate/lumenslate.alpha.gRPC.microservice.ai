from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.prompts.question_segmentation_prompt import QUESTION_SEGMENTATION_PROMPT
from dotenv import load_dotenv
import os

load_dotenv()

# Ensure the API key is set
if "GOOGLE_API_KEY" not in os.environ:
    raise EnvironmentError(
        "GOOGLE_API_KEY is not set in the environment variables."
    )

# Initialize the router
router = APIRouter()

# Define the request model


class QuestionSegmentationRequest(BaseModel):
    question: str = Field(
        description="The question to segment into smaller parts."
    )

# Define the response model


class QuestionSegmentationResponse(BaseModel):
    segmentedQuestion: str = Field(
        description="The segmented parts of the original question as a single text."
    )


# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.75)

# Create a prompt template
prompt_template = PromptTemplate.from_template(
    template=QUESTION_SEGMENTATION_PROMPT
)


@router.post(
    "/segment-question",
    summary="Segment a question into smaller parts",
    description="Segments a given question into smaller, meaningful parts using the Gemini-2.0-Flash model.",
    response_model=QuestionSegmentationResponse,
    response_description="A JSON object containing the segmented parts of the question as a single text.",
)
def segment_question(request: QuestionSegmentationRequest):
    """
    Handles the POST request for segmenting a question into smaller parts.

    Args:
        request (QuestionSegmentationRequest): The request body containing the question.

    Returns:
        QuestionSegmentationResponse: A JSON object containing the segmented parts of the question as a single text.
    """
    try:
        # Format the prompt using the question
        formatted_prompt = prompt_template.format(question=request.question)
        # Create a HumanMessage with the formatted prompt
        message = HumanMessage(content=formatted_prompt)
        # Invoke the LLM
        response = llm.invoke([message])

        # Extract the response content
        segmented_text = response.content.strip()

        return QuestionSegmentationResponse(segmented_question=segmented_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
