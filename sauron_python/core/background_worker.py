import logging
import os
import queue
import threading

from time import time
from typing import Optional, Any, Callable

_TERMINATOR = object()
logger = logging.getLogger(__name__)


class BackgroundWorker:
    """A daemon-thread worker that runs jobs synchronously off a queue.

    Unlike a loop-based worker it does not require a running event loop, so
    telemetry is delivered from both synchronous and asynchronous call sites.
    """

    def __init__(self, queue_size: int = 100):
        self._queue: queue.Queue[Any] = queue.Queue(queue_size)
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        # The event loop / thread must stay within the process that created it.
        self._thread_for_pid: Optional[int] = None

    @property
    def is_alive(self) -> bool:
        if self._thread_for_pid != os.getpid():
            return False
        if not self._thread:
            return False
        return self._thread.is_alive()

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    @property
    def is_full(self) -> bool:
        return self._queue.full()


    def enqueue(self, job: Callable[[], Any]) -> bool:
        self._ensure_thread_started()
        try:
            self._queue.put_nowait(job)
            return True
        except queue.Full:
            logger.warning("BackgroundWorker queue is full. Job will not be enqueued.")
            return False


    def flush(self, timeout: float, notify_callback: Optional[Callable[[int, float], None]] = None) -> None:
        with self._lock:
            if self.is_alive and timeout > 0.0:
                if not self._timed_queue_join(timeout):
                    logger.error("%d event(s) pending on flush", self.pending_count)
                    if notify_callback:
                        notify_callback(self.pending_count, timeout)


    def _timed_queue_join(self, timeout: float) -> bool:
        deadline = time() + timeout
        queue_ref = self._queue
        queue_ref.all_tasks_done.acquire()
        try:
            while queue_ref.unfinished_tasks:
                delay = deadline - time()
                if delay <= 0:
                    return False
                queue_ref.all_tasks_done.wait(timeout=delay)
            return True
        finally:
            queue_ref.all_tasks_done.release()


    def kill(self) -> None:
        with self._lock:
            if self._thread:
                try:
                    self._queue.put_nowait(_TERMINATOR)
                except queue.Full:
                    logger.warning("BackgroundWorker queue is full. Kill request dropped.")
                self._thread = None
                self._thread_for_pid = None


    def start(self) -> None:
        with self._lock:
            if not self.is_alive:
                self._thread = threading.Thread(
                    target=self._process_queue, name="sauron-worker", daemon=True
                )
                try:
                    self._thread.start()
                    self._thread_for_pid = os.getpid()
                except RuntimeError:
                    # The interpreter is already shutting down; we can no longer
                    # start a thread, so events can no longer be sent.
                    logger.warning("Interpreter is shutting down. BackgroundWorker will not start.")
                    self._thread = None


    def _process_queue(self) -> None:
        while True:
            job = self._queue.get()
            try:
                if job is _TERMINATOR:
                    logger.info("Received termination signal. Stopping queue processing.")
                    break
                try:
                    job()
                except Exception as e:
                    logger.error("Error in job task: %s", e)
            finally:
                self._queue.task_done()


    def _ensure_thread_started(self):
        if not self.is_alive:
            self.start()
