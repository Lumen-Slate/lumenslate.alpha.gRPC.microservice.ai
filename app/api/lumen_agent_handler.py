import os
import base64
import io
from datetime import datetime
from app.config.logging_config import logger
from app.config.session_config import session_service_manager

# Agent dependencies
from google.adk.runners import Runner
from app.agents.lumen_agent.agent import lumen_agent
from google.genai import types
from app.utils.history_manager import add_to_history
from app.utils.multimodal_handler import MultimodalHandler

# ─────────────────────────────────────────────────────────────────────────────


def _detect_file_type_from_content(file_bytes):
    """
    Detect file type from file content by examining file headers/magic numbers.
    Returns the appropriate file extension based on the actual file content.
    """
    if not file_bytes or len(file_bytes) < 4:
        return ".unknown"

    # Get the first few bytes for magic number detection
    header = file_bytes[:16]

    # Image formats
    if header.startswith(b'\xFF\xD8\xFF'):  # JPEG
        return ".jpg"
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
        return ".png"
    elif header.startswith(b'RIFF') and b'WEBP' in header[:12]:  # WEBP
        return ".webp"

    # Audio formats
    elif header.startswith(b'RIFF') and b'WAVE' in header[:12]:  # WAV
        return ".wav"
    elif header.startswith(b'ID3') or header.startswith(b'\xFF\xFB') or header.startswith(b'\xFF\xF3') or header.startswith(b'\xFF\xF2'):  # MP3
        return ".mp3"
    elif header.startswith(b'FORM') and b'AIFF' in header[:12]:  # AIFF
        return ".aiff"
    elif header.startswith(b'\xFF\xF1') or header.startswith(b'\xFF\xF9'):  # AAC
        return ".aac"
    elif header.startswith(b'OggS'):  # OGG
        return ".ogg"
    elif header.startswith(b'fLaC'):  # FLAC
        return ".flac"

    # PDF format
    elif header.startswith(b'%PDF'):  # PDF
        return ".pdf"

    # If we can't detect the type, return unknown
    return ".unknown"

# ─────────────────────────────────────────────────────────────────────────────


# Agent configuration
session_service = session_service_manager.get_database_service()

APP_NAME = "LUMEN_SLATE"

# ─────────────────────────────────────────────────────────────────────────────


def create_agent_response(message="", teacherId="", agentName="", agentResponse="",
                          sessionId="", createdAt="", updatedAt="", responseTime="",
                          role="agent", feedback=""):
    """Helper function to create a complete agent response with all required fields"""
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


def call_agent(query, runner, user_id, session_id):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(user_id=user_id, session_id=session_id, new_message=content)

    for event in events:
        # Optionally log/debug events here
        # print(f"\nDEBUG EVENT: {event}\n")
        if event.is_final_response() and event.content and event.content.parts:
            final_answer = event.content.parts[0].text.strip()
            # print("\n🟢 FINAL ANSWER\n", final_answer, "\n")
            return final_answer
    return "No response generated"


async def lumen_agent_handler(request):
    start_time = datetime.now()

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
            agent=lumen_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        if not request.message and not request.file:
            return create_agent_response(
                message="Error: No query or file provided.",
                teacherId=request.teacherId,
                agentName="root_agent",
                agentResponse="Error: No query or file provided.",
                sessionId=sessionId,
                role="agent"
            )

        # Checking if file is present and handle accordingly
        if request.file and request.file.strip():
            try:
                # Decode base64 file content
                file_bytes = base64.b64decode(request.file)

                # Create a file-like object with filename and read method
                class FilelikeObject:
                    def __init__(self, data, filename):
                        self.data = data
                        self.filename = filename
                        self._io = io.BytesIO(data)

                    async def read(self):
                        return self.data

                    def read_sync(self):
                        return self.data

                # Determine file type from file content (ignore frontend fileType field)
                file_extension = _detect_file_type_from_content(file_bytes)
                logger.info(f"File type detection: detected extension '{file_extension}' for file of {len(file_bytes)} bytes (frontend provided: '{request.fileType}')")
                filename = f"uploaded_file{file_extension}"
                file_obj = FilelikeObject(file_bytes, filename)

                # Create temporary object for MultimodalHandler compatibility
                class TempAgentInput:
                    def __init__(self, teacherId, query, file):
                        self.teacherId = teacherId
                        self.query = query
                        self.file = file

                temp_agent_input = TempAgentInput(request.teacherId, request.message, file_obj)
                grand_query = await MultimodalHandler(temp_agent_input)
            except Exception as e:
                logger.error(f"Error processing base64 file: {str(e)}")
                return create_agent_response(
                    message="File processing error",
                    teacherId=request.teacherId,
                    agentName="root_agent",
                    agentResponse=f"Error processing uploaded file: {str(e)}",
                    sessionId=getattr(locals(), 'sessionId', ''),
                    role="agent"
                )

            # Handle unsupported file types
            if grand_query is None:
                supported_image_types = ".jpg, .jpeg, .png, .webp"
                supported_audio_types = ".wav, .mp3, .aiff, .aac, .ogg, .flac"
                supported_text_types = ".pdf"
                error_message = f"Unsupported file type detected. The system automatically detects file types from content. Supported file types are:\nImages: {supported_image_types}\nAudio: {supported_audio_types}\nText: {supported_text_types}"

                return create_agent_response(
                    message="Unsupported file type detected",
                    teacherId=request.teacherId,
                    agentName="general_chat_agent",
                    agentResponse=error_message,
                    sessionId=sessionId,
                    role="agent"
                )
        else:
            # Using original query if no file
            grand_query = request.message.strip() if request.message else None

        user_message = grand_query

        agent_message = call_agent(grand_query, runner, request.teacherId, sessionId)
        if not agent_message:
            agent_message = "No response generated"

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

        # Storing message history
        # try:
        #     await add_to_history(user_message, 'user', request.teacherId, sessionId, APP_NAME, session_service)
        #     await add_to_history(agent_message, 'agent', request.teacherId, sessionId, APP_NAME, session_service)
        # except Exception as e:
        #     logger.warning(f"History logging failed: {e}")

        return response

    except Exception as e:
        logger.exception(f"Agent error: {str(e)}")
        return create_agent_response(
            message=f"Agent error: {str(e)}",
            teacherId=getattr(request, 'teacherId', ''),
            agentName="root_agent",
            agentResponse=f"An error occurred: {str(e)}",
            sessionId=getattr(locals(), 'sessionId', ''),
            role="agent"
        )
