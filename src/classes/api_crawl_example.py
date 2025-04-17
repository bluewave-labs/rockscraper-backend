"""
Example script demonstrating the API crawler implementation
"""
import os
import sys
import time
import logging
import argparse
from datetime import datetime

# Set environment variables for API client and database
os.environ['CRAWL_API_KEY'] = 'crawl-dev-aQR9E7rq94vhaZAU0zHH'
os.environ['CRAWL_API_URL'] = 'https://cdg002.dev.uprock.com'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'rockscraper_db'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'postgres'

from models.database import DatabaseManager
from models.scraped_content import ScrapedContent
from services.api_client import APIClient
from services.api_scraper import APIScraper
from services.crawl_manager import CrawlManager
from services.content_repository import ContentRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def single_url_example(url: str) -> None:
    """
    Example of crawling a single URL
    
    Args:
        url: URL to crawl
    """
    logger.info(f"Single URL Example: {url}")
    
    # Initialize the database
    db = DatabaseManager()
    
    # Create the API scraper
    scraper = APIScraper()
    
    # Create the content repository
    content_repo = ContentRepository()
    
    # Start a session
    session_id = scraper.start_session(300)  # 5 minute session
    logger.info(f"Started session with ID: {session_id}")
    
    try:
        # Scrape the URL
        logger.info(f"Scraping URL: {url}")
        result = scraper.scrape_url(url, session_id)
        
        if result.get('success'):
            logger.info("Scrape successful!")
            
            # Extract some basic info
            content = result.get('content', {})
            title = content.get('title')
            link_count = len(content.get('links', []))
            
            logger.info(f"Title: {title}")
            logger.info(f"Found {link_count} links")
            
            # Save to database
            task_id = "api-example-" + str(int(time.time()))
            content_id = scraper.save_to_database(task_id, result)
            
            if content_id:
                logger.info(f"Saved content to database with ID: {content_id}")
                
                # Retrieve content to verify
                stored_content = ScrapedContent.get_by_id(content_id)
                
                if stored_content:
                    logger.info(f"Retrieved content: {stored_content.title}")
                    logger.info(f"Stored {len(stored_content.links)} links in database")
            else:
                logger.warning("Failed to save content to database")
        else:
            logger.error(f"Scrape failed: {result.get('error')}")
    
    finally:
        # Close the session
        if session_id:
            scraper.end_session(session_id)
            logger.info(f"Closed session: {session_id}")
        
        # Close database connection
        db.close()

def crawl_with_depth_example(start_url: str, max_depth: int) -> None:
    """
    Example of crawling with depth
    
    Args:
        start_url: URL to start crawling from
        max_depth: Maximum depth to crawl
    """
    logger.info(f"Crawl With Depth Example: {start_url} (max depth: {max_depth})")
    
    # Initialize the database
    db = DatabaseManager()
    
    # Create the crawl manager
    manager = CrawlManager(
        max_depth=max_depth,
        same_domain_only=True,
        max_urls_per_session=50
    )
    
    try:
        # Start the crawl
        start_time = time.time()
        result = manager.crawl_with_depth(start_url, max_depth)
        end_time = time.time()
        
        # Print results
        if result.get('success'):
            logger.info("Crawl completed successfully!")
            logger.info(f"Total URLs crawled: {result.get('total_urls_crawled')}")
            logger.info(f"Successful URLs: {result.get('successful_urls')}")
            logger.info(f"Failed URLs: {result.get('failed_urls')}")
            logger.info(f"Total time: {end_time - start_time:.2f} seconds")
            
            # Show some of the crawled URLs
            urls = result.get('urls', {}).get('crawled', [])
            logger.info(f"First 5 crawled URLs:")
            for i, url in enumerate(urls[:5]):
                logger.info(f"  {i+1}. {url}")
            
            if len(urls) > 5:
                logger.info(f"  ... and {len(urls) - 5} more")
            
            # Generate content stats
            content_repo = ContentRepository()
            stats = content_repo.get_content_stats()
            
            logger.info("\nContent Statistics:")
            logger.info(f"Total pages in database: {stats.get('total_pages')}")
            logger.info(f"Total links in database: {stats.get('total_links')}")
            logger.info(f"Crawled links in database: {stats.get('crawled_links')}")
            
            logger.info("\nTop domains:")
            for domain in stats.get('top_domains', []):
                logger.info(f"  {domain.get('domain')}: {domain.get('count')} pages")
        else:
            logger.error(f"Crawl failed: {result.get('error')}")
            logger.info(f"Total URLs attempted: {result.get('total_urls_crawled')}")
    
    finally:
        # Close database connection
        db.close()

def main():
    """Main function to run examples"""
    parser = argparse.ArgumentParser(description="API Crawler Example")
    parser.add_argument("--url", default="https://news.ycombinator.com/", help="URL to crawl")
    parser.add_argument("--depth", type=int, default=1, help="Maximum crawl depth")
    parser.add_argument("--mode", choices=["single", "depth", "both"], default="both", help="Crawl mode")
    
    args = parser.parse_args()
    
    logger.info("=== API Crawler Example ===")
    
    try:
        if args.mode in ["single", "both"]:
            single_url_example(args.url)
        
        if args.mode in ["depth", "both"]:
            crawl_with_depth_example(args.url, args.depth)
            
        logger.info("Examples completed successfully!")
    
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 