import threading
import time

from sauron_python.core.background_worker import BackgroundWorker


def _wait_until(predicate, timeout: float = 2.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def test_enqueue_and_consume():
    worker = BackgroundWorker()
    worker.start()

    results: list[int] = []
    lock = threading.Lock()

    def job(value: int):
        with lock:
            results.append(value)

    for i in range(5):
        assert worker.enqueue(lambda i=i: job(i))

    assert _wait_until(lambda: len(results) == 5)
    assert sorted(results) == [0, 1, 2, 3, 4]


def test_worker_is_alive_after_start():
    worker = BackgroundWorker()
    assert not worker.is_alive

    worker.start()
    assert worker.is_alive


def test_enqueue_without_start_auto_starts():
    worker = BackgroundWorker()
    results: list[str] = []

    def job():
        results.append("done")

    assert worker.enqueue(job)

    assert _wait_until(lambda: results == ["done"])
    assert worker.is_alive


def test_works_without_running_event_loop():
    """The whole point: enqueue succeeds in a plain synchronous context."""
    worker = BackgroundWorker()
    results: list[str] = []

    assert worker.enqueue(lambda: results.append("sent"))

    assert _wait_until(lambda: results == ["sent"])


def test_queue_full_returns_false():
    worker = BackgroundWorker()
    started = threading.Event()
    release = threading.Event()

    def block():
        started.set()
        release.wait()

    # First job occupies the worker thread, the next 100 fill the queue.
    worker.enqueue(block)
    assert started.wait(timeout=2.0)
    for _ in range(100):
        worker.enqueue(lambda: None)

    assert worker.enqueue(lambda: None) is False
    release.set()


def test_flush_waits_for_all_jobs():
    worker = BackgroundWorker()
    results: list[int] = []
    lock = threading.Lock()

    for i in range(5):
        def job(n=i):
            time.sleep(0.02)
            with lock:
                results.append(n)

        worker.enqueue(job)

    worker.flush(timeout=3.0)

    assert sorted(results) == [0, 1, 2, 3, 4]
    assert worker.pending_count == 0


def test_flush_timeout_fires_callback():
    worker = BackgroundWorker()
    release = threading.Event()

    for _ in range(3):
        worker.enqueue(lambda: release.wait())

    callback_calls: list[tuple[int, float]] = []

    def on_notify(pending: int, timeout: float):
        callback_calls.append((pending, timeout))

    worker.flush(timeout=0.1, notify_callback=on_notify)

    assert len(callback_calls) == 1
    assert callback_calls[0][0] > 0

    release.set()
    worker.kill()


def test_kill_stops_worker():
    worker = BackgroundWorker()
    worker.start()
    assert worker.is_alive

    worker.kill()
    assert _wait_until(lambda: not worker.is_alive)
