"""Document vectorization module for creating embeddings."""

import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
import chromadb
from chromadb.config import Settings
import json
from datetime import datetime

from ..database.models import Document, DocumentVector
from ..core.config import settings


class EmbeddingGenerator:
    """Generates embeddings for text documents."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.vector.embedding_model
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            print(f"Error loading model {self.model_name}: {e}")
            # Fallback to a smaller model
            self.model_name = "all-MiniLM-L6-v2"
            self.model = SentenceTransformer(self.model_name)
            print(f"Loaded fallback model: {self.model_name}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        try:
            # Clean and prepare text
            text = self._preprocess_text(text)
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(self.model.get_sentence_embedding_dimension())
    
    def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        try:
            # Clean and prepare texts
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # Generate embeddings in batch
            embeddings = self.model.encode(processed_texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            # Return zero vectors as fallback
            dim = self.model.get_sentence_embedding_dimension()
            return [np.zeros(dim) for _ in texts]
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before embedding generation."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long (models have limits)
        max_length = 512  # Most models work well with this length
        if len(text.split()) > max_length:
            text = " ".join(text.split()[:max_length])
        
        return text
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model."""
        return self.model.get_sentence_embedding_dimension()


class VectorDatabase:
    """Manages vector storage and similarity search using ChromaDB."""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection."""
        try:
            self.client = chromadb.PersistentClient(
                path=settings.vector.chroma_persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.vector.collection_name,
                metadata={"description": "Political document embeddings"}
            )
            
            print(f"Initialized ChromaDB collection: {settings.vector.collection_name}")
            
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            self.client = None
            self.collection = None
    
    def add_documents(self, document_ids: List[str], embeddings: List[List[float]], 
                     texts: List[str], metadatas: List[Dict[str, Any]]):
        """Add documents to the vector database."""
        if not self.collection:
            print("ChromaDB collection not initialized")
            return False
        
        try:
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                ids=document_ids,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            return False
    
    def search_similar(self, query_embedding: List[float], n_results: int = 10) -> List[Dict]:
        """Search for similar documents using embedding."""
        if not self.collection:
            print("ChromaDB collection not initialized")
            return []
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': doc_id,
                        'document': results['documents'][0][i] if results['documents'] else "",
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0.0
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching ChromaDB: {e}")
            return []
    
    def get_collection_count(self) -> int:
        """Get the number of documents in the collection."""
        if not self.collection:
            return 0
        
        try:
            return self.collection.count()
        except Exception as e:
            print(f"Error getting collection count: {e}")
            return 0


class DocumentVectorizer:
    """Handles vectorization of documents in the database."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.embedding_generator = EmbeddingGenerator()
        self.vector_db = VectorDatabase()
    
    def vectorize_document(self, document: Document) -> Optional[DocumentVector]:
        """Vectorize a single document and store in database."""
        try:
            # Generate embedding
            embedding = self.embedding_generator.generate_embedding(document.content)
            
            # Check if vector already exists for this document and model
            existing_vector = self.db.query(DocumentVector).filter(
                DocumentVector.document_id == document.id,
                DocumentVector.embedding_model == self.embedding_generator.model_name
            ).first()
            
            if existing_vector:
                # Update existing vector
                existing_vector.vector_data = embedding.tolist()
                existing_vector.created_date = datetime.utcnow()
                self.db.commit()
                self.db.refresh(existing_vector)
                doc_vector = existing_vector
            else:
                # Create new vector
                doc_vector = DocumentVector(
                    document_id=document.id,
                    embedding_model=self.embedding_generator.model_name,
                    vector_data=embedding.tolist()
                )
                
                self.db.add(doc_vector)
                self.db.commit()
                self.db.refresh(doc_vector)
            
            # Add to ChromaDB
            self.vector_db.add_documents(
                document_ids=[str(document.id)],
                embeddings=[embedding.tolist()],
                texts=[document.content[:1000]],  # Truncate for storage
                metadatas=[{
                    'title': document.title,
                    'source': document.source,
                    'document_type': document.document_type,
                    'url': document.url,
                    'created_date': document.crawled_date.isoformat() if document.crawled_date else None
                }]
            )
            
            return doc_vector
            
        except Exception as e:
            self.db.rollback()
            print(f"Error vectorizing document {document.id}: {e}")
            return None
    
    def vectorize_documents_batch(self, documents: List[Document]) -> List[DocumentVector]:
        """Vectorize multiple documents in batch."""
        if not documents:
            return []
        
        try:
            # Prepare texts for batch processing
            texts = [doc.content for doc in documents]
            
            # Generate embeddings in batch
            embeddings = self.embedding_generator.generate_embeddings(texts)
            
            doc_vectors = []
            chroma_ids = []
            chroma_embeddings = []
            chroma_texts = []
            chroma_metadatas = []
            
            for i, (document, embedding) in enumerate(zip(documents, embeddings)):
                try:
                    # Check if vector already exists
                    existing_vector = self.db.query(DocumentVector).filter(
                        DocumentVector.document_id == document.id,
                        DocumentVector.embedding_model == self.embedding_generator.model_name
                    ).first()
                    
                    if existing_vector:
                        # Update existing vector
                        existing_vector.vector_data = embedding.tolist()
                        existing_vector.created_date = datetime.utcnow()
                        doc_vector = existing_vector
                    else:
                        # Create new vector
                        doc_vector = DocumentVector(
                            document_id=document.id,
                            embedding_model=self.embedding_generator.model_name,
                            vector_data=embedding.tolist()
                        )
                        self.db.add(doc_vector)
                    
                    doc_vectors.append(doc_vector)
                    
                    # Prepare for ChromaDB batch insert
                    chroma_ids.append(str(document.id))
                    chroma_embeddings.append(embedding.tolist())
                    chroma_texts.append(document.content[:1000])
                    chroma_metadatas.append({
                        'title': document.title,
                        'source': document.source,
                        'document_type': document.document_type,
                        'url': document.url,
                        'created_date': document.crawled_date.isoformat() if document.crawled_date else None
                    })
                    
                except Exception as e:
                    print(f"Error processing document {document.id}: {e}")
                    continue
            
            # Commit database changes
            self.db.commit()
            
            # Refresh all objects
            for doc_vector in doc_vectors:
                self.db.refresh(doc_vector)
            
            # Add to ChromaDB in batch
            if chroma_ids:
                self.vector_db.add_documents(
                    document_ids=chroma_ids,
                    embeddings=chroma_embeddings,
                    texts=chroma_texts,
                    metadatas=chroma_metadatas
                )
            
            return doc_vectors
            
        except Exception as e:
            self.db.rollback()
            print(f"Error in batch vectorization: {e}")
            return []
    
    def find_similar_documents(self, query_text: str, n_results: int = 10) -> List[Dict]:
        """Find documents similar to a query text."""
        try:
            # Generate embedding for query
            query_embedding = self.embedding_generator.generate_embedding(query_text)
            
            # Search in ChromaDB
            results = self.vector_db.search_similar(
                query_embedding.tolist(), 
                n_results=n_results
            )
            
            # Enrich results with database information
            enriched_results = []
            for result in results:
                try:
                    doc_id = int(result['id'])
                    document = self.db.query(Document).filter(Document.id == doc_id).first()
                    
                    if document:
                        enriched_results.append({
                            'document_id': doc_id,
                            'title': document.title,
                            'content_preview': document.content[:200] + "...",
                            'source': document.source,
                            'document_type': document.document_type,
                            'url': document.url,
                            'similarity_score': 1 - result['distance'],  # Convert distance to similarity
                            'metadata': result['metadata']
                        })
                except Exception as e:
                    print(f"Error enriching result: {e}")
                    continue
            
            return enriched_results
            
        except Exception as e:
            print(f"Error finding similar documents: {e}")
            return []
    
    def get_vectorization_stats(self) -> Dict[str, Any]:
        """Get statistics about vectorization progress."""
        try:
            total_docs = self.db.query(Document).count()
            vectorized_docs = self.db.query(DocumentVector).filter(
                DocumentVector.embedding_model == self.embedding_generator.model_name
            ).count()
            
            chroma_count = self.vector_db.get_collection_count()
            
            return {
                'total_documents': total_docs,
                'vectorized_documents': vectorized_docs,
                'vectorization_progress': vectorized_docs / total_docs if total_docs > 0 else 0,
                'chroma_documents': chroma_count,
                'embedding_model': self.embedding_generator.model_name,
                'embedding_dimension': self.embedding_generator.get_embedding_dimension()
            }
            
        except Exception as e:
            print(f"Error getting vectorization stats: {e}")
            return {}


