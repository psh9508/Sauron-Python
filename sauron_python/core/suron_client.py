from sauron_python.core.async_http_transport import AsyncHttpTransport
from sauron_python.models.envelope import Envelope


class SauronClient:
    def __init__(self, *, repository_id: int, endpoint: str):
        self.repository_id = repository_id
        self.endpoint = endpoint
        self._transport = AsyncHttpTransport()

    def send(self, data: dict):
        data["repository_id"] = self.repository_id
        envelope = Envelope(
            id="",
            endpoint=self.endpoint,
            payload=data,
        )
        self._transport.send_envelope(envelope)
