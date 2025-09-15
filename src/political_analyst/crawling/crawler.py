"""Web crawling module for political documents."""

import asyncio
import aiohttp
from typing import List, Dict, Optional, AsyncGenerator
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from datetime import datetime

from ..core.config import settings


@dataclass
class CrawledDocument:
    """Data class for crawled documents."""
    
    url: str
    title: str
    content: str
    document_type: str
    source: str
    published_date: Optional[datetime] = None
    metadata: Optional[Dict] = None


class PoliticalDocumentCrawler:
    """Main crawler for political documents."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            "User-Agent": settings.crawling.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=settings.crawling.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=settings.crawling.timeout)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            timeout=timeout
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def crawl_congress_gov(self) -> AsyncGenerator[CrawledDocument, None]:
        """Crawl documents from congress.gov."""
        base_url = "https://www.congress.gov"
        
        # Search for recent bills
        search_urls = [
            f"{base_url}/search?q=*&searchResultViewType=expanded&pageSize=50",
            f"{base_url}/bills/browse",
        ]
        
        for search_url in search_urls:
            async for document in self._crawl_congress_search(search_url):
                yield document
    
    async def _crawl_congress_search(self, search_url: str) -> AsyncGenerator[CrawledDocument, None]:
        """Crawl search results from congress.gov."""
        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find bill links
                    bill_links = soup.find_all('a', href=re.compile(r'/bill/'))
                    
                    for link in bill_links[:10]:  # Limit for demo
                        bill_url = urljoin(search_url, link.get('href'))
                        document = await self._crawl_congress_bill(bill_url)
                        if document:
                            yield document
                            
                        await asyncio.sleep(settings.crawling.delay)
                        
        except Exception as e:
            print(f"Error crawling congress search {search_url}: {e}")
    
    async def _crawl_congress_bill(self, bill_url: str) -> Optional[CrawledDocument]:
        """Crawl a specific bill from congress.gov."""
        try:
            async with self.session.get(bill_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract bill information
                    title_elem = soup.find('h1', class_='legDetail')
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                    
                    # Extract content
                    content_elem = soup.find('div', class_='overview-wrapper')
                    content = content_elem.get_text(strip=True) if content_elem else ""
                    
                    # Extract metadata
                    metadata = self._extract_congress_metadata(soup)
                    
                    # Determine document type
                    doc_type = self._determine_document_type(title, bill_url)
                    
                    return CrawledDocument(
                        url=bill_url,
                        title=title,
                        content=content,
                        document_type=doc_type,
                        source="congress.gov",
                        metadata=metadata
                    )
                    
        except Exception as e:
            print(f"Error crawling bill {bill_url}: {e}")
            return None
    
    def _extract_congress_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from congress.gov page."""
        metadata = {}
        
        # Extract sponsor information
        sponsor_elem = soup.find('a', href=re.compile(r'/member/'))
        if sponsor_elem:
            metadata['sponsor'] = sponsor_elem.get_text(strip=True)
        
        # Extract date information
        date_elem = soup.find('span', class_='date')
        if date_elem:
            metadata['date'] = date_elem.get_text(strip=True)
        
        # Extract status
        status_elem = soup.find('div', class_='bill-status')
        if status_elem:
            metadata['status'] = status_elem.get_text(strip=True)
        
        return metadata
    
    def _determine_document_type(self, title: str, url: str) -> str:
        """Determine document type based on title and URL."""
        title_lower = title.lower()
        url_lower = url.lower()
        
        if 'h.r.' in title_lower or 'house' in url_lower:
            return 'house_bill'
        elif 's.' in title_lower or 'senate' in url_lower:
            return 'senate_bill'
        elif 'resolution' in title_lower:
            return 'resolution'
        elif 'amendment' in title_lower:
            return 'amendment'
        else:
            return 'legislation'
    
    async def crawl_senate_gov(self) -> AsyncGenerator[CrawledDocument, None]:
        """Crawl documents from senate.gov."""
        base_url = "https://www.senate.gov"
        
        # Senate legislative activity
        urls = [
            f"{base_url}/legislative/LIS/roll_call_lists/vote_menu_117_2.htm",
            f"{base_url}/legislative/LIS/roll_call_lists/vote_menu_117_1.htm",
        ]
        
        for url in urls:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract vote information
                        vote_links = soup.find_all('a', href=re.compile(r'vote_cfm'))
                        
                        for link in vote_links[:5]:  # Limit for demo
                            vote_url = urljoin(url, link.get('href'))
                            document = await self._crawl_senate_vote(vote_url)
                            if document:
                                yield document
                                
                            await asyncio.sleep(settings.crawling.delay)
                            
            except Exception as e:
                print(f"Error crawling senate URL {url}: {e}")
    
    async def _crawl_senate_vote(self, vote_url: str) -> Optional[CrawledDocument]:
        """Crawl a specific vote from senate.gov."""
        try:
            async with self.session.get(vote_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract vote information
                    title_elem = soup.find('h2')
                    title = title_elem.get_text(strip=True) if title_elem else "Senate Vote"
                    
                    # Extract content
                    content_elem = soup.find('div', class_='contenttext')
                    content = content_elem.get_text(strip=True) if content_elem else ""
                    
                    return CrawledDocument(
                        url=vote_url,
                        title=title,
                        content=content,
                        document_type='senate_vote',
                        source="senate.gov"
                    )
                    
        except Exception as e:
            print(f"Error crawling senate vote {vote_url}: {e}")
            return None
    
    async def crawl_govinfo_gov(self) -> AsyncGenerator[CrawledDocument, None]:
        """Crawl documents from govinfo.gov."""
        base_url = "https://www.govinfo.gov"
        
        # Search recent congressional documents
        search_url = f"{base_url}/app/browse-congress/current"
        
        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find document links
                    doc_links = soup.find_all('a', href=re.compile(r'/app/details/'))
                    
                    for link in doc_links[:5]:  # Limit for demo
                        doc_url = urljoin(search_url, link.get('href'))
                        document = await self._crawl_govinfo_document(doc_url)
                        if document:
                            yield document
                            
                        await asyncio.sleep(settings.crawling.delay)
                        
        except Exception as e:
            print(f"Error crawling govinfo: {e}")
    
    async def _crawl_govinfo_document(self, doc_url: str) -> Optional[CrawledDocument]:
        """Crawl a specific document from govinfo.gov."""
        try:
            async with self.session.get(doc_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract document information
                    title_elem = soup.find('h1')
                    title = title_elem.get_text(strip=True) if title_elem else "GovInfo Document"
                    
                    # Extract content
                    content_elem = soup.find('div', class_='document-content')
                    content = content_elem.get_text(strip=True) if content_elem else ""
                    
                    return CrawledDocument(
                        url=doc_url,
                        title=title,
                        content=content,
                        document_type='government_document',
                        source="govinfo.gov"
                    )
                    
        except Exception as e:
            print(f"Error crawling govinfo document {doc_url}: {e}")
            return None


class CrawlerManager:
    """Manager for coordinating crawling operations."""
    
    def __init__(self):
        self.crawler = PoliticalDocumentCrawler()
    
    async def crawl_all_sources(self) -> List[CrawledDocument]:
        """Crawl documents from all configured sources."""
        documents = []
        
        async with self.crawler:
            # Crawl congress.gov
            async for doc in self.crawler.crawl_congress_gov():
                documents.append(doc)
            
            # Crawl senate.gov
            async for doc in self.crawler.crawl_senate_gov():
                documents.append(doc)
            
            # Crawl govinfo.gov
            async for doc in self.crawler.crawl_govinfo_gov():
                documents.append(doc)
        
        return documents
    
    async def crawl_source(self, source: str) -> List[CrawledDocument]:
        """Crawl documents from a specific source."""
        documents = []
        
        async with self.crawler:
            if source == "congress.gov":
                async for doc in self.crawler.crawl_congress_gov():
                    documents.append(doc)
            elif source == "senate.gov":
                async for doc in self.crawler.crawl_senate_gov():
                    documents.append(doc)
            elif source == "govinfo.gov":
                async for doc in self.crawler.crawl_govinfo_gov():
                    documents.append(doc)
        
        return documents