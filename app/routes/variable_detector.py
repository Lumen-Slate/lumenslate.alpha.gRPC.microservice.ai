from app.prompts.variable_detector_prompt import VARIABLE_DETECTOR_PROMPT
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from typing import List, Optional
import os

load_dotenv()

# Ensure the API key is set
if "GOOGLE_API_KEY" not in os.environ:
    raise EnvironmentError(
        "GOOGLE_API_KEY is not set in the environment variables.")

router = APIRouter()

# Define the request model


class VariableDetectorRequest(BaseModel):
    question: str = Field(description="The question to analyze for variables.")

# Define the response model


class Variable(BaseModel):
    name: str = Field(description="The name of the variable.")
    value: Optional[str] = Field(
        description="The value of the variable. Can be null if only the variable name is present."
    )
    namePositions: List[int] = Field(
        description="The true positions of the variable name in the question."
    )
    valuePositions: List[int] = Field(
        description="The true positions of the variable value in the question."
    )


class VariableDetectorResponse(BaseModel):
    variables: List[Variable] = Field(
        description="List of detected variables with their details.")


# Initialize the LLM with structured output
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.75)
structured_llm = llm.with_structured_output(VariableDetectorResponse)

# Create a prompt template
prompt_template = PromptTemplate.from_template(
    template=VARIABLE_DETECTOR_PROMPT)


@router.post(
    "/detect-variables",
    summary="Detect variables in a question",
    description="Identifies variables in a given question using the Gemini-2.0-Flash model.",
    response_model=VariableDetectorResponse,
    response_description="A JSON object containing the detected variables.",
)
def detect_variables(request: VariableDetectorRequest):
    """
    Handles the POST request for detecting variables in a question.

    Args:
        request (VariableDetectorRequest): The request body containing the question.

    Returns:
        VariableDetectorResponse: A JSON object containing the detected variables.
    """
    try:
        # Split the question into a list of strings separated by whitespace
        question_as_list = request.question.split()
        # Format the prompt using the template
        formatted_prompt = prompt_template.format(question=question_as_list)
        # Create a HumanMessage with the formatted prompt
        message = HumanMessage(content=formatted_prompt)
        # Invoke the LLM with structured output
        response = structured_llm.invoke([message])

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
