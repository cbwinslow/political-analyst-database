"""Document ingestion module for processing crawled documents."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database.models import Document, CrawlJob
from ..crawling.crawler import CrawledDocument
from ..core.config import settings


class DocumentIngestor:
    """Handles ingestion of crawled documents into the database."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def ingest_document(self, crawled_doc: CrawledDocument) -> Optional[Document]:
        """Ingest a single crawled document into the database."""
        try:
            # Check if document already exists
            existing_doc = self.db.query(Document).filter(
                Document.url == crawled_doc.url
            ).first()
            
            if existing_doc:
                # Update existing document if content has changed
                if existing_doc.content != crawled_doc.content:
                    existing_doc.content = crawled_doc.content
                    existing_doc.title = crawled_doc.title
                    existing_doc.metadata = crawled_doc.metadata
                    existing_doc.crawled_date = datetime.utcnow()
                    self.db.commit()
                    return existing_doc
                else:
                    return existing_doc
            
            # Create new document
            document = Document(
                title=crawled_doc.title,
                content=crawled_doc.content,
                url=crawled_doc.url,
                document_type=crawled_doc.document_type,
                source=crawled_doc.source,
                published_date=crawled_doc.published_date,
                metadata=crawled_doc.metadata or {}
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            return document
            
        except IntegrityError as e:
            self.db.rollback()
            print(f"Integrity error ingesting document {crawled_doc.url}: {e}")
            return None
        except Exception as e:
            self.db.rollback()
            print(f"Error ingesting document {crawled_doc.url}: {e}")
            return None
    
    def ingest_documents(self, crawled_docs: List[CrawledDocument]) -> List[Document]:
        """Ingest multiple crawled documents into the database."""
        ingested_docs = []
        
        for crawled_doc in crawled_docs:
            document = self.ingest_document(crawled_doc)
            if document:
                ingested_docs.append(document)
        
        return ingested_docs
    
    def create_crawl_job(self, job_name: str, target_urls: List[str], 
                        configuration: Optional[Dict[str, Any]] = None) -> CrawlJob:
        """Create a new crawl job record."""
        crawl_job = CrawlJob(
            job_name=job_name,
            target_urls=target_urls,
            configuration=configuration or {},
            started_date=datetime.utcnow()
        )
        
        self.db.add(crawl_job)
        self.db.commit()
        self.db.refresh(crawl_job)
        
        return crawl_job
    
    def update_crawl_job(self, job_id: int, status: str, 
                        documents_found: Optional[int] = None,
                        documents_processed: Optional[int] = None,
                        error_message: Optional[str] = None) -> Optional[CrawlJob]:
        """Update a crawl job's status and metrics."""
        crawl_job = self.db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        
        if not crawl_job:
            return None
        
        crawl_job.status = status
        
        if documents_found is not None:
            crawl_job.documents_found = documents_found
        
        if documents_processed is not None:
            crawl_job.documents_processed = documents_processed
        
        if error_message:
            crawl_job.error_message = error_message
        
        if status in ['completed', 'failed']:
            crawl_job.completed_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(crawl_job)
        
        return crawl_job
    
    def get_recent_documents(self, limit: int = 100) -> List[Document]:
        """Get recently ingested documents."""
        return self.db.query(Document).order_by(
            Document.crawled_date.desc()
        ).limit(limit).all()
    
    def get_documents_by_source(self, source: str, limit: int = 100) -> List[Document]:
        """Get documents from a specific source."""
        return self.db.query(Document).filter(
            Document.source == source
        ).order_by(
            Document.crawled_date.desc()
        ).limit(limit).all()
    
    def get_documents_by_type(self, doc_type: str, limit: int = 100) -> List[Document]:
        """Get documents of a specific type."""
        return self.db.query(Document).filter(
            Document.document_type == doc_type
        ).order_by(
            Document.crawled_date.desc()
        ).limit(limit).all()
    
    def get_unprocessed_documents(self, limit: int = 100) -> List[Document]:
        """Get documents that haven't been analyzed yet."""
        # Documents without any analyses
        return self.db.query(Document).filter(
            ~Document.analyses.any()
        ).order_by(
            Document.crawled_date.desc()
        ).limit(limit).all()
    
    def get_documents_without_vectors(self, limit: int = 100) -> List[Document]:
        """Get documents that haven't been vectorized yet."""
        return self.db.query(Document).filter(
            ~Document.vectors.any()
        ).order_by(
            Document.crawled_date.desc()
        ).limit(limit).all()
    
    def delete_document(self, document_id: int) -> bool:
        """Soft delete a document by marking it as deleted."""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            return False
        
        document.status = "deleted"
        self.db.commit()
        
        return True
    
    def get_crawl_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[CrawlJob]:
        """Get crawl jobs, optionally filtered by status."""
        query = self.db.query(CrawlJob)
        
        if status:
            query = query.filter(CrawlJob.status == status)
        
        return query.order_by(CrawlJob.started_date.desc()).limit(limit).all()


class DocumentProcessor:
    """Processes documents for additional metadata extraction."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def extract_metadata(self, document: Document) -> Dict[str, Any]:
        """Extract additional metadata from document content."""
        metadata = document.metadata.copy() if document.metadata else {}
        
        # Extract basic statistics
        content = document.content
        metadata.update({
            'word_count': len(content.split()),
            'character_count': len(content),
            'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
            'processed_date': datetime.utcnow().isoformat()
        })
        
        # Extract bill numbers and references
        import re
        
        # Look for bill references (H.R. 1234, S. 567, etc.)
        bill_pattern = r'\b(?:H\.R\.|S\.|H\.J\.Res\.|S\.J\.Res\.|H\.Con\.Res\.|S\.Con\.Res\.)\s*\d+'
        bill_refs = re.findall(bill_pattern, content, re.IGNORECASE)
        if bill_refs:
            metadata['referenced_bills'] = list(set(bill_refs))
        
        # Look for congress session references
        congress_pattern = r'\b(?:117th|118th|119th)\s+Congress\b'
        congress_refs = re.findall(congress_pattern, content, re.IGNORECASE)
        if congress_refs:
            metadata['congress_sessions'] = list(set(congress_refs))
        
        # Look for committee references
        committee_pattern = r'\bCommittee on [A-Za-z\s,]+(?=\b(?:and|,|\.|\s*$))'
        committee_refs = re.findall(committee_pattern, content)
        if committee_refs:
            metadata['committees'] = list(set(committee_refs))
        
        return metadata
    
    def update_document_metadata(self, document: Document) -> Document:
        """Update a document with extracted metadata."""
        new_metadata = self.extract_metadata(document)
        document.metadata = new_metadata
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def process_documents_batch(self, documents: List[Document]) -> List[Document]:
        """Process a batch of documents for metadata extraction."""
        processed_docs = []
        
        for document in documents:
            try:
                processed_doc = self.update_document_metadata(document)
                processed_docs.append(processed_doc)
            except Exception as e:
                print(f"Error processing document {document.id}: {e}")
        
        return processed_docs


class IngestionPipeline:
    """Coordinates the entire document ingestion pipeline."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.ingestor = DocumentIngestor(db_session)
        self.processor = DocumentProcessor(db_session)
    
    def run_full_ingestion(self, crawled_docs: List[CrawledDocument], 
                          job_name: str = "Manual Ingestion") -> Dict[str, Any]:
        """Run the complete ingestion pipeline."""
        # Create crawl job
        crawl_job = self.ingestor.create_crawl_job(
            job_name=job_name,
            target_urls=[doc.url for doc in crawled_docs]
        )
        
        try:
            # Update job status
            self.ingestor.update_crawl_job(
                crawl_job.id, 
                "running", 
                documents_found=len(crawled_docs)
            )
            
            # Ingest documents
            ingested_docs = self.ingestor.ingest_documents(crawled_docs)
            
            # Process documents for metadata
            processed_docs = self.processor.process_documents_batch(ingested_docs)
            
            # Update job completion
            self.ingestor.update_crawl_job(
                crawl_job.id,
                "completed",
                documents_processed=len(processed_docs)
            )
            
            return {
                "job_id": crawl_job.id,
                "status": "completed",
                "documents_found": len(crawled_docs),
                "documents_ingested": len(ingested_docs),
                "documents_processed": len(processed_docs)
            }
            
        except Exception as e:
            # Update job with error
            self.ingestor.update_crawl_job(
                crawl_job.id,
                "failed",
                error_message=str(e)
            )
            
            return {
                "job_id": crawl_job.id,
                "status": "failed",
                "error": str(e)
            }