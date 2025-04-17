"""
Implementation of a web scraping task
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from models.enums import TaskStatus

class Task:
    """Implementation of a web scraping task"""
    
    def __init__(
        self,
        url: str,
        priority: int = 1,
        timeout_ms: int = 30000,
        data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ):
        """Creates a new Task instance"""
        self.id = str(uuid.uuid4())
        self.url = url
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.timeout_ms = timeout_ms
        self.data = data or {}
        self.error_count = 0
        self.max_retries = max_retries

    def update_status(self, status: TaskStatus) -> None:
        """Updates the task status"""
        self.status = status
        self.updated_at = datetime.now()

    def record_error(self, error: str) -> None:
        """Records an error for this task"""
        self.error_count += 1
        self.data['last_error'] = error
        
        if self.error_count >= self.max_retries:
            self.update_status(TaskStatus.FAILED)

    def is_timed_out(self) -> bool:
        """Checks if the task has timed out"""
        now = datetime.now()
        in_progress_time = (now - self.updated_at).total_seconds() * 1000
        return self.status == TaskStatus.IN_PROGRESS and in_progress_time > self.timeout_ms

    def reset(self) -> None:
        """Resets the task for retry"""
        self.update_status(TaskStatus.PENDING)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the task to a dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'priority': self.priority,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'timeout_ms': self.timeout_ms,
            'data': self.data,
            'error_count': self.error_count,
            'max_retries': self.max_retries
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Creates a Task instance from a dictionary"""
        task = cls(
            url=data['url'],
            priority=data['priority'],
            timeout_ms=data['timeout_ms'],
            data=data['data'],
            max_retries=data['max_retries']
        )
        task.id = data['id']
        task.status = TaskStatus(data['status'])
        task.created_at = datetime.fromisoformat(data['created_at'])
        task.updated_at = datetime.fromisoformat(data['updated_at'])
        task.error_count = data['error_count']
        return task 