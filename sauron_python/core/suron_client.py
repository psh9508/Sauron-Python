from sauron_python.core.http_transport import HttpTransport
from sauron_python.models.envelope import Envelope


class SauronClient:
    def __init__(self, *, repository_id: int, endpoint: str):
        self.repository_id = repository_id
        self.endpoint = endpoint
        self._transport = HttpTransport()

    def send(self, data: dict):
        data["repository_id"] = self.repository_id
        envelope = Envelope(
            id="",
            endpoint=self.endpoint,
            payload=data,
        )
        self._transport.send_envelope(envelope)

    def close(self, timeout: float = 2.0):
        self._transport.flush(timeout)
        self._transport.close()
