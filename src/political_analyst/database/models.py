"""Database models for the political analyst database."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Document(Base):
    """Model for political documents."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(1000), unique=True, nullable=False)
    document_type = Column(String(100), nullable=False)  # bill, resolution, amendment, etc.
    source = Column(String(200), nullable=False)  # congress.gov, senate.gov, etc.
    published_date = Column(DateTime)
    crawled_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="active")  # active, archived, deleted
    metadata = Column(JSON)
    
    # Relationships
    entities = relationship("DocumentEntity", back_populates="document")
    analyses = relationship("DocumentAnalysis", back_populates="document")
    vectors = relationship("DocumentVector", back_populates="document")


class Politician(Base):
    """Model for politicians."""
    
    __tablename__ = "politicians"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    party = Column(String(50))
    position = Column(String(100))  # Senator, Representative, etc.
    state = Column(String(50))
    district = Column(String(20))
    bio = Column(Text)
    photo_url = Column(String(500))
    website_url = Column(String(500))
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    social_media_accounts = relationship("SocialMediaAccount", back_populates="politician")
    entity_mentions = relationship("PoliticianEntity", back_populates="politician")
    reports = relationship("PoliticianReport", back_populates="politician")


class Entity(Base):
    """Model for extracted entities."""
    
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    entity_type = Column(String(50), nullable=False)  # PERSON, ORG, GPE, etc.
    description = Column(Text)
    confidence_score = Column(Float)
    metadata = Column(JSON)
    
    # Relationships
    document_mentions = relationship("DocumentEntity", back_populates="entity")
    politician_mentions = relationship("PoliticianEntity", back_populates="entity")


class DocumentEntity(Base):
    """Association table for documents and entities."""
    
    __tablename__ = "document_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    entity_id = Column(Integer, ForeignKey("entities.id"))
    mention_count = Column(Integer, default=1)
    context = Column(Text)
    sentiment = Column(Float)  # -1 to 1
    
    # Relationships
    document = relationship("Document", back_populates="entities")
    entity = relationship("Entity", back_populates="document_mentions")


class PoliticianEntity(Base):
    """Association table for politicians and entities."""
    
    __tablename__ = "politician_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    politician_id = Column(Integer, ForeignKey("politicians.id"))
    entity_id = Column(Integer, ForeignKey("entities.id"))
    association_type = Column(String(50))  # mentioned_by, sponsor_of, etc.
    strength = Column(Float)  # Association strength
    
    # Relationships
    politician = relationship("Politician", back_populates="entity_mentions")
    entity = relationship("Entity", back_populates="politician_mentions")


class DocumentAnalysis(Base):
    """Model for document analysis results."""
    
    __tablename__ = "document_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    analysis_type = Column(String(50), nullable=False)  # sentiment, topic, summary, etc.
    result = Column(JSON, nullable=False)
    confidence_score = Column(Float)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="analyses")


class DocumentVector(Base):
    """Model for document vector embeddings."""
    
    __tablename__ = "document_vectors"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    embedding_model = Column(String(100), nullable=False)
    vector_data = Column(JSON, nullable=False)  # Store as JSON array
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="vectors")


class SocialMediaAccount(Base):
    """Model for social media accounts."""
    
    __tablename__ = "social_media_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    politician_id = Column(Integer, ForeignKey("politicians.id"))
    platform = Column(String(50), nullable=False)  # twitter, facebook, instagram, etc.
    username = Column(String(100), nullable=False)
    user_id = Column(String(100))  # Platform-specific user ID
    url = Column(String(500))
    followers_count = Column(Integer)
    following_count = Column(Integer)
    verified = Column(Boolean, default=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    politician = relationship("Politician", back_populates="social_media_accounts")
    posts = relationship("SocialMediaPost", back_populates="account")


class SocialMediaPost(Base):
    """Model for social media posts."""
    
    __tablename__ = "social_media_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("social_media_accounts.id"))
    post_id = Column(String(100), nullable=False)  # Platform-specific post ID
    content = Column(Text, nullable=False)
    posted_date = Column(DateTime, nullable=False)
    likes_count = Column(Integer, default=0)
    retweets_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    sentiment_score = Column(Float)
    metadata = Column(JSON)
    
    # Relationships
    account = relationship("SocialMediaAccount", back_populates="posts")


class PoliticianReport(Base):
    """Model for generated politician reports."""
    
    __tablename__ = "politician_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    politician_id = Column(Integer, ForeignKey("politicians.id"))
    report_type = Column(String(50), nullable=False)  # profile, kpi, comparison, etc.
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    data = Column(JSON)  # Structured report data
    generated_date = Column(DateTime, default=datetime.utcnow)
    version = Column(String(20), default="1.0")
    
    # Relationships
    politician = relationship("Politician", back_populates="reports")


class KnowledgeGraphNode(Base):
    """Model for knowledge graph nodes."""
    
    __tablename__ = "knowledge_graph_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(100), unique=True, nullable=False)
    node_type = Column(String(50), nullable=False)  # politician, bill, organization, etc.
    name = Column(String(200), nullable=False)
    properties = Column(JSON)
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeGraphRelationship(Base):
    """Model for knowledge graph relationships."""
    
    __tablename__ = "knowledge_graph_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(String(100), nullable=False)
    target_node_id = Column(String(100), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # sponsors, opposes, etc.
    properties = Column(JSON)
    strength = Column(Float, default=1.0)
    created_date = Column(DateTime, default=datetime.utcnow)


class CrawlJob(Base):
    """Model for crawling jobs."""
    
    __tablename__ = "crawl_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(100), nullable=False)
    target_urls = Column(JSON)  # List of URLs to crawl
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    documents_found = Column(Integer, default=0)
    documents_processed = Column(Integer, default=0)
    started_date = Column(DateTime)
    completed_date = Column(DateTime)
    error_message = Column(Text)
    configuration = Column(JSON)