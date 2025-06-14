import base64
import io
import json
from datetime import datetime
from typing import Any, Dict, Optional
from app.config.logging_config import logger

# Agent dependencies
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from app.agents.main_agent.agent import main_agent
from google.genai import types
from app.utils.history_manager import add_to_history
from app.utils.multimodal_handler import MultimodalHandler

# ─────────────────────────────────────────────────────────────────────────────

SUPPORTED_IMAGE_TYPES = (".jpg", ".jpeg", ".png", ".webp")
SUPPORTED_AUDIO_TYPES = (".wav", ".mp3", ".aiff", ".aac", ".ogg", ".flac")
SUPPORTED_TEXT_TYPES = (".pdf",)
ALL_SUPPORTED_TYPES = SUPPORTED_IMAGE_TYPES + SUPPORTED_AUDIO_TYPES + SUPPORTED_TEXT_TYPES

DB_URL = 'sqlite:///app/data/sqlite.db'
APP_NAME = "LUMEN_SLATE"

session_service = DatabaseSessionService(db_url=DB_URL)

# ─────────────────────────────────────────────────────────────────────────────

class FileProcessingError(Exception):
    """Custom exception for file processing errors."""
    pass

# ─────────────────────────────────────────────────────────────────────────────

def _detect_file_type_from_content(file_bytes: bytes) -> str:
    """
    Detect file type from file content by examining file headers/magic numbers.
    Returns the appropriate file extension based on the actual file content.
    """
    if not file_bytes or len(file_bytes) < 4:
        return ".unknown"
    header = file_bytes[:16]
    if header.startswith(b'\xFF\xD8\xFF'):
        return ".jpg"
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
        return ".png"
    elif header.startswith(b'RIFF') and b'WEBP' in header[:12]:
        return ".webp"
    elif header.startswith(b'RIFF') and b'WAVE' in header[:12]:
        return ".wav"
    elif header.startswith(b'ID3') or header.startswith(b'\xFF\xFB') or header.startswith(b'\xFF\xF3') or header.startswith(b'\xFF\xF2'):
        return ".mp3"
    elif header.startswith(b'FORM') and b'AIFF' in header[:12]:
        return ".aiff"
    elif header.startswith(b'\xFF\xF1') or header.startswith(b'\xFF\xF9'):
        return ".aac"
    elif header.startswith(b'OggS'):
        return ".ogg"
    elif header.startswith(b'fLaC'):
        return ".flac"
    elif header.startswith(b'%PDF'):
        return ".pdf"
    return ".unknown"

# ─────────────────────────────────────────────────────────────────────────────

def create_agent_response(
    message: str = "",
    teacherId: str = "",
    agentName: str = "",
    agentResponse: str = "",
    sessionId: str = "",
    createdAt: Optional[str] = None,
    updatedAt: Optional[str] = None,
    responseTime: str = "",
    role: str = "agent",
    feedback: str = ""
) -> Dict[str, Any]:
    """Helper function to create a complete agent response with all required fields."""
    current_time = datetime.now().isoformat()
    return {
        "message": str(message) if message else "",
        "teacherId": str(teacherId) if teacherId else "",
        "agentName": str(agentName) if agentName else "",
        "agentResponse": str(agentResponse) if agentResponse else "",
        "sessionId": str(sessionId) if sessionId else "",
        "createdAt": str(createdAt) if createdAt else current_time,
        "updatedAt": str(updatedAt) if updatedAt else current_time,
        "responseTime": str(responseTime) if responseTime else "",
        "role": str(role) if role else "agent",
        "feedback": str(feedback) if feedback else ""
    }

# ─────────────────────────────────────────────────────────────────────────────

def _decode_and_prepare_file(file_b64: str) -> Any:
    """
    Decode a base64-encoded file and wrap it in a file-like object for processing.
    Returns a tuple of (file_obj, detected_extension).
    Raises FileProcessingError on failure.
    """
    try:
        file_bytes = base64.b64decode(file_b64)
    except Exception as e:
        raise FileProcessingError(f"Base64 decode failed: {e}")
    file_extension = _detect_file_type_from_content(file_bytes)
    filename = f"uploaded_file{file_extension}"
    class FilelikeObject:
        def __init__(self, data: bytes, filename: str):
            self.data = data
            self.filename = filename
            self._io = io.BytesIO(data)
        async def read(self) -> bytes:
            return self.data
        def read_sync(self) -> bytes:
            return self.data
    return FilelikeObject(file_bytes, filename), file_extension

# ─────────────────────────────────────────────────────────────────────────────

def _is_supported_filetype(extension: str) -> bool:
    return extension in ALL_SUPPORTED_TYPES

# ─────────────────────────────────────────────────────────────────────────────

