from app.prompts.mcq_variation_generator_prompt import MCQ_VARIATION_GENERATOR_PROMPT
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

# Load the MCQ variation generator prompt

# Define the request model


class MCQRequest(BaseModel):
    question: str = Field(
        description="The original question to generate variations for.")
    options: List[str] = Field(
        description="The list of options for the question.")
    answerIndex: int = Field(
        description="The index of the correct answer in the options list.")

# Define the structure for each MCQ variation


class MCQQuestion(BaseModel):
    question: str = Field(
        description="The variation of the original question.")
    options: List[str] = Field(
        description="The list of options for the variation.")
    answerIndex: int = Field(
        description="The index of the correct answer in the options list.")

# Define the response model


class MCQVariation(BaseModel):
    variations: List[MCQQuestion] = Field(
        description="List of generated MCQ variations.")


# Initialize the LLM with structured output
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.75)
structured_llm = llm.with_structured_output(MCQVariation)

# Create a prompt template
prompt_template = PromptTemplate.from_template(
    template=MCQ_VARIATION_GENERATOR_PROMPT)


@router.post(
    "/generate-mcq-variations",
    summary="Generate MCQ variations using LLM",
    description="Generates variations of a given MCQ question using the Gemini-2.0-Flash model.",
    response_model=MCQVariation,
    response_description="A JSON object containing the generated variations.",
)
def generate_mcq_variations(request: MCQRequest):
    """
    Handles the POST request for generating MCQ variations.

    Args:
        request (MCQRequest): The request body containing the question, options, and correct answer index.

    Returns:
        MCQVariation: A JSON object containing the generated variations.
    """
    try:
        # Format the prompt using the template
        formatted_prompt = prompt_template.format(
            question=request.question,
            options=", ".join(request.options),
            answerIndex=request.answerIndex,
        )
        # Create a HumanMessage with the formatted prompt
        message = HumanMessage(content=formatted_prompt)
        # Invoke the LLM with structured output
        response = structured_llm.invoke([message])

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
