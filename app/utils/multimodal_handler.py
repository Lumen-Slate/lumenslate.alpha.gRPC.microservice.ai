from google import genai
from .clean_text import clean_text
from app.config.logging_config import logger
from dotenv import load_dotenv
import os
import tempfile
from .auth_helper import get_project_id

load_dotenv()

# Check if using Vertex AI or Google AI Studio
USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"

if USE_VERTEXAI:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    
    # Initialize Vertex AI
    project_id = get_project_id()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    vertexai.init(project=project_id, location=location)
    
    # Create Vertex AI model
    model = GenerativeModel('gemini-2.5-flash-lite')
    client = None  # Not using genai client for Vertex AI
else:
    # Use Google AI Studio client
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    model = None  # Not using Vertex AI model

VALID_IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.webp'}

VALID_AUDIO_TYPES = {'.wav', '.mp3', '.aiff', '.aac', '.ogg', '.flac'}

VALID_TEXT_TYPES = {'.pdf'}

def get_mime_type(file_extension):
    """Get the appropriate MIME type based on file extension."""
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg', 
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg',
        '.aiff': 'audio/aiff',
        '.aac': 'audio/aac',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
        '.pdf': 'application/pdf'
    }
    return mime_map.get(file_extension.lower(), 'application/octet-stream')

async def ImageHandler(agent_input, file_extension='.jpg') -> str:
    image_bytes = await agent_input.file.read()

    try:
        if USE_VERTEXAI:
            # Use Vertex AI approach
            mime_type = get_mime_type(file_extension)
            image_part = Part.from_data(
                data=image_bytes,
                mime_type=mime_type
            )
            
            response = model.generate_content([
                "Extract all the text from the image and return the text only.",
                image_part
            ])
            
            response_text = response.text if hasattr(response, 'text') else str(response)
        else:
            # Use Google AI Studio approach with temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(image_bytes)
                tmp_file_path = tmp.name

            try:
                file = client.files.upload(file=tmp_file_path)
                response = client.models.generate_content(
                    model='gemini-2.5-flash-lite',
                    contents=[
                        'Extract all the text from the image and return the text only.',
                        file
                    ],
                )
                response_text = response.text if hasattr(response, 'text') else str(response)
            finally:
                os.remove(tmp_file_path)

        logger.info(f"Image transcription successful")
        return clean_text(response_text) if response_text else "Could not generate transcription."
    except Exception as e:
        logger.error(f"Error during image transcription: {str(e)}")
        return f"Error during transcription: {str(e)}"


async def AudioHandler(agent_input, file_extension='.wav') -> str:
    audio_bytes = await agent_input.file.read()

    try:
        if USE_VERTEXAI:
            # Use Vertex AI approach
            mime_type = get_mime_type(file_extension)
            audio_part = Part.from_data(
                data=audio_bytes,
                mime_type=mime_type
            )
            
            response = model.generate_content([
                "Transcribe the audio into text and return the text only.",
                audio_part
            ])
            
            response_text = response.text if hasattr(response, 'text') else str(response)
        else:
            # Use Google AI Studio approach with temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                tmp_file_path = tmp.name

            try:
                file = client.files.upload(file=tmp_file_path)
                response = client.models.generate_content(
                    model='gemini-2.5-flash-lite',
                    contents=[
                        'Transcribe the audio into text and return the text only.',
                        file
                    ],
                )
                response_text = response.text if hasattr(response, 'text') else str(response)
            finally:
                os.remove(tmp_file_path)

        return clean_text(response_text) if response_text else "Could not generate transcription."
    except Exception as e:
        logger.error(f"Error during audio transcription: {str(e)}")
        return f"Error during transcription: {str(e)}"


async def PDFHandler(agent_input, file_extension='.pdf') -> str:
    pdf_bytes = await agent_input.file.read()

    try:
        if USE_VERTEXAI:
            # Use Vertex AI approach
            mime_type = get_mime_type(file_extension)
            pdf_part = Part.from_data(
                data=pdf_bytes,
                mime_type=mime_type
            )
            
            response = model.generate_content([
                "Extract all the text content from the PDF document and return the text only.",
                pdf_part
            ])
            
            response_text = response.text if hasattr(response, 'text') else str(response)
        else:
            # Use Google AI Studio approach with temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_bytes)
                tmp_file_path = tmp.name

            try:
                file = client.files.upload(file=tmp_file_path)
                response = client.models.generate_content(
                    model='gemini-2.5-flash-lite',
                    contents=[
                        'Extract all the text content from the PDF document and return the text only.',
                        file
                    ],
                )
                response_text = response.text if hasattr(response, 'text') else str(response)
            finally:
                os.remove(tmp_file_path)

        return clean_text(response_text) if response_text else "Could not extract text from PDF."
    except Exception as e:
        logger.error(f"Error during PDF text extraction: {str(e)}")
        return f"Error during PDF text extraction: {str(e)}"


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
        image_description = await ImageHandler(agent_input, file_extension)
        grand_query = f'{{"written_query": {agent_input.query.strip() if agent_input.query else None}, "image_description": {image_description}}}'
        return grand_query
    
    # Checking if it's a valid audio type
    elif file_extension in VALID_AUDIO_TYPES:
        audio_description = await AudioHandler(agent_input, file_extension)
        grand_query = f'{{"written_query": {agent_input.query.strip() if agent_input.query else None}, "audio_description": {audio_description}}}'
        return grand_query
    
    # Checking if it's a valid text type
    elif file_extension in VALID_TEXT_TYPES:
        pdf_content = await PDFHandler(agent_input, file_extension)
        grand_query = f'{{"written_query": {agent_input.query.strip() if agent_input.query else None}, "pdf_content": {pdf_content}}}'
        return grand_query
    
    # File type not supported
    else:
        return None 