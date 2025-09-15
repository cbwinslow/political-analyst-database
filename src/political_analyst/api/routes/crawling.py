"""Crawling API routes."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...database.models import CrawlJob
from ...crawling import CrawlerManager
from ...ingestion import IngestionPipeline
from ..schemas import CrawlJobRequest, CrawlJobResponse

router = APIRouter()


@router.post("/start", response_model=CrawlJobResponse)
async def start_crawl_job(
    background_tasks: BackgroundTasks,
    crawl_request: CrawlJobRequest,
    db: Session = Depends(get_db)
):
    """Start a new crawling job."""
    try:
        # Create crawl job record
        from ...ingestion import DocumentIngestor
        ingestor = DocumentIngestor(db)
        
        crawl_job = ingestor.create_crawl_job(
            job_name=crawl_request.job_name,
            target_urls=crawl_request.target_urls,
            configuration=crawl_request.configuration
        )
        
        # Start crawling in background
        def run_crawl_and_ingest():
            try:
                # Update job status
                ingestor.update_crawl_job(crawl_job.id, "running")
                
                # Run crawling (simplified for demo)
                crawler_manager = CrawlerManager()
                # In a real implementation, this would crawl the specific URLs
                # For now, we'll just run the general crawling
                crawled_docs = []  # This would be the actual crawling result
                
                # Run ingestion
                pipeline = IngestionPipeline(db)
                result = pipeline.run_full_ingestion(
                    crawled_docs, 
                    job_name=crawl_request.job_name
                )
                
                # Update job with results
                if result["status"] == "completed":
                    ingestor.update_crawl_job(
                        crawl_job.id,
                        "completed",
                        documents_found=result.get("documents_found", 0),
                        documents_processed=result.get("documents_processed", 0)
                    )
                else:
                    ingestor.update_crawl_job(
                        crawl_job.id,
                        "failed",
                        error_message=result.get("error", "Unknown error")
                    )
                    
            except Exception as e:
                ingestor.update_crawl_job(
                    crawl_job.id,
                    "failed",
                    error_message=str(e)
                )
        
        background_tasks.add_task(run_crawl_and_ingest)
        
        return crawl_job
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[CrawlJobResponse])
async def get_crawl_jobs(
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get list of crawl jobs."""
    try:
        from ...ingestion import DocumentIngestor
        ingestor = DocumentIngestor(db)
        
        jobs = ingestor.get_crawl_jobs(status=status, limit=limit)
        return jobs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=CrawlJobResponse)
async def get_crawl_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific crawl job."""
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    
    return job


@router.post("/quick-crawl")
async def quick_crawl(
    background_tasks: BackgroundTasks,
    source: str = "congress.gov",
    db: Session = Depends(get_db)
):
    """Run a quick crawl of a specific source."""
    try:
        def run_quick_crawl():
            try:
                # Run crawling
                crawler_manager = CrawlerManager()
                
                if source == "all":
                    crawled_docs = crawler_manager.crawl_all_sources()
                else:
                    crawled_docs = crawler_manager.crawl_source(source)
                
                # Run ingestion
                pipeline = IngestionPipeline(db)
                result = pipeline.run_full_ingestion(
                    crawled_docs,
                    job_name=f"Quick crawl - {source}"
                )
                
                print(f"Quick crawl completed: {result}")
                
            except Exception as e:
                print(f"Quick crawl failed: {e}")
        
        background_tasks.add_task(run_quick_crawl)
        
        return {
            "status": "started",
            "message": f"Quick crawl of {source} started in background"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))