import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file first!
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("🔍 [DEBUG] Environment variables loaded from .env file")
except ImportError:
    print("⚠️ [DEBUG] python-dotenv not installed, using system environment variables only")

# Main Agent Database Configuration - should use Neon DB in production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/data/my_agent_data.db")

# Debug: Print which database URL is being used
print(f"🔍 [DEBUG] Main Agent Database initialization - DATABASE_URL: {DATABASE_URL[:60]}...")
if "postgresql://" in DATABASE_URL:
    print("✅ [DEBUG] Main Agent attempting PostgreSQL/Neon DB connection...")
    try:
        # Test the connection first
        from sqlalchemy import text
        test_engine = create_engine(DATABASE_URL)
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✅ [SUCCESS] Neon DB connection successful!")
        engine = test_engine
    except Exception as e:
        print(f"❌ [ERROR] Neon DB connection failed: {e}")
        print("🔄 [FALLBACK] Switching to SQLite...")
        DATABASE_URL = "sqlite:///./app/data/my_agent_data.db"
        engine = create_engine(DATABASE_URL)
else:
    print("⚠️ [DEBUG] Main Agent using SQLite (development fallback)")
    print("💡 [INFO] For production, set DATABASE_URL to your Neon DB connection string")
    # Creating SQLAlchemy engine
    engine = create_engine(DATABASE_URL)

# Creating SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Creating Base class for declarative models
Base = declarative_base()

# Import models to ensure they're registered with Base
from .models import UnalteredHistory, Questions, SubjectReport

# Create all tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─────────────────────────────────────────────────────────────────────────────
# RAG Agent Database Configuration (separate database)
# RAG Agent is ALWAYS SQLite - no external database needed
# ─────────────────────────────────────────────────────────────────────────────

RAG_DATABASE_URL = "sqlite:///./app/data/rag_agent_data.db"

# Debug: Print RAG database URL
print(f"🔍 [DEBUG] RAG Database initialization - RAG_DATABASE_URL: {RAG_DATABASE_URL} (SQLite only)")
print("📝 [INFO] RAG Agent uses SQLite exclusively (as intended)")

# Creating RAG-specific SQLAlchemy engine
rag_engine = create_engine(RAG_DATABASE_URL)

# Creating RAG-specific SessionLocal class
RAGSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=rag_engine)

# Create all tables for RAG database
Base.metadata.create_all(bind=rag_engine)

# Dependency to get RAG DB session
def get_rag_db():
    db = RAGSessionLocal()
    try:
        yield db
    finally:
        db.close()