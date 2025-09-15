"""Analysis API routes."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database import get_db
from ...analysis import AnalysisPipeline, DocumentAnalyzer
from ...vectorization import VectorizationPipeline
from ..schemas import AnalysisRequest, VectorizationRequest, PipelineStatusResponse

router = APIRouter()


@router.post("/analyze", response_model=PipelineStatusResponse)
async def run_analysis_pipeline(
    background_tasks: BackgroundTasks,
    analysis_request: AnalysisRequest = AnalysisRequest(),
    db: Session = Depends(get_db)
):
    """Run document analysis pipeline."""
    try:
        # Run analysis in background
        def run_analysis():
            pipeline = AnalysisPipeline(db)
            return pipeline.run_analysis(batch_size=analysis_request.batch_size)
        
        background_tasks.add_task(run_analysis)
        
        return PipelineStatusResponse(
            status="started",
            message="Analysis pipeline started in background",
            documents_processed=0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vectorize", response_model=PipelineStatusResponse)
async def run_vectorization_pipeline(
    background_tasks: BackgroundTasks,
    vectorization_request: VectorizationRequest = VectorizationRequest(),
    db: Session = Depends(get_db)
):
    """Run document vectorization pipeline."""
    try:
        # Run vectorization in background
        def run_vectorization():
            pipeline = VectorizationPipeline(db)
            return pipeline.run_vectorization(batch_size=vectorization_request.batch_size)
        
        background_tasks.add_task(run_vectorization)
        
        return PipelineStatusResponse(
            status="started",
            message="Vectorization pipeline started in background",
            documents_processed=0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment-trends")
async def get_sentiment_trends(
    source: Optional[str] = None,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get sentiment trends across documents."""
    try:
        analyzer = DocumentAnalyzer(db)
        trends = analyzer.get_sentiment_trends(source=source, document_type=document_type)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{document_id}/summary")
async def get_document_analysis_summary(document_id: int, db: Session = Depends(get_db)):
    """Get analysis summary for a specific document."""
    try:
        analyzer = DocumentAnalyzer(db)
        summary = analyzer.get_analysis_summary(document_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="No analysis found for document")
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vectorization/stats")
async def get_vectorization_stats(db: Session = Depends(get_db)):
    """Get vectorization statistics."""
    try:
        from ...vectorization import DocumentVectorizer
        vectorizer = DocumentVectorizer(db)
        stats = vectorizer.get_vectorization_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))