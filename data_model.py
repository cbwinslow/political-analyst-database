# ==============================================================================
# Political Intelligence Platform - Pydantic Schemas
# ==============================================================================
# This file defines the core data structures for the application using Pydantic.
# These models are used for API request/response validation, data serialization,
# and ensuring type safety between different services.
# ==============================================================================

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional, Literal
from datetime import date, datetime
from uuid import UUID

# --- Enum-like Literals for strict validation ---
Chamber = Literal['House', 'Senate', 'Joint']
Party = Literal['Democrat', 'Republican', 'Independent', 'Other']
VotePosition = Literal['Yea', 'Nay', 'Abstain', 'Not Voting']
SocialPlatform = Literal['Twitter', 'Facebook', 'Other']
SourceType = Literal['bill_summary', 'bill_text', 'post_text', 'committee_report']

# --- Base Models with common fields ---
class TimeStampedModel(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# --- Core Data Models ---

class Legislator(TimeStampedModel):
    id: str = Field(..., description="Unique identifier, e.g., bioguideId")
    first_name: str
    last_name: str
    party: Optional[Party] = None
    chamber: Optional[Chamber] = None
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    district: Optional[int] = None
    contact_url: Optional[HttpUrl] = None
    social_media_handles: Optional[Dict[str, str]] = Field(default_factory=dict)

class Bill(TimeStampedModel):
    id: str = Field(..., description="Unique identifier, e.g., 'hr123-118'")
    bill_number: str
    congress: int
    title: str
    summary: Optional[str] = None
    introduced_date: Optional[date] = None
    latest_action_date: Optional[date] = None
    latest_action_text: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    raw_text: Optional[str] = None

class Vote(TimeStampedModel):
    id: str = Field(..., description="Unique identifier for the roll call vote")
    roll_call_number: int
    date: Optional[datetime] = None
    chamber: Optional[Chamber] = None
    question: Optional[str] = None
    result: Optional[str] = None
    bill_id: Optional[str] = None

class LegislatorVote(BaseModel):
    legislator_id: str
    vote_id: str
    position: VotePosition

class SocialMediaPost(BaseModel):
    id: str = Field(..., description="Unique identifier for the post, e.g., tweet ID")
    legislator_id: str
    platform: SocialPlatform
    post_text: str
    post_timestamp: Optional[datetime] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None

class Embedding(BaseModel):
    id: Optional[UUID] = None
    source_id: str
    source_type: SourceType
    text_chunk: Optional[str] = None
    embedding: List[float]

# --- API Request/Response Models ---

class IngestRequest(BaseModel):
    title: str
    content: str
    metadata: dict = {}

class CrawlRequest(BaseModel):
    url: HttpUrl
    max_depth: int = Field(0, ge=0)
