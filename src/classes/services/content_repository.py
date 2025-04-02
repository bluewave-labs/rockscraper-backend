"""
Repository service for managing scraped content storage
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

from models.task import Task
from models.task_result import TaskResult
from models.scraped_content import ScrapedContent
from services.content_extractor import ContentExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentRepository:
    """
    Repository service for managing storage and retrieval of scraped web content.
    Acts as an intermediary between task results and the database.
    """
    
    def __init__(self):
        """Initialize the ContentRepository"""
        self.extractor = ContentExtractor()
    
    def process_and_store_result(self, task_result: TaskResult) -> Optional[int]:
        """
        Process a task result and store the content in the database
        
        Args:
            task_result: TaskResult object containing scraping results
            
        Returns:
            ID of the stored content or None if processing failed
        """
        if not task_result.success:
            logger.warning(f"Cannot store content for failed task: {task_result.task_id}")
            return None
        
        try:
            # Extract scraped_content from task_result data
            result_data = task_result.data or {}
            html_content = result_data.get('html_content')
            
            if not html_content:
                logger.warning(f"No HTML content in task result: {task_result.task_id}")
                return None
            
            # Get URL from the task
            url = result_data.get('url')
            if not url:
                logger.warning(f"No URL in task result: {task_result.task_id}")
                return None
            
            # Extract content using the content extractor
            extracted = self.extractor.extract_content(html_content, url)
            
            # Create ScrapedContent object
            content = ScrapedContent(
                task_id=task_result.task_id,
                url=url,
                html_content=html_content,
                text_content=extracted['text_content'],
                title=extracted['title'],
                metadata=extracted['metadata'],
                headers=result_data.get('headers', {}),
                status_code=result_data.get('status_code')
            )
            
            # Add extracted links
            for link in extracted['links']:
                content.add_link(
                    target_url=link['target_url'],
                    link_text=link['link_text'],
                    is_internal=link['is_internal']
                )
            
            # Save to database
            content_id = content.save()
            logger.info(f"Stored content for task {task_result.task_id} with ID {content_id}")
            
            return content_id
            
        except Exception as e:
            logger.error(f"Error processing task result: {e}")
            return None
    
    def get_content_by_task(self, task_id: str) -> Optional[ScrapedContent]:
        """
        Retrieve content by task ID
        
        Args:
            task_id: ID of the task to retrieve content for
            
        Returns:
            ScrapedContent object or None if not found
        """
        return ScrapedContent.get_by_task_id(task_id)
    
    def search_content(self, keyword: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search for content by keyword
        
        Args:
            keyword: Keyword to search for
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of content dictionaries
        """
        results = ScrapedContent.search(keyword, limit, offset)
        return [content.to_dict() for content in results]
    
    def get_uncrawled_links(self, limit: int = 100) -> List[Dict[str, str]]:
        """
        Get links that haven't been crawled yet
        
        Args:
            limit: Maximum number of links to return
            
        Returns:
            List of uncrawled link dictionaries
        """
        from models.database import DatabaseManager
        
        db = DatabaseManager()
        query = """
        SELECT l.id, l.target_url, l.link_text, l.is_internal
        FROM links l
        WHERE l.crawled = FALSE AND l.is_internal = TRUE
        LIMIT %s;
        """
        
        results = db.execute_query(query, (limit,))
        
        return [
            {
                'id': row[0],
                'url': row[1],
                'text': row[2] or '',
            }
            for row in results
        ]
    
    def mark_link_as_crawled(self, link_id: int, crawled: bool = True) -> bool:
        """
        Mark a link as crawled
        
        Args:
            link_id: ID of the link to mark
            crawled: Whether the link has been crawled
            
        Returns:
            True if successful, False otherwise
        """
        from models.database import DatabaseManager
        
        db = DatabaseManager()
        query = """
        UPDATE links
        SET crawled = %s
        WHERE id = %s;
        """
        
        try:
            db.execute_query(query, (crawled, link_id))
            return True
        except Exception as e:
            logger.error(f"Error marking link as crawled: {e}")
            return False
    
    def get_content_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored content
        
        Returns:
            Dictionary of content statistics
        """
        from models.database import DatabaseManager
        
        db = DatabaseManager()
        stats = {}
        
        try:
            # Get total content count
            query = "SELECT COUNT(*) FROM scraped_content;"
            result = db.execute_query(query, fetch_one=True)
            stats['total_pages'] = result[0] if result else 0
            
            # Get total links count
            query = "SELECT COUNT(*) FROM links;"
            result = db.execute_query(query, fetch_one=True)
            stats['total_links'] = result[0] if result else 0
            
            # Get crawled links count
            query = "SELECT COUNT(*) FROM links WHERE crawled = TRUE;"
            result = db.execute_query(query, fetch_one=True)
            stats['crawled_links'] = result[0] if result else 0
            
            # Get top domains
            query = """
            SELECT
                SUBSTRING(url FROM '.*://([^/]*)') as domain,
                COUNT(*) as count
            FROM scraped_content
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10;
            """
            results = db.execute_query(query)
            stats['top_domains'] = [{'domain': row[0], 'count': row[1]} for row in results]
            
            return stats
        except Exception as e:
            logger.error(f"Error getting content stats: {e}")
            return {
                'total_pages': 0,
                'total_links': 0,
                'crawled_links': 0,
                'top_domains': []
            } 