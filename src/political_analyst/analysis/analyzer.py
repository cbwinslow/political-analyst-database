"""Document analysis module for extracting insights from political documents."""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import spacy
from textblob import TextBlob
import nltk
from collections import Counter
import json

from ..database.models import Document, DocumentAnalysis
from ..core.config import settings


class SentimentAnalyzer:
    """Analyzes sentiment of political documents."""
    
    def __init__(self):
        self.nlp = None
        self._load_models()
    
    def _load_models(self):
        """Load NLP models for sentiment analysis."""
        try:
            # Try to load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Download NLTK data if needed
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using multiple methods."""
        results = {}
        
        # TextBlob sentiment
        try:
            blob = TextBlob(text)
            results['textblob'] = {
                'polarity': blob.sentiment.polarity,  # -1 to 1
                'subjectivity': blob.sentiment.subjectivity  # 0 to 1
            }
        except Exception as e:
            print(f"TextBlob sentiment error: {e}")
            results['textblob'] = {'polarity': 0.0, 'subjectivity': 0.0}
        
        # VADER sentiment
        try:
            from nltk.sentiment import SentimentIntensityAnalyzer
            sia = SentimentIntensityAnalyzer()
            vader_scores = sia.polarity_scores(text)
            results['vader'] = vader_scores
        except Exception as e:
            print(f"VADER sentiment error: {e}")
            results['vader'] = {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}
        
        # Overall sentiment classification
        polarity = results['textblob']['polarity']
        if polarity > 0.1:
            sentiment_label = 'positive'
        elif polarity < -0.1:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        results['overall'] = {
            'sentiment': sentiment_label,
            'confidence': abs(polarity)
        }
        
        return results


class TopicAnalyzer:
    """Analyzes topics and themes in political documents."""
    
    def __init__(self):
        self.political_keywords = {
            'healthcare': ['healthcare', 'health care', 'medicare', 'medicaid', 'insurance', 'medical'],
            'economy': ['economy', 'economic', 'jobs', 'employment', 'unemployment', 'budget', 'deficit', 'tax', 'taxes'],
            'education': ['education', 'school', 'schools', 'student', 'students', 'college', 'university'],
            'environment': ['environment', 'environmental', 'climate', 'energy', 'renewable', 'pollution', 'carbon'],
            'immigration': ['immigration', 'immigrant', 'immigrants', 'border', 'visa', 'citizenship'],
            'defense': ['defense', 'military', 'army', 'navy', 'air force', 'security', 'veteran', 'veterans'],
            'justice': ['justice', 'court', 'courts', 'judge', 'judges', 'law', 'legal', 'crime', 'criminal'],
            'infrastructure': ['infrastructure', 'roads', 'bridges', 'transportation', 'public transit'],
            'social_issues': ['abortion', 'gun control', 'gun rights', 'civil rights', 'voting rights', 'privacy']
        }
    
    def analyze_topics(self, text: str) -> Dict[str, Any]:
        """Analyze topics mentioned in the text."""
        text_lower = text.lower()
        
        # Count keyword mentions by topic
        topic_scores = {}
        for topic, keywords in self.political_keywords.items():
            count = sum(text_lower.count(keyword) for keyword in keywords)
            if count > 0:
                topic_scores[topic] = count
        
        # Calculate topic percentages
        total_mentions = sum(topic_scores.values())
        topic_percentages = {}
        if total_mentions > 0:
            for topic, count in topic_scores.items():
                topic_percentages[topic] = (count / total_mentions) * 100
        
        # Find primary topics (top 3)
        primary_topics = sorted(topic_percentages.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'topic_counts': topic_scores,
            'topic_percentages': topic_percentages,
            'primary_topics': primary_topics,
            'total_topic_mentions': total_mentions
        }


class EntityAnalyzer:
    """Analyzes political entities in documents."""
    
    def __init__(self):
        self.nlp = None
        self._load_spacy()
        
        # Pre-compiled patterns for political entities
        self.political_patterns = {
            'bill_references': re.compile(r'\b(?:H\.R\.|S\.|H\.J\.Res\.|S\.J\.Res\.|H\.Con\.Res\.|S\.Con\.Res\.)\s*\d+', re.IGNORECASE),
            'congress_sessions': re.compile(r'\b(?:117th|118th|119th)\s+Congress\b', re.IGNORECASE),
            'committees': re.compile(r'\bCommittee on [A-Za-z\s,]+(?=\b(?:and|,|\.|\s*$))', re.IGNORECASE),
            'political_parties': re.compile(r'\b(?:Republican|Democrat|Democratic|Independent|Libertarian|Green)\s*(?:Party)?\b', re.IGNORECASE),
            'states': re.compile(r'\b(?:Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming)\b', re.IGNORECASE)
        }
    
    def _load_spacy(self):
        """Load spaCy model for entity recognition."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract political entities from text."""
        entities = {
            'people': [],
            'organizations': [],
            'locations': [],
            'bill_references': [],
            'committees': [],
            'political_parties': [],
            'states': [],
            'congress_sessions': []
        }
        
        # Use spaCy NER if available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    entities['people'].append({
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'confidence': 0.8  # spaCy doesn't provide confidence
                    })
                elif ent.label_ in ["ORG", "NORP"]:
                    entities['organizations'].append({
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'confidence': 0.8
                    })
                elif ent.label_ in ["GPE", "LOC"]:
                    entities['locations'].append({
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'confidence': 0.8
                    })
        
        # Extract political-specific entities using regex
        for entity_type, pattern in self.political_patterns.items():
            matches = pattern.findall(text)
            entities[entity_type] = list(set(matches))  # Remove duplicates
        
        # Count entity frequencies
        entity_counts = {}
        for entity_type, entity_list in entities.items():
            if isinstance(entity_list, list) and entity_list:
                if isinstance(entity_list[0], dict):
                    entity_counts[entity_type] = len(entity_list)
                else:
                    entity_counts[entity_type] = len(entity_list)
            else:
                entity_counts[entity_type] = 0
        
        return {
            'entities': entities,
            'entity_counts': entity_counts,
            'total_entities': sum(entity_counts.values())
        }


