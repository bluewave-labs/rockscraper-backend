# Web Scraping Task Distribution System

A distributed system for web scraping tasks with PostgreSQL-based storage for HTML content and API-based crawling.

## Key Components

### Core System
- `Process`: Main class coordinating the entire system
- `Task`: Representation of a web scraping task
- `Worker`: Represents a worker that can execute tasks
- `TaskDistributor`: Service that assigns tasks to workers

### Database Integration
- `DatabaseManager`: Manages PostgreSQL connection pool and schema
- `ScrapedContent`: Model for storing and retrieving web page content
- `ContentExtractor`: Service for extracting content from HTML
- `ContentRepository`: Repository for managing content operations

### API Crawler Integration
- `AbstractScraper`: Abstract base class defining scraper interface
- `APIClient`: Client for the JavaScript crawlsession API
- `APIScraper`: Concrete scraper implementation using the API client
- `CrawlManager`: High-level manager for crawling operations

## PostgreSQL Schema

The system uses PostgreSQL to store:
- Workers and their status
- Tasks and their execution state
- Task results
- Scraped HTML content and extracted text
- Links found in scraped pages

## Getting Started

1. Set up PostgreSQL:
   ```
   python utils/db_config_template.py
   docker-compose -f docker-compose.db.yml up -d
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the example script:
   ```
   python db_content_example.py
   ```

4. Try the API crawler:
   ```
   python api_crawl_example.py --url https://example.com --depth 2
   ```

## Environment Variables

### Database Configuration:
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: rockscraper_db)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password (default: postgres)

### API Configuration:
- `CRAWL_API_KEY`: API key for crawlsession API
- `CRAWL_API_URL`: Base URL for crawlsession API

## Example Code

### Using the Database:
```python
# Initialize database and repository
db = DatabaseManager()
content_repo = ContentRepository()

# Process a successful task result
if task_result.success:
    content_id = content_repo.process_and_store_result(task_result)
    if content_id:
        print(f"Stored content with ID {content_id}")
        
        # Retrieve content
        content = ScrapedContent.get_by_id(content_id)
        print(f"Retrieved: {content.title}")
```

### Using the API Crawler:
```python
# Create the crawler
scraper = APIScraper()

# Start a session
session_id = scraper.start_session(300)  # 5 minute session

# Scrape a URL
result = scraper.scrape_url("https://example.com", session_id)

# Extract links
links = result['content']['links']

# Close the session
scraper.end_session(session_id)
```

### Using the Crawl Manager for Depth Crawling:
```python
# Create the manager
manager = CrawlManager(max_depth=2, same_domain_only=True)

# Crawl with depth
result = manager.crawl_with_depth("https://example.com")

# Print results
print(f"Total URLs crawled: {result['total_urls_crawled']}")
``` 