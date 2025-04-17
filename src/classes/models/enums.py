"""
Enums for the web scraping task distribution system
"""
from enum import Enum, auto

class TaskStatus(str, Enum):
    """Status of a task"""
    PENDING = 'pending'
    ASSIGNED = 'assigned'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    TIMEOUT = 'timeout'

class WorkerStatus(str, Enum):
    """Status of a worker"""
    ONLINE = 'online'
    BUSY = 'busy'
    OFFLINE = 'offline'
    ERROR = 'error'

class DistributionStrategy(str, Enum):
    """Task distribution strategy"""
    ROUND_ROBIN = 'round_robin'
    LEAST_BUSY = 'least_busy'
    PRIORITY_BASED = 'priority_based'
    CAPABILITY_MATCH = 'capability_match'

class ContentType(str, Enum):
    """Type of content scraped"""
    HTML = 'html'
    JSON = 'json'
    XML = 'xml'
    TEXT = 'text'
    IMAGE = 'image'
    UNKNOWN = 'unknown'

class LinkStatus(str, Enum):
    """Status of a link in the crawling process"""
    DISCOVERED = 'discovered'
    QUEUED = 'queued'
    CRAWLED = 'crawled'
    ERROR = 'error'
    IGNORED = 'ignored' 