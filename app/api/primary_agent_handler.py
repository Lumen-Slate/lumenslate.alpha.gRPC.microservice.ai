import os
import json
from fastapi import APIRouter, HTTPException
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
db_url = "sqlite:///./app/data/my_agent_data.db"
session_service = DatabaseSessionService(db_url=db_url)
APP_NAME = "LUMEN_SLATE"

# ─────────────────────────────────────────────────────────────────────────────

@primary_agent_handler_router.post("/agent", tags=["Primary Agent Handler"])
async def primary_agent_handler(agent_input: AgentInput):
    try:
        initial_state = {
            "user_id": agent_input.user_id,
            "message_history": [],
        }

        existing_sessions = await session_service.list_sessions(
            app_name=APP_NAME,
            user_id=agent_input.user_id,
        )

        if existing_sessions and len(existing_sessions.sessions) > 0:
            SESSION_ID = existing_sessions.sessions[0].id
        else:
            new_session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=agent_input.user_id,
                state=initial_state,
            )
            SESSION_ID = new_session.id

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        # Checking if file is present and handle accordingly
        if agent_input.file and agent_input.file.filename:
            # Passing entire AgentInput to MultimodalHandler
            grand_query = await MultimodalHandler(agent_input)
            
            # Handle unsupported file types
            if grand_query is None:
                supported_image_types = ".jpg, .jpeg, .png, .webp"
                supported_audio_types = ".wav, .mp3, .aiff, .aac, .ogg, .flac"
                error_message = f"Unsupported file type '{agent_input.file.filename}'. Supported file types are:\nImages: {supported_image_types}\nAudio: {supported_audio_types}"
                
                return {
                    "agent_response": error_message,
                    "user_id": agent_input.user_id,
                    "session_id": None,
                    "error": "unsupported_file_type"
                }
        else:
            # Using original query if no file
            grand_query = agent_input.query.strip()

        user_message = grand_query
        content = types.Content(role="user", parts=[types.Part(text=grand_query)])

        async for event in runner.run_async(user_id=agent_input.user_id, session_id=SESSION_ID, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                agent_message = event.content.parts[0].text.strip()
                if not agent_message:
                    agent_message = "No response generated"

                try:
                    parsed_json = json.loads(agent_message)
                    if isinstance(parsed_json, dict):
                        if 'questions_requested' in parsed_json:
                            if any(q.get('type') == 'assignment_generator_general' for q in parsed_json['questions_requested']):
                                questions_result = get_questions_general(parsed_json)
                                final_agent_message = questions_result.get('agent_response', agent_message)
                                response = {
                                    "agent_response": final_agent_message,
                                    "user_id": agent_input.user_id,
                                    "session_id": SESSION_ID,
                                    "type": "assignment_generated",
                                    "data": questions_result.get('data', {})
                                }
                                agent_message = final_agent_message
                            else:
                                response = {
                                    "agent_response": agent_message,
                                    "user_id": agent_input.user_id,
                                    "session_id": SESSION_ID
                                }
                        elif 'assessment_data' in parsed_json:
                            assessment_result = save_subject_report(parsed_json, agent_input.user_id)
                            final_agent_message = assessment_result.get('agent_response', agent_message)
                            response = {
                                "agent_response": final_agent_message,
                                "user_id": agent_input.user_id,
                                "session_id": SESSION_ID,
                                "type": "subject_report_created" if assessment_result.get('status') == 'success' else "subject_report_error",
                                "data": assessment_result.get('data', {})
                            }
                            agent_message = final_agent_message
                        else:
                            response = {
                                "agent_response": agent_message,
                                "user_id": agent_input.user_id,
                                "session_id": SESSION_ID
                            }
                    else:
                        response = {
                            "agent_response": agent_message,
                            "user_id": agent_input.user_id,
                            "session_id": SESSION_ID
                        }
                except json.JSONDecodeError:
                    response = {
                        "agent_response": agent_message,
                        "user_id": agent_input.user_id,
                        "session_id": SESSION_ID
                    }

                # Storing message history
                try:
                    await add_to_history(user_message, 'user', agent_input.user_id, SESSION_ID, APP_NAME, session_service)
                    await add_to_history(agent_message, 'agent', agent_input.user_id, SESSION_ID, APP_NAME, session_service)
                except Exception as e:
                    logger.warning(f"History logging failed: {e}")

                return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
