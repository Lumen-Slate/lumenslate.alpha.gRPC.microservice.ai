from ..models.pydantic.models import AgentInput

VALID_IMAGE_TYPES = {
    '.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'
}

VALID_AUDIO_TYPES = {
    '.wav', '.mp3', '.aiff', '.aac', '.ogg', '.flac'
}

async def ImageHandler(agent_input: AgentInput) -> str:
    processed_query = "placeholder"
    return processed_query

async def AudioHandler(agent_input: AgentInput) -> str:
    processed_query = "placeholder"
    return processed_query

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
        return await ImageHandler(agent_input)
    
    # Checking if it's a valid audio type
    elif file_extension in VALID_AUDIO_TYPES:
        return await AudioHandler(agent_input)
    
    # File type not supported
    else:
        return None 