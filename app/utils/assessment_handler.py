from ..models.sqlite import get_db
from ..models.sqlite.models import SubjectReport, Subject
from .subject_handler import get_subject_enum
from datetime import datetime, timezone
import json

def save_subject_report(assessment_data):
    """
    Save assessment data to the SubjectReport table in the database.
    
    Args:
        assessment_data: JSON object containing assessment information from the assessor agent
        
    Returns:
        dict: Formatted response with success/error status and data
    """
    try:
        # Parsing the JSON data if it's a string
        if isinstance(assessment_data, str):
            parsed_data = json.loads(assessment_data)
        else:
            parsed_data = assessment_data
        
        # Extracting the assessment_data field (the actual data from assessor agent)
        report_data = parsed_data.get('assessment_data', {})
        
        if not report_data:
            return {
                "status": "error",
                "message": "No assessment data provided",
                "agent_response": "Error: No assessment data found in the input."
            }
        
        # Checking for mandatory fields
        mandatory_fields = ['user_id', 'student_id', 'student_name', 'subject', 'score']
        missing_fields = []
        
        for field in mandatory_fields:
            if not report_data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return {
                "status": "error",
                "message": f"Missing mandatory fields: {', '.join(missing_fields)}",
                "agent_response": f"Error: Cannot create subject report. Missing required information: {', '.join(missing_fields)}. Please provide these details to generate the report."
            }
        
        # Validating and converting subject to enum
        subject_string = report_data.get('subject')
        subject_enum = get_subject_enum(subject_string)
        
        if not subject_enum:
            return {
                "status": "error",
                "message": f"Invalid subject: {subject_string}",
                "agent_response": f"Error: '{subject_string}' is not a valid subject. Available subjects are: math, science, english, history, geography."
            }
        
        # Getting database connection
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Creating SubjectReport object with all available data
            subject_report = SubjectReport(
                user_id=report_data['user_id'],
                student_id=report_data['student_id'],
                student_name=report_data['student_name'],
                subject=subject_enum,
                score=int(report_data['score']),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Adding optional fields if they exist and are not None
            optional_string_fields = [
                'grade_letter', 'class_name', 'instructor_name', 'term', 'remarks',
                'learning_objectives_mastered', 'areas_for_improvement', 
                'recommended_resources', 'target_goals'
            ]
            
            optional_int_fields = [
                'midterm_score', 'final_exam_score', 'quiz_score', 
                'assignment_score', 'practical_score', 'oral_presentation_score'
            ]
            
            optional_float_fields = [
                'conceptual_understanding', 'problem_solving', 'knowledge_application',
                'analytical_thinking', 'creativity', 'practical_skills',
                'participation', 'discipline', 'punctuality', 'teamwork',
                'effort_level', 'improvement'
            ]
            
            # Setting optional string fields
            for field in optional_string_fields:
                value = report_data.get(field)
                if value is not None and value.strip():  # Not None and not empty string
                    setattr(subject_report, field, value.strip())
            
            # Setting optional integer fields
            for field in optional_int_fields:
                value = report_data.get(field)
                if value is not None:
                    try:
                        setattr(subject_report, field, int(value))
                    except (ValueError, TypeError):
                        pass  # Skipping invalid integer values
            
            # Setting optional float fields
            for field in optional_float_fields:
                value = report_data.get(field)
                if value is not None:
                    try:
                        setattr(subject_report, field, float(value))
                    except (ValueError, TypeError):
                        pass  # Skipping invalid float values
            
            # Saving to database
            db.add(subject_report)
            db.commit()
            db.refresh(subject_report)
            
            # Preparing response data
            saved_data = {
                "report_id": subject_report.report_id,
                "user_id": subject_report.user_id,
                "student_id": subject_report.student_id,
                "student_name": subject_report.student_name,
                "subject": subject_report.subject.value,
                "score": subject_report.score,
                "timestamp": subject_report.timestamp.isoformat()
            }
            
            # Adding non-null optional fields to response
            all_optional_fields = optional_string_fields + optional_int_fields + optional_float_fields
            for field in all_optional_fields:
                value = getattr(subject_report, field, None)
                if value is not None:
                    saved_data[field] = value
            
            # Formatting success message
            response_message = f"**Subject Report Created Successfully**\n\n"
            response_message += f"**Student:** {subject_report.student_name} (ID: {subject_report.student_id})\n"
            response_message += f"**Subject:** {subject_report.subject.value.title()}\n"
            response_message += f"**Overall Score:** {subject_report.score}/100\n"
            
            if subject_report.grade_letter:
                response_message += f"**Grade:** {subject_report.grade_letter}\n"
            
            if subject_report.class_name:
                response_message += f"**Class:** {subject_report.class_name}\n"
            
            if subject_report.instructor_name:
                response_message += f"**Instructor:** {subject_report.instructor_name}\n"
            
            if subject_report.term:
                response_message += f"**Term:** {subject_report.term}\n"
            
            # Adding assessment breakdown if available
            assessment_scores = []
            if subject_report.midterm_score is not None:
                assessment_scores.append(f"Midterm: {subject_report.midterm_score}")
            if subject_report.final_exam_score is not None:
                assessment_scores.append(f"Final: {subject_report.final_exam_score}")
            if subject_report.quiz_score is not None:
                assessment_scores.append(f"Quiz: {subject_report.quiz_score}")
            if subject_report.assignment_score is not None:
                assessment_scores.append(f"Assignments: {subject_report.assignment_score}")
            
            if assessment_scores:
                response_message += f"\n**Assessment Breakdown:** {', '.join(assessment_scores)}\n"
            
            # Adding skill evaluations if available
            skills = []
            if subject_report.conceptual_understanding is not None:
                skills.append(f"Conceptual Understanding: {subject_report.conceptual_understanding}")
            if subject_report.problem_solving is not None:
                skills.append(f"Problem Solving: {subject_report.problem_solving}")
            if subject_report.analytical_thinking is not None:
                skills.append(f"Analytical Thinking: {subject_report.analytical_thinking}")
            
            if skills:
                response_message += f"\n**Key Skills:** {', '.join(skills)}\n"
            
            if subject_report.remarks:
                response_message += f"\n**Remarks:** {subject_report.remarks}\n"
            
            if subject_report.areas_for_improvement:
                response_message += f"\n**Areas for Improvement:** {subject_report.areas_for_improvement}\n"
            
            response_message += f"\n**Report ID:** {subject_report.report_id}"
            response_message += f"\n**Created:** {subject_report.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            
            return {
                "status": "success",
                "agent_response": response_message,
                "data": {
                    "report_created": True,
                    "report_data": saved_data
                }
            }
            
        finally:
            db.close()
            
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}",
            "agent_response": "Error: Could not parse the assessment data. Please try again."
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database error: {str(e)}",
            "agent_response": "Error: Could not save the subject report to database. Please try again."
        } 