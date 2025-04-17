"""
Example script demonstrating the PostgreSQL content storage functionality
"""
import os
import time
import random
import json
import logging
import requests
from datetime import datetime

# Set environment variables for database connection (normally would be in .env file)
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'rockscraper_db'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'postgres'

from process import Process
from models.enums import TaskStatus, WorkerStatus, DistributionStrategy
from models.task import Task
from models.worker import Worker
from models.task_result import TaskResult
from models.database import DatabaseManager
from models.scraped_content import ScrapedContent
from services.content_extractor import ContentExtractor
from services.content_repository import ContentRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_html_content(url):
    """Fetch HTML content from a URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return {
            'html_content': response.text,
            'url': url,
            'headers': dict(response.headers),
            'status_code': response.status_code
        }
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def simulate_worker_execution(process, worker_id, urls, content_repo):
    """Simulate a worker executing scraping tasks with real content fetching"""
    worker = process.distributor.get_worker(worker_id)
    if not worker:
        logger.error(f"Worker {worker_id} not found")
        return
    
    logger.info(f"Worker {worker.name} processing tasks")
    
    for url in urls:
        # Create and assign task
        task = process.create_task(url=url, priority=random.randint(1, 5))
        process.distributor.assign_task(task.id, worker.id)
        
        # Simulate work - actually fetch real content from the URL
        logger.info(f"Fetching content from {url}")
        content_data = get_html_content(url)
        
        if content_data:
            # Create successful result
            result = TaskResult.create_success(
                task_id=task.id,
                worker_id=worker_id,
                execution_time_ms=random.randint(500, 3000),
                data=content_data
            )
            logger.info(f"Successfully scraped {url}")
        else:
            # Create failure result
            result = TaskResult.create_failure(
                task_id=task.id,
                worker_id=worker_id,
                execution_time_ms=random.randint(100, 500),
                error=f"Failed to scrape {url}"
            )
            logger.info(f"Failed to scrape {url}")
        
        # Record task result
        process.record_task_result(result)
        
        # Process and store content if successful
        if result.success:
            content_id = content_repo.process_and_store_result(result)
            if content_id:
                logger.info(f"Stored content with ID {content_id}")
                
                # Retrieve the content to verify
                content = ScrapedContent.get_by_id(content_id)
                if content:
                    logger.info(f"Retrieved content: {content.title} with {len(content.links)} links")
                    
                    # Show some extracted links
                    for i, link in enumerate(content.links[:5]):
                        logger.info(f"Link {i+1}: {link['target_url']}")
                    
                    if len(content.links) > 5:
                        logger.info(f"... and {len(content.links) - 5} more links")
        
        # Wait a bit between requests to avoid overwhelming servers
        time.sleep(2)

def task_completed_callback(task):
    """Callback for completed tasks"""
    logger.info(f"Task completed: {task.id} - {task.url}")

def main():
    """Main function to demonstrate PostgreSQL content storage"""
    
    # Initialize database
    db = DatabaseManager()
    logger.info("Database initialized")
    
    # Create content repository
    content_repo = ContentRepository()
    
    # Create a process
    process = Process(distribution_strategy=DistributionStrategy.CAPABILITY_MATCH)
    
    # Register task completed hook
    process.add_task_hook(TaskStatus.COMPLETED, task_completed_callback)
    
    # Start the process
    process.start()
    
    try:
        # Create a worker
        worker = process.create_worker(
            name="ContentWorker",
            ip_address="192.168.1.101",
            capabilities=["basic-scraping", "javascript"]
        )
        
        # URLs to scrape (using some popular tech websites)
        urls = [
            "https://news.ycombinator.com/",
            "https://www.theverge.com/",
            "https://techcrunch.com/",
            "https://www.wired.com/",
            "https://www.cnet.com/"
        ]
        
        # Simulate worker execution with real content
        simulate_worker_execution(process, worker.id, urls, content_repo)
        
        # Generate content stats
        stats = content_repo.get_content_stats()
        logger.info("Content stats:")
        logger.info(f"Total pages: {stats['total_pages']}")
        logger.info(f"Total links: {stats['total_links']}")
        logger.info(f"Crawled links: {stats['crawled_links']}")
        
        logger.info("Top domains:")
        for domain in stats['top_domains']:
            logger.info(f"  {domain['domain']}: {domain['count']} pages")
        
        # Get uncrawled links
        uncrawled = content_repo.get_uncrawled_links(limit=10)
        logger.info(f"Uncrawled links sample (from {len(uncrawled)}):")
        for i, link in enumerate(uncrawled[:5]):
            logger.info(f"  {i+1}. {link['url']}")
        
    finally:
        # Close the database connection
        db.close()
        
        # Stop the process
        process.stop()

if __name__ == "__main__":
    main() 