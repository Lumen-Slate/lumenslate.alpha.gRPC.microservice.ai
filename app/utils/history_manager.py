from ..models.sqlite import get_db, get_rag_db
from ..models.sqlite.models import UnalteredHistory, Role
from .content_summarizer import create_summary
from datetime import datetime
import logging
import time
from google.adk.sessions import DatabaseSessionService
from google.adk.events import Event, EventActions

async def add_to_history(message: str, role: str, teacherId: str, sessionId: str, app_name: str, session_service):
    """
    Add a message to the conversation history (Primary Agent - uses PostgreSQL)
    """
    db_session = None
    try:
        # Add to database
        db_session = next(get_db())
        db_message = UnalteredHistory(teacherId=teacherId, message=message, role=Role(role))
        db_session.add(db_message)
        db_session.commit()
        
        # Add to session service
        await session_service.append_to_history(
            message=db_message,
            app_name=app_name, 
            teacherId=teacherId, 
            sessionId=sessionId
        )

        # adding the message to the session state using the proper ADK method
        session = await session_service.get_session(
            app_name=app_name, teacherId=teacherId, sessionId=sessionId
        )

        message_history = session.state.get("message_history", [])

        if len(message_history) > 11:
            older_message_history = message_history[:8]
            newer_message_history = message_history[8:]

            summary = create_summary(older_message_history)

            if not summary:
                logging.warning("No summary created for older_message_history.")
                summary = "No summary available for messages prior to the latest ones."

            logging.info(f"Created summary of older_message_history: {summary}")

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

            logging.info(f"Adding message to history: {final_message_history}")

            # Updating session state using the ADK event system
            state_changes = {"message_history": final_message_history}
            actions_with_update = EventActions(state_delta=state_changes)
            system_event = Event(
                invocation_id=f"history_update_{int(time.time() * 1000)}",
                author="root_agent",
                actions=actions_with_update,
                timestamp=time.time()
            )
            await session_service.append_event(session, system_event)

        else:
            latest_message = {
                "role": role,
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            message_history.append(latest_message)

            logging.info(f"Adding message to history:\n{latest_message}")

            # Updating session state using the proper ADK event system
            state_changes = {"message_history": message_history}
            actions_with_update = EventActions(state_delta=state_changes)
            system_event = Event(
                invocation_id=f"history_update_{int(time.time() * 1000)}",
                author="root_agent",
                actions=actions_with_update,
                timestamp=time.time()
            )
            await session_service.append_event(session, system_event)

        # Convert role to proper Event type if needed
        if role == "user":
            user_event = Event(actions=[EventActions.USER_MESSAGE], content=message)
            await session_service.append_event(session, user_event)
        elif role == "agent":
            system_event = Event(actions=[EventActions.SYSTEM_MESSAGE], content=message)
            await session_service.append_event(session, system_event)

    except Exception as e:
        if db_session:
            db_session.rollback()
        print(f"Error adding to history: {e}")
        raise e
    finally:
        if db_session:
            db_session.close()

async def add_to_rag_history(message: str, role: str, teacherId: str, sessionId: str, app_name: str, session_service):
    """
    Add a message to the conversation history (RAG Agent - uses RAG_DATABASE_URL)
    """
    db_session = None
    try:
        # Add to RAG database
        db_session = next(get_rag_db())
        db_message = UnalteredHistory(teacherId=teacherId, message=message, role=Role(role))
        db_session.add(db_message)
        db_session.commit()
        
        # Add to session service
        await session_service.append_to_history(
            message=db_message,
            app_name=app_name, 
            teacherId=teacherId, 
            sessionId=sessionId
        )

        # adding the message to the session state using the proper ADK method
        session = await session_service.get_session(
            app_name=app_name, teacherId=teacherId, sessionId=sessionId
        )

        message_history = session.state.get("message_history", [])

        if len(message_history) > 11:
            older_message_history = message_history[:8]
            newer_message_history = message_history[8:]

            summary = create_summary(older_message_history)

            if not summary:
                logging.warning("No summary created for older_message_history.")
                summary = "No summary available for messages prior to the latest ones."

            logging.info(f"Created summary of older_message_history: {summary}")

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

            logging.info(f"Adding message to RAG history: {final_message_history}")

            # Updating session state using the ADK event system
            state_changes = {"message_history": final_message_history}
            actions_with_update = EventActions(state_delta=state_changes)
            system_event = Event(
                invocation_id=f"history_update_{int(time.time() * 1000)}",
                author="rag_agent",
                actions=actions_with_update,
                timestamp=time.time()
            )
            await session_service.append_event(session, system_event)

        else:
            latest_message = {
                "role": role,
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            message_history.append(latest_message)

            logging.info(f"Adding message to RAG history:\n{latest_message}")

            # Updating session state using the proper ADK event system
            state_changes = {"message_history": message_history}
            actions_with_update = EventActions(state_delta=state_changes)
            system_event = Event(
                invocation_id=f"history_update_{int(time.time() * 1000)}",
                author="rag_agent",
                actions=actions_with_update,
                timestamp=time.time()
            )
            await session_service.append_event(session, system_event)

        # Convert role to proper Event type if needed
        if role == "user":
            user_event = Event(actions=[EventActions.USER_MESSAGE], content=message)
            await session_service.append_event(session, user_event)
        elif role == "agent":
            system_event = Event(actions=[EventActions.SYSTEM_MESSAGE], content=message)
            await session_service.append_event(session, system_event)

    except Exception as e:
        if db_session:
            db_session.rollback()
        print(f"Error adding to RAG history: {e}")
        raise e
    finally:
        if db_session:
            db_session.close() 