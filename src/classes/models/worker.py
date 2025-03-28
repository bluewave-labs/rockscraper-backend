"""
Implementation of a worker that can execute web scraping tasks
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from models.enums import WorkerStatus

class Worker:
    """Implementation of a worker that can execute web scraping tasks"""
    
    def __init__(
        self,
        name: str,
        ip_address: str,
        capabilities: List[str] = None,
        max_load: int = 5
    ):
        """Creates a new Worker instance"""
        self.id = str(uuid.uuid4())
        self.name = name
        self.status = WorkerStatus.ONLINE
        self.capabilities = capabilities or ['basic-scraping']
        self.current_load = 0
        self.max_load = max_load
        self.ip_address = ip_address
        self.last_heartbeat = datetime.now()
        self.current_tasks = []

    def update_heartbeat(self) -> None:
        """Updates the worker's heartbeat"""
        self.last_heartbeat = datetime.now()

    def update_status(self, status: WorkerStatus) -> None:
        """Updates the worker's status"""
        self.status = status
        self.update_heartbeat()

    def assign_task(self, task_id: str) -> bool:
        """Assigns a task to this worker"""
        if self.current_load >= self.max_load:
            return False

        self.current_tasks.append(task_id)
        self.current_load += 1

        if self.current_load >= self.max_load:
            self.update_status(WorkerStatus.BUSY)

        return True

    def complete_task(self, task_id: str) -> bool:
        """Completes a task"""
        if task_id not in self.current_tasks:
            return False

        self.current_tasks.remove(task_id)
        self.current_load -= 1

        if self.status == WorkerStatus.BUSY and self.current_load < self.max_load:
            self.update_status(WorkerStatus.ONLINE)

        return True

    def has_capability(self, capability: str) -> bool:
        """Checks if the worker has a specific capability"""
        return capability in self.capabilities

    def is_available(self) -> bool:
        """Checks if the worker is available for new tasks"""
        return (
            (self.status == WorkerStatus.ONLINE or self.status == WorkerStatus.BUSY) and
            self.current_load < self.max_load
        )

    def is_heartbeat_expired(self, timeout_ms: int = 60000) -> bool:
        """Checks if the worker is offline based on heartbeat"""
        now = datetime.now()
        elapsed_ms = (now - self.last_heartbeat).total_seconds() * 1000
        return elapsed_ms > timeout_ms

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the worker to a dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'capabilities': self.capabilities,
            'current_load': self.current_load,
            'max_load': self.max_load,
            'ip_address': self.ip_address,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'current_tasks': self.current_tasks
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Worker':
        """Creates a Worker instance from a dictionary"""
        worker = cls(
            name=data['name'],
            ip_address=data['ip_address'],
            capabilities=data['capabilities'],
            max_load=data['max_load']
        )
        worker.id = data['id']
        worker.status = WorkerStatus(data['status'])
        worker.current_load = data['current_load']
        worker.last_heartbeat = datetime.fromisoformat(data['last_heartbeat'])
        worker.current_tasks = data['current_tasks']
        return worker 