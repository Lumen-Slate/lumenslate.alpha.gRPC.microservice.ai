#!/usr/bin/env python3
"""
Database setup script for PostgreSQL.
This script creates all necessary tables in the PostgreSQL database.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

# Add the current directory to Python path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.sqlite.models import Base, UnalteredHistory, Questions, SubjectReport, RAGContext

def setup_database():
    """Set up the PostgreSQL database with all required tables."""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print("Please set your PostgreSQL connection string:")
        print("export DATABASE_URL='postgresql://username:password@host:port/database'")
        return False
        
    print(f"🔗 Connecting to database...")
    print(f"Database URL: {database_url[:50]}...")  # Show first 50 chars only for security
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Successfully connected to PostgreSQL!")
            print(f"Database version: {version}")
        
        # Create all tables
        print("🔨 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Verify tables were created
        print("🔍 Verifying tables...")
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"📋 Tables found in database: {', '.join(tables)}")
            
            # Verify unaltered_history table structure
            if 'unaltered_history' in tables:
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'unaltered_history'
                    ORDER BY ordinal_position;
                """))
                columns = result.fetchall()
                print("🔍 unaltered_history table structure:")
                for col_name, data_type, is_nullable in columns:
                    print(f"  - {col_name}: {data_type} ({'nullable' if is_nullable == 'YES' else 'not null'})")
                    
                # Check if teacherId column exists (PostgreSQL lowercases column names)
                teacher_id_exists = any(col[0].lower() == 'teacherid' for col in columns)
                if teacher_id_exists:
                    print("✅ teacherId column found in unaltered_history table!")
                else:
                    print("❌ teacherId column NOT found in unaltered_history table!")
                    return False
            else:
                print("❌ unaltered_history table not found!")
                return False
        
        print("🎉 Database setup completed successfully!")
        return True
        
    except OperationalError as e:
        print(f"❌ Database connection error: {e}")
        print("Please check your DATABASE_URL and ensure PostgreSQL is running.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_database_operations():
    """Test basic database operations."""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set, skipping tests.")
        return False
        
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Test creating a session and inserting a test record
        print("🧪 Testing database operations...")
        
        with SessionLocal() as db:
            # Test insert
            from app.models.sqlite.models import UnalteredHistory, Role
            test_record = UnalteredHistory(
                teacherId="test_teacher_123",
                message="Test message",
                role=Role.USER
            )
            db.add(test_record)
            db.commit()
            db.refresh(test_record)
            print(f"✅ Test insert successful! Record ID: {test_record.id}")
            
            # Test select
            count = db.query(UnalteredHistory).filter(UnalteredHistory.teacherId == "test_teacher_123").count()
            print(f"✅ Test select successful! Found {count} record(s)")
            
            # Clean up test data
            db.query(UnalteredHistory).filter(UnalteredHistory.teacherId == "test_teacher_123").delete()
            db.commit()
            print("✅ Test cleanup successful!")
            
        print("🎉 All database operations working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Database operation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting PostgreSQL database setup...")
    print("=" * 50)
    
    # Setup database
    if setup_database():
        print("\n" + "=" * 50)
        # Test operations
        if test_database_operations():
            print("\n🎯 Database is ready for use!")
            print("\nNext steps:")
            print("1. Start your gRPC microservice")
            print("2. Test the /ai/agent endpoint")
            print("3. Check that history is being saved to PostgreSQL")
        else:
            print("\n⚠️ Database setup complete but operations test failed.")
            print("Please check your configuration.")
    else:
        print("\n❌ Database setup failed!")
        print("Please fix the issues above and try again.") 