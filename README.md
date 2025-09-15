# Political Analyst Database

A comprehensive political document analysis system that crawls political legislation documents, analyzes them using AI/ML techniques, and provides insights through politician profiles, KPIs, and knowledge graphs.

## Features

### 🕷️ Web Crawling
- Automated crawling of political documents from congress.gov, senate.gov, and govinfo.gov
- Configurable crawling parameters and scheduling
- Document deduplication and metadata extraction

### 📊 Document Analysis
- **Sentiment Analysis**: Analyze sentiment of political documents using multiple NLP models
- **Topic Modeling**: Extract and categorize political topics (healthcare, economy, immigration, etc.)
- **Entity Extraction**: Identify politicians, organizations, legislation references, and more
- **Document Summarization**: Generate concise summaries of lengthy political documents

### 🔍 Vector Search & RAG
- Document vectorization using sentence-transformers
- Semantic search capabilities with ChromaDB
- Knowledge graph construction for relationship analysis
- RAG (Retrieval Augmented Generation) for AI-powered insights

### 👨‍💼 Politician Profiles
- Comprehensive politician database with biographical information
- Social media integration (Twitter analysis)
- Voting record analysis and stance tracking
- Performance KPIs and trend analysis

### 📱 Social Media Integration
- Twitter API integration for politician social media analysis
- Sentiment tracking across social media posts
- Topic analysis of social media content
- Engagement metrics and influence scoring

### 🧠 Knowledge Graph & AI Agents
- Neo4j-powered knowledge graph for relationship mapping
- AI agents for automated analysis and report generation
- Complex query capabilities across political data
- Relationship strength scoring and network analysis

### 🚀 REST API
- Comprehensive FastAPI-based REST API
- Real-time data access and analysis endpoints
- Background task processing for heavy operations
- Interactive API documentation with Swagger

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Redis (for caching and task queues)
- Neo4j (for knowledge graph)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cbwinslow/political-analyst-database.git
   cd political-analyst-database
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and API keys
   ```

4. **Set up databases**
   ```bash
   # Create PostgreSQL database
   createdb political_analyst_db
   
   # Start Redis
   redis-server
   
   # Start Neo4j
   neo4j start
   ```

5. **Initialize the database**
   ```bash
   python -c "from political_analyst.database import create_tables; create_tables()"
   ```

6. **Run the API server**
   ```bash
   uvicorn political_analyst.api.main:app --reload
   ```

7. **Access the API documentation**
   Open http://localhost:8000/docs in your browser

### Basic Usage

#### Start a crawling job
```bash
curl -X POST "http://localhost:8000/api/v1/crawling/quick-crawl?source=congress.gov"
```

#### Search documents
```bash
curl -X POST "http://localhost:8000/api/v1/documents/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "healthcare reform", "limit": 10}'
```

#### Analyze documents
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/analyze"
```

#### Get database statistics
```bash
curl "http://localhost:8000/api/v1/stats"
```

## Architecture

### Core Components

1. **Crawling Module** (`src/political_analyst/crawling/`)
   - Web scrapers for government websites
   - Asynchronous crawling with rate limiting
   - Document metadata extraction

2. **Ingestion Pipeline** (`src/political_analyst/ingestion/`)
   - Document processing and storage
   - Metadata enrichment
   - Deduplication logic

3. **Analysis Engine** (`src/political_analyst/analysis/`)
   - Multi-model sentiment analysis
   - Topic extraction and categorization
   - Named entity recognition
   - Document summarization

4. **Vectorization System** (`src/political_analyst/vectorization/`)
   - Document embedding generation
   - Vector database management
   - Similarity search capabilities

5. **Entity Management** (`src/political_analyst/entities/`)
   - Political entity extraction
   - Relationship mapping
   - Entity disambiguation

6. **Social Media Integration** (`src/political_analyst/social_media/`)
   - Twitter API integration
   - Social media sentiment analysis
   - Engagement metrics tracking

7. **Database Layer** (`src/political_analyst/database/`)
   - SQLAlchemy ORM models
   - Database migrations
   - Connection management

8. **API Layer** (`src/political_analyst/api/`)
   - FastAPI application
   - RESTful endpoints
   - Background task processing

### Database Schema

The system uses PostgreSQL for structured data storage with the following key entities:

- **Documents**: Political documents with metadata
- **Politicians**: Politician profiles and biographical data
- **Entities**: Extracted political entities (people, organizations, legislation)
- **Analyses**: Document analysis results (sentiment, topics, summaries)
- **Social Media**: Social media accounts and posts
- **Knowledge Graph**: Nodes and relationships for network analysis

## API Documentation

The API provides comprehensive endpoints for all system functionality:

### Documents
- `GET /api/v1/documents/` - List documents with filtering
- `GET /api/v1/documents/{id}` - Get specific document
- `POST /api/v1/documents/search` - Semantic search

### Politicians
- `GET /api/v1/politicians/` - List politicians
- `GET /api/v1/politicians/{id}` - Get politician profile
- `GET /api/v1/politicians/{id}/social-media` - Social media analysis

### Analysis
- `POST /api/v1/analysis/analyze` - Run analysis pipeline
- `POST /api/v1/analysis/vectorize` - Run vectorization
- `GET /api/v1/analysis/sentiment-trends` - Get sentiment trends

### Crawling
- `POST /api/v1/crawling/start` - Start crawling job
- `GET /api/v1/crawling/jobs` - List crawling jobs
- `POST /api/v1/crawling/quick-crawl` - Quick crawl of specific source

## Configuration

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/political_analyst_db

# APIs
OPENAI_API_KEY=your_openai_key
TWITTER_API_KEY=your_twitter_key
TWITTER_BEARER_TOKEN=your_bearer_token

# Vector Database
CHROMA_PERSIST_DIRECTORY=./data/chroma
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Crawling
CRAWL_DELAY=1
MAX_CONCURRENT_REQUESTS=10
```

## Development

### Running Tests
```bash
python test_setup.py
```

### Code Structure
```
src/political_analyst/
├── core/           # Configuration and utilities
├── database/       # Database models and connections
├── crawling/       # Web crawling components
├── ingestion/      # Document ingestion pipeline
├── vectorization/  # Vector embeddings and search
├── analysis/       # Document analysis tools
├── entities/       # Entity extraction and management
├── social_media/   # Social media integration
└── api/           # FastAPI application and routes
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with FastAPI, SQLAlchemy, and modern Python tools
- Uses sentence-transformers for document embeddings
- Integrates with ChromaDB for vector search
- Leverages spaCy and NLTK for natural language processing
- Social media integration via Twitter API v2