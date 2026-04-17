import asyncio
import logging
import random

from sauron_python.core.async_worker import AsyncWorker

async def _async_main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    worker = AsyncWorker()
    worker.start()

    for i in range(100):
        async def job(n=i):
            await asyncio.sleep(random.uniform(0, 3))

        worker.enqueue(job)
        await asyncio.sleep(random.uniform(0, 2 / 100))

    worker.flush(timeout=1.0, notify_callback=lambda pending, timeout: logging.warning("%d job(s) still pending after %.2f seconds", pending, timeout))

    await asyncio.sleep(10)


def main():
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
