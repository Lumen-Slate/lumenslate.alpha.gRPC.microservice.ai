from models.sqlite import get_db
from models.sqlite.models import UnalteredHistory, Role, Questions
from datetime import datetime
import logging
import os
import google.generativeai as genai
import time
import json
import random
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def create_summary(messages):
    input = f"""
    You are a helpful assistant that summarizes conversations.
    Please summarize the following messages in a concise manner, focusing on the main points and key information.
    Here are the messages:

    {messages}

    Please provide a summary that captures the essence of the conversation without losing important details.
    Do NOT say anything else or extra, just provide the summary.
    The summary should be in a single paragraph and should not exceed 100 words.
    """
    response = model.generate_content(input)
    return response.text.strip() if response and response.text else None

def get_questions_general(questions_data):
    """
    Fetch questions from the database based on the agent's structured request.
    
    Args:
        questions_data: JSON object containing list of question requests
        
    Returns:
        dict: Formatted response with questions organized by subject
    """
    try:
        # Parsing the JSON data
        if isinstance(questions_data, str):
            parsed_data = json.loads(questions_data)
        else:
            parsed_data = questions_data
        
        # Getting the questions_requested list
        questions_requested = parsed_data.get('questions_requested', [])
        
        if not questions_requested:
            return {
                "status": "error",
                "message": "No questions requested",
                "questions": []
            }
        
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            response_data = {
                "status": "success",
                "message": "Questions retrieved successfully",
                "total_subjects": len(questions_requested),
                "subjects": []
            }
            
            total_questions_returned = 0
            
            for request in questions_requested:
                subject = request.get('subject')
                num_questions = request.get('number_of_questions', 10)
                request_type = request.get('type')
                
                # Querying database for questions from this subject
                available_questions = db.query(Questions).filter(
                    Questions.subject == subject
                ).all()
                
                if not available_questions:
                    # If no questions available for this subject
                    subject_data = {
                        "subject": subject,
                        "requested_count": num_questions,
                        "available_count": 0,
                        "returned_count": 0,
                        "questions": [],
                        "message": f"No questions available for {subject}"
                    }
                else:
                    # Randomly sampling the requested number of questions
                    selected_questions = random.sample(
                        available_questions, 
                        min(num_questions, len(available_questions))
                    )
                    
                    # Formatting questions for response
                    formatted_questions = []
                    for q in selected_questions:
                        formatted_questions.append({
                            "question_id": q.question_id,
                            "question": q.question,
                            "options": json.loads(q.options),
                            "answer": q.answer
                        })
                    
                    subject_data = {
                        "subject": subject,
                        "requested_count": num_questions,
                        "available_count": len(available_questions),
                        "returned_count": len(formatted_questions),
                        "questions": formatted_questions
                    }
                    
                    total_questions_returned += len(formatted_questions)
                
                response_data["subjects"].append(subject_data)
            
            response_data["total_questions_returned"] = total_questions_returned
            
            # Formatting as a readable response
            response_message = f"**Assignment Questions Generated**\n\n"
            
            for subject_info in response_data["subjects"]:
                response_message += f"**{subject_info['subject']}** ({subject_info['returned_count']} questions):\n"
                
                for i, question in enumerate(subject_info['questions'], 1):
                    response_message += f"\n{i}. {question['question']}\n"
                    for j, option in enumerate(question['options'], 1):
                        response_message += f"   {chr(96+j)}) {option}\n"
                    response_message += f"   **Answer:** {question['answer']}\n"
                
                response_message += "\n" + "="*50 + "\n"
            
            response_message += f"\n**Total Questions Provided:** {total_questions_returned}"
            
            return {
                "status": "success",
                "agent_response": response_message,
                "data": response_data
            }
            
        finally:
            db.close()
            
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}",
            "agent_response": "Error: Could not parse the question request. Please try again."
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database error: {str(e)}",
            "agent_response": "Error: Could not retrieve questions from database. Please try again."
        }

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


