"""
Implementation of a task result
"""
from datetime import datetime
from typing import Dict, Any, Optional

class TaskResult:
    """Implementation of a task result"""
    
    def __init__(
        self,
        task_id: str,
        worker_id: str,
        success: bool,
        execution_time_ms: int,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Creates a new TaskResult instance"""
        self.task_id = task_id
        self.worker_id = worker_id
        self.success = success
        self.execution_time_ms = execution_time_ms
        self.data = data
        self.error = error
        self.completed_at = datetime.now()

    @classmethod
    def create_success(
        cls,
        task_id: str,
        worker_id: str,
        execution_time_ms: int,
        data: Dict[str, Any]
    ) -> 'TaskResult':
        """Creates a successful result"""
        return cls(task_id, worker_id, True, execution_time_ms, data)

    @classmethod
    def create_failure(
        cls,
        task_id: str,
        worker_id: str,
        execution_time_ms: int,
        error: str
    ) -> 'TaskResult':
        """Creates a failed result"""
        return cls(task_id, worker_id, False, execution_time_ms, None, error)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the task result to a dictionary"""
        return {
            'task_id': self.task_id,
            'worker_id': self.worker_id,
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
            'completed_at': self.completed_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskResult':
        """Creates a TaskResult instance from a dictionary"""
        result = cls(
            task_id=data['task_id'],
            worker_id=data['worker_id'],
            success=data['success'],
            execution_time_ms=data['execution_time_ms'],
            data=data.get('data'),
            error=data.get('error')
        )
        result.completed_at = datetime.fromisoformat(data['completed_at'])
        return result 