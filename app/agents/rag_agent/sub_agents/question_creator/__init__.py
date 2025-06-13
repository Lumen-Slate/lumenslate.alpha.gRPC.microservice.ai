import os
import vertexai
from dotenv import load_dotenv
import json
from google.oauth2 import service_account

load_dotenv()

# Load credentials from the local service-account.json file
credentials_file = os.path.join(os.path.dirname(__file__), 'service-account.json')
with open(credentials_file) as f:
    credentials_info = json.load(f)

# Define the required scopes for Vertex AI and Google Generative AI
SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/aiplatform',
    'https://www.googleapis.com/auth/generative-language'
]

# Create credentials with the required scopes
credentials = service_account.Credentials.from_service_account_info(
    credentials_info, scopes=SCOPES
)
project_id = credentials_info.get('project_id')

# Set the credentials file path as the default for Google Cloud libraries
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file

print("Google Cloud credentials loaded successfully with Vertex AI and Generative AI scopes")

# Get Vertex AI configuration from environment
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")

# Initialize Vertex AI at package load time
try:
    if PROJECT_ID and LOCATION:
        print(f"Initializing Vertex AI with project={PROJECT_ID}, location={LOCATION}")
        vertexai.init(project=project_id, credentials=credentials, location=LOCATION)
        print("Vertex AI initialization successful")
    else:
        print(
            f"Missing Vertex AI configuration. PROJECT_ID={PROJECT_ID}, LOCATION={LOCATION}. "
            f"Tools requiring Vertex AI may not work properly."
        )
except Exception as e:
    print(f"Failed to initialize Vertex AI: {str(e)}")
    print("Please check your Google Cloud credentials and project settings.")

# Import agent after initialization is complete
from . import agent
