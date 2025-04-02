# Web Scraping Task Distribution System

A distributed system for web scraping tasks with PostgreSQL-based storage for HTML content.

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

## Environment Variables

Configure your database connection by setting these environment variables:
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: rockscraper_db)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password (default: postgres)

## Example Code

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