"""Entity extraction and management module."""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import spacy
import re
from collections import defaultdict, Counter

from ..database.models import (
    Document, Entity, DocumentEntity, Politician, 
    PoliticianEntity, DocumentAnalysis
)
from ..core.config import settings


class PoliticalEntityExtractor:
    """Extracts and manages political entities from documents."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.nlp = None
        self._load_spacy()
        
        # Known political entities and patterns
        self.politician_patterns = self._load_politician_patterns()
        self.organization_patterns = self._load_organization_patterns()
        self.legislation_patterns = self._load_legislation_patterns()
    
    def _load_spacy(self):
        """Load spaCy model for entity recognition."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def _load_politician_patterns(self) -> List[Dict[str, Any]]:
        """Load known politician name patterns."""
        # In a real system, this would come from a comprehensive database
        politicians = [
            {"name": "Joe Biden", "titles": ["President", "Senator"], "party": "Democratic"},
            {"name": "Donald Trump", "titles": ["President", "Former President"], "party": "Republican"},
            {"name": "Nancy Pelosi", "titles": ["Speaker", "Representative"], "party": "Democratic"},
            {"name": "Mitch McConnell", "titles": ["Senator", "Minority Leader"], "party": "Republican"},
            {"name": "Chuck Schumer", "titles": ["Senator", "Majority Leader"], "party": "Democratic"},
            {"name": "Kevin McCarthy", "titles": ["Representative", "Speaker"], "party": "Republican"},
        ]
        
        # Create regex patterns
        patterns = []
        for pol in politicians:
            # Create variations of names
            name_parts = pol["name"].split()
            if len(name_parts) >= 2:
                patterns.append({
                    "pattern": re.compile(rf'\b{re.escape(pol["name"])}\b', re.IGNORECASE),
                    "name": pol["name"],
                    "entity_type": "POLITICIAN",
                    "metadata": pol
                })
                
                # Also match with titles
                for title in pol["titles"]:
                    patterns.append({
                        "pattern": re.compile(rf'\b{re.escape(title)}\s+{re.escape(pol["name"])}\b', re.IGNORECASE),
                        "name": f"{title} {pol['name']}",
                        "canonical_name": pol["name"],
                        "entity_type": "POLITICIAN",
                        "metadata": pol
                    })
        
        return patterns
    
    def _load_organization_patterns(self) -> List[Dict[str, Any]]:
        """Load known political organization patterns."""
        organizations = [
            "House of Representatives",
            "Senate",
            "Congress",
            "Supreme Court",
            "Department of Justice",
            "Department of Defense",
            "Department of Health and Human Services",
            "Centers for Disease Control",
            "Federal Bureau of Investigation",
            "Central Intelligence Agency",
            "National Security Agency",
            "Democratic Party",
            "Republican Party",
            "Green Party",
            "Libertarian Party"
        ]
        
        patterns = []
        for org in organizations:
            patterns.append({
                "pattern": re.compile(rf'\b{re.escape(org)}\b', re.IGNORECASE),
                "name": org,
                "entity_type": "ORGANIZATION",
                "metadata": {"type": "government" if "Department" in org or "Court" in org else "political"}
            })
        
        return patterns
    
    def _load_legislation_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns for legislation references."""
        patterns = [
            {
                "pattern": re.compile(r'\b(H\.R\.\s*\d+)\b', re.IGNORECASE),
                "entity_type": "LEGISLATION",
                "subtype": "house_bill"
            },
            {
                "pattern": re.compile(r'\b(S\.\s*\d+)\b', re.IGNORECASE),
                "entity_type": "LEGISLATION",
                "subtype": "senate_bill"
            },
            {
                "pattern": re.compile(r'\b(H\.J\.Res\.\s*\d+)\b', re.IGNORECASE),
                "entity_type": "LEGISLATION",
                "subtype": "house_joint_resolution"
            },
            {
                "pattern": re.compile(r'\b(S\.J\.Res\.\s*\d+)\b', re.IGNORECASE),
                "entity_type": "LEGISLATION",
                "subtype": "senate_joint_resolution"
            },
            {
                "pattern": re.compile(r'\b(H\.Con\.Res\.\s*\d+)\b', re.IGNORECASE),
                "entity_type": "LEGISLATION",
                "subtype": "house_concurrent_resolution"
            },
            {
                "pattern": re.compile(r'\b(S\.Con\.Res\.\s*\d+)\b', re.IGNORECASE),
                "entity_type": "LEGISLATION",
                "subtype": "senate_concurrent_resolution"
            }
        ]
        
        return patterns
    
    def extract_entities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract all entities from text."""
        entities = []
        
        # Extract using spaCy NER
        if self.nlp:
            spacy_entities = self._extract_spacy_entities(text)
            entities.extend(spacy_entities)
        
        # Extract using pattern matching
        pattern_entities = self._extract_pattern_entities(text)
        entities.extend(pattern_entities)
        
        # Deduplicate and merge entities
        entities = self._deduplicate_entities(entities)
        
        return entities
    
    def _extract_spacy_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using spaCy NER."""
        entities = []
        doc = self.nlp(text)
        
        for ent in doc.ents:
            entity_info = {
                "name": ent.text,
                "entity_type": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 0.8,  # spaCy doesn't provide confidence scores
                "source": "spacy",
                "metadata": {"spacy_label": ent.label_}
            }
            entities.append(entity_info)
        
        return entities
    
    def _extract_pattern_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using pattern matching."""
        entities = []
        
        # Extract politicians
        for pattern_info in self.politician_patterns:
            matches = pattern_info["pattern"].finditer(text)
            for match in matches:
                entity_info = {
                    "name": pattern_info.get("canonical_name", pattern_info["name"]),
                    "entity_type": pattern_info["entity_type"],
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.9,
                    "source": "pattern",
                    "metadata": pattern_info["metadata"]
                }
                entities.append(entity_info)
        
        # Extract organizations
        for pattern_info in self.organization_patterns:
            matches = pattern_info["pattern"].finditer(text)
            for match in matches:
                entity_info = {
                    "name": pattern_info["name"],
                    "entity_type": pattern_info["entity_type"],
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.95,
                    "source": "pattern",
                    "metadata": pattern_info["metadata"]
                }
                entities.append(entity_info)
        
        # Extract legislation
        for pattern_info in self.legislation_patterns:
            matches = pattern_info["pattern"].finditer(text)
            for match in matches:
                entity_info = {
                    "name": match.group(1),
                    "entity_type": pattern_info["entity_type"],
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.99,
                    "source": "pattern",
                    "metadata": {"subtype": pattern_info["subtype"]}
                }
                entities.append(entity_info)
        
        return entities
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entities and merge similar ones."""
        # Group entities by normalized name
        entity_groups = defaultdict(list)
        
        for entity in entities:
            normalized_name = entity["name"].lower().strip()
            entity_groups[normalized_name].append(entity)
        
        # Merge entities in each group
        merged_entities = []
        for name, group in entity_groups.items():
            if len(group) == 1:
                merged_entities.append(group[0])
            else:
                # Merge multiple entities with same name
                merged_entity = self._merge_entity_group(group)
                merged_entities.append(merged_entity)
        
        return merged_entities
    
    def _merge_entity_group(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge a group of entities with the same name."""
        # Use the entity with highest confidence as base
        base_entity = max(entities, key=lambda x: x["confidence"])
        
        # Merge metadata
        merged_metadata = {}
        for entity in entities:
            if entity.get("metadata"):
                merged_metadata.update(entity["metadata"])
        
        # Count mentions
        mention_count = len(entities)
        
        base_entity["metadata"] = merged_metadata
        base_entity["mention_count"] = mention_count
        
        return base_entity
    
    def store_entities(self, document: Document, extracted_entities: List[Dict[str, Any]]) -> List[DocumentEntity]:
        """Store extracted entities in the database."""
        document_entities = []
        
        for entity_info in extracted_entities:
            try:
                # Get or create entity
                entity = self._get_or_create_entity(entity_info)
                
                # Create document-entity relationship
                doc_entity = self._create_document_entity(document, entity, entity_info)
                
                if doc_entity:
                    document_entities.append(doc_entity)
                    
            except Exception as e:
                print(f"Error storing entity {entity_info.get('name', 'unknown')}: {e}")
                continue
        
        return document_entities
    
    def _get_or_create_entity(self, entity_info: Dict[str, Any]) -> Entity:
        """Get existing entity or create new one."""
        # Check if entity already exists
        existing_entity = self.db.query(Entity).filter(
            Entity.name == entity_info["name"],
            Entity.entity_type == entity_info["entity_type"]
        ).first()
        
        if existing_entity:
            # Update metadata if needed
            if entity_info.get("metadata"):
                existing_metadata = existing_entity.metadata or {}
                existing_metadata.update(entity_info["metadata"])
                existing_entity.metadata = existing_metadata
                self.db.commit()
            return existing_entity
        
        # Create new entity
        new_entity = Entity(
            name=entity_info["name"],
            entity_type=entity_info["entity_type"],
            confidence_score=entity_info["confidence"],
            metadata=entity_info.get("metadata", {})
        )
        
        self.db.add(new_entity)
        self.db.commit()
        self.db.refresh(new_entity)
        
        return new_entity
    
    def _create_document_entity(self, document: Document, entity: Entity, 
                              entity_info: Dict[str, Any]) -> Optional[DocumentEntity]:
        """Create document-entity relationship."""
        # Check if relationship already exists
        existing_rel = self.db.query(DocumentEntity).filter(
            DocumentEntity.document_id == document.id,
            DocumentEntity.entity_id == entity.id
        ).first()
        
        if existing_rel:
            # Update mention count
            existing_rel.mention_count += entity_info.get("mention_count", 1)
            self.db.commit()
            return existing_rel
        
        # Create new relationship
        doc_entity = DocumentEntity(
            document_id=document.id,
            entity_id=entity.id,
            mention_count=entity_info.get("mention_count", 1),
            context=entity_info.get("context", ""),
            sentiment=0.0  # Will be calculated later
        )
        
        self.db.add(doc_entity)
        self.db.commit()
        self.db.refresh(doc_entity)
        
        return doc_entity
    
    def extract_and_store_entities(self, document: Document) -> List[DocumentEntity]:
        """Extract entities from document and store them."""
        # Extract entities from document content
        extracted_entities = self.extract_entities_from_text(document.content)
        
        # Store entities in database
        document_entities = self.store_entities(document, extracted_entities)
        
        print(f"Extracted {len(extracted_entities)} entities from document {document.id}")
        
        return document_entities
    
    def get_entity_statistics(self) -> Dict[str, Any]:
        """Get statistics about extracted entities."""
        # Count entities by type
        entity_counts = self.db.query(
            Entity.entity_type,
            func.count(Entity.id)
        ).group_by(Entity.entity_type).all()
        
        # Count document-entity relationships
        total_mentions = self.db.query(DocumentEntity).count()
        
        # Get most mentioned entities
        top_entities = self.db.query(
            Entity.name,
            Entity.entity_type,
            func.sum(DocumentEntity.mention_count).label('total_mentions')
        ).join(DocumentEntity).group_by(
            Entity.id, Entity.name, Entity.entity_type
        ).order_by(
            func.sum(DocumentEntity.mention_count).desc()
        ).limit(10).all()
        
        return {
            "entity_counts_by_type": dict(entity_counts),
            "total_entities": sum(count for _, count in entity_counts),
            "total_mentions": total_mentions,
            "top_entities": [
                {
                    "name": name,
                    "type": entity_type,
                    "mention_count": total_mentions
                }
                for name, entity_type, total_mentions in top_entities
            ]
        }
    
    def find_related_entities(self, entity_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find entities that commonly appear with the given entity."""
        # Get the target entity
        target_entity = self.db.query(Entity).filter(Entity.name == entity_name).first()
        
        if not target_entity:
            return []
        
        # Get documents that mention this entity
        target_docs = self.db.query(DocumentEntity.document_id).filter(
            DocumentEntity.entity_id == target_entity.id
        ).subquery()
        
        # Find other entities mentioned in the same documents
        related_entities = self.db.query(
            Entity.name,
            Entity.entity_type,
            func.count(DocumentEntity.document_id).label('co_occurrence_count')
        ).join(DocumentEntity).filter(
            DocumentEntity.document_id.in_(target_docs),
            Entity.id != target_entity.id
        ).group_by(
            Entity.id, Entity.name, Entity.entity_type
        ).order_by(
            func.count(DocumentEntity.document_id).desc()
        ).limit(limit).all()
        
        return [
            {
                "name": name,
                "type": entity_type,
                "co_occurrence_count": count
            }
            for name, entity_type, count in related_entities
        ]


class EntityPipeline:
    """Coordinates entity extraction pipeline."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.extractor = PoliticalEntityExtractor(db_session)
    
    def run_entity_extraction(self, batch_size: int = 50) -> Dict[str, Any]:
        """Run entity extraction on all documents without entities."""
        try:
            # Get documents that haven't had entities extracted
            unprocessed_docs = self.db.query(Document).filter(
                ~Document.entities.any()
            ).all()
            
            if not unprocessed_docs:
                return {
                    'status': 'completed',
                    'message': 'All documents already processed for entities',
                    'documents_processed': 0
                }
            
            print(f"Found {len(unprocessed_docs)} documents to process for entities")
            
            # Process in batches
            total_processed = 0
            total_entities = 0
            
            for i in range(0, len(unprocessed_docs), batch_size):
                batch = unprocessed_docs[i:i+batch_size]
                
                for document in batch:
                    try:
                        document_entities = self.extractor.extract_and_store_entities(document)
                        total_entities += len(document_entities)
                        total_processed += 1
                    except Exception as e:
                        print(f"Error processing document {document.id} for entities: {e}")
                        continue
                
                print(f"Processed batch {i//batch_size + 1}: {len(batch)} documents")
            
            # Get final statistics
            stats = self.extractor.get_entity_statistics()
            
            return {
                'status': 'completed',
                'documents_processed': total_processed,
                'entities_extracted': total_entities,
                'total_documents': len(unprocessed_docs),
                'entity_statistics': stats
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'documents_processed': 0
            }