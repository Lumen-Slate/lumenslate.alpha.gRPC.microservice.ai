from app.prompts.context_generator_prompt import CONTEXT_GENEATOR_PROMPT
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import getpass
import os
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()


if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass(
        "You have not entered the GOOGLE_API_KEY in .env file. Enter your Google AI API key: ")

router = APIRouter()


class ContextRequest(BaseModel):
    question: str
    keywords: list[str] = []
    language: str = "English"


# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Load the context generation prompt template

# Create a prompt template
prompt_template = PromptTemplate.from_template(
    template=CONTEXT_GENEATOR_PROMPT)


@router.post(
    "/generate-context",
    summary="Generate context using LLM",
    description="Generates a response using the Gemini-2.0-Flash model.",
    response_description="A JSON object with the generated response.",
)
def generate_context(request: ContextRequest):
    """
    Handles the POST request for generating context.

    Args:
        request (ContextRequest): The request body containing the prompt, keywords, and language.

    Returns:
        dict: A JSON object with the generated response.
    """
    try:
        # Extract data from the request payload
        question = request.question
        keywords = ",".join(request.keywords) if hasattr(
            request, 'keywords') and request.keywords else ""
        language = request.language if hasattr(
            request, 'language') and request.language else "English"

        # Format the prompt using the template
        formatted_prompt = prompt_template.format(
            question=question,
            keywords=keywords,
            language=language
        )
        # Create a HumanMessage with the formatted prompt
        message = HumanMessage(content=formatted_prompt)
        # Invoke the LLM
        response = llm.invoke([message])

        return {"response": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
