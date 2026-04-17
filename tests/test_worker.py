import asyncio

import pytest

from sauron_python.core.async_worker import AsyncWorker


@pytest.mark.asyncio
async def test_enqueue_and_consume():
    worker = AsyncWorker()
    worker.start()

    results: list[int] = []

    async def job(value: int):
        results.append(value)

    for i in range(5):
        assert worker.enqueue(lambda i=i: job(i))

    await asyncio.sleep(0.1)

    assert sorted(results) == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_worker_is_alive_after_start():
    worker = AsyncWorker()
    assert not worker.is_alive

    worker.start()
    assert worker.is_alive


@pytest.mark.asyncio
async def test_enqueue_without_start_auto_starts():
    worker = AsyncWorker()
    results: list[str] = []

    async def job():
        results.append("done")

    assert worker.enqueue(job)
    await asyncio.sleep(0.1)

    assert worker.is_alive
    assert results == ["done"]


@pytest.mark.asyncio
async def test_queue_full_returns_false():
    worker = AsyncWorker()
    worker.start()

    async def slow_job():
        await asyncio.sleep(10)

    for _ in range(100):
        worker.enqueue(slow_job)

    assert worker.enqueue(slow_job) is False


@pytest.mark.asyncio
async def test_flush_waits_for_all_jobs():
    worker = AsyncWorker()
    worker.start()

    results: list[int] = []

    for i in range(5):
        async def job(n=i):
            await asyncio.sleep(0.05)
            results.append(n)

        worker.enqueue(job)

    worker.flush(timeout=3.0)
    await asyncio.sleep(0.2)

    assert sorted(results) == [0, 1, 2, 3, 4]
    assert worker.pending_count == 0


@pytest.mark.asyncio
async def test_flush_timeout_fires_callback():
    worker = AsyncWorker()
    worker.start()

    async def slow_job():
        await asyncio.sleep(10)

    for _ in range(3):
        worker.enqueue(slow_job)

    callback_calls: list[tuple[int, float]] = []

    def on_notify(pending: int, timeout: float):
        callback_calls.append((pending, timeout))

    worker.flush(timeout=0.1, notify_callback=on_notify)
    await asyncio.sleep(0.3)

    assert len(callback_calls) == 1
    assert callback_calls[0][0] > 0

    worker.kill()


@pytest.mark.asyncio
async def test_flush_on_empty_queue():
    worker = AsyncWorker()
    worker.start()

    worker.flush(timeout=1.0)
    await asyncio.sleep(0.1)

    assert worker.pending_count == 0
