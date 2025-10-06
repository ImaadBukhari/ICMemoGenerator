from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    tokens = relationship("GoogleToken", back_populates="user")
    sources = relationship("Source", back_populates="user")
    memo_requests = relationship("MemoRequest", back_populates="user")


class GoogleToken(Base):
    __tablename__ = "google_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    access_token = Column(Text)
    refresh_token = Column(Text)
    expiry = Column(TIMESTAMP(timezone=True))

    user = relationship("User", back_populates="tokens")


class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_name = Column(String)
    company_description = Column(String, nullable=True)  # NEW - for description
    affinity_data = Column(JSON, nullable=True)
    perplexity_data = Column(JSON, nullable=True)
    gmail_data = Column(JSON, nullable=True)
    drive_data = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # ALL THREE RELATIONSHIPS
    user = relationship("User", back_populates="sources")
    memo_requests = relationship("MemoRequest", back_populates="sources")
    embeddings = relationship("DocumentEmbedding", back_populates="source", cascade="all, delete-orphan")

class MemoSection(Base):
    __tablename__ = "memo_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    memo_request_id = Column(Integer, ForeignKey("memo_requests.id"), nullable=False)
    section_name = Column(String, nullable=False)
    content = Column(Text)
    data_sources = Column(JSON)  # List of Perplexity categories used
    status = Column(String, default="pending")  # pending, completed, failed
    error_log = Column(Text)
    # Fix: Use TIMESTAMP instead of datetime, and func.now() for defaults
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship back to memo request
    memo_request = relationship("MemoRequest", back_populates="sections")

class MemoRequest(Base):
    __tablename__ = "memo_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_name = Column(String)
    drive_link = Column(Text)       # link to final Google Doc
    sources_id = Column(Integer, ForeignKey("sources.id"))
    status = Column(String)         # "pending", "success", "failed"
    error_log = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    sections = relationship("MemoSection", back_populates="memo_request")

    user = relationship("User", back_populates="memo_requests")
    sources = relationship("Source", back_populates="memo_requests")


# Add this to your existing models

class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    chunk_type = Column(String, nullable=False)
    embedding = Column(JSON, nullable=False)
    sources = Column(JSON)
    chunk_metadata = Column(JSON)  # CHANGED FROM 'metadata' to 'chunk_metadata'
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationship
    source = relationship("Source", back_populates="embeddings")
