"""FastAPI application for the political analyst database."""

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..database import get_db, create_tables
from ..database.models import Document, Politician, Entity
from ..core.config import settings
from .schemas import (
    DocumentResponse, PoliticianResponse, EntityResponse,
    CrawlJobRequest, AnalysisRequest, SearchRequest
)
from .routes import documents, politicians, entities, analysis, crawling

# Create FastAPI app
app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description="A comprehensive political document analysis system",
    debug=settings.app.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(politicians.router, prefix="/api/v1/politicians", tags=["politicians"])
app.include_router(entities.router, prefix="/api/v1/entities", tags=["entities"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(crawling.router, prefix="/api/v1/crawling", tags=["crawling"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        create_tables()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Political Analyst Database API",
        "version": settings.app.version,
        "docs": "/docs",
        "endpoints": {
            "documents": "/api/v1/documents",
            "politicians": "/api/v1/politicians",
            "entities": "/api/v1/entities",
            "analysis": "/api/v1/analysis",
            "crawling": "/api/v1/crawling"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app.version
    }


@app.get("/api/v1/stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics."""
    try:
        document_count = db.query(Document).count()
        politician_count = db.query(Politician).count()
        entity_count = db.query(Entity).count()
        
        return {
            "total_documents": document_count,
            "total_politicians": politician_count,
            "total_entities": entity_count,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "political_analyst.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app.debug
    )