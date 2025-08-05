from app.prompts.msq_variation_generator_prompt import MSQ_VARIATION_GENERATOR_PROMPT
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
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.75)
structured_llm = llm.with_structured_output(MSQVariation)

# Create a prompt template
prompt_template = PromptTemplate.from_template(
    template=MSQ_VARIATION_GENERATOR_PROMPT)


def generate_msq_variations_logic(question: str, options: List[str], answerIndices: List[int]) -> MSQVariation:
    """
    Core logic for generating MSQ variations.

    Args:
        question (str): The original question to generate variations for.
        options (List[str]): The list of options for the question.
        answerIndices (List[int]): The indices of the correct answers in the options list.

    Returns:
        MSQVariation: A JSON object containing the generated variations.
    """
    formatted_prompt = prompt_template.format(
        question=question,
        options=", ".join(options),
        answerIndices=", ".join(map(str, answerIndices)),
    )
    message = HumanMessage(content=formatted_prompt)
    response = structured_llm.invoke([message])
    return response