async def _handle_file_input(request) -> Optional[str]:
    """
    Handles file input from the request, returning the processed query string or None if unsupported.
    Raises FileProcessingError on file decode/processing errors.
    """
    file_obj, file_extension = _decode_and_prepare_file(request.file)
    if not _is_supported_filetype(file_extension):
        return None
    class TempAgentInput:
        def __init__(self, teacherId, query, file):
            self.teacherId = teacherId
            self.query = query
            self.file = file
    temp_agent_input = TempAgentInput(request.teacherId, request.message, file_obj)
    return await MultimodalHandler(temp_agent_input)

# ─────────────────────────────────────────────────────────────────────────────

async def main_agent_handler(request) -> Dict[str, Any]:
    """
    Main handler for the primary agent. Processes text and file queries, manages sessions, and returns agent responses.
    """
    start_time = datetime.now()
    sessionId = None
    try:
        initial_state = {
            "user_id": request.teacherId,
            "message_history": [],
        }
        existing_sessions = await session_service.list_sessions(
            app_name=APP_NAME,
            user_id=request.teacherId,
        )
        if existing_sessions and len(existing_sessions.sessions) > 0:
            sessionId = existing_sessions.sessions[0].id
        else:
            new_session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=request.teacherId,
                state=initial_state,
            )
            sessionId = new_session.id
        runner = Runner(
            agent=main_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )
        if not request.message and not getattr(request, 'file', None):
            return create_agent_response(
                message="Error: No query or file provided.",
                teacherId=request.teacherId,
                agentName="root_agent",
                agentResponse="Error: No query or file provided.",
                sessionId=sessionId,
                role="agent"
            )
        # File handling
        grand_query: Optional[str] = None
        if getattr(request, 'file', None) and request.file.strip():
            try:
                grand_query = await _handle_file_input(request)
                # Handle JSON error messages from MultimodalHandler
                if grand_query is not None:
                    try:
                        parsed = json.loads(grand_query)
                        if isinstance(parsed, dict) and "error" in parsed:
                            error_message = (
                                f"File processing error: {parsed['error']}\n"
                                f"Supported file types are:\nImages: {', '.join(SUPPORTED_IMAGE_TYPES)}\n"
                                f"Audio: {', '.join(SUPPORTED_AUDIO_TYPES)}\n"
                                f"Text: {', '.join(SUPPORTED_TEXT_TYPES)}"
                            )
                            return create_agent_response(
                                message="Unsupported file type detected",
                                teacherId=request.teacherId,
                                agentName="general_chat_agent",
                                agentResponse=error_message,
                                sessionId=sessionId,
                                role="agent"
                            )
                    except Exception:
                        pass
            except FileProcessingError as e:
                logger.error(f"Error processing base64 file: {str(e)}")
                return create_agent_response(
                    message="File processing error",
                    teacherId=request.teacherId,
                    agentName="root_agent",
                    agentResponse=f"Error processing uploaded file: {str(e)}",
                    sessionId=sessionId or '',
                    role="agent"
                )
            if grand_query is None:
                error_message = (
                    "Unsupported file type detected. The system automatically detects file types from content. "
                    f"Supported file types are:\nImages: {', '.join(SUPPORTED_IMAGE_TYPES)}\n"
                    f"Audio: {', '.join(SUPPORTED_AUDIO_TYPES)}\n"
                    f"Text: {', '.join(SUPPORTED_TEXT_TYPES)}"
                )
                return create_agent_response(
                    message="Unsupported file type detected",
                    teacherId=request.teacherId,
                    agentName="general_chat_agent",
                    agentResponse=error_message,
                    sessionId=sessionId,
                    role="agent"
                )
        else:
            grand_query = request.message.strip() if request.message else None
        user_message = grand_query
        content = types.Content(role="user", parts=[types.Part(text=grand_query)])
        async for event in runner.run_async(user_id=request.teacherId, session_id=sessionId, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                agent_message = event.content.parts[0].text.strip() or "No response generated"
                end_time = datetime.now()
                responseTime = str((end_time - start_time).total_seconds())
                response = create_agent_response(
                    message="Agent response",
                    teacherId=request.teacherId,
                    agentName="root_agent",
                    agentResponse=agent_message,
                    sessionId=sessionId,
                    responseTime=responseTime,
                    role="agent"
                )
                try:
                    await add_to_history(user_message, 'user', request.teacherId, sessionId, APP_NAME, session_service)
                    await add_to_history(agent_message, 'agent', request.teacherId, sessionId, APP_NAME, session_service)
                except Exception as e:
                    pass
                return response
        return create_agent_response(
            message="No response generated",
            teacherId=request.teacherId,
            agentName="root_agent",
            agentResponse="No response was generated from the agent",
            sessionId=sessionId,
            role="agent"
        )
    except Exception as e:
        logger.exception(f"Agent error: {str(e)}")
        return create_agent_response(
            message=f"Agent error: {str(e)}",
            teacherId=getattr(request, 'teacherId', ''),
            agentName="root_agent",
            agentResponse=f"An error occurred: {str(e)}",
            sessionId=sessionId or '',
            role="agent"
        )
