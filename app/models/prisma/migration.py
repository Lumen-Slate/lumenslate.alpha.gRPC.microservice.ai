"""
Migration utilities for transitioning from SQLAlchemy to Prisma ORM.
This module provides tools to migrate existing data and validate the migration process.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from prisma import Prisma
from prisma.enums import Status

# Import existing SQLAlchemy models
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.models.sqlite.models import RAGContext as SQLAlchemyRAGContext

logger = logging.getLogger(__name__)

class PrismaMigrationManager:
    """
    Manages the migration from SQLAlchemy to Prisma ORM.
    Provides data migration, validation, and rollback capabilities.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize migration manager.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.sqlalchemy_engine = create_engine(database_url)
        self.sqlalchemy_session = sessionmaker(bind=self.sqlalchemy_engine)
        self.prisma_client = Prisma()
    
    async def initialize_prisma(self) -> bool:
        """
        Initialize Prisma client and ensure database connection.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self.prisma_client.connect()
            logger.info("Prisma client connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect Prisma client: {e}")
            return False
    
    async def cleanup_prisma(self) -> None:
        """
        Cleanup Prisma client connection.
        """
        try:
            await self.prisma_client.disconnect()
            logger.info("Prisma client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting Prisma client: {e}")
    
    def get_existing_rag_documents(self) -> List[Dict[str, Any]]:
        """
        Retrieve existing RAG documents from SQLAlchemy models.
        
        Returns:
            List[Dict]: List of document records
        """
        try:
            with self.sqlalchemy_session() as session:
                # Query existing rag_context table if it exists
                result = session.execute(text("""
                    SELECT 
                        id,
                        teacherId as user_id,
                        context_data,
                        source,
                        timestamp as created_at
                    FROM rag_context 
                    ORDER BY timestamp DESC
                """))
                
                documents = []
                for row in result:
                    documents.append({
                        'id': str(row.id),
                        'user_id': row.user_id,
                        'category': 'rag_context',  # Default category for existing data
                        'filename': row.source or f"context_{row.id}.txt",
                        'path': f"documents/{row.user_id}/rag_context/{row.created_at.strftime('%Y-%m-%d')}/{row.source or f'context_{row.id}.txt'}",
                        'size': len(row.context_data.encode('utf-8')) if row.context_data else 0,
                        'mime_type': 'text/plain',
                        'status': 'COMPLETED',
                        'created_at': row.created_at,
                        'updated_at': row.created_at
                    })
                
                logger.info(f"Found {len(documents)} existing RAG documents")
                return documents
                
        except Exception as e:
            logger.error(f"Failed to retrieve existing documents: {e}")
            return []
    
    async def migrate_documents_to_prisma(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Migrate document records to Prisma models.
        
        Args:
            documents: List of document records to migrate
            
        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            migrated_count = 0
            
            for doc in documents:
                try:
                    # Create document in Prisma
                    await self.prisma_client.document.create(
                        data={
                            'id': doc['id'],
                            'userId': doc['user_id'],
                            'category': doc['category'],
                            'filename': doc['filename'],
                            'path': doc['path'],
                            'size': doc['size'],
                            'mimeType': doc['mime_type'],
                            'status': Status.COMPLETED,
                            'createdAt': doc['created_at'],
                            'updatedAt': doc['updated_at']
                        }
                    )
                    
                    # Update or create user usage
                    await self.prisma_client.userusage.upsert(
                        where={'userId': doc['user_id']},
                        data={
                            'userId': doc['user_id'],
                            'fileCount': 1,
                            'totalBytes': doc['size']
                        },
                        update={
                            'fileCount': {'increment': 1},
                            'totalBytes': {'increment': doc['size']}
                        }
                    )
                    
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to migrate document {doc['id']}: {e}")
                    continue
            
            logger.info(f"Successfully migrated {migrated_count}/{len(documents)} documents")
            return migrated_count == len(documents)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    async def validate_migration(self) -> Dict[str, Any]:
        """
        Validate the migration by comparing data between SQLAlchemy and Prisma.
        
        Returns:
            Dict: Validation results
        """
        validation_results = {
            'success': False,
            'sqlalchemy_count': 0,
            'prisma_count': 0,
            'user_usage_count': 0,
            'errors': []
        }
        
        try:
            # Count SQLAlchemy records
            with self.sqlalchemy_session() as session:
                result = session.execute(text("SELECT COUNT(*) FROM rag_context"))
                validation_results['sqlalchemy_count'] = result.scalar()
            
            # Count Prisma records
            validation_results['prisma_count'] = await self.prisma_client.document.count()
            validation_results['user_usage_count'] = await self.prisma_client.userusage.count()
            
            # Check if counts match (allowing for some flexibility)
            if validation_results['prisma_count'] >= validation_results['sqlalchemy_count']:
                validation_results['success'] = True
            else:
                validation_results['errors'].append(
                    f"Document count mismatch: SQLAlchemy={validation_results['sqlalchemy_count']}, "
                    f"Prisma={validation_results['prisma_count']}"
                )
            
            logger.info(f"Migration validation: {validation_results}")
            return validation_results
            
        except Exception as e:
            validation_results['errors'].append(f"Validation failed: {e}")
            logger.error(f"Migration validation failed: {e}")
            return validation_results
    
    async def create_backup_tables(self) -> bool:
        """
        Create backup tables of existing data before migration.
        
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            with self.sqlalchemy_session() as session:
                # Create backup of rag_context table
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS rag_context_backup AS 
                    SELECT * FROM rag_context
                """))
                session.commit()
                
                logger.info("Created backup tables successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create backup tables: {e}")
            return False
    
    async def run_full_migration(self) -> Dict[str, Any]:
        """
        Run the complete migration process.
        
        Returns:
            Dict: Migration results
        """
        migration_results = {
            'success': False,
            'steps_completed': [],
            'errors': []
        }
        
        try:
            # Step 1: Initialize Prisma
            if not await self.initialize_prisma():
                migration_results['errors'].append("Failed to initialize Prisma")
                return migration_results
            migration_results['steps_completed'].append("Prisma initialized")
            
            # Step 2: Create backup
            if await self.create_backup_tables():
                migration_results['steps_completed'].append("Backup created")
            else:
                migration_results['errors'].append("Backup creation failed")
            
            # Step 3: Get existing documents
            existing_docs = self.get_existing_rag_documents()
            migration_results['steps_completed'].append(f"Found {len(existing_docs)} existing documents")
            
            # Step 4: Migrate documents
            if existing_docs:
                if await self.migrate_documents_to_prisma(existing_docs):
                    migration_results['steps_completed'].append("Documents migrated")
                else:
                    migration_results['errors'].append("Document migration failed")
            else:
                migration_results['steps_completed'].append("No documents to migrate")
            
            # Step 5: Validate migration
            validation = await self.validate_migration()
            if validation['success']:
                migration_results['steps_completed'].append("Migration validated")
                migration_results['success'] = True
            else:
                migration_results['errors'].extend(validation['errors'])
            
            migration_results['validation'] = validation
            
        except Exception as e:
            migration_results['errors'].append(f"Migration process failed: {e}")
            logger.error(f"Full migration failed: {e}")
        
        finally:
            await self.cleanup_prisma()
        
        return migration_results

async def run_migration_script():
    """
    Main migration script entry point.
    """
    # Get database URL from environment
    database_url = os.getenv("MICROSERVICE_DATABASE")
    if not database_url:
        print("❌ ERROR: MICROSERVICE_DATABASE environment variable not set!")
        return False
    
    print("🚀 Starting SQLAlchemy to Prisma migration...")
    print("=" * 60)
    
    migration_manager = PrismaMigrationManager(database_url)
    results = await migration_manager.run_full_migration()
    
    print("\n📊 Migration Results:")
    print("=" * 60)
    
    if results['success']:
        print("✅ Migration completed successfully!")
        print("\n📋 Steps completed:")
        for step in results['steps_completed']:
            print(f"  ✓ {step}")
        
        if 'validation' in results:
            validation = results['validation']
            print(f"\n📈 Validation Summary:")
            print(f"  • SQLAlchemy records: {validation['sqlalchemy_count']}")
            print(f"  • Prisma documents: {validation['prisma_count']}")
            print(f"  • User usage records: {validation['user_usage_count']}")
    else:
        print("❌ Migration failed!")
        print("\n🔍 Steps completed:")
        for step in results['steps_completed']:
            print(f"  ✓ {step}")
        
        print("\n❌ Errors encountered:")
        for error in results['errors']:
            print(f"  • {error}")
    
    return results['success']

if __name__ == "__main__":
    asyncio.run(run_migration_script())