import time
import uuid
import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("uvicorn.error")

class TaskState:
    def __init__(self, task_id: str):
        self.task_id: str = task_id
        self.status: str = "pending"  # pending, processing, completed, failed
        self.stage: str = "Uploading"  # Uploading, Parsing, Risk Analysis, AI Processing, Generating Report
        self.progress: int = 0
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.queues: List[asyncio.Queue] = []

    def update_stage(self, stage: str, progress: int):
        """
        Updates the current progress stage and percentage.
        Pushes notifications to all listeners.
        """
        self.status = "processing"
        self.stage = stage
        self.progress = progress
        self.updated_at = time.time()
        logger.info(f"Task {self.task_id[:8]} updated to stage '{stage}' ({progress}%)")
        self._notify_listeners()

    def complete(self, result: Dict[str, Any]):
        """
        Marks the task as completed and provides the final results.
        """
        self.status = "completed"
        self.stage = "Generating Report"
        self.progress = 100
        self.result = result
        self.updated_at = time.time()
        logger.info(f"Task {self.task_id[:8]} successfully completed.")
        self._notify_listeners()

    def fail(self, error: str):
        """
        Marks the task as failed and logs the error.
        """
        self.status = "failed"
        self.progress = 100
        self.error = error
        self.updated_at = time.time()
        logger.error(f"Task {self.task_id[:8]} failed: {error}")
        self._notify_listeners()

    def _notify_listeners(self):
        """
        Pushes the current task state into registered asyncio listener queues.
        """
        payload = {
            "taskId": self.task_id,
            "status": self.status,
            "stage": self.stage,
            "progress": self.progress,
            "result": self.result,
            "error": self.error
        }
        for q in list(self.queues):
            try:
                q.put_nowait(payload)
            except Exception:
                # Listener closed or invalid, will be cleaned up
                pass

# Global tasks in-memory store
tasks: Dict[str, TaskState] = {}

def create_task() -> str:
    """
    Creates a new task in the store and returns its ID.
    Performs periodic cleanup of stale tasks.
    """
    task_id = str(uuid.uuid4())
    tasks[task_id] = TaskState(task_id)
    cleanup_old_tasks()
    return task_id

def cleanup_old_tasks():
    """
    Prunes tasks older than 1 hour, or finished tasks older than 10 minutes to prevent memory leaks.
    """
    now = time.time()
    to_delete = []
    for tid, t in list(tasks.items()):
        # Task life exceeded 1 hour
        if now - t.created_at > 3600:
            to_delete.append(tid)
        # Finished task idle for more than 10 minutes
        elif t.status in ("completed", "failed") and now - t.updated_at > 600:
            to_delete.append(tid)
            
    for tid in to_delete:
        tasks.pop(tid, None)
        logger.info(f"Pruned stale task {tid[:8]} from memory.")
