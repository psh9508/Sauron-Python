import logging

import httpx

from sauron_python.core.async_worker import AsyncWorker
from sauron_python.models.envelope import Envelope

logger = logging.getLogger(__name__)


class AsyncHttpTransport:
    def __init__(self):
        self._worker = AsyncWorker()
        self._client = httpx.AsyncClient()


    def send_envelope(self, envelope: Envelope):
        async def asend_request_wrapper():
            await self._asend_request(envelope)

        self._worker.enqueue(asend_request_wrapper)


    async def _asend_request(self, envelope: Envelope):
        try:
            return await self._client.post(
                envelope.endpoint,
                json=envelope.payload
            )
        except Exception as e:
            logger.debug("Failed to send envelope: %s", e)


    async def close(self):
        self._worker.kill()
        await self._client.aclose()