class DocumentSummarizer:
    """Generates summaries of political documents."""
    
    def __init__(self):
        self.max_summary_sentences = 3
    
    def generate_summary(self, text: str, max_sentences: int = None) -> Dict[str, Any]:
        """Generate a summary of the document."""
        if max_sentences is None:
            max_sentences = self.max_summary_sentences
        
        # Simple extractive summarization
        sentences = self._split_into_sentences(text)
        
        if len(sentences) <= max_sentences:
            summary = text
            key_sentences = sentences
        else:
            # Score sentences based on word frequency
            scored_sentences = self._score_sentences(sentences)
            
            # Select top sentences
            top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:max_sentences]
            
            # Sort by original order
            top_sentences = sorted(top_sentences, key=lambda x: x[2])
            
            key_sentences = [s[0] for s in top_sentences]
            summary = " ".join(key_sentences)
        
        return {
            'summary': summary,
            'key_sentences': key_sentences,
            'original_length': len(text),
            'summary_length': len(summary),
            'compression_ratio': len(summary) / len(text) if len(text) > 0 else 0
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _score_sentences(self, sentences: List[str]) -> List[Tuple[str, float, int]]:
        """Score sentences for importance."""
        # Calculate word frequencies
        all_words = []
        for sentence in sentences:
            words = re.findall(r'\b\w+\b', sentence.lower())
            all_words.extend(words)
        
        word_freq = Counter(all_words)
        
        # Score each sentence
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            words = re.findall(r'\b\w+\b', sentence.lower())
            score = sum(word_freq[word] for word in words) / len(words) if words else 0
            scored_sentences.append((sentence, score, i))
        
        return scored_sentences


class DocumentAnalyzer:
    """Main document analyzer coordinating all analysis types."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.sentiment_analyzer = SentimentAnalyzer()
        self.topic_analyzer = TopicAnalyzer()
        self.entity_analyzer = EntityAnalyzer()
        self.summarizer = DocumentSummarizer()
    
    def analyze_document(self, document: Document) -> List[DocumentAnalysis]:
        """Perform comprehensive analysis on a document."""
        analyses = []
        
        # Sentiment analysis
        try:
            sentiment_result = self.sentiment_analyzer.analyze_sentiment(document.content)
            sentiment_analysis = DocumentAnalysis(
                document_id=document.id,
                analysis_type="sentiment",
                result=sentiment_result,
                confidence_score=sentiment_result['overall']['confidence']
            )
            self.db.add(sentiment_analysis)
            analyses.append(sentiment_analysis)
        except Exception as e:
            print(f"Error in sentiment analysis for document {document.id}: {e}")
        
        # Topic analysis
        try:
            topic_result = self.topic_analyzer.analyze_topics(document.content)
            topic_analysis = DocumentAnalysis(
                document_id=document.id,
                analysis_type="topics",
                result=topic_result,
                confidence_score=0.8  # Fixed confidence for topic analysis
            )
            self.db.add(topic_analysis)
            analyses.append(topic_analysis)
        except Exception as e:
            print(f"Error in topic analysis for document {document.id}: {e}")
        
        # Entity extraction
        try:
            entity_result = self.entity_analyzer.extract_entities(document.content)
            entity_analysis = DocumentAnalysis(
                document_id=document.id,
                analysis_type="entities",
                result=entity_result,
                confidence_score=0.7  # Fixed confidence for entity extraction
            )
            self.db.add(entity_analysis)
            analyses.append(entity_analysis)
        except Exception as e:
            print(f"Error in entity analysis for document {document.id}: {e}")
        
        # Summary generation
        try:
            summary_result = self.summarizer.generate_summary(document.content)
            summary_analysis = DocumentAnalysis(
                document_id=document.id,
                analysis_type="summary",
                result=summary_result,
                confidence_score=0.9  # Fixed confidence for summary
            )
            self.db.add(summary_analysis)
            analyses.append(summary_analysis)
        except Exception as e:
            print(f"Error in summary generation for document {document.id}: {e}")
        
        # Commit all analyses
        try:
            self.db.commit()
            for analysis in analyses:
                self.db.refresh(analysis)
        except Exception as e:
            self.db.rollback()
            print(f"Error committing analyses for document {document.id}: {e}")
            return []
        
        return analyses
    
    def analyze_documents_batch(self, documents: List[Document]) -> List[DocumentAnalysis]:
        """Analyze multiple documents in batch."""
        all_analyses = []
        
        for document in documents:
            try:
                analyses = self.analyze_document(document)
                all_analyses.extend(analyses)
                print(f"Analyzed document {document.id}: {len(analyses)} analyses")
            except Exception as e:
                print(f"Error analyzing document {document.id}: {e}")
                continue
        
        return all_analyses
    
    def get_analysis_summary(self, document_id: int) -> Dict[str, Any]:
        """Get a summary of all analyses for a document."""
        analyses = self.db.query(DocumentAnalysis).filter(
            DocumentAnalysis.document_id == document_id
        ).all()
        
        summary = {}
        for analysis in analyses:
            summary[analysis.analysis_type] = analysis.result
        
        return summary
    
    def get_sentiment_trends(self, source: Optional[str] = None, 
                           document_type: Optional[str] = None) -> Dict[str, Any]:
        """Get sentiment trends across documents."""
        query = self.db.query(DocumentAnalysis, Document).join(Document).filter(
            DocumentAnalysis.analysis_type == "sentiment"
        )
        
        if source:
            query = query.filter(Document.source == source)
        
        if document_type:
            query = query.filter(Document.document_type == document_type)
        
        results = query.all()
        
        sentiment_data = []
        for analysis, document in results:
            sentiment_data.append({
                'document_id': document.id,
                'title': document.title,
                'source': document.source,
                'document_type': document.document_type,
                'crawled_date': document.crawled_date.isoformat() if document.crawled_date else None,
                'sentiment': analysis.result['overall']['sentiment'],
                'polarity': analysis.result['textblob']['polarity'],
                'confidence': analysis.confidence_score
            })
        
        # Calculate aggregates
        if sentiment_data:
            sentiments = [d['sentiment'] for d in sentiment_data]
            polarities = [d['polarity'] for d in sentiment_data]
            
            sentiment_counts = Counter(sentiments)
            avg_polarity = sum(polarities) / len(polarities)
            
            return {
                'total_documents': len(sentiment_data),
                'sentiment_distribution': dict(sentiment_counts),
                'average_polarity': avg_polarity,
                'documents': sentiment_data
            }
        else:
            return {
                'total_documents': 0,
                'sentiment_distribution': {},
                'average_polarity': 0.0,
                'documents': []
            }


class AnalysisPipeline:
    """Coordinates the document analysis pipeline."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.analyzer = DocumentAnalyzer(db_session)
    
    def run_analysis(self, batch_size: int = 50) -> Dict[str, Any]:
        """Run analysis on all unanalyzed documents."""
        try:
            # Get documents that haven't been analyzed
            unanalyzed_docs = self.db.query(Document).filter(
                ~Document.analyses.any()
            ).all()
            
            if not unanalyzed_docs:
                return {
                    'status': 'completed',
                    'message': 'All documents already analyzed',
                    'documents_processed': 0
                }
            
            print(f"Found {len(unanalyzed_docs)} documents to analyze")
            
            # Process in batches
            total_processed = 0
            for i in range(0, len(unanalyzed_docs), batch_size):
                batch = unanalyzed_docs[i:i+batch_size]
                processed_analyses = self.analyzer.analyze_documents_batch(batch)
                total_processed += len(batch)
                
                print(f"Processed batch {i//batch_size + 1}: {len(batch)} documents, {len(processed_analyses)} analyses")
            
            return {
                'status': 'completed',
                'documents_processed': total_processed,
                'total_documents': len(unanalyzed_docs)
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'documents_processed': 0
            }