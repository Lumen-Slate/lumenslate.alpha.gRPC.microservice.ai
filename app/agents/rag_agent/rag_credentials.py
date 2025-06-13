import os
import json
from google.oauth2 import service_account

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

