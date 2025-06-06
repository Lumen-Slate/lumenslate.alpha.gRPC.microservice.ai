from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from . import Base     
from enum import Enum
from sqlalchemy import DateTime
from datetime import datetime, timezone

class Role(Enum):
    USER = "user"   
    AGENT = "agent"

class UnalteredHistory(Base):
    __tablename__ = 'unaltered_history'
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    message = Column(String, nullable=False)
    role = Column(SQLEnum(Role), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class Questions(Base):
    __tablename__ = 'questions'

    question_id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String, nullable=False)
    question = Column(String, nullable=False)
    options = Column(String, nullable=False)  # JSON string of options
    answer = Column(String, nullable=False)  # Correct answer

class ReportCard(Base):
    __tablename__ = 'report_card'

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    score = Column(Integer, nullable=False)  # Score out of 100
    comments = Column(String, nullable=True)  # Additional comments or feedback
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)