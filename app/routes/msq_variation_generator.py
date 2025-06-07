from app.prompts.msq_variation_generator_prompt import MSQ_VARIATION_GENERATOR_PROMPT
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

# Ensure the API key is set
if "GOOGLE_API_KEY" not in os.environ:
    raise EnvironmentError(
        "GOOGLE_API_KEY is not set in the environment variables.")

router = APIRouter()

# Load the MSQ variation generator prompt

# Define the request model


class MSQRequest(BaseModel):
    question: str = Field(
        description="The original question to generate variations for.")
    options: List[str] = Field(
        description="The list of options for the question.")
    answerIndices: List[int] = Field(
        description="The indices of the correct answers in the options list.")

# Define the structure for each MSQ variation


class MSQQuestion(BaseModel):
    question: str = Field(
        description="The variation of the original question.")
    options: List[str] = Field(
        description="The list of options for the variation.")
    answerIndices: List[int] = Field(
        description="The indices of the correct answers in the options list.")

# Define the response model


class MSQVariation(BaseModel):
    variations: List[MSQQuestion] = Field(
        description="List of generated MSQ variations.")


# Initialize the LLM with structured output
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.75)
structured_llm = llm.with_structured_output(MSQVariation)

# Create a prompt template
prompt_template = PromptTemplate.from_template(
    template=MSQ_VARIATION_GENERATOR_PROMPT)


@router.post(
    "/generate-msq-variations",
    summary="Generate MSQ variations using LLM",
    description="Generates variations of a given MSQ question using the Gemini-2.0-Flash model.",
    response_model=MSQVariation,
    response_description="A JSON object containing the generated variations.",
)
def generate_msq_variations(request: MSQRequest):
    """
    Handles the POST request for generating MSQ variations.

    Args:
        request (MSQRequest): The request body containing the question, options, and correct answer indices.

    Returns:
        MSQVariation: A JSON object containing the generated variations.
    """
    try:
        # Format the prompt using the template
        formatted_prompt = prompt_template.format(
            question=request.question,
            options=", ".join(request.options),
            answerIndices=", ".join(map(str, request.answerIndices)),
        )
        # Create a HumanMessage with the formatted prompt
        message = HumanMessage(content=formatted_prompt)
        # Invoke the LLM with structured output
        response = structured_llm.invoke([message])

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
