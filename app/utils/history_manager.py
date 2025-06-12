from ..models.sqlite import get_db
from ..models.sqlite.models import UnalteredHistory, Role
from .content_summarizer import create_summary
from datetime import datetime
import logging
import time

async def add_to_history(message: str, role: str, user_id: str, session_id: str, app_name: str, session_service):
    from google.adk.events import Event, EventActions
    
    db_gen = get_db()     
    db = next(db_gen)     
    try:
        # adding the message to the database
        role = role.lower()
        db_message = UnalteredHistory(user_id= user_id, message = message, role=Role(role))
        db.add(db_message)
        db.commit()

        # adding the message to the session state using the proper ADK method
        session = session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
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
            session_service.append_event(session, system_event)

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
            session_service.append_event(session, system_event)

    finally:
        db_gen.close() 