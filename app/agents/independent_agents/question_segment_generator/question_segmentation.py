from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from .question_segmentation_prompt import QUESTION_SEGMENTATION_PROMPT
from dotenv import load_dotenv
import os

load_dotenv()

# Ensure the API key is set
if "GOOGLE_API_KEY" not in os.environ:
    raise EnvironmentError(
        "GOOGLE_API_KEY is not set in the environment variables."
    )

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
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.75)

# Create a prompt template
prompt_template = PromptTemplate.from_template(
    template=QUESTION_SEGMENTATION_PROMPT
)


def segment_question_agent(question: str) -> str:
    """
    Segments the given question into smaller parts using the gemini-2.5-flash-lite model.

    Args:
        question (str): The question to segment.

    Returns:
        str: The segmented parts of the question as a single text.
    """
    formatted_prompt = prompt_template.format(question=question)
    message = HumanMessage(content=formatted_prompt)
    response = llm.invoke([message])
    segmented_text = response.content.strip()
    return segmented_text
