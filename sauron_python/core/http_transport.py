import logging

import httpx

from sauron_python.core.background_worker import BackgroundWorker
from sauron_python.models.envelope import Envelope

logger = logging.getLogger(__name__)


class HttpTransport:
    def __init__(self):
        self._worker = BackgroundWorker()
        self._client = httpx.Client()


    def send_envelope(self, envelope: Envelope):
        def send_request_wrapper():
            self._send_request(envelope)

        self._worker.enqueue(send_request_wrapper)


    def _send_request(self, envelope: Envelope):
        try:
            return self._client.post(
                envelope.endpoint,
                json=envelope.payload
            )
        except Exception as e:
            logger.debug("Failed to send envelope: %s", e)


    def flush(self, timeout: float):
        self._worker.flush(timeout)


    def close(self):
        self._worker.kill()
        self._client.close()
