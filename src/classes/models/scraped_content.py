"""
Implementation of a scraped content model
"""
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from models.database import DatabaseManager

class ScrapedContent:
    """Model for storing and retrieving scraped web content"""
    
    def __init__(
        self,
        task_id: str,
        url: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        status_code: Optional[int] = None
    ):
        """
        Create a new ScrapedContent object
        
        Args:
            task_id: ID of the task that produced this content
            url: The URL that was scraped
            html_content: HTML content of the page
            text_content: Extracted text content
            title: Page title
            metadata: Additional metadata (e.g., meta tags)
            headers: HTTP response headers
            status_code: HTTP status code
        """
        self.id = None  # Will be set when saved to database
        self.task_id = task_id
        self.url = url
        self.html_content = html_content
        self.text_content = text_content
        self.title = title
        self.metadata = metadata or {}
        self.headers = headers or {}
        self.status_code = status_code
        self.scrape_date = datetime.now()
        self.links = []  # List of extracted links
    
    def add_link(self, target_url: str, link_text: Optional[str] = None, is_internal: bool = False) -> None:
        """
        Add a link found on the page
        
        Args:
            target_url: URL the link points to
            link_text: Text content of the link
            is_internal: Whether the link is internal to the same domain
        """
        self.links.append({
            'target_url': target_url,
            'link_text': link_text,
            'is_internal': is_internal
        })
    
    def save(self) -> int:
        """
        Save the scraped content to the database
        
        Returns:
            The ID of the saved content
        """
        db = DatabaseManager()
        
        # Convert dictionaries to JSON strings for storage
        metadata_json = json.dumps(self.metadata) if self.metadata else None
        headers_json = json.dumps(self.headers) if self.headers else None
        
        # Insert content record
        query = """
        INSERT INTO scraped_content 
        (task_id, url, title, html_content, text_content, metadata, headers, status_code, scrape_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        params = (
            self.task_id, 
            self.url, 
            self.title, 
            self.html_content, 
            self.text_content, 
            metadata_json, 
            headers_json, 
            self.status_code, 
            self.scrape_date
        )
        
        result = db.execute_query(query, params, fetch_one=True)
        self.id = result[0]
        
        # Save links if any
        if self.links:
            self._save_links()
            
        return self.id
    
    def _save_links(self) -> None:
        """Save extracted links to the database"""
        if not self.id:
            raise ValueError("Content must be saved before links can be saved")
        
        db = DatabaseManager()
        
        # Prepare all links for batch insert
        values_parts = []
        params = []
        
        for link in self.links:
            values_parts.append("(%s, %s, %s, %s)")
            params.extend([
                self.id,
                link['target_url'],
                link['link_text'],
                link['is_internal']
            ])
        
        if values_parts:
            values_str = ", ".join(values_parts)
            query = f"""
            INSERT INTO links 
            (source_content_id, target_url, link_text, is_internal)
            VALUES {values_str};
            """
            
            db.execute_query(query, tuple(params))
    
    @classmethod
    def get_by_id(cls, content_id: int) -> Optional['ScrapedContent']:
        """
        Retrieve scraped content by ID
        
        Args:
            content_id: The ID of the content to retrieve
            
        Returns:
            ScrapedContent object or None if not found
        """
        db = DatabaseManager()
        
        query = """
        SELECT id, task_id, url, title, html_content, text_content, 
               metadata, headers, status_code, scrape_date
        FROM scraped_content
        WHERE id = %s;
        """
        
        result = db.execute_query(query, (content_id,), fetch_one=True)
        
        if not result:
            return None
            
        return cls._create_from_db_row(result)
    
    @classmethod
    def get_by_task_id(cls, task_id: str) -> Optional['ScrapedContent']:
        """
        Retrieve scraped content by task ID
        
        Args:
            task_id: The task ID to search for
            
        Returns:
            ScrapedContent object or None if not found
        """
        db = DatabaseManager()
        
        query = """
        SELECT id, task_id, url, title, html_content, text_content, 
               metadata, headers, status_code, scrape_date
        FROM scraped_content
        WHERE task_id = %s;
        """
        
        result = db.execute_query(query, (task_id,), fetch_one=True)
        
        if not result:
            return None
            
        return cls._create_from_db_row(result)
    
    @classmethod
    def get_by_url(cls, url: str) -> Optional['ScrapedContent']:
        """
        Retrieve the most recent scraped content for a specific URL
        
        Args:
            url: The URL to search for
            
        Returns:
            ScrapedContent object or None if not found
        """
        db = DatabaseManager()
        
        query = """
        SELECT id, task_id, url, title, html_content, text_content, 
               metadata, headers, status_code, scrape_date
        FROM scraped_content
        WHERE url = %s
        ORDER BY scrape_date DESC
        LIMIT 1;
        """
        
        result = db.execute_query(query, (url,), fetch_one=True)
        
        if not result:
            return None
            
        return cls._create_from_db_row(result)
    
    @classmethod
    def search(cls, keyword: str, limit: int = 10, offset: int = 0) -> List['ScrapedContent']:
        """
        Search for scraped content by keyword in title or text
        
        Args:
            keyword: The keyword to search for
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of ScrapedContent objects
        """
        db = DatabaseManager()
        
        query = """
        SELECT id, task_id, url, title, html_content, text_content, 
               metadata, headers, status_code, scrape_date
        FROM scraped_content
        WHERE 
            title ILIKE %s OR
            text_content ILIKE %s
        ORDER BY scrape_date DESC
        LIMIT %s OFFSET %s;
        """
        
        search_pattern = f'%{keyword}%'
        results = db.execute_query(query, (search_pattern, search_pattern, limit, offset))
        
        return [cls._create_from_db_row(row) for row in results]
    
    @classmethod
    def _create_from_db_row(cls, row) -> 'ScrapedContent':
        """Create a ScrapedContent object from a database row"""
        id, task_id, url, title, html_content, text_content, metadata_json, headers_json, status_code, scrape_date = row
        
        # Parse JSON fields
        metadata = json.loads(metadata_json) if metadata_json else {}
        headers = json.loads(headers_json) if headers_json else {}
        
        # Create instance
        instance = cls(
            task_id=task_id,
            url=url,
            html_content=html_content,
            text_content=text_content,
            title=title,
            metadata=metadata,
            headers=headers,
            status_code=status_code
        )
        
        # Set fields that aren't passed to __init__
        instance.id = id
        instance.scrape_date = scrape_date
        
        # Load links
        instance._load_links()
        
        return instance
    
    def _load_links(self) -> None:
        """Load links from the database"""
        if not self.id:
            return
            
        db = DatabaseManager()
        
        query = """
        SELECT id, target_url, link_text, is_internal, crawled
        FROM links
        WHERE source_content_id = %s;
        """
        
        results = db.execute_query(query, (self.id,))
        
        self.links = []
        for row in results:
            id, target_url, link_text, is_internal, crawled = row
            self.links.append({
                'id': id,
                'target_url': target_url,
                'link_text': link_text,
                'is_internal': is_internal,
                'crawled': crawled
            })
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the scraped content to a dictionary
        
        Returns:
            Dictionary representation of the scraped content
        """
        return {
            'id': self.id,
            'task_id': self.task_id,
            'url': self.url,
            'title': self.title,
            # Exclude html_content as it can be very large
            'text_content': self.text_content[:1000] + '...' if self.text_content and len(self.text_content) > 1000 else self.text_content,
            'metadata': self.metadata,
            'headers': self.headers,
            'status_code': self.status_code,
            'scrape_date': self.scrape_date.isoformat() if self.scrape_date else None,
            'links_count': len(self.links)
        } 