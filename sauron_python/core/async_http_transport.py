import asyncio
import httpx
import urllib3

from sauron_python.core.async_worker import AsyncWorker


class AsyncHttpTransport:
    def __init__(self, options):
        self._worker = AsyncWorker()
        self._loop = asyncio.get_running_loop()
        self.SAURON_ENDPOINT = options.get('endpoint', 'http://127.0.0.1:8002/test')


    def send_envelope(self, envelope):
        async def asend_request_wrapper():
            await self._asend_request(envelope)

        self._worker.enqueue(asend_request_wrapper)


    async def _asend_request(self, envelope):
        async with httpx.AsyncClient() as client:
            return await client.post(
                self.SAURON_ENDPOINT,
                json=envelope.to_dict()
            )
