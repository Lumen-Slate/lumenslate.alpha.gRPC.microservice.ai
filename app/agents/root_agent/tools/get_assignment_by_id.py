import os
import pymongo
from typing import Dict, Any, Optional
from bson import ObjectId

def get_assignment_by_id(assignment_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch assignment data by ID using direct MongoDB connection.
    
    Args:
        assignment_id: The unique identifier of the assignment
        
    Returns:
        Dictionary containing assignment data if found, None otherwise
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
        collection = db["assignments"]
        
        # Query the assignment by ID
        assignment = collection.find_one({"_id": assignment_id})
        
        if assignment:
            # Convert ObjectId fields to strings for JSON serialization
            if "_id" in assignment:
                assignment["id"] = assignment["_id"]
                del assignment["_id"]
            return assignment
        else:
            print(f"Assignment with ID {assignment_id} not found")
            return None
            
    except Exception as e:
        print(f"Error fetching assignment {assignment_id}: {e}")
        return None
    finally:
        try:
            client.close()
        except:
            pass 