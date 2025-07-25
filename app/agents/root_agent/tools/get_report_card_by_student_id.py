import os
import pymongo
from typing import Dict, Any, Optional, List
from bson import ObjectId

def get_report_card_by_student_id(student_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch agent-generated report card data by student ID using direct MongoDB connection.
    
    Args:
        student_id: The unique identifier of the student
        
    Returns:
        List of agent report cards for the student if found, None otherwise
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
        collection = db["agent_report_cards"]
        
        # Query agent report cards by student ID, sorted by creation date (newest first)
        cursor = collection.find({"reportCard.studentId": student_id}).sort("createdAt", -1)
        
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
            print(f"No agent report cards found for student {student_id}")
            return None
            
    except Exception as e:
        print(f"Error fetching agent report cards for student {student_id}: {e}")
        return None
    finally:
        try:
            client.close()
        except:
            pass 