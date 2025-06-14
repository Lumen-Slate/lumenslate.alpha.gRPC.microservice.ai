from datetime import datetime
from typing import Any, Dict, Optional
from app.config.logging_config import logger

# Agent dependencies
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from app.agents.rag_agent.agent import rag_agent
from google.genai import types


# ─────────────────────────────────────────────────────────────────────────────

# load_dotenv()

# Agent configuration
# default_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sqlite.db")
# db_url = os.getenv("RAG_DATABASE_URL", f"sqlite:///{default_db_path}")
session_service = InMemorySessionService()
APP_NAME = "LUMEN_SLATE_RAG"

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

async def rag_agent_handler(request) -> Dict[str, Any]:
    """
    Main handler for the RAG agent. Processes text queries, manages sessions, and returns agent responses.
    """
    start_time = datetime.now()
    session_id = None
    try:
        # Validate inputs: teacherId and message are both mandatory
        if not getattr(request, 'teacherId', None):
            return create_agent_response(
                message="Error: teacherId is mandatory.",
                agentName="rag_agent",
                agentResponse="Error: teacherId is mandatory.",
                role="agent"
            )
        if not getattr(request, 'message', None):
            return create_agent_response(
                message="Error: message is mandatory.",
                teacherId=getattr(request, 'teacherId', ''),
                agentName="rag_agent",
                agentResponse="Error: message is mandatory.",
                role="agent"
            )
        initial_state = {
            "user_id": request.teacherId,
            "message_history": [],
        }
        existing_sessions = await session_service.list_sessions(
            app_name=APP_NAME,
            user_id=request.teacherId,
        )
        if existing_sessions and len(existing_sessions.sessions) > 0:
            session_id = existing_sessions.sessions[0].id
        else:
            new_session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=request.teacherId,
                state=initial_state,
            )
            session_id = new_session.id
        runner = Runner(
            agent=rag_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )
        user_message = request.message.strip()
        grand_query = f'{{"corpusName": "{request.teacherId}", "message": "{user_message}"}}'
        content = types.Content(role="user", parts=[types.Part(text=grand_query)])
        async for event in runner.run_async(user_id=request.teacherId, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                agent_message = event.content.parts[0].text.strip() or "No response generated"
                end_time = datetime.now()
                response_time = str((end_time - start_time).total_seconds())
                response = create_agent_response(
                    message="Agent response",
                    teacherId=request.teacherId,
                    agentName="rag_agent",
                    agentResponse=agent_message,
                    sessionId=session_id,
                    responseTime=response_time,
                    role="agent"
                )
                return response
        return create_agent_response(
            message="No response generated",
            teacherId=request.teacherId,
            agentName="rag_agent",
            agentResponse="No response was generated from the agent",
            sessionId=session_id,
            role="agent"
        )
    except Exception as e:
        logger.exception(f"Agent error: {str(e)}")
        return create_agent_response(
            message=f"Agent error: {str(e)}",
            teacherId=getattr(request, 'teacherId', ''),
            agentName="rag_agent",
            agentResponse=f"An error occurred: {str(e)}",
            sessionId=session_id or '',
            role="agent"
        )
