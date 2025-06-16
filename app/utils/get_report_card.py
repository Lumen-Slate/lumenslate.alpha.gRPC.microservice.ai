import requests
import json
from typing import Dict, Any, Optional, List

def get_report_card_by_student_id(student_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch agent-generated report card data by student ID from the gin microservice.
    
    Args:
        student_id: The unique identifier of the student
        
    Returns:
        List of agent report cards for the student if found, None otherwise
    """
    try:
        # Make request to gin microservice for agent report cards
        response = requests.get(f"http://localhost:8080/api/agent-report-cards/student/{student_id}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("agent_report_cards"):
                return data["agent_report_cards"]
            return []
        else:
            print(f"Error fetching agent report cards for student {student_id}: {response.status_code} - {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"Request error when fetching agent report cards for student {student_id}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error when fetching agent report cards for student {student_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error when fetching agent report cards for student {student_id}: {e}")
        return None
