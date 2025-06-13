import os
import requests
from typing import Dict, Any, Optional, List

# Configuration
GIN_BACKEND_URL = os.getenv("GIN_BACKEND_URL", "https://lumenslate-backend-756147067348.asia-south1.run.app")

def get_report_card_by_student_id(student_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch agent-generated report card data by student ID using direct HTTP request to GIN backend.
    
    Args:
        student_id: The unique identifier of the student
        
    Returns:
        List of agent report cards for the student if found, None otherwise
    """
    try:
        url = f"{GIN_BACKEND_URL}/agent-report-cards/student/{student_id}"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"No agent report cards found for student {student_id}")
            return None
        else:
            print(f"Error fetching agent report cards: HTTP {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"HTTP request error when fetching agent report cards for student {student_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error when fetching agent report cards for student {student_id}: {e}")
        return None
