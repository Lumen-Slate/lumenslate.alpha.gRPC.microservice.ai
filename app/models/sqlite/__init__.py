import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration - use env variable or fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/data/my_agent_data.db")

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
# ─────────────────────────────────────────────────────────────────────────────

RAG_DATABASE_URL = os.getenv("RAG_DATABASE_URL", "sqlite:///./app/data/rag_agent_data.db")

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