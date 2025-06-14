from ..models.pydantic.models import AgentInput
from google import genai
from .clean_text import clean_text
import pytesseract
from PIL import Image
import io

VALID_IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.webp'}

VALID_AUDIO_TYPES = {'.wav', '.mp3', '.aiff', '.aac', '.ogg', '.flac'}

async def ImageHandler(agent_input: AgentInput) -> str:
    try:
        image_bytes = await agent_input.file.read()
        image = Image.open(io.BytesIO(image_bytes))
        extracted_text = pytesseract.image_to_string(image)
        return extracted_text
    except Exception as e:
        return f"Error processing image: {str(e)}"
    finally:
        if 'image' in locals():
            image.close()

async def AudioHandler(agent_input: AgentInput) -> str:
    audio_file_type = agent_input.file.content_type

    audio_bytes = await agent_input.file.read()

    model = genai.GenerativeModel("gemini-2.0-flash")  

    response = model.generate_content([
        "Transcribe the audio into text and return the text only.",
        {
            "mime_type": audio_file_type,
            "data": audio_bytes
        }
    ])

    return clean_text(response.text) if response and hasattr(response, "text") else "Could not generate transcription."

async def MultimodalHandler(agent_input: AgentInput) -> str:

    if not agent_input.file or not agent_input.file.filename:
        return agent_input.query.strip()
    
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

        grand_query = f'{"written_query": {agent_input.query.strip()}, "image_description": {image_description}}'
        return grand_query
    
    # Checking if it's a valid audio type
    elif file_extension in VALID_AUDIO_TYPES:
        audio_description =  await AudioHandler(agent_input)

        grand_query = f'{"written_query": {agent_input.query.strip()}, "audio_description": {audio_description}}'
        return grand_query
    
    # File type not supported
    else:
        return None 