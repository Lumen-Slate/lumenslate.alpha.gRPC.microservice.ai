import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def create_summary(messages):
    input = f"""
    You are a helpful assistant that summarizes conversations.
    Please summarize the following messages in a concise manner, focusing on the main points and key information.
    Here are the messages:

    {messages}

    Please provide a summary that captures the essence of the conversation without losing important details.
    Do NOT say anything else or extra, just provide the summary.
    The summary should be in a single paragraph and should not exceed 100 words.
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash-lite', contents=input
    )
    return response.text.strip() if response and response.text else None 