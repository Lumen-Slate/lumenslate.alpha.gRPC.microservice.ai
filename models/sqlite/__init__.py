from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = db_url = "sqlite:///./my_agent_data.db"

# Creating SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Creating SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Creating Base class for declarative models
Base = declarative_base()

# Import models to ensure they're registered with Base
from .models import UnalteredHistory, Questions, ReportCard

# Create all tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()