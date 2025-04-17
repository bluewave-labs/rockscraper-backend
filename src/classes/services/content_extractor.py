"""
Service for extracting content from web pages
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import trafilatura
except ImportError:
    trafilatura = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentExtractor:
    """Service for extracting and parsing content from HTML pages"""
    
    def __init__(self):
        """Initialize the ContentExtractor"""
        if BeautifulSoup is None:
            logger.warning("BeautifulSoup is not installed. Some features may not work.")
        
        if trafilatura is None:
            logger.warning("trafilatura is not installed. Text extraction may be less effective.")
    
    def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract content from an HTML page
        
        Args:
            html: HTML content to extract from
            url: URL of the page
            
        Returns:
            Dict containing extracted content
        """
        if not html:
            logger.warning("Empty HTML content provided")
            return {
                'title': None,
                'text_content': None,
                'metadata': {},
                'links': []
            }
        
        try:
            if BeautifulSoup is None:
                title, metadata = None, {}
            else:
                title, metadata = self._extract_metadata(html)
            
            text_content = self._extract_text(html)
            links = self._extract_links(html, url)
            
            return {
                'title': title,
                'text_content': text_content,
                'metadata': metadata,
                'links': links
            }
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return {
                'title': None,
                'text_content': None,
                'metadata': {},
                'links': []
            }
    
    def _extract_metadata(self, html: str) -> Tuple[Optional[str], Dict[str, str]]:
        """
        Extract title and metadata from HTML
        
        Args:
            html: HTML content
            
        Returns:
            Tuple of (title, metadata dict)
        """
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string.strip() if soup.title else None
        
        metadata = {}
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                metadata[name] = content
        
        # Extract JSON-LD structured data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                metadata['json_ld'] = data
            except:
                pass
        
        return title, metadata
    
    def _extract_text(self, html: str) -> Optional[str]:
        """
        Extract main text content from HTML
        
        Args:
            html: HTML content
            
        Returns:
            Extracted text or None if extraction failed
        """
        # Try using trafilatura first (better content extraction)
        if trafilatura is not None:
            try:
                extracted_text = trafilatura.extract(html)
                if extracted_text:
                    return extracted_text
            except Exception as e:
                logger.warning(f"Trafilatura extraction failed: {e}")
        
        # Fall back to BeautifulSoup
        if BeautifulSoup is not None:
            try:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get text
                text = soup.get_text(separator='\n')
                
                # Break into lines and remove leading and trailing space on each
                lines = (line.strip() for line in text.splitlines())
                
                # Break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                
                # Drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return text
            except Exception as e:
                logger.warning(f"BeautifulSoup extraction failed: {e}")
        
        return None
    
    def _extract_links(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract links from HTML
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of link objects
        """
        if BeautifulSoup is None:
            return []
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            base_domain = self._get_domain(base_url)
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].strip()
                
                # Skip empty links, anchors, javascript, and mailto links
                if (not href or 
                    href.startswith('#') or 
                    href.startswith('javascript:') or 
                    href.startswith('mailto:')):
                    continue
                
                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                
                # Check if internal link (same domain)
                link_domain = self._get_domain(absolute_url)
                is_internal = (link_domain == base_domain)
                
                # Get link text
                link_text = a_tag.get_text(strip=True)
                
                links.append({
                    'target_url': absolute_url,
                    'link_text': link_text,
                    'is_internal': is_internal
                })
            
            return links
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
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
            domain = parsed.netloc
            
            # Remove port number if present
            if ':' in domain:
                domain = domain.split(':')[0]
                
            return domain
        except:
            return "" 