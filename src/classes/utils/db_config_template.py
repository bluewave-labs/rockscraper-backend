"""
Utility to generate database configuration templates
"""
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_env_template(output_path: str = '.env.db') -> None:
    """
    Generate a template .env file for database configuration
    
    Args:
        output_path: Path to write the template file
    """
    template = """# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rockscraper_db
DB_USER=postgres
DB_PASSWORD=postgres

# Database Pool Configuration
DB_POOL_MIN_CONN=5
DB_POOL_MAX_CONN=20

# Content Extraction Configuration
EXTRACT_METADATA=true
EXTRACT_LINKS=true
MAX_HTML_SIZE=10485760  # 10MB
MAX_LINKS_PER_PAGE=1000

# Timeout Configuration
DB_TIMEOUT_MS=5000
"""
    
    try:
        with open(output_path, 'w') as f:
            f.write(template)
        logger.info(f"Database configuration template written to {output_path}")
    except Exception as e:
        logger.error(f"Error writing database configuration template: {e}")

def generate_docker_compose_template(output_path: str = 'docker-compose.db.yml') -> None:
    """
    Generate a docker-compose template for setting up PostgreSQL
    
    Args:
        output_path: Path to write the template file
    """
    template = """version: '3.8'

services:
  postgres:
    image: postgres:14
    container_name: rockscraper-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: rockscraper_db
    ports:
      - "5432:5432"
    volumes:
      - rockscraper-postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4
    container_name: rockscraper-pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

volumes:
  rockscraper-postgres-data:
"""
    
    try:
        with open(output_path, 'w') as f:
            f.write(template)
        logger.info(f"Docker Compose template written to {output_path}")
    except Exception as e:
        logger.error(f"Error writing Docker Compose template: {e}")

def main():
    """Generate all configuration templates"""
    generate_env_template()
    generate_docker_compose_template()
    
    logger.info("""
PostgreSQL database templates generated.

To use PostgreSQL with the scraper:
1. Copy the .env.db file to .env in your project root
2. Start the PostgreSQL database with Docker using:
   docker-compose -f docker-compose.db.yml up -d
3. Install required Python packages:
   pip install psycopg2-binary beautifulsoup4 trafilatura requests

The scraper will automatically create the necessary database schema.
""")

if __name__ == "__main__":
    main() 