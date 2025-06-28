"""
Authentication helper for Google Cloud services.
Handles both local development and deployed environments.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def setup_google_auth() -> bool:
    """
    Set up Google Cloud authentication based on environment.
    
    Returns:
        bool: True if authentication is properly configured, False otherwise
    """
    try:
        # Check if we're in a deployed Google Cloud environment
        if is_deployed_environment():
            logger.info("Detected deployed environment - using metadata service for authentication")
            # Remove GOOGLE_APPLICATION_CREDENTIALS if set to allow metadata service
            if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
                del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
            return True
            
        # Check for local service account file
        service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if service_account_path and os.path.exists(service_account_path):
            logger.info(f"Using service account file: {service_account_path}")
            return True
            
        # Try to find service-account.json in common locations
        common_paths = [
            "service-account.json",
            "./service-account.json", 
            "../service-account.json",
            os.path.join(os.getcwd(), "service-account.json")
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"Found service account file at: {path}")
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
                return True
                
        logger.warning("No authentication method found. For local development, ensure service-account.json exists.")
        return False
        
    except Exception as e:
        logger.error(f"Error setting up authentication: {e}")
        return False

def is_deployed_environment() -> bool:
    """
    Check if the application is running in a deployed Google Cloud environment.
    
    Returns:
        bool: True if running in Cloud Run, GKE, or other GCP compute environment
    """
    # Check for Cloud Run environment variables
    if os.getenv("K_SERVICE") or os.getenv("CLOUD_RUN_JOB"):
        return True
        
    # Check for GKE environment variables
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return True
        
    # Check for Compute Engine metadata server
    try:
        import urllib.request
        urllib.request.urlopen("http://metadata.google.internal", timeout=1)
        return True
    except:
        pass
        
    # Check for Google Cloud environment variables
    if any(os.getenv(var) for var in [
        "GOOGLE_CLOUD_PROJECT", 
        "GCLOUD_PROJECT", 
        "GCP_PROJECT",
        "FUNCTION_NAME",  # Cloud Functions
        "GAE_SERVICE"     # App Engine
    ]):
        return True
        
    return False

def get_project_id() -> Optional[str]:
    """
    Get the Google Cloud project ID from various sources.
    
    Returns:
        str: Project ID if found, None otherwise
    """
    # Try environment variables first
    project_id = os.getenv("GOOGLE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCLOUD_PROJECT")
    if project_id:
        return project_id
        
    # If in deployed environment, try metadata service
    if is_deployed_environment():
        try:
            import urllib.request
            import json
            
            req = urllib.request.Request(
                "http://metadata.google.internal/computeMetadata/v1/project/project-id",
                headers={"Metadata-Flavor": "Google"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            logger.warning(f"Could not get project ID from metadata service: {e}")
            
    return None
