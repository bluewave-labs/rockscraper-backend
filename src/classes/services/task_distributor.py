"""
Service for distributing tasks among available workers
"""
from typing import Dict, List, Optional

from models.enums import DistributionStrategy, TaskStatus
from models.task import Task
from models.worker import Worker

class TaskDistributor:
    """Service for distributing tasks among available workers"""
    
    def __init__(self, strategy: DistributionStrategy = DistributionStrategy.LEAST_BUSY):
        """Creates a new TaskDistributor instance"""
        self.tasks: Dict[str, Task] = {}
        self.workers: Dict[str, Worker] = {}
        self.strategy = strategy

    def add_task(self, task: Task) -> None:
        """Adds a task to the distributor"""
        self.tasks[task.id] = task

    def add_tasks(self, tasks: List[Task]) -> None:
        """Adds multiple tasks to the distributor"""
        for task in tasks:
            self.add_task(task)

    def remove_task(self, task_id: str) -> bool:
        """Removes a task from the distributor"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    def get_task(self, task_id: str) -> Optional[Task]:
        """Gets a task by ID"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        """Gets all tasks"""
        return list(self.tasks.values())

    def get_pending_tasks(self) -> List[Task]:
        """Gets pending tasks"""
        return [task for task in self.get_all_tasks() if task.status == TaskStatus.PENDING]

    def add_worker(self, worker: Worker) -> None:
        """Adds a worker to the distributor"""
        self.workers[worker.id] = worker

    def add_workers(self, workers: List[Worker]) -> None:
        """Adds multiple workers to the distributor"""
        for worker in workers:
            self.add_worker(worker)

    def remove_worker(self, worker_id: str) -> bool:
        """Removes a worker from the distributor"""
        if worker_id in self.workers:
            del self.workers[worker_id]
            return True
        return False

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        """Gets a worker by ID"""
        return self.workers.get(worker_id)

    def get_all_workers(self) -> List[Worker]:
        """Gets all workers"""
        return list(self.workers.values())

    def get_available_workers(self) -> List[Worker]:
        """Gets available workers"""
        return [worker for worker in self.get_all_workers() if worker.is_available()]

    def set_strategy(self, strategy: DistributionStrategy) -> None:
        """Updates the distribution strategy"""
        self.strategy = strategy

    def distribute(self) -> int:
        """
        Distributes tasks to available workers using the selected strategy
        Returns: Number of tasks assigned
        """
        pending_tasks = self.get_pending_tasks()
        if not pending_tasks:
            return 0

        available_workers = self.get_available_workers()
        if not available_workers:
            return 0

        tasks_assigned = 0

        if self.strategy == DistributionStrategy.ROUND_ROBIN:
            tasks_assigned = self._distribute_round_robin(pending_tasks, available_workers)
        elif self.strategy == DistributionStrategy.LEAST_BUSY:
            tasks_assigned = self._distribute_least_busy(pending_tasks, available_workers)
        elif self.strategy == DistributionStrategy.PRIORITY_BASED:
            tasks_assigned = self._distribute_priority_based(pending_tasks, available_workers)
        elif self.strategy == DistributionStrategy.CAPABILITY_MATCH:
            tasks_assigned = self._distribute_capability_match(pending_tasks, available_workers)
        else:
            tasks_assigned = self._distribute_least_busy(pending_tasks, available_workers)

        return tasks_assigned

    def _distribute_round_robin(self, tasks: List[Task], workers: List[Worker]) -> int:
        """Distributes tasks using round-robin strategy"""
        tasks_assigned = 0
        worker_index = 0
        worker_count = len(workers)

        for task in tasks:
            if not workers:
                break

            worker = workers[worker_index]
            if worker.assign_task(task.id):
                task.update_status(TaskStatus.ASSIGNED)
                tasks_assigned += 1

            worker_index = (worker_index + 1) % worker_count
            if not worker.is_available():
                workers.remove(worker)
                worker_count = len(workers)
                if worker_count > 0:
                    worker_index = worker_index % worker_count

        return tasks_assigned

    def _distribute_least_busy(self, tasks: List[Task], workers: List[Worker]) -> int:
        """Distributes tasks to the least busy workers"""
        tasks_assigned = 0
        workers.sort(key=lambda w: w.current_load)

        for task in tasks:
            if not workers:
                break

            worker = workers[0]
            if worker.assign_task(task.id):
                task.update_status(TaskStatus.ASSIGNED)
                tasks_assigned += 1

            # Re-sort workers or remove if full
            if not worker.is_available():
                workers.pop(0)
            else:
                workers.sort(key=lambda w: w.current_load)

        return tasks_assigned

    def _distribute_priority_based(self, tasks: List[Task], workers: List[Worker]) -> int:
        """Distributes tasks based on priority"""
        tasks_assigned = 0
        workers.sort(key=lambda w: w.current_load)
        tasks.sort(key=lambda t: t.priority, reverse=True)

        for task in tasks:
            if not workers:
                break

            worker = workers[0]
            if worker.assign_task(task.id):
                task.update_status(TaskStatus.ASSIGNED)
                tasks_assigned += 1

            # Re-sort workers or remove if full
            if not worker.is_available():
                workers.pop(0)
            else:
                workers.sort(key=lambda w: w.current_load)

        return tasks_assigned

    def _distribute_capability_match(self, tasks: List[Task], workers: List[Worker]) -> int:
        """Distributes tasks based on worker capabilities"""
        tasks_assigned = 0

        for task in tasks:
            if not workers:
                break

            # Assume task has a required capability in its data
            required_capability = task.data.get('required_capability')
            
            # Find workers with the required capability
            capable_workers = [w for w in workers if not required_capability or w.has_capability(required_capability)]
            
            if not capable_workers:
                continue

            # Sort by current load
            capable_workers.sort(key=lambda w: w.current_load)
            
            worker = capable_workers[0]
            if worker.assign_task(task.id):
                task.update_status(TaskStatus.ASSIGNED)
                tasks_assigned += 1

            # Update available workers list
            if not worker.is_available() and worker in workers:
                workers.remove(worker)

        return tasks_assigned 