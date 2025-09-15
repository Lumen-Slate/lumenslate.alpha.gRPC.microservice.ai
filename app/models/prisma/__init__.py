"""
Prisma ORM client initialization and connection management for Document Storage Service.
This module provides the Prisma client instance and database connection utilities.
"""

import os
import asyncio
from typing import Optional
from prisma import Prisma
from prisma.errors import PrismaError
import logging

logger = logging.getLogger(__name__)

# Global Prisma client instance
_prisma_client: Optional[Prisma] = None

def get_prisma_client() -> Prisma:
    """
    Get the global Prisma client instance.
    Creates a new instance if one doesn't exist.
    
    Returns:
        Prisma: The Prisma client instance
    """
    global _prisma_client
    
    if _prisma_client is None:
        _prisma_client = Prisma()
        logger.info("Created new Prisma client instance")
    
    return _prisma_client

async def connect_prisma() -> bool:
    """
    Connect to the database using Prisma client.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        client = get_prisma_client()
        await client.connect()
        logger.info("Successfully connected to database via Prisma")
        return True
    except PrismaError as e:
        logger.error(f"Failed to connect to database via Prisma: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error connecting to database: {e}")
        return False

async def disconnect_prisma() -> None:
    """
    Disconnect from the database and cleanup Prisma client.
    """
    global _prisma_client
    
    if _prisma_client is not None:
        try:
            await _prisma_client.disconnect()
            logger.info("Disconnected from database via Prisma")
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")
        finally:
            _prisma_client = None

async def verify_database_connection() -> bool:
    """
    Verify that the database connection is working by performing a simple query.
    
    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        client = get_prisma_client()
        
        # Try to count documents (this will work even if table is empty)
        await client.document.count()
        logger.info("Database connection verified successfully")
        return True
    except PrismaError as e:
        logger.error(f"Database connection verification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during connection verification: {e}")
        return False

class PrismaManager:
    """
    Context manager for Prisma database operations.
    Ensures proper connection and disconnection handling.
    """
    
    def __init__(self):
        self.client = None
    
    async def __aenter__(self) -> Prisma:
        """
        Async context manager entry.
        
        Returns:
            Prisma: Connected Prisma client
        """
        self.client = get_prisma_client()
        
        # Connect if not already connected
        if not self.client.is_connected():
            await connect_prisma()
        
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        Note: We don't disconnect here as the client may be used elsewhere.
        """
        if exc_type is not None:
            logger.error(f"Exception in Prisma context: {exc_type.__name__}: {exc_val}")
        
        # Don't disconnect here - let the application manage the global connection

# Dependency function for dependency injection
async def get_prisma_dependency() -> Prisma:
    """
    Dependency function to get Prisma client for dependency injection.
    Ensures the client is connected before returning.
    
    Returns:
        Prisma: Connected Prisma client
    """
    client = get_prisma_client()
    
    if not client.is_connected():
        await connect_prisma()
    
    return client