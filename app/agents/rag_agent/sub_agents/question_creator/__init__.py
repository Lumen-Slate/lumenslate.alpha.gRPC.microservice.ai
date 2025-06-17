import os
import vertexai
from dotenv import load_dotenv
from app.utils.auth_helper import setup_google_auth, get_project_id

# Load env vars
load_dotenv()

# Setup authentication first
auth_success = setup_google_auth()

# Get config from environment
PROJECT_ID = get_project_id() or os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Initialize Vertex AI
try:
    if PROJECT_ID and LOCATION and auth_success:
        print(f"Initializing Vertex AI - project={PROJECT_ID}, location={LOCATION}")
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        print("✅ Vertex AI initialized successfully")
    else:
        missing_items = []
        if not PROJECT_ID:
            missing_items.append("PROJECT_ID")
        if not LOCATION:
            missing_items.append("LOCATION")
        if not auth_success:
            missing_items.append("authentication")
        print(f"❌ Missing: {', '.join(missing_items)}. Vertex AI may not work properly.")
except Exception as e:
    print(f"❌ Failed to initialize Vertex AI: {str(e)}")
    print("For deployed environments, ensure the service has proper IAM permissions.")

# Import agent after successful init
from . import agent
