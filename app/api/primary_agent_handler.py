import os
from datetime import datetime
from app.config.logging_config import logger

# Agent dependencies
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from app.agents.root_agent.agent import root_agent
from google.genai import types
from app.utils.history_manager import add_to_history
from app.utils.multimodal_handler import MultimodalHandler

# ─────────────────────────────────────────────────────────────────────────────


# Agent configuration
db_url = os.getenv("DATABASE_URL")
session_service = DatabaseSessionService(db_url=db_url)
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

async def primary_agent_handler(request):
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
            agent=root_agent,
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
        if request.file and request.file:
            # Create temporary object for MultimodalHandler compatibility
            class TempAgentInput:
                def __init__(self, teacherId, query, file):
                    self.teacherId = teacherId
                    self.query = query
                    self.file = file
            
            temp_agent_input = TempAgentInput(request.teacherId, request.message, request.file)
            grand_query = await MultimodalHandler(temp_agent_input)
            
            # Handle unsupported file types
            if grand_query is None:
                supported_image_types = ".jpg, .jpeg, .png, .webp"
                supported_audio_types = ".wav, .mp3, .aiff, .aac, .ogg, .flac"
                error_message = f"Unsupported file type. Supported file types are:\nImages: {supported_image_types}\nAudio: {supported_audio_types}"
                
                return create_agent_response(
                    message="Unsupported file type",
                    teacherId=request.teacherId,
                    agentName="root_agent",
                    agentResponse=error_message,
                    sessionId=sessionId,
                    role="agent"
                )
        else:
            # Using original query if no file
            grand_query = request.message.strip() if request.message else None

        user_message = grand_query
        content = types.Content(role="user", parts=[types.Part(text=grand_query)])

        async for event in runner.run_async(user_id=request.teacherId, session_id=sessionId, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                agent_message = event.content.parts[0].text.strip()
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
                try:
                    await add_to_history(user_message, 'user', request.teacherId, sessionId, APP_NAME, session_service)
                    await add_to_history(agent_message, 'agent', request.teacherId, sessionId, APP_NAME, session_service)
                except Exception as e:
                    logger.warning(f"History logging failed: {e}")

                return response

        # If no final response was generated
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
            sessionId=getattr(locals(), 'sessionId', ''),
            role="agent"
        )