class VectorizationPipeline:
    """Coordinates the vectorization pipeline."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.vectorizer = DocumentVectorizer(db_session)
    
    def run_vectorization(self, batch_size: int = 50) -> Dict[str, Any]:
        """Run vectorization on all unvectorized documents."""
        try:
            # Get documents that haven't been vectorized
            unvectorized_docs = self.db.query(Document).filter(
                ~Document.vectors.any()
            ).all()
            
            if not unvectorized_docs:
                return {
                    'status': 'completed',
                    'message': 'All documents already vectorized',
                    'documents_processed': 0
                }
            
            print(f"Found {len(unvectorized_docs)} documents to vectorize")
            
            # Process in batches
            total_processed = 0
            for i in range(0, len(unvectorized_docs), batch_size):
                batch = unvectorized_docs[i:i+batch_size]
                processed_vectors = self.vectorizer.vectorize_documents_batch(batch)
                total_processed += len(processed_vectors)
                
                print(f"Processed batch {i//batch_size + 1}: {len(processed_vectors)} documents")
            
            # Get final stats
            stats = self.vectorizer.get_vectorization_stats()
            
            return {
                'status': 'completed',
                'documents_processed': total_processed,
                'total_documents': stats['total_documents'],
                'vectorization_progress': stats['vectorization_progress'],
                'stats': stats
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'documents_processed': 0
            }