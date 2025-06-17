import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from config.logging_config import logger

# Agent dependencies
from app.models.pydantic.models import AgentInput
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from app.agents.root_agent.agent import root_agent
from google.genai import types
from app.utils.history_manager import add_to_history
from app.utils.question_retriever import get_questions_general
from app.utils.assessment_handler import save_subject_report
from app.utils.multimodal_handler import MultimodalHandler

# ─────────────────────────────────────────────────────────────────────────────

primary_agent_handler_router = APIRouter()

# Agent configuration
db_url = os.getenv("DATABASE_URL")
session_service = DatabaseSessionService(db_url=db_url)
APP_NAME = "LUMEN_SLATE"

# ─────────────────────────────────────────────────────────────────────────────

def create_agent_response(message="", user_id="", agent_name="", agent_response="", 
                         session_id="", created_at="", updated_at="", response_time="", 
                         role="agent", feedback=""):
    """Helper function to create a complete agent response with all required fields"""
    current_time = datetime.now().isoformat()
    return {
        "message": str(message) if message else "",
        "user_id": str(user_id) if user_id else "",
        "agent_name": str(agent_name) if agent_name else "",
        "agent_response": str(agent_response) if agent_response else "",
        "session_id": str(session_id) if session_id else "",
        "createdAt": str(created_at) if created_at else current_time,
        "updatedAt": str(updated_at) if updated_at else current_time,
        "response_time": str(response_time) if response_time else "",
        "role": str(role) if role else "agent",
        "feedback": str(feedback) if feedback else ""
    }

async def primary_agent_handler(request):
    start_time = datetime.now()
    
    try:
        initial_state = {
            "user_id": request.userId,
            "message_history": [],
        }

        existing_sessions = await session_service.list_sessions(
            app_name=APP_NAME,
            user_id=request.userId,
        )

        if existing_sessions and len(existing_sessions.sessions) > 0:
            SESSION_ID = existing_sessions.sessions[0].id
        else:
            new_session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=request.userId,
                state=initial_state,
            )
            SESSION_ID = new_session.id

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        if not request.message and not request.file:
            return create_agent_response(
                message="Error: No query or file provided.",
                user_id=request.userId,
                agent_name="root_agent",
                agent_response="Error: No query or file provided.",
                session_id=SESSION_ID,
                role="agent"
            )

        # Checking if file is present and handle accordingly
        if request.file and request.file:
            # Create temporary object for MultimodalHandler compatibility
            class TempAgentInput:
                def __init__(self, user_id, query, file):
                    self.user_id = user_id
                    self.query = query
                    self.file = file
            
            temp_agent_input = TempAgentInput(request.userId, request.message, request.file)
            grand_query = await MultimodalHandler(temp_agent_input)
            
            # Handle unsupported file types
            if grand_query is None:
                supported_image_types = ".jpg, .jpeg, .png, .webp"
                supported_audio_types = ".wav, .mp3, .aiff, .aac, .ogg, .flac"
                error_message = f"Unsupported file type. Supported file types are:\nImages: {supported_image_types}\nAudio: {supported_audio_types}"
                
                return create_agent_response(
                    message="Unsupported file type",
                    user_id=request.userId,
                    agent_name="root_agent",
                    agent_response=error_message,
                    session_id=SESSION_ID,
                    role="agent"
                )
        else:
            # Using original query if no file
            grand_query = request.message.strip() if request.message else None

        user_message = grand_query
        content = types.Content(role="user", parts=[types.Part(text=grand_query)])

        async for event in runner.run_async(user_id=request.userId, session_id=SESSION_ID, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                agent_message = event.content.parts[0].text.strip()
                if not agent_message:
                    agent_message = "No response generated"

                end_time = datetime.now()
                response_time = str((end_time - start_time).total_seconds())

                try:
                    parsed_json = json.loads(agent_message)
                    if isinstance(parsed_json, dict):
                        if 'questions_requested' in parsed_json:
                            if any(q.get('type') == 'assignment_generator_general' for q in parsed_json['questions_requested']):
                                questions_result = get_questions_general(parsed_json)
                                final_agent_message = questions_result.get('agent_response', agent_message)
                                response = create_agent_response(
                                    message="Assignment generated successfully",
                                    user_id=request.userId,
                                    agent_name="assignment_generator_general",
                                    agent_response=final_agent_message,
                                    session_id=SESSION_ID,
                                    response_time=response_time,
                                    role="agent"
                                )
                                agent_message = final_agent_message
                            else:
                                response = create_agent_response(
                                    message="Questions requested",
                                    user_id=request.userId,
                                    agent_name="root_agent",
                                    agent_response=agent_message,
                                    session_id=SESSION_ID,
                                    response_time=response_time,
                                    role="agent"
                                )
                        elif 'assessment_data' in parsed_json:
                            assessment_result = save_subject_report(parsed_json, request.userId)
                            final_agent_message = assessment_result.get('agent_response', agent_message)
                            response = create_agent_response(
                                message="Subject Assessment report processed",
                                user_id=request.userId,
                                agent_name="assessment_agent",
                                agent_response=final_agent_message,
                                session_id=SESSION_ID,
                                response_time=response_time,
                                role="agent"
                            )
                            agent_message = final_agent_message
                        else:
                            response = create_agent_response(
                                message="Agent response",
                                user_id=request.userId,
                                agent_name="root_agent",
                                agent_response=agent_message,
                                session_id=SESSION_ID,
                                response_time=response_time,
                                role="agent"
                            )
                    else:
                        response = create_agent_response(
                            message="Agent response",
                            user_id=request.userId,
                            agent_name="root_agent",
                            agent_response=agent_message,
                            session_id=SESSION_ID,
                            response_time=response_time,
                            role="agent"
                        )
                except json.JSONDecodeError:
                    response = create_agent_response(
                        message="Agent response",
                        user_id=request.userId,
                        agent_name="root_agent",
                        agent_response=agent_message,
                        session_id=SESSION_ID,
                        response_time=response_time,
                        role="agent"
                    )

                # Storing message history
                try:
                    await add_to_history(user_message, 'user', request.userId, SESSION_ID, APP_NAME, session_service)
                    await add_to_history(agent_message, 'agent', request.userId, SESSION_ID, APP_NAME, session_service)
                except Exception as e:
                    logger.warning(f"History logging failed: {e}")

                return response

        # If no final response was generated
        return create_agent_response(
            message="No response generated",
            user_id=request.userId,
            agent_name="root_agent",
            agent_response="No response was generated from the agent",
            session_id=SESSION_ID,
            role="agent"
        )

    except Exception as e:
        logger.exception(f"Agent error: {str(e)}")
        return create_agent_response(
            message=f"Agent error: {str(e)}",
            user_id=getattr(request, 'userId', ''),
            agent_name="root_agent",
            agent_response=f"An error occurred: {str(e)}",
            session_id=getattr(locals(), 'SESSION_ID', ''),
            role="agent"
        )
