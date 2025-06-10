from app.prompts.context_generator_prompt import CONTEXT_GENEATOR_PROMPT
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

class ContextRequest(BaseModel):
    question: str
    keywords: list[str] = []
    language: str = "English"


# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Create a prompt template
prompt_template = PromptTemplate.from_template(
    template=CONTEXT_GENEATOR_PROMPT)

def generate_context_logic(question: str, keywords: list[str], language: str = "English") -> str:
    keywords_str = ",".join(keywords) if keywords else ""
    language = language if language else "English"
    formatted_prompt = prompt_template.format(
        question=question,
        keywords=keywords_str,
        language=language
    )
    message = HumanMessage(content=formatted_prompt)
    response = llm.invoke([message])
    return response.content
