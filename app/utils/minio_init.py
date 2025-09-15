#!/usr/bin/env python3
"""
MinIO initialization and verification script.

This script can be used to initialize MinIO buckets and verify the connection
during application startup or as a standalone verification tool.
"""

import asyncio
import logging
import sys
from typing import Dict, Any
from app.utils.minio_client import get_minio_client, MinIOConnectionError, MinIOBucketError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def verify_minio_setup() -> Dict[str, Any]:
    """
    Verify MinIO setup and return status information.
    
    Returns:
        Dict containing verification results and status information.
    """
    results = {
        "success": False,
        "connection": False,
        "buckets_created": False,
        "health_check": {},
        "errors": []
    }
    
    try:
        logger.info("Starting MinIO setup verification...")
        
        # Get MinIO client
        client = get_minio_client()
        logger.info(f"MinIO client configuration: {client.get_client_config()}")
        
        # Verify connection
        logger.info("Verifying MinIO connection...")
        if await client.verify_connection():
            results["connection"] = True
            logger.info("✓ MinIO connection verified successfully")
        else:
            results["errors"].append("MinIO connection verification failed")
            logger.error("✗ MinIO connection verification failed")
            return results
        
        # Initialize buckets
        logger.info("Ensuring required buckets exist...")
        try:
            await client.ensure_buckets_exist()
            results["buckets_created"] = True
            logger.info("✓ All required buckets are available")
        except MinIOBucketError as e:
            results["errors"].append(f"Bucket initialization failed: {e}")
            logger.error(f"✗ Bucket initialization failed: {e}")
            return results
        
        # Perform health check
        logger.info("Performing comprehensive health check...")
        health_status = await client.health_check()
        results["health_check"] = health_status
        
        if health_status["status"] == "healthy":
            logger.info("✓ MinIO health check passed")
            results["success"] = True
        elif health_status["status"] == "degraded":
            logger.warning("⚠ MinIO health check shows degraded status")
            results["errors"].extend(health_status.get("errors", []))
        else:
            logger.error("✗ MinIO health check failed")
            results["errors"].extend(health_status.get("errors", []))
        
        # Log bucket information
        for bucket_name, bucket_info in health_status.get("buckets", {}).items():
            if bucket_info.get("exists"):
                logger.info(f"  ✓ Bucket '{bucket_name}' ({bucket_info.get('purpose', 'unknown')}) is available")
            else:
                logger.warning(f"  ✗ Bucket '{bucket_name}' ({bucket_info.get('purpose', 'unknown')}) is not available")
        
    except MinIOConnectionError as e:
        results["errors"].append(f"Connection error: {e}")
        logger.error(f"✗ MinIO connection error: {e}")
    except Exception as e:
        results["errors"].append(f"Unexpected error: {e}")
        logger.error(f"✗ Unexpected error during MinIO verification: {e}")
    
    return results


async def main():
    """Main function for standalone script execution."""
    logger.info("MinIO Setup Verification Tool")
    logger.info("=" * 50)
    
    results = await verify_minio_setup()
    
    logger.info("\nVerification Results:")
    logger.info("=" * 50)
    logger.info(f"Overall Success: {'✓' if results['success'] else '✗'}")
    logger.info(f"Connection: {'✓' if results['connection'] else '✗'}")
    logger.info(f"Buckets Created: {'✓' if results['buckets_created'] else '✗'}")
    
    if results["errors"]:
        logger.error("\nErrors encountered:")
        for error in results["errors"]:
            logger.error(f"  - {error}")
    
    if results["health_check"]:
        health = results["health_check"]
        logger.info(f"\nHealth Status: {health['status']}")
        logger.info(f"Endpoint: {health['endpoint']}")
        
        if health.get("buckets"):
            logger.info("Bucket Status:")
            for bucket_name, bucket_info in health["buckets"].items():
                status = "✓" if bucket_info.get("exists") else "✗"
                purpose = bucket_info.get("purpose", "unknown")
                logger.info(f"  {status} {bucket_name} ({purpose})")
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())