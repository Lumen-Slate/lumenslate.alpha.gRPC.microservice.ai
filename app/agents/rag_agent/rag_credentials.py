import os
import vertexai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

# Initialize Vertex AI using ADC
try:
    if PROJECT_ID and LOCATION:
        print(f"Initializing Vertex AI with ADC - project={PROJECT_ID}, location={LOCATION}")
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        print("✅ Vertex AI initialized using ADC")
    else:
        print(f"❌ Missing PROJECT_ID or LOCATION. Check your .env settings.")
except Exception as e:
    print(f"❌ Failed to initialize Vertex AI: {e}")
