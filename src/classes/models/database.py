"""
PostgreSQL database connection manager
"""
import os
import psycopg2
from psycopg2 import pool
from typing import Optional, Dict, Any, List, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages PostgreSQL database connection and operations for the scraper system.
    Uses connection pooling for efficient database access.
    """
    _instance = None
    _pool = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one database connection pool exists"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance
    
    def _initialize_pool(self) -> None:
        """Initialize the connection pool using environment variables"""
        try:
            # Get database connection parameters from environment variables
            db_host = os.environ.get('DB_HOST', 'localhost')
            db_port = os.environ.get('DB_PORT', '5432')
            db_name = os.environ.get('DB_NAME', 'rockscraper_db')
            db_user = os.environ.get('DB_USER', 'postgres')
            db_password = os.environ.get('DB_PASSWORD', 'postgres')
            
            # Create a connection pool with a minimum of 5 and maximum of 20 connections
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password
            )
            
            logger.info(f"Connection pool initialized: {db_host}:{db_port}/{db_name}")
            
            # Initialize the database schema
            self._initialize_schema()
            
        except Exception as e:
            logger.error(f"Error initializing database pool: {e}")
            raise
    
    def _initialize_schema(self) -> None:
        """Initialize the database schema if it doesn't exist"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Create schemas if they don't exist
                self._create_tables(cursor)
                conn.commit()
            logger.info("Database schema initialized successfully")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error initializing database schema: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def _create_tables(self, cursor) -> None:
        """Create database tables if they don't exist"""
        # Create enums for task and worker status
        cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
                CREATE TYPE task_status AS ENUM (
                    'pending', 'assigned', 'in_progress', 'completed', 'failed', 'timeout'
                );
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'worker_status') THEN
                CREATE TYPE worker_status AS ENUM (
                    'online', 'busy', 'offline', 'error'
                );
            END IF;
        END
        $$;
        """)

        # Create workers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            status worker_status NOT NULL,
            capabilities JSONB NOT NULL,
            current_load INTEGER NOT NULL DEFAULT 0,
            max_load INTEGER NOT NULL DEFAULT 5,
            ip_address VARCHAR(45) NOT NULL,
            last_heartbeat TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Create tasks table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(36) PRIMARY KEY,
            url TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 1,
            status task_status NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            timeout_ms INTEGER NOT NULL DEFAULT 30000,
            data JSONB,
            error_count INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT 3
        );
        """)
        
        # Create task_results table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_results (
            id SERIAL PRIMARY KEY,
            task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
            worker_id VARCHAR(36) NOT NULL REFERENCES workers(id),
            success BOOLEAN NOT NULL,
            execution_time_ms INTEGER NOT NULL,
            data JSONB,
            error TEXT,
            completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
            UNIQUE(task_id)
        );
        """)
        
        # Create scraped_content table for storing HTML data
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraped_content (
            id SERIAL PRIMARY KEY,
            task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
            url TEXT NOT NULL,
            title VARCHAR(512),
            html_content TEXT,
            text_content TEXT,
            metadata JSONB,
            headers JSONB,
            status_code INTEGER,
            scrape_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(task_id)
        );
        """)
        
        # Create links table for tracking relationships between pages
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id SERIAL PRIMARY KEY,
            source_content_id INTEGER NOT NULL REFERENCES scraped_content(id),
            target_url TEXT NOT NULL,
            link_text TEXT,
            is_internal BOOLEAN NOT NULL,
            crawled BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_content_id);
        CREATE INDEX IF NOT EXISTS idx_links_target_url ON links(target_url);
        CREATE INDEX IF NOT EXISTS idx_links_crawled ON links(crawled);
        """)
        
        # Create worker_tasks table (many-to-many relationship)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS worker_tasks (
            worker_id VARCHAR(36) NOT NULL REFERENCES workers(id),
            task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
            assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (worker_id, task_id)
        );
        """)
        
        # Create indexes
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
        CREATE INDEX IF NOT EXISTS idx_workers_status ON workers(status);
        CREATE INDEX IF NOT EXISTS idx_workers_load ON workers(current_load);
        CREATE INDEX IF NOT EXISTS idx_scraped_content_url ON scraped_content(url);
        """)
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self._pool.getconn()
    
    def release_connection(self, conn):
        """Release a connection back to the pool"""
        if conn:
            self._pool.putconn(conn)
    
    def execute_query(self, query: str, params: Tuple = None, fetch_one: bool = False):
        """
        Execute a query and optionally return results
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: Whether to return a single result
            
        Returns:
            Query result or None
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                if query.strip().upper().startswith('SELECT'):
                    if fetch_one:
                        result = cursor.fetchone()
                    else:
                        result = cursor.fetchall()
                    return result
                
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database query error: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def close(self):
        """Close the connection pool"""
        if self._pool:
            self._pool.closeall()
            logger.info("Database connection pool closed") 