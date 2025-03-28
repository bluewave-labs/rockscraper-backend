"""
Models for the web scraping task distribution system
"""

from models.enums import TaskStatus, WorkerStatus, DistributionStrategy
from models.task import Task
from models.worker import Worker
from models.task_result import TaskResult

__all__ = [
    'TaskStatus', 
    'WorkerStatus', 
    'DistributionStrategy', 
    'Task', 
    'Worker', 
    'TaskResult'
] 