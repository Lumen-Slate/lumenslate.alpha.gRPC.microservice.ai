"""
Prisma database initialization utilities.
This module provides functions to initialize and manage Prisma database connections.
"""

import asyncio
import os
import logging
from typing import Optional
from prisma import Prisma
from prisma.errors import PrismaError
from app.config.settings.document_service import document_service_settings

logger = logging.getLogger(__name__)

class PrismaInitializer:
    """
    Handles Prisma database initialization and health checks.
    """
    
    def __init__(self):
        self.client: Optional[Prisma] = None
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize Prisma client and establish database connection.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing Prisma database connection...")
            
            # Create Prisma client
            self.client = Prisma()
            
            # Connect to database
            await self.client.connect()
            
            # Verify connection with a simple query
            await self.verify_connection()
            
            self.is_initialized = True
            logger.info("✅ Prisma database connection initialized successfully")
            return True
            
        except PrismaError as e:
            logger.error(f"❌ Prisma initialization failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during Prisma initialization: {e}")
            return False
    
    async def verify_connection(self) -> bool:
        """
        Verify that the database connection is working.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        if not self.client:
            logger.error("Prisma client not initialized")
            return False
        
        try:
            # Try to perform a simple query
            await self.client.document.count()
            logger.info("Database connection verified successfully")
            return True
            
        except PrismaError as e:
            logger.error(f"Database connection verification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection verification: {e}")
            return False
    
    async def ensure_tables_exist(self) -> bool:
        """
        Ensure that required database tables exist.
        This is typically handled by Prisma migrations, but we can verify here.
        
        Returns:
            bool: True if tables exist or were created, False otherwise
        """
        if not self.client:
            logger.error("Prisma client not initialized")
            return False
        
        try:
            # Try to query each table to ensure they exist
            await self.client.document.count()
            await self.client.userusage.count()
            
            logger.info("All required database tables are available")
            return True
            
        except PrismaError as e:
            logger.error(f"Database tables verification failed: {e}")
            logger.info("You may need to run 'prisma migrate deploy' to create tables")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during table verification: {e}")
            return False
    
    async def cleanup(self) -> None:
        """
        Cleanup Prisma client connection.
        """
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("Prisma client disconnected successfully")
            except Exception as e:
                logger.error(f"Error disconnecting Prisma client: {e}")
            finally:
                self.client = None
                self.is_initialized = False
    
    def get_client(self) -> Optional[Prisma]:
        """
        Get the initialized Prisma client.
        
        Returns:
            Optional[Prisma]: Prisma client if initialized, None otherwise
        """
        return self.client if self.is_initialized else None

# Global initializer instance
prisma_initializer = PrismaInitializer()

async def initialize_prisma_database() -> bool:
    """
    Initialize Prisma database connection.
    This function should be called during application startup.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    logger.info("🚀 Starting Prisma database initialization...")
    
    # Check if database URL is configured
    if not document_service_settings.microservice_database:
        logger.error("❌ MICROSERVICE_DATABASE environment variable not set!")
        logger.info("Please set your database connection string:")
        logger.info("export MICROSERVICE_DATABASE='mysql://username:password@host:port/database'")
        return False
    
    # Log database connection info (without credentials)
    db_url = document_service_settings.microservice_database
    safe_url = db_url.split('@')[-1] if '@' in db_url else db_url[:50]
    logger.info(f"🔗 Connecting to database: {safe_url}")
    
    # Initialize Prisma
    success = await prisma_initializer.initialize()
    
    if success:
        # Verify tables exist
        tables_ok = await prisma_initializer.ensure_tables_exist()
        if not tables_ok:
            logger.warning("⚠️ Database tables may not exist. Consider running migrations.")
        
        logger.info("🎉 Prisma database initialization completed!")
        return True
    else:
        logger.error("❌ Prisma database initialization failed!")
        return False

async def cleanup_prisma_database() -> None:
    """
    Cleanup Prisma database connection.
    This function should be called during application shutdown.
    """
    logger.info("🧹 Cleaning up Prisma database connection...")
    await prisma_initializer.cleanup()
    logger.info("✅ Prisma cleanup completed")

def get_prisma_client() -> Optional[Prisma]:
    """
    Get the global Prisma client instance.
    
    Returns:
        Optional[Prisma]: Prisma client if initialized, None otherwise
    """
    return prisma_initializer.get_client()

async def health_check() -> dict:
    """
    Perform a health check on the Prisma database connection.
    
    Returns:
        dict: Health check results
    """
    health_status = {
        'prisma_initialized': prisma_initializer.is_initialized,
        'database_connected': False,
        'tables_accessible': False,
        'timestamp': asyncio.get_event_loop().time()
    }
    
    if prisma_initializer.is_initialized:
        # Check database connection
        health_status['database_connected'] = await prisma_initializer.verify_connection()
        
        # Check table accessibility
        if health_status['database_connected']:
            health_status['tables_accessible'] = await prisma_initializer.ensure_tables_exist()
    
    return health_status

if __name__ == "__main__":
    """
    Run Prisma initialization as a standalone script.
    """
    async def main():
        success = await initialize_prisma_database()
        
        if success:
            # Run health check
            health = await health_check()
            print("\n📊 Health Check Results:")
            for key, value in health.items():
                status = "✅" if value else "❌"
                print(f"  {status} {key}: {value}")
        
        await cleanup_prisma_database()
        return success
    
    result = asyncio.run(main())
    exit(0 if result else 1)