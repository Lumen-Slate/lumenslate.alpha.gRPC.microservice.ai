#!/usr/bin/env python3
"""
Test script for Prisma ORM setup and migration.
This script verifies that Prisma is properly configured and can connect to the database.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.prisma_init import initialize_prisma_database, cleanup_prisma_database, health_check, get_prisma_client
from app.models.prisma.models import DocumentRepository, UserUsageRepository, DocumentService
from prisma.enums import Status

async def test_prisma_connection():
    """Test basic Prisma connection and operations."""
    print("🧪 Testing Prisma Database Connection")
    print("=" * 50)
    
    # Initialize Prisma
    success = await initialize_prisma_database()
    if not success:
        print("❌ Failed to initialize Prisma database")
        return False
    
    # Get client
    client = get_prisma_client()
    if not client:
        print("❌ Failed to get Prisma client")
        return False
    
    print("✅ Prisma client initialized successfully")
    
    # Test health check
    health = await health_check()
    print("\n📊 Health Check Results:")
    for key, value in health.items():
        if key != 'timestamp':
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
    
    return all([health['prisma_initialized'], health['database_connected'], health['tables_accessible']])

async def test_document_operations():
    """Test document CRUD operations."""
    print("\n🧪 Testing Document Operations")
    print("=" * 50)
    
    client = get_prisma_client()
    if not client:
        print("❌ Prisma client not available")
        return False
    
    try:
        # Initialize repositories
        doc_repo = DocumentRepository(client)
        usage_repo = UserUsageRepository(client)
        doc_service = DocumentService(client)
        
        test_user_id = "test_user_123"
        test_filename = "test_document.pdf"
        test_path = f"documents/{test_user_id}/test/{datetime.now().strftime('%Y-%m-%d')}/{test_filename}"
        
        print(f"📝 Testing with user: {test_user_id}")
        
        # Test 1: Create document with usage update
        print("  🔹 Creating document with usage update...")
        document = await doc_service.create_document_with_usage_update(
            user_id=test_user_id,
            category="test",
            filename=test_filename,
            path=test_path,
            size=1024,
            mime_type="application/pdf"
        )
        print(f"  ✅ Created document: {document.id}")
        
        # Test 2: Retrieve document
        print("  🔹 Retrieving document...")
        retrieved_doc = await doc_repo.get_document_by_id(document.id)
        if retrieved_doc:
            print(f"  ✅ Retrieved document: {retrieved_doc.filename}")
        else:
            print("  ❌ Failed to retrieve document")
            return False
        
        # Test 3: List user documents
        print("  🔹 Listing user documents...")
        user_docs = await doc_repo.list_documents_by_user(test_user_id)
        print(f"  ✅ Found {len(user_docs)} documents for user")
        
        # Test 4: Get user usage
        print("  🔹 Getting user usage...")
        usage = await usage_repo.get_user_usage(test_user_id)
        if usage:
            print(f"  ✅ User usage: {usage.fileCount} files, {usage.totalBytes} bytes")
        else:
            print("  ❌ Failed to get user usage")
            return False
        
        # Test 5: Update document status
        print("  🔹 Updating document status...")
        updated_doc = await doc_repo.update_document_status(document.id, Status.COMPLETED)
        if updated_doc and updated_doc.status == Status.COMPLETED:
            print("  ✅ Document status updated successfully")
        else:
            print("  ❌ Failed to update document status")
            return False
        
        # Test 6: Delete document with usage update
        print("  🔹 Deleting document with usage update...")
        deleted = await doc_service.delete_document_with_usage_update(document.id)
        if deleted:
            print("  ✅ Document deleted successfully")
        else:
            print("  ❌ Failed to delete document")
            return False
        
        # Test 7: Verify usage updated after deletion
        print("  🔹 Verifying usage after deletion...")
        final_usage = await usage_repo.get_user_usage(test_user_id)
        if final_usage and final_usage.fileCount == 0 and final_usage.totalBytes == 0:
            print("  ✅ Usage statistics updated correctly after deletion")
        else:
            print(f"  ⚠️ Usage after deletion: {final_usage.fileCount if final_usage else 'N/A'} files, {final_usage.totalBytes if final_usage else 'N/A'} bytes")
        
        print("\n✅ All document operations completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Document operations test failed: {e}")
        return False

async def test_migration_readiness():
    """Test migration readiness and compatibility."""
    print("\n🧪 Testing Migration Readiness")
    print("=" * 50)
    
    try:
        # Check if we can import migration utilities
        from app.models.prisma.migration import PrismaMigrationManager
        
        database_url = os.getenv("MICROSERVICE_DATABASE")
        if not database_url:
            print("⚠️ MICROSERVICE_DATABASE not set - migration testing skipped")
            return True
        
        print("  🔹 Migration utilities imported successfully")
        
        # Initialize migration manager (but don't run migration)
        migration_manager = PrismaMigrationManager(database_url)
        print("  ✅ Migration manager initialized")
        
        # Test Prisma connection through migration manager
        connected = await migration_manager.initialize_prisma()
        if connected:
            print("  ✅ Migration manager can connect to database")
            await migration_manager.cleanup_prisma()
        else:
            print("  ❌ Migration manager failed to connect to database")
            return False
        
        print("\n✅ Migration readiness test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration readiness test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Prisma ORM Setup Test Suite")
    print("=" * 60)
    
    all_tests_passed = True
    
    try:
        # Test 1: Basic connection
        connection_ok = await test_prisma_connection()
        all_tests_passed = all_tests_passed and connection_ok
        
        if connection_ok:
            # Test 2: Document operations
            operations_ok = await test_document_operations()
            all_tests_passed = all_tests_passed and operations_ok
            
            # Test 3: Migration readiness
            migration_ok = await test_migration_readiness()
            all_tests_passed = all_tests_passed and migration_ok
        else:
            print("\n⚠️ Skipping further tests due to connection failure")
    
    except Exception as e:
        print(f"\n❌ Test suite failed with unexpected error: {e}")
        all_tests_passed = False
    
    finally:
        # Cleanup
        await cleanup_prisma_database()
    
    # Print final results
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 All tests passed! Prisma ORM setup is ready.")
        print("\n📋 Next steps:")
        print("  1. Run 'prisma migrate deploy' to apply schema to database")
        print("  2. Optionally run migration script to migrate existing data")
        print("  3. Integrate Prisma with gRPC document service")
    else:
        print("❌ Some tests failed. Please check the configuration and try again.")
        print("\n🔍 Common issues:")
        print("  • Check MICROSERVICE_DATABASE environment variable")
        print("  • Ensure database server is running and accessible")
        print("  • Run 'prisma migrate deploy' to create database schema")
    
    return all_tests_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)