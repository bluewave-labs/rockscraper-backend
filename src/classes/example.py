"""
Example script for demonstrating the web scraping task distribution system
"""
import time
import random
from datetime import datetime

from process import Process
from models.enums import TaskStatus, WorkerStatus, DistributionStrategy
from models.task import Task
from models.worker import Worker
from models.task_result import TaskResult

def task_completed_callback(task):
    """Callback for completed tasks"""
    print(f"Task completed callback: {task.id} - {task.url}")

def worker_offline_callback(worker):
    """Callback for offline workers"""
    print(f"Worker offline callback: {worker.name} ({worker.id})")

def simulate_worker_execution(process, worker_id, sleep_time=1):
    """Simulate a worker executing its tasks"""
    worker = process.distributor.get_worker(worker_id)
    if not worker:
        print(f"Worker {worker_id} not found")
        return

    print(f"Worker {worker.name} processing {len(worker.current_tasks)} tasks")
    
    for task_id in list(worker.current_tasks):  # Create a copy to avoid modification during iteration
        task = process.distributor.get_task(task_id)
        if not task:
            continue
            
        # Simulate work
        time.sleep(sleep_time)
        
        # 80% chance of success
        success = random.random() < 0.8
        execution_time = random.randint(100, 2000)
        
        if success:
            result = TaskResult.create_success(
                task_id=task_id,
                worker_id=worker_id,
                execution_time_ms=execution_time,
                data={'scraped_content': f'Content from {task.url}', 'timestamp': datetime.now().isoformat()}
            )
        else:
            result = TaskResult.create_failure(
                task_id=task_id,
                worker_id=worker_id,
                execution_time_ms=execution_time,
                error=f"Failed to scrape {task.url}"
            )
            
        process.record_task_result(result)
        print(f"Task {task_id} completed with success={success}")

def main():
    """Main function"""
    # Create a process
    process = Process(distribution_strategy=DistributionStrategy.CAPABILITY_MATCH)
    
    # Register task completed hook
    process.add_task_hook(TaskStatus.COMPLETED, task_completed_callback)
    
    # Register worker offline hook
    process.add_worker_hook(WorkerStatus.OFFLINE, worker_offline_callback)
    
    # Start the process
    process.start()
    
    try:
        # Create workers with different capabilities
        worker1 = process.create_worker("Worker1", "192.168.1.101", ["basic-scraping", "javascript"])
        worker2 = process.create_worker("Worker2", "192.168.1.102", ["basic-scraping", "image-processing"])
        worker3 = process.create_worker("Worker3", "192.168.1.103", ["basic-scraping", "form-filling"])
        
        # Create tasks with different requirements
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
            "https://example.com/page4",
            "https://example.com/page5",
            "https://example.com/page6",
        ]
        
        capabilities = ["javascript", "image-processing", "form-filling", None]
        
        for i, url in enumerate(urls):
            # Assign random capabilities
            capability = capabilities[i % len(capabilities)]
            data = {"required_capability": capability} if capability else {}
            
            # Create task with varying priorities
            process.create_task(
                url=url,
                priority=random.randint(1, 5),
                data=data
            )
        
        print(f"Created {len(urls)} tasks")
        
        # Distribute tasks
        tasks_assigned = process.distributor.distribute()
        print(f"Distributed {tasks_assigned} tasks to workers")
        
        # Simulate worker execution
        for worker in process.distributor.get_all_workers():
            if worker.current_tasks:
                simulate_worker_execution(process, worker.id)
        
        # Print metrics
        metrics = process.generate_metrics()
        print("\nMetrics:")
        print(f"Tasks: {metrics['task_counts']['total']}")
        print(f"Workers: {metrics['worker_counts']['total']}")
        print(f"Results: {metrics['results']['total']} (Success rate: {metrics['results']['success_rate']:.1f}%)")
        print("\nTask status counts:")
        for status, count in metrics['task_counts']['by_status'].items():
            if count > 0:
                print(f"  {status}: {count}")
                
        # Save state
        process.save_state("state.json")
        print("\nState saved to state.json")
        
    finally:
        # Stop the process
        process.stop()

if __name__ == "__main__":
    main() 