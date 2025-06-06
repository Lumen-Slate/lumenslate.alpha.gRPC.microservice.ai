from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware 
from models.pydantic.models import AgentInput
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from root_agent.agent import root_agent
from google.genai import types
from utils import add_to_history, get_questions_general
import json

try:
    load_dotenv() 
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error loading environment variables: {e}")

api = FastAPI()

# Enabling CORS for all origins
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db_url = "sqlite:///./my_agent_data.db"
session_service = DatabaseSessionService(db_url=db_url)

APP_NAME = "LUMEN_SLATE"
        
@api.post("/agent")
async def main(agent_input: AgentInput):
    
    try:
        initial_state = {
            "user_id": agent_input.user_id,
            "message_history": [],
        }

        existing_sessions = session_service.list_sessions(
        app_name=APP_NAME,
        user_id=agent_input.user_id,
        )

        if existing_sessions and len(existing_sessions.sessions) > 0:
            SESSION_ID = existing_sessions.sessions[0].id
            print(f"Continuing existing session: {SESSION_ID}")
        else:
            new_session = session_service.create_session(
                app_name=APP_NAME,
                user_id=agent_input.user_id,
                state=initial_state,
            )
            SESSION_ID = new_session.id
            print(f"Created new session: {SESSION_ID}")

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        user_message = agent_input.query.strip()


        content = types.Content(role="user", parts=[types.Part(text=agent_input.query)])

        try:
            async for event in runner.run_async(user_id=agent_input.user_id, session_id=SESSION_ID, new_message=content):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        agent_message = event.content.parts[0].text.strip()
                        
                        if agent_message:
                            # Check if the response is JSON
                            try:
                                parsed_json = json.loads(agent_message)
                                
                                # Check if it's an assignment_generator_general type
                                if isinstance(parsed_json, dict) and 'questions_requested' in parsed_json:
                                    # Check if any of the questions have type "assignment_generator_general"
                                    questions_requested = parsed_json.get('questions_requested', [])
                                    if any(q.get('type') == 'assignment_generator_general' for q in questions_requested):
                                        # Handle assignment generation
                                        print("Processing assignment generation request...")
                                        questions_result = get_questions_general(parsed_json)
                                        
                                        if questions_result.get('status') == 'success':
                                            final_agent_message = questions_result.get('agent_response', agent_message)
                                        else:
                                            final_agent_message = questions_result.get('agent_response', "Error generating questions")
                                        
                                        response = {
                                            "agent_response": final_agent_message,
                                            "user_id": agent_input.user_id,
                                            "session_id": SESSION_ID,
                                            "type": "assignment_generated",
                                            "data": questions_result.get('data', {})
                                        }
                                        
                                        # Store the final formatted message in history
                                        agent_message = final_agent_message
                                    else:
                                        # Regular JSON response
                                        response = {
                                            "agent_response": agent_message,
                                            "user_id": agent_input.user_id,
                                            "session_id": SESSION_ID
                                        }
                                else:
                                    # Regular JSON response
                                    response = {
                                        "agent_response": agent_message,
                                        "user_id": agent_input.user_id,
                                        "session_id": SESSION_ID
                                    }
                                    
                            except json.JSONDecodeError:
                                # Not JSON, handle as regular text response
                                response = {
                                    "agent_response": agent_message,
                                    "user_id": agent_input.user_id,
                                    "session_id": SESSION_ID
                                }

                        else:
                            # Empty response
                            response = {
                                "agent_response": "No response generated",
                                "user_id": agent_input.user_id,
                                "session_id": SESSION_ID
                            }
                            agent_message = "No response generated"

                        # Add messages to history
                        try:
                            await add_to_history(user_message, 'user', user_id=agent_input.user_id, session_id=SESSION_ID, app_name=APP_NAME, session_service=session_service)
                        except Exception as history_error:
                            print(f"Error adding user message to history: {history_error}")

                        try:
                            await add_to_history(agent_message, 'agent', user_id=agent_input.user_id, session_id=SESSION_ID, app_name=APP_NAME, session_service=session_service)
                        except Exception as history_error:
                            print(f"Error adding agent message to history: {history_error}")
                        
                        return response
                    
        except Exception as e:
            print(f"Error during agent call: {e}")
            raise HTTPException(status_code=500, detail=f"Agent processing error: {str(e)}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

print("API is running.")











