from google import genai
from .clean_text import clean_text
from app.config.logging_config import logger
from dotenv import load_dotenv
import os
import tempfile

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

VALID_IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.webp'}

VALID_AUDIO_TYPES = {'.wav', '.mp3', '.aiff', '.aac', '.ogg', '.flac'}

VALID_TEXT_TYPES = {'.pdf'}

async def ImageHandler(agent_input) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        audio_bytes = await agent_input.file.read()
        tmp.write(audio_bytes)
        tmp_file_path = tmp.name

    try:
        # Now uploading using the file path
        file = client.files.upload(file=tmp_file_path)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                'Extract all the text from the image and return the text only.',
                file
            ],
        )

        return clean_text(response.text) if response and hasattr(response, "text") else "Could not generate transcription."
    except Exception as e:
        return f"Error during transcription: {str(e)}"
    finally:
        # Cleaning up the temporary file
        import os
        os.remove(tmp_file_path)
        logger.info(f"Temporary file {tmp_file_path} removed")


async def AudioHandler(agent_input) -> str:
    # Save upload to a temporary file first
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio_bytes = await agent_input.file.read()
        tmp.write(audio_bytes)
        tmp_file_path = tmp.name

    try:
        # Now uploading using the file path
        file = client.files.upload(file=tmp_file_path)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                'Transcribe the audio into text and return the text only.',
                file
            ],
        )

        return clean_text(response.text) if response and hasattr(response, "text") else "Could not generate transcription."
    except Exception as e:
        return f"Error during transcription: {str(e)}"
    finally:
        # Cleaning up the temporary file
        import os
        os.remove(tmp_file_path)
        logger.info(f"Temporary file {tmp_file_path} removed")


async def PDFHandler(agent_input) -> str:
    # Save upload to a temporary file first
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_bytes = await agent_input.file.read()
        tmp.write(pdf_bytes)
        tmp_file_path = tmp.name

    try:
        # Now uploading using the file path
        file = client.files.upload(file=tmp_file_path)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                'Extract all the text content from the PDF document and return the text only.',
                file
            ],
        )

        return clean_text(response.text) if response and hasattr(response, "text") else "Could not extract text from PDF."
    except Exception as e:
        return f"Error during PDF text extraction: {str(e)}"
    finally:
        # Cleaning up the temporary file
        import os
        os.remove(tmp_file_path)
        logger.info(f"Temporary file {tmp_file_path} removed")


async def MultimodalHandler(agent_input) -> str:

    if not agent_input.file or not agent_input.file.filename:
        return agent_input.query.strip() if agent_input.query else None
    
    filename = agent_input.file.filename.lower()
    file_extension = None
    
    # Extracting file extension
    if '.' in filename:
        file_extension = '.' + filename.split('.')[-1]
    
    if not file_extension:
        return None  # No file extension found

    # Checking if it's a valid image type
    if file_extension in VALID_IMAGE_TYPES:
        image_description = await ImageHandler(agent_input)

        grand_query = f'{{"written_query": {agent_input.query.strip() if agent_input.query else None}, "image_description": {image_description}}}'
        logger.info(f"Grand query: {grand_query}")
        return grand_query
    
    # Checking if it's a valid audio type
    elif file_extension in VALID_AUDIO_TYPES:
        audio_description =  await AudioHandler(agent_input)

        grand_query = f'{{"written_query": {agent_input.query.strip() if agent_input.query else None}, "audio_description": {audio_description}}}'
        logger.info(f"Grand query: {grand_query}")
        return grand_query
    
    # Checking if it's a valid text type
    elif file_extension in VALID_TEXT_TYPES:
        pdf_content = await PDFHandler(agent_input)

        grand_query = f'{{"written_query": {agent_input.query.strip() if agent_input.query else None}, "pdf_content": {pdf_content}}}'
        logger.info(f"Grand query: {grand_query}")
        return grand_query
    
    # File type not supported
    else:
        return None 