from typing import Any, Dict, List, Union
from ..models.sqlite import get_db
from ..models.sqlite.models import Questions, Difficulty
from .subject_handler import get_subject_enum
import json
import random

# Constants
AVAILABLE_SUBJECTS = ["Math", "Science", "English", "History", "Geography"]


def get_questions_general(questions_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Fetch questions from the database based on the agent's structured request.

    Args:
        questions_data: JSON string or dict containing list of question requests

    Returns:
        dict: Formatted response with questions organized by subject
    """
    try:
        parsed_data = _parse_questions_data(questions_data)
        questions_requested = parsed_data.get('questions_requested', [])
        if not questions_requested:
            return _error_response("No questions requested")
        db_gen = get_db()
        db = next(db_gen)
        try:
            response = _process_questions_requests(db, questions_requested)
        finally:
            db.close()
        return response
    except json.JSONDecodeError as e:
        return _error_response(f"Invalid JSON format: {str(e)}", agent_response="Error: Could not parse the question request. Please try again.")
    except Exception as e:
        return _error_response(f"Database error: {str(e)}", agent_response="Error: Could not retrieve questions from database. Please try again.")

def _parse_questions_data(questions_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(questions_data, str):
        return json.loads(questions_data)
    return questions_data

def _error_response(message: str, agent_response: str = "") -> Dict[str, Any]:
    return {
        "status": "error",
        "message": message,
        "agent_response": agent_response or message,
        "questions": []
    }

def _process_questions_requests(db, questions_requested: List[Dict[str, Any]]) -> Dict[str, Any]:
    subject_requests = _group_requests_by_subject(questions_requested)
    response_data = {
        "status": "success",
        "message": "Questions retrieved successfully",
        "total_subjects": len(subject_requests),
        "subjects": []
    }
    total_questions_returned = 0
    for _, subject_info in subject_requests.items():
        subject_enum = subject_info["subject_enum"]
        display_subject = subject_info["display_subject"]
        requests = subject_info["requests"]
        if not subject_enum:
            total_requested = sum(req["num_questions"] for req in requests)
            subject_data = {
                "subject": display_subject,
                "requested_count": total_requested,
                "available_count": 0,
                "returned_count": 0,
                "questions": [],
                "message": f"Subject '{display_subject}' is not supported. Available subjects: {', '.join(AVAILABLE_SUBJECTS)}"
            }
            response_data["subjects"].append(subject_data)
            continue
        all_questions_for_subject = []
        total_requested = 0
        for req in requests:
            num_questions = req["num_questions"]
            difficulty = req["difficulty"]
            total_requested += num_questions
            query = db.query(Questions).filter(Questions.subject == subject_enum)
            if difficulty:
                try:
                    difficulty_enum = Difficulty(difficulty.lower())
                    query = query.filter(Questions.difficulty == difficulty_enum)
                except ValueError:
                    pass
            available_questions = query.all()
            if not available_questions or num_questions > len(available_questions):
                continue
            selected_questions = random.sample(available_questions, num_questions)
            all_questions_for_subject.extend(selected_questions)
        if len(all_questions_for_subject) < total_requested:
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
            formatted_questions = [_format_question(q) for q in all_questions_for_subject]
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
    response_message = _format_response_message(response_data["subjects"], total_questions_returned)
    return {
        "status": "success",
        "agent_response": response_message,
        "data": response_data
    }

def _group_requests_by_subject(questions_requested: List[Dict[str, Any]]) -> Dict[str, Any]:
    subject_requests = {}
    for request in questions_requested:
        subject_string = request.get('subject')
        num_questions = request.get('number_of_questions', 10)
        difficulty = request.get('difficulty')
        subject_enum = get_subject_enum(subject_string)
        if not subject_enum:
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
            key = subject_enum.value
            if key not in subject_requests:
                subject_requests[key] = {
                    "subject_enum": subject_enum,
                    "display_subject": subject_string,
                    "requests": []
                }
            subject_requests[key]["requests"].append({
                "num_questions": num_questions,
                "difficulty": difficulty
            })
    return subject_requests

def _format_question(q: Questions) -> Dict[str, Any]:
    return {
        "question_id": q.question_id,
        "question": q.question,
        "options": json.loads(q.options),
        "answer": q.answer,
        "difficulty": q.difficulty.value
    }

def _format_response_message(subjects: List[Dict[str, Any]], total_questions_returned: int) -> str:
    response_message = f"**Assignment Questions Generated**\n\n"
    for subject_info in subjects:
        if subject_info['returned_count'] == 0 and 'message' in subject_info:
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
    return response_message 