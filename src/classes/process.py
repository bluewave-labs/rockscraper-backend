"""
Main process class for managing web scraping tasks
"""
import time
import json
import logging
import threading
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timedelta

from models.enums import TaskStatus, WorkerStatus, DistributionStrategy
from models.task import Task
from models.worker import Worker
from models.task_result import TaskResult
from services.task_distributor import TaskDistributor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Process:
    """
    Main process class responsible for managing web scraping tasks,
    workers, and distributing tasks among available workers.
    """
    
    def __init__(
        self, 
        distribution_strategy: DistributionStrategy = DistributionStrategy.LEAST_BUSY,
        heartbeat_timeout_ms: int = 60000,
        task_check_interval_sec: int = 10
    ):
        """Initialize the Process"""
        self.distributor = TaskDistributor(distribution_strategy)
        self.heartbeat_timeout_ms = heartbeat_timeout_ms
        self.task_check_interval_sec = task_check_interval_sec
        self.running = False
        self.task_results: Dict[str, TaskResult] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.task_hooks: Dict[TaskStatus, List[Callable[[Task], None]]] = {
            status: [] for status in TaskStatus
        }
        self.worker_hooks: Dict[WorkerStatus, List[Callable[[Worker], None]]] = {
            status: [] for status in WorkerStatus
        }
        
    def start(self) -> None:
        """Start the process monitoring"""
        if self.running:
            logger.warning("Process is already running")
            return
            
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitor_tasks, daemon=True)
        self.monitoring_thread.start()
        logger.info("Process started")
        
    def stop(self) -> None:
        """Stop the process monitoring"""
        if not self.running:
            logger.warning("Process is not running")
            return
            
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logger.info("Process stopped")
    
    def _monitor_tasks(self) -> None:
        """Monitor tasks and workers"""
        while self.running:
            try:
                self._check_worker_heartbeats()
                self._check_task_timeouts()
                self._distribute_tasks()
            except Exception as e:
                logger.error(f"Error in monitoring thread: {e}")
            
            time.sleep(self.task_check_interval_sec)
    
    def _check_worker_heartbeats(self) -> None:
        """Check worker heartbeats and mark offline workers"""
        for worker in self.distributor.get_all_workers():
            if worker.is_heartbeat_expired(self.heartbeat_timeout_ms) and worker.status != WorkerStatus.OFFLINE:
                old_status = worker.status
                worker.update_status(WorkerStatus.OFFLINE)
                logger.info(f"Worker {worker.name} ({worker.id}) marked as offline due to expired heartbeat")
                self._trigger_worker_hooks(worker, old_status)
    
    def _check_task_timeouts(self) -> None:
        """Check for task timeouts"""
        for task in self.distributor.get_all_tasks():
            if task.status == TaskStatus.IN_PROGRESS and task.is_timed_out():
                task.update_status(TaskStatus.TIMEOUT)
                logger.info(f"Task {task.id} timed out")
                self._trigger_task_hooks(task, TaskStatus.IN_PROGRESS)
    
    def _distribute_tasks(self) -> None:
        """Distribute pending tasks to available workers"""
        tasks_assigned = self.distributor.distribute()
        if tasks_assigned > 0:
            logger.info(f"Distributed {tasks_assigned} tasks to workers")
    
    def add_task(self, task: Task) -> None:
        """Add a task to the process"""
        self.distributor.add_task(task)
        logger.info(f"Added task {task.id} for URL: {task.url}")
    
    def add_tasks(self, tasks: List[Task]) -> None:
        """Add multiple tasks to the process"""
        self.distributor.add_tasks(tasks)
        logger.info(f"Added {len(tasks)} tasks")
    
    def register_worker(self, worker: Worker) -> None:
        """Register a worker with the process"""
        self.distributor.add_worker(worker)
        logger.info(f"Registered worker {worker.name} ({worker.id})")
    
    def register_workers(self, workers: List[Worker]) -> None:
        """Register multiple workers with the process"""
        self.distributor.add_workers(workers)
        logger.info(f"Registered {len(workers)} workers")
    
    def record_task_result(self, result: TaskResult) -> None:
        """Record a task result"""
        task_id = result.task_id
        worker_id = result.worker_id
        
        task = self.distributor.get_task(task_id)
        worker = self.distributor.get_worker(worker_id)
        
        if not task:
            logger.warning(f"Task {task_id} not found for result")
            return
            
        if not worker:
            logger.warning(f"Worker {worker_id} not found for result")
            return
        
        old_status = task.status
        
        # Update task status
        if result.success:
            task.update_status(TaskStatus.COMPLETED)
        else:
            task.record_error(result.error or "Unknown error")
        
        # Update worker
        worker.complete_task(task_id)
        
        # Store result
        self.task_results[task_id] = result
        
        logger.info(f"Recorded result for task {task_id}: success={result.success}")
        
        # Trigger hooks
        self._trigger_task_hooks(task, old_status)
    
    def update_worker_heartbeat(self, worker_id: str) -> bool:
        """Update worker heartbeat"""
        worker = self.distributor.get_worker(worker_id)
        if not worker:
            logger.warning(f"Worker {worker_id} not found for heartbeat update")
            return False
        
        old_status = worker.status
        was_offline = worker.status == WorkerStatus.OFFLINE
        
        worker.update_heartbeat()
        
        # If worker was offline, mark it as online
        if was_offline:
            worker.update_status(WorkerStatus.ONLINE)
            logger.info(f"Worker {worker.name} ({worker.id}) is back online")
            self._trigger_worker_hooks(worker, old_status)
            
        return True
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        return self.distributor.get_pending_tasks()
    
    def get_available_workers(self) -> List[Worker]:
        """Get all available workers"""
        return self.distributor.get_available_workers()
    
    def change_distribution_strategy(self, strategy: DistributionStrategy) -> None:
        """Change the task distribution strategy"""
        self.distributor.set_strategy(strategy)
        logger.info(f"Changed distribution strategy to {strategy.value}")
    
    def add_task_hook(self, status: TaskStatus, hook: Callable[[Task], None]) -> None:
        """Add a hook to be called when a task status changes"""
        self.task_hooks[status].append(hook)
    
    def add_worker_hook(self, status: WorkerStatus, hook: Callable[[Worker], None]) -> None:
        """Add a hook to be called when a worker status changes"""
        self.worker_hooks[status].append(hook)
    
    def _trigger_task_hooks(self, task: Task, old_status: TaskStatus) -> None:
        """Trigger hooks for task status changes"""
        if task.status != old_status:
            for hook in self.task_hooks[task.status]:
                try:
                    hook(task)
                except Exception as e:
                    logger.error(f"Error in task hook: {e}")
    
    def _trigger_worker_hooks(self, worker: Worker, old_status: WorkerStatus) -> None:
        """Trigger hooks for worker status changes"""
        if worker.status != old_status:
            for hook in self.worker_hooks[worker.status]:
                try:
                    hook(worker)
                except Exception as e:
                    logger.error(f"Error in worker hook: {e}")
    
    def create_task(self, url: str, priority: int = 1, timeout_ms: int = 30000, 
                   data: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> Task:
        """Helper to create and add a task in one step"""
        task = Task(url, priority, timeout_ms, data, max_retries)
        self.add_task(task)
        return task
    
    def create_worker(self, name: str, ip_address: str, 
                     capabilities: List[str] = None, max_load: int = 5) -> Worker:
        """Helper to create and register a worker in one step"""
        worker = Worker(name, ip_address, capabilities, max_load)
        self.register_worker(worker)
        return worker
    
    def save_state(self, filename: str) -> None:
        """Save the current state to a file"""
        state = {
            'tasks': [task.to_dict() for task in self.distributor.get_all_tasks()],
            'workers': [worker.to_dict() for worker in self.distributor.get_all_workers()],
            'results': [result.to_dict() for result in self.task_results.values()],
            'settings': {
                'distribution_strategy': self.distributor.strategy.value,
                'heartbeat_timeout_ms': self.heartbeat_timeout_ms,
                'task_check_interval_sec': self.task_check_interval_sec,
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Saved state to {filename}")
    
    def load_state(self, filename: str) -> None:
        """Load state from a file"""
        with open(filename, 'r') as f:
            state = json.load(f)
        
        # Clear current state
        self.distributor.tasks.clear()
        self.distributor.workers.clear()
        self.task_results.clear()
        
        # Load tasks
        for task_data in state['tasks']:
            task = Task.from_dict(task_data)
            self.distributor.add_task(task)
        
        # Load workers
        for worker_data in state['workers']:
            worker = Worker.from_dict(worker_data)
            self.distributor.add_worker(worker)
        
        # Load results
        for result_data in state['results']:
            result = TaskResult.from_dict(result_data)
            self.task_results[result.task_id] = result
        
        # Load settings
        settings = state['settings']
        self.distributor.set_strategy(DistributionStrategy(settings['distribution_strategy']))
        self.heartbeat_timeout_ms = settings['heartbeat_timeout_ms']
        self.task_check_interval_sec = settings['task_check_interval_sec']
        
        logger.info(f"Loaded state from {filename}")
    
    def generate_metrics(self) -> Dict[str, Any]:
        """Generate metrics about the current state"""
        tasks = self.distributor.get_all_tasks()
        workers = self.distributor.get_all_workers()
        
        task_status_counts = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            task_status_counts[task.status.value] += 1
            
        worker_status_counts = {status.value: 0 for status in WorkerStatus}
        for worker in workers:
            worker_status_counts[worker.status.value] += 1
        
        return {
            'task_counts': {
                'total': len(tasks),
                'by_status': task_status_counts
            },
            'worker_counts': {
                'total': len(workers),
                'by_status': worker_status_counts,
                'available': len(self.distributor.get_available_workers())
            },
            'results': {
                'total': len(self.task_results),
                'success_rate': sum(1 for r in self.task_results.values() if r.success) / max(1, len(self.task_results)) * 100
            },
            'distribution_strategy': self.distributor.strategy.value
        } 