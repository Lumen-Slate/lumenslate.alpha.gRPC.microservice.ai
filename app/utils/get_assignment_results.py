import requests
import json
from typing import Dict, Any, Optional, List

def get_assignment_results_by_student_id(student_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch assignment results data by student ID from the gin microservice.
    
    Args:
        student_id: The unique identifier of the student
        
    Returns:
        List of assignment results for the student if found, None otherwise
    """
    try:
        # Make request to gin microservice with studentId filter
        response = requests.get(f"http://localhost:8080/api/assignment-results?studentId={student_id}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                return data["data"]
            return []
        else:
            print(f"Error fetching assignment results for student {student_id}: {response.status_code} - {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"Request error when fetching assignment results for student {student_id}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error when fetching assignment results for student {student_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error when fetching assignment results for student {student_id}: {e}")
        return None
