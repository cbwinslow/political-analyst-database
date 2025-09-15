"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentBase(BaseModel):
    """Base document schema."""
    title: str
    content: str
    url: str
    document_type: str
    source: str
    published_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    """Schema for creating documents."""
    pass


class DocumentResponse(DocumentBase):
    """Schema for document responses."""
    id: int
    crawled_date: datetime
    status: str
    
    class Config:
        from_attributes = True


class PoliticianBase(BaseModel):
    """Base politician schema."""
    name: str
    party: Optional[str] = None
    position: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    website_url: Optional[str] = None


class PoliticianCreate(PoliticianBase):
    """Schema for creating politicians."""
    pass


class PoliticianResponse(PoliticianBase):
    """Schema for politician responses."""
    id: int
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True


class EntityBase(BaseModel):
    """Base entity schema."""
    name: str
    entity_type: str
    description: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class EntityCreate(EntityBase):
    """Schema for creating entities."""
    pass


class EntityResponse(EntityBase):
    """Schema for entity responses."""
    id: int
    
    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    """Schema for analysis responses."""
    id: int
    document_id: int
    analysis_type: str
    result: Dict[str, Any]
    confidence_score: Optional[float] = None
    created_date: datetime
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Schema for search requests."""
    query: str
    limit: Optional[int] = Field(default=10, ge=1, le=100)
    source: Optional[str] = None
    document_type: Optional[str] = None


class SearchResponse(BaseModel):
    """Schema for search responses."""
    documents: List[Dict[str, Any]]
    total_results: int
    query: str


class CrawlJobRequest(BaseModel):
    """Schema for crawl job requests."""
    job_name: str
    target_urls: List[str]
    configuration: Optional[Dict[str, Any]] = None


class CrawlJobResponse(BaseModel):
    """Schema for crawl job responses."""
    id: int
    job_name: str
    target_urls: List[str]
    status: str
    documents_found: int
    documents_processed: int
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    """Schema for analysis requests."""
    document_ids: Optional[List[int]] = None
    analysis_types: Optional[List[str]] = None
    batch_size: Optional[int] = Field(default=50, ge=1, le=100)


class VectorizationRequest(BaseModel):
    """Schema for vectorization requests."""
    document_ids: Optional[List[int]] = None
    batch_size: Optional[int] = Field(default=50, ge=1, le=100)


class SocialMediaAccountRequest(BaseModel):
    """Schema for social media account requests."""
    politician_id: int
    platform: str
    username: str


class SocialMediaAccountResponse(BaseModel):
    """Schema for social media account responses."""
    id: int
    politician_id: int
    platform: str
    username: str
    url: Optional[str] = None
    followers_count: int
    following_count: int
    verified: bool
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True


class ReportRequest(BaseModel):
    """Schema for report generation requests."""
    politician_id: int
    report_type: str
    title: str
    data: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """Schema for report responses."""
    id: int
    politician_id: int
    report_type: str
    title: str
    content: str
    data: Optional[Dict[str, Any]] = None
    generated_date: datetime
    version: str
    
    class Config:
        from_attributes = True


class KnowledgeGraphNodeResponse(BaseModel):
    """Schema for knowledge graph node responses."""
    id: int
    node_id: str
    node_type: str
    name: str
    properties: Optional[Dict[str, Any]] = None
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True


class KnowledgeGraphRelationshipResponse(BaseModel):
    """Schema for knowledge graph relationship responses."""
    id: int
    source_node_id: str
    target_node_id: str
    relationship_type: str
    properties: Optional[Dict[str, Any]] = None
    strength: float
    created_date: datetime
    
    class Config:
        from_attributes = True


class PipelineStatusResponse(BaseModel):
    """Schema for pipeline status responses."""
    status: str
    message: Optional[str] = None
    documents_processed: int
    total_documents: Optional[int] = None
    progress: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None