import requests
import json
from typing import Dict, List, Any
from config.logging_config import logger
import os

def get_subject_reports_by_student_id(student_id: int) -> Dict[str, Any]:
    """
    Tool function to fetch all subject reports for a given student_id from the Go backend.
    
    Args:
        student_id (int): The student ID to fetch reports for
        
    Returns:
        Dict[str, Any]: Dictionary containing the fetched subject reports
    """
    try:
        # Get the Go backend URL from environment variables
        go_backend_url = os.getenv("GO_BACKEND_URL", "http://localhost:8080")
        
        # Make API call to Go backend to fetch subject reports
        url = f"{go_backend_url}/api/subject-reports"
        params = {"studentId": str(student_id)}
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Format the response for the agent
            if data and "data" in data and isinstance(data["data"], list):
                subject_reports = data["data"]
                
                return {
                    "status": "success",
                    "student_id": student_id,
                    "total_reports": len(subject_reports),
                    "subject_reports": subject_reports,
                    "message": f"Successfully fetched {len(subject_reports)} subject reports for student {student_id}"
                }
            else:
                return {
                    "status": "success",
                    "student_id": student_id,
                    "total_reports": 0,
                    "subject_reports": [],
                    "message": f"No subject reports found for student {student_id}"
                }
                
        else:
            logger.error(f"Failed to fetch subject reports: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "student_id": student_id,
                "total_reports": 0,
                "subject_reports": [],
                "message": f"Failed to fetch subject reports: {response.status_code}"
            }
            
    except requests.RequestException as e:
        logger.error(f"Network error while fetching subject reports: {str(e)}")
        return {
            "status": "error",
            "student_id": student_id,
            "total_reports": 0,
            "subject_reports": [],
            "message": f"Network error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error while fetching subject reports: {str(e)}")
        return {
            "status": "error",
            "student_id": student_id,
            "total_reports": 0,
            "subject_reports": [],
            "message": f"Unexpected error: {str(e)}"
        } 


def get_report_cards_by_student_id(student_id: int) -> Dict[str, Any]:
    """
    Tool function to fetch all report cards for a given student_id from the Go backend.
    This is what assignment_generator_tailored should use (not subject reports).
    
    Args:
        student_id (int): The student ID to fetch report cards for
        
    Returns:
        Dict[str, Any]: Dictionary containing the fetched report cards
    """
    try:
        # Get the Go backend URL from environment variables
        go_backend_url = os.getenv("GO_BACKEND_URL", "http://localhost:8080")
        
        # Make API call to Go backend to fetch report cards
        url = f"{go_backend_url}/api/report-cards"
        params = {"studentId": str(student_id)}
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Format the response for the agent
            if data and "data" in data and isinstance(data["data"], list):
                report_cards = data["data"]
                
                return {
                    "status": "success",
                    "student_id": student_id,
                    "total_report_cards": len(report_cards),
                    "report_cards": report_cards,
                    "message": f"Successfully fetched {len(report_cards)} report cards for student {student_id}"
                }
            else:
                return {
                    "status": "success",
                    "student_id": student_id,
                    "total_report_cards": 0,
                    "report_cards": [],
                    "message": f"No report cards found for student {student_id}"
                }
                
        else:
            logger.error(f"Failed to fetch report cards: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "student_id": student_id,
                "total_report_cards": 0,
                "report_cards": [],
                "message": f"Failed to fetch report cards: {response.status_code}"
            }
            
    except requests.RequestException as e:
        logger.error(f"Network error while fetching report cards: {str(e)}")
        return {
            "status": "error",
            "student_id": student_id,
            "total_report_cards": 0,
            "report_cards": [],
            "message": f"Network error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error while fetching report cards: {str(e)}")
        return {
            "status": "error",
            "student_id": student_id,
            "total_report_cards": 0,
            "report_cards": [],
            "message": f"Unexpected error: {str(e)}"
        } 