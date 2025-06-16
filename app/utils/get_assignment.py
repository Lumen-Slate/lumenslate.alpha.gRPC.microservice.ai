import requests
import json
from typing import Dict, Any, Optional

def get_assignment_by_id(assignment_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch assignment data by ID from the gin microservice.
    
    Args:
        assignment_id: The unique identifier of the assignment
        
    Returns:
        Dictionary containing assignment data if found, None otherwise
    """
    try:
        # Make request to gin microservice
        response = requests.get(f"http://localhost:8080/assignments/{assignment_id}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                return data["data"]
            return None
        elif response.status_code == 404:
            print(f"Assignment with ID {assignment_id} not found")
            return None
        else:
            print(f"Error fetching assignment: {response.status_code} - {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"Request error when fetching assignment {assignment_id}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error when fetching assignment {assignment_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error when fetching assignment {assignment_id}: {e}")
        return None
