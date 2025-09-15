"""Documents API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database import get_db
from ...database.models import Document
from ...ingestion import DocumentIngestor
from ...vectorization import DocumentVectorizer
from ..schemas import DocumentResponse, SearchRequest, SearchResponse

router = APIRouter()


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source: Optional[str] = None,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of documents with optional filtering."""
    query = db.query(Document)
    
    if source:
        query = query.filter(Document.source == source)
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
    
    documents = query.offset(skip).limit(limit).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get a specific document by ID."""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Search documents using vector similarity."""
    try:
        vectorizer = DocumentVectorizer(db)
        
        # Find similar documents
        similar_docs = vectorizer.find_similar_documents(
            search_request.query,
            n_results=search_request.limit
        )
        
        return SearchResponse(
            documents=similar_docs,
            total_results=len(similar_docs),
            query=search_request.query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/analyses")
async def get_document_analyses(document_id: int, db: Session = Depends(get_db)):
    """Get all analyses for a specific document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return [
        {
            "id": analysis.id,
            "analysis_type": analysis.analysis_type,
            "result": analysis.result,
            "confidence_score": analysis.confidence_score,
            "created_date": analysis.created_date
        }
        for analysis in document.analyses
    ]


@router.get("/{document_id}/entities")
async def get_document_entities(document_id: int, db: Session = Depends(get_db)):
    """Get all entities mentioned in a specific document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return [
        {
            "entity_id": doc_entity.entity.id,
            "entity_name": doc_entity.entity.name,
            "entity_type": doc_entity.entity.entity_type,
            "mention_count": doc_entity.mention_count,
            "context": doc_entity.context,
            "sentiment": doc_entity.sentiment
        }
        for doc_entity in document.entities
    ]