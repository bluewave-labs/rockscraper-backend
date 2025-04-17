"""
API-based scraper implementation
"""
import re
import json
import logging
import zlib
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urljoin, urlparse

from services.abstract_scraper import AbstractScraper
from services.api_client import APIClient
from services.content_extractor import ContentExtractor
from models.scraped_content import ScrapedContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIScraper(AbstractScraper):
    """
    Concrete scraper implementation that uses the JavaScript crawlsession API
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_sec: int = 30
    ):
        """
        Initialize the API scraper
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for the API
            timeout_sec: Default timeout for requests in seconds
        """
        self.client = APIClient(api_key, base_url, timeout_sec)
        self.extractor = ContentExtractor()
    
    def start_session(self, duration_seconds: int = 300) -> Optional[str]:
        """
        Start a new scraping session
        
        Args:
            duration_seconds: Duration of the session in seconds
            
        Returns:
            Session ID or None if creation failed
        """
        return self.client.create_session(duration_seconds)
    
    def end_session(self, session_id: str) -> bool:
        """
        End an existing session
        
        Args:
            session_id: ID of the session to end
            
        Returns:
            True if session was ended successfully, False otherwise
        """
        return self.client.close_session(session_id)
    
    def scrape_url(
        self, 
        url: str, 
        session_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Scrape content from a URL using the API
        
        Args:
            url: URL to scrape
            session_id: Optional session ID to use
            params: Optional additional parameters
            
        Returns:
            Dictionary with the scraped data
        """
        try:
            # Submit the job
            job_result = self.client.submit_crawl_job(url, session_id)
            job_id = job_result.get('job_id')
            
            if not job_id:
                logger.error("No job ID returned from API")
                return {
                    'success': False,
                    'error': 'No job ID returned from API',
                    'url': url
                }
            
            # Wait for the job to complete
            status = self.client.poll_job_status(job_id)
            
            if status.get('status') != 'completed':
                logger.warning(f"Job {job_id} failed with status: {status.get('status')}")
                return {
                    'success': False,
                    'error': f"Job failed with status: {status.get('status')}",
                    'url': url,
                    'job_id': job_id,
                    'session_id': status.get('session_id')
                }
            
            # Download the content
            content, details = self.client.download_job_content(job_id)
            
            # Process the content
            processed_content = self.process_content(content, url)
            
            # Combine with job details
            result = {
                'success': True,
                'url': url,
                'job_id': job_id,
                'session_id': status.get('session_id'),
                'status_code': details.get('status_code'),
                'headers': details.get('response_headers'),
                'content': processed_content
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def extract_links(self, content: str, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract links from HTML content
        
        Args:
            content: HTML content to extract links from
            base_url: Base URL to resolve relative links
            
        Returns:
            List of dictionaries with extracted links
        """
        extracted = self.extractor.extract_content(content, base_url)
        return extracted.get('links', [])
    
    def process_content(self, content: bytes, url: str) -> Dict[str, Any]:
        """
        Process raw content bytes
        
        Args:
            content: Raw content bytes
            url: URL the content was scraped from
            
        Returns:
            Dictionary with processed content
        """
        try:
            # Try to decode content as UTF-8
            html_content = content.decode('utf-8')
            
            # Extract content using our extractor
            extracted = self.extractor.extract_content(html_content, url)
            
            return {
                'html_content': html_content,
                'text_content': extracted.get('text_content'),
                'title': extracted.get('title'),
                'metadata': extracted.get('metadata'),
                'links': extracted.get('links')
            }
            
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode content as UTF-8, trying to decompress")
            
            try:
                # Try to decompress with gzip
                decompressed = zlib.decompress(content, 16 + zlib.MAX_WBITS)
                html_content = decompressed.decode('utf-8')
                
                # Extract content
                extracted = self.extractor.extract_content(html_content, url)
                
                return {
                    'html_content': html_content,
                    'text_content': extracted.get('text_content'),
                    'title': extracted.get('title'),
                    'metadata': extracted.get('metadata'),
                    'links': extracted.get('links')
                }
                
            except Exception as e:
                logger.error(f"Failed to decompress content: {e}")
                
                # Return raw binary content
                return {
                    'binary_content': content,
                    'text_content': None,
                    'title': None,
                    'metadata': {},
                    'links': []
                }
        except Exception as e:
            logger.error(f"Error processing content: {e}")
            return {
                'html_content': None,
                'text_content': None,
                'title': None,
                'metadata': {},
                'links': []
            }
    
    def save_to_database(self, task_id: str, scrape_result: Dict[str, Any]) -> Optional[int]:
        """
        Save scrape result to the database
        
        Args:
            task_id: Task ID associated with this scrape
            scrape_result: Scrape result dictionary
            
        Returns:
            ID of saved content or None if save failed
        """
        if not scrape_result.get('success'):
            logger.warning(f"Cannot save failed scrape result for task {task_id}")
            return None
        
        try:
            content = scrape_result.get('content', {})
            
            # Create ScrapedContent object
            scraped_content = ScrapedContent(
                task_id=task_id,
                url=scrape_result.get('url'),
                html_content=content.get('html_content'),
                text_content=content.get('text_content'),
                title=content.get('title'),
                metadata=content.get('metadata'),
                headers={h.get('name'): h.get('value') for h in scrape_result.get('headers', [])},
                status_code=scrape_result.get('status_code')
            )
            
            # Add extracted links
            for link in content.get('links', []):
                scraped_content.add_link(
                    target_url=link.get('target_url'),
                    link_text=link.get('link_text'),
                    is_internal=link.get('is_internal')
                )
            
            # Save to database
            content_id = scraped_content.save()
            logger.info(f"Saved content for URL {scrape_result.get('url')} with ID {content_id}")
            
            return content_id
            
        except Exception as e:
            logger.error(f"Error saving content to database: {e}")
            return None 