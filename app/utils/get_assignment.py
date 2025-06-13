import os
import requests
from typing import Dict, Any, Optional

# Configuration
GIN_BACKEND_URL = os.getenv("GIN_BACKEND_URL", "https://lumenslate-backend-756147067348.asia-south1.run.app")

def get_assignment_by_id(assignment_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch assignment data by ID using direct HTTP request to GIN backend.
    
    Args:
        assignment_id: The unique identifier of the assignment
        
    Returns:
        Dictionary containing assignment data if found, None otherwise
    """
    try:
        url = f"{GIN_BACKEND_URL}/assignments/{assignment_id}"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"Assignment with ID {assignment_id} not found")
            return None
        else:
            print(f"Error fetching assignment: HTTP {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"HTTP request error when fetching assignment {assignment_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error when fetching assignment {assignment_id}: {e}")
        return None
