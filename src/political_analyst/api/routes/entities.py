"""Entities API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from ...database import get_db
from ...database.models import Entity, DocumentEntity
from ...entities import PoliticalEntityExtractor
from ..schemas import EntityResponse

router = APIRouter()


@router.get("/", response_model=List[EntityResponse])
async def get_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of entities with optional filtering."""
    query = db.query(Entity)
    
    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)
    
    entities = query.offset(skip).limit(limit).all()
    return entities


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: int, db: Session = Depends(get_db)):
    """Get a specific entity by ID."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return entity


@router.get("/statistics")
async def get_entity_statistics(db: Session = Depends(get_db)):
    """Get entity statistics."""
    try:
        extractor = PoliticalEntityExtractor(db)
        stats = extractor.get_entity_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_id}/documents")
async def get_entity_documents(
    entity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get documents that mention a specific entity."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    document_entities = (
        db.query(DocumentEntity)
        .filter(DocumentEntity.entity_id == entity_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        {
            "document_id": doc_entity.document.id,
            "document_title": doc_entity.document.title,
            "document_type": doc_entity.document.document_type,
            "source": doc_entity.document.source,
            "mention_count": doc_entity.mention_count,
            "context": doc_entity.context,
            "sentiment": doc_entity.sentiment
        }
        for doc_entity in document_entities
    ]


@router.get("/{entity_id}/related")
async def get_related_entities(
    entity_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get entities related to a specific entity."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    try:
        extractor = PoliticalEntityExtractor(db)
        related_entities = extractor.find_related_entities(entity.name, limit=limit)
        return related_entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_entity_types(db: Session = Depends(get_db)):
    """Get all unique entity types."""
    entity_types = (
        db.query(Entity.entity_type, func.count(Entity.id).label('count'))
        .group_by(Entity.entity_type)
        .all()
    )
    
    return [
        {
            "entity_type": entity_type,
            "count": count
        }
        for entity_type, count in entity_types
    ]


@router.get("/search")
async def search_entities(
    q: str = Query(..., min_length=1),
    entity_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search entities by name."""
    query = db.query(Entity).filter(Entity.name.ilike(f"%{q}%"))
    
    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)
    
    entities = query.limit(limit).all()
    
    return [
        {
            "id": entity.id,
            "name": entity.name,
            "entity_type": entity.entity_type,
            "confidence_score": entity.confidence_score
        }
        for entity in entities
    ]