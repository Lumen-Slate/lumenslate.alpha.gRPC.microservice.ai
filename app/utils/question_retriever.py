from ..models.sqlite import get_db
from ..models.sqlite.models import Questions, Difficulty
from .subject_handler import get_subject_enum
import json
import random

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