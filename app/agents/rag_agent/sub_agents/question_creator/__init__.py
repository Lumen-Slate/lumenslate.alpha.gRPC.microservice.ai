import os
import vertexai
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Get config from environment
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

# Let ADC handle credentials loading (via GOOGLE_APPLICATION_CREDENTIALS)
try:
    if PROJECT_ID and LOCATION:
        print(f"Initializing Vertex AI with ADC - project={PROJECT_ID}, location={LOCATION}")
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        print("✅ Vertex AI initialized using ADC")
    else:
        print(
            f"❌ Missing config. PROJECT_ID={PROJECT_ID}, LOCATION={LOCATION}. "
            "Vertex AI may not work properly."
        )
except Exception as e:
    print(f"❌ Failed to initialize Vertex AI: {str(e)}")
    print("Please verify GOOGLE_APPLICATION_CREDENTIALS and GCP setup.")

# Import agent after successful init
from . import agent
