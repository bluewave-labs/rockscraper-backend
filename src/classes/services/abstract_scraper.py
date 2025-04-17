"""
Abstract base class for web scrapers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple

class AbstractScraper(ABC):
    """
    Abstract base class defining the common interface for all scrapers
    """
    
    @abstractmethod
    def start_session(self, duration_seconds: int = 300) -> Optional[str]:
        """
        Start a new scraping session
        
        Args:
            duration_seconds: Duration of the session in seconds
            
        Returns:
            Session ID or None if creation failed
        """
        pass
    
    @abstractmethod
    def end_session(self, session_id: str) -> bool:
        """
        End an existing session
        
        Args:
            session_id: ID of the session to end
            
        Returns:
            True if session was ended successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def scrape_url(
        self, 
        url: str, 
        session_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Scrape content from a URL
        
        Args:
            url: URL to scrape
            session_id: Optional session ID to use
            params: Optional additional parameters
            
        Returns:
            Dictionary with the scraped data
        """
        pass
    
    @abstractmethod
    def extract_links(self, content: str, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract links from content
        
        Args:
            content: Content to extract links from
            base_url: Base URL to resolve relative links
            
        Returns:
            List of dictionaries with extracted links
        """
        pass
    
    @abstractmethod
    def process_content(self, content: bytes, url: str) -> Dict[str, Any]:
        """
        Process raw content
        
        Args:
            content: Raw content bytes
            url: URL the content was scraped from
            
        Returns:
            Dictionary with processed content
        """
        pass 