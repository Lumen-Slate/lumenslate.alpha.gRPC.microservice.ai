import os
from datetime import datetime
from app.config.logging_config import logger
from app.config.session_config import session_service_manager

# Agent dependencies
from google.adk.runners import Runner
from app.agents.rag_agent.agent import rag_agent
from google.genai import types


# ─────────────────────────────────────────────────────────────────────────────

# load_dotenv()

# Agent configuration
# default_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sqlite.db")
# db_url = os.getenv("RAG_DATABASE_URL", f"sqlite:///{default_db_path}")
session_service = session_service_manager.get_database_service()
APP_NAME = "LUMEN_SLATE_RAG"

# ─────────────────────────────────────────────────────────────────────────────


def create_agent_response(message="", corpusName="", agentName="", agentResponse="",
                          sessionId="", createdAt="", updatedAt="", responseTime="",
                          role="agent", feedback=""):
    """Helper function to create a complete agent response with all required fields"""
    current_time = datetime.now().isoformat()
    return {
        "message": str(message) if message else "",
        "corpusName": str(corpusName) if corpusName else "",
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


async def rag_agent_handler(request):
    start_time = datetime.now()

    try:
        # Validate inputs: corpusName and message are both mandatory
        if not request.corpusName:
            return create_agent_response(
                message="Error: corpusName is mandatory.",
                agentName="rag_agent",
                agentResponse="Error: corpusName is mandatory.",
                role="agent"
            )

        if not request.message:
            return create_agent_response(
                message="Error: message is mandatory.",
                corpusName=request.corpusName,
                agentName="rag_agent",
                agentResponse="Error: message is mandatory.",
                role="agent"
            )

        initial_state = {
            "user_id": request.corpusName,
            "message_history": [],
        }

        existing_sessions = await session_service.list_sessions(
            app_name=APP_NAME,
            user_id=request.corpusName,
        )

        if existing_sessions and len(existing_sessions.sessions) > 0:
            SESSION_ID = existing_sessions.sessions[0].id
        else:
            new_session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=request.corpusName,
                state=initial_state,
            )
            SESSION_ID = new_session.id

        runner = Runner(
            agent=rag_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        user_message = request.message.strip()
        grand_query = f'{{"corpusName": "{request.corpusName}", "message": "{user_message}"}}'

        agent_message = call_agent(grand_query, runner, request.corpusName, SESSION_ID)
        if not agent_message:
            agent_message = "No response generated"

        end_time = datetime.now()
        response_time = str((end_time - start_time).total_seconds())

        response = create_agent_response(
            message="Agent response",
            corpusName=request.corpusName,
            agentName="rag_agent",
            agentResponse=agent_message,
            sessionId=SESSION_ID,
            responseTime=response_time,
            role="agent"
        )

        # Note: History is managed by InMemorySessionService
        # No additional database storage needed

        return response

        # If no final response was generated
        # return create_agent_response(
        #     message="No response generated",
        #     teacherId=request.teacherId,
        #     agentName="rag_agent",
        #     agentResponse="No response was generated from the agent",
        #     sessionId=SESSION_ID,
        #     role="agent"
        # )

    except Exception as e:
        logger.exception(f"Agent error: {str(e)}")
        return create_agent_response(
            message=f"Agent error: {str(e)}",
            corpusName=getattr(request, 'corpusName', ''),
            agentName="rag_agent",
            agentResponse=f"An error occurred: {str(e)}",
            sessionId=getattr(locals(), 'SESSION_ID', ''),
            role="agent"
        )
