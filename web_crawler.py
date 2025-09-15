import os
import httpx
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crawler-service")

AGENTIC_KG_URL = os.getenv("AGENTIC_KG_URL", "http://agentic-kg:8000")
CRAWLER_USER_AGENT = "PoliticalDocumentAnalysisBot/1.0 (+http://yourprojectwebsite.com/bot)"

app = FastAPI(
    title="Ethical Web Crawler Service",
    description="A service to crawl government websites and ingest documents into the Agentic KG.",
)

# --- Pydantic Models ---
class CrawlRequest(BaseModel):
    url: HttpUrl
    max_depth: int = 0  # 0 means only crawl the initial URL

class IngestPayload(BaseModel):
    title: str
    content: str
    metadata: dict = {}

# --- Helper Functions ---
async def fetch_url_content(client: httpx.AsyncClient, url: str) -> str | None:
    """Fetches the content of a URL respecting a custom user-agent."""
    try:
        headers = {"User-Agent": CRAWLER_USER_AGENT}
        response = await client.get(url, headers=headers, follow_redirects=True, timeout=15.0)
        response.raise_for_status()
        return response.text
    except httpx.RequestError as e:
        logger.error(f"HTTP error fetching {url}: {e}")
        return None

def extract_text_and_links(html: str, base_url: str) -> (str, str, list[str]):
    """Extracts title, clean text, and absolute links from HTML content."""
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract title
    title = soup.title.string if soup.title else "No Title Found"
    
    # Extract clean text content, removing script and style tags
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
        
    # Get text, trying to focus on main content areas first
    main_content = soup.find('main') or soup.find('article') or soup.find('body')
    if main_content:
        text = ' '.join(main_content.get_text(separator=' ', strip=True).split())
    else:
        text = "No main content found."

    # Extract all unique absolute links from the same domain
    links = set()
    parsed_base = urlparse(base_url)
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_link = urljoin(base_url, href)
        parsed_link = urlparse(absolute_link)
        if parsed_link.netloc == parsed_base.netloc: # Stay on the same domain
            links.add(absolute_link)
            
    return title, text, list(links)

async def post_to_ingest_service(client: httpx.AsyncClient, payload: IngestPayload):
    """Posts the extracted content to the agentic-kg service."""
    ingest_url = f"{AGENTIC_KG_URL}/ingest"
    try:
        response = await client.post(ingest_url, json=payload.dict())
        response.raise_for_status()
        logger.info(f"Successfully ingested content from: {payload.metadata.get('source_url')}")
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Failed to ingest to {ingest_url}: {e}")
        return None

async def crawl_and_ingest_task(start_url: str):
    """The main background task for crawling and ingesting a single URL."""
    async with httpx.AsyncClient() as client:
        logger.info(f"Starting crawl for: {start_url}")
        html = await fetch_url_content(client, start_url)
        if not html:
            logger.warning(f"Could not retrieve content from {start_url}. Aborting.")
            return

        title, text, links = extract_text_and_links(html, start_url)
        
        if not text or len(text) < 100: # Basic filter for empty or trivial pages
             logger.info(f"Page at {start_url} has insufficient content. Skipping ingest.")
             return

        payload = IngestPayload(
            title=title,
            content=text,
            metadata={"source_url": start_url, "crawl_timestamp": "now()"} # Let DB handle timestamp
        )
        await post_to_ingest_service(client, payload)

# --- API Endpoints ---
@app.post("/crawl", status_code=202)
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """
    Initiates a web crawl as a background task.
    This endpoint immediately returns a 202 Accepted response.
    """
    # NOTE: A robust implementation would check robots.txt here before proceeding.
    # For this example, we assume we have permission to crawl the requested URL.
    logger.info(f"Received crawl request for {request.url}. Scheduling task.")
    background_tasks.add_task(crawl_and_ingest_task, str(request.url))
    return {"message": "Crawl task accepted and scheduled to run in the background."}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
