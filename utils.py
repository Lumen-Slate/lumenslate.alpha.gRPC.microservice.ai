from models.sqlite import get_db
from models.sqlite.models import UnalteredHistory, Role, Questions, Difficulty, Subject
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

def get_subject_enum(subject_string):
    """Convert subject string to Subject enum, handling various formats"""
    subject_mapping = {
        'math': Subject.MATH,
        'mathematics': Subject.MATH,
        'maths': Subject.MATH,
        'science': Subject.SCIENCE,
        'biology': Subject.SCIENCE,
        'chemistry': Subject.SCIENCE,
        'physics': Subject.SCIENCE,
        'english': Subject.ENGLISH,
        'language arts': Subject.ENGLISH,
        'literature': Subject.ENGLISH,
        'reading': Subject.ENGLISH,
        'history': Subject.HISTORY,
        'social studies': Subject.HISTORY,
        'world history': Subject.HISTORY,
        'geography': Subject.GEOGRAPHY,
        'geo': Subject.GEOGRAPHY
    }
    
    normalized_subject = subject_string.lower().strip()
    return subject_mapping.get(normalized_subject, None)

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
            # Grouping requests by subject to handle multiple difficulty levels for the same subject
            subject_requests = {}
            
            for request in questions_requested:
                subject_string = request.get('subject')
                num_questions = request.get('number_of_questions', 10)
                difficulty = request.get('difficulty')
                
                # Converting subject string to Subject enum
                subject_enum = get_subject_enum(subject_string)
                
                if not subject_enum:
                    # Keeping invalid subjects for error reporting
                    if subject_string not in subject_requests:
                        subject_requests[subject_string] = {
                            "subject_enum": None,
                            "display_subject": subject_string,
                            "requests": []
                        }
                    subject_requests[subject_string]["requests"].append({
                        "num_questions": num_questions,
                        "difficulty": difficulty
                    })
                else:
                    # Using subject enum value as key to group same subjects
                    key = subject_enum.value
                    if key not in subject_requests:
                        subject_requests[key] = {
                            "subject_enum": subject_enum,
                            "display_subject": subject_string,  # Using first occurrence for display
                            "requests": []
                        }
                    subject_requests[key]["requests"].append({
                        "num_questions": num_questions,
                        "difficulty": difficulty
                    })
            
            response_data = {
                "status": "success",
                "message": "Questions retrieved successfully",
                "total_subjects": len(subject_requests),
                "subjects": []
            }
            
            total_questions_returned = 0
            
            for subject_key, subject_info in subject_requests.items():
                subject_enum = subject_info["subject_enum"]
                display_subject = subject_info["display_subject"]
                requests = subject_info["requests"]
                
                if not subject_enum:
                    # Invalid subject
                    total_requested = sum(req["num_questions"] for req in requests)
                    subject_data = {
                        "subject": display_subject,
                        "requested_count": total_requested,
                        "available_count": 0,
                        "returned_count": 0,
                        "questions": [],
                        "message": f"Subject '{display_subject}' is not supported. Available subjects: Math, Science, English, History, Geography"
                    }
                    response_data["subjects"].append(subject_data)
                    continue
                
                # Processing all requests for this subject
                all_questions_for_subject = []
                total_requested = 0
                
                for req in requests:
                    num_questions = req["num_questions"]
                    difficulty = req["difficulty"]
                    total_requested += num_questions
                    
                    # Querying database for questions from this subject with specific difficulty
                    query = db.query(Questions).filter(Questions.subject == subject_enum)
                    
                    # Adding difficulty filter if specified
                    if difficulty:
                        try:
                            difficulty_enum = Difficulty(difficulty.lower())
                            query = query.filter(Questions.difficulty == difficulty_enum)
                        except ValueError:
                            # Invalid difficulty value, ignore filter
                            pass
                    
                    available_questions = query.all()
                    
                    if not available_questions:
                        # No questions available for this difficulty
                        continue
                    elif num_questions > len(available_questions):
                        # Not enough questions for this difficulty, skip this request
                        continue
                    else:
                        # Randomly sampling the requested number of questions
                        selected_questions = random.sample(available_questions, num_questions)
                        all_questions_for_subject.extend(selected_questions)
                
                # Checking if we got all requested questions
                if len(all_questions_for_subject) < total_requested:
                    # Getting total available questions for this subject (any difficulty)
                    total_available = db.query(Questions).filter(Questions.subject == subject_enum).count()
                    
                    subject_data = {
                        "subject": display_subject,
                        "requested_count": total_requested,
                        "available_count": total_available,
                        "returned_count": 0,
                        "questions": [],
                        "message": f"Could not fulfill all requests for {display_subject}. Some difficulty levels may not have enough questions available."
                    }
                elif not all_questions_for_subject:
                    # No questions available for this subject
                    total_available = db.query(Questions).filter(Questions.subject == subject_enum).count()
                    subject_data = {
                        "subject": display_subject,
                        "requested_count": total_requested,
                        "available_count": total_available,
                        "returned_count": 0,
                        "questions": [],
                        "message": f"No questions available for {display_subject} with the requested difficulty levels"
                    }
                else:
                    # Successfully got all requested questions
                    # Formatting questions for response
                    formatted_questions = []
                    for q in all_questions_for_subject:
                        formatted_questions.append({
                            "question_id": q.question_id,
                            "question": q.question,
                            "options": json.loads(q.options),
                            "answer": q.answer,
                            "difficulty": q.difficulty.value
                        })
                    
                    # Getting total available questions for this subject
                    total_available = db.query(Questions).filter(Questions.subject == subject_enum).count()
                    
                    subject_data = {
                        "subject": display_subject,
                        "requested_count": total_requested,
                        "available_count": total_available,
                        "returned_count": len(formatted_questions),
                        "questions": formatted_questions
                    }
                    
                    total_questions_returned += len(formatted_questions)
                
                response_data["subjects"].append(subject_data)
            
            response_data["total_questions_returned"] = total_questions_returned
            
            # Formatting as a readable response
            response_message = f"**Assignment Questions Generated**\n\n"
            
            for subject_info in response_data["subjects"]:
                if subject_info['returned_count'] == 0 and 'message' in subject_info:
                    # Handling case where no questions were returned due to error/insufficient questions
                    response_message += f"**{subject_info['subject']}**: {subject_info['message']}\n"
                else:
                    response_message += f"**{subject_info['subject']}** ({subject_info['returned_count']} questions):\n"
                    
                    for i, question in enumerate(subject_info['questions'], 1):
                        response_message += f"\n{i}. {question['question']} *({question['difficulty']})*\n"
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


