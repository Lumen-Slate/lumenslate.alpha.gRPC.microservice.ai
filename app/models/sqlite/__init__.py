import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file first!
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Main Agent Database Configuration - should use Neon DB in production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/data/my_agent_data.db")

if "postgresql://" in DATABASE_URL:
    try:
        # Test the connection first
        from sqlalchemy import text
        test_engine = create_engine(DATABASE_URL)
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        engine = test_engine
    except Exception:
        # Fallback to SQLite on connection failure
        DATABASE_URL = "sqlite:///./app/data/my_agent_data.db"
        engine = create_engine(DATABASE_URL)
else:
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
# # ─────────────────────────────────────────────────────────────────────────────
# # RAG Agent Database Configuration (separate database)
# # RAG Agent is ALWAYS SQLite - no external database needed
# # ─────────────────────────────────────────────────────────────────────────────

# RAG_DATABASE_URL = "sqlite:///./app/data/rag_agent_data.db"

# # Debug: Print RAG database URL
# print(f"🔍 [DEBUG] RAG Database initialization - RAG_DATABASE_URL: {RAG_DATABASE_URL} (SQLite only)")
# print("📝 [INFO] RAG Agent uses SQLite exclusively (as intended)")

# # Creating RAG-specific SQLAlchemy engine
# rag_engine = create_engine(RAG_DATABASE_URL)

# # Creating RAG-specific SessionLocal class
# RAGSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=rag_engine)

# # Create all tables for RAG database
# Base.metadata.create_all(bind=rag_engine)

# # Dependency to get RAG DB session
# def get_rag_db():
#     db = RAGSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
