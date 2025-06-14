import os
from google import genai
from dotenv import load_dotenv
from .summarizer_prompt import SUMMARIZER_PROMPT

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def create_summary(messages):
    input = SUMMARIZER_PROMPT.format(messages=messages)
    response = client.models.generate_content(
        model='gemini-2.0-flash', contents=input
    )
    return response.text.strip() if response and response.text else None 