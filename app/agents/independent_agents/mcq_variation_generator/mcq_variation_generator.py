from .mcq_variation_generator_prompt import MCQ_VARIATION_GENERATOR_PROMPT
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
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.75)
structured_llm = llm.with_structured_output(MCQVariation)

# Create a prompt template
prompt_template = PromptTemplate.from_template(
    template=MCQ_VARIATION_GENERATOR_PROMPT)


def generate_mcq_variations_agent(question: str, options: List[str], answerIndex: int) -> MCQVariation:
    """
    Core logic for generating MCQ variations.

    Args:
        question (str): The original question to generate variations for.
        options (List[str]): The list of options for the question.
        answerIndex (int): The index of the correct answer in the options list.

    Returns:
        MCQVariation: A JSON object containing the generated variations.
    """
    formatted_prompt = prompt_template.format(
        question=question,
        options=", ".join(options),
        answerIndex=answerIndex,
    )
    message = HumanMessage(content=formatted_prompt)
    response = structured_llm.invoke([message])
    return response
