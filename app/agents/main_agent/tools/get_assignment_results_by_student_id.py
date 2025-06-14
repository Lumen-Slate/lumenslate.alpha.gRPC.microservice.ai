import os
import pymongo
from typing import Dict, Any, Optional, List
from bson import ObjectId

def get_assignment_results_by_student_id(student_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch assignment results data by student ID using direct MongoDB connection.
    
    Args:
        student_id: The unique identifier of the student
        
    Returns:
        List of assignment results for the student if found, None otherwise
    """
    try:
        # Get MongoDB URI from environment
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print("MONGO_URI environment variable not set")
            return None
        
        # Connect to MongoDB
        client = pymongo.MongoClient(mongo_uri)
        db = client["lumen_slate"]
        collection = db["assignment_results"]
        
        # Query assignment results by student ID, sorted by creation date (newest first)
        cursor = collection.find({"studentId": student_id}).sort("createdAt", -1)
        
        results = []
        for result in cursor:
            # Convert ObjectId to string for JSON serialization
            if "_id" in result:
                result["id"] = str(result["_id"])
                del result["_id"]
            results.append(result)
        
        if results:
            return results
        else:
            print(f"No assignment results found for student {student_id}")
            return None
            
    except Exception as e:
        print(f"Error fetching assignment results for student {student_id}: {e}")
        return None
    finally:
        try:
            client.close()
        except:
            pass 