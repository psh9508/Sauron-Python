import asyncio
import logging

from typing import Optional, Any, Callable

_TERMINATOR = object()
logger = logging.getLogger(__name__)

class AsyncWorker:
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: Optional[asyncio.Queue[Any]] = None
        self._consumer_task: Optional[asyncio.Task[None]] = None
        self._active_jobs: set[asyncio.Task[None]] = set()

    @property
    def is_alive(self):
        return self._loop.is_running() if self._loop else False
    
    @property
    def pending_count(self) -> int:
        if self._queue is None:
            return 0
        return self._queue.qsize() + len(self._active_jobs)

    @property
    def is_full(self) -> bool:
        if self._queue is None:
            return True
        return self._queue.full()

    
    def enqueue(self, job: Callable[[], Any]) -> bool:
        self._ensure_loop_started()
        if self._queue is None:
            logger.warning("AsyncWorker queue is not initialized. Job will not be enqueued.")
            return False
        try:
            self._queue.put_nowait(job)
            return True
        except asyncio.QueueFull:
            logger.warning("AsyncWorker queue is full. Job will not be enqueued.")
            return False

    
    def flush(self, timeout: float, notify_callback: Optional[Callable[[int, float], None]] = None) -> None:
        if self.is_alive and timeout > 0.0 and self._loop and self._loop.is_running():
            self._loop.create_task(self._await_flush(timeout, notify_callback))


    async def _await_flush(self, timeout: float, notify_callback: Optional[Callable[[int, float], None]] = None) -> None:
        if not self._loop or not self._loop.is_running() or self._queue is None:
            return
        try:
            await asyncio.wait_for(self._queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error("%d event(s) pending on flush", self.pending_count)
            if notify_callback:
                notify_callback(self.pending_count, timeout)


    def kill(self) -> None:
        if self._consumer_task:
            self._consumer_task.cancel()
            jobs_to_cancel = set(self._active_jobs)
            for job in jobs_to_cancel:
                job.cancel()
            self._active_jobs.clear()
            self._loop = None
            self._consumer_task = None


    def start(self):
        if not self.is_alive:
            try:
                self._loop = asyncio.get_running_loop()
                self._queue = asyncio.Queue(maxsize=100)
                self._consumer_task = self._loop.create_task(self._process_queue()) # run loop
            except RuntimeError:
                logger.warning("No running event loop found. AsyncWorker will not start.")
                self._loop = None
                self._queue = None
                self._consumer_task = None


    async def _process_queue(self) -> None:
        if self._queue is None:
            return
        try:
            while True:
                job = await self._queue.get()
                if job is _TERMINATOR:
                    logger.info("Received termination signal. Stopping queue processing.")
                    break

                job_task = self._loop.create_task(self._run_job(job))
                self._active_jobs.add(job_task)
                queue_ref = self._queue
                job_task.add_done_callback(lambda task: self._on_task_complete(task, queue_ref))

                await asyncio.sleep(0) # Yield to let the event loop run other tasks
        except asyncio.CancelledError:
            logger.info("Queue processing task cancelled.")
            pass

    
    def _on_task_complete(self, task: asyncio.Task[None], queue: asyncio.Queue[Any]) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Error in job task: %s", e)
        finally:
            if queue is not None:
                queue.task_done()
            self._active_jobs.discard(task)


    async def _run_job(self, job: Callable[[], Any]) -> None:
        await job()


    def _ensure_loop_started(self):
        if not self.is_alive:
            self.start()
