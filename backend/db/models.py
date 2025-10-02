from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    memos = relationship("Memo", back_populates="user")
    google_tokens = relationship("GoogleToken", back_populates="user")
    sources = relationship("Source", back_populates="user")
    memo_requests = relationship("MemoRequest", back_populates="user")

class GoogleToken(Base):
    __tablename__ = "google_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="google_tokens")

class Memo(Base):
    __tablename__ = "memos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, default="draft")  # draft, in_review, approved
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="memos")

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    company_id = Column(String, nullable=True)
    affinity_data = Column(JSON, nullable=True)
    drive_data = Column(JSON, nullable=True)
    perplexity_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="sources")

class MemoRequest(Base):
    __tablename__ = "memo_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    sources_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    status = Column(String, default="pending")  # pending, completed, failed, partial_success
    drive_link = Column(String, nullable=True)
    error_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="memo_requests")
    sections = relationship("MemoSection", back_populates="memo_request")

class MemoSection(Base):
    __tablename__ = "memo_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    memo_request_id = Column(Integer, ForeignKey("memo_requests.id"), nullable=False)
    section_name = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    data_sources = Column(JSON, nullable=True)  # ← Add this field
    status = Column(String, default="pending")  # pending, completed, failed
    error_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    memo_request = relationship("MemoRequest", back_populates="sections")