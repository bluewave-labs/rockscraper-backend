"""
Manager for crawling operations
"""
import logging
import time
from typing import Dict, Any, Optional, List, Set, Tuple
from urllib.parse import urlparse

from models.task import Task
from models.task_result import TaskResult
from models.enums import TaskStatus
from services.abstract_scraper import AbstractScraper
from services.api_scraper import APIScraper
from services.content_repository import ContentRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CrawlManager:
    """
    Manager for handling high-level crawling operations
    Orchestrates the scraping process using the JS crawlsession API
    """
    
    def __init__(
        self,
        scraper: Optional[AbstractScraper] = None,
        content_repo: Optional[ContentRepository] = None,
        session_duration: int = 1800,  # 30 minutes
        max_urls_per_session: int = 100,
        follow_links: bool = True,
        max_depth: int = 3,
        same_domain_only: bool = True
    ):
        """
        Initialize the crawl manager
        
        Args:
            scraper: Scraper instance to use (creates default if None)
            content_repo: Content repository to use (creates default if None)
            session_duration: Duration of crawl sessions in seconds
            max_urls_per_session: Maximum URLs to crawl per session
            follow_links: Whether to follow links in crawled pages
            max_depth: Maximum depth to crawl when following links
            same_domain_only: Only follow links to the same domain
        """
        self.scraper = scraper or APIScraper()
        self.content_repo = content_repo or ContentRepository()
        self.session_duration = session_duration
        self.max_urls_per_session = max_urls_per_session
        self.follow_links = follow_links
        self.max_depth = max_depth
        self.same_domain_only = same_domain_only
        
        # State variables
        self.active_session_id = None
        self.urls_in_session = 0
        self.visited_urls = set()
        
    def crawl(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Crawl a single URL (with optional session management)
        
        Args:
            url: URL to crawl
            params: Optional parameters for the crawler
            
        Returns:
            Dictionary with crawl result
        """
        # Create a basic task for tracking
        task = Task(url=url)
        
        try:
            # Handle session creation if needed
            if not self.active_session_id:
                self.active_session_id = self.scraper.start_session(self.session_duration)
                self.urls_in_session = 0
                logger.info(f"Started new crawl session: {self.active_session_id}")
            
            # Scrape the URL
            result = self.scraper.scrape_url(url, self.active_session_id, params)
            self.urls_in_session += 1
            self.visited_urls.add(url)
            
            # Create task result
            if result.get('success'):
                task_result = TaskResult.create_success(
                    task_id=task.id,
                    worker_id="api-scraper",  # Using a placeholder worker ID
                    execution_time_ms=int(time.time() * 1000 - task.created_at.timestamp() * 1000),
                    data={
                        'url': url,
                        'html_content': result.get('content', {}).get('html_content'),
                        'headers': result.get('headers'),
                        'status_code': result.get('status_code'),
                        'job_id': result.get('job_id'),
                        'session_id': result.get('session_id')
                    }
                )
                
                # Store content in the database
                content_id = self.scraper.save_to_database(task.id, result)
                result['content_id'] = content_id
                
                # Update task status
                task.update_status(TaskStatus.COMPLETED)
            else:
                task_result = TaskResult.create_failure(
                    task_id=task.id,
                    worker_id="api-scraper",
                    execution_time_ms=int(time.time() * 1000 - task.created_at.timestamp() * 1000),
                    error=result.get('error', 'Unknown error')
                )
                
                # Update task status
                task.record_error(result.get('error', 'Unknown error'))
            
            # Handle session rotation
            if self.urls_in_session >= self.max_urls_per_session:
                self._rotate_session()
            
            # Handle link following if enabled and successful
            if self.follow_links and result.get('success'):
                content = result.get('content', {})
                links = content.get('links', [])
                
                # Extract links to follow (filter by domain if needed)
                links_to_follow = self._filter_links_to_follow(links, url)
                
                # Add links to result
                result['links_to_follow'] = links_to_follow
            
            return result
            
        except Exception as e:
            logger.error(f"Error crawling URL {url}: {e}")
            
            # Update task status
            task.record_error(str(e))
            
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'task_id': task.id
            }
    
    def crawl_with_depth(self, start_url: str, max_depth: Optional[int] = None) -> Dict[str, Any]:
        """
        Crawl a URL and follow links up to max_depth
        
        Args:
            start_url: URL to start crawling from
            max_depth: Maximum depth to crawl (overrides instance setting if provided)
            
        Returns:
            Dictionary with crawl statistics
        """
        max_depth = max_depth if max_depth is not None else self.max_depth
        crawl_queue = [(start_url, 0)]  # (url, depth)
        crawled_urls = set()
        successful_urls = set()
        failed_urls = set()
        
        # Start a new session
        self.active_session_id = self.scraper.start_session(self.session_duration)
        self.urls_in_session = 0
        logger.info(f"Started new crawl session for depth crawl: {self.active_session_id}")
        
        try:
            while crawl_queue:
                url, depth = crawl_queue.pop(0)
                
                # Skip already crawled URLs
                if url in crawled_urls:
                    continue
                
                # Crawl the URL
                logger.info(f"Crawling URL {url} at depth {depth}")
                result = self.crawl(url)
                crawled_urls.add(url)
                
                if result.get('success'):
                    successful_urls.add(url)
                    
                    # Follow links if not at max depth
                    if depth < max_depth:
                        links_to_follow = result.get('links_to_follow', [])
                        
                        for link in links_to_follow:
                            link_url = link.get('target_url')
                            
                            if link_url and link_url not in crawled_urls:
                                crawl_queue.append((link_url, depth + 1))
                else:
                    failed_urls.add(url)
            
            # End the session
            if self.active_session_id:
                self.scraper.end_session(self.active_session_id)
                self.active_session_id = None
            
            # Return statistics
            return {
                'success': True,
                'start_url': start_url,
                'max_depth': max_depth,
                'total_urls_crawled': len(crawled_urls),
                'successful_urls': len(successful_urls),
                'failed_urls': len(failed_urls),
                'urls': {
                    'crawled': list(crawled_urls),
                    'successful': list(successful_urls),
                    'failed': list(failed_urls)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in depth crawl from {start_url}: {e}")
            
            # End the session even if there was an error
            if self.active_session_id:
                self.scraper.end_session(self.active_session_id)
                self.active_session_id = None
            
            return {
                'success': False,
                'error': str(e),
                'start_url': start_url,
                'total_urls_crawled': len(crawled_urls),
                'successful_urls': len(successful_urls),
                'failed_urls': len(failed_urls)
            }
    
    def _rotate_session(self) -> None:
        """Rotate the current session by closing it and starting a new one"""
        if self.active_session_id:
            logger.info(f"Rotating session after {self.urls_in_session} URLs")
            self.scraper.end_session(self.active_session_id)
            self.active_session_id = self.scraper.start_session(self.session_duration)
            self.urls_in_session = 0
            logger.info(f"Started new session: {self.active_session_id}")
    
    def _filter_links_to_follow(self, links: List[Dict[str, Any]], base_url: str) -> List[Dict[str, Any]]:
        """
        Filter links to determine which ones to follow
        
        Args:
            links: List of link dictionaries
            base_url: URL that the links were extracted from
            
        Returns:
            Filtered list of links to follow
        """
        if not links:
            return []
            
        # Parse base URL
        base_domain = self._get_domain(base_url)
        
        # Filter links
        links_to_follow = []
        
        for link in links:
            link_url = link.get('target_url')
            
            # Skip if no URL
            if not link_url:
                continue
                
            # Skip if already visited
            if link_url in self.visited_urls:
                continue
                
            # Filter by domain if needed
            if self.same_domain_only:
                link_domain = self._get_domain(link_url)
                if link_domain != base_domain:
                    continue
            
            # Add link to follow
            links_to_follow.append(link)
        
        return links_to_follow
    
    @staticmethod
    def _get_domain(url: str) -> str:
        """
        Extract domain from URL
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain string
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "" 