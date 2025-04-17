"""
API client for interfacing with the JavaScript crawlsession API
"""
import os
import json
import time
import logging
import requests
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIClient:
    """
    API client for interfacing with the JavaScript crawlsession API
    Manages session creation, job submission, and content retrieval
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_sec: int = 30
    ):
        """
        Initialize the API client
        
        Args:
            api_key: API key for authentication (falls back to env variable)
            base_url: Base URL for the API (falls back to env variable)
            timeout_sec: Default timeout for requests in seconds
        """
        self.api_key = api_key or os.environ.get('CRAWL_API_KEY', 'crawl-dev-aQR9E7rq94vhaZAU0zHH')
        self.base_url = base_url or os.environ.get('CRAWL_API_URL', 'https://cdg002.dev.uprock.com')
        self.timeout_sec = timeout_sec
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        # Headers for authentication
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"API client initialized with base URL: {self.base_url}")
    
    def create_session(self, duration_seconds: int = 300) -> Optional[str]:
        """
        Create a new crawl session
        
        Args:
            duration_seconds: Duration of the session in seconds
            
        Returns:
            Session ID or None if creation failed
        """
        logger.info(f"Creating a new crawl session (duration: {duration_seconds}s)")
        
        try:
            session_request = {
                'duration_seconds': duration_seconds
            }
            
            response = requests.post(
                f"{self.base_url}/crawl/v1/session/new",
                headers=self.headers,
                json=session_request,
                timeout=self.timeout_sec
            )
            
            response.raise_for_status()
            data = response.json()
            
            session_id = data.get('session_id')
            if session_id:
                logger.info(f"Session created successfully: {session_id}")
                return session_id
            else:
                logger.warning("No session ID returned in successful response")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None
    
    def close_session(self, session_id: str) -> bool:
        """
        Close an existing session
        
        Args:
            session_id: ID of the session to close
            
        Returns:
            True if session was closed successfully, False otherwise
        """
        if not session_id:
            logger.warning("No session ID provided to close")
            return False
            
        logger.info(f"Closing session {session_id}")
        
        try:
            response = requests.post(
                f"{self.base_url}/crawl/v1/session/{session_id}/close",
                headers=self.headers,
                timeout=self.timeout_sec
            )
            
            response.raise_for_status()
            logger.info(f"Session {session_id} closed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to close session: {e}")
            return False
    
    def submit_crawl_job(self, url: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a crawl job
        
        Args:
            url: URL to crawl
            session_id: Optional session ID to use for the job
            
        Returns:
            Dictionary with job_id and session_id (if provided)
            
        Raises:
            Exception if job submission fails
        """
        logger.info(f"Submitting job for URL: {url}" + (f" with session ID: {session_id}" if session_id else ""))
        
        job_request = {
            'url': url,
            'method': 'GET',
            'timeout_sec': self.timeout_sec,
            'headers': {
                'User-Agent': [self.user_agent],
                'Accept': ['text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'],
                'Accept-Language': ['en-US,en;q=0.9'],
                'Accept-Encoding': ['gzip, deflate, br'],
                'Cache-Control': ['no-cache'],
                'Pragma': ['no-cache'],
                'Sec-Ch-Ua': ['"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'],
                'Sec-Ch-Ua-Mobile': ['?0'],
                'Sec-Ch-Ua-Platform': ['"Windows"'],
                'Sec-Fetch-Dest': ['document'],
                'Sec-Fetch-Mode': ['navigate'],
                'Sec-Fetch-Site': ['none'],
                'Sec-Fetch-User': ['?1'],
                'Upgrade-Insecure-Requests': ['1']
            }
        }
        
        # Add session ID if provided
        if session_id:
            job_request['session_id'] = session_id
        
        try:
            response = requests.post(
                f"{self.base_url}/crawl/v1/new",
                headers=self.headers,
                json=job_request,
                timeout=self.timeout_sec
            )
            
            response.raise_for_status()
            data = response.json()
            
            job_id = data.get('job_id')
            returned_session_id = data.get('session_id')
            
            if session_id and not returned_session_id:
                logger.warning("Session ID was provided but not returned in response")
            
            return {
                'job_id': job_id,
                'session_id': returned_session_id or session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to submit job: {e}")
            raise
    
    def poll_job_status(self, job_id: str, poll_interval: int = 2) -> Dict[str, Any]:
        """
        Poll for job status until completed or failed
        
        Args:
            job_id: ID of the job to poll
            poll_interval: Interval between polls in seconds
            
        Returns:
            Dictionary with job status information
            
        Raises:
            Exception if status polling fails
        """
        logger.info(f"Polling status for job {job_id}")
        
        try:
            completed = False
            status = None
            
            while not completed:
                response = requests.get(
                    f"{self.base_url}/crawl/v1/status/{job_id}",
                    headers=self.headers,
                    timeout=self.timeout_sec
                )
                
                response.raise_for_status()
                status = response.json()
                logger.debug(f"Job {job_id} status: {status.get('status')}")
                
                if status.get('session_id'):
                    logger.debug(f"Job has session ID: {status.get('session_id')}")
                
                # Check if job is completed or failed
                if status.get('status') in ['completed', 'failed', 'timeout']:
                    completed = True
                else:
                    # Wait before polling again
                    time.sleep(poll_interval)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to poll job status: {e}")
            raise
    
    def download_job_content(self, job_id: str) -> Tuple[bytes, Dict[str, Any]]:
        """
        Download job content and details
        
        Args:
            job_id: ID of the job to download
            
        Returns:
            Tuple of (content bytes, job details dictionary)
            
        Raises:
            Exception if content download fails
        """
        logger.info(f"Downloading content for job {job_id}")
        
        try:
            # Get job content
            content_response = requests.get(
                f"{self.base_url}/crawl/v1/jobs/{job_id}/download",
                headers=self.headers,
                timeout=self.timeout_sec
            )
            
            content_response.raise_for_status()
            content = content_response.content
            
            # Get job details
            details_response = requests.get(
                f"{self.base_url}/crawl/v1/jobs/{job_id}/detail",
                headers=self.headers,
                timeout=self.timeout_sec
            )
            
            details_response.raise_for_status()
            details = details_response.json()
            
            # Extract content type and encoding
            content_type = self._get_header_value(details.get('response_headers', []), 'content-type')
            content_encoding = self._get_header_value(details.get('response_headers', []), 'content-encoding')
            
            logger.info(f"Content Type: {content_type or 'not specified'}")
            logger.info(f"Content Encoding: {content_encoding or 'not specified'}")
            
            return content, details
            
        except Exception as e:
            logger.error(f"Failed to download job content: {e}")
            raise
    
    def _get_header_value(self, headers: List[Dict[str, str]], name: str) -> Optional[str]:
        """
        Get a specific header value from response headers
        
        Args:
            headers: List of header dictionaries
            name: Name of the header to find
            
        Returns:
            Header value or None if not found
        """
        if not headers:
            return None
            
        # Find the header (case insensitive)
        for header in headers:
            if header.get('name', '').lower() == name.lower():
                return header.get('value')
                
        return None 