from ..models.sqlite import get_db
from ..models.sqlite.models import UnalteredHistory, Role
from app.agents.independent_agents.summarizer.summarizer import create_summary
from datetime import datetime
import time
from google.adk.events import Event, EventActions
from app.config.logging_config import logger

async def add_to_history(
    message: str,
    role: str,
    teacherId: str,
    sessionId: str,
    app_name: str,
    session_service
) -> None:
    """
    Add a message to the conversation history (Primary Agent - uses PostgreSQL)
    """
    db_session = None
    try:
        db_session = next(get_db())
        _add_message_to_db(db_session, teacherId, message, role)
        await _add_message_to_session_service(session_service, app_name, teacherId, sessionId, message, role)
    except Exception as e:
        if db_session:
            db_session.rollback()
        logger.error(f"Error adding to history: {e}")
        raise e
    finally:
        if db_session:
            db_session.close()


def _add_message_to_db(db_session, teacherId: str, message: str, role: str) -> None:
    db_message = UnalteredHistory(teacherId=teacherId, message=message, role=Role(role))
    db_session.add(db_message)
    db_session.commit()

async def _add_message_to_session_service(session_service, app_name: str, teacherId: str, sessionId: str, message: str, role: str) -> None:
    db_message = UnalteredHistory(teacherId=teacherId, message=message, role=Role(role))
    await session_service.append_to_history(
        message=db_message,
        app_name=app_name, 
        teacherId=teacherId, 
        sessionId=sessionId
    )
    session = await session_service.get_session(
        app_name=app_name, teacherId=teacherId, sessionId=sessionId
    )
    message_history = session.state.get("message_history", [])
    if len(message_history) > 11:
        await _summarize_and_update_history(session_service, session, message_history, message, role)
    else:
        await _append_latest_message(session_service, session, message_history, message, role)
    # Convert role to proper Event type if needed
    await _append_role_event(session_service, session, message, role)

async def _summarize_and_update_history(session_service, session, message_history, message, role):
    older_message_history = message_history[:8]
    newer_message_history = message_history[8:]
    summary = create_summary(older_message_history)
    if not summary:
        summary = "No summary available for messages prior to the latest ones."
    summary_message = {
        "role": "prior_messages_summary",
        "message": f"""
                The following message is a summary of the entire prior conversation, before the newest messages.
                {summary}
                """
    }
    final_message_history = [summary_message] + newer_message_history
    latest_message = {
        "role": role,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    final_message_history.append(latest_message)
    state_changes = {"message_history": final_message_history}
    actions_with_update = EventActions(state_delta=state_changes)
    system_event = Event(
        invocation_id=f"history_update_{int(time.time() * 1000)}",
        author="root_agent",
        actions=actions_with_update,
        timestamp=time.time()
    )
    await session_service.append_event(session, system_event)

async def _append_latest_message(session_service, session, message_history, message, role):
    latest_message = {
        "role": role,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    message_history.append(latest_message)
    state_changes = {"message_history": message_history}
    actions_with_update = EventActions(state_delta=state_changes)
    system_event = Event(
        invocation_id=f"history_update_{int(time.time() * 1000)}",
        author="root_agent",
        actions=actions_with_update,
        timestamp=time.time()
    )
    await session_service.append_event(session, system_event)

async def _append_role_event(session_service, session, message, role):
    if role == "user":
        user_event = Event(actions=[EventActions.USER_MESSAGE], content=message)
        await session_service.append_event(session, user_event)
    elif role == "agent":
        system_event = Event(actions=[EventActions.SYSTEM_MESSAGE], content=message)
        await session_service.append_event(session, system_event)

 