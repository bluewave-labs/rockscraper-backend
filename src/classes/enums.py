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